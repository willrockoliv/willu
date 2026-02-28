"""
Motor de Conciliação Inteligente.
Implementa o fluxo de matching: Dicionário → Fuzzy → Palavras-chave.
"""

from datetime import timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from thefuzz import fuzz

from app.models.transacao import Transacao, StatusTransacao
from app.models.dicionario_conciliacao import DicionarioConciliacao
from app.models.categoria import Categoria
from app.schemas.conciliacao import LinhaExtrato, SugestaoConciliacao

# Configurações do motor
TOLERANCIA_DIAS = 3
TOLERANCIA_VALOR_PERCENTUAL = 0.05  # 5%
SCORE_MINIMO_FUZZY = 50
SCORE_MINIMO_PALAVRAS = 50


async def conciliar_linha(
    db: AsyncSession,
    linha: LinhaExtrato,
    conta_id: int,
) -> SugestaoConciliacao:
    """
    Tenta conciliar uma linha de extrato com transações existentes.
    Prioridade: 1) Dicionário 2) Fuzzy 3) Palavras-chave
    """
    # 1. Dicionário Histórico (match exato na descrição do banco)
    sugestao = await _match_dicionario(db, linha)
    if sugestao:
        return sugestao

    # 2. Busca Fuzzy (data + valor + descrição)
    sugestao = await _match_fuzzy(db, linha, conta_id)
    if sugestao:
        return sugestao

    # 3. Palavras-chave (fallback por similaridade de texto)
    sugestao = await _match_palavras_chave(db, linha)
    if sugestao:
        return sugestao

    # Nenhum match encontrado - transação nova
    return SugestaoConciliacao(
        linha_extrato=linha,
        transacao_id=None,
        transacao_descricao=None,
        categoria_id=None,
        categoria_nome=None,
        score=0.0,
        origem="nova",
    )


async def _match_dicionario(
    db: AsyncSession, linha: LinhaExtrato
) -> SugestaoConciliacao | None:
    """Verifica se a descrição do banco já foi mapeada anteriormente."""
    result = await db.execute(
        select(DicionarioConciliacao).where(
            DicionarioConciliacao.descricao_banco == linha.descricao.strip()
        )
    )
    dic = result.scalar_one_or_none()
    if dic:
        cat_result = await db.execute(
            select(Categoria).where(Categoria.id == dic.categoria_id)
        )
        cat = cat_result.scalar_one_or_none()
        return SugestaoConciliacao(
            linha_extrato=linha,
            transacao_id=None,
            transacao_descricao=dic.descricao_padrao or linha.descricao,
            categoria_id=dic.categoria_id,
            categoria_nome=cat.nome if cat else None,
            score=100.0,
            origem="dicionario",
        )
    return None


async def _match_fuzzy(
    db: AsyncSession, linha: LinhaExtrato, conta_id: int
) -> SugestaoConciliacao | None:
    """Busca transações projetadas em janela de tolerância de data e valor."""
    data_min = linha.data - timedelta(days=TOLERANCIA_DIAS)
    data_max = linha.data + timedelta(days=TOLERANCIA_DIAS)
    valor_abs = abs(linha.valor)

    result = await db.execute(
        select(Transacao).where(
            and_(
                Transacao.conta_id == conta_id,
                Transacao.status == StatusTransacao.PROJETADA,
                Transacao.data_vencimento >= data_min,
                Transacao.data_vencimento <= data_max,
            )
        )
    )
    candidatas = result.scalars().all()

    melhor_score = 0.0
    melhor_transacao = None

    for t in candidatas:
        valor_previsto_abs = abs(float(t.valor_previsto))

        # Score de valor (0-50 pontos)
        if valor_previsto_abs == 0:
            score_valor = 0
        else:
            diff_pct = abs(valor_abs - valor_previsto_abs) / valor_previsto_abs
            if diff_pct <= TOLERANCIA_VALOR_PERCENTUAL:
                score_valor = 50 * (1 - diff_pct / TOLERANCIA_VALOR_PERCENTUAL)
            else:
                score_valor = 0

        # Score de data (0-30 pontos)
        diff_dias = abs((linha.data - t.data_vencimento).days)
        score_data = max(0, 30 - (diff_dias * 10))

        # Score de texto (0-20 pontos)
        score_texto = fuzz.token_sort_ratio(linha.descricao, t.descricao) / 100 * 20

        score_total = score_valor + score_data + score_texto

        if score_total > melhor_score:
            melhor_score = score_total
            melhor_transacao = t

    if melhor_transacao and melhor_score >= SCORE_MINIMO_FUZZY:
        cat_result = await db.execute(
            select(Categoria).where(Categoria.id == melhor_transacao.categoria_id)
        )
        cat = cat_result.scalar_one_or_none()
        return SugestaoConciliacao(
            linha_extrato=linha,
            transacao_id=melhor_transacao.id,
            transacao_descricao=melhor_transacao.descricao,
            categoria_id=melhor_transacao.categoria_id,
            categoria_nome=cat.nome if cat else None,
            score=round(melhor_score, 1),
            origem="fuzzy",
        )
    return None


async def _match_palavras_chave(
    db: AsyncSession, linha: LinhaExtrato
) -> SugestaoConciliacao | None:
    """Verifica similaridade entre descrição do banco e nomes de categorias."""
    result = await db.execute(select(Categoria))
    categorias = result.scalars().all()

    melhor_score = 0.0
    melhor_categoria = None

    for cat in categorias:
        score = fuzz.token_sort_ratio(linha.descricao.lower(), cat.nome.lower())
        if score > melhor_score:
            melhor_score = score
            melhor_categoria = cat

    if melhor_categoria and melhor_score >= SCORE_MINIMO_PALAVRAS:
        return SugestaoConciliacao(
            linha_extrato=linha,
            transacao_id=None,
            transacao_descricao=None,
            categoria_id=melhor_categoria.id,
            categoria_nome=melhor_categoria.nome,
            score=round(melhor_score, 1),
            origem="palavras_chave",
        )
    return None


async def confirmar_conciliacao(
    db: AsyncSession,
    transacao_id: int | None,
    linha: LinhaExtrato,
    categoria_id: int | None,
    descricao: str,
    conta_id: int,
    salvar_dicionario: bool = True,
) -> Transacao:
    """
    Confirma uma conciliação:
    - Se transacao_id existe, atualiza a transação projetada para executada
    - Se não, cria uma nova transação executada
    - Salva no dicionário de conciliação se solicitado
    """
    if transacao_id:
        result = await db.execute(
            select(Transacao).where(Transacao.id == transacao_id)
        )
        transacao = result.scalar_one()
        transacao.status = StatusTransacao.EXECUTADA
        transacao.valor_realizado = linha.valor
        transacao.data_pagamento = linha.data
        transacao.descricao_banco = linha.descricao
        if categoria_id:
            transacao.categoria_id = categoria_id
    else:
        transacao = Transacao(
            conta_id=conta_id,
            categoria_id=categoria_id,
            valor_previsto=linha.valor,
            valor_realizado=linha.valor,
            data_vencimento=linha.data,
            data_pagamento=linha.data,
            status=StatusTransacao.EXECUTADA,
            descricao=descricao,
            descricao_banco=linha.descricao,
        )
        db.add(transacao)

    # Salvar no dicionário de conciliação para aprendizado
    if salvar_dicionario and categoria_id and linha.descricao.strip():
        existing = await db.execute(
            select(DicionarioConciliacao).where(
                DicionarioConciliacao.descricao_banco == linha.descricao.strip()
            )
        )
        dic = existing.scalar_one_or_none()
        if dic:
            dic.categoria_id = categoria_id
            dic.descricao_padrao = descricao
        else:
            dic = DicionarioConciliacao(
                descricao_banco=linha.descricao.strip(),
                categoria_id=categoria_id,
                descricao_padrao=descricao,
            )
            db.add(dic)

    await db.flush()
    return transacao


def conciliar_linha_sync(
    linha: LinhaExtrato,
    transacoes_projetadas: list[dict],
    dicionario: dict[str, dict],
    categorias: list[dict],
) -> SugestaoConciliacao:
    """
    Versão síncrona para uso em testes.
    dicionario: {descricao_banco: {categoria_id, categoria_nome, descricao_padrao}}
    transacoes_projetadas: [{id, descricao, valor_previsto, data_vencimento, categoria_id, categoria_nome}]
    categorias: [{id, nome}]
    """
    # 1. Dicionário
    desc = linha.descricao.strip()
    if desc in dicionario:
        d = dicionario[desc]
        return SugestaoConciliacao(
            linha_extrato=linha,
            transacao_id=None,
            transacao_descricao=d.get("descricao_padrao", desc),
            categoria_id=d["categoria_id"],
            categoria_nome=d.get("categoria_nome"),
            score=100.0,
            origem="dicionario",
        )

    # 2. Fuzzy
    melhor_score = 0.0
    melhor_t = None
    for t in transacoes_projetadas:
        data_min = linha.data - timedelta(days=TOLERANCIA_DIAS)
        data_max = linha.data + timedelta(days=TOLERANCIA_DIAS)
        data_t = t["data_vencimento"]

        if not (data_min <= data_t <= data_max):
            continue

        valor_abs = abs(linha.valor)
        valor_prev_abs = abs(t["valor_previsto"])

        if valor_prev_abs == 0:
            score_valor = 0
        else:
            diff_pct = abs(valor_abs - valor_prev_abs) / valor_prev_abs
            score_valor = 50 * (1 - diff_pct / TOLERANCIA_VALOR_PERCENTUAL) if diff_pct <= TOLERANCIA_VALOR_PERCENTUAL else 0

        diff_dias = abs((linha.data - data_t).days)
        score_data = max(0, 30 - (diff_dias * 10))
        score_texto = fuzz.token_sort_ratio(linha.descricao, t["descricao"]) / 100 * 20

        score_total = score_valor + score_data + score_texto
        if score_total > melhor_score:
            melhor_score = score_total
            melhor_t = t

    if melhor_t and melhor_score >= SCORE_MINIMO_FUZZY:
        return SugestaoConciliacao(
            linha_extrato=linha,
            transacao_id=melhor_t["id"],
            transacao_descricao=melhor_t["descricao"],
            categoria_id=melhor_t.get("categoria_id"),
            categoria_nome=melhor_t.get("categoria_nome"),
            score=round(melhor_score, 1),
            origem="fuzzy",
        )

    # 3. Palavras-chave
    melhor_score_cat = 0.0
    melhor_cat = None
    for c in categorias:
        score = fuzz.token_sort_ratio(linha.descricao.lower(), c["nome"].lower())
        if score > melhor_score_cat:
            melhor_score_cat = score
            melhor_cat = c

    if melhor_cat and melhor_score_cat >= SCORE_MINIMO_PALAVRAS:
        return SugestaoConciliacao(
            linha_extrato=linha,
            transacao_id=None,
            transacao_descricao=None,
            categoria_id=melhor_cat["id"],
            categoria_nome=melhor_cat["nome"],
            score=round(melhor_score_cat, 1),
            origem="palavras_chave",
        )

    return SugestaoConciliacao(
        linha_extrato=linha,
        score=0.0,
        origem="nova",
    )

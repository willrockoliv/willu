"""
Serviço de projeção de saldo dia-a-dia.
Calcula saldo passado (real) e futuro (projetado) para o gráfico principal.
Considera despesas fixas (repetição mensal indefinida) e recorrentes (parcelas).
"""

from calendar import monthrange
from datetime import date, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conta import Conta
from app.models.transacao import Transacao, StatusTransacao


def _add_months(data_base: date, n: int) -> date:
    """Adiciona n meses a uma data, ajustando o dia para meses mais curtos."""
    month = data_base.month - 1 + n
    year = data_base.year + month // 12
    month = month % 12 + 1
    day = min(data_base.day, monthrange(year, month)[1])
    return date(year, month, day)


def _gerar_virtuais(
    transacoes: list[dict],
    data_fim: date,
    hoje: date | None = None,
) -> list[dict]:
    """
    Gera transações virtuais futuras com base na natureza da categoria.

    Cada dict em transacoes deve ter: data, valor, descricao
    Campos opcionais: categoria_id, natureza ("Fixa"/"Recorrente"/"Variável"),
                      parcela_atual, total_parcelas

    Regras:
    - Fixa: repete mensalmente no mesmo dia, indefinidamente até data_fim.
    - Recorrente: repete com base em parcela_atual/total_parcelas.
    - Variável: não repete.

    Retorna lista de dicts: {data, valor, descricao, virtual: True}
    """
    if hoje is None:
        hoje = date.today()

    virtuais = []

    # Rastrear meses com transação real por chave (categoria_id, descricao)
    meses_existentes: dict[tuple, set[tuple[int, int]]] = {}
    for t in transacoes:
        cat_id = t.get("categoria_id")
        if cat_id:
            key = (cat_id, t["descricao"])
            d = t["data"]
            meses_existentes.setdefault(key, set()).add((d.year, d.month))

    # Agrupar por chave → template é a transação mais recente
    templates: dict[tuple, dict] = {}
    for t in transacoes:
        cat_id = t.get("categoria_id")
        if not cat_id:
            continue
        key = (cat_id, t["descricao"])
        if key not in templates or t["data"] > templates[key]["data"]:
            templates[key] = t

    for key, template in templates.items():
        natureza = template.get("natureza")
        if not natureza:
            continue

        # Normalizar: se for enum, pegar o value
        if hasattr(natureza, "value"):
            natureza = natureza.value

        if natureza == "Fixa":
            data_base = template["data"]
            valor = template["valor"]
            desc = template["descricao"]
            existentes = meses_existentes.get(key, set())

            for i in range(1, 121):  # Max 10 anos
                nova_data = _add_months(data_base, i)
                if nova_data > data_fim:
                    break
                if nova_data <= hoje:
                    continue
                if (nova_data.year, nova_data.month) in existentes:
                    continue

                virtuais.append({
                    "data": nova_data,
                    "valor": valor,
                    "descricao": f"{desc} (projeção)",
                    "virtual": True,
                })

        elif natureza == "Recorrente":
            parcela_atual = template.get("parcela_atual")
            total_parcelas = template.get("total_parcelas")

            if (
                parcela_atual is not None
                and total_parcelas is not None
                and parcela_atual < total_parcelas
            ):
                data_base = template["data"]
                valor = template["valor"]
                desc = template["descricao"]
                existentes = meses_existentes.get(key, set())

                restantes = total_parcelas - parcela_atual
                for i in range(1, restantes + 1):
                    nova_data = _add_months(data_base, i)
                    if nova_data > data_fim:
                        break
                    if nova_data <= hoje:
                        continue
                    if (nova_data.year, nova_data.month) in existentes:
                        continue

                    virtuais.append({
                        "data": nova_data,
                        "valor": valor,
                        "descricao": f"{desc} ({parcela_atual + i}/{total_parcelas})",
                        "virtual": True,
                    })

    return virtuais


async def calcular_projecao(
    db: AsyncSession,
    conta_id: int,
    data_inicio: date,
    data_fim: date,
) -> list[dict]:
    """
    Retorna lista de dicts {data, saldo, tipo, movimentacao, detalhes}
    para cada dia no intervalo [data_inicio, data_fim].
    Inclui transações virtuais de despesas fixas e recorrentes.
    """
    hoje = date.today()

    # Buscar saldo inicial da conta
    result = await db.execute(select(Conta).where(Conta.id == conta_id))
    conta = result.scalar_one_or_none()
    if not conta:
        return []

    saldo_inicial = float(conta.saldo_inicial)

    # Buscar transações com categorias carregadas (eager loading)
    result = await db.execute(
        select(Transacao)
        .options(selectinload(Transacao.categoria))
        .where(
            and_(
                Transacao.conta_id == conta_id,
                Transacao.data_vencimento <= data_fim,
            )
        )
        .order_by(Transacao.data_vencimento)
    )
    transacoes = result.scalars().all()

    # Converter para dicts normalizados
    transacoes_dicts = []
    for t in transacoes:
        d = (
            t.data_pagamento
            if t.data_pagamento and t.status == StatusTransacao.EXECUTADA
            else t.data_vencimento
        )
        transacoes_dicts.append({
            "data": d,
            "valor": float(t.valor_efetivo),
            "descricao": t.descricao,
            "id": t.id,
            "status": t.status.value,
            "categoria_id": t.categoria_id,
            "natureza": t.categoria.natureza.value if t.categoria else None,
            "parcela_atual": t.parcela_atual,
            "total_parcelas": t.total_parcelas,
            "virtual": False,
        })

    # Gerar transações virtuais (fixas + recorrentes)
    virtuais = _gerar_virtuais(transacoes_dicts, data_fim)
    for v in virtuais:
        v.setdefault("id", None)
        v.setdefault("status", "Projetada")

    # Combinar reais + virtuais
    todas = transacoes_dicts + virtuais

    # Agrupar por data
    transacoes_por_dia: dict[date, list[dict]] = {}
    for t in todas:
        transacoes_por_dia.setdefault(t["data"], []).append(t)

    # Acumular saldo antes do período visível
    saldo = saldo_inicial
    for t in todas:
        if t["data"] < data_inicio:
            saldo += t["valor"]

    # Gerar série diária
    projecao = []
    dia_atual = data_inicio
    while dia_atual <= data_fim:
        movimentacao = 0.0
        detalhes = []
        for t in transacoes_por_dia.get(dia_atual, []):
            movimentacao += t["valor"]
            detalhes.append({
                "id": t.get("id"),
                "descricao": t["descricao"],
                "valor": t["valor"],
                "status": t.get("status", "Projetada"),
                "virtual": t.get("virtual", False),
            })

        saldo += movimentacao
        tipo = "real" if dia_atual <= hoje else "projetado"

        projecao.append({
            "data": dia_atual.isoformat(),
            "saldo": round(saldo, 2),
            "tipo": tipo,
            "movimentacao": round(movimentacao, 2),
            "detalhes": detalhes,
        })
        dia_atual += timedelta(days=1)

    return projecao


def calcular_projecao_sync(
    saldo_inicial: float,
    transacoes: list[dict],
    data_inicio: date,
    data_fim: date,
    hoje: date | None = None,
) -> list[dict]:
    """
    Versão síncrona para uso em testes.
    transacoes: lista de dicts com {data, valor, status, descricao}
                campos opcionais: categoria_id, natureza, parcela_atual, total_parcelas
    """
    if hoje is None:
        hoje = date.today()

    # Gerar transações virtuais (fixas + recorrentes)
    virtuais = _gerar_virtuais(transacoes, data_fim, hoje=hoje)

    # Combinar reais + virtuais
    todas = list(transacoes) + virtuais

    transacoes_por_dia: dict[date, list[dict]] = {}
    for t in todas:
        transacoes_por_dia.setdefault(t["data"], []).append(t)

    saldo = saldo_inicial
    # Acumular antes do período
    for t in todas:
        if t["data"] < data_inicio:
            saldo += t["valor"]

    projecao = []
    dia_atual = data_inicio
    while dia_atual <= data_fim:
        movimentacao = 0.0
        for t in transacoes_por_dia.get(dia_atual, []):
            movimentacao += t["valor"]

        saldo += movimentacao
        tipo = "real" if dia_atual <= hoje else "projetado"

        projecao.append({
            "data": dia_atual.isoformat(),
            "saldo": round(saldo, 2),
            "tipo": tipo,
            "movimentacao": round(movimentacao, 2),
        })
        dia_atual += timedelta(days=1)

    return projecao

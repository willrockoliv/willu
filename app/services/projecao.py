"""
Serviço de projeção de saldo dia-a-dia.
Calcula saldo passado (real) e futuro (projetado) para o gráfico principal.
"""

from datetime import date, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conta import Conta
from app.models.transacao import Transacao, StatusTransacao


async def calcular_projecao(
    db: AsyncSession,
    conta_id: int,
    data_inicio: date,
    data_fim: date,
) -> list[dict]:
    """
    Retorna uma lista de dicts com {data, saldo, tipo} para cada dia
    no intervalo [data_inicio, data_fim].
    - tipo='real' para dias até hoje (usa valor_realizado quando disponível)
    - tipo='projetado' para dias futuros
    """
    hoje = date.today()

    # Buscar saldo inicial da conta
    result = await db.execute(select(Conta).where(Conta.id == conta_id))
    conta = result.scalar_one_or_none()
    if not conta:
        return []

    saldo_inicial = float(conta.saldo_inicial)

    # Buscar todas as transações no período expandido (desde antes de data_inicio
    # para calcular o saldo acumulado)
    result = await db.execute(
        select(Transacao)
        .where(
            and_(
                Transacao.conta_id == conta_id,
                Transacao.data_vencimento <= data_fim,
            )
        )
        .order_by(Transacao.data_vencimento)
    )
    transacoes = result.scalars().all()

    # Agrupar transações por data de vencimento
    transacoes_por_dia: dict[date, list[Transacao]] = {}
    for t in transacoes:
        d = t.data_pagamento if t.data_pagamento and t.status == StatusTransacao.EXECUTADA else t.data_vencimento
        transacoes_por_dia.setdefault(d, []).append(t)

    # Calcular saldo acumulado antes do período visível
    saldo = saldo_inicial
    for t in transacoes:
        d = t.data_pagamento if t.data_pagamento and t.status == StatusTransacao.EXECUTADA else t.data_vencimento
        if d < data_inicio:
            saldo += float(t.valor_efetivo)

    # Gerar série diária
    projecao = []
    dia_atual = data_inicio
    while dia_atual <= data_fim:
        movimentacao = 0.0
        transacoes_dia = transacoes_por_dia.get(dia_atual, [])
        detalhes = []
        for t in transacoes_dia:
            valor = float(t.valor_efetivo)
            movimentacao += valor
            detalhes.append({
                "id": t.id,
                "descricao": t.descricao,
                "valor": valor,
                "status": t.status.value,
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
) -> list[dict]:
    """
    Versão síncrona para uso em testes.
    transacoes: lista de dicts com {data, valor, status, descricao}
    """
    hoje = date.today()

    transacoes_por_dia: dict[date, list[dict]] = {}
    for t in transacoes:
        transacoes_por_dia.setdefault(t["data"], []).append(t)

    saldo = saldo_inicial
    # Acumular antes do período
    for t in transacoes:
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

from datetime import date, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.conta import Conta
from app.models.categoria import Categoria, NaturezaCategoria, TipoCategoria
from app.models.transacao import Transacao, StatusTransacao
from app.services.projecao import calcular_projecao

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    conta_id: int | None = None,
    dias_futuro: int = 90,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Página principal com o dashboard de projeção."""
    # Buscar contas
    result = await db.execute(select(Conta).order_by(Conta.nome))
    contas = result.scalars().all()

    # Se nenhuma conta, mostrar página vazia
    if not contas:
        return templates.TemplateResponse(
            request, "dashboard.html",
            {"contas": [], "projecao": [], "conta_selecionada": None, "hoje": date.today(), "dias_futuro": dias_futuro,
             "data_inicio": "", "data_fim": ""},
        )

    conta_selecionada = conta_id or (contas[0].id if contas else None)

    hoje = date.today()

    # Período: usar parâmetros de filtro se fornecidos, senão padrão
    if data_inicio:
        dt_inicio = date.fromisoformat(data_inicio)
    else:
        dt_inicio = hoje - timedelta(days=30)

    if data_fim:
        dt_fim = date.fromisoformat(data_fim)
    else:
        dt_fim = hoje + timedelta(days=dias_futuro)

    projecao = await calcular_projecao(db, conta_selecionada, dt_inicio, dt_fim)

    # Resumo para cards
    saldo_atual = 0.0
    saldo_fim_mes = 0.0
    for p in projecao:
        if p["data"] == hoje.isoformat():
            saldo_atual = p["saldo"]
        # Fim do mês corrente
        fim_mes = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1) if hoje.month < 12 else date(hoje.year, 12, 31)
        if p["data"] == fim_mes.isoformat():
            saldo_fim_mes = p["saldo"]

    # Dias negativos
    dias_negativos = [p for p in projecao if p["saldo"] < 0 and p["tipo"] == "projetado"]

    # Somatório de despesas por natureza no período
    despesas_natureza = {n.value: 0.0 for n in NaturezaCategoria}
    stmt = (
        select(Categoria.natureza, func.sum(Transacao.valor_previsto))
        .join(Categoria, Transacao.categoria_id == Categoria.id)
        .where(
            and_(
                Transacao.conta_id == conta_selecionada,
                Categoria.tipo == TipoCategoria.DESPESA,
                Transacao.data_vencimento >= dt_inicio,
                Transacao.data_vencimento <= dt_fim,
            )
        )
        .group_by(Categoria.natureza)
    )
    result_nat = await db.execute(stmt)
    for natureza, total in result_nat.all():
        despesas_natureza[natureza.value if hasattr(natureza, 'value') else natureza] = abs(float(total or 0))

    return templates.TemplateResponse(
        request, "dashboard.html",
        {
            "contas": contas,
            "conta_selecionada": conta_selecionada,
            "projecao": projecao,
            "saldo_atual": saldo_atual,
            "saldo_fim_mes": saldo_fim_mes,
            "dias_negativos": len(dias_negativos),
            "hoje": hoje,
            "dias_futuro": dias_futuro,
            "data_inicio": dt_inicio.isoformat(),
            "data_fim": dt_fim.isoformat(),
            "despesas_natureza": despesas_natureza,
        },
    )


@router.get("/api/projecao", response_class=HTMLResponse)
async def api_projecao(
    request: Request,
    conta_id: int,
    dias_futuro: int = 90,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Retorna o partial do gráfico via HTMX."""
    hoje = date.today()
    dt_inicio = date.fromisoformat(data_inicio) if data_inicio else hoje - timedelta(days=30)
    dt_fim = date.fromisoformat(data_fim) if data_fim else hoje + timedelta(days=dias_futuro)

    projecao = await calcular_projecao(db, conta_id, dt_inicio, dt_fim)

    return templates.TemplateResponse(
        request, "partials/grafico.html",
        {"projecao": projecao, "hoje": hoje},
    )


@router.get("/api/projecao-lista", response_class=HTMLResponse)
async def api_projecao_lista(
    request: Request,
    conta_id: int,
    dias_futuro: int = 90,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Retorna o partial da lista de projeção via HTMX."""
    hoje = date.today()
    dt_inicio = date.fromisoformat(data_inicio) if data_inicio else hoje - timedelta(days=30)
    dt_fim = date.fromisoformat(data_fim) if data_fim else hoje + timedelta(days=dias_futuro)

    projecao = await calcular_projecao(db, conta_id, dt_inicio, dt_fim)

    return templates.TemplateResponse(
        request, "partials/projecao_lista.html",
        {"projecao": projecao, "hoje": hoje},
    )


@router.get("/api/calendario", response_class=HTMLResponse)
async def api_calendario(
    request: Request,
    conta_id: int,
    ano: int | None = None,
    mes: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Retorna o partial do calendário financeiro via HTMX."""
    hoje = date.today()
    ano = ano or hoje.year
    mes = mes or hoje.month

    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim = date(ano, mes + 1, 1) - timedelta(days=1)

    projecao = await calcular_projecao(db, conta_id, data_inicio, data_fim)

    # Weekday do dia 1 do mês (0=segunda, 6=domingo) para alinhar o grid
    primeiro_weekday = data_inicio.weekday()

    return templates.TemplateResponse(
        request, "partials/calendario.html",
        {
            "projecao": projecao,
            "ano": ano,
            "mes": mes,
            "conta_id": conta_id,
            "hoje": hoje,
            "primeiro_weekday": primeiro_weekday,
        },
    )

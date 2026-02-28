from datetime import date, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conta import Conta
from app.models.transacao import Transacao, StatusTransacao
from app.services.projecao import calcular_projecao

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    conta_id: int | None = None,
    meses: int = 3,
    db: AsyncSession = Depends(get_db),
):
    """Página principal com o dashboard de projeção."""
    # Buscar contas
    result = await db.execute(select(Conta).order_by(Conta.nome))
    contas = result.scalars().all()

    # Se nenhuma conta, mostrar página vazia
    if not contas:
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "contas": [], "projecao": [], "conta_selecionada": None, "hoje": date.today()},
        )

    conta_selecionada = conta_id or (contas[0].id if contas else None)

    # Calcular projeção: 30 dias atrás até X meses à frente
    hoje = date.today()
    data_inicio = hoje - timedelta(days=30)
    data_fim = hoje + timedelta(days=30 * meses)

    projecao = await calcular_projecao(db, conta_selecionada, data_inicio, data_fim)

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

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "contas": contas,
            "conta_selecionada": conta_selecionada,
            "projecao": projecao,
            "saldo_atual": saldo_atual,
            "saldo_fim_mes": saldo_fim_mes,
            "dias_negativos": len(dias_negativos),
            "hoje": hoje,
        },
    )


@router.get("/api/projecao", response_class=HTMLResponse)
async def api_projecao(
    request: Request,
    conta_id: int,
    meses: int = 3,
    db: AsyncSession = Depends(get_db),
):
    """Retorna o partial do gráfico via HTMX."""
    hoje = date.today()
    data_inicio = hoje - timedelta(days=30)
    data_fim = hoje + timedelta(days=30 * meses)

    projecao = await calcular_projecao(db, conta_id, data_inicio, data_fim)

    return templates.TemplateResponse(
        "partials/grafico.html",
        {"request": request, "projecao": projecao, "hoje": hoje},
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

    return templates.TemplateResponse(
        "partials/calendario.html",
        {
            "request": request,
            "projecao": projecao,
            "ano": ano,
            "mes": mes,
            "conta_id": conta_id,
            "hoje": hoje,
        },
    )

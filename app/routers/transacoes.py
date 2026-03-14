from datetime import date
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.transacao import Transacao, StatusTransacao
from app.models.conta import Conta
from app.models.categoria import Categoria, NaturezaCategoria
from app.schemas.transacao import TransacaoCreate

router = APIRouter(prefix="/transacoes", tags=["Transações"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def listar_transacoes(
    request: Request,
    conta_id: int | None = None,
    status: str | None = None,
    natureza: str | None = None,
    mes: int | None = None,
    ano: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    hoje = date.today()
    mes = mes or hoje.month
    ano = ano or hoje.year

    query = select(Transacao).order_by(Transacao.data_vencimento.desc())

    if conta_id:
        query = query.where(Transacao.conta_id == conta_id)
    if status:
        query = query.where(Transacao.status == status)
    if natureza:
        query = query.join(Categoria, Transacao.categoria_id == Categoria.id).where(
            Categoria.natureza == natureza
        )

    # Filtrar por mês/ano
    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1)
    else:
        data_fim = date(ano, mes + 1, 1)
    query = query.where(
        and_(
            Transacao.data_vencimento >= data_inicio,
            Transacao.data_vencimento < data_fim,
        )
    )

    result = await db.execute(query)
    transacoes = result.scalars().all()

    result_contas = await db.execute(select(Conta).order_by(Conta.nome))
    contas = result_contas.scalars().all()

    result_cats = await db.execute(select(Categoria).order_by(Categoria.nome))
    categorias = result_cats.scalars().all()

    return templates.TemplateResponse(
        request, "transacoes.html",
        {
            "transacoes": transacoes,
            "contas": contas,
            "categorias": categorias,
            "conta_id": conta_id,
            "status_filtro": status,
            "natureza_filtro": natureza,
            "naturezas": [n.value for n in NaturezaCategoria],
            "mes": mes,
            "ano": ano,
            "hoje": hoje,
        },
    )


@router.get("/lista", response_class=HTMLResponse)
async def lista_transacoes_partial(
    request: Request,
    conta_id: int | None = None,
    natureza: str | None = None,
    mes: int | None = None,
    ano: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    hoje = date.today()
    mes = mes or hoje.month
    ano = ano or hoje.year

    query = select(Transacao).order_by(Transacao.data_vencimento.desc())
    if conta_id:
        query = query.where(Transacao.conta_id == conta_id)
    if natureza:
        query = query.join(Categoria, Transacao.categoria_id == Categoria.id).where(
            Categoria.natureza == natureza
        )

    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1)
    else:
        data_fim = date(ano, mes + 1, 1)
    query = query.where(
        and_(
            Transacao.data_vencimento >= data_inicio,
            Transacao.data_vencimento < data_fim,
        )
    )

    result = await db.execute(query)
    transacoes = result.scalars().all()

    return templates.TemplateResponse(
        request, "partials/transacoes_lista.html",
        {"transacoes": transacoes},
    )


@router.get("/form", response_class=HTMLResponse)
async def form_transacao(request: Request, db: AsyncSession = Depends(get_db)):
    """Retorna o formulário modal para nova transação."""
    result_contas = await db.execute(select(Conta).order_by(Conta.nome))
    contas = result_contas.scalars().all()
    result_cats = await db.execute(select(Categoria).order_by(Categoria.nome))
    categorias = result_cats.scalars().all()

    return templates.TemplateResponse(
        request, "partials/transacao_form.html",
        {"contas": contas, "categorias": categorias, "transacao": None},
    )


@router.get("/form/{transacao_id}", response_class=HTMLResponse)
async def form_editar_transacao(
    transacao_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    """Retorna o formulário modal para editar transação."""
    result = await db.execute(select(Transacao).where(Transacao.id == transacao_id))
    transacao = result.scalar_one_or_none()

    result_contas = await db.execute(select(Conta).order_by(Conta.nome))
    contas = result_contas.scalars().all()
    result_cats = await db.execute(select(Categoria).order_by(Categoria.nome))
    categorias = result_cats.scalars().all()

    return templates.TemplateResponse(
        request, "partials/transacao_form.html",
        {"contas": contas, "categorias": categorias, "transacao": transacao},
    )


@router.post("/", response_class=HTMLResponse)
async def criar_transacao(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()

    valor = float(form.get("valor_previsto", 0))
    # Despesas são negativas
    tipo_valor = form.get("tipo_valor", "despesa")
    if tipo_valor == "despesa" and valor > 0:
        valor = -valor
    elif tipo_valor == "receita" and valor < 0:
        valor = -valor

    status = form.get("status", StatusTransacao.PROJETADA)

    parcela_atual_str = (form.get("parcela_atual") or "").strip()
    total_parcelas_str = (form.get("total_parcelas") or "").strip()

    transacao = Transacao(
        conta_id=int(form.get("conta_id")),
        categoria_id=int(form.get("categoria_id")) if form.get("categoria_id") else None,
        valor_previsto=valor,
        valor_realizado=valor if status == StatusTransacao.EXECUTADA.value else None,
        data_vencimento=date.fromisoformat(form.get("data_vencimento")),
        data_pagamento=date.fromisoformat(form.get("data_pagamento")) if form.get("data_pagamento") else None,
        status=status,
        descricao=form.get("descricao", ""),
        parcela_atual=int(parcela_atual_str) if parcela_atual_str else None,
        total_parcelas=int(total_parcelas_str) if total_parcelas_str else None,
    )
    db.add(transacao)
    await db.flush()

    return HTMLResponse(
        headers={"HX-Trigger": "transacaoCriada"},
        content='<div class="p-3 bg-green-100 text-green-800 rounded-lg text-sm">✅ Transação criada com sucesso!</div>',
    )


@router.put("/{transacao_id}", response_class=HTMLResponse)
async def atualizar_transacao(
    transacao_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    form = await request.form()
    result = await db.execute(select(Transacao).where(Transacao.id == transacao_id))
    transacao = result.scalar_one_or_none()
    if not transacao:
        return HTMLResponse("<p class='text-red-500'>Transação não encontrada</p>", status_code=404)

    if form.get("descricao"):
        transacao.descricao = form["descricao"]
    if form.get("valor_previsto"):
        valor = float(form["valor_previsto"])
        tipo_valor = form.get("tipo_valor", "despesa")
        if tipo_valor == "despesa" and valor > 0:
            valor = -valor
        transacao.valor_previsto = valor
    if form.get("data_vencimento"):
        transacao.data_vencimento = date.fromisoformat(form["data_vencimento"])
    if form.get("categoria_id"):
        transacao.categoria_id = int(form["categoria_id"])
    if form.get("status"):
        transacao.status = form["status"]
    if form.get("data_pagamento"):
        transacao.data_pagamento = date.fromisoformat(form["data_pagamento"])
    if form.get("valor_realizado"):
        transacao.valor_realizado = float(form["valor_realizado"])

    parcela_atual_str = (form.get("parcela_atual") or "").strip()
    transacao.parcela_atual = int(parcela_atual_str) if parcela_atual_str else None
    total_parcelas_str = (form.get("total_parcelas") or "").strip()
    transacao.total_parcelas = int(total_parcelas_str) if total_parcelas_str else None

    await db.flush()

    return HTMLResponse(
        headers={"HX-Trigger": "transacaoAtualizada"},
        content='<div class="p-3 bg-green-100 text-green-800 rounded-lg text-sm">✅ Transação atualizada!</div>',
    )


@router.delete("/{transacao_id}", response_class=HTMLResponse)
async def deletar_transacao(
    transacao_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Transacao).where(Transacao.id == transacao_id))
    transacao = result.scalar_one_or_none()
    if transacao:
        await db.delete(transacao)
        await db.flush()

    return HTMLResponse(
        headers={"HX-Trigger": "transacaoDeletada"},
        content="",
    )

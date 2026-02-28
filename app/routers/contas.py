from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conta import Conta
from app.schemas.conta import ContaCreate, ContaUpdate

router = APIRouter(prefix="/contas", tags=["Contas"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def listar_contas(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conta).order_by(Conta.nome))
    contas = result.scalars().all()
    return templates.TemplateResponse(
        "contas.html", {"request": request, "contas": contas}
    )


@router.get("/lista", response_class=HTMLResponse)
async def lista_contas_partial(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conta).order_by(Conta.nome))
    contas = result.scalars().all()
    return templates.TemplateResponse(
        "partials/contas_lista.html", {"request": request, "contas": contas}
    )


@router.post("/", response_class=HTMLResponse)
async def criar_conta(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    dados = ContaCreate(
        nome=form.get("nome", ""),
        saldo_inicial=float(form.get("saldo_inicial", 0)),
    )
    conta = Conta(nome=dados.nome, saldo_inicial=dados.saldo_inicial)
    db.add(conta)
    await db.flush()

    result = await db.execute(select(Conta).order_by(Conta.nome))
    contas = result.scalars().all()
    return templates.TemplateResponse(
        "partials/contas_lista.html", {"request": request, "contas": contas}
    )


@router.put("/{conta_id}", response_class=HTMLResponse)
async def atualizar_conta(
    conta_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    form = await request.form()
    result = await db.execute(select(Conta).where(Conta.id == conta_id))
    conta = result.scalar_one_or_none()
    if not conta:
        return HTMLResponse("<p class='text-red-500'>Conta não encontrada</p>", status_code=404)

    if form.get("nome"):
        conta.nome = form["nome"]
    if form.get("saldo_inicial"):
        conta.saldo_inicial = float(form["saldo_inicial"])

    await db.flush()

    result = await db.execute(select(Conta).order_by(Conta.nome))
    contas = result.scalars().all()
    return templates.TemplateResponse(
        "partials/contas_lista.html", {"request": request, "contas": contas}
    )


@router.delete("/{conta_id}", response_class=HTMLResponse)
async def deletar_conta(
    conta_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Conta).where(Conta.id == conta_id))
    conta = result.scalar_one_or_none()
    if conta:
        await db.delete(conta)
        await db.flush()

    result = await db.execute(select(Conta).order_by(Conta.nome))
    contas = result.scalars().all()
    return templates.TemplateResponse(
        "partials/contas_lista.html", {"request": request, "contas": contas}
    )

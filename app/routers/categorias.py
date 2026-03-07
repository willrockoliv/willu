from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.categoria import Categoria, TipoCategoria, NaturezaCategoria
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate

router = APIRouter(prefix="/categorias", tags=["Categorias"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def listar_categorias(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Categoria).order_by(Categoria.tipo, Categoria.nome))
    categorias = result.scalars().all()
    return templates.TemplateResponse(
        request, "categorias.html",
        {
            "categorias": categorias,
            "tipos": TipoCategoria,
            "naturezas": NaturezaCategoria,
        },
    )


@router.get("/lista", response_class=HTMLResponse)
async def lista_categorias_partial(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Categoria).order_by(Categoria.tipo, Categoria.nome))
    categorias = result.scalars().all()
    return templates.TemplateResponse(
        request, "partials/categorias_lista.html", {"categorias": categorias}
    )


@router.post("/", response_class=HTMLResponse)
async def criar_categoria(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    dados = CategoriaCreate(
        nome=form.get("nome", ""),
        tipo=form.get("tipo", TipoCategoria.DESPESA),
        natureza=form.get("natureza", NaturezaCategoria.VARIAVEL),
    )
    categoria = Categoria(nome=dados.nome, tipo=dados.tipo, natureza=dados.natureza)
    db.add(categoria)
    await db.flush()

    result = await db.execute(select(Categoria).order_by(Categoria.tipo, Categoria.nome))
    categorias = result.scalars().all()
    return templates.TemplateResponse(
        request, "partials/categorias_lista.html", {"categorias": categorias}
    )


@router.put("/{categoria_id}", response_class=HTMLResponse)
async def atualizar_categoria(
    categoria_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    form = await request.form()
    result = await db.execute(select(Categoria).where(Categoria.id == categoria_id))
    cat = result.scalar_one_or_none()
    if not cat:
        return HTMLResponse("<p class='text-red-500'>Categoria não encontrada</p>", status_code=404)

    if form.get("nome"):
        cat.nome = form["nome"]
    if form.get("tipo"):
        cat.tipo = form["tipo"]
    if form.get("natureza"):
        cat.natureza = form["natureza"]

    await db.flush()

    result = await db.execute(select(Categoria).order_by(Categoria.tipo, Categoria.nome))
    categorias = result.scalars().all()
    return templates.TemplateResponse(
        request, "partials/categorias_lista.html", {"categorias": categorias}
    )


@router.delete("/{categoria_id}", response_class=HTMLResponse)
async def deletar_categoria(
    categoria_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Categoria).where(Categoria.id == categoria_id))
    cat = result.scalar_one_or_none()
    if cat:
        await db.delete(cat)
        await db.flush()

    result = await db.execute(select(Categoria).order_by(Categoria.tipo, Categoria.nome))
    categorias = result.scalars().all()
    return templates.TemplateResponse(
        request, "partials/categorias_lista.html", {"categorias": categorias}
    )


@router.get("/api/options", response_class=HTMLResponse)
async def categorias_options(
    request: Request, tipo: str | None = None, db: AsyncSession = Depends(get_db)
):
    """Retorna options HTML para selects de categorias."""
    query = select(Categoria).order_by(Categoria.nome)
    if tipo:
        query = query.where(Categoria.tipo == tipo)
    result = await db.execute(query)
    categorias = result.scalars().all()

    options = '<option value="">Selecione...</option>'
    for c in categorias:
        options += f'<option value="{c.id}">{c.nome} ({c.natureza.value})</option>'
    return HTMLResponse(options)

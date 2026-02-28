import json
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conta import Conta
from app.models.categoria import Categoria
from app.services.importacao import importar_ofx, importar_csv, detectar_formato
from app.services.conciliacao import conciliar_linha, confirmar_conciliacao
from app.schemas.conciliacao import LinhaExtrato, ConfirmacaoConciliacao

router = APIRouter(prefix="/importacao", tags=["Importação"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def pagina_importacao(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conta).order_by(Conta.nome))
    contas = result.scalars().all()
    return templates.TemplateResponse(
        "importacao.html", {"request": request, "contas": contas}
    )


@router.post("/upload", response_class=HTMLResponse)
async def upload_extrato(
    request: Request,
    arquivo: UploadFile = File(...),
    conta_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Faz upload do arquivo, parseia e retorna sugestões de conciliação."""
    conteudo = await arquivo.read()
    formato = detectar_formato(arquivo.filename)

    if formato == "ofx":
        linhas = importar_ofx(conteudo)
    else:
        linhas = importar_csv(conteudo)

    # Conciliar cada linha
    sugestoes = []
    for linha in linhas:
        sugestao = await conciliar_linha(db, linha, conta_id)
        sugestoes.append(sugestao)

    # Buscar categorias para o select
    result = await db.execute(select(Categoria).order_by(Categoria.nome))
    categorias = result.scalars().all()

    return templates.TemplateResponse(
        "partials/conciliacao_lista.html",
        {
            "request": request,
            "sugestoes": sugestoes,
            "categorias": categorias,
            "conta_id": conta_id,
        },
    )


@router.post("/confirmar", response_class=HTMLResponse)
async def confirmar(request: Request, db: AsyncSession = Depends(get_db)):
    """Confirma uma conciliação individual."""
    form = await request.form()

    linha = LinhaExtrato(
        data=form.get("data"),
        descricao=form.get("descricao_banco"),
        valor=float(form.get("valor")),
    )

    transacao_id = int(form.get("transacao_id")) if form.get("transacao_id") else None
    categoria_id = int(form.get("categoria_id")) if form.get("categoria_id") else None
    descricao = form.get("descricao", linha.descricao)
    conta_id = int(form.get("conta_id"))
    salvar_dic = form.get("salvar_dicionario", "on") == "on"

    transacao = await confirmar_conciliacao(
        db=db,
        transacao_id=transacao_id,
        linha=linha,
        categoria_id=categoria_id,
        descricao=descricao,
        conta_id=conta_id,
        salvar_dicionario=salvar_dic,
    )

    return HTMLResponse(
        f'<tr class="bg-green-50"><td colspan="6" class="px-4 py-2 text-green-700 text-sm">'
        f'✅ Conciliado: {descricao} — R$ {abs(linha.valor):,.2f}</td></tr>'
    )


@router.post("/confirmar-todas", response_class=HTMLResponse)
async def confirmar_todas(request: Request, db: AsyncSession = Depends(get_db)):
    """Confirma todas as conciliações de uma vez."""
    form = await request.form()
    dados_json = form.get("dados")

    if not dados_json:
        return HTMLResponse('<p class="text-red-500">Nenhum dado recebido</p>')

    itens = json.loads(dados_json)
    confirmados = 0

    for item in itens:
        linha = LinhaExtrato(
            data=item["data"],
            descricao=item["descricao_banco"],
            valor=float(item["valor"]),
        )
        transacao_id = int(item["transacao_id"]) if item.get("transacao_id") else None
        categoria_id = int(item["categoria_id"]) if item.get("categoria_id") else None

        await confirmar_conciliacao(
            db=db,
            transacao_id=transacao_id,
            linha=linha,
            categoria_id=categoria_id,
            descricao=item.get("descricao", linha.descricao),
            conta_id=int(item["conta_id"]),
            salvar_dicionario=True,
        )
        confirmados += 1

    return HTMLResponse(
        f'<div class="p-4 bg-green-100 text-green-800 rounded-lg">'
        f'✅ {confirmados} transações conciliadas com sucesso!'
        f'</div>'
    )

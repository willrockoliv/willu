from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import engine, Base
from app.routers import dashboard, contas, categorias, transacoes, importacao


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Criar tabelas no startup (dev only — em produção use Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title=settings.APP_TITLE, lifespan=lifespan)

# Routers
app.include_router(dashboard.router)
app.include_router(contas.router)
app.include_router(categorias.router)
app.include_router(transacoes.router)
app.include_router(importacao.router)

"""
Fixtures compartilhadas para testes.
Configura banco SQLite in-memory para testes de integração HTTP.
"""

import pytest
import pytest_asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from app.database import Base, get_db

# Importar todos os models para registrá-los no Base.metadata
import app.models  # noqa: F401


TEST_DATABASE_URL = "sqlite+aiosqlite://"

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
async_session_test = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """Override do get_db para usar banco de testes."""
    async with async_session_test() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def db_session():
    """Sessão de banco de dados para testes diretos com models."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_test() as session:
        yield session

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Cliente HTTP para testes de integração com FastAPI."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.routers import dashboard, contas, categorias, transacoes, importacao

    @asynccontextmanager
    async def noop_lifespan(app: FastAPI):
        yield

    test_app = FastAPI(lifespan=noop_lifespan)
    test_app.include_router(dashboard.router)
    test_app.include_router(contas.router)
    test_app.include_router(categorias.router)
    test_app.include_router(transacoes.router)
    test_app.include_router(importacao.router)

    test_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        yield ac

    test_app.dependency_overrides.clear()

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

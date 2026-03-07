"""
Script para popular o banco com categorias iniciais.
Uso: python -m scripts.seed
"""

import asyncio
from sqlalchemy import select
from app.database import async_session, engine, Base
from app.models.categoria import Categoria, TipoCategoria, NaturezaCategoria


CATEGORIAS_INICIAIS = [
    # Despesas Fixas
    ("Aluguel", TipoCategoria.DESPESA, NaturezaCategoria.FIXA),
    ("Condomínio", TipoCategoria.DESPESA, NaturezaCategoria.FIXA),
    ("Financiamento", TipoCategoria.DESPESA, NaturezaCategoria.FIXA),
    ("Seguro", TipoCategoria.DESPESA, NaturezaCategoria.FIXA),
    ("Plano de Saúde", TipoCategoria.DESPESA, NaturezaCategoria.FIXA),
    ("Escola/Faculdade", TipoCategoria.DESPESA, NaturezaCategoria.FIXA),
    # Despesas Recorrentes
    ("Energia Elétrica", TipoCategoria.DESPESA, NaturezaCategoria.RECORRENTE),
    ("Água", TipoCategoria.DESPESA, NaturezaCategoria.RECORRENTE),
    ("Internet", TipoCategoria.DESPESA, NaturezaCategoria.RECORRENTE),
    ("Celular", TipoCategoria.DESPESA, NaturezaCategoria.RECORRENTE),
    ("Streaming", TipoCategoria.DESPESA, NaturezaCategoria.RECORRENTE),
    ("Academia", TipoCategoria.DESPESA, NaturezaCategoria.RECORRENTE),
    # Despesas Variáveis (média mensal usada na projeção)
    ("Alimentação", TipoCategoria.DESPESA, NaturezaCategoria.VARIAVEL),
    ("Supermercado", TipoCategoria.DESPESA, NaturezaCategoria.VARIAVEL),
    ("Transporte", TipoCategoria.DESPESA, NaturezaCategoria.VARIAVEL),
    ("Saúde", TipoCategoria.DESPESA, NaturezaCategoria.VARIAVEL),
    # Despesas Esporádicas (não entram na projeção)
    ("Lazer", TipoCategoria.DESPESA, NaturezaCategoria.ESPORADICA),
    ("Vestuário", TipoCategoria.DESPESA, NaturezaCategoria.ESPORADICA),
    ("Educação", TipoCategoria.DESPESA, NaturezaCategoria.ESPORADICA),
    ("Presentes", TipoCategoria.DESPESA, NaturezaCategoria.ESPORADICA),
    ("Viagens", TipoCategoria.DESPESA, NaturezaCategoria.ESPORADICA),
    ("Outros", TipoCategoria.DESPESA, NaturezaCategoria.ESPORADICA),
    # Receitas
    ("Salário", TipoCategoria.RECEITA, NaturezaCategoria.FIXA),
    ("Freelance", TipoCategoria.RECEITA, NaturezaCategoria.VARIAVEL),
    ("Investimentos", TipoCategoria.RECEITA, NaturezaCategoria.VARIAVEL),
    ("Outros (Receita)", TipoCategoria.RECEITA, NaturezaCategoria.VARIAVEL),
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Verificar se já existem categorias
        result = await session.execute(select(Categoria))
        existentes = result.scalars().all()

        if existentes:
            print(f"⚠️  Já existem {len(existentes)} categorias no banco. Pulando seed.")
            return

        for nome, tipo, natureza in CATEGORIAS_INICIAIS:
            session.add(Categoria(nome=nome, tipo=tipo, natureza=natureza))

        await session.commit()
        print(f"✅ {len(CATEGORIAS_INICIAIS)} categorias criadas com sucesso!")


if __name__ == "__main__":
    asyncio.run(seed())

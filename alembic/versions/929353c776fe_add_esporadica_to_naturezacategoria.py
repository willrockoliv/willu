"""add_esporadica_to_naturezacategoria

Revision ID: 929353c776fe
Revises: f15c4d42dc5a
Create Date: 2026-03-07 19:48:12.749884
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '929353c776fe'
down_revision: Union[str, None] = 'f15c4d42dc5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requer ALTER TYPE para adicionar valores a um enum existente
    op.execute("ALTER TYPE naturezacategoria ADD VALUE IF NOT EXISTS 'Esporádica'")


def downgrade() -> None:
    # PostgreSQL não suporta remover valores de enum diretamente.
    # Para reverter, seria necessário recriar o tipo e a coluna.
    pass

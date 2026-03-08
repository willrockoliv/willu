"""add_esporadica_to_naturezacategoria

Revision ID: f15c4d42dc5a
Revises: cfd8663aee73
Create Date: 2026-03-07 19:47:55.893929
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f15c4d42dc5a'
down_revision: Union[str, None] = 'cfd8663aee73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

"""initial_with_parcelas

Revision ID: cfd8663aee73
Revises: 
Create Date: 2026-03-07 19:24:56.407458
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'cfd8663aee73'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'contas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('saldo_inicial', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'categorias',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('tipo', sa.Enum('Receita', 'Despesa', name='tipocategoria'), nullable=False),
        sa.Column(
            'natureza',
            sa.Enum('Fixa', 'Recorrente', 'Variável', 'Esporádica', name='naturezacategoria'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'transacoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conta_id', sa.Integer(), nullable=False),
        sa.Column('categoria_id', sa.Integer(), nullable=True),
        sa.Column('valor_previsto', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('valor_realizado', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('data_vencimento', sa.Date(), nullable=False),
        sa.Column('data_pagamento', sa.Date(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('Projetada', 'Executada', name='statustransacao'),
            nullable=False,
        ),
        sa.Column('descricao', sa.String(length=255), nullable=False),
        sa.Column('descricao_banco', sa.Text(), nullable=True),
        sa.Column('parcela_atual', sa.Integer(), nullable=True),
        sa.Column('total_parcelas', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['categoria_id'], ['categorias.id']),
        sa.ForeignKeyConstraint(['conta_id'], ['contas.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'dicionario_conciliacao',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('descricao_banco', sa.Text(), nullable=False),
        sa.Column('categoria_id', sa.Integer(), nullable=False),
        sa.Column('descricao_padrao', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['categoria_id'], ['categorias.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('descricao_banco'),
    )


def downgrade() -> None:
    op.drop_table('dicionario_conciliacao')
    op.drop_table('transacoes')
    op.drop_table('categorias')
    op.drop_table('contas')

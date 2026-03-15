"""add orcamento, orcamento_item, orcamento_status_log tables

Revision ID: a3450ecbfd60
Revises: 059651626f0f
Create Date: 2026-03-15 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'a3450ecbfd60'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('orcamento',
        sa.Column('service_type', sa.Enum('perfuracao', 'reparo', name='servicetype'), nullable=False),
        sa.Column('execution_address', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('city', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('cep', sqlmodel.sql.sqltypes.AutoString(length=9), nullable=True),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('forma_pagamento', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('vendedor', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('ref_code', sqlmodel.sql.sqltypes.AutoString(length=6), nullable=False),
        sa.Column('client_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.Enum('rascunho', 'em_analise', 'aprovado', 'cancelado', name='orcamentostatus'), nullable=False),
        sa.Column('validade_proposta', sa.Date(), nullable=True),
        sa.Column('service_id', sa.Uuid(), nullable=True),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['client.id']),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['service_id'], ['service.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_orcamento_client_id'), 'orcamento', ['client_id'], unique=False)
    op.create_index(op.f('ix_orcamento_ref_code'), 'orcamento', ['ref_code'], unique=True)
    op.create_index(op.f('ix_orcamento_status'), 'orcamento', ['status'], unique=False)

    op.create_table('orcamento_item',
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('show_unit_price', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('orcamento_id', sa.Uuid(), nullable=False),
        sa.Column('product_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['orcamento_id'], ['orcamento.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_orcamento_item_orcamento_id'), 'orcamento_item', ['orcamento_id'], unique=False)

    op.create_table('orcamento_status_log',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('orcamento_id', sa.Uuid(), nullable=False),
        sa.Column('from_status', sa.Enum('rascunho', 'em_analise', 'aprovado', 'cancelado', name='orcamentostatus'), nullable=False),
        sa.Column('to_status', sa.Enum('rascunho', 'em_analise', 'aprovado', 'cancelado', name='orcamentostatus'), nullable=False),
        sa.Column('changed_by', sa.Uuid(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.ForeignKeyConstraint(['changed_by'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['orcamento_id'], ['orcamento.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_orcamento_status_log_orcamento_id'), 'orcamento_status_log', ['orcamento_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_orcamento_status_log_orcamento_id'), table_name='orcamento_status_log')
    op.drop_table('orcamento_status_log')
    op.drop_index(op.f('ix_orcamento_item_orcamento_id'), table_name='orcamento_item')
    op.drop_table('orcamento_item')
    op.drop_index(op.f('ix_orcamento_status'), table_name='orcamento')
    op.drop_index(op.f('ix_orcamento_ref_code'), table_name='orcamento')
    op.drop_index(op.f('ix_orcamento_client_id'), table_name='orcamento')
    op.drop_table('orcamento')
    # Note: the orcamentostatus enum type will remain in the DB after downgrade

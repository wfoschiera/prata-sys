"""add transacao table

Revision ID: ebef516f7ec1
Revises: f4ed2978c38c
Create Date: 2026-03-13 16:15:26.377988

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'ebef516f7ec1'
down_revision = 'f4ed2978c38c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'transacao',
        sa.Column('tipo', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column('categoria', sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column('valor', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('data_competencia', sa.Date(), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('nome_contraparte', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('service_id', sa.Uuid(), nullable=True),
        sa.Column('client_id', sa.Uuid(), nullable=True),
        sa.Column('fornecedor_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['service_id'], ['service.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_transacao_client_id'), 'transacao', ['client_id'], unique=False)
    op.create_index(op.f('ix_transacao_fornecedor_id'), 'transacao', ['fornecedor_id'], unique=False)
    op.create_index(op.f('ix_transacao_service_id'), 'transacao', ['service_id'], unique=False)
    op.create_index('ix_transacao_data_competencia', 'transacao', ['data_competencia'], unique=False)


def downgrade():
    op.drop_index('ix_transacao_data_competencia', table_name='transacao')
    op.drop_index(op.f('ix_transacao_service_id'), table_name='transacao')
    op.drop_index(op.f('ix_transacao_fornecedor_id'), table_name='transacao')
    op.drop_index(op.f('ix_transacao_client_id'), table_name='transacao')
    op.drop_table('transacao')

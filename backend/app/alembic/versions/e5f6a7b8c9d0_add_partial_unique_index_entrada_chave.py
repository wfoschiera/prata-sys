"""add partial unique index on entradaestoque numero_documento

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    # One entrada per chave de acesso. Scoped to 44-character documents so
    # hand-typed short numbers ("NF 123") from different suppliers remain
    # allowed. Precedent: ix_fornecedor_cnpj_unique in f3a68091d1fb.
    op.create_index(
        'ix_entradaestoque_chave_unique',
        'entradaestoque',
        ['numero_documento'],
        unique=True,
        postgresql_where=sa.text('char_length(numero_documento) = 44'),
    )


def downgrade():
    op.drop_index('ix_entradaestoque_chave_unique', table_name='entradaestoque')

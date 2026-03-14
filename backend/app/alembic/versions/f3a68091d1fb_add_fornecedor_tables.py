"""add fornecedor tables

Revision ID: f3a68091d1fb
Revises: bb87e5034a77
Create Date: 2026-03-14 10:31:58.820208

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'f3a68091d1fb'
down_revision = 'bb87e5034a77'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'fornecedor',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('cnpj', sqlmodel.sql.sqltypes.AutoString(length=14), nullable=True),
        sa.Column('address', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_fornecedor_company_name'), 'fornecedor', ['company_name'], unique=False)
    # Partial unique index: only enforce uniqueness when cnpj is not NULL
    op.create_index(
        'ix_fornecedor_cnpj_unique',
        'fornecedor',
        ['cnpj'],
        unique=True,
        postgresql_where=sa.text('cnpj IS NOT NULL'),
    )

    op.create_table(
        'fornecedor_categoria',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('fornecedor_id', sa.Uuid(), nullable=False),
        sa.Column('category', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.ForeignKeyConstraint(['fornecedor_id'], ['fornecedor.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fornecedor_id', 'category'),
    )
    op.create_index(op.f('ix_fornecedor_categoria_fornecedor_id'), 'fornecedor_categoria', ['fornecedor_id'], unique=False)

    op.create_table(
        'fornecedor_contato',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('fornecedor_id', sa.Uuid(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('telefone', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('whatsapp', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.ForeignKeyConstraint(['fornecedor_id'], ['fornecedor.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_fornecedor_contato_fornecedor_id'), 'fornecedor_contato', ['fornecedor_id'], unique=False)

    # Add FK from transacao.fornecedor_id → fornecedor.id (column existed without FK since Phase 4)
    op.create_foreign_key(
        'transacao_fornecedor_id_fkey',
        'transacao',
        'fornecedor',
        ['fornecedor_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade():
    op.drop_constraint('transacao_fornecedor_id_fkey', 'transacao', type_='foreignkey')
    op.drop_index(op.f('ix_fornecedor_contato_fornecedor_id'), table_name='fornecedor_contato')
    op.drop_table('fornecedor_contato')
    op.drop_index(op.f('ix_fornecedor_categoria_fornecedor_id'), table_name='fornecedor_categoria')
    op.drop_table('fornecedor_categoria')
    op.drop_index('ix_fornecedor_cnpj_unique', table_name='fornecedor')
    op.drop_index(op.f('ix_fornecedor_company_name'), table_name='fornecedor')
    op.drop_table('fornecedor')

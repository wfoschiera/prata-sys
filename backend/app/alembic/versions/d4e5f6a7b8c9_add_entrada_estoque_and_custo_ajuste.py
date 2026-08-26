"""add entrada estoque and custo ajuste

Revision ID: d4e5f6a7b8c9
Revises: 6134a479de6e
Create Date: 2026-08-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = '6134a479de6e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('entradaestoque',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('fornecedor_id', sa.Uuid(), nullable=True),
    sa.Column('data_entrada', sa.Date(), nullable=False),
    sa.Column('numero_documento', sqlmodel.sql.sqltypes.AutoString(length=44), nullable=True),
    sa.Column('observacao', sa.Text(), nullable=True),
    sa.Column('transacao_id', sa.Uuid(), nullable=True),
    sa.Column('created_by_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['fornecedor_id'], ['fornecedor.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['transacao_id'], ['transacao.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entradaestoque_fornecedor_id'), 'entradaestoque', ['fornecedor_id'], unique=False)

    op.create_table('custoajuste',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('entrada_id', sa.Uuid(), nullable=False),
    sa.Column('tipo', sa.Enum('frete', 'seguro', 'icms_st', 'ipi', 'despesa_acessoria', 'desconto_comercial', 'devolucao', 'correcao_documento', 'outros', name='tipocustoajuste'), nullable=False),
    sa.Column('valor', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('documento_referencia', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('observacao', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['entrada_id'], ['entradaestoque.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_custoajuste_entrada_id'), 'custoajuste', ['entrada_id'], unique=False)

    # Additive only. Do NOT issue an UPDATE against productitem here:
    # get_stock_prediction() infers consumption from productitem.updated_at,
    # so rewriting that column would corrupt the 90-day window.
    op.add_column('productitem', sa.Column('entrada_id', sa.Uuid(), nullable=True))
    op.add_column('productitem', sa.Column('custo_unitario_nf', sa.Numeric(precision=12, scale=4), nullable=True))
    op.create_index(op.f('ix_productitem_entrada_id'), 'productitem', ['entrada_id'], unique=False)
    op.create_foreign_key(
        'productitem_entrada_id_fkey',
        'productitem',
        'entradaestoque',
        ['entrada_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade():
    op.drop_constraint('productitem_entrada_id_fkey', 'productitem', type_='foreignkey')
    op.drop_index(op.f('ix_productitem_entrada_id'), table_name='productitem')
    op.drop_column('productitem', 'custo_unitario_nf')
    op.drop_column('productitem', 'entrada_id')
    op.drop_index(op.f('ix_custoajuste_entrada_id'), table_name='custoajuste')
    op.drop_table('custoajuste')
    op.drop_index(op.f('ix_entradaestoque_fornecedor_id'), table_name='entradaestoque')
    op.drop_table('entradaestoque')
    op.execute("DROP TYPE IF EXISTS tipocustoajuste")

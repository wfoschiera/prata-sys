"""add product_type, product, product_item tables

Revision ID: 8455314730e6
Revises: f3a68091d1fb
Create Date: 2026-03-14 12:07:39.791343

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '8455314730e6'
down_revision = 'f3a68091d1fb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('producttype',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('category', sa.Enum('tubos', 'conexoes', 'bombas', 'cabos', 'outros', name='productcategory'), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('unit_of_measure', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('category', 'name')
    )
    op.create_table('product',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('product_type_id', sa.Uuid(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('fornecedor_id', sa.Uuid(), nullable=True),
    sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['fornecedor_id'], ['fornecedor.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['product_type_id'], ['producttype.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('productitem',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('product_id', sa.Uuid(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=12, scale=4), nullable=False),
    sa.Column('status', sa.Enum('em_estoque', 'reservado', 'utilizado', name='productitemstatus'), nullable=False),
    sa.Column('service_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['service_id'], ['service.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('productitem')
    op.drop_table('product')
    op.drop_table('producttype')
    op.execute("DROP TYPE IF EXISTS productitemstatus")
    op.execute("DROP TYPE IF EXISTS productcategory")

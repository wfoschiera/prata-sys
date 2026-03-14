"""add product_id fk to serviceitem

Revision ID: 059651626f0f
Revises: 64482a5b8fae
Create Date: 2026-03-14 23:30:03.993859

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '059651626f0f'
down_revision = '64482a5b8fae'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('serviceitem', sa.Column('product_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        None, 'serviceitem', 'product', ['product_id'], ['id'], ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint(None, 'serviceitem', type_='foreignkey')
    op.drop_column('serviceitem', 'product_id')

"""add index on productitem.status, service.client_id and service.status

Revision ID: 58569e0fd0db
Revises: 8455314730e6
Create Date: 2026-03-14 20:28:09.280594

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '58569e0fd0db'
down_revision = '8455314730e6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f('ix_productitem_status'), 'productitem', ['status'], unique=False)
    op.create_index(op.f('ix_service_client_id'), 'service', ['client_id'], unique=False)
    op.create_index(op.f('ix_service_status'), 'service', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_service_status'), table_name='service')
    op.drop_index(op.f('ix_service_client_id'), table_name='service')
    op.drop_index(op.f('ix_productitem_status'), table_name='productitem')

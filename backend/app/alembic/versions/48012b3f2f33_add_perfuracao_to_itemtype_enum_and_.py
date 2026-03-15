"""add_perfuracao_to_itemtype_enum_and_index_service_type

Revision ID: 48012b3f2f33
Revises: fe56fa70289e
Create Date: 2026-03-15 15:04:32.655670

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '48012b3f2f33'
down_revision = 'c2d3e4f5a6b7'
branch_labels = None
depends_on = None


def upgrade():
    # Add 'perfuração' value to the itemtype enum
    op.execute("ALTER TYPE itemtype ADD VALUE IF NOT EXISTS 'perfuração'")

    # Add index on service.type for dashboard GROUP BY queries
    op.create_index('ix_service_type', 'service', ['type'], unique=False)


def downgrade():
    # Note: PostgreSQL does not support removing enum values.
    # Downgrade only removes the index.
    op.drop_index('ix_service_type', table_name='service')

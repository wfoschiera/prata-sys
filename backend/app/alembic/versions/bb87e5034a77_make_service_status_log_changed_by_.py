"""make service_status_log changed_by nullable with SET NULL

Revision ID: bb87e5034a77
Revises: c51700221dfa
Create Date: 2026-03-14 07:13:06.296420

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb87e5034a77'
down_revision = 'c51700221dfa'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('service_status_log', 'changed_by',
               existing_type=sa.UUID(),
               nullable=True)
    op.drop_constraint('service_status_log_changed_by_fkey', 'service_status_log', type_='foreignkey')
    op.create_foreign_key(None, 'service_status_log', 'user', ['changed_by'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint(None, 'service_status_log', type_='foreignkey')
    op.create_foreign_key('service_status_log_changed_by_fkey', 'service_status_log', 'user', ['changed_by'], ['id'])
    op.alter_column('service_status_log', 'changed_by',
               existing_type=sa.UUID(),
               nullable=False)

"""add service lifecycle fields and status log

Revision ID: c51700221dfa
Revises: ebef516f7ec1
Create Date: 2026-03-14 06:54:37.662167

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'c51700221dfa'
down_revision = 'ebef516f7ec1'
branch_labels = None
depends_on = None


def upgrade():
    # Create service_status_log table
    op.create_table(
        'service_status_log',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('service_id', sa.Uuid(), nullable=False),
        sa.Column('from_status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('to_status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('changed_by', sa.Uuid(), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.ForeignKeyConstraint(['changed_by'], ['user.id']),
        sa.ForeignKeyConstraint(['service_id'], ['service.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_service_status_log_service_id'),
        'service_status_log', ['service_id'], unique=False,
    )
    op.create_index(
        'ix_service_status_log_service_id_changed_at',
        'service_status_log', ['service_id', 'changed_at'],
    )

    # Add new columns to service table
    op.add_column('service', sa.Column('description', sa.Text(), nullable=True))
    op.add_column(
        'service',
        sa.Column('cancelled_reason', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    )


def downgrade():
    op.drop_column('service', 'cancelled_reason')
    op.drop_column('service', 'description')
    op.drop_index('ix_service_status_log_service_id_changed_at', table_name='service_status_log')
    op.drop_index(op.f('ix_service_status_log_service_id'), table_name='service_status_log')
    op.drop_table('service_status_log')

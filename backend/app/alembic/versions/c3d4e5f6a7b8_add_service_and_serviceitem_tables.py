"""add service and service_item tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'service',
        sa.Column('type', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('execution_address', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False, server_default='requested'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'serviceitem',
        sa.Column('item_type', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('service_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['service_id'], ['service.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('serviceitem')
    op.drop_table('service')

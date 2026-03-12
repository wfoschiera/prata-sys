"""add role to user drop item table

Revision ID: a1b2c3d4e5f6
Revises: 1a31ce608336
Create Date: 2026-03-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    # Add role column to user table
    op.add_column('user', sa.Column('role', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False, server_default='admin'))

    # Drop item table (template boilerplate, no production data)
    op.drop_table('item')


def downgrade():
    # Recreate item table
    op.create_table(
        'item',
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Remove role column
    op.drop_column('user', 'role')

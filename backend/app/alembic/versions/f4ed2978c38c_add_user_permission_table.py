"""add user_permission table

Revision ID: f4ed2978c38c
Revises: c3d4e5f6a7b8
Create Date: 2026-03-13 09:48:00.866159

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'f4ed2978c38c'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user_permission',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('permission', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'permission')
    )
    op.create_index(op.f('ix_user_permission_user_id'), 'user_permission', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_user_permission_user_id'), table_name='user_permission')
    op.drop_table('user_permission')

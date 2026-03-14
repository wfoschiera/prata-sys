"""add used_password_reset_token table

Revision ID: 64482a5b8fae
Revises: 58569e0fd0db
Create Date: 2026-03-14 23:23:52.388291

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '64482a5b8fae'
down_revision = '58569e0fd0db'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'used_password_reset_token',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('token_hash', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_used_password_reset_token_token_hash'),
        'used_password_reset_token',
        ['token_hash'],
        unique=True,
    )


def downgrade():
    op.drop_index(
        op.f('ix_used_password_reset_token_token_hash'),
        table_name='used_password_reset_token',
    )
    op.drop_table('used_password_reset_token')

"""add_token_version_to_user

Revision ID: 6134a479de6e
Revises: 48012b3f2f33
Create Date: 2026-07-12 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '6134a479de6e'
down_revision = '48012b3f2f33'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user',
        sa.Column(
            'token_version', sa.Integer(), nullable=False, server_default='0'
        ),
    )


def downgrade():
    op.drop_column('user', 'token_version')

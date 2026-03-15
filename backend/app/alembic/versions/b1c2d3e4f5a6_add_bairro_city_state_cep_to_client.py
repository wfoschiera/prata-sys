"""add bairro, city, state, cep to client

Revision ID: b1c2d3e4f5a6
Revises: 059651626f0f
Create Date: 2026-03-15 00:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision = 'b1c2d3e4f5a6'
down_revision = '059651626f0f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('client', sa.Column('bairro', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True))
    op.add_column('client', sa.Column('city', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True))
    op.add_column('client', sa.Column('state', sqlmodel.sql.sqltypes.AutoString(length=2), nullable=True))
    op.add_column('client', sa.Column('cep', sqlmodel.sql.sqltypes.AutoString(length=9), nullable=True))


def downgrade():
    op.drop_column('client', 'cep')
    op.drop_column('client', 'state')
    op.drop_column('client', 'city')
    op.drop_column('client', 'bairro')

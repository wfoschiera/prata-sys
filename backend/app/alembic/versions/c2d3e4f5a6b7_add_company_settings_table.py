"""add company_settings table

Revision ID: c2d3e4f5a6b7
Revises: 059651626f0f
Create Date: 2026-03-15 00:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision = 'c2d3e4f5a6b7'
down_revision = 'a3450ecbfd60'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('company_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('cnpj', sqlmodel.sql.sqltypes.AutoString(length=18), nullable=True),
        sa.Column('inscricao_municipal', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('address', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('logo_url', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('company_settings')

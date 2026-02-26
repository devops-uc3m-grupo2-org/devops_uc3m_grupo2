"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('email', sa.String, nullable=False, unique=True),
    )

    op.create_table(
        'tickets',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('description', sa.String, nullable=False),
        sa.Column('tags', sa.JSON, nullable=False),
    )


def downgrade() -> None:
    op.drop_table('tickets')
    op.drop_table('users')

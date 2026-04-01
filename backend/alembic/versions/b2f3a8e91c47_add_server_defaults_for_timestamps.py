"""Add server defaults for timestamp columns

Revision ID: b2f3a8e91c47
Revises: caa1d6630b66
Create Date: 2026-04-01 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f3a8e91c47'
down_revision: Union[str, Sequence[str], None] = 'caa1d6630b66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'created_at', server_default=sa.func.now())
    op.alter_column('products', 'created_at', server_default=sa.func.now())
    op.alter_column('products', 'updated_at', server_default=sa.func.now())
    op.alter_column('competitor_urls', 'created_at', server_default=sa.func.now())
    op.alter_column('price_histories', 'scraped_at', server_default=sa.func.now())
    op.alter_column('price_histories', 'created_at', server_default=sa.func.now())


def downgrade() -> None:
    op.alter_column('price_histories', 'created_at', server_default=None)
    op.alter_column('price_histories', 'scraped_at', server_default=None)
    op.alter_column('competitor_urls', 'created_at', server_default=None)
    op.alter_column('products', 'updated_at', server_default=None)
    op.alter_column('products', 'created_at', server_default=None)
    op.alter_column('users', 'created_at', server_default=None)

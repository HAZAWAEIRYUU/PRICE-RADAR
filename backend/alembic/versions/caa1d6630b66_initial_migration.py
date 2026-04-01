"""Initial migration

Revision ID: caa1d6630b66
Revises:
Create Date: 2026-04-01 11:28:17.178743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'caa1d6630b66'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('plan', sa.String(), server_default='free', nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_stripe_customer_id', 'users', ['stripe_customer_id'])
    op.create_index('ix_users_stripe_subscription_id', 'users', ['stripe_subscription_id'])

    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('own_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_products_id', 'products', ['id'])
    op.create_index('ix_products_user_id', 'products', ['user_id'])
    op.create_index('ix_products_product_name', 'products', ['product_name'])

    op.create_table(
        'competitor_urls',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=True),
        sa.Column('competitor_name', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_competitor_urls_id', 'competitor_urls', ['id'])

    op.create_table(
        'price_histories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('competitor_url_id', sa.Integer(), sa.ForeignKey('competitor_urls.id'), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=True),
        sa.Column('stock_status', sa.String(), server_default='在庫あり', nullable=True),
        sa.Column('scraped_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_price_histories_id', 'price_histories', ['id'])


def downgrade() -> None:
    op.drop_table('price_histories')
    op.drop_table('competitor_urls')
    op.drop_table('products')
    op.drop_table('users')

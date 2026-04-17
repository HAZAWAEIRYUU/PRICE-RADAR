"""Add processed_stripe_events idempotency table

Revision ID: e8b41d5a29c3
Revises: d5a3f7e92b18
Create Date: 2026-04-17 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e8b41d5a29c3'
down_revision: Union[str, Sequence[str], None] = 'd5a3f7e92b18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'processed_stripe_events',
        sa.Column('event_id', sa.String(), primary_key=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('ALTER TABLE public.processed_stripe_events ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    op.drop_table('processed_stripe_events')

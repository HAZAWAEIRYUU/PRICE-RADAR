"""Add LINE integration and notification settings

Revision ID: c4e7d2a91f3b
Revises: b2f3a8e91c47
Create Date: 2026-04-14 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e7d2a91f3b'
down_revision: Union[str, Sequence[str], None] = 'b2f3a8e91c47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend users with LINE + notification fields
    op.add_column('users', sa.Column('line_user_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('line_display_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('notification_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('users', sa.Column('notify_price_loss', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('users', sa.Column('notify_price_recovery', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('users', sa.Column('notify_stock_change', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('users', sa.Column('notify_subscription', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.create_index('ix_users_line_user_id', 'users', ['line_user_id'], unique=True)

    # Notification logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('previous_state', sa.String(), nullable=True),
        sa.Column('current_state', sa.String(), nullable=True),
        sa.Column('line_message_id', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_notification_logs_id', 'notification_logs', ['id'])
    op.create_index('ix_notification_logs_user_id', 'notification_logs', ['user_id'])
    op.create_index('ix_notification_logs_event_type', 'notification_logs', ['event_type'])
    op.create_index('ix_notification_logs_entity_id', 'notification_logs', ['entity_id'])
    op.create_index('ix_notification_logs_sent_at', 'notification_logs', ['sent_at'])


def downgrade() -> None:
    op.drop_index('ix_notification_logs_sent_at', table_name='notification_logs')
    op.drop_index('ix_notification_logs_entity_id', table_name='notification_logs')
    op.drop_index('ix_notification_logs_event_type', table_name='notification_logs')
    op.drop_index('ix_notification_logs_user_id', table_name='notification_logs')
    op.drop_index('ix_notification_logs_id', table_name='notification_logs')
    op.drop_table('notification_logs')

    op.drop_index('ix_users_line_user_id', table_name='users')
    op.drop_column('users', 'notify_subscription')
    op.drop_column('users', 'notify_stock_change')
    op.drop_column('users', 'notify_price_recovery')
    op.drop_column('users', 'notify_price_loss')
    op.drop_column('users', 'notification_enabled')
    op.drop_column('users', 'line_display_name')
    op.drop_column('users', 'line_user_id')

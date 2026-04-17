"""Enable RLS on public tables (Supabase advisor fix)

Revision ID: d5a3f7e92b18
Revises: c4e7d2a91f3b
Create Date: 2026-04-17 10:00:00.000000

Supabase's PostgREST auto-exposes every public table through the anon/authenticated
JWT roles. Without RLS those rows are reachable with just the anon key. This
migration enables row level security on every app table so PostgREST requests
default-deny. The FastAPI backend connects with the database owner role, which
is exempt from RLS (we intentionally do NOT use FORCE ROW LEVEL SECURITY), so
application queries continue to work unchanged.

No policies are created: we have no client that should talk to these tables via
PostgREST, so default-deny is the desired behaviour.

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd5a3f7e92b18'
down_revision: Union[str, Sequence[str], None] = 'c4e7d2a91f3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = (
    'users',
    'products',
    'competitor_urls',
    'price_histories',
    'notification_logs',
)


def upgrade() -> None:
    bind = op.get_bind()
    # Skip on non-Postgres backends (e.g. SQLite test database)
    if bind.dialect.name != 'postgresql':
        return
    for table in TABLES:
        op.execute(f'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return
    for table in reversed(TABLES):
        op.execute(f'ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY')

"""Idempotent Row Level Security enforcement.

The RLS-enable migration (d5a3f7e92b18) runs once per deploy. If RLS
is later turned off out-of-band — Supabase dashboard Table Editor
toggle, point-in-time recovery, a new database branch, or a manual
`ALTER TABLE ... DISABLE ROW LEVEL SECURITY` — no existing code path
would put it back. Call `ensure_rls_enabled()` at app startup to
re-assert the invariant on every process boot.

`ALTER TABLE ... ENABLE ROW LEVEL SECURITY` is a no-op when the
table already has RLS on, so running this on every boot is cheap.
"""
from __future__ import annotations

import logging
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger("priceradar.rls")

# Every public table PostgREST would auto-expose. Keep this in sync
# with the models.py table names; if a new table is added, add it
# here too (and to the ALTER statement in its Alembic migration).
PUBLIC_TABLES: tuple[str, ...] = (
    "users",
    "products",
    "competitor_urls",
    "price_histories",
    "notification_logs",
    "processed_stripe_events",
)


def ensure_rls_enabled(engine: Engine, tables: Iterable[str] = PUBLIC_TABLES) -> None:
    """Run ENABLE ROW LEVEL SECURITY on every listed table.

    Silently skips non-Postgres backends (local SQLite dev). Never
    raises — a connection error here shouldn't crash app startup.
    """
    if engine.dialect.name != "postgresql":
        logger.debug("RLS guard: %s dialect — skipping", engine.dialect.name)
        return

    changed: list[str] = []
    try:
        with engine.connect() as conn:
            for table in tables:
                # Safe against SQL injection: table names are a fixed, hardcoded
                # constant list — never user-supplied.
                conn.execute(text(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY"))
                changed.append(table)
            conn.commit()
    except Exception as e:
        logger.warning(
            "RLS guard failed to assert on one or more tables (non-fatal): %s "
            "(processed before failure: %s)",
            e, changed,
        )
        return

    logger.info("RLS guard: ensured RLS enabled on %s public tables", len(changed))

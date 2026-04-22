"""Tests for the startup RLS guard."""
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine

from services.rls_guard import PUBLIC_TABLES, ensure_rls_enabled


def test_skips_non_postgres_backends():
    # SQLite (used by tests and local dev) doesn't support RLS and
    # shouldn't be touched.
    engine = create_engine("sqlite:///:memory:")
    ensure_rls_enabled(engine)  # must not raise


def test_runs_alter_on_every_listed_table():
    # Mock engine that pretends to be postgres and records executed SQL.
    executed: list[str] = []

    class FakeConn:
        def execute(self, clause):
            executed.append(str(clause))

        def commit(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    fake_engine = MagicMock()
    fake_engine.dialect.name = "postgresql"
    fake_engine.connect.return_value = FakeConn()

    ensure_rls_enabled(fake_engine)

    # One ALTER per table, and every table is mentioned.
    assert len(executed) == len(PUBLIC_TABLES)
    for table in PUBLIC_TABLES:
        assert any(
            f"public.{table} ENABLE ROW LEVEL SECURITY" in stmt for stmt in executed
        ), f"{table} was not asserted. got: {executed}"


def test_swallows_exceptions():
    # If the DB is briefly unreachable at startup we must not crash
    # the whole app.
    fake_engine = MagicMock()
    fake_engine.dialect.name = "postgresql"
    fake_engine.connect.side_effect = RuntimeError("boom")

    # No assertion — just "did not raise".
    ensure_rls_enabled(fake_engine)


def test_public_tables_matches_models():
    # Guard against drift: every public table declared by our ORM must
    # be in PUBLIC_TABLES, otherwise the guard will silently miss new
    # tables that need RLS.
    import models

    orm_tables = {
        t.__tablename__ for t in models.Base.__subclasses__() if hasattr(t, "__tablename__")
    }
    missing = orm_tables - set(PUBLIC_TABLES)
    assert not missing, (
        f"ORM declares tables not in rls_guard.PUBLIC_TABLES: {missing}. "
        "Add them to PUBLIC_TABLES and create a migration enabling RLS."
    )

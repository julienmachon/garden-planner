"""
Migration tests.

Verifies that the Alembic migrations run cleanly on a fresh database
and produce the expected schema. This catches broken migrations before
they reach users with existing data.
"""
import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


ALEMBIC_INI = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
)

EXPECTED_TABLES = {"planting_materials", "plantings", "events", "harvests"}


@pytest.fixture
def alembic_engine(tmp_path):
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    yield engine
    engine.dispose()


def test_upgrade_creates_all_tables(alembic_engine):
    inspector = inspect(alembic_engine)
    tables = set(inspector.get_table_names())
    assert EXPECTED_TABLES <= tables, (
        f"Missing tables after migration: {EXPECTED_TABLES - tables}"
    )


def test_downgrade_removes_all_tables(alembic_engine, tmp_path):
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.downgrade(cfg, "base")

    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names()) - {"alembic_version"}
    assert not tables, f"Tables still present after full downgrade: {tables}"
    engine.dispose()


def test_upgrade_is_idempotent(alembic_engine, tmp_path):
    """Running upgrade head twice must not raise or corrupt the schema."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")  # second run — must be a no-op

    inspector = inspect(create_engine(db_url))
    assert EXPECTED_TABLES <= set(inspector.get_table_names())

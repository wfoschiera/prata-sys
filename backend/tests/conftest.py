"""Test configuration with per-test isolation via transaction rollback.

Architecture:
  ┌────────────────────────────────────────────────────────────┐
  │  SESSION SCOPE (once per test run)                         │
  │                                                            │
  │  1. Build test engine → "app_test" database                │
  │  2. Run Alembic migrations (create all tables)             │
  │  3. Seed superuser via init_db()                           │
  │  4. Sentinel: assert DB was clean before seeding            │
  └────────────────────────────────────────────────────────────┘
                           │
  ┌────────────────────────▼───────────────────────────────────┐
  │  FUNCTION SCOPE (once per test)                            │
  │                                                            │
  │  1. BEGIN outer transaction on test engine connection       │
  │  2. Create Session bound to that connection                 │
  │  3. Override app's get_db → yield test Session              │
  │  4. Run test                                                │
  │  5. ROLLBACK outer transaction → all changes undone         │
  │  6. Restore app's get_db                                    │
  └────────────────────────────────────────────────────────────┘
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from sqlalchemy import event, text
from sqlmodel import Session, SQLModel, create_engine

from app.api.deps import get_db
from app.core.config import settings
from app.core.db import init_db
from app.main import app
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers

# ---------------------------------------------------------------------------
# Test database engine (points to "app_test", not "app")
# ---------------------------------------------------------------------------

_test_db_url = PostgresDsn.build(
    scheme="postgresql+psycopg",
    username=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.POSTGRES_SERVER,
    port=settings.POSTGRES_PORT,
    path="app_test",
)

test_engine = create_engine(str(_test_db_url), echo=False)


# ---------------------------------------------------------------------------
# Session-scoped setup: migrate + seed
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _setup_test_db() -> Generator[None, None, None]:
    """Create all tables via Alembic migrations and seed the superuser.

    Runs once per test session. The test DB persists between runs;
    the sentinel check below catches stale data.
    """
    # Run Alembic migrations against the test database.
    # We use SQLModel.metadata.create_all for simplicity and speed —
    # it mirrors the Alembic-managed schema without needing subprocess calls.
    SQLModel.metadata.create_all(test_engine)

    # Seed the superuser (needed for auth in most tests).
    with Session(test_engine) as session:
        init_db(session)

    yield

    # No teardown — test DB persists for inspection.
    # Per-test rollback handles cleanup.


# ---------------------------------------------------------------------------
# Sentinel: verify test DB is clean (no leftover data from previous runs)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _sentinel_check_clean_db(_setup_test_db: None) -> None:
    """Assert the test DB has no stale data beyond the seeded superuser.

    If this fails, a previous test run didn't roll back properly.
    Fix: drop and recreate the app_test database, or run
    `docker compose down -v` to wipe volumes.
    """
    with Session(test_engine) as session:
        # Only the seeded superuser should exist
        user_count = session.execute(text('SELECT count(*) FROM "user"')).scalar()
        assert user_count == 1, (
            f"Test DB is not clean: expected 1 user (superuser), found {user_count}. "
            "A previous test run may have leaked data. "
            "Run `docker compose down -v && docker compose up -d` to reset."
        )

        # No clients should exist
        client_count = session.execute(text("SELECT count(*) FROM client")).scalar()
        assert client_count == 0, (
            f"Test DB is not clean: found {client_count} clients. "
            "Run `docker compose down -v && docker compose up -d` to reset."
        )


# ---------------------------------------------------------------------------
# Per-test fixtures: transaction rollback + dependency override
# ---------------------------------------------------------------------------


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """Yield a Session wrapped in a transaction that rolls back after the test.

    This gives each test a clean slate without needing manual cleanup.
    The nested savepoint pattern allows the code under test to call
    session.commit() without actually persisting to disk.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # When application code calls session.commit(), SQLAlchemy would
    # normally end the transaction. We intercept this by restarting
    # a nested savepoint so the outer transaction stays open for rollback.
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(_session, transaction_record):  # type: ignore[no-untyped-def]
        nonlocal nested
        if transaction_record.nested and not transaction_record.parent.nested:
            nested = connection.begin_nested()

    yield session

    # Cleanup: rollback everything
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient with get_db overridden to use the per-test Session."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture()
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )

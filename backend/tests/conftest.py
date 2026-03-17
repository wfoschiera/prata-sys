"""Test configuration with per-test isolation via transaction rollback.

Architecture:
  ┌────────────────────────────────────────────────────────────────┐
  │  SESSION SCOPE (once per test run)                             │
  │                                                                │
  │  1. Build test engine → "app_test" database                    │
  │  2. Create all tables via SQLModel.metadata.create_all         │
  │  3. Seed superuser + role users (admin, finance, client)       │
  │  4. Generate auth tokens for each role (reused across tests)   │
  │  5. Sentinel: assert DB was clean before seeding               │
  └────────────────────────────────────────────────────────────────┘
                           │
  ┌────────────────────────▼───────────────────────────────────────┐
  │  FUNCTION SCOPE (once per test)                                │
  │                                                                │
  │  1. BEGIN outer transaction on test engine connection           │
  │  2. Create Session bound to that connection                    │
  │  3. Override app's get_db → yield test Session                 │
  │  4. Run test                                                   │
  │  5. ROLLBACK outer transaction → all changes undone            │
  │  6. Restore app's get_db                                       │
  └────────────────────────────────────────────────────────────────┘

Session-scoped role users persist across tests (like the superuser).
Per-test changes are rolled back via the savepoint pattern.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from sqlalchemy import event, text
from sqlmodel import Session, SQLModel, create_engine

from app import crud
from app.api.deps import get_db
from app.core.config import settings
from app.main import app
from app.models import UserCreate, UserRole

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
# Well-known test user credentials (seeded once, reused across all tests)
# ---------------------------------------------------------------------------

_ROLE_USERS = {
    "admin": {
        "email": "test-admin@prata-sys.example.com",
        "password": "adminpass12345678",  # gitleaks:allow (test-only credential)
        "role": UserRole.admin,
    },
    "finance": {
        "email": "test-finance@prata-sys.example.com",
        "password": "financepass12345678",  # gitleaks:allow (test-only credential)
        "role": UserRole.finance,
    },
    "client": {
        "email": "test-client@prata-sys.example.com",
        "password": "clientpass12345678",  # gitleaks:allow (test-only credential)
        "role": UserRole.client,
    },
}

# Number of seeded users: 1 superuser + 3 role users
_SEEDED_USER_COUNT = 1 + len(_ROLE_USERS)


# ---------------------------------------------------------------------------
# Session-scoped setup: migrate + seed
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _setup_test_db() -> Generator[None, None, None]:
    """Create all tables and seed the superuser + role users.

    Runs once per test session. The test DB persists between runs;
    the sentinel check below catches stale data.
    """
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        # Seed superuser (idempotent — init_db checks existence)
        from app.core.db import init_db

        init_db(session)

        # Seed role users (idempotent — skip if already exists)
        for info in _ROLE_USERS.values():
            existing = crud.get_user_by_email(session=session, email=info["email"])
            if not existing:
                user_in = UserCreate(
                    email=info["email"],
                    password=info["password"],
                    role=info["role"],
                )
                crud.create_user(session=session, user_create=user_in)

    yield


# ---------------------------------------------------------------------------
# Sentinel: verify test DB is clean (no leftover data from previous runs)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _sentinel_check_clean_db(_setup_test_db: None) -> None:
    """Assert the test DB has no stale data beyond the seeded users.

    If this fails, a previous test run didn't roll back properly.
    Fix: drop and recreate the app_test database, or run
    `docker compose down -v` to wipe volumes.
    """
    with Session(test_engine) as session:
        user_count = session.execute(text('SELECT count(*) FROM "user"')).scalar()
        assert user_count == _SEEDED_USER_COUNT, (
            f"Test DB is not clean: expected {_SEEDED_USER_COUNT} users "
            f"(superuser + role users), found {user_count}. "
            "A previous test run may have leaked data. "
            "Run `docker compose down -v && docker compose up -d` to reset."
        )

        client_count = session.execute(text("SELECT count(*) FROM client")).scalar()
        assert client_count == 0, (
            f"Test DB is not clean: found {client_count} clients. "
            "Run `docker compose down -v && docker compose up -d` to reset."
        )


# ---------------------------------------------------------------------------
# Session-scoped auth tokens (generated once, reused across all tests)
# ---------------------------------------------------------------------------


def _session_scoped_test_client() -> TestClient:
    """Create a TestClient with get_db overridden to use the test engine.

    This is needed because the session-scoped token fixtures run before
    the per-test ``client`` fixture, and the app's default engine points
    to the main ``app`` database, not ``app_test``.
    """

    def _override_get_db() -> Generator[Session, None, None]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app)


def _login_for_token(tc: TestClient, email: str, password: str) -> dict[str, str]:
    """Log in via the API and return Authorization headers."""
    r = tc.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )
    assert r.status_code == 200, f"Login failed for {email}: {r.text}"
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def superuser_token_headers(_setup_test_db: None) -> dict[str, str]:
    """Auth headers for the superuser (session-scoped, generated once)."""
    with _session_scoped_test_client() as tc:
        return _login_for_token(
            tc, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
        )


@pytest.fixture(scope="session")
def admin_token_headers(_setup_test_db: None) -> dict[str, str]:
    """Auth headers for the admin role user (session-scoped)."""
    info = _ROLE_USERS["admin"]
    with _session_scoped_test_client() as tc:
        return _login_for_token(tc, info["email"], info["password"])


@pytest.fixture(scope="session")
def finance_token_headers(_setup_test_db: None) -> dict[str, str]:
    """Auth headers for the finance role user (session-scoped)."""
    info = _ROLE_USERS["finance"]
    with _session_scoped_test_client() as tc:
        return _login_for_token(tc, info["email"], info["password"])


@pytest.fixture(scope="session")
def client_token_headers(_setup_test_db: None) -> dict[str, str]:
    """Auth headers for the client role user (session-scoped)."""
    info = _ROLE_USERS["client"]
    with _session_scoped_test_client() as tc:
        return _login_for_token(tc, info["email"], info["password"])


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

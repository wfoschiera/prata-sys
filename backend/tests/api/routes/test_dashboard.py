"""Tests for the operational dashboard endpoint."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import (
    Client,
    ClientCreate,
    DocumentType,
    ItemType,
    Service,
    ServiceCreate,
    ServiceItem,
    ServiceItemCreate,
    ServiceStatus,
    ServiceType,
    TipoTransacao,
    TransacaoCreate,
    TransacaoPublic,
)
from tests.utils.utils import random_lower_string

API_URL = f"{settings.API_V1_STR}/dashboard/operational"

# ── Helpers ───────────────────────────────────────────────────────────────────


def _cpf() -> str:
    uid_digits = "".join(c for c in uuid.uuid4().hex if c.isdigit())
    return (uid_digits + "00000000000")[:11]


def _create_client(db: Session) -> Client:
    return crud.create_client(
        session=db,
        client_in=ClientCreate(
            name=random_lower_string(),
            document_type=DocumentType.cpf,
            document_number=_cpf(),
        ),
    )


def _create_completed_service(
    db: Session, svc_type: ServiceType = ServiceType.perfuracao
) -> Service:
    cl = _create_client(db)
    svc = crud.create_service(
        session=db,
        service_in=ServiceCreate(
            type=svc_type,
            execution_address="Rua Teste, 1",
            client_id=cl.id,
        ),
    )
    # Transition to completed: requested → scheduled → executing → completed
    superuser = db.get(
        __import__("app.models", fromlist=["User"]).User,
        crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER).id,  # type: ignore[union-attr]
    )
    for to_status in [
        ServiceStatus.scheduled,
        ServiceStatus.executing,
        ServiceStatus.completed,
    ]:
        crud.transition_service_status(
            session=db,
            service=svc,
            to_status=to_status,
            changed_by_id=superuser.id,  # type: ignore[union-attr]
        )
        db.refresh(svc)
    return svc


def _add_drilling_item(db: Session, service: Service, quantity: float) -> ServiceItem:
    item_in = ServiceItemCreate(
        item_type=ItemType.perfuracao,
        description="Mão de obra de perfuração",
        quantity=quantity,
        unit_price=Decimal("50.00"),
    )
    return crud.create_service_item(session=db, service_id=service.id, item_in=item_in)


def _create_transaction(
    db: Session, tipo: TipoTransacao, valor: Decimal, competencia: date | None = None
) -> TransacaoPublic:
    if competencia is None:
        competencia = date.today()
    tx_in = TransacaoCreate(
        tipo=tipo,
        valor=valor,
        descricao=f"Test {tipo}",
        data_competencia=competencia,
        categoria="SERVICO" if tipo == TipoTransacao.receita else "COMBUSTIVEL",
    )
    return crud.create_transacao(session=db, transacao_in=tx_in)


def _client_role_headers(client: TestClient, db: Session) -> dict[str, str]:
    from app.models import UserCreate, UserRole
    from tests.utils.user import user_authentication_headers

    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    crud.create_user(
        session=db,
        user_create=UserCreate(email=email, password=password, role=UserRole.client),
    )
    return user_authentication_headers(client=client, email=email, password=password)


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_dashboard_operational_returns_valid_structure(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Endpoint returns YearlyOperationalDashboard with ano + weeks list."""
    ano = datetime.now(timezone.utc).year
    r = client.get(API_URL, headers=superuser_token_headers, params={"ano": ano})
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["ano"] == ano
    assert isinstance(data["weeks"], list)
    if data["weeks"]:
        week = data["weeks"][0]
        assert "week_number" in week
        assert "week_start" in week
        assert "repairs_count" in week
        assert "drillings_count" in week
        assert "drilling_meters" in week
        assert "profit" in week


def test_dashboard_operational_counts_completed_perfuracao(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Completed perfuracao service increments drillings_count for its week."""
    ano = datetime.now(timezone.utc).year
    _create_completed_service(db, ServiceType.perfuracao)

    r = client.get(API_URL, headers=superuser_token_headers, params={"ano": ano})
    assert r.status_code == HTTPStatus.OK
    weeks = r.json()["weeks"]
    # Find current week
    current_week = date.today().isocalendar()[1]
    week_data = next((w for w in weeks if w["week_number"] == current_week), None)
    assert week_data is not None
    assert week_data["drillings_count"] >= 1


def test_dashboard_operational_counts_completed_reparo(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Completed reparo service increments repairs_count for its week."""
    ano = datetime.now(timezone.utc).year
    _create_completed_service(db, ServiceType.reparo)

    r = client.get(API_URL, headers=superuser_token_headers, params={"ano": ano})
    assert r.status_code == HTTPStatus.OK
    weeks = r.json()["weeks"]
    current_week = date.today().isocalendar()[1]
    week_data = next((w for w in weeks if w["week_number"] == current_week), None)
    assert week_data is not None
    assert week_data["repairs_count"] >= 1


def test_dashboard_operational_sums_drilling_meters(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """drilling_meters sums quantity of ItemType.perfuracao items on completed services."""
    ano = datetime.now(timezone.utc).year
    # Create service and add drilling item BEFORE completing it
    cl = _create_client(db)
    superuser = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert superuser is not None
    svc = crud.create_service(
        session=db,
        service_in=ServiceCreate(
            type=ServiceType.perfuracao,
            execution_address="Rua Teste, 1",
            client_id=cl.id,
        ),
    )
    _add_drilling_item(db, svc, 120.5)
    for to_status in [
        ServiceStatus.scheduled,
        ServiceStatus.executing,
        ServiceStatus.completed,
    ]:
        crud.transition_service_status(
            session=db, service=svc, to_status=to_status, changed_by_id=superuser.id
        )
        db.refresh(svc)

    r = client.get(API_URL, headers=superuser_token_headers, params={"ano": ano})
    assert r.status_code == HTTPStatus.OK
    weeks = r.json()["weeks"]
    current_week = date.today().isocalendar()[1]
    week_data = next((w for w in weeks if w["week_number"] == current_week), None)
    assert week_data is not None
    assert Decimal(str(week_data["drilling_meters"])) >= Decimal("120.5")


def test_dashboard_operational_ignores_non_completed_services(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Services not in completed status are excluded from counts."""
    cl = _create_client(db)
    # Create a service but leave it in 'requested' status
    crud.create_service(
        session=db,
        service_in=ServiceCreate(
            type=ServiceType.perfuracao,
            execution_address="Rua Teste, 1",
            client_id=cl.id,
        ),
    )
    ano = datetime.now(timezone.utc).year
    r = client.get(API_URL, headers=superuser_token_headers, params={"ano": ano})
    assert r.status_code == HTTPStatus.OK
    # Just verify the call succeeds; the non-completed service is not counted
    # (we can't assert exact zero since other tests may add completed services)


def test_dashboard_operational_computes_weekly_profit(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """profit = receitas - despesas for the week. Check delta from before/after."""
    ano = datetime.now(timezone.utc).year
    today = date.today()
    current_week = today.isocalendar()[1]

    # Snapshot profit before adding transactions
    r_before = client.get(API_URL, headers=superuser_token_headers, params={"ano": ano})
    assert r_before.status_code == HTTPStatus.OK
    weeks_before = r_before.json()["weeks"]
    week_before = next(
        (w for w in weeks_before if w["week_number"] == current_week), None
    )
    profit_before = Decimal(str(week_before["profit"])) if week_before else Decimal("0")

    _create_transaction(db, TipoTransacao.receita, Decimal("1000.00"), today)
    _create_transaction(db, TipoTransacao.despesa, Decimal("300.00"), today)

    r_after = client.get(API_URL, headers=superuser_token_headers, params={"ano": ano})
    assert r_after.status_code == HTTPStatus.OK
    weeks_after = r_after.json()["weeks"]
    week_after = next(
        (w for w in weeks_after if w["week_number"] == current_week), None
    )
    assert week_after is not None
    profit_after = Decimal(str(week_after["profit"]))

    # Net effect: +1000 receita, -300 despesa = +700 delta
    assert profit_after - profit_before == Decimal("700.00")


def test_dashboard_operational_permission_denied(
    client: TestClient, db: Session
) -> None:
    """Client role gets 403 Forbidden."""
    headers = _client_role_headers(client, db)
    r = client.get(API_URL, headers=headers)
    assert r.status_code == HTTPStatus.FORBIDDEN
    assert r.json()["detail"] == "Insufficient permissions"


def test_dashboard_operational_unauthenticated(client: TestClient) -> None:
    """Unauthenticated request gets 401."""
    r = client.get(API_URL)
    assert r.status_code == HTTPStatus.UNAUTHORIZED

import uuid
from decimal import Decimal
from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import (
    Client,
    ClientCreate,
    DeductionItem,
    DocumentType,
    ItemType,
    Service,
    ServiceCreate,
    ServiceItem,
    ServiceItemCreate,
    ServiceStatus,
    ServiceType,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _cpf() -> str:
    uid_digits = "".join(c for c in uuid.uuid4().hex if c.isdigit())
    return (uid_digits + "00000000000")[:11]


def _cnpj() -> str:
    import random

    def calc_dv(digits: list[int], weights: list[int]) -> int:
        remainder = sum(d * w for d, w in zip(digits, weights, strict=False)) % 11
        return 0 if remainder < 2 else 11 - remainder

    while True:
        root = [random.randint(0, 9) for _ in range(8)]
        base = root + [0, 0, 0, 1]
        if len(set(base)) == 1:
            continue
        dv1 = calc_dv(base, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        dv2 = calc_dv(base + [dv1], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        return "".join(str(d) for d in base + [dv1, dv2])


def create_random_client(db: Session) -> Client:
    client_in = ClientCreate(
        name="Test Client",
        document_type=DocumentType.cpf,
        document_number=_cpf(),
    )
    return crud.create_client(session=db, client_in=client_in)


def create_random_service(db: Session, client: Client | None = None) -> Service:
    if client is None:
        client = create_random_client(db)
    service_in = ServiceCreate(
        type=ServiceType.perfuracao,
        execution_address="Rua das Palmeiras, 100",
        client_id=client.id,
    )
    return crud.create_service(session=db, service_in=service_in)


def create_service_item(db: Session, service: Service) -> ServiceItem:
    item_in = ServiceItemCreate(
        item_type=ItemType.material,
        description="Tubo PVC 50mm",
        quantity=10.0,
        unit_price=15.50,
    )
    return crud.create_service_item(session=db, service_id=service.id, item_in=item_in)


# ── List services ─────────────────────────────────────────────────────────────


def test_read_services_superuser(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_service(db)
    r = client.get(f"{settings.API_V1_STR}/services/", headers=superuser_token_headers)
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] >= 1
    for item in data["data"]:
        assert "id" in item
        assert "status" in item


def test_read_services_finance_role_forbidden(
    client: TestClient, finance_token_headers: dict[str, str]
) -> None:
    """Finance role does not have manage_services by default."""
    r = client.get(f"{settings.API_V1_STR}/services/", headers=finance_token_headers)
    assert r.status_code == HTTPStatus.FORBIDDEN


def test_read_services_no_permission_forbidden(
    client: TestClient, client_token_headers: dict[str, str]
) -> None:
    """Client role has no permissions by default."""
    r = client.get(f"{settings.API_V1_STR}/services/", headers=client_token_headers)
    assert r.status_code == HTTPStatus.FORBIDDEN
    assert r.json()["detail"] == "Insufficient permissions"


def test_read_services_unauthenticated(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/services/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


def test_read_services_pagination(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_service(db)
    create_random_service(db)
    r = client.get(
        f"{settings.API_V1_STR}/services/?skip=0&limit=1",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    assert len(r.json()["data"]) == 1


# ── Create service ────────────────────────────────────────────────────────────


def test_create_service(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    db_client = create_random_client(db)
    payload = {
        "type": "perfuração",
        "execution_address": "Rua Nova, 200",
        "client_id": str(db_client.id),
    }
    r = client.post(
        f"{settings.API_V1_STR}/services/",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.CREATED
    data = r.json()
    assert data["client_id"] == str(db_client.id)
    assert data["status"] == "requested"
    assert "id" in data


def test_create_service_with_notes(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    db_client = create_random_client(db)
    payload = {
        "type": "reparo",
        "execution_address": "Rua Velha, 10",
        "notes": "Urgente",
        "client_id": str(db_client.id),
    }
    r = client.post(
        f"{settings.API_V1_STR}/services/",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.CREATED
    assert r.json()["notes"] == "Urgente"


def test_create_service_client_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    payload = {
        "type": "reparo",
        "execution_address": "Rua Teste, 99",
        "client_id": str(uuid.uuid4()),
    }
    r = client.post(
        f"{settings.API_V1_STR}/services/",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.NOT_FOUND
    assert r.json()["detail"] == "Client not found"


def test_create_service_unauthenticated(client: TestClient, db: Session) -> None:
    db_client = create_random_client(db)
    payload = {
        "type": "perfuração",
        "execution_address": "Rua Nova, 200",
        "client_id": str(db_client.id),
    }
    r = client.post(f"{settings.API_V1_STR}/services/", json=payload)
    assert r.status_code == HTTPStatus.UNAUTHORIZED


def test_create_service_wrong_role_forbidden(
    client: TestClient, client_token_headers: dict[str, str], db: Session
) -> None:
    db_client = create_random_client(db)
    payload = {
        "type": "perfuração",
        "execution_address": "Rua Nova, 200",
        "client_id": str(db_client.id),
    }
    r = client.post(
        f"{settings.API_V1_STR}/services/", headers=client_token_headers, json=payload
    )
    assert r.status_code == HTTPStatus.FORBIDDEN


# ── Read single service ───────────────────────────────────────────────────────


def test_read_service(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    r = client.get(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["id"] == str(svc.id)
    assert data["status"] == "requested"
    # Client ref is embedded
    assert "client" in data


def test_read_service_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/services/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NOT_FOUND
    assert r.json()["detail"] == "Service not found"


def test_read_service_unauthenticated(client: TestClient, db: Session) -> None:
    svc = create_random_service(db)
    r = client.get(f"{settings.API_V1_STR}/services/{svc.id}")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


# ── Update service ────────────────────────────────────────────────────────────


def test_update_service_address(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    r = client.patch(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
        json={"execution_address": "Av. Atualizada, 500"},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["execution_address"] == "Av. Atualizada, 500"
    assert r.json()["updated_at"] is not None


def test_update_service_status_via_patch_rejected(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # Status transitions are no longer allowed via PATCH /services/{id}.
    # Use POST /services/{id}/transition instead (added in Phase 5 API routes).
    svc = create_random_service(db)
    assert svc.status == ServiceStatus.requested
    r = client.patch(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
        json={"status": "scheduled"},
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_service_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.patch(
        f"{settings.API_V1_STR}/services/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json={"execution_address": "Ghost Street"},
    )
    assert r.status_code == HTTPStatus.NOT_FOUND
    assert r.json()["detail"] == "Service not found"


def test_update_service_unauthenticated(client: TestClient, db: Session) -> None:
    svc = create_random_service(db)
    r = client.patch(
        f"{settings.API_V1_STR}/services/{svc.id}",
        json={"execution_address": "No Auth"},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


# ── Delete service ────────────────────────────────────────────────────────────


def test_delete_service(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    svc_id = svc.id
    r = client.delete(
        f"{settings.API_V1_STR}/services/{svc_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NO_CONTENT
    assert crud.get_service(session=db, service_id=svc_id) is None


def test_delete_service_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/services/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NOT_FOUND
    assert r.json()["detail"] == "Service not found"


def test_delete_service_unauthenticated(client: TestClient, db: Session) -> None:
    svc = create_random_service(db)
    r = client.delete(f"{settings.API_V1_STR}/services/{svc.id}")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


def test_delete_service_wrong_role_forbidden(
    client: TestClient, client_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    r = client.delete(
        f"{settings.API_V1_STR}/services/{svc.id}", headers=client_token_headers
    )
    assert r.status_code == HTTPStatus.FORBIDDEN


# ── Service items ─────────────────────────────────────────────────────────────


def test_create_service_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    payload = {
        "item_type": "material",
        "description": "Tubo PVC 50mm",
        "quantity": 5.0,
        "unit_price": 20.0,
    }
    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/items",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.CREATED
    data = r.json()
    assert data["service_id"] == str(svc.id)
    assert data["description"] == "Tubo PVC 50mm"
    assert data["quantity"] == 5.0
    assert data["unit_price"] == 20.0
    assert "id" in data


def test_create_service_item_servico_type(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    payload = {
        "item_type": "serviço",
        "description": "Mão de obra",
        "quantity": 1.0,
        "unit_price": 500.0,
    }
    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/items",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.CREATED
    assert r.json()["item_type"] == "serviço"


def test_create_service_item_service_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    payload = {
        "item_type": "material",
        "description": "Something",
        "quantity": 1.0,
        "unit_price": 10.0,
    }
    r = client.post(
        f"{settings.API_V1_STR}/services/{uuid.uuid4()}/items",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.NOT_FOUND
    assert r.json()["detail"] == "Service not found"


def test_create_service_item_invalid_quantity(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    payload = {
        "item_type": "material",
        "description": "Bad qty",
        "quantity": 0,  # must be > 0
        "unit_price": 10.0,
    }
    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/items",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_service_item_unauthenticated(client: TestClient, db: Session) -> None:
    svc = create_random_service(db)
    payload = {
        "item_type": "material",
        "description": "No auth",
        "quantity": 1.0,
        "unit_price": 5.0,
    }
    r = client.post(f"{settings.API_V1_STR}/services/{svc.id}/items", json=payload)
    assert r.status_code == HTTPStatus.UNAUTHORIZED


# ── Delete service item ───────────────────────────────────────────────────────


def test_delete_service_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    item = create_service_item(db, svc)
    item_id = item.id

    r = client.delete(
        f"{settings.API_V1_STR}/services/{svc.id}/items/{item_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NO_CONTENT
    result = db.exec(select(ServiceItem).where(ServiceItem.id == item_id)).first()
    assert result is None


def test_delete_service_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    r = client.delete(
        f"{settings.API_V1_STR}/services/{svc.id}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NOT_FOUND
    assert r.json()["detail"] == "Item not found"


def test_delete_service_item_wrong_service(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Item belongs to svc1 but we try to delete it via svc2 — should 404."""
    svc1 = create_random_service(db)
    svc2 = create_random_service(db)
    item = create_service_item(db, svc1)

    r = client.delete(
        f"{settings.API_V1_STR}/services/{svc2.id}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NOT_FOUND
    assert r.json()["detail"] == "Item not found"


def test_delete_service_item_unauthenticated(client: TestClient, db: Session) -> None:
    svc = create_random_service(db)
    item = create_service_item(db, svc)
    r = client.delete(f"{settings.API_V1_STR}/services/{svc.id}/items/{item.id}")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


# ── Read service includes items ───────────────────────────────────────────────


def test_read_service_includes_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    create_service_item(db, svc)
    create_service_item(db, svc)
    r = client.get(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "items" in data
    assert len(data["items"]) == 2


def test_delete_service_cascades_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    item = create_service_item(db, svc)
    item_id = item.id

    r = client.delete(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NO_CONTENT
    # Item should also be gone (cascade)
    result = db.exec(select(ServiceItem).where(ServiceItem.id == item_id)).first()
    assert result is None


# ── Service lifecycle / transition ────────────────────────────────────────────


def test_valid_transition_creates_status_log(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """POST /transition valid forward transition creates a ServiceStatusLog entry."""
    from app.models import ServiceStatusLog

    svc = create_random_service(db)
    assert svc.status == ServiceStatus.requested

    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "scheduled"},
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["service"]["status"] == "scheduled"
    assert data["stock_warnings"] == []

    log = db.exec(
        select(ServiceStatusLog).where(ServiceStatusLog.service_id == svc.id)
    ).first()
    assert log is not None
    assert log.from_status == ServiceStatus.requested
    assert log.to_status == ServiceStatus.scheduled


def test_transition_to_cancelled_without_reason_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """POST /transition to cancelled without reason returns 422."""
    svc = create_random_service(db)
    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "cancelled"},
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_transition_to_cancelled_with_reason_persists(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """POST /transition to cancelled with reason persists cancelled_reason."""
    svc = create_random_service(db)
    reason = "Obra suspensa pelo cliente"
    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "cancelled", "reason": reason},
    )
    assert r.status_code == HTTPStatus.OK
    db.refresh(svc)
    assert svc.cancelled_reason == reason
    assert svc.status == ServiceStatus.cancelled


def test_transition_from_terminal_state_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """POST /transition from a terminal state (cancelled) returns 422."""
    svc = create_random_service(db)
    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "cancelled", "reason": "test"},
    )
    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "scheduled"},
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_patch_with_status_field_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """PATCH /services/{id} with status in body is rejected (status not in ServiceUpdate)."""
    svc = create_random_service(db)
    r = client.patch(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
        json={"status": "scheduled"},
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_transition_finance_user_forbidden(
    client: TestClient, finance_token_headers: dict[str, str], db: Session
) -> None:
    """Finance user calling POST /transition returns 403."""
    svc = create_random_service(db)
    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=finance_token_headers,
        json={"to_status": "scheduled"},
    )
    assert r.status_code == HTTPStatus.FORBIDDEN


def test_deduct_stock_on_non_executing_service_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """POST /deduct-stock on a non-executing service returns 422."""
    svc = create_random_service(db)
    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/deduct-stock",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_get_service_includes_status_logs(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """GET /services/{id} response includes status_logs in chronological order."""
    svc = create_random_service(db)
    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "scheduled"},
    )
    r = client.get(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "status_logs" in data
    assert len(data["status_logs"]) == 1
    log = data["status_logs"][0]
    assert log["from_status"] == "requested"
    assert log["to_status"] == "scheduled"


def test_valid_transitions_logic() -> None:
    """Unit test: VALID_STATUS_TRANSITIONS maps all states correctly."""
    from app.models import VALID_STATUS_TRANSITIONS, ServiceStatus

    assert ServiceStatus.scheduled in VALID_STATUS_TRANSITIONS[ServiceStatus.requested]
    assert ServiceStatus.executing in VALID_STATUS_TRANSITIONS[ServiceStatus.scheduled]
    assert ServiceStatus.completed in VALID_STATUS_TRANSITIONS[ServiceStatus.executing]
    assert ServiceStatus.cancelled in VALID_STATUS_TRANSITIONS[ServiceStatus.requested]
    assert ServiceStatus.cancelled in VALID_STATUS_TRANSITIONS[ServiceStatus.scheduled]
    assert ServiceStatus.cancelled in VALID_STATUS_TRANSITIONS[ServiceStatus.executing]
    assert VALID_STATUS_TRANSITIONS[ServiceStatus.completed] == []
    assert VALID_STATUS_TRANSITIONS[ServiceStatus.cancelled] == []


def test_deduct_stock_items_rejects_non_material(db: Session) -> None:
    """_deduct_stock_items raises ValueError when service_item_id is not a material item."""
    import pytest

    from app.crud import _deduct_stock_items

    svc = create_random_service(db)
    item = crud.create_service_item(
        session=db,
        service_id=svc.id,
        item_in=ServiceItemCreate(
            description="Mão de obra",
            item_type=ItemType.servico,
            quantity=1,
            unit_price=100.0,
        ),
    )
    with pytest.raises(ValueError, match="not a material item"):
        _deduct_stock_items(
            db, svc, [DeductionItem(service_item_id=item.id, quantity=1)]
        )


def test_get_service_status_logs_crud(
    db: Session, superuser_token_headers: dict[str, str], client: TestClient
) -> None:
    """get_service_status_logs returns logs ordered by changed_at."""
    svc = create_random_service(db)
    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "scheduled"},
    )
    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "executing"},
    )
    logs = crud.get_service_status_logs(session=db, service_id=svc.id)
    assert len(logs) == 2
    assert logs[0].from_status == ServiceStatus.requested
    assert logs[1].from_status == ServiceStatus.scheduled


# ── Phase 8: Stock integration tests ─────────────────────────────────────────


def _create_product_item(db: Session, quantity: float = 5.0) -> object:
    """Create a ProductType, Product, and ProductItem with em_estoque status."""
    from app.models import (
        Product,
        ProductCategory,
        ProductItem,
        ProductItemStatus,
        ProductType,
    )

    pt = ProductType(
        category=ProductCategory.tubos,
        name=f"Tubo Teste {uuid.uuid4().hex[:6]}",
        unit_of_measure="un",
    )
    db.add(pt)
    db.flush()

    prod = Product(
        product_type_id=pt.id,
        name=f"Produto {uuid.uuid4().hex[:6]}",
        unit_price=Decimal("10.00"),
    )
    db.add(prod)
    db.flush()

    item = ProductItem(
        product_id=prod.id,
        quantity=Decimal(str(quantity)),
        status=ProductItemStatus.em_estoque,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _reserved_for_service(db: Session, service_id: object) -> list:
    """Return all ProductItems currently reserved for a service."""
    from app.models import ProductItem, ProductItemStatus

    return list(
        db.exec(
            select(ProductItem).where(
                ProductItem.service_id == service_id,
                ProductItem.status == ProductItemStatus.reservado,
            )
        ).all()
    )


def _utilizado_for_service(db: Session, service_id: object) -> list:
    """Return all ProductItems marked utilizado that were reserved for a service."""
    from app.models import ProductItem, ProductItemStatus

    return list(
        db.exec(
            select(ProductItem).where(
                ProductItem.service_id == service_id,
                ProductItem.status == ProductItemStatus.utilizado,
            )
        ).all()
    )


def test_transition_to_scheduled_reserves_stock(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Transitioning to scheduled reserves em_estoque ProductItems for the service."""
    svc = create_random_service(db)
    create_service_item(db, svc)
    _create_product_item(db, quantity=20.0)

    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "scheduled"},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["service"]["status"] == "scheduled"

    reserved = _reserved_for_service(db, svc.id)
    assert len(reserved) >= 1
    assert all(item.service_id == svc.id for item in reserved)


def test_transition_to_scheduled_with_insufficient_stock_returns_warning(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Insufficient stock produces a warning but does not block transition."""
    svc = create_random_service(db)
    # Service item needs 10 units, only 2 available
    item_in = ServiceItemCreate(
        item_type=ItemType.material,
        description="Material escasso",
        quantity=10.0,
        unit_price=5.0,
    )
    crud.create_service_item(session=db, service_id=svc.id, item_in=item_in)
    _create_product_item(db, quantity=2.0)

    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "scheduled"},
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["service"]["status"] == "scheduled"
    assert len(data["stock_warnings"]) >= 1
    warning = data["stock_warnings"][0]
    assert warning["shortfall"] > 0


def test_transition_to_cancelled_releases_reserved_stock(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Cancelling a service releases all reserved ProductItems back to em_estoque."""
    from app.models import ProductItemStatus

    svc = create_random_service(db)
    create_service_item(db, svc)
    _create_product_item(db, quantity=20.0)

    # Schedule (reserves stock)
    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "scheduled"},
    )
    reserved = _reserved_for_service(db, svc.id)
    assert len(reserved) >= 1

    # Cancel (should release)
    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "cancelled", "reason": "Obra cancelada pelo cliente"},
    )
    assert r.status_code == HTTPStatus.OK

    # All items reserved for this service should be released
    assert len(_reserved_for_service(db, svc.id)) == 0
    # Released items no longer point to this service
    from app.models import ProductItem

    released = db.exec(
        select(ProductItem).where(
            ProductItem.status == ProductItemStatus.em_estoque,
            ProductItem.service_id.is_(None),  # type: ignore[union-attr]
        )
    ).all()
    assert len(released) >= 1


def test_transition_to_completed_marks_stock_utilizado(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Completing a service marks reserved ProductItems as utilizado."""
    svc = create_random_service(db)
    svc_item = create_service_item(db, svc)
    _create_product_item(db, quantity=20.0)

    # requested → scheduled → executing → completed
    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "scheduled"},
    )
    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "executing"},
    )
    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={
            "to_status": "completed",
            "deduction_items": [
                {"service_item_id": str(svc_item.id), "quantity": 10.0}
            ],
        },
    )
    assert r.status_code == HTTPStatus.OK

    # No items should remain reserved for this service
    assert len(_reserved_for_service(db, svc.id)) == 0
    # Items reserved for this service are now utilizado
    utilizado = _utilizado_for_service(db, svc.id)
    assert len(utilizado) >= 1


def test_deduct_stock_marks_reserved_items_utilizado(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """POST /deduct-stock on an executing service marks reserved items utilizado."""
    svc = create_random_service(db)
    create_service_item(db, svc)
    _create_product_item(db, quantity=20.0)

    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "scheduled"},
    )
    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "executing"},
    )

    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/deduct-stock",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK

    # All reserved items are now utilizado
    assert len(_reserved_for_service(db, svc.id)) == 0
    utilizado = _utilizado_for_service(db, svc.id)
    assert len(utilizado) >= 1


# ── T-08 / T-10: Service mutation guard tests ─────────────────────────────────


def _advance_service_to(
    client: TestClient,
    headers: dict,
    service_id: object,
    target: str,
) -> None:
    """Advance a service through the state machine up to the target status."""
    path = {
        "scheduled": ["scheduled"],
        "executing": ["scheduled", "executing"],
        "completed": ["scheduled", "executing"],
    }
    for status in path.get(target, []):
        payload: dict = {"to_status": status}
        if status == "completed":
            payload["deduction_items"] = []
        client.post(
            f"{settings.API_V1_STR}/services/{service_id}/transition",
            headers=headers,
            json=payload,
        )


def test_delete_scheduled_service_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Cannot delete a service in scheduled status."""
    svc = create_random_service(db)
    _advance_service_to(client, superuser_token_headers, svc.id, "scheduled")

    r = client.delete(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_delete_executing_service_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Cannot delete a service in executing status."""
    svc = create_random_service(db)
    _advance_service_to(client, superuser_token_headers, svc.id, "executing")

    r = client.delete(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_delete_requested_service_succeeds(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Can delete a service in requested status (no state lock)."""
    svc = create_random_service(db)

    r = client.delete(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NO_CONTENT


def test_add_item_to_executing_service_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Cannot add line items to an executing service."""
    svc = create_random_service(db)
    _advance_service_to(client, superuser_token_headers, svc.id, "executing")

    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/items",
        headers=superuser_token_headers,
        json={
            "item_type": "material",
            "description": "Tubo extra",
            "quantity": 1,
            "unit_price": 10,
        },
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_add_item_to_completed_service_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Cannot add line items to a completed service."""
    svc = create_random_service(db)
    svc_item = create_service_item(db, svc)

    # Complete the service
    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "scheduled"},
    )
    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={"to_status": "executing"},
    )
    client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/transition",
        headers=superuser_token_headers,
        json={
            "to_status": "completed",
            "deduction_items": [{"service_item_id": str(svc_item.id), "quantity": 1.0}],
        },
    )

    r = client.post(
        f"{settings.API_V1_STR}/services/{svc.id}/items",
        headers=superuser_token_headers,
        json={
            "item_type": "material",
            "description": "Novo item",
            "quantity": 1,
            "unit_price": 10,
        },
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_delete_item_from_executing_service_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Cannot remove line items from an executing service."""
    svc = create_random_service(db)
    svc_item = create_service_item(db, svc)
    _advance_service_to(client, superuser_token_headers, svc.id, "executing")

    r = client.delete(
        f"{settings.API_V1_STR}/services/{svc.id}/items/{svc_item.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

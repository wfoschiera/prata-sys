import uuid
from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlmodel import Session, select

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
)
from tests.utils.utils import random_lower_string

# ── Helpers ───────────────────────────────────────────────────────────────────


def _cpf() -> str:
    uid_digits = "".join(c for c in uuid.uuid4().hex if c.isdigit())
    return (uid_digits + "00000000000")[:11]


def _cnpj() -> str:
    uid_digits = "".join(c for c in uuid.uuid4().hex if c.isdigit())
    return (uid_digits + "00000000000000")[:14]


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


def _finance_headers(client: TestClient, db: Session) -> dict[str, str]:
    from app.models import UserCreate, UserRole
    from tests.utils.user import user_authentication_headers

    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.finance)
    crud.create_user(session=db, user_create=user_in)
    return user_authentication_headers(client=client, email=email, password=password)


def _client_role_headers(client: TestClient, db: Session) -> dict[str, str]:
    from app.models import UserCreate, UserRole
    from tests.utils.user import user_authentication_headers

    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.client)
    crud.create_user(session=db, user_create=user_in)
    return user_authentication_headers(client=client, email=email, password=password)


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


def test_read_services_finance_role_forbidden(client: TestClient, db: Session) -> None:
    """Finance role does not have manage_services by default."""
    headers = _finance_headers(client, db)
    r = client.get(f"{settings.API_V1_STR}/services/", headers=headers)
    assert r.status_code == HTTPStatus.FORBIDDEN


def test_read_services_no_permission_forbidden(client: TestClient, db: Session) -> None:
    """Client role has no permissions by default."""
    headers = _client_role_headers(client, db)
    r = client.get(f"{settings.API_V1_STR}/services/", headers=headers)
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


def test_create_service_wrong_role_forbidden(client: TestClient, db: Session) -> None:
    db_client = create_random_client(db)
    headers = _client_role_headers(client, db)
    payload = {
        "type": "perfuração",
        "execution_address": "Rua Nova, 200",
        "client_id": str(db_client.id),
    }
    r = client.post(f"{settings.API_V1_STR}/services/", headers=headers, json=payload)
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


def test_update_service_valid_status_transition(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    assert svc.status == ServiceStatus.requested
    r = client.patch(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
        json={"status": "scheduled"},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["status"] == "scheduled"


def test_update_service_full_status_chain(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    transitions = ["scheduled", "executing", "completed"]
    for new_status in transitions:
        r = client.patch(
            f"{settings.API_V1_STR}/services/{svc.id}",
            headers=superuser_token_headers,
            json={"status": new_status},
        )
        assert r.status_code == HTTPStatus.OK
        assert r.json()["status"] == new_status


def test_update_service_invalid_status_transition(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    # requested → executing is not valid (must go through scheduled)
    r = client.patch(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
        json={"status": "executing"},
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_service_completed_no_further_transitions(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    svc = create_random_service(db)
    # Advance to completed
    for status in ["scheduled", "executing", "completed"]:
        client.patch(
            f"{settings.API_V1_STR}/services/{svc.id}",
            headers=superuser_token_headers,
            json={"status": status},
        )
    # Try to re-transition from completed
    r = client.patch(
        f"{settings.API_V1_STR}/services/{svc.id}",
        headers=superuser_token_headers,
        json={"status": "requested"},
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


def test_delete_service_wrong_role_forbidden(client: TestClient, db: Session) -> None:
    svc = create_random_service(db)
    headers = _client_role_headers(client, db)
    r = client.delete(f"{settings.API_V1_STR}/services/{svc.id}", headers=headers)
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

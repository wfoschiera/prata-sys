import uuid
from http import HTTPStatus

from faker import Faker
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import Client
from tests.factories import ClientFactory

fake = Faker("pt_BR")

# ── Helpers ───────────────────────────────────────────────────────────────────
# Replaced by `random_client` fixture (conftest.py) and `ClientFactory()`.


# ── List clients ──────────────────────────────────────────────────────────────


def test_read_clients_superuser(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    random_client: Client,
) -> None:
    r = client.get(f"{settings.API_V1_STR}/clients/", headers=superuser_token_headers)
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] >= 1
    for item in data["data"]:
        assert "name" in item
        assert "id" in item


def test_read_clients_finance_user_forbidden(
    client: TestClient, finance_token_headers: dict[str, str]
) -> None:
    """Finance role does not have manage_clients by default."""
    r = client.get(f"{settings.API_V1_STR}/clients/", headers=finance_token_headers)
    assert r.status_code == HTTPStatus.FORBIDDEN


def test_read_clients_no_permission_forbidden(
    client: TestClient, client_token_headers: dict[str, str]
) -> None:
    """Client role has no permissions by default."""
    r = client.get(f"{settings.API_V1_STR}/clients/", headers=client_token_headers)
    assert r.status_code == HTTPStatus.FORBIDDEN
    assert r.json()["detail"] == "Insufficient permissions"


def test_read_clients_unauthenticated(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/clients/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


def test_read_clients_pagination(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    ClientFactory()
    ClientFactory()
    r = client.get(
        f"{settings.API_V1_STR}/clients/?skip=0&limit=1",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert len(data["data"]) == 1


# ── Create client ─────────────────────────────────────────────────────────────


def test_create_client_cpf(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    doc = fake.cpf().replace(".", "").replace("-", "")
    payload = {
        "name": "João da Silva",
        "document_type": "cpf",
        "document_number": doc,
        "email": "joao@example.com",
        "phone": "11999990000",
        "address": "Av. Principal, 1",
    }
    r = client.post(
        f"{settings.API_V1_STR}/clients/",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.CREATED
    created = r.json()
    assert created["document_number"] == doc
    assert created["name"] == "João da Silva"
    assert "id" in created

    # Verify it exists in DB
    db_client = crud.get_client_by_document(session=db, document_number=doc)
    assert db_client is not None
    assert db_client.name == "João da Silva"


def test_create_client_cnpj(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    doc = fake.cnpj().replace(".", "").replace("/", "").replace("-", "")
    payload = {
        "name": "Empresa LTDA",
        "document_type": "cnpj",
        "document_number": doc,
    }
    r = client.post(
        f"{settings.API_V1_STR}/clients/",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.CREATED
    created = r.json()
    assert created["document_number"] == doc


def test_create_client_duplicate_document(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    random_client: Client,
) -> None:
    payload = {
        "name": "Duplicate",
        "document_type": random_client.document_type.value,
        "document_number": random_client.document_number,
    }
    r = client.post(
        f"{settings.API_V1_STR}/clients/",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.CONFLICT
    assert r.json()["detail"] == "Document number already registered"


def test_create_client_invalid_cpf_length(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    payload = {
        "name": "Invalid",
        "document_type": "cpf",
        "document_number": "123",  # only 3 digits — invalid
    }
    r = client.post(
        f"{settings.API_V1_STR}/clients/",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_client_document_with_letters(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    payload = {
        "name": "Invalid",
        "document_type": "cpf",
        "document_number": "1234567890a",  # contains letter
    }
    r = client.post(
        f"{settings.API_V1_STR}/clients/",
        headers=superuser_token_headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_client_unauthenticated(client: TestClient) -> None:
    payload = {
        "name": "No Auth",
        "document_type": "cpf",
        "document_number": fake.cpf().replace(".", "").replace("-", ""),
    }
    r = client.post(f"{settings.API_V1_STR}/clients/", json=payload)
    assert r.status_code == HTTPStatus.UNAUTHORIZED


def test_create_client_wrong_role_forbidden(
    client: TestClient, client_token_headers: dict[str, str]
) -> None:
    payload = {
        "name": "Forbidden",
        "document_type": "cpf",
        "document_number": fake.cpf().replace(".", "").replace("-", ""),
    }
    r = client.post(
        f"{settings.API_V1_STR}/clients/", headers=client_token_headers, json=payload
    )
    assert r.status_code == HTTPStatus.FORBIDDEN


# ── Read single client ────────────────────────────────────────────────────────


def test_read_client(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    random_client: Client,
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/clients/{random_client.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["id"] == str(random_client.id)
    assert data["document_number"] == random_client.document_number


def test_read_client_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/clients/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NOT_FOUND
    assert r.json()["detail"] == "Client not found"


def test_read_client_unauthenticated(
    client: TestClient, db: Session, random_client: Client
) -> None:
    r = client.get(f"{settings.API_V1_STR}/clients/{random_client.id}")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


# ── Update client ─────────────────────────────────────────────────────────────


def test_update_client_name(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    random_client: Client,
) -> None:
    r = client.patch(
        f"{settings.API_V1_STR}/clients/{random_client.id}",
        headers=superuser_token_headers,
        json={"name": "Updated Name"},
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["name"] == "Updated Name"
    assert data["updated_at"] is not None


def test_update_client_document_number(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    random_client: Client,
) -> None:
    new_doc = fake.cpf().replace(".", "").replace("-", "")
    r = client.patch(
        f"{settings.API_V1_STR}/clients/{random_client.id}",
        headers=superuser_token_headers,
        json={"document_number": new_doc, "document_type": "cpf"},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["document_number"] == new_doc


def test_update_client_duplicate_document(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    random_client: Client,
) -> None:
    other_client = ClientFactory()
    r = client.patch(
        f"{settings.API_V1_STR}/clients/{random_client.id}",
        headers=superuser_token_headers,
        json={
            "document_number": other_client.document_number,
            "document_type": other_client.document_type.value,
        },
    )
    assert r.status_code == HTTPStatus.CONFLICT
    assert r.json()["detail"] == "Document number already registered"


def test_update_client_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.patch(
        f"{settings.API_V1_STR}/clients/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json={"name": "Ghost"},
    )
    assert r.status_code == HTTPStatus.NOT_FOUND
    assert r.json()["detail"] == "Client not found"


def test_update_client_same_document_no_conflict(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    random_client: Client,
) -> None:
    """Updating a client with its own document number should not raise 409."""
    r = client.patch(
        f"{settings.API_V1_STR}/clients/{random_client.id}",
        headers=superuser_token_headers,
        json={
            "document_number": random_client.document_number,
            "document_type": random_client.document_type.value,
            "name": "Same Doc Updated",
        },
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["name"] == "Same Doc Updated"


def test_update_client_unauthenticated(
    client: TestClient, db: Session, random_client: Client
) -> None:
    r = client.patch(
        f"{settings.API_V1_STR}/clients/{random_client.id}",
        json={"name": "No Auth"},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


# ── Delete client ─────────────────────────────────────────────────────────────


def test_delete_client(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    random_client: Client,
) -> None:
    client_id = random_client.id
    r = client.delete(
        f"{settings.API_V1_STR}/clients/{client_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["message"] == "Client deleted successfully"

    # Confirm removed from DB
    result = db.exec(select(Client).where(Client.id == client_id)).first()
    assert result is None


def test_delete_client_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/clients/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NOT_FOUND
    assert r.json()["detail"] == "Client not found"


def test_delete_client_unauthenticated(
    client: TestClient, db: Session, random_client: Client
) -> None:
    r = client.delete(f"{settings.API_V1_STR}/clients/{random_client.id}")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


def test_delete_client_wrong_role_forbidden(
    client: TestClient,
    client_token_headers: dict[str, str],
    db: Session,
    random_client: Client,
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/clients/{random_client.id}",
        headers=client_token_headers,
    )
    assert r.status_code == HTTPStatus.FORBIDDEN

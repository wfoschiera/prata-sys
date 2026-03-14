import uuid
from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import Client, ClientCreate, DocumentType
from tests.utils.utils import random_lower_string

# ── Helpers ───────────────────────────────────────────────────────────────────


def _cpf() -> str:
    """Return a unique 11-digit CPF string."""
    base = random_lower_string()[:11]
    digits = "".join(c for c in base if c.isdigit())
    # Pad / trim to exactly 11 digits using a counter derived from a uuid
    uid_digits = "".join(c for c in uuid.uuid4().hex if c.isdigit())
    combined = (digits + uid_digits)[:11].ljust(11, "0")
    return combined


def _cnpj() -> str:
    """Return a unique 14-digit CNPJ string."""
    uid_digits = "".join(c for c in uuid.uuid4().hex if c.isdigit())
    return (uid_digits + "00000000000000")[:14]


def create_random_client(db: Session) -> Client:
    client_in = ClientCreate(
        name="Test Client",
        document_type=DocumentType.cpf,
        document_number=_cpf(),
        email="client@example.com",
        phone="11999999999",
        address="Rua Teste, 123",
    )
    return crud.create_client(session=db, client_in=client_in)


# ── List clients ──────────────────────────────────────────────────────────────


def test_read_clients_superuser(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_client(db)
    r = client.get(f"{settings.API_V1_STR}/clients/", headers=superuser_token_headers)
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] >= 1
    for item in data["data"]:
        assert "name" in item
        assert "id" in item


def test_read_clients_finance_user_forbidden(client: TestClient, db: Session) -> None:
    """Finance role does not have manage_clients by default."""
    from app.models import UserCreate, UserRole
    from tests.utils.user import user_authentication_headers

    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.finance)
    crud.create_user(session=db, user_create=user_in)
    headers = user_authentication_headers(client=client, email=email, password=password)

    r = client.get(f"{settings.API_V1_STR}/clients/", headers=headers)
    assert r.status_code == HTTPStatus.FORBIDDEN


def test_read_clients_no_permission_forbidden(client: TestClient, db: Session) -> None:
    """Client role has no permissions by default."""
    from app.models import UserCreate, UserRole
    from tests.utils.user import user_authentication_headers

    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.client)
    crud.create_user(session=db, user_create=user_in)
    headers = user_authentication_headers(client=client, email=email, password=password)

    r = client.get(f"{settings.API_V1_STR}/clients/", headers=headers)
    assert r.status_code == HTTPStatus.FORBIDDEN
    assert r.json()["detail"] == "Insufficient permissions"


def test_read_clients_unauthenticated(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/clients/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


def test_read_clients_pagination(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_client(db)
    create_random_client(db)
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
    doc = _cpf()
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
    doc = _cnpj()
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
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    existing = create_random_client(db)
    payload = {
        "name": "Duplicate",
        "document_type": existing.document_type.value,
        "document_number": existing.document_number,
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
        "document_number": _cpf(),
    }
    r = client.post(f"{settings.API_V1_STR}/clients/", json=payload)
    assert r.status_code == HTTPStatus.UNAUTHORIZED


def test_create_client_wrong_role_forbidden(client: TestClient, db: Session) -> None:
    from app.models import UserCreate, UserRole
    from tests.utils.user import user_authentication_headers

    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.client)
    crud.create_user(session=db, user_create=user_in)
    headers = user_authentication_headers(client=client, email=email, password=password)

    payload = {
        "name": "Forbidden",
        "document_type": "cpf",
        "document_number": _cpf(),
    }
    r = client.post(f"{settings.API_V1_STR}/clients/", headers=headers, json=payload)
    assert r.status_code == HTTPStatus.FORBIDDEN


# ── Read single client ────────────────────────────────────────────────────────


def test_read_client(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    db_client = create_random_client(db)
    r = client.get(
        f"{settings.API_V1_STR}/clients/{db_client.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["id"] == str(db_client.id)
    assert data["document_number"] == db_client.document_number


def test_read_client_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/clients/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NOT_FOUND
    assert r.json()["detail"] == "Client not found"


def test_read_client_unauthenticated(client: TestClient, db: Session) -> None:
    db_client = create_random_client(db)
    r = client.get(f"{settings.API_V1_STR}/clients/{db_client.id}")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


# ── Update client ─────────────────────────────────────────────────────────────


def test_update_client_name(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    db_client = create_random_client(db)
    r = client.patch(
        f"{settings.API_V1_STR}/clients/{db_client.id}",
        headers=superuser_token_headers,
        json={"name": "Updated Name"},
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["name"] == "Updated Name"
    assert data["updated_at"] is not None


def test_update_client_document_number(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    db_client = create_random_client(db)
    new_doc = _cpf()
    r = client.patch(
        f"{settings.API_V1_STR}/clients/{db_client.id}",
        headers=superuser_token_headers,
        json={"document_number": new_doc, "document_type": "cpf"},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["document_number"] == new_doc


def test_update_client_duplicate_document(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    client1 = create_random_client(db)
    client2 = create_random_client(db)
    r = client.patch(
        f"{settings.API_V1_STR}/clients/{client1.id}",
        headers=superuser_token_headers,
        json={
            "document_number": client2.document_number,
            "document_type": client2.document_type.value,
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
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Updating a client with its own document number should not raise 409."""
    db_client = create_random_client(db)
    r = client.patch(
        f"{settings.API_V1_STR}/clients/{db_client.id}",
        headers=superuser_token_headers,
        json={
            "document_number": db_client.document_number,
            "document_type": db_client.document_type.value,
            "name": "Same Doc Updated",
        },
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["name"] == "Same Doc Updated"


def test_update_client_unauthenticated(client: TestClient, db: Session) -> None:
    db_client = create_random_client(db)
    r = client.patch(
        f"{settings.API_V1_STR}/clients/{db_client.id}", json={"name": "No Auth"}
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


# ── Delete client ─────────────────────────────────────────────────────────────


def test_delete_client(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    db_client = create_random_client(db)
    client_id = db_client.id
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


def test_delete_client_unauthenticated(client: TestClient, db: Session) -> None:
    db_client = create_random_client(db)
    r = client.delete(f"{settings.API_V1_STR}/clients/{db_client.id}")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


def test_delete_client_wrong_role_forbidden(client: TestClient, db: Session) -> None:
    from app.models import UserCreate, UserRole
    from tests.utils.user import user_authentication_headers

    db_client = create_random_client(db)
    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.client)
    crud.create_user(session=db, user_create=user_in)
    headers = user_authentication_headers(client=client, email=email, password=password)

    r = client.delete(f"{settings.API_V1_STR}/clients/{db_client.id}", headers=headers)
    assert r.status_code == HTTPStatus.FORBIDDEN

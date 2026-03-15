"""Tests for orçamento CRUD endpoints."""

import uuid
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
    Product,
    ProductCategory,
    ProductType,
)
from tests.utils.utils import random_lower_string

# ── Helpers ───────────────────────────────────────────────────────────────────


def _random_cpf() -> str:
    uid_digits = "".join(c for c in uuid.uuid4().hex if c.isdigit())
    return (uid_digits + "00000000000")[:11]


def _create_client(db: Session) -> Client:
    return crud.create_client(
        session=db,
        client_in=ClientCreate(
            name=random_lower_string(),
            document_type=DocumentType.cpf,
            document_number=_random_cpf(),
        ),
    )


def _create_product(db: Session) -> Product:
    pt = ProductType(
        category=ProductCategory.tubos,
        name=f"Type-{uuid.uuid4().hex[:6]}",
        unit_of_measure="un",
    )
    db.add(pt)
    db.flush()
    prod = Product(
        product_type_id=pt.id,
        name=f"Product-{uuid.uuid4().hex[:6]}",
        unit_price=Decimal("100.00"),
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


def _create_orcamento(
    client: TestClient,
    headers: dict[str, str],
    db: Session,
) -> dict:
    cl = _create_client(db)
    payload = {
        "client_id": str(cl.id),
        "service_type": "perfuração",
        "execution_address": "Rua Teste, 123",
    }
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/",
        headers=headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.CREATED
    return r.json()


def _add_item(
    client: TestClient,
    headers: dict[str, str],
    orcamento_id: str,
    product_id: str,
) -> dict:
    payload = {
        "product_id": product_id,
        "description": "Item teste",
        "quantity": 10.0,
        "unit_price": 50.0,
        "show_unit_price": True,
    }
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orcamento_id}/items",
        headers=headers,
        json=payload,
    )
    assert r.status_code == HTTPStatus.CREATED
    return r.json()


# ── CRUD tests ────────────────────────────────────────────────────────────────


def test_create_orcamento(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    assert orc["status"] == "rascunho"
    assert len(orc["ref_code"]) == 6


def test_list_orcamentos(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _create_orcamento(client, superuser_token_headers, db)
    r = client.get(
        f"{settings.API_V1_STR}/orcamentos/",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["count"] >= 1


def test_read_orcamento(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    r = client.get(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["ref_code"] == orc["ref_code"]


def test_update_orcamento(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    r = client.patch(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}",
        headers=superuser_token_headers,
        json={"description": "Updated description"},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["description"] == "Updated description"


def test_delete_rascunho_orcamento(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    r = client.delete(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NO_CONTENT


# ── Transition tests ──────────────────────────────────────────────────────────


def test_transition_to_em_analise(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["orcamento"]["status"] == "em_analise"


def test_approve_with_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    _add_item(client, superuser_token_headers, orc["id"], str(prod.id))

    # rascunho → em_analise → aprovado
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "aprovado"},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["orcamento"]["status"] == "aprovado"


def test_approve_without_items_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "aprovado"},
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_cancel_orcamento(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "cancelado"},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["orcamento"]["status"] == "cancelado"


# ── Convert to service ────────────────────────────────────────────────────────


def test_convert_approved_to_service(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    _add_item(client, superuser_token_headers, orc["id"], str(prod.id))

    # Approve
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "aprovado"},
    )

    # Convert
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/convert-to-service",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["status"] == "requested"


def test_convert_twice_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    _add_item(client, superuser_token_headers, orc["id"], str(prod.id))

    # Approve + convert
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "aprovado"},
    )
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/convert-to-service",
        headers=superuser_token_headers,
    )

    # Try again
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/convert-to-service",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ── Duplicate ─────────────────────────────────────────────────────────────────


def test_duplicate_orcamento(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    _add_item(client, superuser_token_headers, orc["id"], str(prod.id))

    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/duplicate",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.CREATED
    dup = r.json()
    assert dup["status"] == "rascunho"
    assert dup["ref_code"] != orc["ref_code"]
    assert len(dup["items"]) == 1


# ── Item tests ────────────────────────────────────────────────────────────────


def test_add_item_to_orcamento(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    item = _add_item(client, superuser_token_headers, orc["id"], str(prod.id))
    assert item["product_id"] == str(prod.id)
    assert item["show_unit_price"] is True


def test_delete_item_from_orcamento(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    item = _add_item(client, superuser_token_headers, orc["id"], str(prod.id))

    r = client.delete(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/items/{item['id']}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NO_CONTENT


def test_add_item_to_approved_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    _add_item(client, superuser_token_headers, orc["id"], str(prod.id))

    # Approve
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "aprovado"},
    )

    # Try to add item
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/items",
        headers=superuser_token_headers,
        json={
            "product_id": str(prod.id),
            "description": "New item",
            "quantity": 1.0,
            "unit_price": 10.0,
        },
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ── Filter tests ──────────────────────────────────────────────────────────────


def test_list_filter_by_status(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _create_orcamento(client, superuser_token_headers, db)
    r = client.get(
        f"{settings.API_V1_STR}/orcamentos/?status=rascunho",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    for orc in r.json()["data"]:
        assert orc["status"] == "rascunho"


def test_list_filter_by_search(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    cl_name = orc["client"]["name"]
    r = client.get(
        f"{settings.API_V1_STR}/orcamentos/?search={cl_name[:5]}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["count"] >= 1


# ── Guard tests ───────────────────────────────────────────────────────────────


def test_delete_non_rascunho_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    r = client.delete(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_approved_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    _add_item(client, superuser_token_headers, orc["id"], str(prod.id))
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "aprovado"},
    )
    r = client.patch(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}",
        headers=superuser_token_headers,
        json={"description": "Should fail"},
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_invalid_transition_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "aprovado"},
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_convert_non_approved_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/convert-to-service",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_read_nonexistent_returns_404(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/orcamentos/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.NOT_FOUND


def test_update_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    item = _add_item(client, superuser_token_headers, orc["id"], str(prod.id))
    r = client.patch(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/items/{item['id']}",
        headers=superuser_token_headers,
        json={"quantity": 99.0, "show_unit_price": False},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["show_unit_price"] is False


def test_backward_transition_em_analise_to_rascunho(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "rascunho"},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["orcamento"]["status"] == "rascunho"


def test_backward_transition_aprovado_to_em_analise(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    _add_item(client, superuser_token_headers, orc["id"], str(prod.id))
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "aprovado"},
    )
    r = client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["orcamento"]["status"] == "em_analise"


def test_list_filter_by_date_range(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    _create_orcamento(client, superuser_token_headers, db)
    r = client.get(
        f"{settings.API_V1_STR}/orcamentos/?data_inicio=2020-01-01&data_fim=2030-12-31",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["count"] >= 1


def test_delete_item_from_approved_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    item = _add_item(client, superuser_token_headers, orc["id"], str(prod.id))
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "aprovado"},
    )
    r = client.delete(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/items/{item['id']}",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_item_on_approved_returns_422(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    orc = _create_orcamento(client, superuser_token_headers, db)
    prod = _create_product(db)
    item = _add_item(client, superuser_token_headers, orc["id"], str(prod.id))
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "em_analise"},
    )
    client.post(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/transition",
        headers=superuser_token_headers,
        json={"to_status": "aprovado"},
    )
    r = client.patch(
        f"{settings.API_V1_STR}/orcamentos/{orc['id']}/items/{item['id']}",
        headers=superuser_token_headers,
        json={"quantity": 999.0},
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ── Company settings tests ────────────────────────────────────────────────────


def test_get_company_settings_returns_default(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/settings/empresa",
        headers=superuser_token_headers,
    )
    assert r.status_code == HTTPStatus.OK
    assert "company_name" in r.json()


def test_update_company_settings(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.put(
        f"{settings.API_V1_STR}/settings/empresa",
        headers=superuser_token_headers,
        json={
            "company_name": "Prata Poços",
            "cnpj": "49.508.087/0001-00",
            "phone": "66 9 9985-0535",
        },
    )
    assert r.status_code == HTTPStatus.OK
    assert r.json()["company_name"] == "Prata Poços"

    # Read back
    r2 = client.get(
        f"{settings.API_V1_STR}/settings/empresa",
        headers=superuser_token_headers,
    )
    assert r2.json()["cnpj"] == "49.508.087/0001-00"

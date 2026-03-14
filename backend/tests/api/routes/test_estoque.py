"""Tests for estoque (inventory) endpoints: product types, products, items, dashboard."""

import uuid
from decimal import Decimal
from http import HTTPStatus
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import (
    ProductCategory,
    ProductItemStatus,
    ServiceStatus,
    UserRole,
)
from tests.utils.utils import random_lower_string

PT_PREFIX = f"{settings.API_V1_STR}/product-types"
P_PREFIX = f"{settings.API_V1_STR}/products"
PI_PREFIX = f"{settings.API_V1_STR}/product-items"
ESTOQUE_PREFIX = f"{settings.API_V1_STR}/estoque"
SERVICES_PREFIX = f"{settings.API_V1_STR}/services"


# ── Helpers ────────────────────────────────────────────────────────────────────


def _superuser_headers(client: TestClient) -> dict[str, str]:
    login = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={
            "username": settings.FIRST_SUPERUSER,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
        },
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_user_with_role(
    client: TestClient, db: Session, role: UserRole
) -> dict[str, str]:
    from app import crud
    from app.models import UserCreate

    email = f"{random_lower_string()}@example.com"
    user_in = UserCreate(email=email, password="testpassword123", role=role)
    crud.create_user(session=db, user_create=user_in)
    login = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": "testpassword123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_product_type(
    client: TestClient,
    headers: dict[str, str],
    category: str = "tubos",
    name: str | None = None,
    unit_of_measure: str = "metros",
) -> Any:
    body = {
        "category": category,
        "name": name or random_lower_string(),
        "unit_of_measure": unit_of_measure,
    }
    resp = client.post(PT_PREFIX, json=body, headers=headers)
    assert resp.status_code == HTTPStatus.CREATED, resp.text
    return resp.json()


def _create_product(
    client: TestClient,
    headers: dict[str, str],
    product_type_id: str,
    name: str | None = None,
    unit_price: float = 10.0,
) -> Any:
    body = {
        "product_type_id": product_type_id,
        "name": name or random_lower_string(),
        "unit_price": unit_price,
    }
    resp = client.post(P_PREFIX, json=body, headers=headers)
    assert resp.status_code == HTTPStatus.CREATED, resp.text
    return resp.json()


def _create_product_item(
    client: TestClient,
    headers: dict[str, str],
    product_id: str,
    quantity: float = 100.0,
) -> Any:
    body = {"product_id": product_id, "quantity": quantity}
    resp = client.post(PI_PREFIX, json=body, headers=headers)
    assert resp.status_code == HTTPStatus.CREATED, resp.text
    return resp.json()


# ── ProductType tests ──────────────────────────────────────────────────────────


def test_create_product_type(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    data = _create_product_type(client, headers)
    assert "id" in data
    assert data["category"] == "tubos"
    assert data["unit_of_measure"] == "metros"


def test_create_product_type_duplicate_conflict(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    name = random_lower_string()
    _create_product_type(client, headers, name=name)
    resp = client.post(
        PT_PREFIX,
        json={"category": "tubos", "name": name, "unit_of_measure": "metros"},
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.CONFLICT


def test_create_product_type_finance_forbidden(client: TestClient, db: Session) -> None:
    headers = _create_user_with_role(client, db, UserRole.finance)
    resp = client.post(
        PT_PREFIX,
        json={
            "category": "tubos",
            "name": random_lower_string(),
            "unit_of_measure": "m",
        },
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_list_product_types(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    _create_product_type(client, headers)
    resp = client.get(PT_PREFIX, headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


def test_list_product_types_finance_allowed(client: TestClient, db: Session) -> None:
    headers = _create_user_with_role(client, db, UserRole.finance)
    resp = client.get(PT_PREFIX, headers=headers)
    assert resp.status_code == HTTPStatus.OK


def test_get_product_type(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    created = _create_product_type(client, headers)
    resp = client.get(f"{PT_PREFIX}/{created['id']}", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["id"] == created["id"]


def test_get_product_type_not_found(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    resp = client.get(f"{PT_PREFIX}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_update_product_type(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    created = _create_product_type(client, headers)
    resp = client.patch(
        f"{PT_PREFIX}/{created['id']}",
        json={"unit_of_measure": "cm"},
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["unit_of_measure"] == "cm"


def test_delete_product_type(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    created = _create_product_type(client, headers)
    resp = client.delete(f"{PT_PREFIX}/{created['id']}", headers=headers)
    assert resp.status_code == HTTPStatus.NO_CONTENT
    resp2 = client.get(f"{PT_PREFIX}/{created['id']}", headers=headers)
    assert resp2.status_code == HTTPStatus.NOT_FOUND


def test_delete_product_type_with_products_conflict(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    _create_product(client, headers, product_type_id=pt["id"])
    resp = client.delete(f"{PT_PREFIX}/{pt['id']}", headers=headers)
    assert resp.status_code == HTTPStatus.CONFLICT


# ── Product tests ─────────────────────────────────────────────────────────────


def test_create_product(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    data = _create_product(client, headers, product_type_id=pt["id"])
    assert "id" in data
    assert data["product_type"]["id"] == pt["id"]
    assert data["unit_price"] == "10.00"


def test_create_product_invalid_product_type_id(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    resp = client.post(
        P_PREFIX,
        json={
            "product_type_id": str(uuid.uuid4()),
            "name": random_lower_string(),
            "unit_price": 5.0,
        },
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_create_product_negative_unit_price(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    resp = client.post(
        P_PREFIX,
        json={
            "product_type_id": pt["id"],
            "name": random_lower_string(),
            "unit_price": -1.0,
        },
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_product_finance_forbidden(client: TestClient, db: Session) -> None:
    admin_headers = _superuser_headers(client)
    pt = _create_product_type(client, admin_headers)
    headers = _create_user_with_role(client, db, UserRole.finance)
    resp = client.post(
        P_PREFIX,
        json={
            "product_type_id": pt["id"],
            "name": random_lower_string(),
            "unit_price": 5.0,
        },
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_list_products(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    _create_product(client, headers, product_type_id=pt["id"])
    resp = client.get(P_PREFIX, headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert isinstance(resp.json(), list)


def test_list_products_filter_category(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers, category="bombas")
    _create_product(client, headers, product_type_id=pt["id"])
    resp = client.get(f"{P_PREFIX}?category=bombas", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    for p in resp.json():
        assert p["product_type"]["category"] == "bombas"


def test_get_product(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    created = _create_product(client, headers, product_type_id=pt["id"])
    resp = client.get(f"{P_PREFIX}/{created['id']}", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["id"] == created["id"]


def test_get_product_not_found(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    resp = client.get(f"{P_PREFIX}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_update_product(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    created = _create_product(client, headers, product_type_id=pt["id"])
    resp = client.patch(
        f"{P_PREFIX}/{created['id']}",
        json={"unit_price": 99.99},
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["unit_price"] == "99.99"


def test_delete_product(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    created = _create_product(client, headers, product_type_id=pt["id"])
    resp = client.delete(f"{P_PREFIX}/{created['id']}", headers=headers)
    assert resp.status_code == HTTPStatus.NO_CONTENT


def test_delete_product_with_items_conflict(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    product = _create_product(client, headers, product_type_id=pt["id"])
    _create_product_item(client, headers, product_id=product["id"])
    resp = client.delete(f"{P_PREFIX}/{product['id']}", headers=headers)
    assert resp.status_code == HTTPStatus.CONFLICT


# ── ProductItem tests ──────────────────────────────────────────────────────────


def test_create_product_item(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    product = _create_product(client, headers, product_type_id=pt["id"])
    data = _create_product_item(client, headers, product_id=product["id"])
    assert data["status"] == ProductItemStatus.em_estoque.value
    assert data["service_id"] is None
    assert data["quantity"] == "100.0000"


def test_create_product_item_invalid_product_id(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    resp = client.post(
        PI_PREFIX,
        json={"product_id": str(uuid.uuid4()), "quantity": 10.0},
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_create_product_item_zero_quantity(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    product = _create_product(client, headers, product_type_id=pt["id"])
    resp = client.post(
        PI_PREFIX,
        json={"product_id": product["id"], "quantity": 0},
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_product_item_finance_forbidden(client: TestClient, db: Session) -> None:
    admin_headers = _superuser_headers(client)
    pt = _create_product_type(client, admin_headers)
    product = _create_product(client, admin_headers, product_type_id=pt["id"])
    headers = _create_user_with_role(client, db, UserRole.finance)
    resp = client.post(
        PI_PREFIX,
        json={"product_id": product["id"], "quantity": 10.0},
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_list_product_items(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    product = _create_product(client, headers, product_type_id=pt["id"])
    _create_product_item(client, headers, product_id=product["id"])
    resp = client.get(f"{PI_PREFIX}?product_id={product['id']}", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert len(resp.json()) >= 1


# ── ProductItem transitions (CRUD level) ──────────────────────────────────────


def test_validate_product_item_transition_valid(db: Session) -> None:  # noqa: ARG001
    from app.crud import validate_product_item_transition

    # Should not raise
    validate_product_item_transition(
        ProductItemStatus.em_estoque, ProductItemStatus.reservado
    )
    validate_product_item_transition(
        ProductItemStatus.reservado, ProductItemStatus.utilizado
    )


def test_validate_product_item_transition_invalid(db: Session) -> None:  # noqa: ARG001
    from app.crud import validate_product_item_transition

    with pytest.raises(ValueError):
        validate_product_item_transition(
            ProductItemStatus.em_estoque, ProductItemStatus.utilizado
        )
    with pytest.raises(ValueError):
        validate_product_item_transition(
            ProductItemStatus.utilizado, ProductItemStatus.em_estoque
        )


# ── Reserve stock tests ───────────────────────────────────────────────────────


def test_reserve_stock_sufficient(client: TestClient, db: Session) -> None:
    from app import crud
    from app.models import ServiceCreate, ServiceType

    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    product = _create_product(client, headers, product_type_id=pt["id"])
    _create_product_item(client, headers, product_id=product["id"], quantity=50.0)

    # Create a service to reserve for
    client_resp = client.post(
        f"{settings.API_V1_STR}/clients",
        json={
            "name": random_lower_string(),
            "document_type": "cpf",
            "document_number": "12345678901",
            "email": f"{random_lower_string()}@example.com",
        },
        headers=headers,
    )
    client_id = client_resp.json()["id"]
    svc = crud.create_service(
        session=db,
        service_in=ServiceCreate(
            type=ServiceType.perfuracao,
            execution_address="Test Address 123",
            client_id=uuid.UUID(client_id),
        ),
    )

    warnings = crud.reserve_stock_for_service(
        db,
        service_id=svc.id,
        product_quantities=[(uuid.UUID(product["id"]), Decimal("20"))],
    )
    assert warnings == []

    # Verify items are reservado
    from sqlmodel import select

    from app.models import ProductItem

    items = list(
        db.exec(
            select(ProductItem).where(
                ProductItem.product_id == uuid.UUID(product["id"]),
                ProductItem.status == ProductItemStatus.reservado,
            )
        ).all()
    )
    assert len(items) > 0


def test_reserve_stock_insufficient(client: TestClient, db: Session) -> None:
    from app import crud
    from app.models import ServiceCreate, ServiceType

    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    product = _create_product(client, headers, product_type_id=pt["id"])
    _create_product_item(client, headers, product_id=product["id"], quantity=5.0)

    client_resp = client.post(
        f"{settings.API_V1_STR}/clients",
        json={
            "name": random_lower_string(),
            "document_type": "cpf",
            "document_number": "98765432100",
            "email": f"{random_lower_string()}@example.com",
        },
        headers=headers,
    )
    client_id = client_resp.json()["id"]
    svc = crud.create_service(
        session=db,
        service_in=ServiceCreate(
            type=ServiceType.perfuracao,
            execution_address="Test Address 456",
            client_id=uuid.UUID(client_id),
        ),
    )

    warnings = crud.reserve_stock_for_service(
        db,
        service_id=svc.id,
        product_quantities=[(uuid.UUID(product["id"]), Decimal("100"))],
    )
    assert len(warnings) == 1
    assert warnings[0].product_id == uuid.UUID(product["id"])
    assert warnings[0].shortfall_qty > 0


def test_utilize_reserved_items(client: TestClient, db: Session) -> None:
    from app import crud
    from app.models import ServiceCreate, ServiceType

    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    product = _create_product(client, headers, product_type_id=pt["id"])
    _create_product_item(client, headers, product_id=product["id"], quantity=30.0)

    client_resp = client.post(
        f"{settings.API_V1_STR}/clients",
        json={
            "name": random_lower_string(),
            "document_type": "cpf",
            "document_number": "11122233344",
            "email": f"{random_lower_string()}@example.com",
        },
        headers=headers,
    )
    client_id = client_resp.json()["id"]
    svc = crud.create_service(
        session=db,
        service_in=ServiceCreate(
            type=ServiceType.perfuracao,
            execution_address="Test Address 789",
            client_id=uuid.UUID(client_id),
        ),
    )

    crud.reserve_stock_for_service(
        db,
        service_id=svc.id,
        product_quantities=[(uuid.UUID(product["id"]), Decimal("10"))],
    )

    count = crud.utilize_reserved_items_for_service(db, service_id=svc.id)
    assert count > 0

    # Verify items are utilizado
    from sqlmodel import select

    from app.models import ProductItem

    utilized_items = list(
        db.exec(
            select(ProductItem).where(
                ProductItem.service_id == svc.id,
                ProductItem.status == ProductItemStatus.utilizado,
            )
        ).all()
    )
    assert len(utilized_items) > 0


# ── Prediction tests ──────────────────────────────────────────────────────────


def test_get_product_prediction_no_history(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    product = _create_product(client, headers, product_type_id=pt["id"])
    resp = client.get(f"{P_PREFIX}/{product['id']}/prediction", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["days_to_stockout"] is None
    assert data["level"] == "green"


def test_get_product_prediction_with_stock(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    product = _create_product(client, headers, product_type_id=pt["id"])
    _create_product_item(client, headers, product_id=product["id"], quantity=500.0)
    resp = client.get(f"{P_PREFIX}/{product['id']}/prediction", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert float(data["em_estoque_qty"]) == 500.0


def test_get_product_prediction_not_found(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    resp = client.get(f"{P_PREFIX}/{uuid.uuid4()}/prediction", headers=headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_get_product_items_list(
    client: TestClient,
    db: Session,  # noqa: ARG001
) -> None:
    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    product = _create_product(client, headers, product_type_id=pt["id"])
    _create_product_item(client, headers, product_id=product["id"])
    resp = client.get(f"{P_PREFIX}/{product['id']}/items", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


# ── Dashboard tests ────────────────────────────────────────────────────────────


def test_get_dashboard_admin(client: TestClient, db: Session) -> None:  # noqa: ARG001
    headers = _superuser_headers(client)
    resp = client.get(f"{ESTOQUE_PREFIX}/dashboard", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert isinstance(data, list)
    # Should return all 5 categories
    assert len(data) == 5
    cats = {item["category"] for item in data}
    assert cats == {c.value for c in ProductCategory}


def test_get_dashboard_finance(client: TestClient, db: Session) -> None:
    headers = _create_user_with_role(client, db, UserRole.finance)
    resp = client.get(f"{ESTOQUE_PREFIX}/dashboard", headers=headers)
    assert resp.status_code == HTTPStatus.OK


def test_get_dashboard_client_forbidden(client: TestClient, db: Session) -> None:
    headers = _create_user_with_role(client, db, UserRole.client)
    resp = client.get(f"{ESTOQUE_PREFIX}/dashboard", headers=headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN


# ── Baixar estoque tests ───────────────────────────────────────────────────────


def test_baixar_estoque_on_executing_service(client: TestClient, db: Session) -> None:
    from app import crud
    from app.models import ServiceCreate, ServiceType

    headers = _superuser_headers(client)
    pt = _create_product_type(client, headers)
    product = _create_product(client, headers, product_type_id=pt["id"])
    _create_product_item(client, headers, product_id=product["id"], quantity=50.0)

    # Create client
    client_resp = client.post(
        f"{settings.API_V1_STR}/clients",
        json={
            "name": random_lower_string(),
            "document_type": "cpf",
            "document_number": "55566677788",
            "email": f"{random_lower_string()}@example.com",
        },
        headers=headers,
    )
    client_id = uuid.UUID(client_resp.json()["id"])

    svc = crud.create_service(
        session=db,
        service_in=ServiceCreate(
            type=ServiceType.perfuracao,
            execution_address="Address 101",
            client_id=client_id,
        ),
    )

    # Reserve stock
    crud.reserve_stock_for_service(
        db,
        service_id=svc.id,
        product_quantities=[(uuid.UUID(product["id"]), Decimal("10"))],
    )

    # Transition to scheduled, then executing
    # Get the actual admin user id
    from sqlmodel import select

    from app.models import User

    admin = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()
    assert admin is not None

    crud.transition_service_status(
        db, svc, to_status=ServiceStatus.scheduled, changed_by_id=admin.id
    )
    crud.transition_service_status(
        db, svc, to_status=ServiceStatus.executing, changed_by_id=admin.id
    )

    resp = client.post(f"{SERVICES_PREFIX}/{svc.id}/baixar-estoque", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["service_id"] == str(svc.id)
    assert data["items_updated"] >= 0


def test_baixar_estoque_non_executing_service(client: TestClient, db: Session) -> None:
    from app import crud
    from app.models import ServiceCreate, ServiceType

    headers = _superuser_headers(client)

    client_resp = client.post(
        f"{settings.API_V1_STR}/clients",
        json={
            "name": random_lower_string(),
            "document_type": "cpf",
            "document_number": "99988877766",
            "email": f"{random_lower_string()}@example.com",
        },
        headers=headers,
    )
    client_id = uuid.UUID(client_resp.json()["id"])

    svc = crud.create_service(
        session=db,
        service_in=ServiceCreate(
            type=ServiceType.reparo,
            execution_address="Address 202",
            client_id=client_id,
        ),
    )

    resp = client.post(f"{SERVICES_PREFIX}/{svc.id}/baixar-estoque", headers=headers)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

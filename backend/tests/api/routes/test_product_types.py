"""Per-router tests for the product-types endpoints.

Broad CRUD/validation coverage for this router lives in ``test_estoque.py``.
This module targets the edge cases not exercised there: the 404 branches on
update/delete, and the permission matrix (client-role forbidden, unauthenticated).
"""

import uuid
from http import HTTPStatus

from fastapi.testclient import TestClient

from app.core.config import settings

PREFIX = f"{settings.API_V1_STR}/product-types"


def test_update_product_type_not_found(
    client: TestClient, admin_token_headers: dict[str, str]
) -> None:
    resp = client.patch(
        f"{PREFIX}/{uuid.uuid4()}",
        json={"name": "x"},
        headers=admin_token_headers,
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_delete_product_type_not_found(
    client: TestClient, admin_token_headers: dict[str, str]
) -> None:
    resp = client.delete(f"{PREFIX}/{uuid.uuid4()}", headers=admin_token_headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_list_product_types_client_forbidden(
    client: TestClient, client_token_headers: dict[str, str]
) -> None:
    resp = client.get(PREFIX, headers=client_token_headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_list_product_types_unauthenticated(client: TestClient) -> None:
    resp = client.get(PREFIX)
    assert resp.status_code == HTTPStatus.UNAUTHORIZED

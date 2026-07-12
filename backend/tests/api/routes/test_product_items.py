"""Per-router tests for the product-items endpoints.

The product-items router exposes only create + list. Broad coverage lives in
``test_estoque.py``; this module adds the permission matrix (client-role
forbidden, unauthenticated) and a status-filter check on the list endpoint.
"""

from http import HTTPStatus

from fastapi.testclient import TestClient

from app.core.config import settings
from app.models import ProductItem, ProductItemStatus

PREFIX = f"{settings.API_V1_STR}/product-items"


def test_list_product_items_client_forbidden(
    client: TestClient, client_token_headers: dict[str, str]
) -> None:
    resp = client.get(PREFIX, headers=client_token_headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_list_product_items_unauthenticated(client: TestClient) -> None:
    resp = client.get(PREFIX)
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_list_product_items_filter_by_status(
    client: TestClient,
    admin_token_headers: dict[str, str],
    product_item: ProductItem,
) -> None:
    resp = client.get(
        PREFIX,
        params={"status": ProductItemStatus.em_estoque.value},
        headers=admin_token_headers,
    )
    assert resp.status_code == HTTPStatus.OK
    ids = [item["id"] for item in resp.json()]
    assert str(product_item.id) in ids

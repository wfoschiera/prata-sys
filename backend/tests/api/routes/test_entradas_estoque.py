"""Tests for the entrada de estoque / custo de aquisição endpoints.

Covers the apportionment maths, the typed-adjustment validation rules, the
weighted-average coverage reporting, and the permission matrix.
"""

import uuid
from decimal import Decimal
from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import CustoAjuste, EntradaEstoque, ProductItem, Transacao
from tests.factories import ProductFactory

PREFIX = f"{settings.API_V1_STR}/entradas-estoque"
PRODUCTS_PREFIX = f"{settings.API_V1_STR}/products"


def _payload(
    *,
    itens: list[dict[str, object]],
    ajustes: list[dict[str, object]] | None = None,
    **overrides: object,
) -> dict[str, object]:
    body: dict[str, object] = {
        "data_entrada": "2026-08-01",
        "itens": itens,
        "ajustes": ajustes or [],
    }
    body.update(overrides)
    return body


def _item(product_id: uuid.UUID, quantity: str, custo: str) -> dict[str, object]:
    return {
        "product_id": str(product_id),
        "quantity": quantity,
        "custo_unitario_nf": custo,
    }


def _real(item: dict[str, object]) -> Decimal:
    return Decimal(str(item["custo_unitario_real"]))


def _by_product(
    itens: list[dict[str, object]], product_id: uuid.UUID
) -> dict[str, object]:
    return next(i for i in itens if i["product_id"] == str(product_id))


# ── Entrada creation ───────────────────────────────────────────────────────────


def test_create_entrada_creates_stock_lots(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    p1 = ProductFactory()
    p2 = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p1.id, "10", "100.00"), _item(p2.id, "5", "200.00")]
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CREATED
    data = resp.json()
    assert len(data["itens"]) == 2

    lots = db.exec(
        select(ProductItem).where(ProductItem.entrada_id == uuid.UUID(data["id"]))
    ).all()
    assert len(lots) == 2
    assert all(lot.status == "em_estoque" for lot in lots)
    assert all(lot.service_id is None for lot in lots)


def test_create_entrada_requires_manage_estoque(
    client: TestClient, finance_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(itens=[_item(p.id, "1", "10.00")]),
        headers=finance_token_headers,
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_create_entrada_client_role_forbidden(
    client: TestClient, client_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(itens=[_item(p.id, "1", "10.00")]),
        headers=client_token_headers,
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_create_entrada_without_items_rejected(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    resp = client.post(PREFIX, json=_payload(itens=[]), headers=superuser_token_headers)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_entrada_negative_quantity_rejected(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(itens=[_item(p.id, "0", "10.00")]),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_entrada_unknown_product_is_atomic(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    """A bad reference on the second line must leave no partial records."""
    p1 = ProductFactory()
    missing = uuid.uuid4()
    entradas_before = len(db.exec(select(EntradaEstoque)).all())
    lots_before = len(
        db.exec(select(ProductItem).where(ProductItem.product_id == p1.id)).all()
    )

    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p1.id, "10", "100.00"), _item(missing, "1", "1.00")]
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND

    db.expire_all()
    assert len(db.exec(select(EntradaEstoque)).all()) == entradas_before
    assert (
        len(db.exec(select(ProductItem).where(ProductItem.product_id == p1.id)).all())
        == lots_before
    )


# ── Apportionment ──────────────────────────────────────────────────────────────


def test_freight_apportioned_by_value_share(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Spec worked example: 10 x 100,00 and 5 x 200,00 with frete 200,00."""
    p1 = ProductFactory()
    p2 = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p1.id, "10", "100.00"), _item(p2.id, "5", "200.00")],
            ajustes=[
                {
                    "tipo": "frete",
                    "valor": "200.00",
                    "documento_referencia": "CTE-123",
                }
            ],
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CREATED
    itens = resp.json()["itens"]
    assert _real(_by_product(itens, p1.id)) == Decimal("110")
    assert _real(_by_product(itens, p2.id)) == Decimal("220")


def test_apportioned_shares_reconcile_to_total(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """An uneven three-way split must still sum back to the adjustment total."""
    products = [ProductFactory() for _ in range(3)]
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p.id, "1", "1.00") for p in products],
            ajustes=[{"tipo": "frete", "valor": "100.00"}],
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CREATED
    data = resp.json()
    recomposed = sum(
        (_real(i) * Decimal(str(i["quantity"])) for i in data["itens"]), Decimal(0)
    )
    expected = Decimal(str(data["total_produtos"])) + Decimal(
        str(data["total_ajustes"])
    )
    assert recomposed == expected
    assert Decimal(str(data["total_real"])) == expected


def test_bonificacao_receives_no_freight_share(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    priced = ProductFactory()
    bonificado = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[
                _item(priced.id, "10", "100.00"),
                _item(bonificado.id, "2", "0.00"),
            ],
            ajustes=[{"tipo": "frete", "valor": "200.00"}],
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CREATED
    itens = resp.json()["itens"]
    assert _real(_by_product(itens, bonificado.id)) == Decimal("0")
    # Entire freight lands on the priced lot: (1000 + 200) / 10
    assert _real(_by_product(itens, priced.id)) == Decimal("120")


def test_discount_reduces_real_cost_below_invoice(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p.id, "10", "100.00")],
            ajustes=[{"tipo": "desconto_comercial", "valor": "-100.00"}],
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CREATED
    assert _real(resp.json()["itens"][0]) == Decimal("90")


def test_zero_value_entrada_falls_back_to_quantity_share(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """An all-bonificação delivery still apportions its freight, by quantity."""
    p1 = ProductFactory()
    p2 = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p1.id, "3", "0.00"), _item(p2.id, "1", "0.00")],
            ajustes=[{"tipo": "frete", "valor": "40.00"}],
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CREATED
    itens = resp.json()["itens"]
    assert _real(_by_product(itens, p1.id)) == Decimal("10")
    assert _real(_by_product(itens, p2.id)) == Decimal("10")


# ── Adjustment validation ──────────────────────────────────────────────────────


def test_positive_value_on_discount_type_rejected(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p.id, "1", "10.00")],
            ajustes=[{"tipo": "desconto_comercial", "valor": "50.00"}],
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_negative_value_on_freight_rejected(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p.id, "1", "10.00")],
            ajustes=[{"tipo": "frete", "valor": "-50.00"}],
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_zero_value_adjustment_rejected(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p.id, "1", "10.00")],
            ajustes=[{"tipo": "frete", "valor": "0"}],
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_unclassified_adjustment_rejected(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """An adjustment amount with no tipo has no place to go."""
    p = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p.id, "1", "10.00")],
            ajustes=[{"valor": "50.00"}],
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_outros_without_observacao_rejected(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p.id, "1", "10.00")],
            ajustes=[{"tipo": "outros", "valor": "50.00"}],
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_outros_with_observacao_accepted(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p.id, "1", "10.00")],
            ajustes=[
                {
                    "tipo": "outros",
                    "valor": "50.00",
                    "observacao": "Taxa de descarga cobrada no ato",
                }
            ],
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CREATED


# ── Adjustments on an existing entrada ─────────────────────────────────────────


def _create_simple_entrada(
    client: TestClient,
    headers: dict[str, str],
    quantity: str = "10",
    custo: str = "100.00",
) -> dict[str, object]:
    p = ProductFactory()
    resp = client.post(
        PREFIX, json=_payload(itens=[_item(p.id, quantity, custo)]), headers=headers
    )
    assert resp.status_code == HTTPStatus.CREATED
    return resp.json()


def test_add_freight_adjustment_to_existing_entrada(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    entrada = _create_simple_entrada(client, superuser_token_headers)
    resp = client.post(
        f"{PREFIX}/{entrada['id']}/ajustes",
        json={
            "tipo": "frete",
            "valor": "200.00",
            "documento_referencia": "CTE-999",
        },
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CREATED

    detail = client.get(
        f"{PREFIX}/{entrada['id']}", headers=superuser_token_headers
    ).json()
    assert _real(detail["itens"][0]) == Decimal("120")
    assert detail["ajustes"][0]["documento_referencia"] == "CTE-999"


def test_correction_preserves_original_invoice_cost(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """A correction shifts real cost but never rewrites custo_unitario_nf."""
    entrada = _create_simple_entrada(client, superuser_token_headers)
    resp = client.post(
        f"{PREFIX}/{entrada['id']}/ajustes",
        json={
            "tipo": "correcao_documento",
            "valor": "50.00",
            "documento_referencia": "CCe-001",
        },
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CREATED

    detail = client.get(
        f"{PREFIX}/{entrada['id']}", headers=superuser_token_headers
    ).json()
    item = detail["itens"][0]
    assert Decimal(str(item["custo_unitario_nf"])) == Decimal("100")
    assert _real(item) == Decimal("105")


def test_add_adjustment_requires_manage_estoque(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    finance_token_headers: dict[str, str],
) -> None:
    entrada = _create_simple_entrada(client, superuser_token_headers)
    resp = client.post(
        f"{PREFIX}/{entrada['id']}/ajustes",
        json={"tipo": "frete", "valor": "10.00"},
        headers=finance_token_headers,
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_add_adjustment_to_unknown_entrada(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    resp = client.post(
        f"{PREFIX}/{uuid.uuid4()}/ajustes",
        json={"tipo": "frete", "valor": "10.00"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_delete_adjustment(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    entrada = _create_simple_entrada(client, superuser_token_headers)
    created = client.post(
        f"{PREFIX}/{entrada['id']}/ajustes",
        json={"tipo": "frete", "valor": "200.00"},
        headers=superuser_token_headers,
    ).json()

    resp = client.delete(
        f"{PREFIX}/{entrada['id']}/ajustes/{created['id']}",
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT

    db.expire_all()
    assert db.get(CustoAjuste, uuid.UUID(created["id"])) is None
    detail = client.get(
        f"{PREFIX}/{entrada['id']}", headers=superuser_token_headers
    ).json()
    assert _real(detail["itens"][0]) == Decimal("100")


# ── Despesa booking ────────────────────────────────────────────────────────────


def test_criar_transacao_books_the_expense(
    client: TestClient,
    db: Session,
    fornecedor: object,
    superuser_token_headers: dict[str, str],
) -> None:
    p1 = ProductFactory()
    p2 = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p1.id, "10", "100.00"), _item(p2.id, "5", "200.00")],
            ajustes=[{"tipo": "frete", "valor": "200.00"}],
            fornecedor_id=str(fornecedor.id),  # type: ignore[attr-defined]
            criar_transacao=True,
        ),
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CREATED
    data = resp.json()
    assert data["transacao_id"] is not None

    transacao = db.get(Transacao, uuid.UUID(data["transacao_id"]))
    assert transacao is not None
    assert transacao.tipo == "despesa"
    assert transacao.categoria == "COMPRA_MATERIAL"
    assert transacao.valor == Decimal("2200.00")
    assert transacao.fornecedor_id == fornecedor.id  # type: ignore[attr-defined]


def test_no_transacao_created_by_default(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    entrada = _create_simple_entrada(client, superuser_token_headers)
    assert entrada["transacao_id"] is None


def test_criar_transacao_requires_manage_financeiro(
    client: TestClient, db: Session, admin_token_headers: dict[str, str]
) -> None:
    """Admin holds manage_estoque but not manage_financeiro."""
    p = ProductFactory()
    entradas_before = len(db.exec(select(EntradaEstoque)).all())

    resp = client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p.id, "1", "10.00")],
            criar_transacao=True,
        ),
        headers=admin_token_headers,
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN

    db.expire_all()
    assert len(db.exec(select(EntradaEstoque)).all()) == entradas_before


# ── Listing and detail ─────────────────────────────────────────────────────────


def test_list_filters_by_fornecedor(
    client: TestClient,
    fornecedor: object,
    superuser_token_headers: dict[str, str],
) -> None:
    p = ProductFactory()
    client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p.id, "1", "10.00")],
            fornecedor_id=str(fornecedor.id),  # type: ignore[attr-defined]
        ),
        headers=superuser_token_headers,
    )
    _create_simple_entrada(client, superuser_token_headers)

    resp = client.get(
        PREFIX,
        params={"fornecedor_id": str(fornecedor.id)},  # type: ignore[attr-defined]
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert len(data) == 1
    assert data[0]["fornecedor_id"] == str(fornecedor.id)  # type: ignore[attr-defined]


def test_get_unknown_entrada_returns_404(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    resp = client.get(f"{PREFIX}/{uuid.uuid4()}", headers=superuser_token_headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_list_requires_view_estoque(
    client: TestClient, client_token_headers: dict[str, str]
) -> None:
    resp = client.get(PREFIX, headers=client_token_headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_finance_can_read_entradas(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    finance_token_headers: dict[str, str],
) -> None:
    _create_simple_entrada(client, superuser_token_headers)
    resp = client.get(PREFIX, headers=finance_token_headers)
    assert resp.status_code == HTTPStatus.OK


def test_entrada_list_has_no_n_plus_one(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    from sqlalchemy import event

    for _ in range(5):
        p1 = ProductFactory()
        p2 = ProductFactory()
        client.post(
            PREFIX,
            json=_payload(
                itens=[_item(p1.id, "2", "10.00"), _item(p2.id, "3", "20.00")],
                ajustes=[{"tipo": "frete", "valor": "5.00"}],
            ),
            headers=superuser_token_headers,
        )

    statement_count = 0
    engine = db.get_bind()

    def before_cursor_execute(*_args: object) -> None:  # noqa: ARG001
        nonlocal statement_count
        statement_count += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        resp = client.get(PREFIX, headers=superuser_token_headers)
        assert resp.status_code == HTTPStatus.OK
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)

    assert statement_count <= 10, f"Too many SQL statements: {statement_count}"


# ── Weighted average cost ──────────────────────────────────────────────────────


def test_weighted_average_is_quantity_weighted(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    client.post(
        PREFIX,
        json=_payload(itens=[_item(p.id, "10", "100.00")]),
        headers=superuser_token_headers,
    )
    client.post(
        PREFIX,
        json=_payload(itens=[_item(p.id, "30", "200.00")]),
        headers=superuser_token_headers,
    )

    resp = client.get(f"{PRODUCTS_PREFIX}/{p.id}", headers=superuser_token_headers)
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    # (10*100 + 30*200) / 40 = 175
    assert Decimal(str(data["custo_medio_ponderado"])) == Decimal("175")
    assert data["lotes_sem_custo"] == 0


def test_weighted_average_excludes_and_counts_costless_lots(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    client.post(
        PREFIX,
        json=_payload(itens=[_item(p.id, "10", "100.00")]),
        headers=superuser_token_headers,
    )
    # Lots created through the legacy path carry no cost.
    for _ in range(3):
        db.add(ProductItem(product_id=p.id, quantity=Decimal("5")))
    db.commit()

    resp = client.get(f"{PRODUCTS_PREFIX}/{p.id}", headers=superuser_token_headers)
    data = resp.json()
    assert Decimal(str(data["custo_medio_ponderado"])) == Decimal("100")
    assert data["lotes_sem_custo"] == 3


def test_weighted_average_is_null_when_no_priced_stock(
    client: TestClient, product: object, superuser_token_headers: dict[str, str]
) -> None:
    resp = client.get(
        f"{PRODUCTS_PREFIX}/{product.id}",  # type: ignore[attr-defined]
        headers=superuser_token_headers,
    )
    data = resp.json()
    assert data["custo_medio_ponderado"] is None


def test_weighted_average_reflects_adjustments(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    client.post(
        PREFIX,
        json=_payload(
            itens=[_item(p.id, "10", "100.00")],
            ajustes=[{"tipo": "frete", "valor": "200.00"}],
        ),
        headers=superuser_token_headers,
    )
    resp = client.get(f"{PRODUCTS_PREFIX}/{p.id}", headers=superuser_token_headers)
    assert Decimal(str(resp.json()["custo_medio_ponderado"])) == Decimal("120")


def test_weighted_average_ignores_non_em_estoque_lots(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    p = ProductFactory()
    resp = client.post(
        PREFIX,
        json=_payload(itens=[_item(p.id, "10", "100.00"), _item(p.id, "10", "500.00")]),
        headers=superuser_token_headers,
    )
    entrada_id = uuid.UUID(resp.json()["id"])

    expensive = db.exec(
        select(ProductItem)
        .where(ProductItem.entrada_id == entrada_id)
        .where(ProductItem.custo_unitario_nf == Decimal("500.0000"))
    ).one()
    expensive.status = "utilizado"  # type: ignore[assignment]
    db.add(expensive)
    db.commit()

    data = client.get(
        f"{PRODUCTS_PREFIX}/{p.id}", headers=superuser_token_headers
    ).json()
    assert Decimal(str(data["custo_medio_ponderado"])) == Decimal("100")


def test_product_list_cost_has_no_n_plus_one(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    from sqlalchemy import event

    for _ in range(5):
        p = ProductFactory()
        client.post(
            PREFIX,
            json=_payload(
                itens=[_item(p.id, "2", "10.00"), _item(p.id, "3", "20.00")],
                ajustes=[{"tipo": "frete", "valor": "5.00"}],
            ),
            headers=superuser_token_headers,
        )

    statement_count = 0
    engine = db.get_bind()

    def before_cursor_execute(*_args: object) -> None:  # noqa: ARG001
        nonlocal statement_count
        statement_count += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        resp = client.get(PRODUCTS_PREFIX, headers=superuser_token_headers)
        assert resp.status_code == HTTPStatus.OK
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)

    assert statement_count <= 10, f"Too many SQL statements: {statement_count}"


# ── Immutability of the invoice cost ───────────────────────────────────────────


def test_no_write_surface_for_custo_unitario_nf(
    client: TestClient, product_item: object, superuser_token_headers: dict[str, str]
) -> None:
    """Immutability is enforced by absence: no update schema, no PATCH route."""
    import app.models as models

    # No /product-items/{id} route exists at all, so the path itself is unmatched.
    resp = client.patch(
        f"{settings.API_V1_STR}/product-items/{product_item.id}",  # type: ignore[attr-defined]
        json={"custo_unitario_nf": "1.00"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND

    writable = [
        name
        for name in dir(models)
        if name.endswith(("Create", "Update"))
        and hasattr(getattr(models, name), "model_fields")
        and "custo_unitario_nf" in getattr(models, name).model_fields
    ]
    assert writable == ["EntradaItemCreate"], (
        f"custo_unitario_nf must only be writable at lot creation, found: {writable}"
    )


# ── Migration safety ───────────────────────────────────────────────────────────


def test_migration_does_not_rewrite_productitem_updated_at() -> None:
    """get_stock_prediction infers consumption from ProductItem.updated_at.

    The migration that adds the cost columns must be purely additive — any UPDATE
    against productitem would bump updated_at and corrupt the 90-day window.
    """
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[3]
        / "app"
        / "alembic"
        / "versions"
        / "d4e5f6a7b8c9_add_entrada_estoque_and_custo_ajuste.py"
    )
    upgrade_src = migration.read_text().lower().split("def downgrade")[0]
    assert "op.add_column('productitem'" in upgrade_src

    # Strip comments — they legitimately mention UPDATE when explaining the rule.
    code = "\n".join(line.split("#")[0] for line in upgrade_src.splitlines())
    assert "op.execute" not in code, (
        "upgrade() must not run raw SQL against existing rows"
    )
    for forbidden in ("update ", "update("):
        assert forbidden not in code, (
            f"migration must not issue an UPDATE (found {forbidden!r})"
        )

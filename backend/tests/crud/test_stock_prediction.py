"""Unit tests for get_stock_prediction — exercises all branching logic.

These tests run against a real DB session (via the session-scoped `db` fixture)
but use isolated product records to avoid interference with other tests.
"""

import uuid
from decimal import Decimal

import pytest
from sqlmodel import Session

from app import crud
from app.models import (
    Product,
    ProductItem,
    ProductItemStatus,
)
from tests.factories import ProductFactory

# ── Helpers ────────────────────────────────────────────────────────────────────


def _add_items(
    db: Session,
    product_id: uuid.UUID,
    status: ProductItemStatus,
    quantity: float,
    count: int = 1,
) -> None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    for _ in range(count):
        item = ProductItem(
            product_id=product_id,
            quantity=Decimal(str(quantity)),
            status=status,
            # Set updated_at so the 90-day consumption window picks up utilizado items.
            # The prediction function filters utilizado items by updated_at >= 90 days ago.
            updated_at=now,
        )
        db.add(item)
    db.commit()


# ── Tests ──────────────────────────────────────────────────────────────────────


def test_prediction_no_stock_no_history(db: Session) -> None:
    """Product with zero stock and no consumption history → green, no stockout date."""
    prod: Product = ProductFactory()  # type: ignore[assignment]
    result = crud.get_stock_prediction(session=db, product_id=prod.id)

    assert result.level == "green"
    assert result.days_to_stockout is None
    assert result.em_estoque_qty == Decimal("0")
    assert result.reservado_qty == Decimal("0")
    assert result.avg_daily_consumption is None


def test_prediction_stock_available_no_history(db: Session) -> None:
    """Stock available but no consumption history → green (cannot predict)."""
    prod: Product = ProductFactory()  # type: ignore[assignment]
    _add_items(db, prod.id, ProductItemStatus.em_estoque, quantity=50.0)

    result = crud.get_stock_prediction(session=db, product_id=prod.id)

    assert result.level == "green"
    assert result.days_to_stockout is None
    assert result.em_estoque_qty == Decimal("50")


def test_prediction_all_reserved_no_history(db: Session) -> None:
    """All stock reserved, no consumption history → yellow."""
    prod: Product = ProductFactory()  # type: ignore[assignment]
    _add_items(db, prod.id, ProductItemStatus.reservado, quantity=10.0)

    result = crud.get_stock_prediction(session=db, product_id=prod.id)

    assert result.level == "yellow"
    assert result.days_to_stockout is None
    assert result.reservado_qty == Decimal("10")


def test_prediction_net_stock_zero_with_history(db: Session) -> None:
    """Net stock ≤ 0 with consumption history → red."""
    prod: Product = ProductFactory()  # type: ignore[assignment]
    # All em_estoque is also all reserved → net = 0
    _add_items(db, prod.id, ProductItemStatus.reservado, quantity=20.0)
    _add_items(db, prod.id, ProductItemStatus.utilizado, quantity=1.0)

    result = crud.get_stock_prediction(session=db, product_id=prod.id)

    assert result.level == "red"


def test_prediction_red_threshold(db: Session) -> None:
    """≤ 7 days to stockout → red."""
    prod: Product = ProductFactory()  # type: ignore[assignment]
    # 7 units in stock, consuming 1/day → 7 days → red
    _add_items(db, prod.id, ProductItemStatus.em_estoque, quantity=7.0)
    # Simulate 90 days of consumption: 90 units utilizado
    _add_items(db, prod.id, ProductItemStatus.utilizado, quantity=90.0)

    result = crud.get_stock_prediction(session=db, product_id=prod.id)

    assert result.level == "red"
    assert result.days_to_stockout is not None
    assert result.days_to_stockout <= 7


def test_prediction_yellow_threshold(db: Session) -> None:
    """8–30 days to stockout → yellow."""
    prod: Product = ProductFactory()  # type: ignore[assignment]
    # 20 units in stock, 1/day avg consumption → 20 days → yellow
    _add_items(db, prod.id, ProductItemStatus.em_estoque, quantity=20.0)
    _add_items(db, prod.id, ProductItemStatus.utilizado, quantity=90.0)

    result = crud.get_stock_prediction(session=db, product_id=prod.id)

    assert result.level == "yellow"
    assert result.days_to_stockout is not None
    assert 8 <= result.days_to_stockout <= 30


def test_prediction_green_threshold(db: Session) -> None:
    """31+ days to stockout → green."""
    prod: Product = ProductFactory()  # type: ignore[assignment]
    # 100 units in stock, 1/day avg → 100 days → green
    _add_items(db, prod.id, ProductItemStatus.em_estoque, quantity=100.0)
    _add_items(db, prod.id, ProductItemStatus.utilizado, quantity=90.0)

    result = crud.get_stock_prediction(session=db, product_id=prod.id)

    assert result.level == "green"
    assert result.days_to_stockout is not None
    assert result.days_to_stockout > 30


def test_prediction_product_not_found_returns_zero(db: Session) -> None:
    """Non-existent product_id → all zeros, green."""
    result = crud.get_stock_prediction(session=db, product_id=uuid.uuid4())

    assert result.level == "green"
    assert result.em_estoque_qty == Decimal("0")
    assert result.reservado_qty == Decimal("0")
    assert result.days_to_stockout is None


@pytest.mark.parametrize(
    ("em_estoque", "reservado", "utilizado_90d", "expected_level"),
    [
        (0, 0, 0, "green"),  # zero everything
        (10, 0, 0, "green"),  # stock with no history
        (0, 10, 0, "yellow"),  # all reserved, no history
        (5, 0, 450, "red"),  # 5 units, 5/day → 1 day → red
        (15, 0, 90, "yellow"),  # 15 units, 1/day → 15 days → yellow
        (50, 0, 90, "green"),  # 50 units, 1/day → 50 days → green
    ],
)
def test_prediction_parametrized(
    db: Session,
    em_estoque: float,
    reservado: float,
    utilizado_90d: float,
    expected_level: str,
) -> None:
    """Parametrized coverage of all level branches."""
    prod: Product = ProductFactory()  # type: ignore[assignment]
    if em_estoque:
        _add_items(db, prod.id, ProductItemStatus.em_estoque, quantity=em_estoque)
    if reservado:
        _add_items(db, prod.id, ProductItemStatus.reservado, quantity=reservado)
    if utilizado_90d:
        _add_items(db, prod.id, ProductItemStatus.utilizado, quantity=utilizado_90d)

    result = crud.get_stock_prediction(session=db, product_id=prod.id)
    assert result.level == expected_level

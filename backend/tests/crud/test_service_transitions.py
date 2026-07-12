"""CRUD-level unit tests for service status transitions.

These tests exercise transition_service_status() directly — no HTTP layer.
This catches logic bugs in the state machine without the overhead of route setup.
"""

import logging
import uuid
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from app import crud
from app.models import (
    DeductionItem,
    ProductItem,
    ProductItemStatus,
    Service,
    ServiceStatus,
)
from tests.factories import (
    ProductFactory,
    ProductItemFactory,
    ServiceFactory,
    ServiceItemFactory,
)

# ── Helpers ────────────────────────────────────────────────────────────────────


def _transition(
    db: Session,
    service: Service,
    to_status: ServiceStatus,
    *,
    reason: str | None = None,
    deduction_items=None,
    superuser_id: uuid.UUID,
) -> tuple[Service, list]:
    return crud.transition_service_status(
        session=db,
        service=service,
        to_status=to_status,
        changed_by_id=superuser_id,
        reason=reason,
        deduction_items=deduction_items or [],
    )


# ── Valid transition tests ─────────────────────────────────────────────────────


def test_requested_to_scheduled(db: Session, superuser_id: uuid.UUID) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    assert svc.status == ServiceStatus.requested
    updated, warnings = _transition(
        db, svc, ServiceStatus.scheduled, superuser_id=superuser_id
    )
    assert updated.status == ServiceStatus.scheduled
    assert warnings == []


def test_scheduled_to_executing(db: Session, superuser_id: uuid.UUID) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    _transition(db, svc, ServiceStatus.scheduled, superuser_id=superuser_id)
    db.refresh(svc)
    updated, warnings = _transition(
        db, svc, ServiceStatus.executing, superuser_id=superuser_id
    )
    assert updated.status == ServiceStatus.executing


def test_executing_to_completed_with_deduction_items(
    db: Session, superuser_id: uuid.UUID
) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    item = ServiceItemFactory(service=svc)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.scheduled, superuser_id=superuser_id)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.executing, superuser_id=superuser_id)
    db.refresh(svc)
    from app.models import DeductionItem

    updated, _ = _transition(
        db,
        svc,
        ServiceStatus.completed,
        deduction_items=[DeductionItem(service_item_id=item.id, quantity=5.0)],
        superuser_id=superuser_id,
    )
    assert updated.status == ServiceStatus.completed


def test_requested_to_cancelled(db: Session, superuser_id: uuid.UUID) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    updated, _ = _transition(
        db,
        svc,
        ServiceStatus.cancelled,
        reason="Cancelado pelo cliente",
        superuser_id=superuser_id,
    )
    assert updated.status == ServiceStatus.cancelled
    assert updated.cancelled_reason == "Cancelado pelo cliente"


def test_scheduled_to_cancelled(db: Session, superuser_id: uuid.UUID) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    _transition(db, svc, ServiceStatus.scheduled, superuser_id=superuser_id)
    db.refresh(svc)
    updated, _ = _transition(
        db,
        svc,
        ServiceStatus.cancelled,
        reason="Motivo teste",
        superuser_id=superuser_id,
    )
    assert updated.status == ServiceStatus.cancelled


def test_executing_to_cancelled(db: Session, superuser_id: uuid.UUID) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    _transition(db, svc, ServiceStatus.scheduled, superuser_id=superuser_id)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.executing, superuser_id=superuser_id)
    db.refresh(svc)
    updated, _ = _transition(
        db, svc, ServiceStatus.cancelled, reason="Emergência", superuser_id=superuser_id
    )
    assert updated.status == ServiceStatus.cancelled


# ── Invalid transition tests ───────────────────────────────────────────────────


def test_invalid_requested_to_executing_raises(
    db: Session, superuser_id: uuid.UUID
) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Cannot transition"):
        _transition(db, svc, ServiceStatus.executing, superuser_id=superuser_id)


def test_invalid_requested_to_completed_raises(
    db: Session, superuser_id: uuid.UUID
) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Cannot transition"):
        _transition(db, svc, ServiceStatus.completed, superuser_id=superuser_id)


def test_invalid_completed_to_anything_raises(
    db: Session, superuser_id: uuid.UUID
) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    item = ServiceItemFactory(service=svc)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.scheduled, superuser_id=superuser_id)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.executing, superuser_id=superuser_id)
    db.refresh(svc)
    from app.models import DeductionItem

    _transition(
        db,
        svc,
        ServiceStatus.completed,
        deduction_items=[DeductionItem(service_item_id=item.id, quantity=5.0)],
        superuser_id=superuser_id,
    )
    db.refresh(svc)
    for bad_status in [
        ServiceStatus.requested,
        ServiceStatus.scheduled,
        ServiceStatus.executing,
        ServiceStatus.cancelled,
    ]:
        with pytest.raises(ValueError, match="Cannot transition"):
            _transition(db, svc, bad_status, superuser_id=superuser_id)


def test_invalid_cancelled_to_anything_raises(
    db: Session, superuser_id: uuid.UUID
) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    _transition(
        db, svc, ServiceStatus.cancelled, reason="Teste", superuser_id=superuser_id
    )
    db.refresh(svc)
    for bad_status in [
        ServiceStatus.requested,
        ServiceStatus.scheduled,
        ServiceStatus.executing,
        ServiceStatus.completed,
    ]:
        with pytest.raises(ValueError, match="Cannot transition"):
            _transition(db, svc, bad_status, superuser_id=superuser_id)


# ── Status log tests ───────────────────────────────────────────────────────────


def test_transition_creates_status_log(db: Session, superuser_id: uuid.UUID) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    _transition(db, svc, ServiceStatus.scheduled, superuser_id=superuser_id)
    logs = crud.get_service_status_logs(session=db, service_id=svc.id)
    assert len(logs) == 1
    assert logs[0].from_status == ServiceStatus.requested
    assert logs[0].to_status == ServiceStatus.scheduled


def test_multiple_transitions_create_ordered_logs(
    db: Session, superuser_id: uuid.UUID
) -> None:
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    _transition(db, svc, ServiceStatus.scheduled, superuser_id=superuser_id)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.executing, superuser_id=superuser_id)
    logs = crud.get_service_status_logs(session=db, service_id=svc.id)
    assert len(logs) == 2
    assert logs[0].from_status == ServiceStatus.requested
    assert logs[1].from_status == ServiceStatus.scheduled


# ── Deduction item validation tests ───────────────────────────────────────────


def test_invalid_deduction_item_id_raises(db: Session, superuser_id: uuid.UUID) -> None:
    """Completing with a service_item_id not belonging to this service raises ValueError."""
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    ServiceItemFactory(service=svc)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.scheduled, superuser_id=superuser_id)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.executing, superuser_id=superuser_id)
    db.refresh(svc)

    with pytest.raises(ValueError, match="not a material item"):
        _transition(
            db,
            svc,
            ServiceStatus.completed,
            deduction_items=[DeductionItem(service_item_id=uuid.uuid4(), quantity=1.0)],
            superuser_id=superuser_id,
        )


# ── Stock deduction quantities on completion (issue #102) ───────────────────────


def _items_for_product(db: Session, product_id: uuid.UUID) -> list[ProductItem]:
    return list(
        db.exec(
            select(ProductItem).where(ProductItem.product_id == product_id)
        ).all()
    )


def _setup_reserved_service(
    db: Session,
    superuser_id: uuid.UUID,
    *,
    item_qtys: list[str],
    needed: float,
) -> tuple[Service, uuid.UUID, uuid.UUID]:
    """Build a product with reserved stock and advance a service to executing.

    Creates one ProductItem per entry in ``item_qtys`` (all em_estoque), a service
    with a single material ServiceItem scoped to that product needing ``needed``
    units, then schedules (reserves) and moves it to executing. Returns the
    service, the service-item id, and the product id.
    """
    product = ProductFactory()  # type: ignore[assignment]
    for qty in item_qtys:
        ProductItemFactory(product=product, quantity=Decimal(qty))
    svc: Service = ServiceFactory()  # type: ignore[assignment]
    svc_item = ServiceItemFactory(
        service=svc, product_id=product.id, quantity=needed
    )
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.scheduled, superuser_id=superuser_id)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.executing, superuser_id=superuser_id)
    db.refresh(svc)
    return svc, svc_item.id, product.id


def test_completion_partial_deduction_releases_remainder(
    db: Session, superuser_id: uuid.UUID
) -> None:
    """Deducting less than reserved consumes only what is needed; rest is released."""
    svc, svc_item_id, product_id = _setup_reserved_service(
        db, superuser_id, item_qtys=["5", "5"], needed=10.0
    )
    # Two 5-unit items reserved (total 10). Deduct only 5.
    _transition(
        db,
        svc,
        ServiceStatus.completed,
        deduction_items=[DeductionItem(service_item_id=svc_item_id, quantity=5.0)],
        superuser_id=superuser_id,
    )
    items = _items_for_product(db, product_id)
    utilizado = [i for i in items if i.status == ProductItemStatus.utilizado]
    em_estoque = [i for i in items if i.status == ProductItemStatus.em_estoque]
    assert len(utilizado) == 1
    assert len(em_estoque) == 1
    # Released item is back in stock and no longer tied to the service.
    assert em_estoque[0].service_id is None
    assert not [i for i in items if i.status == ProductItemStatus.reservado]


def test_completion_full_deduction_consumes_all(
    db: Session, superuser_id: uuid.UUID
) -> None:
    """Deducting the full reserved quantity consumes every reserved item."""
    svc, svc_item_id, product_id = _setup_reserved_service(
        db, superuser_id, item_qtys=["5", "5"], needed=10.0
    )
    _transition(
        db,
        svc,
        ServiceStatus.completed,
        deduction_items=[DeductionItem(service_item_id=svc_item_id, quantity=10.0)],
        superuser_id=superuser_id,
    )
    items = _items_for_product(db, product_id)
    assert len(items) == 2
    assert all(i.status == ProductItemStatus.utilizado for i in items)


def test_completion_over_request_consumes_all_reserved_and_logs(
    db: Session,
    superuser_id: uuid.UUID,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Requesting more than reserved consumes all reserved and logs a shortfall."""
    svc, svc_item_id, product_id = _setup_reserved_service(
        db, superuser_id, item_qtys=["5"], needed=5.0
    )
    with caplog.at_level(logging.WARNING, logger="app.crud"):
        updated, _ = _transition(
            db,
            svc,
            ServiceStatus.completed,
            deduction_items=[
                DeductionItem(service_item_id=svc_item_id, quantity=999.0)
            ],
            superuser_id=superuser_id,
        )
    assert updated.status == ServiceStatus.completed
    items = _items_for_product(db, product_id)
    assert all(i.status == ProductItemStatus.utilizado for i in items)
    assert any("service_deduction_shortfall" in r.message for r in caplog.records)

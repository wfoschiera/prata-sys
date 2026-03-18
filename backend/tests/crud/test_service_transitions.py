"""CRUD-level unit tests for service status transitions.

These tests exercise transition_service_status() directly — no HTTP layer.
This catches logic bugs in the state machine without the overhead of route setup.
"""

import uuid

import pytest
from sqlmodel import Session

from app import crud
from app.models import (
    Service,
    ServiceStatus,
)
from tests.factories import ServiceFactory, ServiceItemFactory

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
    from app.models import DeductionItem

    with pytest.raises(ValueError, match="not a material item"):
        _transition(
            db,
            svc,
            ServiceStatus.completed,
            deduction_items=[DeductionItem(service_item_id=uuid.uuid4(), quantity=1.0)],
            superuser_id=superuser_id,
        )

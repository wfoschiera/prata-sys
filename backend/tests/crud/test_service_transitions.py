"""CRUD-level unit tests for service status transitions.

These tests exercise transition_service_status() directly — no HTTP layer.
This catches logic bugs in the state machine without the overhead of route setup.
"""

import uuid

import pytest
from sqlmodel import Session

from app import crud
from app.models import (
    Client,
    ClientCreate,
    DocumentType,
    ItemType,
    Service,
    ServiceCreate,
    ServiceItem,
    ServiceItemCreate,
    ServiceStatus,
    ServiceType,
)

# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_client(db: Session) -> Client:
    uid_digits = "".join(c for c in uuid.uuid4().hex if c.isdigit())
    cpf = (uid_digits + "00000000000")[:11]
    client_in = ClientCreate(
        name="Test Client",
        document_type=DocumentType.cpf,
        document_number=cpf,
    )
    return crud.create_client(session=db, client_in=client_in)


def _make_service(db: Session) -> Service:
    client = _make_client(db)
    return crud.create_service(
        session=db,
        service_in=ServiceCreate(
            type=ServiceType.perfuracao,
            execution_address="Rua Teste, 100",
            client_id=client.id,
        ),
    )


def _make_material_item(db: Session, service: Service) -> ServiceItem:
    return crud.create_service_item(
        session=db,
        service_id=service.id,
        item_in=ServiceItemCreate(
            item_type=ItemType.material,
            description="Tubo teste",
            quantity=5.0,
            unit_price=10.0,
        ),
    )


def _get_superuser_id(db: Session) -> uuid.UUID:
    """Fetch the seeded superuser's ID to satisfy the changed_by FK."""
    from app.core.config import settings

    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None, "Superuser not found — was init_db run?"
    return user.id


def _transition(
    db: Session,
    service: Service,
    to_status: ServiceStatus,
    *,
    reason: str | None = None,
    deduction_items=None,
) -> tuple[Service, list]:
    return crud.transition_service_status(
        session=db,
        service=service,
        to_status=to_status,
        changed_by_id=_get_superuser_id(db),
        reason=reason,
        deduction_items=deduction_items or [],
    )


# ── Valid transition tests ─────────────────────────────────────────────────────


def test_requested_to_scheduled(db: Session) -> None:
    svc = _make_service(db)
    assert svc.status == ServiceStatus.requested
    updated, warnings = _transition(db, svc, ServiceStatus.scheduled)
    assert updated.status == ServiceStatus.scheduled
    assert warnings == []


def test_scheduled_to_executing(db: Session) -> None:
    svc = _make_service(db)
    _transition(db, svc, ServiceStatus.scheduled)
    db.refresh(svc)
    updated, warnings = _transition(db, svc, ServiceStatus.executing)
    assert updated.status == ServiceStatus.executing


def test_executing_to_completed_with_deduction_items(db: Session) -> None:
    svc = _make_service(db)
    item = _make_material_item(db, svc)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.scheduled)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.executing)
    db.refresh(svc)
    from app.models import DeductionItem

    updated, _ = _transition(
        db,
        svc,
        ServiceStatus.completed,
        deduction_items=[DeductionItem(service_item_id=item.id, quantity=5.0)],
    )
    assert updated.status == ServiceStatus.completed


def test_requested_to_cancelled(db: Session) -> None:
    svc = _make_service(db)
    updated, _ = _transition(
        db, svc, ServiceStatus.cancelled, reason="Cancelado pelo cliente"
    )
    assert updated.status == ServiceStatus.cancelled
    assert updated.cancelled_reason == "Cancelado pelo cliente"


def test_scheduled_to_cancelled(db: Session) -> None:
    svc = _make_service(db)
    _transition(db, svc, ServiceStatus.scheduled)
    db.refresh(svc)
    updated, _ = _transition(db, svc, ServiceStatus.cancelled, reason="Motivo teste")
    assert updated.status == ServiceStatus.cancelled


def test_executing_to_cancelled(db: Session) -> None:
    svc = _make_service(db)
    _transition(db, svc, ServiceStatus.scheduled)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.executing)
    db.refresh(svc)
    updated, _ = _transition(db, svc, ServiceStatus.cancelled, reason="Emergência")
    assert updated.status == ServiceStatus.cancelled


# ── Invalid transition tests ───────────────────────────────────────────────────


def test_invalid_requested_to_executing_raises(db: Session) -> None:
    svc = _make_service(db)
    with pytest.raises(ValueError, match="Cannot transition"):
        _transition(db, svc, ServiceStatus.executing)


def test_invalid_requested_to_completed_raises(db: Session) -> None:
    svc = _make_service(db)
    with pytest.raises(ValueError, match="Cannot transition"):
        _transition(db, svc, ServiceStatus.completed)


def test_invalid_completed_to_anything_raises(db: Session) -> None:
    svc = _make_service(db)
    item = _make_material_item(db, svc)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.scheduled)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.executing)
    db.refresh(svc)
    from app.models import DeductionItem

    _transition(
        db,
        svc,
        ServiceStatus.completed,
        deduction_items=[DeductionItem(service_item_id=item.id, quantity=5.0)],
    )
    db.refresh(svc)
    for bad_status in [
        ServiceStatus.requested,
        ServiceStatus.scheduled,
        ServiceStatus.executing,
        ServiceStatus.cancelled,
    ]:
        with pytest.raises(ValueError, match="Cannot transition"):
            _transition(db, svc, bad_status)


def test_invalid_cancelled_to_anything_raises(db: Session) -> None:
    svc = _make_service(db)
    _transition(db, svc, ServiceStatus.cancelled, reason="Teste")
    db.refresh(svc)
    for bad_status in [
        ServiceStatus.requested,
        ServiceStatus.scheduled,
        ServiceStatus.executing,
        ServiceStatus.completed,
    ]:
        with pytest.raises(ValueError, match="Cannot transition"):
            _transition(db, svc, bad_status)


# ── Status log tests ───────────────────────────────────────────────────────────


def test_transition_creates_status_log(db: Session) -> None:
    svc = _make_service(db)
    _transition(db, svc, ServiceStatus.scheduled)
    logs = crud.get_service_status_logs(session=db, service_id=svc.id)
    assert len(logs) == 1
    assert logs[0].from_status == ServiceStatus.requested
    assert logs[0].to_status == ServiceStatus.scheduled


def test_multiple_transitions_create_ordered_logs(db: Session) -> None:
    svc = _make_service(db)
    _transition(db, svc, ServiceStatus.scheduled)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.executing)
    logs = crud.get_service_status_logs(session=db, service_id=svc.id)
    assert len(logs) == 2
    assert logs[0].from_status == ServiceStatus.requested
    assert logs[1].from_status == ServiceStatus.scheduled


# ── Deduction item validation tests ───────────────────────────────────────────


def test_invalid_deduction_item_id_raises(db: Session) -> None:
    """Completing with a service_item_id not belonging to this service raises ValueError."""
    svc = _make_service(db)
    _make_material_item(db, svc)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.scheduled)
    db.refresh(svc)
    _transition(db, svc, ServiceStatus.executing)
    db.refresh(svc)
    from app.models import DeductionItem

    with pytest.raises(ValueError, match="not a material item"):
        _transition(
            db,
            svc,
            ServiceStatus.completed,
            deduction_items=[DeductionItem(service_item_id=uuid.uuid4(), quantity=1.0)],
        )

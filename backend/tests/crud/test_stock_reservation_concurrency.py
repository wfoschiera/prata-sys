"""Concurrency test for the ``FOR UPDATE`` stock-reservation path.

The default test fixtures use single-connection savepoint isolation, so the
row locking in ``_check_stock_for_service`` (``SELECT ... FOR UPDATE``) is never
exercised under contention. This test proves that two services competing for
the same stock cannot both reserve it.

Because the test must *commit* so two independent connections can see the same
rows, it runs against a dedicated throwaway database (``app_test_concurrency``)
rather than the shared ``app_test``. That keeps its committed data invisible to
the rest of the suite, which asserts a globally clean ``app_test`` (e.g. the
dashboard tests).

The handoff is deterministic: thread A runs the reservation (acquiring the row
locks) and signals *before* committing; thread B only starts once A holds the
locks, so B's ``FOR UPDATE`` query blocks until A commits and then observes the
already-reserved rows.
"""

import threading
import time
import uuid
from collections.abc import Generator
from decimal import Decimal

import pytest
from faker import Faker
from sqlalchemy import Engine
from sqlalchemy.engine import URL
from sqlmodel import Session, SQLModel, create_engine, select, text

from app.core.config import settings
from app.crud import _check_stock_for_service
from app.models import (
    Client,
    DocumentType,
    ItemType,
    Product,
    ProductCategory,
    ProductItem,
    ProductItemStatus,
    ProductType,
    Service,
    ServiceItem,
    ServiceType,
)

fake = Faker("pt_BR")

_CONC_DB = "app_test_concurrency"


def _db_url(database: str) -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        database=database,
    )


@pytest.fixture(scope="module")
def conc_engine() -> Generator[Engine, None, None]:
    """A dedicated, isolated database for the committed concurrency data."""
    server = create_engine(_db_url("postgres"), isolation_level="AUTOCOMMIT")
    with server.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{_CONC_DB}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{_CONC_DB}"'))

    engine = create_engine(_db_url(_CONC_DB))
    SQLModel.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()
        with server.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{_CONC_DB}" WITH (FORCE)'))
        server.dispose()


def _make_service(
    session: Session, client_id: uuid.UUID, product_id: uuid.UUID
) -> uuid.UUID:
    svc = Service(
        type=ServiceType.perfuracao,
        execution_address="x",
        client_id=client_id,
    )
    session.add(svc)
    session.flush()
    session.add(
        ServiceItem(
            service_id=svc.id,
            item_type=ItemType.material,
            description="mat",
            quantity=Decimal("3"),
            unit_price=Decimal("0"),
            product_id=product_id,
        )
    )
    session.flush()
    return svc.id


def test_for_update_prevents_double_reservation(conc_engine: Engine) -> None:
    # ── committed setup (visible across connections in the isolated DB) ──
    with Session(conc_engine) as s:
        pt = ProductType(
            category=ProductCategory.tubos,
            name=f"conc-{uuid.uuid4().hex[:8]}",
            unit_of_measure="un",
        )
        s.add(pt)
        s.flush()
        product = Product(
            product_type_id=pt.id,
            name=f"prod-{uuid.uuid4().hex[:8]}",
            unit_price=Decimal("10"),
        )
        s.add(product)
        s.flush()
        product_id = product.id
        for _ in range(3):
            s.add(
                ProductItem(
                    product_id=product_id,
                    quantity=Decimal("1"),
                    status=ProductItemStatus.em_estoque,
                )
            )
        client = Client(
            name=fake.name(),
            document_type=DocumentType.cpf,
            document_number=fake.cpf().replace(".", "").replace("-", ""),
        )
        s.add(client)
        s.flush()
        svc_a = _make_service(s, client.id, product_id)
        svc_b = _make_service(s, client.id, product_id)
        s.commit()

    a_locked = threading.Event()
    results: dict[str, list] = {}
    errors: dict[str, Exception] = {}

    def worker_a() -> None:
        try:
            with Session(conc_engine) as s:
                svc = s.get(Service, svc_a)
                assert svc is not None
                results["a"] = _check_stock_for_service(s, svc)
                a_locked.set()  # locks held; commit deferred to force contention
                time.sleep(0.5)
                s.commit()
        except Exception as exc:
            errors["a"] = exc
            a_locked.set()

    def worker_b() -> None:
        try:
            a_locked.wait(5)
            with Session(conc_engine) as s:
                svc = s.get(Service, svc_b)
                assert svc is not None
                # This SELECT ... FOR UPDATE blocks until A commits.
                results["b"] = _check_stock_for_service(s, svc)
                s.commit()
        except Exception as exc:
            errors["b"] = exc

    ta = threading.Thread(target=worker_a)
    tb = threading.Thread(target=worker_b)
    ta.start()
    tb.start()
    ta.join(15)
    tb.join(15)

    assert not errors, errors
    # A committed first: it reserved all stock with no shortfall.
    assert results["a"] == []
    # B was blocked until A committed, then found nothing left to reserve.
    assert len(results["b"]) == 1
    assert results["b"][0].shortfall == 3.0

    with Session(conc_engine) as s:
        items = s.exec(
            select(ProductItem).where(ProductItem.product_id == product_id)
        ).all()
        reserved = [i for i in items if i.status == ProductItemStatus.reservado]
        # All three items reserved, every one owned by A — none double-booked.
        assert len(reserved) == 3
        assert {i.service_id for i in reserved} == {svc_a}

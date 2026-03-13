import uuid
from typing import Any

from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Client,
    ClientCreate,
    ClientUpdate,
    Service,
    ServiceCreate,
    ServiceItem,
    ServiceItemCreate,
    ServiceUpdate,
    User,
    UserCreate,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


# ── Client CRUD ───────────────────────────────────────────────────────────────


def get_client(*, session: Session, client_id: uuid.UUID) -> Client | None:
    return session.get(Client, client_id)


def get_clients(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[Client], int]:
    count = session.exec(select(func.count()).select_from(Client)).one()
    clients = session.exec(select(Client).offset(skip).limit(limit)).all()
    return list(clients), count


def get_client_by_document(*, session: Session, document_number: str) -> Client | None:
    return session.exec(
        select(Client).where(Client.document_number == document_number)
    ).first()


def create_client(*, session: Session, client_in: ClientCreate) -> Client:
    db_client = Client.model_validate(client_in)
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return db_client


def update_client(
    *, session: Session, db_client: Client, client_in: ClientUpdate
) -> Client:
    from datetime import datetime, timezone

    client_data = client_in.model_dump(exclude_unset=True)
    db_client.sqlmodel_update(client_data)
    db_client.updated_at = datetime.now(timezone.utc)
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return db_client


def delete_client(*, session: Session, db_client: Client) -> None:
    session.delete(db_client)
    session.commit()


# ── Service CRUD ──────────────────────────────────────────────────────────────


def get_service(*, session: Session, service_id: uuid.UUID) -> Service | None:
    statement = (
        select(Service)
        .where(Service.id == service_id)
        .options(selectinload(Service.client), selectinload(Service.items))  # type: ignore[arg-type]
    )
    return session.exec(statement).first()


def get_services(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[Service], int]:
    count = session.exec(select(func.count()).select_from(Service)).one()
    statement = (
        select(Service)
        .options(selectinload(Service.client), selectinload(Service.items))  # type: ignore[arg-type]
        .offset(skip)
        .limit(limit)
    )
    services = session.exec(statement).all()
    return list(services), count


def create_service(*, session: Session, service_in: ServiceCreate) -> Service:
    db_service = Service.model_validate(service_in)
    session.add(db_service)
    session.commit()
    session.refresh(db_service)
    result = get_service(session=session, service_id=db_service.id)
    assert result is not None
    return result


def update_service(
    *, session: Session, db_service: Service, service_in: ServiceUpdate
) -> Service:
    from datetime import datetime, timezone

    from app.models import VALID_STATUS_TRANSITIONS

    service_data = service_in.model_dump(exclude_unset=True)
    if "status" in service_data:
        new_status = service_data["status"]
        allowed = VALID_STATUS_TRANSITIONS.get(db_service.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid status transition from '{db_service.status}' to '{new_status}'"
            )
    db_service.sqlmodel_update(service_data)
    db_service.updated_at = datetime.now(timezone.utc)
    session.add(db_service)
    session.commit()
    result = get_service(session=session, service_id=db_service.id)
    assert result is not None
    return result


def delete_service(*, session: Session, db_service: Service) -> None:
    session.delete(db_service)
    session.commit()


def create_service_item(
    *, session: Session, service_id: uuid.UUID, item_in: ServiceItemCreate
) -> ServiceItem:
    db_item = ServiceItem.model_validate(item_in, update={"service_id": service_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def get_service_item(*, session: Session, item_id: uuid.UUID) -> ServiceItem | None:
    return session.get(ServiceItem, item_id)


def delete_service_item(*, session: Session, db_item: ServiceItem) -> None:
    session.delete(db_item)
    session.commit()

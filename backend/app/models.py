import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import EmailStr, field_validator
from sqlalchemy import DateTime, Text
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    admin = "admin"
    finance = "finance"
    client = "client"


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = UserRole.admin


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ── Client ────────────────────────────────────────────────────────────────────


class DocumentType(str, enum.Enum):
    cpf = "cpf"
    cnpj = "cnpj"


def _validate_document_number(document_type: str, document_number: str) -> str:
    digits = document_number.strip()
    if not digits.isdigit():
        raise ValueError("document_number must contain only digits")
    expected = 11 if document_type == DocumentType.cpf else 14
    if len(digits) != expected:
        raise ValueError(
            f"document_number must have {expected} digits for {document_type.upper()}"
        )
    return digits


class ClientBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    document_type: DocumentType
    document_number: str = Field(max_length=14)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)

    @field_validator("document_number", mode="before")
    @classmethod
    def validate_document_number(cls, v: str, info: Any) -> str:
        doc_type = (info.data or {}).get("document_type")
        if doc_type is not None:
            return _validate_document_number(doc_type, v)
        return v


class ClientCreate(ClientBase):
    pass


class ClientUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    document_type: DocumentType | None = None
    document_number: str | None = Field(default=None, max_length=14)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)

    @field_validator("document_number", mode="before")
    @classmethod
    def validate_document_number(cls, v: str | None, info: Any) -> str | None:
        if v is None:
            return v
        doc_type = (info.data or {}).get("document_type")
        if doc_type is not None:
            return _validate_document_number(doc_type, v)
        return v


class Client(ClientBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_number: str = Field(max_length=14, unique=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class ClientPublic(ClientBase):
    id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ClientsPublic(SQLModel):
    data: list[ClientPublic]
    count: int


# ── Service ───────────────────────────────────────────────────────────────────


class ServiceType(str, enum.Enum):
    perfuracao = "perfuração"
    reparo = "reparo"


class ServiceStatus(str, enum.Enum):
    requested = "requested"
    scheduled = "scheduled"
    executing = "executing"
    completed = "completed"


class ItemType(str, enum.Enum):
    material = "material"
    servico = "serviço"


# Valid status transitions
VALID_STATUS_TRANSITIONS: dict[ServiceStatus, list[ServiceStatus]] = {
    ServiceStatus.requested: [ServiceStatus.scheduled],
    ServiceStatus.scheduled: [ServiceStatus.executing],
    ServiceStatus.executing: [ServiceStatus.completed],
    ServiceStatus.completed: [],
}


class ServiceItemBase(SQLModel):
    item_type: ItemType
    description: str = Field(min_length=1, max_length=500)
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)


class ServiceItemCreate(ServiceItemBase):
    pass


class ServiceItemRead(ServiceItemBase):
    id: uuid.UUID
    service_id: uuid.UUID


class ServiceItem(ServiceItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    service_id: uuid.UUID = Field(foreign_key="service.id", nullable=False)
    service: "Service" = Relationship(back_populates="items")


class ClientRef(SQLModel):
    id: uuid.UUID
    name: str


class ServiceBase(SQLModel):
    type: ServiceType
    execution_address: str = Field(min_length=1, max_length=500)
    notes: str | None = Field(default=None, sa_type=Text)


class ServiceCreate(ServiceBase):
    client_id: uuid.UUID


class ServiceUpdate(SQLModel):
    type: ServiceType | None = None
    status: ServiceStatus | None = None
    execution_address: str | None = Field(default=None, min_length=1, max_length=500)
    notes: str | None = None


class ServiceRead(ServiceBase):
    id: uuid.UUID
    client_id: uuid.UUID
    status: ServiceStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None
    client: ClientRef | None = None
    items: list[ServiceItemRead] = []


class ServicesPublic(SQLModel):
    data: list[ServiceRead]
    count: int


class Service(ServiceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="client.id", nullable=False)
    status: ServiceStatus = Field(default=ServiceStatus.requested)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    client: Client | None = Relationship()
    items: list[ServiceItem] = Relationship(
        back_populates="service",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

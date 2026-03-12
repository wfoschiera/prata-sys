import enum
import uuid
from datetime import datetime, timezone

from typing import Any

from pydantic import EmailStr, field_validator
from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


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

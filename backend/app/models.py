import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from pydantic import EmailStr, field_validator, model_validator
from sqlalchemy import DateTime, Numeric, Text, UniqueConstraint
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
    user_permissions: list["UserPermission"] = Relationship(
        back_populates="user",
        cascade_delete=True,
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None
    permissions: list[str] = []


class UserPermission(SQLModel, table=True):
    __tablename__ = "user_permission"
    __table_args__ = (UniqueConstraint("user_id", "permission"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    permission: str = Field(max_length=100)

    user: User = Relationship(back_populates="user_permissions")


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
        msg = "document_number must contain only digits"
        raise ValueError(msg)
    expected = 11 if document_type == DocumentType.cpf else 14
    if len(digits) != expected:
        msg = f"document_number must have {expected} digits for {document_type.upper()}"
        raise ValueError(msg)
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
    cancelled = "cancelled"


class ItemType(str, enum.Enum):
    material = "material"
    servico = "serviço"


# Valid status transitions
VALID_STATUS_TRANSITIONS: dict[ServiceStatus, list[ServiceStatus]] = {
    ServiceStatus.requested: [ServiceStatus.scheduled, ServiceStatus.cancelled],
    ServiceStatus.scheduled: [ServiceStatus.executing, ServiceStatus.cancelled],
    ServiceStatus.executing: [ServiceStatus.completed, ServiceStatus.cancelled],
    ServiceStatus.completed: [],
    ServiceStatus.cancelled: [],
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
    execution_address: str | None = Field(default=None, min_length=1, max_length=500)
    notes: str | None = None
    description: str | None = None


class ServiceStatusLogRead(SQLModel):
    id: uuid.UUID
    from_status: ServiceStatus
    to_status: ServiceStatus
    changed_by: uuid.UUID
    changed_at: datetime
    notes: str | None = None
    changed_by_name: str | None = None


class ServiceRead(ServiceBase):
    id: uuid.UUID
    client_id: uuid.UUID
    status: ServiceStatus
    description: str | None = None
    cancelled_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    client: ClientRef | None = None
    items: list[ServiceItemRead] = []
    status_logs: list[ServiceStatusLogRead] = []
    has_stock_warning: bool = False


class ServicesPublic(SQLModel):
    data: list[ServiceRead]
    count: int


class Service(ServiceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="client.id", nullable=False)
    status: ServiceStatus = Field(default=ServiceStatus.requested)
    description: str | None = Field(default=None, sa_type=Text)
    cancelled_reason: str | None = Field(default=None, max_length=500)
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
    status_logs: list["ServiceStatusLog"] = Relationship(
        back_populates="service",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "ServiceStatusLog.changed_at",
        },
    )


class ServiceStatusLog(SQLModel, table=True):
    __tablename__ = "service_status_log"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    service_id: uuid.UUID = Field(
        foreign_key="service.id", nullable=False, ondelete="CASCADE", index=True
    )
    from_status: ServiceStatus
    to_status: ServiceStatus
    changed_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    changed_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    notes: str | None = Field(default=None, max_length=500)
    changed_by_user: User | None = Relationship()
    service: "Service" = Relationship(back_populates="status_logs")


class DeductionItem(SQLModel):
    service_item_id: uuid.UUID
    quantity: float = Field(gt=0)


class ServiceTransitionRequest(SQLModel):
    to_status: ServiceStatus
    reason: str | None = None
    deduction_items: list[DeductionItem] | None = None

    @model_validator(mode="after")
    def validate_transition_fields(self) -> "ServiceTransitionRequest":
        if self.to_status == ServiceStatus.cancelled and not self.reason:
            msg = "reason is required when transitioning to cancelled"
            raise ValueError(msg)
        if self.to_status == ServiceStatus.completed and not self.deduction_items:
            msg = "deduction_items is required when transitioning to completed"
            raise ValueError(msg)
        return self


class StockWarning(SQLModel):
    service_item_id: uuid.UUID
    description: str
    required_quantity: float
    available_quantity: float
    shortfall: float


class ServiceTransitionResponse(SQLModel):
    service: "ServiceRead"
    stock_warnings: list[StockWarning] = []


ServiceTransitionResponse.model_rebuild()


# ── Financeiro ────────────────────────────────────────────────────────────────


class TipoTransacao(str, enum.Enum):
    receita = "receita"
    despesa = "despesa"


class CategoriaTransacao(str, enum.Enum):
    # Income categories (valid only when tipo=receita)
    SERVICO = "SERVICO"
    VENDA_EQUIPAMENTO = "VENDA_EQUIPAMENTO"
    RENDIMENTO = "RENDIMENTO"
    CAPITAL_FIXO = "CAPITAL_FIXO"
    # Expense categories (valid only when tipo=despesa)
    COMBUSTIVEL = "COMBUSTIVEL"
    MANUTENCAO_EQUIPAMENTO = "MANUTENCAO_EQUIPAMENTO"
    MANUTENCAO_VEICULO = "MANUTENCAO_VEICULO"
    MANUTENCAO_ESCRITORIO = "MANUTENCAO_ESCRITORIO"
    COMPRA_MATERIAL = "COMPRA_MATERIAL"
    MO_CLT = "MO_CLT"
    MO_DIARISTA = "MO_DIARISTA"
    ADMIN = "ADMIN"


INCOME_CATEGORIES: frozenset[CategoriaTransacao] = frozenset(
    {
        CategoriaTransacao.SERVICO,
        CategoriaTransacao.VENDA_EQUIPAMENTO,
        CategoriaTransacao.RENDIMENTO,
        CategoriaTransacao.CAPITAL_FIXO,
    }
)

EXPENSE_CATEGORIES: frozenset[CategoriaTransacao] = frozenset(
    {
        CategoriaTransacao.COMBUSTIVEL,
        CategoriaTransacao.MANUTENCAO_EQUIPAMENTO,
        CategoriaTransacao.MANUTENCAO_VEICULO,
        CategoriaTransacao.MANUTENCAO_ESCRITORIO,
        CategoriaTransacao.COMPRA_MATERIAL,
        CategoriaTransacao.MO_CLT,
        CategoriaTransacao.MO_DIARISTA,
        CategoriaTransacao.ADMIN,
    }
)

# PT-BR labels for frontend display
CATEGORIA_LABELS: dict[CategoriaTransacao, str] = {
    CategoriaTransacao.SERVICO: "Serviço",
    CategoriaTransacao.VENDA_EQUIPAMENTO: "Venda de Equipamento",
    CategoriaTransacao.RENDIMENTO: "Rendimento",
    CategoriaTransacao.CAPITAL_FIXO: "Capital Fixo",
    CategoriaTransacao.COMBUSTIVEL: "Combustível",
    CategoriaTransacao.MANUTENCAO_EQUIPAMENTO: "Manutenção de Equipamento",
    CategoriaTransacao.MANUTENCAO_VEICULO: "Manutenção de Veículo",
    CategoriaTransacao.MANUTENCAO_ESCRITORIO: "Manutenção de Escritório",
    CategoriaTransacao.COMPRA_MATERIAL: "Compra de Material",
    CategoriaTransacao.MO_CLT: "Mão de Obra CLT",
    CategoriaTransacao.MO_DIARISTA: "Mão de Obra Diarista",
    CategoriaTransacao.ADMIN: "Administrativo",
}


class ServiceSummary(SQLModel):
    id: uuid.UUID
    type: ServiceType
    status: ServiceStatus


class TransacaoBase(SQLModel):
    tipo: TipoTransacao
    categoria: CategoriaTransacao
    valor: Decimal = Field(sa_type=Numeric(12, 2))  # type: ignore
    data_competencia: date
    descricao: str | None = Field(default=None, sa_type=Text)
    nome_contraparte: str | None = Field(default=None, max_length=200)


class TransacaoCreate(TransacaoBase):
    service_id: uuid.UUID | None = None
    client_id: uuid.UUID | None = None
    # fornecedor_id will be added in Phase 6 (FK constraint added then)
    fornecedor_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def validate_tipo_categoria_and_client(self) -> "TransacaoCreate":
        if self.valor <= 0:
            msg = "valor must be greater than zero"
            raise ValueError(msg)
        if (
            self.tipo == TipoTransacao.receita
            and self.categoria not in INCOME_CATEGORIES
        ):
            msg = (
                f"categoria '{self.categoria}' is not valid for tipo='receita'. "
                f"Valid categories: {[c.value for c in INCOME_CATEGORIES]}"
            )
            raise ValueError(msg)
        if (
            self.tipo == TipoTransacao.despesa
            and self.categoria not in EXPENSE_CATEGORIES
        ):
            msg = (
                f"categoria '{self.categoria}' is not valid for tipo='despesa'. "
                f"Valid categories: {[c.value for c in EXPENSE_CATEGORIES]}"
            )
            raise ValueError(msg)
        if self.tipo == TipoTransacao.despesa and self.client_id is not None:
            msg = "client_id may only be set when tipo='receita'"
            raise ValueError(msg)
        return self


class TransacaoUpdate(SQLModel):
    # tipo is intentionally omitted — immutable after creation
    categoria: CategoriaTransacao | None = None
    valor: Decimal | None = None
    data_competencia: date | None = None
    descricao: str | None = None
    nome_contraparte: str | None = None
    service_id: uuid.UUID | None = None
    fornecedor_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def validate_valor(self) -> "TransacaoUpdate":
        if self.valor is not None and self.valor <= 0:
            msg = "valor must be greater than zero"
            raise ValueError(msg)
        return self


class TransacaoPublic(TransacaoBase):
    id: uuid.UUID
    service_id: uuid.UUID | None = None
    client_id: uuid.UUID | None = None
    fornecedor_id: uuid.UUID | None = None
    service: ServiceSummary | None = None
    client: ClientRef | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TransacoesPublic(SQLModel):
    data: list[TransacaoPublic]
    count: int


class ResumoMensal(SQLModel):
    ano: int
    mes: int
    total_receitas: Decimal
    total_despesas: Decimal
    resultado_liquido: Decimal


class Transacao(TransacaoBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    service_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="service.id",
        ondelete="SET NULL",
        index=True,
    )
    client_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="client.id",
        ondelete="SET NULL",
        index=True,
    )
    # fornecedor_id stored without FK constraint until Phase 6 adds the fornecedor table
    fornecedor_id: uuid.UUID | None = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    service: Service | None = Relationship()
    client: Client | None = Relationship()

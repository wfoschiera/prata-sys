import enum
import re
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

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


class UsedPasswordResetToken(SQLModel, table=True):
    """Tracks consumed password reset tokens to prevent reuse within expiry window."""

    __tablename__ = "used_password_reset_token"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    token_hash: str = Field(unique=True, index=True, max_length=64)
    used_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),  # type: ignore
    )


# ── Client ────────────────────────────────────────────────────────────────────


class DocumentType(str, enum.Enum):
    cpf = "cpf"
    cnpj = "cnpj"


def _cnpj_char_value(c: str) -> int:
    """Return the numeric value of a CNPJ character using the ASCII-48 rule.

    Digits '0'-'9' → 0-9 (unchanged).
    Letters 'A'-'Z' → 17-42  (ord('A')=65, 65-48=17; ...; ord('Z')=90, 90-48=42).
    This rule is defined by Receita Federal for the alphanumeric CNPJ format
    effective from July 2026 (and is backwards-compatible with the old numeric format).
    """
    return ord(c) - 48


def _validate_cnpj(value: str) -> str:
    """Validate a CNPJ in either the current numeric format or the new
    alphanumeric format introduced in July 2026.

    Accepted input:
      - Numeric:       14 digits, e.g. "11222333000181"
      - Alphanumeric:  12 uppercase alphanumeric chars + 2 numeric check digits,
                       e.g. "1A2B3C4D0001AB" (letters A-Z and digits 0-9 in
                       positions 0-11; positions 12-13 are always digits).

    Formatting characters (`.`, `/`, `-`) are stripped before validation.
    Raises ValueError for wrong length, invalid characters, or bad check digits.
    """
    cnpj = value.strip().upper()
    # Strip common formatting
    cnpj = cnpj.replace(".", "").replace("/", "").replace("-", "")

    if len(cnpj) != 14:
        msg = "CNPJ must have 14 characters"
        raise ValueError(msg)

    # First 12 positions: alphanumeric (A-Z, 0-9); last 2: numeric check digits
    if not re.match(r"^[A-Z0-9]{12}\d{2}$", cnpj):
        msg = (
            "CNPJ must contain only uppercase letters and digits in the first 12 "
            "positions and digits in the last 2 positions"
        )
        raise ValueError(msg)

    # Reject all-same-character sequences (e.g. "00000000000000")
    if len(set(cnpj)) == 1:
        msg = "CNPJ is invalid (all characters are the same)"
        raise ValueError(msg)

    # --- Check digit validation (Modulo 11, ASCII-48 values) ---
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    def _calc_dv(chars: str, weights: list[int]) -> int:
        total = sum(
            _cnpj_char_value(c) * w for c, w in zip(chars, weights, strict=False)
        )
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    if _calc_dv(cnpj[:12], weights1) != int(cnpj[12]):
        msg = "CNPJ has invalid check digits"
        raise ValueError(msg)
    if _calc_dv(cnpj[:13], weights2) != int(cnpj[13]):
        msg = "CNPJ has invalid check digits"
        raise ValueError(msg)

    return cnpj


def _validate_document_number(document_type: str, document_number: str) -> str:
    value = document_number.strip()
    if document_type == DocumentType.cnpj:
        return _validate_cnpj(value)
    # CPF: digits only, 11 characters
    if not value.isdigit():
        msg = "document_number must contain only digits"
        raise ValueError(msg)
    if len(value) != 11:
        msg = "document_number must have 11 digits for CPF"
        raise ValueError(msg)
    return value


class ClientBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    document_type: DocumentType
    document_number: str = Field(max_length=14)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    bairro: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=2)
    cep: str | None = Field(default=None, max_length=9)

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
    bairro: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=2)
    cep: str | None = Field(default=None, max_length=9)

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
    # Optional link to a catalog Product — enables product-scoped stock reservation.
    # When set, _check_stock_for_service() will reserve ProductItems for this product.
    product_id: uuid.UUID | None = Field(default=None)


class ServiceItemCreate(ServiceItemBase):
    pass


class ServiceItemRead(ServiceItemBase):
    id: uuid.UUID
    service_id: uuid.UUID


class ServiceItem(ServiceItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    service_id: uuid.UUID = Field(foreign_key="service.id", nullable=False)
    product_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="product.id",
        nullable=True,
        ondelete="SET NULL",
    )
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
    changed_by: uuid.UUID | None
    changed_at: datetime
    notes: str | None = None
    changed_by_name: str | None = None


class ServiceRead(ServiceBase):
    """Full service detail — includes status_logs. Used by GET /services/{id}."""

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


class ServiceListRead(ServiceBase):
    """Lightweight service summary for list responses — omits status_logs."""

    id: uuid.UUID
    client_id: uuid.UUID
    status: ServiceStatus
    description: str | None = None
    cancelled_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    client: ClientRef | None = None
    items: list[ServiceItemRead] = []
    has_stock_warning: bool = False


class ServicesPublic(SQLModel):
    data: list[ServiceListRead]
    count: int


class Service(ServiceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="client.id", nullable=False, index=True)
    status: ServiceStatus = Field(default=ServiceStatus.requested, index=True)
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
    product_items: list["ProductItem"] = Relationship(back_populates="service")


class ServiceStatusLog(SQLModel, table=True):
    __tablename__ = "service_status_log"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    service_id: uuid.UUID = Field(
        foreign_key="service.id", nullable=False, ondelete="CASCADE", index=True
    )
    from_status: ServiceStatus
    to_status: ServiceStatus
    changed_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", nullable=True, ondelete="SET NULL"
    )
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


class DeductionSummary(SQLModel):
    product_item_id: uuid.UUID
    quantity: float


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
    fornecedor_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="fornecedor.id",
        ondelete="SET NULL",
        index=True,
    )
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


# ── Fornecedor ─────────────────────────────────────────────────────────────────


class FornecedorCategoryEnum(str, enum.Enum):
    tubos = "tubos"
    conexoes = "conexoes"
    bombas = "bombas"
    cabos = "cabos"
    outros = "outros"


class FornecedorBase(SQLModel):
    company_name: str = Field(min_length=1, max_length=255)
    cnpj: str | None = Field(default=None, max_length=14)
    address: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, sa_type=Text)

    @field_validator("cnpj", mode="before")
    @classmethod
    def validate_cnpj_field(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        return _validate_cnpj(v)


class FornecedorCreate(FornecedorBase):
    categories: list[FornecedorCategoryEnum] = []


class FornecedorUpdate(SQLModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    cnpj: str | None = Field(default=None, max_length=14)
    address: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    categories: list[FornecedorCategoryEnum] | None = None

    @field_validator("cnpj", mode="before")
    @classmethod
    def validate_cnpj_field(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        return _validate_cnpj(v)


class FornecedorContatoBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    telefone: str = Field(min_length=1, max_length=20)
    whatsapp: str | None = Field(default=None, max_length=20)
    description: str = Field(min_length=1, max_length=100)


class FornecedorContatoCreate(FornecedorContatoBase):
    pass


class FornecedorContatoUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    telefone: str | None = Field(default=None, min_length=1, max_length=20)
    whatsapp: str | None = Field(default=None, max_length=20)
    description: str | None = Field(default=None, min_length=1, max_length=100)


class FornecedorContatoPublic(FornecedorContatoBase):
    id: uuid.UUID
    fornecedor_id: uuid.UUID


class FornecedorPublic(FornecedorBase):
    id: uuid.UUID
    categories: list[FornecedorCategoryEnum]
    contatos: list[FornecedorContatoPublic]


# ── Fornecedor DB tables ───────────────────────────────────────────────────────


class Fornecedor(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    company_name: str = Field(min_length=1, max_length=255, index=True)
    cnpj: str | None = Field(default=None, max_length=14)
    address: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, sa_type=Text)

    contatos: list["FornecedorContato"] = Relationship(
        back_populates="fornecedor",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    categorias: list["FornecedorCategoria"] = Relationship(
        back_populates="fornecedor",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    transacoes: list["Transacao"] = Relationship()


class FornecedorContato(SQLModel, table=True):
    __tablename__ = "fornecedor_contato"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    fornecedor_id: uuid.UUID = Field(
        foreign_key="fornecedor.id", ondelete="CASCADE", index=True
    )
    name: str = Field(min_length=1, max_length=255)
    telefone: str = Field(min_length=1, max_length=20)
    whatsapp: str | None = Field(default=None, max_length=20)
    description: str = Field(min_length=1, max_length=100)

    fornecedor: Fornecedor = Relationship(back_populates="contatos")


class FornecedorCategoria(SQLModel, table=True):
    __tablename__ = "fornecedor_categoria"
    __table_args__ = (UniqueConstraint("fornecedor_id", "category"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    fornecedor_id: uuid.UUID = Field(
        foreign_key="fornecedor.id", ondelete="CASCADE", index=True
    )
    category: str = Field(max_length=20)

    fornecedor: Fornecedor = Relationship(back_populates="categorias")


# ── Estoque (Inventory) ────────────────────────────────────────────────────────


class ProductCategory(str, enum.Enum):
    tubos = "tubos"
    conexoes = "conexoes"
    bombas = "bombas"
    cabos = "cabos"
    outros = "outros"


class ProductItemStatus(str, enum.Enum):
    em_estoque = "em_estoque"
    reservado = "reservado"
    utilizado = "utilizado"


class ProductType(SQLModel, table=True):
    __tablename__ = "producttype"
    __table_args__ = (UniqueConstraint("category", "name"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    category: ProductCategory = Field(nullable=False)
    name: str = Field(max_length=255, nullable=False)
    unit_of_measure: str = Field(max_length=50, nullable=False)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    products: list["Product"] = Relationship(back_populates="product_type")


class Product(SQLModel, table=True):
    __tablename__ = "product"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    product_type_id: uuid.UUID = Field(
        foreign_key="producttype.id", nullable=False, ondelete="RESTRICT"
    )
    name: str = Field(max_length=255, nullable=False)
    fornecedor_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="fornecedor.id",
        nullable=True,
        ondelete="SET NULL",
    )
    unit_price: Decimal = Field(sa_type=Numeric(10, 2), nullable=False)  # type: ignore
    description: str | None = Field(default=None, sa_type=Text)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    product_type: ProductType = Relationship(back_populates="products")
    fornecedor: Fornecedor | None = Relationship()
    items: list["ProductItem"] = Relationship(back_populates="product")


class ProductItem(SQLModel, table=True):
    __tablename__ = "productitem"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    product_id: uuid.UUID = Field(
        foreign_key="product.id", nullable=False, ondelete="CASCADE"
    )
    quantity: Decimal = Field(sa_type=Numeric(12, 4), nullable=False)  # type: ignore
    status: ProductItemStatus = Field(
        default=ProductItemStatus.em_estoque, nullable=False, index=True
    )
    service_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="service.id",
        nullable=True,
        ondelete="SET NULL",
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    product: Product = Relationship(back_populates="items")
    service: Optional["Service"] = Relationship(back_populates="product_items")


# ── Estoque Pydantic Schemas ───────────────────────────────────────────────────


class ProductTypeCreate(SQLModel):
    category: ProductCategory
    name: str = Field(min_length=1, max_length=255)
    unit_of_measure: str = Field(min_length=1, max_length=50)


class ProductTypeRead(SQLModel):
    id: uuid.UUID
    category: ProductCategory
    name: str
    unit_of_measure: str
    created_at: datetime | None = None


class ProductTypeUpdate(SQLModel):
    category: ProductCategory | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    unit_of_measure: str | None = Field(default=None, min_length=1, max_length=50)


class FornecedorRef(SQLModel):
    id: uuid.UUID
    company_name: str


class ProductCreate(SQLModel):
    product_type_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    fornecedor_id: uuid.UUID | None = None
    unit_price: Decimal
    description: str | None = None

    @field_validator("unit_price", mode="before")
    @classmethod
    def validate_unit_price(cls, v: Any) -> Decimal:
        d = Decimal(str(v))
        if d < 0:
            msg = "unit_price must be >= 0"
            raise ValueError(msg)
        return d


class ProductRead(SQLModel):
    id: uuid.UUID
    product_type_id: uuid.UUID
    product_type: ProductTypeRead
    name: str
    fornecedor_id: uuid.UUID | None = None
    fornecedor: FornecedorRef | None = None
    unit_price: Decimal
    description: str | None = None
    created_at: datetime | None = None


class ProductUpdate(SQLModel):
    product_type_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    fornecedor_id: uuid.UUID | None = None
    unit_price: Decimal | None = None
    description: str | None = None

    @field_validator("unit_price", mode="before")
    @classmethod
    def validate_unit_price(cls, v: Any) -> Decimal | None:
        if v is None:
            return None
        d = Decimal(str(v))
        if d < 0:
            msg = "unit_price must be >= 0"
            raise ValueError(msg)
        return d


class ProductItemCreate(SQLModel):
    product_id: uuid.UUID
    quantity: Decimal

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, v: Any) -> Decimal:
        d = Decimal(str(v))
        if d <= 0:
            msg = "quantity must be > 0"
            raise ValueError(msg)
        return d


class ProductItemRead(SQLModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    status: ProductItemStatus
    service_id: uuid.UUID | None = None
    created_at: datetime | None = None


class StockPredictionRead(SQLModel):
    product_id: uuid.UUID
    days_to_stockout: int | None = None
    level: str  # "green" | "yellow" | "red"
    em_estoque_qty: Decimal
    reservado_qty: Decimal
    avg_daily_consumption: Decimal | None = None


class CategoryDashboardItem(SQLModel):
    category: ProductCategory
    em_estoque_total: Decimal
    reservado_total: Decimal
    utilizado_total: Decimal


class InventoryStockWarning(SQLModel):
    product_id: uuid.UUID
    product_name: str
    required_qty: Decimal
    available_qty: Decimal
    shortfall_qty: Decimal


class BaixarEstoqueResponse(SQLModel):
    service_id: uuid.UUID
    items_updated: int


# ── Orçamento ──────────────────────────────────────────────────────────────────


class OrcamentoStatus(str, enum.Enum):
    rascunho = "rascunho"
    em_analise = "em_analise"
    aprovado = "aprovado"
    cancelado = "cancelado"


VALID_ORCAMENTO_TRANSITIONS: dict[OrcamentoStatus, list[OrcamentoStatus]] = {
    OrcamentoStatus.rascunho: [OrcamentoStatus.em_analise, OrcamentoStatus.cancelado],
    OrcamentoStatus.em_analise: [
        OrcamentoStatus.rascunho,
        OrcamentoStatus.aprovado,
        OrcamentoStatus.cancelado,
    ],
    OrcamentoStatus.aprovado: [OrcamentoStatus.em_analise, OrcamentoStatus.cancelado],
    OrcamentoStatus.cancelado: [],
}


class OrcamentoItemBase(SQLModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(sa_type=Numeric(12, 4), gt=0)  # type: ignore
    unit_price: Decimal = Field(sa_type=Numeric(10, 2), ge=0)  # type: ignore
    show_unit_price: bool = Field(default=True)


class OrcamentoItemCreate(OrcamentoItemBase):
    product_id: uuid.UUID


class OrcamentoItemUpdate(SQLModel):
    description: str | None = Field(default=None, min_length=1, max_length=500)
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    show_unit_price: bool | None = None


class OrcamentoItemRead(OrcamentoItemBase):
    id: uuid.UUID
    orcamento_id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime | None = None


class OrcamentoItem(OrcamentoItemBase, table=True):
    __tablename__ = "orcamento_item"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    orcamento_id: uuid.UUID = Field(
        foreign_key="orcamento.id", nullable=False, ondelete="CASCADE", index=True
    )
    product_id: uuid.UUID = Field(
        foreign_key="product.id", nullable=False, ondelete="RESTRICT"
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    orcamento: "Orcamento" = Relationship(back_populates="items")
    product: "Product" = Relationship()


class OrcamentoBase(SQLModel):
    service_type: ServiceType
    execution_address: str = Field(min_length=1, max_length=500)
    city: str | None = Field(default=None, max_length=100)
    cep: str | None = Field(default=None, max_length=9)
    description: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, sa_type=Text)
    forma_pagamento: str | None = Field(default=None, max_length=500)
    vendedor: str | None = Field(default=None, max_length=255)


class OrcamentoCreate(OrcamentoBase):
    client_id: uuid.UUID
    validade_proposta: date | None = None


class OrcamentoUpdate(SQLModel):
    service_type: ServiceType | None = None
    execution_address: str | None = Field(default=None, min_length=1, max_length=500)
    city: str | None = Field(default=None, max_length=100)
    cep: str | None = Field(default=None, max_length=9)
    description: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    forma_pagamento: str | None = Field(default=None, max_length=500)
    validade_proposta: date | None = None
    vendedor: str | None = Field(default=None, max_length=255)


class OrcamentoStatusLogRead(SQLModel):
    id: uuid.UUID
    from_status: OrcamentoStatus
    to_status: OrcamentoStatus
    changed_by: uuid.UUID | None = None
    changed_at: datetime | None = None
    notes: str | None = None


class OrcamentoRead(OrcamentoBase):
    """Full orçamento detail — includes items and status_logs."""

    id: uuid.UUID
    ref_code: str
    client_id: uuid.UUID
    status: OrcamentoStatus
    validade_proposta: date | None = None
    service_id: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    client: ClientRef | None = None
    items: list[OrcamentoItemRead] = []
    status_logs: list[OrcamentoStatusLogRead] = []


class OrcamentoListRead(OrcamentoBase):
    """Lightweight orçamento for list responses — no items or logs."""

    id: uuid.UUID
    ref_code: str
    client_id: uuid.UUID
    status: OrcamentoStatus
    validade_proposta: date | None = None
    service_id: uuid.UUID | None = None
    created_at: datetime | None = None
    client: ClientRef | None = None


class OrcamentosPublic(SQLModel):
    data: list[OrcamentoListRead]
    count: int


class OrcamentoTransitionRequest(SQLModel):
    to_status: OrcamentoStatus
    reason: str | None = None


class OrcamentoTransitionResponse(SQLModel):
    orcamento: OrcamentoRead


class Orcamento(OrcamentoBase, table=True):
    __tablename__ = "orcamento"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ref_code: str = Field(max_length=6, unique=True, index=True)
    client_id: uuid.UUID = Field(foreign_key="client.id", nullable=False, index=True)
    status: OrcamentoStatus = Field(default=OrcamentoStatus.rascunho, index=True)
    validade_proposta: date | None = Field(default=None)
    service_id: uuid.UUID | None = Field(
        default=None, foreign_key="service.id", nullable=True, ondelete="SET NULL"
    )
    created_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", nullable=True, ondelete="SET NULL"
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    client: Client | None = Relationship()
    items: list[OrcamentoItem] = Relationship(
        back_populates="orcamento",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    status_logs: list["OrcamentoStatusLog"] = Relationship(
        back_populates="orcamento",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "OrcamentoStatusLog.changed_at",
        },
    )
    created_by_user: User | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Orcamento.created_by]"}
    )
    service: Optional["Service"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Orcamento.service_id]"}
    )


class OrcamentoStatusLog(SQLModel, table=True):
    __tablename__ = "orcamento_status_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    orcamento_id: uuid.UUID = Field(
        foreign_key="orcamento.id", nullable=False, ondelete="CASCADE", index=True
    )
    from_status: OrcamentoStatus = Field(nullable=False)
    to_status: OrcamentoStatus = Field(nullable=False)
    changed_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", nullable=True, ondelete="SET NULL"
    )
    changed_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    notes: str | None = Field(default=None, max_length=500)

    orcamento: Orcamento = Relationship(back_populates="status_logs")
    changed_by_user: User | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[OrcamentoStatusLog.changed_by]"}
    )

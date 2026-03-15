import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import extract
from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    VALID_ORCAMENTO_TRANSITIONS,
    VALID_STATUS_TRANSITIONS,
    BaixarEstoqueResponse,
    CategoriaTransacao,
    CategoryDashboardItem,
    Client,
    ClientCreate,
    ClientRef,
    ClientUpdate,
    DeductionItem,
    DeductionSummary,
    Fornecedor,
    FornecedorCategoria,
    FornecedorCategoryEnum,
    FornecedorContato,
    FornecedorContatoCreate,
    FornecedorContatoUpdate,
    FornecedorCreate,
    FornecedorUpdate,
    InventoryStockWarning,
    ItemType,
    Orcamento,
    OrcamentoCreate,
    OrcamentoItem,
    OrcamentoItemCreate,
    OrcamentoItemUpdate,
    OrcamentoStatus,
    OrcamentoStatusLog,
    OrcamentoUpdate,
    Product,
    ProductCategory,
    ProductCreate,
    ProductItem,
    ProductItemCreate,
    ProductItemStatus,
    ProductType,
    ProductTypeCreate,
    ProductTypeUpdate,
    ProductUpdate,
    ResumoMensal,
    Service,
    ServiceCreate,
    ServiceItem,
    ServiceItemCreate,
    ServiceStatus,
    ServiceStatusLog,
    ServiceSummary,
    ServiceType,
    ServiceUpdate,
    StockPredictionRead,
    StockWarning,
    TipoTransacao,
    Transacao,
    TransacaoCreate,
    TransacaoPublic,
    TransacaoUpdate,
    User,
    UserCreate,
    UserPermission,
    UserUpdate,
    WeeklyOperationalSummary,
    YearlyOperationalDashboard,
    get_datetime_utc,
)

logger = logging.getLogger(__name__)


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


# ── Permission CRUD ───────────────────────────────────────────────────────────


def get_user_permissions(
    *, session: Session, user_id: uuid.UUID
) -> list[UserPermission]:
    statement = select(UserPermission).where(UserPermission.user_id == user_id)
    return list(session.exec(statement).all())


def set_user_permissions(
    *, session: Session, user_id: uuid.UUID, permissions: list[str]
) -> list[UserPermission]:
    from app.core.permissions import ALL_PERMISSIONS, get_role_defaults

    user = session.get(User, user_id)
    if not user:
        msg = f"User {user_id} not found"
        raise ValueError(msg)

    # Validate permission strings
    invalid = [p for p in permissions if p not in ALL_PERMISSIONS]
    if invalid:
        msg = f"Invalid permissions: {invalid}"
        raise ValueError(msg)

    # Filter out role defaults (no need to store redundant overrides)
    role_defaults = get_role_defaults(user.role)
    overrides = [p for p in permissions if p not in role_defaults]

    # Delete existing overrides
    existing = get_user_permissions(session=session, user_id=user_id)
    for perm in existing:
        session.delete(perm)

    # Insert new overrides
    new_perms = []
    for p in overrides:
        up = UserPermission(user_id=user_id, permission=p)
        session.add(up)
        new_perms.append(up)

    session.commit()
    for perm in new_perms:
        session.refresh(perm)
    return new_perms


def clear_user_permissions(*, session: Session, user_id: uuid.UUID) -> None:
    existing = get_user_permissions(session=session, user_id=user_id)
    for perm in existing:
        session.delete(perm)
    session.commit()


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
        .options(
            selectinload(Service.client),  # type: ignore[arg-type]
            selectinload(Service.items),  # type: ignore[arg-type]
            selectinload(Service.status_logs).selectinload(  # type: ignore[arg-type]
                ServiceStatusLog.changed_by_user  # type: ignore[arg-type]
            ),
        )
    )
    return session.exec(statement).first()


def get_services(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[Service], int]:
    """Return a lightweight list of services — does NOT load status_logs.

    status_logs are only loaded by get_service() (single-item detail endpoint)
    to avoid fetching hundreds of log rows for a list response.
    """
    count = session.exec(select(func.count()).select_from(Service)).one()
    statement = (
        select(Service)
        .options(
            selectinload(Service.client),  # type: ignore[arg-type]
            selectinload(Service.items),  # type: ignore[arg-type]
        )
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
    if result is None:
        msg = f"Service {db_service.id} not found after commit"
        raise RuntimeError(msg)  # pragma: no cover
    return result


def update_service(
    *, session: Session, db_service: Service, service_in: ServiceUpdate
) -> Service:
    from datetime import datetime, timezone

    if getattr(service_in, "status", None) is not None:
        msg = "Use the /transition endpoint to change service status"
        raise ValueError(msg)

    service_data = service_in.model_dump(exclude_unset=True)
    db_service.sqlmodel_update(service_data)
    db_service.updated_at = datetime.now(timezone.utc)
    session.add(db_service)
    session.commit()
    result = get_service(session=session, service_id=db_service.id)
    if result is None:
        msg = f"Service {db_service.id} not found after commit"
        raise RuntimeError(msg)  # pragma: no cover
    return result


def delete_service(*, session: Session, db_service: Service) -> None:
    locked = {ServiceStatus.scheduled, ServiceStatus.executing}
    if db_service.status in locked:
        msg = f"Não é possível excluir um serviço com status '{db_service.status}'. Cancele-o primeiro."
        raise ValueError(msg)
    session.delete(db_service)
    session.commit()


def create_service_item(
    *, session: Session, service_id: uuid.UUID, item_in: ServiceItemCreate
) -> ServiceItem:
    service = session.get(Service, service_id)
    locked = {ServiceStatus.executing, ServiceStatus.completed}
    if service is not None and service.status in locked:
        msg = (
            f"Não é possível adicionar itens a um serviço com status '{service.status}'"
        )
        raise ValueError(msg)
    db_item = ServiceItem.model_validate(item_in, update={"service_id": service_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def get_service_item(*, session: Session, item_id: uuid.UUID) -> ServiceItem | None:
    return session.get(ServiceItem, item_id)


def delete_service_item(*, session: Session, db_item: ServiceItem) -> None:
    service = session.get(Service, db_item.service_id)
    locked = {ServiceStatus.executing, ServiceStatus.completed}
    if service is not None and service.status in locked:
        msg = (
            f"Não é possível remover itens de um serviço com status '{service.status}'"
        )
        raise ValueError(msg)
    session.delete(db_item)
    session.commit()


def _release_stock_items(session: Session, service: Service) -> None:
    """Release all reserved ProductItems back to em_estoque when a service is cancelled."""
    items = session.exec(
        select(ProductItem).where(
            ProductItem.service_id == service.id,
            ProductItem.status == ProductItemStatus.reservado,
        )
    ).all()
    for item in items:
        item.status = ProductItemStatus.em_estoque
        item.service_id = None
        item.updated_at = get_datetime_utc()
        session.add(item)


def _check_stock_for_service(session: Session, service: Service) -> list[StockWarning]:
    """Reserve ProductItems for each material ServiceItem. Returns warnings for shortfalls.

    Items are reserved FIFO (oldest created_at first). Reservation is best-effort:
    partial reservation is allowed — a StockWarning is emitted for any shortfall
    but the transition is not blocked.

    When service_item.product_id is set, only ProductItems for that specific product
    are considered. Without product_id, all em_estoque items are candidates (legacy).
    """
    warnings: list[StockWarning] = []
    material_items = [i for i in service.items if i.item_type == ItemType.material]

    for service_item in material_items:
        needed = Decimal(str(service_item.quantity))
        # Use product-scoped reservation when product_id is set (T-20)
        stock_filter = ProductItem.status == ProductItemStatus.em_estoque
        if service_item.product_id is not None:
            stock_filter = stock_filter & (
                ProductItem.product_id == service_item.product_id
            )
        candidates = session.exec(
            select(ProductItem)
            .where(stock_filter)
            .order_by(ProductItem.created_at)  # type: ignore[arg-type]
            .with_for_update()
        ).all()

        reserved = Decimal("0")
        for item in candidates:
            if reserved >= needed:
                break
            item.status = ProductItemStatus.reservado
            item.service_id = service.id
            item.updated_at = get_datetime_utc()
            session.add(item)
            reserved += item.quantity

        if reserved < needed:
            warnings.append(
                StockWarning(
                    service_item_id=service_item.id,
                    description=service_item.description,
                    required_quantity=float(needed),
                    available_quantity=float(reserved),
                    shortfall=float(needed - reserved),
                )
            )

    return warnings


def _deduct_stock_items(
    session: Session,
    service: Service,
    deduction_items: list[DeductionItem],
) -> None:
    """Mark reserved ProductItems as utilizado when a service is completed."""
    material_ids = {
        item.id for item in service.items if item.item_type == ItemType.material
    }
    for d in deduction_items:
        if d.service_item_id not in material_ids:
            msg = f"service_item_id {d.service_item_id} is not a material item of this service"
            raise ValueError(msg)

    reserved_items = session.exec(
        select(ProductItem).where(
            ProductItem.service_id == service.id,
            ProductItem.status == ProductItemStatus.reservado,
        )
    ).all()
    for item in reserved_items:
        item.status = ProductItemStatus.utilizado
        item.updated_at = get_datetime_utc()
        session.add(item)


def transition_service_status(
    session: Session,
    service: Service,
    to_status: ServiceStatus,
    changed_by_id: uuid.UUID,
    reason: str | None = None,
    deduction_items: list[DeductionItem] | None = None,
) -> tuple[Service, list[StockWarning]]:
    allowed = VALID_STATUS_TRANSITIONS.get(service.status, [])
    if to_status not in allowed:
        msg = f"Cannot transition from '{service.status}' to '{to_status}'"
        raise ValueError(msg)

    stock_warnings: list[StockWarning] = []

    logger.info(
        "service_transition_start",
        extra={
            "service_id": str(service.id),
            "from_status": service.status,
            "to_status": to_status,
            "changed_by_id": str(changed_by_id),
        },
    )

    # Handle stock reservation when moving to scheduled
    if to_status == ServiceStatus.scheduled:
        stock_warnings = _check_stock_for_service(session, service)
        if stock_warnings:
            logger.warning(
                "service_transition_stock_warnings",
                extra={
                    "service_id": str(service.id),
                    "warning_count": len(stock_warnings),
                },
            )

    # Handle stock deduction when moving to completed
    if to_status == ServiceStatus.completed:
        _deduct_stock_items(session, service, deduction_items or [])

    # Handle cancellation — release any reserved stock
    if to_status == ServiceStatus.cancelled:
        service.cancelled_reason = reason
        _release_stock_items(session, service)

    log = ServiceStatusLog(
        service_id=service.id,
        from_status=service.status,
        to_status=to_status,
        changed_by=changed_by_id,
        notes=reason,
    )
    session.add(log)

    service.status = to_status
    service.updated_at = get_datetime_utc()
    session.add(service)
    session.commit()
    session.refresh(service)

    return service, stock_warnings


def get_service_status_logs(
    session: Session, service_id: uuid.UUID
) -> list[ServiceStatusLog]:
    statement = (
        select(ServiceStatusLog)
        .where(ServiceStatusLog.service_id == service_id)
        .options(selectinload(ServiceStatusLog.changed_by_user))  # type: ignore[arg-type]
        .order_by(ServiceStatusLog.changed_at)  # type: ignore[arg-type]
    )
    return list(session.exec(statement).all())


def deduct_stock(
    session: Session,
    service: Service,
    _changed_by_id: uuid.UUID,
) -> list[DeductionSummary]:
    """Manually deduct all reserved ProductItems for a service in executing status."""
    if service.status != ServiceStatus.executing:
        msg = "Stock can only be deducted from a service in 'executing' status"
        raise ValueError(msg)

    reserved_items = session.exec(
        select(ProductItem).where(
            ProductItem.service_id == service.id,
            ProductItem.status == ProductItemStatus.reservado,
        )
    ).all()

    result: list[DeductionSummary] = []
    for item in reserved_items:
        item.status = ProductItemStatus.utilizado
        item.updated_at = get_datetime_utc()
        session.add(item)
        result.append(
            DeductionSummary(product_item_id=item.id, quantity=float(item.quantity))
        )

    session.commit()
    return result


# ── Transacao CRUD ─────────────────────────────────────────────────────────────


def _build_transacao_public(t: Transacao) -> TransacaoPublic:
    """Convert a Transacao ORM object to TransacaoPublic with embedded summaries."""
    service_summary = None
    if t.service is not None:
        service_summary = ServiceSummary(
            id=t.service.id,
            type=t.service.type,
            status=t.service.status,
        )
    client_ref = None
    if t.client is not None:
        client_ref = ClientRef(id=t.client.id, name=t.client.name)
    return TransacaoPublic(
        id=t.id,
        tipo=t.tipo,
        categoria=t.categoria,
        valor=t.valor,
        data_competencia=t.data_competencia,
        descricao=t.descricao,
        nome_contraparte=t.nome_contraparte,
        service_id=t.service_id,
        client_id=t.client_id,
        fornecedor_id=t.fornecedor_id,
        service=service_summary,
        client=client_ref,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _get_transacao_with_relations(
    session: Session, transacao_id: uuid.UUID
) -> Transacao | None:
    statement = (
        select(Transacao)
        .where(Transacao.id == transacao_id)
        .options(selectinload(Transacao.service), selectinload(Transacao.client))  # type: ignore
    )
    return session.exec(statement).first()


def create_transacao(
    *, session: Session, transacao_in: TransacaoCreate
) -> TransacaoPublic:
    if transacao_in.service_id is not None:
        if session.get(Service, transacao_in.service_id) is None:
            msg = "Service not found"
            raise ValueError(msg)
    if transacao_in.client_id is not None:
        if session.get(Client, transacao_in.client_id) is None:
            msg = "Client not found"
            raise ValueError(msg)

    db_transacao = Transacao.model_validate(transacao_in)
    session.add(db_transacao)
    session.commit()
    result = _get_transacao_with_relations(session, db_transacao.id)
    if result is None:
        msg = f"Transacao {db_transacao.id} not found after commit"
        raise RuntimeError(msg)  # pragma: no cover
    return _build_transacao_public(result)


def get_transacao(
    *, session: Session, transacao_id: uuid.UUID
) -> TransacaoPublic | None:
    t = _get_transacao_with_relations(session, transacao_id)
    if t is None:
        return None
    return _build_transacao_public(t)


def get_transacoes(
    *,
    session: Session,
    tipo: TipoTransacao | None = None,
    categoria: CategoriaTransacao | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    service_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[TransacaoPublic], int]:
    base = select(Transacao)
    count_base = select(func.count()).select_from(Transacao)

    if tipo is not None:
        base = base.where(Transacao.tipo == tipo)
        count_base = count_base.where(Transacao.tipo == tipo)
    if categoria is not None:
        base = base.where(Transacao.categoria == categoria)
        count_base = count_base.where(Transacao.categoria == categoria)
    if data_inicio is not None:
        base = base.where(Transacao.data_competencia >= data_inicio)
        count_base = count_base.where(Transacao.data_competencia >= data_inicio)
    if data_fim is not None:
        base = base.where(Transacao.data_competencia <= data_fim)
        count_base = count_base.where(Transacao.data_competencia <= data_fim)
    if service_id is not None:
        base = base.where(Transacao.service_id == service_id)
        count_base = count_base.where(Transacao.service_id == service_id)

    count = session.exec(count_base).one()
    statement = (
        base.order_by(Transacao.data_competencia.desc())  # type: ignore
        .options(selectinload(Transacao.service), selectinload(Transacao.client))  # type: ignore
        .offset(skip)
        .limit(limit)
    )
    transacoes = session.exec(statement).all()
    return [_build_transacao_public(t) for t in transacoes], count


def update_transacao(
    *,
    session: Session,
    db_transacao: Transacao,
    transacao_in: TransacaoUpdate,
) -> TransacaoPublic:
    update_data = transacao_in.model_dump(exclude_unset=True)

    if "service_id" in update_data and update_data["service_id"] is not None:
        if session.get(Service, update_data["service_id"]) is None:
            msg = "Service not found"
            raise ValueError(msg)

    # validate categoria/tipo compatibility if categoria is being changed
    if "categoria" in update_data and update_data["categoria"] is not None:
        from app.models import EXPENSE_CATEGORIES, INCOME_CATEGORIES

        new_cat = update_data["categoria"]
        if (
            db_transacao.tipo == TipoTransacao.receita
            and new_cat not in INCOME_CATEGORIES
        ):
            msg = f"categoria '{new_cat}' is not valid for tipo='receita'"
            raise ValueError(msg)
        if (
            db_transacao.tipo == TipoTransacao.despesa
            and new_cat not in EXPENSE_CATEGORIES
        ):
            msg = f"categoria '{new_cat}' is not valid for tipo='despesa'"
            raise ValueError(msg)

    db_transacao.sqlmodel_update(update_data)
    db_transacao.updated_at = datetime.now(timezone.utc)
    session.add(db_transacao)
    session.commit()
    result = _get_transacao_with_relations(session, db_transacao.id)
    if result is None:
        msg = f"Transacao {db_transacao.id} not found after commit"
        raise RuntimeError(msg)  # pragma: no cover
    return _build_transacao_public(result)


def delete_transacao(*, session: Session, db_transacao: Transacao) -> None:
    session.delete(db_transacao)
    session.commit()


def get_resumo_mensal(*, session: Session, ano: int, mes: int) -> ResumoMensal:
    from calendar import monthrange

    first_day = date(ano, mes, 1)
    last_day = date(ano, mes, monthrange(ano, mes)[1])

    statement = (
        select(Transacao.tipo, func.sum(Transacao.valor))
        .where(Transacao.data_competencia >= first_day)
        .where(Transacao.data_competencia <= last_day)
        .group_by(Transacao.tipo)
    )
    rows = session.exec(statement).all()
    totals: dict[str, Decimal] = {
        TipoTransacao.receita: Decimal(0),
        TipoTransacao.despesa: Decimal(0),
    }
    for tipo, total in rows:
        totals[tipo] = total or Decimal(0)

    total_receitas = totals[TipoTransacao.receita]
    total_despesas = totals[TipoTransacao.despesa]
    return ResumoMensal(
        ano=ano,
        mes=mes,
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        resultado_liquido=total_receitas - total_despesas,
    )


# ── Fornecedor ────────────────────────────────────────────────────────────────


def _fornecedor_options() -> list[Any]:
    return [
        selectinload(Fornecedor.contatos),  # type: ignore[arg-type]
        selectinload(Fornecedor.categorias),  # type: ignore[arg-type]
    ]


def get_fornecedores(
    *,
    session: Session,
    search: str | None = None,
    category: FornecedorCategoryEnum | None = None,
) -> list[Fornecedor]:
    statement = select(Fornecedor).options(*_fornecedor_options())
    if search:
        statement = statement.where(Fornecedor.company_name.ilike(f"%{search}%"))  # type: ignore[attr-defined]
    if category:
        statement = statement.where(
            Fornecedor.id.in_(  # type: ignore[attr-defined]
                select(FornecedorCategoria.fornecedor_id).where(
                    FornecedorCategoria.category == category.value
                )
            )
        )
    return list(session.exec(statement).all())


def get_fornecedor(*, session: Session, fornecedor_id: uuid.UUID) -> Fornecedor | None:
    statement = (
        select(Fornecedor)
        .where(Fornecedor.id == fornecedor_id)
        .options(*_fornecedor_options())
    )
    return session.exec(statement).first()


def create_fornecedor(*, session: Session, data: FornecedorCreate) -> Fornecedor:
    fornecedor = Fornecedor(
        company_name=data.company_name,
        cnpj=data.cnpj,
        address=data.address,
        notes=data.notes,
    )
    session.add(fornecedor)
    session.flush()
    for cat in data.categories:
        session.add(
            FornecedorCategoria(fornecedor_id=fornecedor.id, category=cat.value)
        )
    session.commit()
    session.refresh(fornecedor)
    # reload with relationships
    return get_fornecedor(session=session, fornecedor_id=fornecedor.id)  # type: ignore[return-value]


def update_fornecedor(
    *, session: Session, fornecedor: Fornecedor, data: FornecedorUpdate
) -> Fornecedor:
    update_data = data.model_dump(exclude_unset=True)
    categories = update_data.pop("categories", None)

    for field, value in update_data.items():
        setattr(fornecedor, field, value)

    if categories is not None:
        for existing_cat in list(fornecedor.categorias):
            session.delete(existing_cat)
        fornecedor.categorias.clear()
        session.flush()
        for cat in categories:
            session.add(
                FornecedorCategoria(
                    fornecedor_id=fornecedor.id,
                    category=cat.value
                    if isinstance(cat, FornecedorCategoryEnum)
                    else cat,
                )
            )

    session.add(fornecedor)
    session.commit()
    return get_fornecedor(session=session, fornecedor_id=fornecedor.id)  # type: ignore[return-value]


def delete_fornecedor(*, session: Session, fornecedor: Fornecedor) -> None:
    session.delete(fornecedor)
    session.commit()


def create_contato(
    *, session: Session, fornecedor_id: uuid.UUID, data: FornecedorContatoCreate
) -> FornecedorContato:
    contato = FornecedorContato(
        fornecedor_id=fornecedor_id,
        name=data.name,
        telefone=data.telefone,
        whatsapp=data.whatsapp,
        description=data.description,
    )
    session.add(contato)
    session.commit()
    session.refresh(contato)
    return contato


def update_contato(
    *, session: Session, contato: FornecedorContato, data: FornecedorContatoUpdate
) -> FornecedorContato:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contato, field, value)
    session.add(contato)
    session.commit()
    session.refresh(contato)
    return contato


def delete_contato(*, session: Session, contato: FornecedorContato) -> None:
    session.delete(contato)
    session.commit()


# ── ProductType CRUD ───────────────────────────────────────────────────────────


def create_product_type(*, session: Session, pt_in: ProductTypeCreate) -> ProductType:
    from sqlalchemy.exc import IntegrityError

    existing = session.exec(
        select(ProductType).where(
            ProductType.category == pt_in.category,
            ProductType.name == pt_in.name,
        )
    ).first()
    if existing:
        msg = f"ProductType with category '{pt_in.category}' and name '{pt_in.name}' already exists"
        raise ValueError(msg)
    pt = ProductType.model_validate(pt_in)
    session.add(pt)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        msg = f"ProductType with category '{pt_in.category}' and name '{pt_in.name}' already exists"
        raise ValueError(msg)
    session.refresh(pt)
    return pt


def get_product_type(
    *, session: Session, product_type_id: uuid.UUID
) -> ProductType | None:
    return session.get(ProductType, product_type_id)


def get_product_types(*, session: Session) -> list[ProductType]:
    return list(session.exec(select(ProductType)).all())


def update_product_type(
    *, session: Session, pt: ProductType, pt_in: ProductTypeUpdate
) -> ProductType:
    update_data = pt_in.model_dump(exclude_unset=True)
    pt.sqlmodel_update(update_data)
    pt.updated_at = get_datetime_utc()
    session.add(pt)
    session.commit()
    session.refresh(pt)
    return pt


def delete_product_type(*, session: Session, product_type_id: uuid.UUID) -> None:
    from sqlalchemy.exc import IntegrityError

    pt = session.get(ProductType, product_type_id)
    if pt is None:
        return
    try:
        session.delete(pt)
        session.commit()
    except IntegrityError:
        session.rollback()
        msg = "Cannot delete ProductType: products reference this type"
        raise ValueError(msg)


# ── Product CRUD ───────────────────────────────────────────────────────────────


def _product_options() -> list[Any]:
    return [
        selectinload(Product.product_type),  # type: ignore[arg-type]
        selectinload(Product.fornecedor),  # type: ignore[arg-type]
    ]


def create_product(*, session: Session, product_in: ProductCreate) -> Product:
    if session.get(ProductType, product_in.product_type_id) is None:
        msg = "ProductType not found"
        raise ValueError(msg)
    if product_in.fornecedor_id is not None:
        if session.get(Fornecedor, product_in.fornecedor_id) is None:
            msg = "Fornecedor not found"
            raise ValueError(msg)
    product = Product.model_validate(product_in)
    session.add(product)
    session.commit()
    result = get_product(session=session, product_id=product.id)
    if result is None:
        msg = f"Product {product.id} not found after commit"
        raise RuntimeError(msg)  # pragma: no cover
    return result


def get_product(*, session: Session, product_id: uuid.UUID) -> Product | None:
    statement = (
        select(Product).where(Product.id == product_id).options(*_product_options())
    )
    return session.exec(statement).first()


def get_products(
    *,
    session: Session,
    category: ProductCategory | None = None,
    fornecedor_id: uuid.UUID | None = None,
) -> list[Product]:
    statement = select(Product).options(*_product_options())
    if category is not None:
        statement = statement.join(ProductType).where(ProductType.category == category)
    if fornecedor_id is not None:
        statement = statement.where(Product.fornecedor_id == fornecedor_id)
    return list(session.exec(statement).all())


def update_product(
    *, session: Session, product: Product, product_in: ProductUpdate
) -> Product:
    update_data = product_in.model_dump(exclude_unset=True)
    if "product_type_id" in update_data and update_data["product_type_id"] is not None:
        if session.get(ProductType, update_data["product_type_id"]) is None:
            msg = "ProductType not found"
            raise ValueError(msg)
    if "fornecedor_id" in update_data and update_data["fornecedor_id"] is not None:
        if session.get(Fornecedor, update_data["fornecedor_id"]) is None:
            msg = "Fornecedor not found"
            raise ValueError(msg)
    product.sqlmodel_update(update_data)
    product.updated_at = get_datetime_utc()
    session.add(product)
    session.commit()
    result = get_product(session=session, product_id=product.id)
    if result is None:
        msg = f"Product {product.id} not found after commit"
        raise RuntimeError(msg)  # pragma: no cover
    return result


def delete_product(*, session: Session, product_id: uuid.UUID) -> None:
    from sqlalchemy.exc import IntegrityError

    product = session.get(Product, product_id)
    if product is None:
        return
    try:
        session.delete(product)
        session.commit()
    except IntegrityError:
        session.rollback()
        msg = "Cannot delete Product: stock items reference this product"
        raise ValueError(msg)


# ── ProductItem CRUD ───────────────────────────────────────────────────────────


def create_product_item(*, session: Session, item_in: ProductItemCreate) -> ProductItem:
    if session.get(Product, item_in.product_id) is None:
        msg = "Product not found"
        raise ValueError(msg)
    item = ProductItem(
        product_id=item_in.product_id,
        quantity=item_in.quantity,
        status=ProductItemStatus.em_estoque,
        service_id=None,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def get_product_items_by_product(
    *, session: Session, product_id: uuid.UUID
) -> list[ProductItem]:
    statement = (
        select(ProductItem)
        .where(ProductItem.product_id == product_id)
        .options(selectinload(ProductItem.service))  # type: ignore[arg-type]
        .order_by(ProductItem.created_at.desc())  # type: ignore[union-attr]
    )
    return list(session.exec(statement).all())


def get_product_items_by_service(
    *,
    session: Session,
    service_id: uuid.UUID,
    status: ProductItemStatus | None = None,
) -> list[ProductItem]:
    statement = select(ProductItem).where(ProductItem.service_id == service_id)
    if status is not None:
        statement = statement.where(ProductItem.status == status)
    return list(session.exec(statement).all())


def get_product_items(
    *,
    session: Session,
    product_id: uuid.UUID | None = None,
    status: ProductItemStatus | None = None,
    service_id: uuid.UUID | None = None,
) -> list[ProductItem]:
    statement = select(ProductItem)
    if product_id is not None:
        statement = statement.where(ProductItem.product_id == product_id)
    if status is not None:
        statement = statement.where(ProductItem.status == status)
    if service_id is not None:
        statement = statement.where(ProductItem.service_id == service_id)
    return list(session.exec(statement).all())


def validate_product_item_transition(
    current_status: ProductItemStatus, new_status: ProductItemStatus
) -> None:
    allowed: set[tuple[ProductItemStatus, ProductItemStatus]] = {
        (ProductItemStatus.em_estoque, ProductItemStatus.reservado),
        (ProductItemStatus.reservado, ProductItemStatus.utilizado),
    }
    if (current_status, new_status) not in allowed:
        msg = f"Invalid transition from '{current_status}' to '{new_status}'"
        raise ValueError(msg)


def reserve_stock_for_service(
    session: Session,
    service_id: uuid.UUID,
    product_quantities: list[tuple[uuid.UUID, Decimal]],
) -> list[InventoryStockWarning]:
    warnings: list[InventoryStockWarning] = []
    for product_id, needed_qty in product_quantities:
        product = session.get(Product, product_id)
        if product is None:
            continue
        # Select em_estoque items for this product, ordered by oldest first
        items = list(
            session.exec(
                select(ProductItem)
                .where(
                    ProductItem.product_id == product_id,
                    ProductItem.status == ProductItemStatus.em_estoque,
                )
                .order_by(ProductItem.created_at)  # type: ignore[arg-type]
                .with_for_update()
            ).all()
        )
        available_qty = sum((i.quantity for i in items), Decimal("0"))
        remaining = needed_qty
        for item in items:
            if remaining <= 0:
                break
            item.status = ProductItemStatus.reservado
            item.service_id = service_id
            item.updated_at = get_datetime_utc()
            session.add(item)
            remaining -= item.quantity
        if remaining > 0:
            # Shortfall
            warnings.append(
                InventoryStockWarning(
                    product_id=product_id,
                    product_name=product.name,
                    required_qty=needed_qty,
                    available_qty=available_qty,
                    shortfall_qty=remaining,
                )
            )
    session.commit()
    return warnings


def utilize_reserved_items_for_service(session: Session, service_id: uuid.UUID) -> int:
    items = list(
        session.exec(
            select(ProductItem).where(
                ProductItem.service_id == service_id,
                ProductItem.status == ProductItemStatus.reservado,
            )
        ).all()
    )
    for item in items:
        item.status = ProductItemStatus.utilizado
        item.updated_at = get_datetime_utc()
        session.add(item)
    session.commit()
    return len(items)


# ── Stock Prediction & Dashboard ──────────────────────────────────────────────


def get_stock_prediction(
    *, session: Session, product_id: uuid.UUID
) -> StockPredictionRead:
    from datetime import timedelta

    now = get_datetime_utc()
    window_start = now - timedelta(days=90)

    em_estoque_qty = session.exec(
        select(func.sum(ProductItem.quantity)).where(
            ProductItem.product_id == product_id,
            ProductItem.status == ProductItemStatus.em_estoque,
        )
    ).one() or Decimal("0")

    reservado_qty = session.exec(
        select(func.sum(ProductItem.quantity)).where(
            ProductItem.product_id == product_id,
            ProductItem.status == ProductItemStatus.reservado,
        )
    ).one() or Decimal("0")

    utilizado_90d = session.exec(
        select(func.sum(ProductItem.quantity)).where(
            ProductItem.product_id == product_id,
            ProductItem.status == ProductItemStatus.utilizado,
            ProductItem.updated_at >= window_start,  # type: ignore[operator]
        )
    ).one() or Decimal("0")

    avg_daily = Decimal(str(utilizado_90d)) / Decimal("90") if utilizado_90d else None

    days_to_stockout: int | None = None
    net_stock = Decimal(str(em_estoque_qty)) - Decimal(str(reservado_qty))
    if avg_daily is None or avg_daily == 0:
        # No known consumption history — cannot predict, treat as green
        if net_stock <= 0 and (em_estoque_qty > 0 or reservado_qty > 0):
            # Had stock but it's all reserved; still no consumption data
            level = "yellow"
        else:
            level = "green"
    elif net_stock <= 0:
        level = "red"
    else:
        days_to_stockout = int(net_stock / avg_daily)
        if days_to_stockout <= 7:
            level = "red"
        elif days_to_stockout <= 30:
            level = "yellow"
        else:
            level = "green"

    return StockPredictionRead(
        product_id=product_id,
        days_to_stockout=days_to_stockout,
        level=level,
        em_estoque_qty=Decimal(str(em_estoque_qty)),
        reservado_qty=Decimal(str(reservado_qty)),
        avg_daily_consumption=avg_daily,
    )


def get_stock_dashboard(*, session: Session) -> list[CategoryDashboardItem]:

    # Query all categories and statuses in one pass using GROUP BY
    rows = session.exec(
        select(
            ProductType.category,
            ProductItem.status,
            func.sum(ProductItem.quantity),
        )
        .join(Product, Product.product_type_id == ProductType.id)  # type: ignore[arg-type]
        .join(ProductItem, ProductItem.product_id == Product.id)  # type: ignore[arg-type]
        .group_by(ProductType.category, ProductItem.status)
    ).all()

    # Build a dict: category -> status -> total
    totals: dict[str, dict[str, Decimal]] = {}
    for cat_val, status_val, total in rows:
        cat = cat_val.value if isinstance(cat_val, ProductCategory) else cat_val
        status = (
            status_val.value
            if isinstance(status_val, ProductItemStatus)
            else status_val
        )
        if cat not in totals:
            totals[cat] = {}
        totals[cat][status] = Decimal(str(total or 0))

    result = []
    for cat in ProductCategory:
        cat_data = totals.get(cat.value, {})
        result.append(
            CategoryDashboardItem(
                category=cat,
                em_estoque_total=cat_data.get(
                    ProductItemStatus.em_estoque.value, Decimal("0")
                ),
                reservado_total=cat_data.get(
                    ProductItemStatus.reservado.value, Decimal("0")
                ),
                utilizado_total=cat_data.get(
                    ProductItemStatus.utilizado.value, Decimal("0")
                ),
            )
        )
    return result


def baixar_estoque_for_service(
    *, session: Session, service_id: uuid.UUID
) -> BaixarEstoqueResponse:
    service = session.get(Service, service_id)
    if service is None or service.status != ServiceStatus.executing:
        msg = "Service must be in 'executing' status to baixar estoque"
        raise ValueError(msg)
    count = utilize_reserved_items_for_service(session=session, service_id=service_id)
    return BaixarEstoqueResponse(service_id=service_id, items_updated=count)


# ── Orçamento CRUD ─────────────────────────────────────────────────────────────


def _generate_ref_code(session: Session) -> str:
    """Generate a unique 6-char uppercase hex code. Retry on collision."""
    import secrets

    for _ in range(10):
        code = secrets.token_hex(3).upper()
        existing = session.exec(
            select(Orcamento).where(Orcamento.ref_code == code)
        ).first()
        if existing is None:
            return code
    msg = "Failed to generate unique ref_code after 10 attempts"
    raise RuntimeError(msg)  # pragma: no cover


def _orcamento_detail_options() -> list[Any]:
    return [
        selectinload(Orcamento.client),  # type: ignore[arg-type]
        selectinload(Orcamento.items).selectinload(OrcamentoItem.product),  # type: ignore[arg-type]
        selectinload(Orcamento.status_logs).selectinload(  # type: ignore[arg-type]
            OrcamentoStatusLog.changed_by_user  # type: ignore[arg-type]
        ),
    ]


def get_orcamento(*, session: Session, orcamento_id: uuid.UUID) -> Orcamento | None:
    statement = (
        select(Orcamento)
        .where(Orcamento.id == orcamento_id)
        .options(*_orcamento_detail_options())
    )
    return session.exec(statement).first()


def get_orcamentos(
    *,
    session: Session,
    search: str | None = None,
    status: OrcamentoStatus | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Orcamento], int]:
    base = select(Orcamento)
    count_base = select(func.count()).select_from(Orcamento)

    if search is not None:
        pattern = f"%{search}%"
        search_filter = Orcamento.client_id.in_(  # type: ignore[attr-defined]
            select(Client.id).where(
                (Client.name.ilike(pattern))  # type: ignore[attr-defined]
                | (Client.document_number.ilike(pattern))  # type: ignore[attr-defined]
            )
        )
        base = base.where(search_filter)
        count_base = count_base.where(search_filter)

    if status is not None:
        base = base.where(Orcamento.status == status)
        count_base = count_base.where(Orcamento.status == status)

    if data_inicio is not None:
        base = base.where(Orcamento.created_at >= data_inicio)  # type: ignore[operator]
        count_base = count_base.where(Orcamento.created_at >= data_inicio)  # type: ignore[operator]

    if data_fim is not None:
        base = base.where(Orcamento.created_at <= data_fim)  # type: ignore[operator]
        count_base = count_base.where(Orcamento.created_at <= data_fim)  # type: ignore[operator]

    count = session.exec(count_base).one()
    statement = (
        base.options(selectinload(Orcamento.client))  # type: ignore[arg-type]
        .order_by(Orcamento.created_at.desc())  # type: ignore[union-attr]
        .offset(skip)
        .limit(limit)
    )
    orcamentos = session.exec(statement).all()
    return list(orcamentos), count


def create_orcamento(
    *, session: Session, orcamento_in: OrcamentoCreate, created_by_id: uuid.UUID
) -> Orcamento:
    ref_code = _generate_ref_code(session)
    db_orcamento = Orcamento.model_validate(
        orcamento_in, update={"ref_code": ref_code, "created_by": created_by_id}
    )
    session.add(db_orcamento)
    session.commit()
    result = get_orcamento(session=session, orcamento_id=db_orcamento.id)
    if result is None:
        msg = f"Orcamento {db_orcamento.id} not found after commit"
        raise RuntimeError(msg)  # pragma: no cover
    return result


def update_orcamento(
    *, session: Session, db_orcamento: Orcamento, orcamento_in: OrcamentoUpdate
) -> Orcamento:
    locked = {OrcamentoStatus.aprovado, OrcamentoStatus.cancelado}
    if db_orcamento.status in locked:
        msg = f"Não é possível editar um orçamento com status '{db_orcamento.status}'"
        raise ValueError(msg)
    update_data = orcamento_in.model_dump(exclude_unset=True)
    db_orcamento.sqlmodel_update(update_data)
    db_orcamento.updated_at = get_datetime_utc()
    session.add(db_orcamento)
    session.commit()
    result = get_orcamento(session=session, orcamento_id=db_orcamento.id)
    if result is None:
        msg = f"Orcamento {db_orcamento.id} not found after commit"
        raise RuntimeError(msg)  # pragma: no cover
    return result


def delete_orcamento(*, session: Session, db_orcamento: Orcamento) -> None:
    if db_orcamento.status != OrcamentoStatus.rascunho:
        msg = f"Apenas orçamentos em rascunho podem ser excluídos (status atual: '{db_orcamento.status}')"
        raise ValueError(msg)
    session.delete(db_orcamento)
    session.commit()


def transition_orcamento_status(
    session: Session,
    orcamento: Orcamento,
    to_status: OrcamentoStatus,
    changed_by_id: uuid.UUID,
    reason: str | None = None,
) -> Orcamento:
    allowed = VALID_ORCAMENTO_TRANSITIONS.get(orcamento.status, [])
    if to_status not in allowed:
        msg = f"Transição inválida: '{orcamento.status}' → '{to_status}'"
        raise ValueError(msg)

    # Guard: can't approve without items
    if to_status == OrcamentoStatus.aprovado and len(orcamento.items) == 0:
        msg = "Não é possível aprovar um orçamento sem itens"
        raise ValueError(msg)

    # Guard: can't cancel or un-approve a converted orçamento
    if orcamento.service_id is not None and to_status in {
        OrcamentoStatus.cancelado,
        OrcamentoStatus.em_analise,
    }:
        msg = "Não é possível alterar o status de um orçamento já convertido em serviço"
        raise ValueError(msg)

    log = OrcamentoStatusLog(
        orcamento_id=orcamento.id,
        from_status=orcamento.status,
        to_status=to_status,
        changed_by=changed_by_id,
        notes=reason,
    )
    session.add(log)

    orcamento.status = to_status
    orcamento.updated_at = get_datetime_utc()
    session.add(orcamento)
    session.commit()
    session.refresh(orcamento)

    result = get_orcamento(session=session, orcamento_id=orcamento.id)
    if result is None:
        msg = f"Orcamento {orcamento.id} not found after commit"
        raise RuntimeError(msg)  # pragma: no cover
    return result


# ── Orçamento Items ────────────────────────────────────────────────────────────


def create_orcamento_item(
    *, session: Session, orcamento_id: uuid.UUID, item_in: OrcamentoItemCreate
) -> OrcamentoItem:
    orcamento = session.get(Orcamento, orcamento_id)
    if orcamento is None:
        msg = "Orçamento não encontrado"
        raise ValueError(msg)
    locked = {OrcamentoStatus.aprovado, OrcamentoStatus.cancelado}
    if orcamento.status in locked:
        msg = f"Não é possível adicionar itens a um orçamento com status '{orcamento.status}'"
        raise ValueError(msg)
    product = session.get(Product, item_in.product_id)
    if product is None:
        msg = "Produto não encontrado"
        raise ValueError(msg)
    db_item = OrcamentoItem.model_validate(
        item_in, update={"orcamento_id": orcamento_id}
    )
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def update_orcamento_item(
    *, session: Session, db_item: OrcamentoItem, item_in: OrcamentoItemUpdate
) -> OrcamentoItem:
    orcamento = session.get(Orcamento, db_item.orcamento_id)
    locked = {OrcamentoStatus.aprovado, OrcamentoStatus.cancelado}
    if orcamento is not None and orcamento.status in locked:
        msg = f"Não é possível editar itens de um orçamento com status '{orcamento.status}'"
        raise ValueError(msg)
    update_data = item_in.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(update_data)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def delete_orcamento_item(*, session: Session, db_item: OrcamentoItem) -> None:
    orcamento = session.get(Orcamento, db_item.orcamento_id)
    locked = {OrcamentoStatus.aprovado, OrcamentoStatus.cancelado}
    if orcamento is not None and orcamento.status in locked:
        msg = f"Não é possível remover itens de um orçamento com status '{orcamento.status}'"
        raise ValueError(msg)
    session.delete(db_item)
    session.commit()


# ── Orçamento Conversions ──────────────────────────────────────────────────────


def convert_orcamento_to_service(
    session: Session,
    orcamento: Orcamento,
    created_by_id: uuid.UUID,  # noqa: ARG001 — kept for audit trail in future
) -> Service:
    """Create a Service from an approved Orçamento. One-time only."""
    if orcamento.status != OrcamentoStatus.aprovado:
        msg = "Apenas orçamentos aprovados podem ser convertidos em serviço"
        raise ValueError(msg)
    if orcamento.service_id is not None:
        msg = "Este orçamento já foi convertido em serviço"
        raise ValueError(msg)

    service_in = ServiceCreate(
        type=orcamento.service_type,
        client_id=orcamento.client_id,
        execution_address=orcamento.execution_address,
    )
    db_service = Service.model_validate(service_in)
    if orcamento.description:
        db_service.description = orcamento.description
    session.add(db_service)
    session.flush()

    # Copy items as ServiceItems
    for orc_item in orcamento.items:
        svc_item = ServiceItem(
            service_id=db_service.id,
            item_type=ItemType.material,
            product_id=orc_item.product_id,
            description=orc_item.description,
            quantity=float(orc_item.quantity),
            unit_price=float(orc_item.unit_price),
        )
        session.add(svc_item)

    orcamento.service_id = db_service.id
    orcamento.updated_at = get_datetime_utc()
    session.add(orcamento)
    session.commit()

    result = get_service(session=session, service_id=db_service.id)
    if result is None:
        msg = f"Service {db_service.id} not found after commit"
        raise RuntimeError(msg)  # pragma: no cover
    return result


def duplicate_orcamento(
    session: Session, orcamento: Orcamento, created_by_id: uuid.UUID
) -> Orcamento:
    """Create a deep copy of an orçamento as a new rascunho."""
    ref_code = _generate_ref_code(session)
    new_orc = Orcamento(
        ref_code=ref_code,
        client_id=orcamento.client_id,
        service_type=orcamento.service_type,
        status=OrcamentoStatus.rascunho,
        execution_address=orcamento.execution_address,
        city=orcamento.city,
        cep=orcamento.cep,
        description=orcamento.description,
        notes=orcamento.notes,
        forma_pagamento=orcamento.forma_pagamento,
        vendedor=orcamento.vendedor,
        created_by=created_by_id,
    )
    session.add(new_orc)
    session.flush()

    for item in orcamento.items:
        new_item = OrcamentoItem(
            orcamento_id=new_orc.id,
            product_id=item.product_id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            show_unit_price=item.show_unit_price,
        )
        session.add(new_item)

    session.commit()
    result = get_orcamento(session=session, orcamento_id=new_orc.id)
    if result is None:
        msg = f"Orcamento {new_orc.id} not found after commit"
        raise RuntimeError(msg)  # pragma: no cover
    return result


# ── Dashboard CRUD ─────────────────────────────────────────────────────────────


def get_yearly_operational_summary(
    *, session: Session, ano: int
) -> YearlyOperationalDashboard:
    """Return weekly operational KPIs for the given year (ISO weeks).

    Three aggregation queries:
      1. Completed service counts by type (repairs vs drillings), grouped by ISO week
      2. Drilling meters (SUM of service_item.quantity where item_type=perfuração), grouped by ISO week
      3. Weekly profit (receitas - despesas from transacao), grouped by ISO week

    Weeks with no activity get zeros. Only weeks up to the current ISO week are returned.
    """
    today = date.today()
    max_week = today.isocalendar()[1] if today.year == ano else 52

    # ── Query 1: completed service counts by type and ISO week ─────────────────
    service_rows = session.exec(
        select(
            extract("week", Service.updated_at).label("week_num"),  # type: ignore[arg-type]
            Service.type,
            func.count(Service.id),  # type: ignore[arg-type]
        )
        .where(Service.status == ServiceStatus.completed)
        .where(extract("year", Service.updated_at) == ano)  # type: ignore[arg-type]
        .group_by(extract("week", Service.updated_at), Service.type)  # type: ignore[arg-type]
    ).all()

    # ── Query 2: drilling meters (perfuração items) by ISO week ────────────────
    meters_rows = session.exec(
        select(
            extract("week", Service.updated_at).label("week_num"),  # type: ignore[arg-type]
            func.sum(ServiceItem.quantity),
        )
        .join(Service, ServiceItem.service_id == Service.id)  # type: ignore[arg-type]
        .where(ServiceItem.item_type == ItemType.perfuracao)
        .where(Service.status == ServiceStatus.completed)
        .where(extract("year", Service.updated_at) == ano)  # type: ignore[arg-type]
        .group_by(extract("week", Service.updated_at))  # type: ignore[arg-type]
    ).all()

    # ── Query 3: weekly profit (receitas - despesas) ───────────────────────────
    profit_rows = session.exec(
        select(
            extract("week", Transacao.data_competencia).label("week_num"),  # type: ignore[arg-type]
            Transacao.tipo,
            func.sum(Transacao.valor),
        )
        .where(extract("year", Transacao.data_competencia) == ano)  # type: ignore[arg-type]
        .group_by(
            extract("week", Transacao.data_competencia),  # type: ignore[arg-type]
            Transacao.tipo,
        )
    ).all()

    # ── Merge results into per-week dicts ──────────────────────────────────────
    repairs: dict[int, int] = {}
    drillings: dict[int, int] = {}
    for week_num_raw, svc_type, count in service_rows:
        week_num = int(week_num_raw)
        if svc_type == ServiceType.reparo:  # noqa: SIM114
            repairs[week_num] = repairs.get(week_num, 0) + count
        elif svc_type == ServiceType.perfuracao:
            drillings[week_num] = drillings.get(week_num, 0) + count

    meters: dict[int, Decimal] = {}
    for week_num_raw, total in meters_rows:
        meters[int(week_num_raw)] = Decimal(str(total or 0))

    receitas: dict[int, Decimal] = {}
    despesas: dict[int, Decimal] = {}
    for week_num_raw, tipo, total in profit_rows:  # type: ignore[assignment]
        week_num = int(week_num_raw)
        val: Decimal = Decimal(str(total or 0))
        if tipo == TipoTransacao.receita:
            receitas[week_num] = val
        else:
            despesas[week_num] = val

    # ── Build list of WeeklyOperationalSummary ─────────────────────────────────
    weeks: list[WeeklyOperationalSummary] = []
    for week_num in range(1, max_week + 1):
        week_start = date.fromisocalendar(ano, week_num, 1)  # Monday
        profit = receitas.get(week_num, Decimal(0)) - despesas.get(week_num, Decimal(0))
        weeks.append(
            WeeklyOperationalSummary(
                week_number=week_num,
                week_start=week_start,
                repairs_count=repairs.get(week_num, 0),
                drillings_count=drillings.get(week_num, 0),
                drilling_meters=meters.get(week_num, Decimal(0)),
                profit=profit,
            )
        )

    return YearlyOperationalDashboard(ano=ano, weeks=weeks)

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    VALID_STATUS_TRANSITIONS,
    BaixarEstoqueResponse,
    CategoriaTransacao,
    CategoryDashboardItem,
    Client,
    ClientCreate,
    ClientRef,
    ClientUpdate,
    DeductionItem,
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
    get_datetime_utc,
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
    count = session.exec(select(func.count()).select_from(Service)).one()
    statement = (
        select(Service)
        .options(
            selectinload(Service.client),  # type: ignore[arg-type]
            selectinload(Service.items),  # type: ignore[arg-type]
            selectinload(Service.status_logs).selectinload(  # type: ignore[arg-type]
                ServiceStatusLog.changed_by_user  # type: ignore[arg-type]
            ),
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
    assert result is not None
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
    """
    warnings: list[StockWarning] = []
    material_items = [i for i in service.items if i.item_type == ItemType.material]

    for service_item in material_items:
        needed = Decimal(str(service_item.quantity))
        candidates = session.exec(
            select(ProductItem)
            .where(ProductItem.status == ProductItemStatus.em_estoque)
            .order_by(ProductItem.created_at)  # type: ignore[arg-type]
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

    # Handle stock reservation when moving to scheduled
    if to_status == ServiceStatus.scheduled:
        stock_warnings = _check_stock_for_service(session, service)

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
) -> list[dict]:  # type: ignore[type-arg]
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

    result = []
    for item in reserved_items:
        item.status = ProductItemStatus.utilizado
        item.updated_at = get_datetime_utc()
        session.add(item)
        result.append(
            {"product_item_id": str(item.id), "quantity": float(item.quantity)}
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
    from fastapi import HTTPException

    if transacao_in.service_id is not None:
        if session.get(Service, transacao_in.service_id) is None:
            raise HTTPException(status_code=404, detail="Service not found")
    if transacao_in.client_id is not None:
        if session.get(Client, transacao_in.client_id) is None:
            raise HTTPException(status_code=404, detail="Client not found")

    db_transacao = Transacao.model_validate(transacao_in)
    session.add(db_transacao)
    session.commit()
    result = _get_transacao_with_relations(session, db_transacao.id)
    assert result is not None
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
    from fastapi import HTTPException

    update_data = transacao_in.model_dump(exclude_unset=True)

    if "service_id" in update_data and update_data["service_id"] is not None:
        if session.get(Service, update_data["service_id"]) is None:
            raise HTTPException(status_code=404, detail="Service not found")

    # validate categoria/tipo compatibility if categoria is being changed
    if "categoria" in update_data and update_data["categoria"] is not None:
        from app.models import EXPENSE_CATEGORIES, INCOME_CATEGORIES

        new_cat = update_data["categoria"]
        if (
            db_transacao.tipo == TipoTransacao.receita
            and new_cat not in INCOME_CATEGORIES
        ):
            raise HTTPException(
                status_code=422,
                detail=f"categoria '{new_cat}' is not valid for tipo='receita'",
            )
        if (
            db_transacao.tipo == TipoTransacao.despesa
            and new_cat not in EXPENSE_CATEGORIES
        ):
            raise HTTPException(
                status_code=422,
                detail=f"categoria '{new_cat}' is not valid for tipo='despesa'",
            )

    db_transacao.sqlmodel_update(update_data)
    db_transacao.updated_at = datetime.now(timezone.utc)
    session.add(db_transacao)
    session.commit()
    result = _get_transacao_with_relations(session, db_transacao.id)
    assert result is not None
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
    from fastapi import HTTPException

    if session.get(ProductType, product_in.product_type_id) is None:
        raise HTTPException(status_code=404, detail="ProductType not found")
    if product_in.fornecedor_id is not None:
        if session.get(Fornecedor, product_in.fornecedor_id) is None:
            raise HTTPException(status_code=404, detail="Fornecedor not found")
    product = Product.model_validate(product_in)
    session.add(product)
    session.commit()
    result = get_product(session=session, product_id=product.id)
    assert result is not None
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
    from fastapi import HTTPException

    update_data = product_in.model_dump(exclude_unset=True)
    if "product_type_id" in update_data and update_data["product_type_id"] is not None:
        if session.get(ProductType, update_data["product_type_id"]) is None:
            raise HTTPException(status_code=404, detail="ProductType not found")
    if "fornecedor_id" in update_data and update_data["fornecedor_id"] is not None:
        if session.get(Fornecedor, update_data["fornecedor_id"]) is None:
            raise HTTPException(status_code=404, detail="Fornecedor not found")
    product.sqlmodel_update(update_data)
    product.updated_at = get_datetime_utc()
    session.add(product)
    session.commit()
    result = get_product(session=session, product_id=product.id)
    assert result is not None
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
    from fastapi import HTTPException

    if session.get(Product, item_in.product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")
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
            ProductItem.created_at >= window_start,  # type: ignore[operator]
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

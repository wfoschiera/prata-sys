import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    CategoriaTransacao,
    Client,
    ClientCreate,
    ClientRef,
    ClientUpdate,
    ResumoMensal,
    Service,
    ServiceCreate,
    ServiceItem,
    ServiceItemCreate,
    ServiceSummary,
    ServiceUpdate,
    TipoTransacao,
    Transacao,
    TransacaoCreate,
    TransacaoPublic,
    TransacaoUpdate,
    User,
    UserCreate,
    UserPermission,
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
            msg = f"Invalid status transition from '{db_service.status}' to '{new_status}'"
            raise ValueError(msg)
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

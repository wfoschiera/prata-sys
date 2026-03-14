"""Tests for /api/v1/transacoes endpoints and CRUD."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.core.permissions import get_role_defaults
from app.models import (
    CategoriaTransacao,
    Client,
    ClientCreate,
    DocumentType,
    Service,
    ServiceCreate,
    ServiceType,
    TipoTransacao,
    Transacao,
    TransacaoCreate,
    UserCreate,
    UserRole,
)
from tests.utils.utils import random_lower_string

API_PREFIX = settings.API_V1_STR


# ── Helpers ───────────────────────────────────────────────────────────────────


def _create_finance_user_headers(client: TestClient, db: Session) -> dict[str, str]:
    from tests.utils.user import user_authentication_headers

    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.finance)
    crud.create_user(session=db, user_create=user_in)
    return user_authentication_headers(client=client, email=email, password=password)


def _create_client(db: Session) -> Client:
    client_in = ClientCreate(
        name="Test Cliente",
        document_type=DocumentType("cpf"),
        document_number="12345678901",
    )
    c = Client.model_validate(client_in)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _create_service(db: Session, client_id: uuid.UUID) -> Service:
    service_in = ServiceCreate(
        type=ServiceType.perfuracao,
        execution_address="Rua Teste 1",
        client_id=client_id,
    )
    s = Service.model_validate(service_in)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _make_receita(service_id: uuid.UUID | None = None) -> dict[str, object]:
    return {
        "tipo": "receita",
        "categoria": "SERVICO",
        "valor": 1500.00,
        "data_competencia": str(date.today()),
        "service_id": str(service_id) if service_id else None,
    }


def _make_despesa() -> dict[str, object]:
    return {
        "tipo": "despesa",
        "categoria": "COMBUSTIVEL",
        "valor": 250.00,
        "data_competencia": str(date.today()),
        "descricao": "Abastecimento caminhão",
        "nome_contraparte": "Posto Shell",
    }


# ── Unit: permissions ─────────────────────────────────────────────────────────


def test_finance_role_has_manage_financeiro() -> None:
    defaults = get_role_defaults(UserRole.finance)
    assert "manage_financeiro" in defaults
    assert "view_financeiro" in defaults
    assert "view_contas_pagar" in defaults
    assert "view_contas_receber" in defaults


def test_admin_role_has_view_financeiro() -> None:
    defaults = get_role_defaults(UserRole.admin)
    assert "view_financeiro" in defaults
    assert "manage_financeiro" not in defaults


def test_client_role_has_no_finance_permissions() -> None:
    defaults = get_role_defaults(UserRole.client)
    assert "manage_financeiro" not in defaults
    assert "view_financeiro" not in defaults


# ── Unit: CRUD ─────────────────────────────────────────────────────────────────


def test_create_receita_crud(db: Session) -> None:
    t = TransacaoCreate(
        tipo=TipoTransacao.receita,
        categoria=CategoriaTransacao.SERVICO,
        valor=Decimal("1000.00"),
        data_competencia=date.today(),
    )
    result = crud.create_transacao(session=db, transacao_in=t)
    assert result.id is not None
    assert result.tipo == TipoTransacao.receita
    assert result.valor == 1000.00


def test_create_despesa_crud(db: Session) -> None:
    t = TransacaoCreate(
        tipo=TipoTransacao.despesa,
        categoria=CategoriaTransacao.COMBUSTIVEL,
        valor=Decimal("100"),
        data_competencia=date.today(),
        nome_contraparte="Posto X",
    )
    result = crud.create_transacao(session=db, transacao_in=t)
    assert result.tipo == TipoTransacao.despesa
    assert result.nome_contraparte == "Posto X"


def test_create_receita_invalid_categoria_raises() -> None:
    with pytest.raises(ValueError, match="not valid for tipo='receita'"):
        TransacaoCreate(
            tipo=TipoTransacao.receita,
            categoria=CategoriaTransacao.COMBUSTIVEL,
            valor=Decimal("100"),
            data_competencia=date.today(),
        )


def test_create_despesa_invalid_categoria_raises() -> None:
    with pytest.raises(ValueError, match="not valid for tipo='despesa'"):
        TransacaoCreate(
            tipo=TipoTransacao.despesa,
            categoria=CategoriaTransacao.SERVICO,
            valor=Decimal("100"),
            data_competencia=date.today(),
        )


def test_create_valor_zero_raises() -> None:
    with pytest.raises(ValueError, match="valor must be greater than zero"):
        TransacaoCreate(
            tipo=TipoTransacao.receita,
            categoria=CategoriaTransacao.SERVICO,
            valor=Decimal("0"),
            data_competencia=date.today(),
        )


def test_create_despesa_with_client_id_raises() -> None:
    with pytest.raises(
        ValueError, match="client_id may only be set when tipo='receita'"
    ):
        TransacaoCreate(
            tipo=TipoTransacao.despesa,
            categoria=CategoriaTransacao.COMBUSTIVEL,
            valor=Decimal("100"),
            data_competencia=date.today(),
            client_id=uuid.uuid4(),
        )


def test_get_transacoes_filter_by_tipo(db: Session) -> None:
    TransacaoCreate(
        tipo=TipoTransacao.receita,
        categoria=CategoriaTransacao.RENDIMENTO,
        valor=Decimal("200"),
        data_competencia=date.today(),
    )
    results, _ = crud.get_transacoes(session=db, tipo=TipoTransacao.despesa)
    for t in results:
        assert t.tipo == TipoTransacao.despesa


def test_resumo_mensal_no_data(db: Session) -> None:
    resumo = crud.get_resumo_mensal(session=db, ano=1999, mes=1)
    assert resumo.total_receitas == 0
    assert resumo.total_despesas == 0
    assert resumo.resultado_liquido == 0
    assert resumo.ano == 1999
    assert resumo.mes == 1


def test_resumo_mensal_with_data(db: Session) -> None:
    target_year = 2020
    target_month = 6
    target_date = date(target_year, target_month, 15)
    r = Transacao(
        tipo=TipoTransacao.receita,
        categoria=CategoriaTransacao.SERVICO,
        valor=Decimal("5000"),
        data_competencia=target_date,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    d = Transacao(
        tipo=TipoTransacao.despesa,
        categoria=CategoriaTransacao.COMBUSTIVEL,
        valor=Decimal("1000"),
        data_competencia=target_date,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(r)
    db.add(d)
    db.commit()

    resumo = crud.get_resumo_mensal(session=db, ano=target_year, mes=target_month)
    assert resumo.total_receitas >= 5000
    assert resumo.total_despesas >= 1000
    assert resumo.resultado_liquido == resumo.total_receitas - resumo.total_despesas


# ── API route tests ────────────────────────────────────────────────────────────


def test_create_transacao_finance_user(client: TestClient, db: Session) -> None:
    headers = _create_finance_user_headers(client, db)
    payload = _make_despesa()
    r = client.post(f"{API_PREFIX}/transacoes/", json=payload, headers=headers)
    assert r.status_code == HTTPStatus.CREATED
    data = r.json()
    assert data["tipo"] == "despesa"
    assert data["categoria"] == "COMBUSTIVEL"


def test_create_transacao_unauthorized(client: TestClient, db: Session) -> None:
    """Admin-role users have view_financeiro but NOT manage_financeiro."""

    # Create a non-superuser admin-role user
    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    from tests.utils.user import user_authentication_headers

    user_in = UserCreate(email=email, password=password, role=UserRole.admin)
    crud.create_user(session=db, user_create=user_in)
    headers = user_authentication_headers(client=client, email=email, password=password)
    r = client.post(f"{API_PREFIX}/transacoes/", json=_make_despesa(), headers=headers)
    assert r.status_code == HTTPStatus.FORBIDDEN


def test_create_transacao_invalid_tipo_categoria(
    client: TestClient, db: Session
) -> None:
    headers = _create_finance_user_headers(client, db)
    payload = {
        "tipo": "despesa",
        "categoria": "SERVICO",
        "valor": 100,
        "data_competencia": str(date.today()),
    }
    r = client.post(f"{API_PREFIX}/transacoes/", json=payload, headers=headers)
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_transacao_zero_valor(client: TestClient, db: Session) -> None:
    headers = _create_finance_user_headers(client, db)
    payload = {
        "tipo": "despesa",
        "categoria": "COMBUSTIVEL",
        "valor": 0,
        "data_competencia": str(date.today()),
    }
    r = client.post(f"{API_PREFIX}/transacoes/", json=payload, headers=headers)
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_list_transacoes(client: TestClient, db: Session) -> None:
    headers = _create_finance_user_headers(client, db)
    r = client.get(f"{API_PREFIX}/transacoes/", headers=headers)
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "data" in data
    assert "count" in data


def test_list_transacoes_filter_tipo(client: TestClient, db: Session) -> None:
    headers = _create_finance_user_headers(client, db)
    r = client.get(f"{API_PREFIX}/transacoes/?tipo=despesa", headers=headers)
    assert r.status_code == HTTPStatus.OK
    for t in r.json()["data"]:
        assert t["tipo"] == "despesa"


def test_get_single_transacao(client: TestClient, db: Session) -> None:
    headers = _create_finance_user_headers(client, db)
    # Create one
    r = client.post(f"{API_PREFIX}/transacoes/", json=_make_despesa(), headers=headers)
    assert r.status_code == 201
    tid = r.json()["id"]
    r2 = client.get(f"{API_PREFIX}/transacoes/{tid}", headers=headers)
    assert r2.status_code == HTTPStatus.OK
    assert r2.json()["id"] == tid


def test_get_transacao_not_found(client: TestClient, db: Session) -> None:
    headers = _create_finance_user_headers(client, db)
    r = client.get(f"{API_PREFIX}/transacoes/{uuid.uuid4()}", headers=headers)
    assert r.status_code == HTTPStatus.NOT_FOUND


def test_update_transacao(client: TestClient, db: Session) -> None:
    headers = _create_finance_user_headers(client, db)
    r = client.post(f"{API_PREFIX}/transacoes/", json=_make_despesa(), headers=headers)
    tid = r.json()["id"]
    r2 = client.patch(
        f"{API_PREFIX}/transacoes/{tid}", json={"valor": 999.99}, headers=headers
    )
    assert r2.status_code == 200
    assert float(r2.json()["valor"]) == pytest.approx(999.99)


def test_delete_transacao(client: TestClient, db: Session) -> None:
    headers = _create_finance_user_headers(client, db)
    r = client.post(f"{API_PREFIX}/transacoes/", json=_make_despesa(), headers=headers)
    tid = r.json()["id"]
    r2 = client.delete(f"{API_PREFIX}/transacoes/{tid}", headers=headers)
    assert r2.status_code == 204
    r3 = client.get(f"{API_PREFIX}/transacoes/{tid}", headers=headers)
    assert r3.status_code == HTTPStatus.NOT_FOUND


def test_resumo_endpoint(client: TestClient, db: Session) -> None:
    headers = _create_finance_user_headers(client, db)
    r = client.get(f"{API_PREFIX}/transacoes/resumo", headers=headers)
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "total_receitas" in data
    assert "total_despesas" in data
    assert "resultado_liquido" in data


def test_client_role_cannot_view_transacoes(client: TestClient, db: Session) -> None:
    from tests.utils.user import user_authentication_headers

    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.client)
    crud.create_user(session=db, user_create=user_in)
    headers = user_authentication_headers(client=client, email=email, password=password)
    r = client.get(f"{API_PREFIX}/transacoes/", headers=headers)
    assert r.status_code == HTTPStatus.FORBIDDEN

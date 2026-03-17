import uuid
from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import (
    FornecedorCategoryEnum,
)
from tests.utils.utils import random_lower_string

PREFIX = f"{settings.API_V1_STR}/fornecedores"

# ── Helpers ───────────────────────────────────────────────────────────────────


def _valid_cnpj() -> str:
    """Return a valid, unique numeric CNPJ using the Modulo 11 algorithm."""
    import random

    def calc_dv(digits: list[int], weights: list[int]) -> int:
        remainder = sum(d * w for d, w in zip(digits, weights, strict=False)) % 11
        return 0 if remainder < 2 else 11 - remainder

    while True:
        root = [random.randint(0, 9) for _ in range(8)]
        base = root + [0, 0, 0, 1]
        if len(set(base)) == 1:
            continue
        dv1 = calc_dv(base, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        dv2 = calc_dv(base + [dv1], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        return "".join(str(d) for d in base + [dv1, dv2])


def _create_fornecedor(
    client: TestClient,
    headers: dict[str, str],
    company_name: str | None = None,
    cnpj: str | None = None,
    categories: list[str] | None = None,
) -> dict[str, object]:
    body: dict[str, object] = {"company_name": company_name or random_lower_string()}
    if cnpj is not None:
        body["cnpj"] = cnpj
    if categories is not None:
        body["categories"] = categories
    resp = client.post(PREFIX, json=body, headers=headers)
    assert resp.status_code == HTTPStatus.CREATED, resp.text
    return resp.json()  # type: ignore[no-any-return]


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_create_fornecedor(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = _create_fornecedor(client, superuser_token_headers)
    assert "id" in data
    assert data["contatos"] == []
    assert data["categories"] == []


def test_create_fornecedor_with_categories(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    cats = [FornecedorCategoryEnum.tubos.value, FornecedorCategoryEnum.bombas.value]
    data = _create_fornecedor(client, superuser_token_headers, categories=cats)
    assert set(data["categories"]) == set(cats)  # type: ignore[call-overload]

    # GET returns them too
    resp = client.get(f"{PREFIX}/{data['id']}", headers=superuser_token_headers)
    assert resp.status_code == HTTPStatus.OK
    assert set(resp.json()["categories"]) == set(cats)


def test_create_fornecedor_duplicate_cnpj(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    cnpj = _valid_cnpj()
    _create_fornecedor(client, superuser_token_headers, cnpj=cnpj)
    resp = client.post(
        PREFIX,
        json={"company_name": random_lower_string(), "cnpj": cnpj},
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CONFLICT


def test_create_fornecedor_invalid_cnpj(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # 13 digits — too short
    resp = client.post(
        PREFIX,
        json={"company_name": random_lower_string(), "cnpj": "1234567890123"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # Wrong check digits
    resp = client.post(
        PREFIX,
        json={"company_name": random_lower_string(), "cnpj": "11222333000199"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_fornecedor_no_cnpj(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = _create_fornecedor(client, superuser_token_headers)
    assert data["cnpj"] is None


def test_get_fornecedores_search(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    unique = f"ZZ{uuid.uuid4().hex[:6]}"
    _create_fornecedor(
        client, superuser_token_headers, company_name=f"{unique} Empresa A"
    )
    _create_fornecedor(client, superuser_token_headers, company_name="Unrelated Corp")

    resp = client.get(f"{PREFIX}?search={unique}", headers=superuser_token_headers)
    assert resp.status_code == HTTPStatus.OK
    names = [f["company_name"] for f in resp.json()]
    assert all(unique in n for n in names)
    assert len(names) >= 1


def test_get_fornecedores_category_filter(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    unique = f"CAT{uuid.uuid4().hex[:6]}"
    _create_fornecedor(
        client,
        superuser_token_headers,
        company_name=f"{unique} Tubos",
        categories=["tubos"],
    )
    _create_fornecedor(
        client,
        superuser_token_headers,
        company_name=f"{unique} Other",
        categories=["cabos"],
    )

    resp = client.get(
        f"{PREFIX}?category=tubos&search={unique}", headers=superuser_token_headers
    )
    assert resp.status_code == HTTPStatus.OK
    results = resp.json()
    assert len(results) == 1
    assert "tubos" in results[0]["categories"]


def test_update_fornecedor_replaces_categories(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = _create_fornecedor(
        client, superuser_token_headers, categories=["tubos", "bombas"]
    )
    fid = data["id"]

    resp = client.patch(
        f"{PREFIX}/{fid}",
        json={"categories": ["cabos"]},
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["categories"] == ["cabos"]


def test_update_fornecedor_no_categories_field(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = _create_fornecedor(client, superuser_token_headers, categories=["tubos"])
    fid = data["id"]

    resp = client.patch(
        f"{PREFIX}/{fid}",
        json={"address": "Rua A, 123"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.OK
    # categories unchanged
    assert resp.json()["categories"] == ["tubos"]


def test_delete_fornecedor_cascades(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = _create_fornecedor(client, superuser_token_headers, categories=["outros"])
    fid = data["id"]
    # add contato
    client.post(
        f"{PREFIX}/{fid}/contatos",
        json={"name": "João", "telefone": "11999999999", "description": "Vendas"},
        headers=superuser_token_headers,
    )

    resp = client.delete(f"{PREFIX}/{fid}", headers=superuser_token_headers)
    assert resp.status_code == HTTPStatus.NO_CONTENT

    resp = client.get(f"{PREFIX}/{fid}", headers=superuser_token_headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_create_contato(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = _create_fornecedor(client, superuser_token_headers)
    fid = data["id"]

    resp = client.post(
        f"{PREFIX}/{fid}/contatos",
        json={"name": "Maria", "telefone": "11988887777", "description": "Compras"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CREATED
    assert resp.json()["name"] == "Maria"

    detail = client.get(f"{PREFIX}/{fid}", headers=superuser_token_headers).json()
    assert len(detail["contatos"]) == 1


def test_update_contato(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = _create_fornecedor(client, superuser_token_headers)
    fid = data["id"]

    contato = client.post(
        f"{PREFIX}/{fid}/contatos",
        json={"name": "Pedro", "telefone": "11977776666", "description": "TI"},
        headers=superuser_token_headers,
    ).json()
    cid = contato["id"]

    resp = client.patch(
        f"{PREFIX}/{fid}/contatos/{cid}",
        json={"telefone": "11900001111"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["telefone"] == "11900001111"
    assert resp.json()["name"] == "Pedro"


def test_delete_contato(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = _create_fornecedor(client, superuser_token_headers)
    fid = data["id"]

    contato = client.post(
        f"{PREFIX}/{fid}/contatos",
        json={"name": "Ana", "telefone": "11966665555", "description": "RH"},
        headers=superuser_token_headers,
    ).json()
    cid = contato["id"]

    resp = client.delete(
        f"{PREFIX}/{fid}/contatos/{cid}", headers=superuser_token_headers
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT

    detail = client.get(f"{PREFIX}/{fid}", headers=superuser_token_headers).json()
    assert len(detail["contatos"]) == 0


def test_contato_wrong_fornecedor(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    f1 = _create_fornecedor(client, superuser_token_headers)
    f2 = _create_fornecedor(client, superuser_token_headers)

    contato = client.post(
        f"{PREFIX}/{f1['id']}/contatos",
        json={"name": "X", "telefone": "11955554444", "description": "Test"},
        headers=superuser_token_headers,
    ).json()
    cid = contato["id"]

    # Try to update/delete using wrong fornecedor
    resp = client.patch(
        f"{PREFIX}/{f2['id']}/contatos/{cid}",
        json={"name": "Y"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND

    resp = client.delete(
        f"{PREFIX}/{f2['id']}/contatos/{cid}", headers=superuser_token_headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_finance_can_read(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    finance_token_headers: dict[str, str],
) -> None:
    resp = client.get(PREFIX, headers=finance_token_headers)
    assert resp.status_code == HTTPStatus.OK

    data = _create_fornecedor(client, superuser_token_headers)
    resp = client.get(f"{PREFIX}/{data['id']}", headers=finance_token_headers)
    assert resp.status_code == HTTPStatus.OK


def test_finance_cannot_write(
    client: TestClient, finance_token_headers: dict[str, str]
) -> None:
    resp = client.post(
        PREFIX,
        json={"company_name": random_lower_string()},
        headers=finance_token_headers,
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_client_cannot_read(
    client: TestClient, client_token_headers: dict[str, str]
) -> None:
    resp = client.get(PREFIX, headers=client_token_headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_admin_full_access(
    client: TestClient, admin_token_headers: dict[str, str]
) -> None:
    # list
    resp = client.get(PREFIX, headers=admin_token_headers)
    assert resp.status_code == HTTPStatus.OK

    # create
    data = _create_fornecedor(client, admin_token_headers)
    fid = data["id"]

    # update
    resp = client.patch(
        f"{PREFIX}/{fid}",
        json={"address": "Av. Brasil, 100"},
        headers=admin_token_headers,
    )
    assert resp.status_code == HTTPStatus.OK

    # delete
    resp = client.delete(f"{PREFIX}/{fid}", headers=admin_token_headers)
    assert resp.status_code == HTTPStatus.NO_CONTENT


def test_superuser_bypass(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Superuser with role=client bypasses permission checks."""
    resp = client.get(PREFIX, headers=superuser_token_headers)
    assert resp.status_code == HTTPStatus.OK

    data = _create_fornecedor(client, superuser_token_headers)
    fid = data["id"]
    resp = client.delete(f"{PREFIX}/{fid}", headers=superuser_token_headers)
    assert resp.status_code == HTTPStatus.NO_CONTENT


def test_no_n_plus_one(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    """List query must not trigger N+1: statement count should stay low."""
    from sqlalchemy import event

    # Create 5 fornecedores each with 2 contacts and 2 categories
    for _ in range(5):
        data = _create_fornecedor(
            client, superuser_token_headers, categories=["tubos", "cabos"]
        )
        fid = data["id"]
        for _ in range(2):
            client.post(
                f"{PREFIX}/{fid}/contatos",
                json={
                    "name": random_lower_string(),
                    "telefone": "11900000000",
                    "description": "x",
                },
                headers=superuser_token_headers,
            )

    # Count SQL statements issued during the list request
    statement_count = 0
    engine = db.get_bind()

    def before_cursor_execute(*_args: object) -> None:  # noqa: ARG001
        nonlocal statement_count
        statement_count += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        resp = client.get(PREFIX, headers=superuser_token_headers)
        assert resp.status_code == HTTPStatus.OK
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)

    # With selectinload, we expect: 1 auth query + ~3 data queries (fornecedores, contatos, categorias)
    # Generous upper bound: ≤ 10 total
    assert statement_count <= 10, f"Too many SQL statements: {statement_count}"

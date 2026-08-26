"""Tests for the NF-e XML import (parse-preview-submit) endpoint.

The parser is exercised as a pure unit; the route tests cover the preview
contract: nothing persisted, totals mapped to typed adjustments, suggestive
matching, duplicate rejection, and the permission matrix.
"""

from decimal import Decimal
from http import HTTPStatus
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import EntradaEstoque, ProductItem
from app.nfe import NfeParseError, parse_nfe_xml
from tests.factories import FornecedorFactory, ProductFactory

PREFIX = f"{settings.API_V1_STR}/entradas-estoque"
FIXTURES = Path(__file__).parents[2] / "fixtures" / "nfe"

CHAVE = "12345678901234567890123456789012345678901234"
CNPJ_DIGITS = "12345678000195"


def _fixture(name: str, **subs: str) -> bytes:
    content = (FIXTURES / name).read_text(encoding="utf-8")
    for key, value in subs.items():
        content = content.replace("{{" + key + "}}", value)
    return content.encode("utf-8")


def _upload(
    client: TestClient,
    data: bytes,
    headers: dict[str, str],
) -> object:
    return client.post(
        f"{PREFIX}/importar-xml",
        files={"file": ("nfe.xml", data, "text/xml")},
        headers=headers,
    )


# ── Parser (pure unit) ────────────────────────────────────────────────────────


def test_parser_extracts_envelope_fields() -> None:
    parsed = parse_nfe_xml(_fixture("nfe_envelope.xml", CHAVE=CHAVE, CNPJ=CNPJ_DIGITS, NNF="123"))
    assert parsed.chave == CHAVE
    assert parsed.numero == "123"
    assert parsed.emission_date.isoformat() == "2026-08-20"
    assert parsed.emitter_cnpj_digits == CNPJ_DIGITS
    assert len(parsed.items) == 2
    first = parsed.items[0]
    assert first.quantity == Decimal("10.0000")
    assert first.unit_price == Decimal("100.0000")
    assert first.unit == "UN"
    assert first.cfop == "5102"
    assert parsed.totals.freight == Decimal("200.00")
    assert parsed.totals.icms_st == Decimal("50.00")
    assert parsed.totals.discount == Decimal("100.00")
    assert parsed.totals.invoice_total == Decimal("2150.00")


def test_parser_handles_bare_nfe_and_demi_fallback() -> None:
    parsed = parse_nfe_xml(_fixture("nfe_bare.xml", CHAVE=CHAVE, CNPJ=CNPJ_DIGITS, NNF="777"))
    # No protNFe in the envelope: chave comes from infNFe/@Id.
    assert parsed.chave == CHAVE
    # dEmi fallback when dhEmi is absent.
    assert parsed.emission_date.isoformat() == "2026-07-15"


def test_parser_rejects_non_55_model() -> None:
    try:
        parse_nfe_xml(_fixture("nfce_mod65.xml", CHAVE=CHAVE, CNPJ=CNPJ_DIGITS, NNF="1"))
    except NfeParseError as exc:
        assert "55" in str(exc)
    else:
        msg = "expected NfeParseError for modelo 65"
        raise AssertionError(msg)


def test_parser_rejects_malformed_and_missing_chave() -> None:
    for data in [b"not xml at all", b"<html/>"]:
        try:
            parse_nfe_xml(data)
        except NfeParseError:
            pass
        else:
            msg = "expected NfeParseError"
            raise AssertionError(msg)


# ── Route ─────────────────────────────────────────────────────────────────────


def test_import_preview_returns_full_suggestion(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    fornecedor = FornecedorFactory(cnpj=CNPJ_DIGITS)
    ProductFactory(fornecedor=fornecedor, name="Tubo PVC 100mm 6m")

    resp = _upload(
        client,
        _fixture("nfe_envelope.xml", CHAVE=CHAVE, CNPJ=CNPJ_DIGITS, NNF="123"),
        superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.OK  # type: ignore[attr-defined]
    data = resp.json()  # type: ignore[attr-defined]

    assert data["chave"] == CHAVE
    assert data["numero_nota"] == "123"
    assert data["data_entrada"] == "2026-08-20"
    assert data["fornecedor_sugerido"]["id"] == str(fornecedor.id)

    by_desc = {i["description"]: i for i in data["itens"]}
    matched = by_desc["Tubo PVC 100mm 6m"]
    assert matched["match_status"] == "sugerido"
    unmatched = by_desc["Bomba Submersa 1CV"]
    assert unmatched["match_status"] == "sem_match"
    assert unmatched["product_sugerido_id"] is None

    ajustes = {(a["tipo"], a["valor"]) for a in data["ajustes_sugeridos"]}
    assert ("frete", "200.00") in ajustes
    assert ("icms_st", "50.00") in ajustes
    assert ("desconto_comercial", "-100.00") in ajustes
    assert all(a["documento_referencia"] == CHAVE for a in data["ajustes_sugeridos"])
    assert all(("seguro" != t and "ipi" != t) for (t, _v) in ajustes)


def test_import_preview_creates_no_records(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    resp = _upload(
        client,
        _fixture("nfe_envelope.xml", CHAVE=CHAVE, CNPJ=CNPJ_DIGITS, NNF="123"),
        superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.OK  # type: ignore[attr-defined]
    entradas = db.exec(select(EntradaEstoque)).all()
    lots = db.exec(select(ProductItem)).all()
    assert not entradas
    assert not lots


def test_import_matching_prefers_supplier_scope_and_flags_ambiguity(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    fornecedor = FornecedorFactory(cnpj=CNPJ_DIGITS)
    other = FornecedorFactory()
    # Exists only outside supplier scope: global fallback must find it.
    ProductFactory(fornecedor=other, name="Bomba Submersa 1CV")
    # Two same-named products inside supplier scope -> ambiguous.
    ProductFactory(fornecedor=fornecedor, name="Tubo PVC 100mm 6m")
    ProductFactory(fornecedor=fornecedor, name="Tubo PVC 100mm 6m")

    resp = _upload(
        client,
        _fixture("nfe_envelope.xml", CHAVE=CHAVE, CNPJ=CNPJ_DIGITS, NNF="123"),
        superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.OK  # type: ignore[attr-defined]
    by_desc = {i["description"]: i for i in resp.json()["itens"]}  # type: ignore[attr-defined]
    assert by_desc["Bomba Submersa 1CV"]["match_status"] == "sugerido"
    assert by_desc["Tubo PVC 100mm 6m"]["match_status"] == "ambiguo"


def test_import_unknown_cnpj_yields_null_supplier_suggestion(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    resp = _upload(
        client,
        _fixture("nfe_envelope.xml", CHAVE=CHAVE, CNPJ="99999999000199", NNF="123"),
        superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.OK  # type: ignore[attr-defined]
    assert resp.json()["fornecedor_sugerido"] is None  # type: ignore[attr-defined]


def test_reimporting_same_chave_returns_conflict(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    # Seed the existing entrada directly (the create endpoint is phase-11 surface).
    db.add(
        EntradaEstoque(data_entrada="2026-08-01", numero_documento=CHAVE)
    )
    db.commit()

    resp = _upload(
        client,
        _fixture("nfe_envelope.xml", CHAVE=CHAVE, CNPJ=CNPJ_DIGITS, NNF="123"),
        superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.CONFLICT  # type: ignore[attr-defined]
    detail = resp.json()["detail"]  # type: ignore[attr-defined]
    assert detail["existing_entrada_id"]


def test_manual_short_document_numbers_are_not_blocked_by_dedupe(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    db.add(EntradaEstoque(data_entrada="2026-08-01", numero_documento="NF 123"))
    db.commit()
    entrada = EntradaEstoque(data_entrada="2026-08-02", numero_documento="NF 123")
    db.add(entrada)
    db.commit()
    assert entrada.id is not None


def test_import_rejects_mod65_malformed_and_oversize(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    resp = _upload(
        client,
        _fixture("nfce_mod65.xml", CHAVE=CHAVE, CNPJ=CNPJ_DIGITS, NNF="1"),
        superuser_token_headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY  # type: ignore[attr-defined]

    resp = _upload(client, b"not xml", superuser_token_headers)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY  # type: ignore[attr-defined]

    big = b"<a>" + b"x" * (512 * 1024 + 1) + b"</a>"
    resp = _upload(client, big, superuser_token_headers)
    assert resp.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE  # type: ignore[attr-defined]


def test_import_requires_manage_estoque(
    client: TestClient, client_token_headers: dict[str, str]
) -> None:
    resp = _upload(
        client,
        _fixture("nfe_envelope.xml", CHAVE=CHAVE, CNPJ=CNPJ_DIGITS, NNF="123"),
        client_token_headers,
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN  # type: ignore[attr-defined]


def test_partial_unique_index_blocks_duplicate_chave_at_db_level(db: Session) -> None:
    """Route bypass scenario: writes of duplicate chaves hit the index."""
    import sqlalchemy.exc

    db.add(EntradaEstoque(data_entrada="2026-08-01", numero_documento=CHAVE))
    db.commit()
    db.add(EntradaEstoque(data_entrada="2026-08-02", numero_documento=CHAVE))
    try:
        db.commit()
    except sqlalchemy.exc.IntegrityError:
        db.rollback()
    else:
        msg = "partial unique index did not fire for duplicate chave"
        raise AssertionError(msg)

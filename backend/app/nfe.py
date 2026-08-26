"""NF-e (modelo 55) XML parsing for stock entry import.

Parses the subset of the NF-e XML layout this system needs: document
identification, emitter, line items, and the totals block. Uses stdlib
ElementTree only — it does not resolve external entities, which closes
the XXE class without adding a dependency.

The parser produces plain data; it never touches the database. Matching
against catalog records happens in crud.py.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

NFE_NAMESPACE = "http://www.portalfiscal.inf.br/nfe"

# NF-e financial/quantity fields are dot-decimal strings ("1234.56").
_DECIMAL_RE = re.compile(r"^-?\d+(\.\d+)?$")
_CHAVE_RE = re.compile(r"^\d{44}$")


class NfeParseError(ValueError):
    """Raised when an uploaded file is not a parseable NF-e modelo 55."""


@dataclass(frozen=True)
class ParsedNfeItem:
    description: str
    product_code: str | None
    quantity: Decimal
    unit_price: Decimal
    unit: str | None
    cfop: str | None
    total: Decimal | None


@dataclass(frozen=True)
class ParsedNfeTotals:
    products: Decimal | None = None
    freight: Decimal | None = None
    insurance: Decimal | None = None
    icms_st: Decimal | None = None
    ipi: Decimal | None = None
    discount: Decimal | None = None
    invoice_total: Decimal | None = None


@dataclass(frozen=True)
class ParsedNfe:
    chave: str
    numero: str | None
    emission_date: date | None
    emitter_cnpj_digits: str | None
    items: list[ParsedNfeItem] = field(default_factory=list)
    totals: ParsedNfeTotals = field(default_factory=ParsedNfeTotals)


def _ns(tag: str) -> str:
    return f"{{{NFE_NAMESPACE}}}{tag}"


def _parse_decimal(raw: str | None) -> Decimal | None:
    if raw is None:
        return None
    value = raw.strip()
    if not _DECIMAL_RE.match(value):
        return None
    return Decimal(value)


def _digits(raw: str | None) -> str | None:
    if raw is None:
        return None
    digits = re.sub(r"\D", "", raw)
    return digits or None


def _find_text(parent: ET.Element, path: str) -> str | None:
    node = parent.find(path)
    if node is None or node.text is None:
        return None
    text = node.text.strip()
    return text or None


def _extract_chave(root: ET.Element) -> str:
    prot = root.find(f".//{_ns('protNFe')}/{_ns('infProt')}")
    if prot is not None:
        chave = _find_text(prot, _ns("chNFe"))
        if chave and _CHAVE_RE.match(chave):
            return chave
    inf_nfe = root.find(f".//{_ns('infNFe')}")
    if inf_nfe is not None:
        raw_id = inf_nfe.get("Id", "").strip()
        # Id looks like "NFe<44 digits>".
        candidate = raw_id[3:] if raw_id.upper().startswith("NFE") else raw_id
        if _CHAVE_RE.match(candidate):
            return candidate
    msg = "Chave de acesso da NF-e não encontrada no XML."
    raise NfeParseError(msg)


def _extract_emission_date(inf_nfe: ET.Element) -> date | None:
    raw = _find_text(inf_nfe, f"{_ns('ide')}/{_ns('dhEmi')}")
    if raw is None:
        raw = _find_text(inf_nfe, f"{_ns('ide')}/{_ns('dEmi')}")
    if raw is None:
        return None
    # dhEmi is ISO-ish "2026-08-20T10:00:00-03:00"; dEmi is "2026-08-20".
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _extract_items(inf_nfe: ET.Element) -> list[ParsedNfeItem]:
    items: list[ParsedNfeItem] = []
    for det in inf_nfe.findall(_ns("det")):
        prod = det.find(_ns("prod"))
        if prod is None:
            continue
        quantity = _parse_decimal(_find_text(prod, _ns("qCom")))
        unit_price = _parse_decimal(_find_text(prod, _ns("vUnCom")))
        description = _find_text(prod, _ns("xProd"))
        if quantity is None or unit_price is None or description is None:
            msg = f"Item da NF-e sem quantidade, valor unitário ou descrição: {det.get('nItem', '?')}."
            raise NfeParseError(msg)
        items.append(
            ParsedNfeItem(
                description=description,
                product_code=_find_text(prod, _ns("cProd")),
                quantity=quantity,
                unit_price=unit_price,
                unit=_find_text(prod, _ns("uCom")),
                cfop=_find_text(prod, _ns("CFOP")),
                total=_parse_decimal(_find_text(prod, _ns("vProd"))),
            )
        )
    return items


def _extract_totals(inf_nfe: ET.Element) -> ParsedNfeTotals:
    icms_tot = inf_nfe.find(f"{_ns('total')}/{_ns('ICMSTot')}")
    if icms_tot is None:
        return ParsedNfeTotals()
    return ParsedNfeTotals(
        products=_parse_decimal(_find_text(icms_tot, _ns("vProd"))),
        freight=_parse_decimal(_find_text(icms_tot, _ns("vFrete"))),
        insurance=_parse_decimal(_find_text(icms_tot, _ns("vSeg"))),
        icms_st=_parse_decimal(_find_text(icms_tot, _ns("vICMSST"))),
        ipi=_parse_decimal(_find_text(icms_tot, _ns("vIPI"))),
        discount=_parse_decimal(_find_text(icms_tot, _ns("vDesc"))),
        invoice_total=_parse_decimal(_find_text(icms_tot, _ns("vNF"))),
    )


def parse_nfe_xml(data: bytes) -> ParsedNfe:
    """Parse an NF-e modelo 55 XML (envelope or bare NFe) into plain data."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        msg = "O arquivo não é um XML válido."
        raise NfeParseError(msg) from exc

    inf_nfe = root.find(f".//{_ns('infNFe')}")
    if inf_nfe is None:
        msg = "Documento XML não contém uma NF-e (infNFe ausente)."
        raise NfeParseError(msg)

    model = _find_text(inf_nfe, f"{_ns('ide')}/{_ns('mod')}")
    if model != "55":
        msg = (
            "Este importador aceita apenas NF-e modelo 55 "
            "(recebido: modelo {model})."
        ).format(model=model or "?")
        raise NfeParseError(msg)

    emit = inf_nfe.find(_ns("emit"))

    return ParsedNfe(
        chave=_extract_chave(root),
        numero=_find_text(inf_nfe, f"{_ns('ide')}/{_ns('nNF')}"),
        emission_date=_extract_emission_date(inf_nfe),
        emitter_cnpj_digits=_digits(_find_text(emit, _ns("CNPJ"))) if emit is not None else None,
        items=_extract_items(inf_nfe),
        totals=_extract_totals(inf_nfe),
    )

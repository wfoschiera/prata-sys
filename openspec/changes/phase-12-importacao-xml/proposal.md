## Why

Phase 11 built `EntradaEstoque` — the document header a future NF-e XML importer could write into "without a schema change" — and explicitly deferred the import itself. Every stock entrada today is typed by hand: supplier, date, document number, one line per lot, one line per adjustment. The source of all of that data is an NF-e XML file (modelo 55) that the supplier already produced and that arrives by email. Retyping it is slow, and slow data entry is the main reason cost tracking silently stops being used.

## What Changes

- New endpoint `POST /api/v1/entradas-estoque/importar-xml` (multipart upload): parses an NF-e XML and returns an **import preview** — supplier candidate matched by CNPJ, chave de acesso, emission date, line items with quantity and invoice unit price, and suggested adjustments derived from the invoice totals block (`ICMSTot`: frete, seguro, ICMS-ST, IPI, desconto).
- Product matching is **suggestive, never automatic**: each XML line carries a suggested `Product` found by normalized-name equality among the matched supplier's products first, then the wider catalog; unmatched lines are returned with no product and MUST be resolved in the UI before submission.
- The preview creates **nothing**. Submission goes through the existing `POST /api/v1/entradas-estoque` — one write path, unchanged validation, unchanged transaction semantics.
- Duplicate protection: a partial unique index on `entradasestoque.numero_documento` scoped to 44-character documents (i.e. chaves de acesso). Hand-typed short numbers are unaffected; importing the same XML twice returns HTTP 409 with the existing entrada id.
- Frontend: "Importar XML da NF-e" on the new-entrada page — upload, preview with per-line product resolution, then pre-fill of the existing `EntradaForm`.

## Capabilities

### New Capabilities

- `importacao-nfe.parse`: Parse an NF-e modelo 55 XML into a validated preview of header, items, and suggested adjustments.
- `importacao-nfe.matching`: Suggest catalog products for XML lines by normalized name match, flagging unresolved lines.
- `importacao-nfe.dedupe`: Guarantee one entrada per chave de acesso via a partial unique index and a 409 on re-import.

### Modified Capabilities

- `custo-aquisicao.entrada`: No behavioral change to the write path. `numero_documento` becomes unique when it holds a 44-char chave.

## Impact

- **Backend:** new parser module `backend/app/nfe.py` (stdlib `xml.etree.ElementTree` only — no new dependency); schemas + one route in `entradas_estoque.py`; small CRUD helper for duplicate lookup; Alembic migration adding the partial unique index (hand-written revision id, repo convention).
- **Frontend:** upload + preview component on `/estoque/entradas/new`; regenerated API client.
- **DB:** one partial unique index on `entradasestoque.numero_documento`. Additive only; no column changes, so `get_stock_prediction`'s `updated_at` sensitivity is untouched.
- **Auth:** no new permissions — preview requires `manage_estoque`, same as entrada creation (it is step one of that flow).
- **Security:** XML parsed with stdlib ElementTree, which does not resolve external entities; file size capped (413 above 512 KB); only `text/xml` content accepted.

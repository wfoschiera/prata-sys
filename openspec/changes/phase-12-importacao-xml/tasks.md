## 1. Parser module

- [x] 1.1 Create `backend/app/nfe.py` with the NFE namespace constant (`http://www.portalfiscal.inf.br/nfe`), a `NfeParseError(ValueError)` exception, and dataclass-level extraction helpers — no Pydantic here, schemas live in `models.py`
- [x] 1.2 Implement `parse_nfe_xml(data: bytes) -> ParsedNfe` accepting both `nfeProc` envelope (chave from `protNFe/infProt/chNFe`) and bare `NFe` (chave from `infNFe/@Id`, stripping the `NFe` prefix); raise `NfeParseError` on malformed XML or missing required nodes
- [x] 1.3 Reject documents where `ide/mod != "55"` with `NfeParseError`
- [x] 1.4 Extract per-det fields as `Decimal` from raw strings: `qCom`, `vUnCom`, plus `xProd`, `cProd`, `uCom`, `CFOP`; extract totals from `ICMSTot`: `vFrete`, `vSeg`, `vICMSST`, `vIPI`, `vDesc`, `vProd`, `vNF`
- [x] 1.5 Extract emission date from `dhEmi` (fall back to `dEmi`), taking the date part only
- [x] 1.6 Strip emitter `CNPJ` to digits; handle absent/empty CNPJ without crashing

## 2. Models & migration

- [x] 2.1 Add preview schemas to `backend/app/models.py`: `ImportacaoItemPreview` (line fields + `product_sugerido_id: uuid.UUID | None`, `match_status: Literal["sugerido","sem_match","ambiguo"]`), `ImportacaoAjusteSugerido` (`tipo: TipoCustoAjuste`, `valor: Decimal`, `documento_referencia`), `FornecedorRef` reuse for supplier suggestion, and `ImportacaoNfePreview` aggregating all
- [x] 2.2 Hand-write Alembic migration adding the partial unique index `ix_entradaestoque_chave_unique` on `entradaestoque(numero_documento)` with `postgresql_where=sa.text("char_length(numero_documento) = 44")`, `down_revision = 'd4e5f6a7b8c9'`, additive only
- [x] 2.3 Verify `downgrade()` drops only the index

## 3. CRUD

- [x] 3.1 Import new models at the **top** of `backend/app/crud.py` (see `docs/pitfalls.md` #3)
- [x] 3.2 Implement `find_fornecedor_by_cnpj(*, session, cnpj_digits) -> Fornecedor | None` (exact match on digit string)
- [x] 3.3 Implement `suggest_products_for_lines(*, session, fornecedor_id, descriptions) -> list[...]` doing normalized-name equality matching in at most 2 queries (supplier products first, then others only if needed)
- [x] 3.4 Implement `find_entrada_by_numero_documento(*, session, numero_documento) -> EntradaEstoque | None` for the 409 check

## 4. Route

- [x] 4.1 Add `POST /importar-xml` to `entradas_estoque.py`: multipart `UploadFile`, size cap 512 KB → 413, `NfeParseError` → 422 with PT-BR detail, duplicate chave → 409 with existing id, success → `ImportacaoNfePreview` (200)
- [x] 4.2 Guard with `ManageGuard` (`manage_estoque`)
- [x] 4.3 Build suggested adjustments from parsed totals per the mapping table in design.md Decision 2 (skip zero values; `documento_referencia` = chave)

## 5. Backend tests

- [x] 5.1 Fixture XMLs under `backend/tests/fixtures/nfe/`: authorized envelope with frete/ICMS-ST/desconto, bare `NFe`, NFC-e (mod 65), malformed file
- [x] 5.2 Parser unit tests: envelope vs bare extraction, Decimal parsing, date fallback `dhEmi`→`dEmi`, CNPJ digit stripping, error cases
- [x] 5.3 Route tests: full happy path asserting every suggested adjustment and its sign; no-records-created assertion after preview
- [x] 5.4 Matching tests: unique supplier-product match → `sugerido`; ambiguous → `ambiguo`; none → `sem_match`; supplier-scoped search preferred over global
- [x] 5.5 Duplicate test: import twice → second returns 409 with existing id; manual short-number duplicates still allowed
- [x] 5.6 Error tests: mod 65 → 422; malformed → 422; >512 KB → 413; view-only user → 403

## 6. Frontend

- [x] 6.1 Run `bash ./scripts/generate-client.sh`
- [x] 6.2 Add an "Importar XML da NF-e" action on `/estoque/entradas/new`: file input → upload → preview panel showing chave, emission date, supplier suggestion, lines with `uCom` visible, match status badges
- [x] 6.3 Per-line product select resolving `sem_match`/`ambiguo` lines; submit disabled while any line is unresolved
- [x] 6.4 On confirm, pre-fill the existing `EntradaForm` (supplier, date, numero_documento = chave, itens from resolved lines, ajustes from suggestions) and submit through the unchanged create flow
- [x] 6.5 Handle 409 with a PT-BR message linking to the existing entrada
- [x] 6.6 All user-facing strings PT-BR; code/comments English

## 7. Verification

- [x] 7.1 `uv run pytest -n auto tests/` green (only the two known pre-existing `.env.example` failures allowed)
- [x] 7.2 Ruff clean on changed files; mypy no new errors
- [x] 7.3 `cd frontend && bun run build` clean
- [x] 7.4 E2E against dev stack: upload fixture XML → resolve matches → submit → entrada created with chave, lots, and adjustments; real costs apportioned correctly
- [x] 7.5 Re-upload same XML → 409 surfaced cleanly in UI

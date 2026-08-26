## Context

Phase 11 delivered the entrada write path: `EntradaEstoqueCreate` → `crud.create_entrada_estoque` (flush-then-commit, atomic, validates products, optionally books a `Transacao`) → apportioned real costs. The header already has `numero_documento: str | None = Field(max_length=44)` sized for a chave de acesso.

An NF-e XML is a namespaced document (`http://www.portalfiscal.inf.br/nfe`), either bare (`<NFe>`) or wrapped in an envelope (`<nfeProc>` with `<protNFe>` carrying the authorization and chave). Line items live in `infNFe/det`, each with `prod/qCom`, `prod/vUnCom`, `prod/xProd`, `prod/cProd`, `prod/CFOP`. The totals block `infNFe/total/ICMSTot` carries delivery-level values: `vFrete`, `vSeg`, `vICMSST`, `vIPI`, `vDesc`, `vProd`, `vNF`.

The catalog side has no SKU/EAN: `Product` carries only `name`, `description`, `fornecedor_id`. Product codes in the XML come from the *supplier's* ERP and are meaningless here.

## Goals / Non-Goals

**Goals:**

- Eliminate hand-typing of entradas when the supplier's XML is available.
- Keep exactly one write path — the phase-11 create endpoint — so validation, atomicity, and expense booking semantics cannot diverge.
- Make re-importing an invoice impossible at the database level.

**Non-Goals:**

- **SEFAZ integration.** No certificate, no `NFeDistribuicaoDFe`, no download-by-chave. Manual upload of the `.xml` file only.
- **Automatic catalog creation.** Unmatched XML lines do not create Products; they are flagged and resolved by the user against existing catalog entries.
- **XSD schema validation.** Structural parsing plus targeted field extraction; full XSD validation adds nothing for files SEFAZ has already authorized.
- **NFC-e (modelo 65).** Rejected explicitly — stock purchases arrive as NF-e modelo 55.
- **Per-item desconto mapping.** Item-level `prod/vDesc` is left to the user to reflect in `custo_unitario_nf` if needed; only total-level `vDesc` is suggested as an adjustment. Per-item discount semantics vary by supplier and guessing them wrong corrupts cost silently.
- **Email ingestion.** Out of scope.

## Decisions

### 1. Parse-preview-submit, not parse-and-create

`POST /importar-xml` returns a preview and persists nothing. The frontend resolves product matches, then submits a plain `EntradaEstoqueCreate` to the existing endpoint.

*Why:* the de-para problem makes fully automatic import wrong — an unmatched line would either abort the import or invent a product. Preview keeps the machine work (parsing, totals, matching) and leaves judgment to the user, while reusing all phase-11 guarantees for free.

*Alternative considered:* import-with-placeholders creating unmatched products automatically. Rejected — pollutes the catalog with supplier-named duplicates that later fragment weighted-average cost.

### 2. Suggested adjustments derive from `ICMSTot`, mapped onto the closed `TipoCustoAjuste` set

| ICMSTot field | Condition | Adjustment |
|---|---|---|
| `vFrete` | > 0 | `frete` (+) |
| `vSeg` | > 0 | `seguro` (+) |
| `vICMSST` | > 0 | `icms_st` (+) |
| `vIPI` | > 0 | `ipi` (+) |
| `vDesc` | > 0 | `desconto_comercial` (−) |

`documento_referencia` is prefilled with the chave on every suggested adjustment. Values parse as `Decimal` from string — never float — and zero-valued totals produce no adjustment, since `CustoAjusteCreate` rejects zero anyway.

### 3. Supplier matched by CNPJ digits, never auto-created

`emit/CNPJ` is stripped to digits and looked up against `Fornecedor.cnpj` (already stored as a plain digit string). A miss yields a `null` fornecedor suggestion and the UI asks the user to pick one; submission validates through the existing path. CPF emitters (odd but legal for small suppliers) are surfaced but not matched — `Fornecedor.cnpj` is CNPJ-only today.

### 4. Name-normalized product suggestions

Each XML line is matched by exact normalized name equality (casefold, whitespace collapsed) among products of the matched supplier first, then across all products. Exactly one candidate ⇒ status `sugerido` with the id; zero or many ⇒ `sem_match` / `ambiguo` and the UI forces a manual pick. Matching never writes anything.

*Why not fuzzy:* fuzzy matches presented as suggestions erode trust precisely where correctness matters (cost per lot). Equality-only is either right or visibly absent.

### 5. One entrada per chave, enforced twice

- Application level: the import route looks up an existing entrada with the same 44-char `numero_documento` before returning a preview and answers HTTP 409 with the existing id.
- Database level: partial unique index `CREATE UNIQUE INDEX ix_entradaestoque_chave_unique ON entradaestoque (numero_documento) WHERE char_length(numero_documento) = 44`.

Scoping to 44 chars is what keeps hand-typed short numbers working — two suppliers legitimately issue both "NF 123". Chaves are globally unique by construction, so no false positives. Precedent: `ix_fornecedor_cnpj_unique` partial-index pattern from `f3a68091d1fb`.

### 6. Parser hardening without new dependencies

Stdlib `xml.etree.ElementTree` only. ET does not resolve external entities, which closes the XXE class; namespace handling via explicit URI constants rather than prefix sniffing. Uploads are capped at 512 KB (413 above) — real NF-e files are tens of KB — and any parse failure or missing required node returns 422 with a PT-BR message naming the problem. Modelo check: `ide/mod = "55"`, else 422.

## Risks / Trade-offs

- **Risk**: suppliers issue XMLs whose line quantities use units different from our stock unit (`uCom` "CX" vs stock "UN"). → Not solvable automatically; the preview shows `uCom` next to quantity so the mismatch is visible, and the user corrects the quantity before submit. Documented in the UI copy.
- **Risk**: the unique index migration fails on existing duplicate chaves. → Impossible today: nothing wrote 44-char values yet except manual entry of a chave twice, which the pre-migration SQL can surface; migration is additive and reversible (`downgrade()` drops the index).
- **Risk**: preview arithmetic drifting from create-time arithmetic. → Mitigated structurally: the preview computes no derived costs at all. It only echoes parsed values; all money math stays in the single write path.
- **Trade-off**: two-step flow costs one extra click versus one-shot import. Accepted — it buys match resolution and duplicate visibility.

## Migration Plan

1. Add schemas (`ImportacaoNfe*Read`) and the parser module.
2. Hand-write the Alembic migration adding the partial unique index (`down_revision` = current head `d4e5f6a7b8c9`), additive only.
3. Add the CRUD duplicate lookup + route; register nothing new (router exists).
4. Regenerate client; build the upload/preview UI into `/estoque/entradas/new`.
5. Tests: parser fixtures (envelope and bare NFe), totals→adjustments mapping, matching statuses, 409 duplicate, 422 malformed/modelo-wrong/oversize, permission checks.

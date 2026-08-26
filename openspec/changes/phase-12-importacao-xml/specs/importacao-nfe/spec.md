## ADDED Requirements

### Requirement: Parsing an NF-e XML produces an import preview without persisting anything
The system SHALL accept a multipart upload of an NF-e XML file (modelo 55) at `POST /api/v1/entradas-estoque/importar-xml` from users with `manage_estoque`, and SHALL return a preview containing: the chave de acesso (44 digits), the invoice number (`nNF`), the emission date as `data_entrada`, the emitter's CNPJ and matched supplier candidate (or `null`), one line per `det` item carrying quantity (`qCom`), invoice unit price (`vUnCom`), description (`xProd`), unit (`uCom`), and CFOP, and suggested adjustments derived from the totals block. The endpoint SHALL NOT create any database record. All monetary and quantity values SHALL be parsed as `Decimal` from the raw strings. Files above 512 KB SHALL be rejected with HTTP 413. Malformed XML, a missing required node, or a document whose `ide/mod` is not `"55"` SHALL be rejected with HTTP 422 and a message in PT-BR naming the problem.

#### Scenario: Envelope XML is fully parsed
- **WHEN** a user with `manage_estoque` uploads an authorized NF-e (`nfeProc` envelope) whose totals are vFrete 200.00, vICMSST 50.00, vDesc 100.00 and two `det` lines
- **THEN** the response returns HTTP 200 with the chave, emission date, both lines with their quantities and unit prices
- **AND** suggested adjustments include `frete` 200.00, `icms_st` 50.00, and `desconto_comercial` −100.00

#### Scenario: Preview creates no records
- **WHEN** any preview request completes successfully
- **THEN** no `EntradaEstoque`, `ProductItem`, or `CustoAjuste` row exists for the uploaded document

#### Scenario: NFC-e document is rejected
- **WHEN** a user uploads an XML whose `ide/mod` is `"65"`
- **THEN** the system returns HTTP 422 with a PT-BR message

#### Scenario: Malformed XML is rejected
- **WHEN** the uploaded body is not well-formed XML
- **THEN** the system returns HTTP 422 with a PT-BR message

#### Scenario: Oversized upload is rejected
- **WHEN** the uploaded file exceeds 512 KB
- **THEN** the system returns HTTP 413

#### Scenario: User without manage_estoque cannot import
- **WHEN** a user holding only `view_estoque` POSTs to `/importar-xml`
- **THEN** the system returns HTTP 403 Forbidden

---

### Requirement: Supplier matching by CNPJ never auto-creates
The parser SHALL strip the emitter CNPJ to digits and look it up among existing `Fornecedor` records. On exactly one match, the preview SHALL carry that supplier; otherwise it SHALL carry `null`. The system SHALL NOT create a supplier during import.

#### Scenario: Known supplier is matched
- **WHEN** the XML emitter CNPJ equals an existing `Fornecedor.cnpj`
- **THEN** the preview carries that fornecedor id and company name

#### Scenario: Unknown supplier yields null and blocks nothing
- **WHEN** the emitter CNPJ matches no fornecedor
- **THEN** the preview carries `fornecedor_sugerido: null`
- **AND** submission of the resulting entrada still succeeds once the user picks a fornecedor in the UI

---

### Requirement: Product suggestions are equality-based and non-binding
Each preview line SHALL carry a product suggestion found by normalized-name equality (casefold, whitespace collapsed), searching first among products whose `fornecedor_id` equals the matched supplier, then across all products. A line with exactly one candidate SHALL have status `sugerido` and carry the product id; zero candidates SHALL be `sem_match`; more than one SHALL be `ambiguo`. Suggestions SHALL NOT create, link, or modify any record. Unresolved lines MUST be resolved to a valid `product_id` before submission via the unchanged create endpoint.

#### Scenario: Unique name match is suggested
- **WHEN** an XML line's normalized `xProd` equals exactly one product name of the matched supplier
- **THEN** the line has status `sugerido` with that product's id

#### Scenario: Ambiguous match is flagged, not guessed
- **WHEN** two products of the supplier share the same normalized name
- **THEN** the line has status `ambiguo` with no product id

#### Scenario: No match leaves resolution to the user
- **WHEN** no catalog product normalizes equal to the XML line
- **THEN** the line has status `sem_match`
- **AND** the frontend requires an explicit product selection before submit

---

### Requirement: One entrada per chave de acesso
Importing an XML whose chave de acesso already exists as a 44-character `numero_documento` on any `EntradaEstoque` SHALL fail with HTTP 409 and the existing entrada's id in the response detail, checked before returning a preview. The database SHALL enforce uniqueness with a partial unique index on `numero_documento` scoped to documents of length 44; hand-typed shorter numbers SHALL remain unrestricted.

#### Scenario: Re-importing the same invoice is rejected
- **WHEN** a preview is requested for an XML whose chave was already imported
- **THEN** the system returns HTTP 409 with the existing entrada id

#### Scenario: Duplicate hand-typed short numbers remain allowed
- **WHEN** two entradas from different suppliers are created manually with `numero_documento` "123"
- **THEN** both are accepted

#### Scenario: Database enforces the chave constraint
- **WHEN** a write attempts to insert a second entrada with the same 44-character `numero_documento`, bypassing the route check
- **THEN** the database raises an integrity error on the partial unique index

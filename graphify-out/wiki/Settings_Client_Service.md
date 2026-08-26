# Settings Client Service

> 6 nodes · cohesion 0.33

## Key Concepts

- **SettingsService** (4 connections) — `frontend/src/client/sdk.gen.ts`
- **.updateCompanySettings()** (4 connections) — `frontend/src/client/sdk.gen.ts`
- **.getCompanySettings()** (3 connections) — `frontend/src/client/sdk.gen.ts`
- **SettingsGetCompanySettingsResponse** (3 connections) — `frontend/src/client/types.gen.ts`
- **SettingsUpdateCompanySettingsData** (3 connections) — `frontend/src/client/types.gen.ts`
- **SettingsUpdateCompanySettingsResponse** (3 connections) — `frontend/src/client/types.gen.ts`

## Relationships

- [[SDK Mutations (sdk.gen)]] (4 shared connections)
- [[Generated TypeScript Types]] (3 shared connections)
- [[SDK Query Operations]] (2 shared connections)
- [[Frontend Service Layer]] (1 shared connections)

## Source Files

- `frontend/src/client/sdk.gen.ts`
- `frontend/src/client/types.gen.ts`

## Audit Trail

- EXTRACTED: 20 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*

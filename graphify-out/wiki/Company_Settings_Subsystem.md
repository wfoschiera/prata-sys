# Company Settings Subsystem

> 12 nodes · cohesion 0.30

## Key Concepts

- **CompanySettings** (7 connections) — `backend/app/models.py`
- **SessionDep** (6 connections) — `backend/app/api/routes/settings.py`
- **CompanySettingsRead** (6 connections) — `backend/app/api/routes/settings.py`
- **update_company_settings()** (6 connections) — `backend/app/api/routes/settings.py`
- **CompanySettingsRead** (5 connections) — `backend/app/models.py`
- **CompanySettingsUpdate** (5 connections) — `backend/app/models.py`
- **CompanySettingsUpdate** (5 connections) — `backend/app/api/routes/settings.py`
- **get_company_settings()** (4 connections) — `backend/app/api/routes/settings.py`
- **settings.py** (3 connections) — `backend/app/api/routes/settings.py`
- **Singleton table — stores company info for document headers (orçamentos, etc.).** (1 connections) — `backend/app/models.py`
- **Get company settings for document headers.** (1 connections) — `backend/app/api/routes/settings.py`
- **Update company settings. Admin only.** (1 connections) — `backend/app/api/routes/settings.py`

## Relationships

- [[Backend CRUD Core]] (7 shared connections)
- [[Estoque Router]] (3 shared connections)

## Source Files

- `backend/app/api/routes/settings.py`
- `backend/app/models.py`

## Audit Trail

- EXTRACTED: 29 (58%)
- INFERRED: 21 (42%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*

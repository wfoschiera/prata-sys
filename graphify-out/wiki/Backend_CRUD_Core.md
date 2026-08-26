# Backend CRUD Core

> 315 nodes · cohesion 0.09

## Key Concepts

- **models.py** (153 connections) — `backend/app/models.py`
- **Session** (134 connections) — `backend/app/crud.py`
- **Service** (128 connections) — `backend/app/models.py`
- **Client** (121 connections) — `backend/app/models.py`
- **User** (106 connections) — `backend/app/models.py`
- **ServiceItem** (103 connections) — `backend/app/models.py`
- **ProductItem** (100 connections) — `backend/app/models.py`
- **SQLModel** (98 connections)
- **ProductItemStatus** (97 connections) — `backend/app/models.py`
- **Product** (94 connections) — `backend/app/models.py`
- **UUID** (94 connections) — `backend/app/crud.py`
- **Transacao** (92 connections) — `backend/app/models.py`
- **crud.py** (91 connections) — `backend/app/crud.py`
- **Fornecedor** (91 connections) — `backend/app/models.py`
- **CategoriaTransacao** (90 connections) — `backend/app/models.py`
- **TipoTransacao** (90 connections) — `backend/app/models.py`
- **ProductCategory** (88 connections) — `backend/app/models.py`
- **ServiceItemCreate** (84 connections) — `backend/app/models.py`
- **ServiceType** (84 connections) — `backend/app/models.py`
- **UserUpdate** (84 connections) — `backend/app/models.py`
- **ServiceCreate** (83 connections) — `backend/app/models.py`
- **FornecedorCategoryEnum** (82 connections) — `backend/app/models.py`
- **ItemType** (82 connections) — `backend/app/models.py`
- **ProductType** (82 connections) — `backend/app/models.py`
- **TransacaoCreate** (82 connections) — `backend/app/models.py`
- *... and 290 more nodes in this community*

## Relationships

- [[Service API Schemas]] (150 shared connections)
- [[Service Transition Unit Tests]] (96 shared connections)
- [[Permissions Model & Tests]] (84 shared connections)
- [[Inventory & Supplier Schemas]] (79 shared connections)
- [[Fornecedor Schemas]] (70 shared connections)
- [[Services API Tests]] (59 shared connections)
- [[Orcamentos Router]] (49 shared connections)
- [[Estoque Router]] (41 shared connections)
- [[Stock Prediction Tests]] (39 shared connections)
- [[Transacoes API Tests]] (30 shared connections)
- [[Estoque API Tests]] (29 shared connections)
- [[Clients Router]] (26 shared connections)

## Source Files

- `backend/app/api/routes/orcamentos.py`
- `backend/app/api/routes/transacoes.py`
- `backend/app/core/permissions.py`
- `backend/app/crud.py`
- `backend/app/models.py`
- `backend/tests/api/routes/test_dashboard.py`
- `backend/tests/api/routes/test_estoque.py`
- `backend/tests/api/routes/test_private.py`
- `backend/tests/api/routes/test_transacoes.py`
- `backend/tests/conftest.py`
- `backend/tests/crud/test_stock_reservation_concurrency.py`
- `backend/tests/factories.py`

## Audit Trail

- EXTRACTED: 1445 (14%)
- INFERRED: 8742 (86%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*

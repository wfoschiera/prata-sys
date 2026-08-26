# Inventory & Supplier Schemas

> 41 nodes · cohesion 0.15

## Key Concepts

- **SessionDep** (17 connections) — `backend/app/api/routes/products.py`
- **UUID** (17 connections) — `backend/app/api/routes/products.py`
- **ProductItemRead** (16 connections) — `backend/app/models.py`
- **ProductTypeRead** (16 connections) — `backend/app/models.py`
- **ProductRead** (15 connections) — `backend/app/api/routes/products.py`
- **FornecedorRef** (12 connections) — `backend/app/models.py`
- **ProductRead** (11 connections) — `backend/app/models.py`
- **Product** (11 connections) — `backend/app/api/routes/products.py`
- **ProductCategory** (11 connections) — `backend/app/api/routes/products.py`
- **ProductCreate** (11 connections) — `backend/app/api/routes/products.py`
- **ProductItemRead** (11 connections) — `backend/app/api/routes/products.py`
- **ProductUpdate** (11 connections) — `backend/app/api/routes/products.py`
- **StockPredictionRead** (11 connections) — `backend/app/api/routes/products.py`
- **products.py** (11 connections) — `backend/app/api/routes/products.py`
- **SessionDep** (9 connections) — `backend/app/api/routes/product_types.py`
- **get_product()** (9 connections) — `backend/app/api/routes/products.py`
- **UUID** (8 connections) — `backend/app/api/routes/product_types.py`
- **ProductTypeRead** (8 connections) — `backend/app/api/routes/product_types.py`
- **product_types.py** (8 connections) — `backend/app/api/routes/product_types.py`
- **_to_product_read()** (8 connections) — `backend/app/api/routes/products.py`
- **update_product()** (7 connections) — `backend/app/api/routes/products.py`
- **ProductItemRead** (6 connections) — `backend/app/api/routes/product_items.py`
- **SessionDep** (6 connections) — `backend/app/api/routes/product_items.py`
- **UUID** (6 connections) — `backend/app/api/routes/product_items.py`
- **get_product_type()** (6 connections) — `backend/app/api/routes/product_types.py`
- *... and 16 more nodes in this community*

## Relationships

- [[Backend CRUD Core]] (79 shared connections)
- [[Estoque Router]] (19 shared connections)

## Source Files

- `backend/app/api/routes/product_items.py`
- `backend/app/api/routes/product_types.py`
- `backend/app/api/routes/products.py`
- `backend/app/models.py`

## Audit Trail

- EXTRACTED: 162 (48%)
- INFERRED: 176 (52%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*

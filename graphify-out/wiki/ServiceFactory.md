# ServiceFactory

> God node · 106 connections · `backend/tests/factories.py`

**Community:** [[Services API Tests]]

## Connections by Relation

### calls
- [[_setup_reserved_service()]] `EXTRACTED`
- [[test_transition_to_completed_marks_stock_utilizado()]] `EXTRACTED`
- [[test_deduct_stock_marks_reserved_items_utilizado()]] `EXTRACTED`
- [[test_cancel_executing_service_releases_stock()]] `EXTRACTED`
- [[test_transition_to_scheduled_reserves_stock()]] `EXTRACTED`
- [[test_transition_to_cancelled_releases_reserved_stock()]] `EXTRACTED`
- [[test_transition_to_scheduled_with_insufficient_stock_returns_warning()]] `EXTRACTED`
- [[test_invalid_deduction_item_id_raises()]] `EXTRACTED`
- [[_create_completed_service()]] `EXTRACTED`
- [[test_dashboard_operational_sums_drilling_meters()]] `EXTRACTED`
- [[test_deduct_stock_items_rejects_non_material()]] `EXTRACTED`
- [[test_delete_item_from_executing_service_returns_422()]] `EXTRACTED`
- [[test_executing_to_completed_with_deduction_items()]] `EXTRACTED`
- [[test_invalid_completed_to_anything_raises()]] `EXTRACTED`
- [[test_delete_service_item_wrong_service()]] `EXTRACTED`
- [[test_delete_scheduled_service_returns_422()]] `EXTRACTED`
- [[test_delete_executing_service_returns_422()]] `EXTRACTED`
- [[test_add_item_to_executing_service_returns_422()]] `EXTRACTED`
- [[test_add_item_to_completed_service_returns_422()]] `EXTRACTED`
- [[test_list_transacoes_filter_by_service_id_via_api()]] `EXTRACTED`

### contains
- [[factories.py]] `EXTRACTED`

### rationale_for
- [[Create a Service directly in the database.      Auto-creates a Client via SubFac]] `EXTRACTED`

### uses
- [[Service]] `INFERRED`
- [[Client]] `INFERRED`
- [[ServiceItem]] `INFERRED`
- [[ProductItem]] `INFERRED`
- [[ProductItemStatus]] `INFERRED`
- [[Product]] `INFERRED`
- [[Transacao]] `INFERRED`
- [[Fornecedor]] `INFERRED`
- [[TipoTransacao]] `INFERRED`
- [[CategoriaTransacao]] `INFERRED`
- [[ProductCategory]] `INFERRED`
- [[ServiceType]] `INFERRED`
- [[ItemType]] `INFERRED`
- [[FornecedorCategoryEnum]] `INFERRED`
- [[ProductType]] `INFERRED`
- [[FornecedorContato]] `INFERRED`
- [[FornecedorCategoria]] `INFERRED`
- [[TestClient]] `INFERRED`
- [[Session]] `INFERRED`
- [[TestClient]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*

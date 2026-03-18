# Specs: Phase 8 — Stock Integration

## Data model

No new tables. All changes are to `ProductItem.status` and `ProductItem.service_id` values.

```
ProductItem status machine:

  em_estoque ──[reserve]──▶ reservado ──[utilize]──▶ utilizado
       ▲                        │
       └────────[release]───────┘
                (on cancel)

Transitions:
  reserve:  em_estoque  → reservado   (set service_id = service.id, updated_at = now)
  utilize:  reservado   → utilizado   (updated_at = now)
  release:  reservado   → em_estoque  (clear service_id = null, updated_at = now)

Rules:
  - Only items with matching product_id are candidates for reservation
  - Items are processed FIFO by created_at (oldest stock first)
  - Reservation is best-effort: partial reservation is allowed (warns, doesn't block)
  - Cancellation from any non-terminal state must release all reserved items for the service
```

## API contract changes

### `POST /services/{id}/transition` (existing)

**When `to_status = scheduled`:**
- Response `stock_warnings` may now contain non-empty list
- Each `StockWarning`: `{ product_id, product_name, needed_qty, available_qty }`

**When `to_status = completed`:**
- All `ProductItem` records with `status=reservado` and `service_id=this service` are marked `utilizado`
- No new response fields

**When `to_status = cancelled`:**
- All `ProductItem` records with `status=reservado` and `service_id=this service` are marked `em_estoque`, `service_id` cleared

### `POST /services/{id}/deduct-stock` (existing stub → real implementation)

**Request:** No body
**Response:** `list[DeductionSummary]`
```json
[
  { "product_id": "...", "product_name": "Tubo 6\"", "quantity_deducted": 3.0 }
]
```
**Status codes:**
- 200: deduction successful (may be empty list if nothing reserved)
- 422: service is not in `executing` status

## Error handling

| Scenario | Behavior |
|----------|----------|
| No stock available for reservation | Transition proceeds; `StockWarning` added to response |
| Partial stock (some but not enough) | Reserve what's available; warn about shortfall |
| Deduction when nothing reserved | Return empty list (OK, not an error) |
| Race: two concurrent completions | Second request finds no reservado items → returns empty list |
| service_id mismatch in deduction_items | ValueError → 422 (existing behavior, keep) |

## Behavior diagram

```
TRANSITION TO scheduled:
  for each material ServiceItem:
    needed_qty = service_item.quantity
    candidates = SELECT * FROM productitem
                 WHERE product_id = ? AND status = 'em_estoque'
                 ORDER BY created_at ASC
    reserved = 0
    for item in candidates:
      if reserved >= needed_qty: break
      item.status = 'reservado'
      item.service_id = service.id
      item.updated_at = now
      reserved += item.quantity
    if reserved < needed_qty:
      append StockWarning(product_id, needed_qty, reserved)

TRANSITION TO completed:
  _deduct_stock_items(session, service, deduction_items)
    → mark all service's reservado items as utilizado

TRANSITION TO cancelled:
  _release_stock_items(session, service)
    → mark all service's reservado items as em_estoque, clear service_id

POST /deduct-stock (manual, while executing):
  same as deduction path above
```

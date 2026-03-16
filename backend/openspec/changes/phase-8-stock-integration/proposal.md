# Proposal: Phase 8 — Stock Integration (Complete Stub Implementations)

## Problem

Phases 5 and 7 left three stock-related functions as stubs in `backend/app/crud.py`.
These stubs are reachable via live API endpoints but produce no side-effects:

| Stub | Location | Effect |
|------|----------|--------|
| `_check_stock_for_service` | `crud.py:311` | Always returns `[]` — no stock is ever reserved |
| `_deduct_stock_items` | `crud.py:319` | Validates IDs but never marks stock `utilizado` |
| `deduct_stock` | `crud.py:393` | Always returns `[]` — manual deduction does nothing |

As a result:
- Services can be scheduled with zero available stock and no warning is shown
- Completing a service never consumes inventory — stock is never decremented
- Inventory levels are permanently incorrect (nothing ever leaves `em_estoque`)

## Proposed solution

Complete the three stubs using the existing `ProductItem` model (already shipping in Phase 7).

### Reservation flow (on `scheduled` transition)

For each `ServiceItem` of type `material` on the service:
1. Find matching `ProductItem` records with `status = em_estoque` for the same product
2. Flip enough items to `reservado` (set `service_id`, set `updated_at`)
3. If total available < needed quantity → produce a `StockWarning` (do not block the transition)

### Deduction flow (on `completed` transition or manual `POST /deduct-stock`)

For each `ProductItem` with `status = reservado` and `service_id = this service`:
1. Mark it `utilizado`, set `updated_at`

### Release flow (on `cancelled` transition)

For each `ProductItem` with `status = reservado` and `service_id = this service`:
1. Mark it `em_estoque`, clear `service_id`, set `updated_at`

## Non-goals

- No new models or migrations needed — `ProductItem` already has `status`, `service_id`, `updated_at`
- No changes to the service lifecycle state machine (VALID_STATUS_TRANSITIONS stays the same)
- No UI changes required (warnings surface through the existing `StockWarning` schema)
- No change to the `baixar_estoque` endpoint (already implemented and working)

## Success criteria

1. Transitioning a service to `scheduled` with insufficient stock returns `stock_warnings` in the response
2. Completing a service marks all associated reserved `ProductItem` records as `utilizado`
3. Cancelling a service releases all reserved `ProductItem` records back to `em_estoque`
4. `POST /deduct-stock` on an `executing` service marks reserved items as `utilizado`
5. Stock prediction (`get_stock_prediction`) accuracy improves because `updated_at` is now set reliably

## Risk

Low. This is implementing described-but-deferred logic. The data model fully supports it.
The only risk is a race condition if two requests attempt to reserve the same `ProductItem`
simultaneously — mitigated by the atomic `UPDATE … WHERE status = 'em_estoque'` pattern.

---
name: fix-tests
description: Run tests and fix them if needed
disable-model-invocation: true
---
# Fix tests

## Description

This command runs the tests and fixes them, if needed.

## Steps

- Determine which part of the codebase changed (backend, frontend, or both).
- **Backend**: Run `cd backend && bash ../scripts/test.sh`. If tests fail, investigate and fix them.
- **Frontend**: Run `cd frontend && bun run test`. If tests fail, investigate and fix them.
- When fixing backend tests, watch out for:
  - N+1 queries — use `selectinload` or `joinedload` as needed
  - Forward reference imports — always import models at the top of `crud.py`
  - Python 3.14 header validation — no trailing colons in header names
- When fixing frontend tests, watch out for:
  - Zod v4 API: use `error:` not `required_error:`
  - React Hook Form + Zod: use `z.number()` with `valueAsNumber`, never `z.coerce.number()`

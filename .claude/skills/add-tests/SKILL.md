---
name: add-tests
description: Add tests for the current changes
disable-model-invocation: true
---
# Add tests

## Description

This command adds tests for the current changes.

## Steps

- Check the current changes and add tests for them, if needed.
- **Backend tests** (pytest): tests live in `backend/tests/`. Follow existing test patterns — use fixtures for DB session and test client. Always check for N+1 queries in tested code.
- **Frontend E2E tests** (Playwright): tests live in `frontend/tests/`.
- Run the tests to check if they are passing:
  - Backend: `cd backend && bash ../scripts/test.sh`
  - Frontend: `cd frontend && bun run test`
- UI-facing text in tests (expected values, assertions on labels) must be in PT-BR.
- Code, comments, and test names must be in English.

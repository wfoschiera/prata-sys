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

## Faker & factory_boy Conventions (Backend)

### CPF / CNPJ Generation
- **Always** use `Faker("pt_BR")` for generating Brazilian documents — never hand-roll CPF/CNPJ helpers.
- **Always strip formatting** before passing to model fields:
  - CPF: `fake.cpf().replace(".", "").replace("-", "")` → 11-digit string
  - CNPJ: `fake.cnpj().replace(".", "").replace("/", "").replace("-", "")` → 14-digit string
- The CPF validator (`_validate_document_number` in `models.py`) requires **digits-only** — `fake.cpf()` returns formatted `"XXX.XXX.XXX-XX"` which will fail validation if not stripped.
- The CNPJ validator strips formatting itself, but strip anyway for consistency.
- Use locale `"pt_BR"` (underscore, not hyphen) — both work but standardize on underscore.
- Module-level pattern: `fake = Faker("pt_BR")` at the top of each test file.

### factory_boy
- Factories live in `backend/tests/factories.py`.
- The `_bind_factory_session` autouse fixture in `conftest.py` automatically wires all factories to the per-test transactional DB session.
- Use factories for complex objects that are test prerequisites (e.g., `FornecedorFactory` for supplier-dependent tests).
- Fixtures wrapping factories go in `conftest.py` (e.g., `fornecedor` fixture).
- Factory example pattern:
  ```python
  class FornecedorFactory(factory.Factory):
      class Meta:
          model = Fornecedor
      company_name = factory.LazyFunction(lambda: fake.company())
      cnpj = factory.LazyFunction(
          lambda: fake.cnpj().replace(".", "").replace("/", "").replace("-", "")
      )
  ```

### What NOT to replace with Faker
- Intentionally invalid CPF/CNPJ values in negative tests (e.g., `"1234567890123"`, `"11222333000199"`, `"123"`) — these test validation and must remain hardcoded.

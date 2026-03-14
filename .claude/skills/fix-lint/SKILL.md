---
name: fix-lint
description: Check code lint and fix it if needed
disable-model-invocation: true
---
# Fix lint

## Description

This command checks the code lint and fixes it, if needed.

## Steps

- Determine which part of the codebase changed (backend, frontend, or both).
- **Backend** (from `backend/`):
  - Run `ruff check . --fix` to auto-fix linting issues.
  - Run `mypy .` to check types. Fix any type errors manually — do not add `# type: ignore` unless absolutely necessary.
- **Frontend** (from `frontend/`):
  - Run `bun run lint` (Biome) to check for issues.
  - Run `bun run build` to verify TypeScript compiles.
- If there are lint errors that cannot be auto-fixed, investigate and fix them manually.
- Never suppress lint rules by modifying config files — only fix the actual code.

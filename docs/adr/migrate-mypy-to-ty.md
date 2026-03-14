# ADR: Migrate from mypy to ty (Astral)

**Status:** Deferred
**Date:** 2026-03-12

## Context

[ty](https://github.com/astral-sh/ty) is Astral's new type checker for Python (the same team behind Ruff and uv). It is written in Rust and is reported to be 10–100x faster than mypy.

We currently use `mirrors-mypy` in `.pre-commit-config.yaml` with `--python-version=3.13` and `additional_dependencies` for sqlmodel, pydantic, and fastapi.

## Why we haven't migrated yet

1. **ty is in beta** — as of March 2026 it is at v0.0.x. The API and error messages are still evolving.
2. **No official pre-commit hook repo** — unlike `ruff-pre-commit`, there is no `astral-sh/ty-pre-commit` repository yet. Progress is tracked in [astral-sh/ty#269](https://github.com/astral-sh/ty/issues/269).
3. **Different strictness profile** — ty may flag different errors than mypy or miss some mypy-specific checks. A migration would require auditing the backend code against ty's output.

## How to migrate when ready

### 1. Add ty to backend dev dependencies

```bash
uv add --dev ty
```

### 2. Replace the mypy hook in `.pre-commit-config.yaml`

Remove:
```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.19.1
  hooks:
    - id: mypy
      args: [--ignore-missing-imports, --python-version=3.13]
      files: ^backend/
      additional_dependencies:
        - sqlmodel
        - pydantic
        - fastapi
```

Add (inside the existing `local` repo block):
```yaml
- id: local-ty
  name: ty check
  entry: uv run ty check backend/app
  require_serial: true
  language: system
  pass_filenames: false
  files: ^backend/
```

### 3. Fix any new type errors ty surfaces

Run `uv run ty check backend/app` and fix reported issues before committing.

### 4. (Optional) Configure ty in pyproject.toml

```toml
[tool.ty]
# ty reads python-version from requires-python automatically
```

## References

- [ty GitHub repo](https://github.com/astral-sh/ty)
- [ty pre-commit tracking issue #269](https://github.com/astral-sh/ty/issues/269)
- [Upstream full-stack-fastapi-template PR #2227](https://github.com/fastapi/full-stack-fastapi-template/pull/2227) — reference implementation

# prata-sys — Backend

FastAPI + SQLModel + PostgreSQL backend. Uses `uv` for Python package management.

For full local dev setup (Postgres + Mailpit via `compose.dev.yml`, the full app workflow), see [`../development.md`](../development.md).

## Quick start

```bash
# From the project root, boot the dev infra (Postgres + Mailpit) once:
bash scripts/dev-setup.sh

# Then from this directory:
uv sync
uv run fastapi dev app/main.py
```

Open http://localhost:8000/docs for Swagger.

## Where the code lives

- Models: `app/models.py` (SQLModel)
- CRUD: `app/crud.py`
- API routes: `app/api/routes/`
- Settings: `app/core/config.py` (reads `../.env`)
- Migrations: `app/alembic/versions/`

## Tests

```bash
bash scripts/test.sh           # pytest with coverage
bash scripts/tests-start.sh    # pytest only (assumes DB is up)
```

Coverage report lands in `htmlcov/index.html`.

## Migrations (Alembic)

```bash
# Create a new revision after changing models
uv run alembic revision --autogenerate -m "describe the change"

# Apply pending migrations
uv run alembic upgrade head
```

## Email templates

Templates live in `app/email-templates/{src,build}`. Author `.mjml` files in `src/` and export to HTML in `build/` using the [MJML VS Code extension](https://github.com/mjmlio/vscode-mjml).

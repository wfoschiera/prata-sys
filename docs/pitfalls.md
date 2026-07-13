# prata-sys — Known Pitfalls

A growing log of gotchas specific to this stack. Load on demand; the root
[`CLAUDE.md`](../CLAUDE.md) links here from its Conventions section. Add new entries
as you hit them.

## Zod v4 API changes

- Use `error:` instead of `required_error:` in schema params — `required_error` no
  longer exists in Zod v4
- Example: `z.enum(["a", "b"], { error: "Required" })` not `{ required_error: "Required" }`

## React Hook Form + Zod number fields

- Never use `z.coerce.number()` for form fields — it makes the inferred input type
  `unknown`, causing a resolver type mismatch with `useForm<FormData>`
- Instead use `z.number()` and add
  `onChange={(e) => field.onChange(e.target.valueAsNumber)}` on the
  `<input type="number">` element

## SQLModel CRUD imports

- Never use local (inline) imports inside CRUD functions with string annotations like
  `-> "Client"` — mypy cannot resolve forward references to models that are not
  imported at module level
- Always import all models at the top of `crud.py`

## pre-commit mypy hook

- The `mirrors-mypy` pre-commit hook runs in an isolated environment; it must have
  `additional_dependencies` listing `sqlmodel`, `pydantic`, and `fastapi` to
  understand SQLModel table models (`table=True`)
- The hook must also pass `--python-version=3.14` to match the project's Python version

## Python 3.14: HTTP response header names must be valid (no trailing colon)

- Python 3.14 tightened RFC 5322 validation in `email.message` — header field names
  with trailing colons (e.g. `"subject:"`) now raise `ValueError`
- This surfaces as a crash in `httpx` when processing HTTP responses containing such
  headers
- Always use valid header names without trailing colons: `{"subject": value}` not
  `{"subject:": value}`

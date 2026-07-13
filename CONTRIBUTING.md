# Contributing

Thanks for contributing to **prata-sys**. This guide covers the conventions this repo
expects. For agent/AI-assisted work, the same rules live in [`CLAUDE.md`](CLAUDE.md).

## Before you start

- Read the [Development Guide](development.md) to set up your environment (native dev:
  `uv` + `bun`, Docker only for Postgres and Mailpit).
- New here? [`ONBOARDING.md`](ONBOARDING.md) walks through the architecture, repo map,
  and data model.

## Bug workflow (required)

Never start fixing a bug directly:

1. **Open a GitHub issue first** — one issue per bug, describing the problem before any
   code changes.
2. **One branch per issue** — never fix multiple issues on the same branch.
3. **Name the branch** `wfoschiera/<type>/<description>`, where `<type>` is the
   conventional-commit type (`fix` for bugs) and `<description>` is a short kebab-case
   summary — e.g. `wfoschiera/fix/stock-deduction-quantities`.

For non-trivial features, use the [OpenSpec](https://openspec.dev) workflow (`/opsx:*`)
before implementing. Small, obvious changes can go straight to a PR.

## Commits

- **Use [Conventional Commits](https://www.conventionalcommits.org/)** — the
  `/git-commit` skill handles this.
- **Before every commit**, run the linter, type checker, and tests:
  - Backend: `cd backend && bash scripts/lint.sh && bash scripts/test.sh`
  - Frontend: `cd frontend && bun run lint && bun run test`
- Never commit generated artifacts (`htmlcov/`, etc.) — they're already in `.gitignore`.

## Pull requests

1. Keep each PR focused on a single change.
2. Make sure lint, type checks, and tests pass.
3. Update or add tests when changing functionality.
4. Reference the related issue in the PR description.
5. **Add at least one type label** (`feat`, `fix`, `chore`, `refact`, `docs`,
   `upgrade`, `breaking`, `security`, …) — CI requires it. The `/create-pr` skill sets
   this automatically.

## Language policy

- **UI / user-facing text**: Brazilian Portuguese (PT-BR) — labels, messages, toasts,
  placeholders, everything a user sees.
- **Code, comments, commit messages, PR descriptions, and docs**: plain English.

## AI-assisted contributions

This project is developed with AI tooling (Claude Code), so AI assistance is welcome —
just keep meaningful human judgement in the loop: review what you submit, make sure it
builds and passes tests, and don't open PRs you haven't read.

## Questions?

Open a [GitHub issue](https://github.com/wfoschiera/prata-sys/issues).

---
name: git-commit
description: Generate a conventional commit message from staged git changes in the prata-sys monorepo. Use when the user asks to commit, generate a commit message, or stage and commit changes.
---

# Git Commit

## Workflow

1. Run `git diff --staged` to inspect the staged changes.
2. If nothing is staged, run `git status` and ask the user what to stage, or stage all changes with `git add -A` if they say "everything".
3. Determine the **scope** from the affected files (see Scope below).
4. Generate a commit message following the format below.
5. Run `git commit -m "..."` using a HEREDOC to preserve formatting.

## Commit Message Format

```
<type>(<scope>): <short description>

[optional body: why or additional context, if non-obvious]
```

- **type**: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`, `perf`, `ci`, `build`
- **short description**: imperative, lowercase, no period, max ~72 chars
- **body**: only add if the change needs context beyond the title

## Determining Scope

When in doubt, use `git diff --staged --name-only` to list changed files and pick the most specific scope.

## Examples

```
feat(frontend): add react 19 support center section

chore(backend): update shared dependencies

refactor(estoque): simplify token resolution

docs: update contributing guide with staging instructions
```

## Notes

- PRs are squash-merged, so individual commits are free-form — but following conventional commits here keeps history readable during review.
- PR titles (not commit messages) are what CI validates. Match the style anyway.

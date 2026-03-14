# Git Worktrees

## Critical Rules

- **When using worktrees, always use `wt` (Worktrunk)** — don't use raw `git worktree` commands.
- **Project hooks auto-run setup** on new worktrees (install, configure, codegen) — no manual setup needed.

Use [Worktrunk](https://worktrunk.dev) (`wt`) for creating and managing git worktrees. Worktrees provide isolated copies of the repo — useful for parallel tasks, experiments, or working on multiple features without stashing.

## Setup

```bash
# Install shell plugin (enables auto-cd on switch)
wt config shell install
```

*Claude Code users: install the [Worktrunk plugin](https://worktrunk.dev/claude-code/) for integrated worktree management.*

## Usage

```bash
# Create a worktree for a new branch
wt switch --create my-branch

# List active worktrees
wt list

# Switch between worktrees
wt switch my-branch

# Remove a worktree
wt remove my-branch
```

## Project Hooks

Project hooks (`.config/wt.toml`) automatically run setup on new worktrees:

1. `pnpm install` — install dependencies
2. `jus configure` — configure local environment
3. `pnpm nx run-many -t codegen` — generate GraphQL types and other codegen artifacts

This ensures every new worktree is fully functional without manual setup.

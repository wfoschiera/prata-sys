# Git Worktrees

## Critical Rules

- **When using worktrees, always use `wt` (Worktrunk)** — don't use raw `git worktree` commands.
- **Project hooks auto-run setup** on new worktrees (dependency install) — no manual setup needed.

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

Project hooks (`.config/wt.toml`) automatically run `[post-create]` setup on new
worktrees so they're immediately ready to run tests and start the dev server:

1. `cd backend && uv sync` — install backend (Python) dependencies
2. `cd frontend && bun install` — install frontend (JavaScript) dependencies

This ensures every new worktree is fully functional without manual setup.

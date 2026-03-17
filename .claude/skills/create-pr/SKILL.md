---
name: create-pr
description: Create a PR for the current branch
disable-model-invocation: true
---
# Create PR

## Description

This command creates a PR for the current branch.

## Steps

- If there are uncommitted changes in the current branch, abort and ask the user to commit them.
- If there is already a PR opened for the current branch, abort.
- Use the first text after the command as the base branch. If no argument is provided, use `main` as the base branch.
- Check if the current branch is up to date with the base branch. If not, pull the base branch and merge it into the current branch. If the merge has conflicts, abort.
- Generate a PR title and description for the current git diff against the base branch.
- The PR title must follow the conventional commit format: e.g. `feat(frontend): add client dashboard`, `fix(backend): handle CNPJ validation edge case`, `chore(openspec): mark phase tasks complete`. Use a relevant scope like `backend`, `frontend`, `openspec`, or the specific module name.
- Put the description with a brief explanation about the changes.
- The PR must include exactly one label matching the pattern `<type>` or `<type>(<scope>)`. Base types: `feat`, `fix`, `chore`, `refact`, `docs`, `upgrade`, `breaking`, `security`, `bug`, `feature`, `internal`, `lang-all`. The scope is optional and must be lowercase alphanumeric with dashes (e.g. `fix(backend)`, `chore(crud-api)`, `feat(frontend)`). The `check-labels` CI job will fail without a valid label.
- Save the PR title and description in a temporary folder (e.g. `mktemp -d`): e.g. `pr-title.txt` and `pr-description.md`.
- Execute `gh pr create --title "$(cat pr-title.txt)" --body-file pr-description.md --base <BASE_BRANCH> --label <LABEL> --web` to create the PR.
- Do not call `gh pr view` after creating the PR; `gh pr create --web` already opens the PR in the browser.

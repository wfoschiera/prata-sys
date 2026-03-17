---
name: review-pr
description: Reviews PR changes
disable-model-invocation: true
---
# Review PR

Use when the user types /review-pr or asks to review a PR.

## Description

Reviews the PR changes using gh CLI.

## Steps

1. **Determine PR number**: Use the first text after the command as the PR
   number. If none provided, use the current PR number running
   `gh pr view --json number --jq '.number'`.
2. **Fetch diff**: Run `gh pr diff <number>` to get the PR changes (omit
   `<number>` when using current PR).
3. **Analyze changes**: Review the diff and provide:
   - Summary of what changed (files, areas affected)
   - Assessment of correctness and potential issues
   - Check for N+1 queries in any new/modified database operations
   - Verify UI text is in PT-BR and code/comments are in English
   - Check for known pitfalls (Zod v4 `error:` vs `required_error:`, `z.coerce.number()` misuse, SQLModel forward reference imports, Python 3.14 header validation)
    - Verify the PR has a required label matching `<type>` or `<type>(<scope>)` (e.g. `fix`, `chore(backend)`, `feat(frontend)`)
   - Suggestions or concerns, if any
4. After the analysis, ask the developer if they want to comment on the PR.
5. Never comment on the PR, unless the developer explicitly asks for it.
6. When commenting, add a comment specific to the file and line numbers of the
   changes. Also, add a comment with the overall summary of the changes.
7. When the developer asks to review the changes, repeat the steps 2-6.

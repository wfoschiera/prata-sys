---
name: review-locally
description: >
  Reviews changes locally by running git diff against a base branch and
  analyzing the changes.
disable-model-invocation: true
---
# Review PR Locally

Use when the user types /review-locally or asks to review changes locally.

## Description

Reviews the current branch changes against a base branch by examining the git
diff and providing analysis of the modifications.

## Steps

1. **Determine base branch**: Use the first text after the command as the base
   branch. If none provided, use `main` as the base branch.
2. **Run diff**: Execute `git diff <base-branch> .` to get the changes in the
   current workspace.
3. **Analyze changes**: Review the diff and provide:
   - Summary of what changed (files, areas affected)
   - Assessment of correctness and potential issues
   - Check for N+1 queries in any new/modified database operations
   - Verify UI text is in PT-BR and code/comments are in English
   - Check for known pitfalls (Zod v4 `error:` vs `required_error:`, `z.coerce.number()` misuse, SQLModel forward reference imports, Python 3.14 header validation)
   - Suggestions or concerns, if any

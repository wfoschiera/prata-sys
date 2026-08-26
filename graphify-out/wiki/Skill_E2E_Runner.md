# Skill E2E Runner

> 8 nodes · cohesion 0.32

## Key Concepts

- **test-server.ts** (5 connections) — `.claude/skills/gstack/browse/test/test-server.ts`
- **session-runner.ts** (4 connections) — `.claude/skills/gstack/test/helpers/session-runner.ts`
- **skill-e2e.test.ts** (4 connections) — `.claude/skills/gstack/test/skill-e2e.test.ts`
- **startTestServer()** (4 connections) — `.claude/skills/gstack/browse/test/test-server.ts`
- **runSkillTest()** (2 connections) — `.claude/skills/gstack/test/helpers/session-runner.ts`
- **BROWSE_ERROR_PATTERNS** (1 connections) — `.claude/skills/gstack/test/helpers/session-runner.ts`
- **SkillTestResult** (1 connections) — `.claude/skills/gstack/test/helpers/session-runner.ts`
- **FIXTURES_DIR** (1 connections) — `.claude/skills/gstack/browse/test/test-server.ts`

## Relationships

- [[Browser Event Buffers]] (2 shared connections)
- [[Meta Commands Dispatch]] (2 shared connections)

## Source Files

- `.claude/skills/gstack/browse/test/test-server.ts`
- `.claude/skills/gstack/test/helpers/session-runner.ts`
- `.claude/skills/gstack/test/skill-e2e.test.ts`

## Audit Trail

- EXTRACTED: 22 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*

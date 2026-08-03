---
applyTo:
  - "src/**/*"
  - ".claude/rules/**/*"
  - ".claude/skills/**/*"
  - ".claude/settings.json"
excludeFrom:
  - "node_modules/**/*"
  - "vendor/**/*"
priority: high
pathScoping:
  "src/browser/**": ".claude/rules/crawl.md"
  "src/parsers/**": ".claude/rules/preprocess.md"
  "src/tokenization/**": ".claude/rules/preprocess.md"
  "src/llm/**": ".claude/rules/assess.md"
  "src/assessment/**": ".claude/rules/assess.md"
  "src/cli.py": ".claude/rules/cli.md"
  "src/cli/**": ".claude/rules/verify.md"
  "src/storage/**": ".claude/rules/storage.md"
  "src/tui/**": ".claude/rules/tui/"
  "tasks.md": ".claude/rules/multi-agent.md"
---

# Copilot Instructions
Routes to [CLAUDE.md](../CLAUDE.md) and [AGENTS.md](../AGENTS.md).

## Phase-Specific Rules
| Pattern | Rules |
|---------|-------|
| `src/browser/**` | [crawl.md](../.claude/rules/crawl.md) |
| `src/parsers/**`, `tokenization/**` | [preprocess.md](../.claude/rules/preprocess.md) |
| `src/llm/**`, `assessment/**` | [assess.md](../.claude/rules/assess.md) |
| `src/cli.py` | [cli.md](../.claude/rules/cli.md) |
| `src/cli/**` | [verify.md](../.claude/rules/verify.md) |
| `src/storage/**` | [storage.md](../.claude/rules/storage.md) |
| `src/tui/**` | [tui/](../.claude/rules/tui/) |

## Key Constraints
**NEVER:** Assess unconfirmed jobs • Run concurrent assessment (SQLite single-writer) • Send raw HTML to Claude • Commit to `main` (pre-commit blocks)
**ALWAYS:** Show cost estimate before API • Use semantic chunking • Test before commit

## Tool Constraints (Enforced)
**DENIED:** `rm -rf` • `git push --force` • `git reset --hard` • `git clean -fd` • `.env` read/edit
**CONFIRM:** `git push` (normal) • `git rebase` • `.github/*` writes

## Workflow
**Architect** (plan) → **Coder** (implement) → **Reviewer** (verify). Gate 1 + Gate 2 before merge. [AGENTS.md](../AGENTS.md)

**Updated:** 2026-08-02

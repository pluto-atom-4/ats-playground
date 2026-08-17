---
applyTo: '**/*'
model: claude-sonnet-5
context: minimal
---

# Copilot Instructions

Routes to [CLAUDE.md](../CLAUDE.md), [AGENTS.md](../AGENTS.md), and [Constraints](.claude/CONSTRAINTS.md). Path-scoped rules in [.claude/copilot-routing.json](.claude/copilot-routing.json).

**Key Rules:** See [CONSTRAINTS.md](.claude/CONSTRAINTS.md) • Phase rules: [.claude/rules/](.claude/rules/)

**Workflow:** Architect (plan) → Coder (implement) → Reviewer (verify). Gate 1 + Gate 2 before merge.

### WRAP Pattern

**Write** clear requirements in issues. **Refine** with Architect before coding. **Atomic** tasks in Phase 1–4. **Pair** Coder + Reviewer at verification gates.

## Tool Constraints (sync with settings.json)

**Denied (blocked):**
- `Bash(rm -rf *)` – Never recursive delete
- `Bash(git push --force*)` – Never force-push
- `Bash(git reset --hard*)` – Never hard-reset

**Ask (confirm first):**
- `Bash(rm *)` – Delete files
- `Bash(git push *)` – Push any changes
- `Bash(git rebase *)` – Rebase branches
- `Bash(npm *)` – NPM commands

**Updated:** 2026-08-09 (Phase B)

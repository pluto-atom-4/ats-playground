---
applyTo: '**/*'
model: claude-sonnet-5
context: minimal
---

# Copilot Instructions

Global rules for GitHub Copilot IDE completions. Path-scoped rules in [.github/instructions/](instructions/).

**Key References:**
- [CLAUDE.md](../CLAUDE.md) – Project setup, commands, git workflow
- [AGENTS.md](../AGENTS.md) – Agent roles, permissions, model configuration
- [CONSTRAINTS.md](.claude/CONSTRAINTS.md) – Core constraints (NEVER/ALWAYS rules)
- [.claude/rules/](.claude/rules/) – Phase-specific guidance (crawl, preprocess, assess, etc.)
- [.github/instructions/](instructions/) – Instruction files (CLI, code patterns, issue workflow)

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

# Agent Roles & Governance

Multi-agent coordination framework for ATS Playground. Defines role boundaries and escalation.

---

## Agent Roles

### Architect/Planner
- Draft implementation plans (tasks.md)
- Design module boundaries + APIs
- Write architectural decisions
- ✅ Read codebase, write tasks.md + docs/
- ❌ FORBIDDEN: Write production code

### Coder/Implementer
- Implement features, write tests
- Create commits
- Flag design issues to Architect
- ✅ Write src/, tests/, run tests
- ❌ FORBIDDEN: Modify tasks.md, CLAUDE.md, AGENTS.md, skip tests

### Reviewer/Tester
- Verify implementation vs tasks.md
- Run full test suite (pytest, coverage, lint)
- Check test coverage, code quality
- ✅ Read codebase, run verification commands
- ❌ FORBIDDEN: Modify production code, merge without human approval

---

## Claude Model Configuration

**Source of Truth:** `.claude/agents/{role}.md` frontmatter (overrides global default)
**Global Default:** `.claude/settings.json` → `claude-haiku-4-5-20251001`

| Role | Model | Budget | Source |
|------|-------|--------|--------|
| **Architect** | claude-sonnet-5 | Deep planning | `.claude/agents/architect.md` |
| **Coder** | claude-haiku-4-5 | Synthesis | `.claude/agents/coder.md` |
| **Reviewer** | claude-haiku-4-5 | Code review | `.claude/agents/reviewer.md` |
| *Default* | haiku-4-5 | (all others) | `.claude/settings.json` |

**Precedence:** Agent `.md` frontmatter > Global settings.json

Haiku reduces costs ~60% vs Sonnet while maintaining sufficient capability for code review + synthesis.


---

## Two-Gate System

All multi-file changes require **Gate 1 (Plan Review)** + **Gate 2 (Evidence-Based Verification)** before merge.

### Gate 1: Plan Mode Review
Before implementing cross-file changes:
1. Architect drafts tasks.md with API contracts
2. Architect sketches affected files (list + scope)
3. Human/team reviews and approves

Triggered by: module interface changes, config files, CLI changes, schema migrations.

### Gate 2: Evidence-Based Verification
After implementation, Reviewer verifies with **local tools** (not predictions):
- **Tests:** All tests pass (pytest)
- **Linter:** ruff/black pass
- **Type check:** mypy passes
- **Build:** Full build succeeds

Verify with actual tool output, not predictions.

---

## Handover Protocol

```
ARCHITECT → CODER → REVIEWER → HUMAN (merge)
```

**Approval gates:** Gate 1 (plan) before code → Gate 2 (verification) before merge


---

## Directory Scoping Map

| Path | Owner | Purpose | Example |
|------|-------|---------|---------|
| `.claude/rules/*.md` | Claude Code | Phase-specific guidance (crawl, preprocess, assess, storage) | `crawl.md`: Playwright patterns + rate limiting |
| `.github/copilot/rules/` | GitHub Copilot | IDE context, real-time completions, coding conventions | (future: language-specific rules) |
| `.claude/skills/<name>/` | Custom skills | Lazy-loaded specialized workflows, project-specific automation | `pre-commit-enforce/`: Feature branch protection |
| `.claude/agents/*.md` | Agent config | Model + tool overrides per role (Architect, Coder, Reviewer) | `architect.md`: sonnet-5 model override |
| `.github/instructions/` | Documentation | CLI usage, issue workflows, GitHub-specific patterns | `cli-usage.instructions.md`: Command reference |

**Rule Priority**: Agent `.md` frontmatter > `.claude/settings.json` > GitHub defaults

---

## Claude ↔ Copilot Handoff

**When to use Copilot (IDE):**
- Single-file edits or completions
- Quick fixes, refactoring within module boundaries
- Real-time inline suggestions
- Exploratory coding

**When to escalate to Claude Code:**
- Multi-file refactors (scope >3 files)
- Cross-module API changes
- Complex planning or architecture decisions
- Cost-sensitive operations (use haiku model)
- Verification + testing workflows

**Escalation Rule**: If scope exceeds 3 files OR touches `.claude/`, `AGENTS.md`, `CLAUDE.md`, switch to Claude Code.

**Return to Copilot**: After Claude Code planning approved, Coder can implement single-phase tasks in IDE (non-blocking).

---

## Skill Discovery

Custom skills in `.claude/skills/<skill-name>/` use YAML metadata for lazy-loading. See `.claude/skills/<skill>/SKILL.md` for examples.


---

## Permission Matrix

| Role | tasks.md | src/ | tests/ | docs/ | CLAUDE.md | .claude/ |
|------|----------|------|--------|-------|-----------|----------|
| Architect | W | R | R | W | R | R |
| Coder | R | W | W | R | ❌ | ❌ |
| Reviewer | R | R | R | W | R | R |
| Human | R | R | R | R | W | W |

**W** = write, **R** = read, **❌** = denied. Configuration in `.claude/agents/` overrides this matrix.


---

## Related

- **Agent Tool Configuration:** `.claude/agents/` files define tool permissions and models per role (source-of-truth for tool access)
- **Phase Coordination:** See `.claude/rules/multi-agent.md` for phase-specific handoffs
- **CLAUDE.md:** Project setup, commands, git workflow
- **DESIGN.md:** Architecture decisions

---

**Last Updated:** 2026-08-22
**Status:** P2 complete (Issue #288): Consolidated 3 model sources → single source of truth; deleted invalid profiles.json; tightened permission deny lists

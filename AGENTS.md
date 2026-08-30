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
Reviewer verifies with local tools (not predictions): pytest ✅, ruff/black ✅, mypy ✅, build ✅

---

## Handover Protocol

```
ARCHITECT → CODER → REVIEWER → HUMAN (merge)
```

**Approval gates:** Gate 1 (plan) before code → Gate 2 (verification) before merge


---

## Directory Scoping Map

| Path | Owner | Purpose |
|------|-------|---------|
| `.claude/rules/*.md` | Claude Code | Phase-specific guidance (crawl, preprocess, assess) |
| `.claude/skills/<name>/` | Custom skills | Lazy-loaded project workflows |
| `.claude/agents/*.md` | Agent config | Model + tool overrides per role |
| `.github/copilot/rules/` | GitHub Copilot | IDE completions, conventions |
| `.github/instructions/` | Documentation | CLI usage, issue workflows |

**Rule Priority**: Agent `.md` frontmatter > `.claude/settings.json` > GitHub defaults

---

## Claude ↔ Copilot Handoff

**Copilot (IDE)**: Single-file edits, quick fixes, real-time suggestions

**Claude Code**: Multi-file refactors (>3 files), cross-module changes, complex planning, verification

**Escalation Rule**: If scope exceeds 3 files OR touches `.claude/`, `AGENTS.md`, `CLAUDE.md`, use Claude Code.

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

**Related:** [CLAUDE.md](CLAUDE.md) • [DESIGN.md](DESIGN.md) • [.claude/rules/multi-agent.md](.claude/rules/multi-agent.md)

**Last Updated:** 2026-08-30 (Issue #305: Scoping map + handoff rules)

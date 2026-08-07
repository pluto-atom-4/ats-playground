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

## Claude Tier Configuration

| Role | Model |
|------|-------|
| **Architect** | claude-sonnet-5 |
| **Coder** | claude-haiku-4.5 |
| **Reviewer** | claude-haiku-4.5 |

Haiku for reviewers reduces costs ~60% while maintaining sufficient capability.


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

**Last Updated:** 2026-08-06
**Status:** Enhanced with model selection clarity and permission boundaries; Issue #235 addressed

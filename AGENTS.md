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
- ❌ FORBIDDEN: Modify tasks.md, CLAUDE.md, skip tests

### Reviewer/Tester
- Verify implementation vs tasks.md
- Run full test suite (pytest, coverage, lint)
- Check test coverage, code quality
- ✅ Read codebase, run verification commands
- ❌ FORBIDDEN: Modify production code, merge without human approval

---

## Two-Gate System

All multi-file changes require **Gate 1 (Plan Review)** + **Gate 2 (Evidence-Based Verification)** before merge.

### Gate 1: Plan Mode Review
Before implementing cross-file changes:
1. Architect drafts tasks.md with API contracts
2. Architect sketches affected files (list + scope)
3. Human/team reviews plan
4. Approval required before code touch

**Examples triggering Gate 1:**
- Refactoring module interfaces
- Adding new config files (AGENTS.md, CLAUDE.md, .claude/settings.json)
- Cross-phase CLI changes
- Database schema migrations

### Gate 2: Evidence-Based Verification
After implementation, Reviewer verifies with **local tools** (not predictions):
- **LSP:** Type errors in affected files
- **Tests:** All new + changed tests pass
- **Linter:** ruff/black pass on changed files
- **Build:** Full build succeeds (uv sync, pytest)
- **Logs:** Check CI workflow output for failures

**Examples of evidence:**
- ✅ "pytest passed: 47 tests" (not "looks correct")
- ✅ "ruff check: 0 errors" (not "style should be fine")
- ✅ "mypy --strict: 0 errors" (not "types look right")

**Invalid (predictions, no evidence):**
- ❌ "Should work because X" (no test run)
- ❌ "This file looks right" (no linter check)
- ❌ "No breaking changes" (no verification tool)

---

## Handover Protocol

```
ARCHITECT (plan + Gate 1 review)
    ↓ tasks.md + approval
CODER (implement + test)
    ↓ PR + commits
REVIEWER (Gate 2: verify with tools)
    ↓ approval/feedback with evidence
HUMAN (merge decision)
```

**Checklist:**
- [ ] tasks.md complete and approved (Gate 1)
- [ ] Coder implements, writes tests
- [ ] All tests passing (pytest, coverage, lint)
- [ ] Reviewer verifies with local tools (Gate 2)
- [ ] Human merges PR

---

## Skill Discovery

Custom skills in `.claude/skills/<skill-name>/` use standardized **YAML metadata** for lazy-loading.

**Metadata fields (SKILL.md frontmatter):**
- `name`, `description`, `dependencies`, `phases`, `cost_estimate`, `execution`, `triggers`

See `.claude/skills/<skill>/SKILL.md` for examples (crawl-jobs, assess-jobs, pre-commit-enforce).

---

## Permission Matrix

| Role | tasks.md | src/ | tests/ | docs/ | CLAUDE.md | .claude/ |
|------|----------|------|--------|-------|-----------|----------|
| Architect | W | R | R | W | R | R |
| Coder | R | W | W | R | R | R |
| Reviewer | R | R | R | W | R | R |
| Human | R | R | R | R | W | W |

**W** = write, **R** = read

---

## Related

- **Phase Coordination:** See `.claude/rules/multi-agent.md` for phase-specific handoffs
- **CLAUDE.md:** Project setup, commands, git workflow
- **DESIGN.md:** Architecture decisions

---

**Last Updated:** 2026-08-01
**Status:** Condensed for token budget compliance; Phase 5-7 enhancements documented

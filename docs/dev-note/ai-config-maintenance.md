# AI Configuration File Maintenance Guide

Automated validation + manual checklist for Claude Code / Copilot CLI configuration files.

---

## Overview

This project maintains several config files for cross-tool compatibility:
- **CLAUDE.md** – Claude Code project instructions
- **AGENTS.md** – Multi-agent governance, role permissions
- **.claude/settings.json** – Claude Code harness settings (hooks, permissions)
- **.github/copilot-instructions.md** – GitHub Copilot Agent Mode guidance
- **.claude/skills/*/SKILL.md** – Skill metadata (lazy-loading for both tools)

**CI Validation:** `.github/workflows/config-validation.yml` runs on every commit to config files.

---

## Token Budget Management

### Current Thresholds
- **CLAUDE.md:** Max 250 lines (currently ~110, 44% used)
- **AGENTS.md:** Max 200 lines (currently ~160, 80% used)
- **.github/copilot-instructions.md:** Max 300 lines (currently ~110, 37% used)

### Auto-Compact Trigger
When total context approaches 50% budget:
1. Archive old memory files (move to `docs/archive/`)
2. Consolidate redundant sections
3. Increase external references (link to `.claude/rules/` subdocs)

Threshold: **80K tokens** used across CLAUDE.md + AGENTS.md + settings.json metadata.

---

## Maintenance Checklist (Monthly)

### File Validation
- [ ] Run `config-validation.yml` locally (or PR triggers automatically)
- [ ] Verify all JSON files parse without errors
- [ ] Check YAML frontmatter in copilot-instructions.md
- [ ] Confirm all SKILL.md files have metadata fields:
  - `name`, `description`, `dependencies`, `phases`, `cost_estimate`

### Content Review
- [ ] CLAUDE.md still under 250 lines
- [ ] AGENTS.md still under 200 lines (consider splitting if over)
- [ ] copilot-instructions.md still under 300 lines
- [ ] All referenced files exist (e.g., `.claude/rules/` subdocs)
- [ ] Cross-document links work (e.g., @AGENTS.md in CLAUDE.md)

### Hook & Permission Sync
- [ ] `.claude/settings.json` PreToolUse guards match tool constraints in copilot-instructions.md
- [ ] Destructive commands blocked consistently (rm -rf, git push --force, etc.)
- [ ] PostToolUse hooks running on file edits (black, ruff)
- [ ] Network allowlist includes all needed domains (anthropic, github, pypi)

### Skill Metadata
- [ ] All skills in `.claude/skills/` have SKILL.md with full frontmatter
- [ ] Phases field matches actual workflow (crawl, preprocess, verify, assess, export)
- [ ] Dependencies listed (Playwright, spaCy, anthropic, etc.)
- [ ] Cost estimates realistic and updated if pricing changes

---

## When to Update

### CLAUDE.md
- **Trigger:** New CLI commands, changed setup steps, git workflow updates
- **Process:**
  1. Edit locally
  2. Verify line count < 250
  3. Test `uv run python -m src.cli --help`
  4. Commit with message: "docs: update CLAUDE.md (setup/commands)"

### AGENTS.md
- **Trigger:** New agent roles, permission changes, governance updates
- **Process:**
  1. Edit locally
  2. Update permission matrix if needed
  3. Verify line count < 200 (split if necessary)
  4. Commit: "docs: update AGENTS.md (role definitions)"

### .claude/settings.json
- **Trigger:** New permissions needed, hook patterns, sandbox rules
- **Process:**
  1. Edit locally
  2. Validate: `python3 -m json.tool .claude/settings.json`
  3. Test hooks manually (e.g., edit a file, verify black runs)
  4. Commit: "config: update .claude/settings.json (hooks/perms)"

### .github/copilot-instructions.md
- **Trigger:** Tool constraint changes, new patterns, Copilot CLI updates
- **Process:**
  1. Edit locally
  2. Update tool matrix in sync with settings.json denies/asks
  3. Keep under 300 lines
  4. Commit: "docs: update copilot-instructions (tool matrix)"

### .claude/skills/*/SKILL.md
- **Trigger:** New dependencies, phase changes, cost updates
- **Process:**
  1. Edit frontmatter only (metadata)
  2. Update cost_estimate if API pricing changes
  3. Add/remove phases if workflow evolves
  4. Commit: "feat: update skill metadata (crawl-jobs: add phase)"

---

## Testing Changes

### Before Merge
```bash
# Validate all config files
bash .github/workflows/config-validation.yml  # Or run via CI

# Check line counts
wc -l CLAUDE.md AGENTS.md .github/copilot-instructions.md

# Test CLAUDE.md commands
uv run python -m src.cli --help

# Verify hooks work
bash .claude/hooks/post-edit-quality.sh  # Manual test

# Check JSON syntax
python3 -m json.tool .claude/settings.json
```

### CI Validation
Config validation runs automatically on PR:
- JSON schema checks
- YAML frontmatter validation
- Hook pattern matching
- Line count limits
- Cross-file reference checks

If CI fails, fix issues before merge.

---

## Artifact Checklist (Per-File)

### CLAUDE.md
- [ ] Under 250 lines
- [ ] @AGENTS.md reference on line 1-2
- [ ] All build/test/lint commands up-to-date
- [ ] Context management directives clear
- [ ] References to .claude/rules/ accurate

### AGENTS.md
- [ ] Under 200 lines (or split into subfiles)
- [ ] Two-Gate System clearly explained
- [ ] Skill Discovery section + template present
- [ ] Permission matrix accurate
- [ ] Phase coordination doc referenced

### .claude/settings.json
- [ ] Valid JSON (no parse errors)
- [ ] PreToolUse guards all destructive ops
- [ ] PostToolUse hooks working (quality checks)
- [ ] Network allowlist complete
- [ ] Model + role overrides correct

### .github/copilot-instructions.md
- [ ] Under 300 lines
- [ ] YAML frontmatter present (applyTo, priority)
- [ ] Tool constraints matrix readable
- [ ] Sections align with CLAUDE.md structure
- [ ] References to .claude/rules/ correct

### .claude/skills/*/SKILL.md
- [ ] Frontmatter has: name, description, dependencies, phases, cost_estimate
- [ ] Phases match actual workflow
- [ ] Dependencies listed with versions (e.g., "playwright >= 1.40")
- [ ] Triggers array searchable
- [ ] Execution type set (atomic, streaming, queued)

---

## Emergency: Token Budget Crisis

If context grows beyond 80K tokens:

1. **Archive old files:** Move stale docs to `docs/archive/`
2. **Consolidate:** Merge AGENTS.md Phase Coordination into multi-agent.md
3. **Link out:** Replace long sections with external references
4. **Compress:** Use abbreviations (TUI → TextUI, LLM → Claude, etc.)
5. **Split:** Move AGENTS.md to .claude/agents/ subdirectory if >200 lines

After crisis fix, run `config-validation.yml` to confirm recovery.

---

## Monitoring

**Automated:**
- CI validates on every commit to config files
- Config-validation.yml reports line counts and hook status
- Pre-commit hook (if enabled) catches JSON errors locally

**Manual:**
- Monthly checklist review (see above)
- Quarterly cross-tool sync audit
- Bi-annual token budget review

---

## Related Files

- **CI Workflow:** `.github/workflows/config-validation.yml`
- **Hook Scripts:** `.claude/hooks/post-edit-quality.sh`
- **Phase Rules:** `.claude/rules/` (crawl, preprocess, assess, etc.)
- **Skill Definitions:** `.claude/skills/*/SKILL.md`

---

**Last Updated:** 2026-07-25
**Maintainer:** Architecture team
**Frequency:** Monthly checklist, quarterly audit

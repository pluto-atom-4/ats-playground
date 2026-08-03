# Skill Template

Reference template for creating new Claude Code skills. All skills must follow this structure.

---

## YAML Frontmatter (Required)

```yaml
---
name: skill-name
description: Brief description of what skill does (1 line)
dependencies:
  - "package >= version"
  - "another-package >= version"
phases:
  - phase-name
cost_estimate: "Cost or free estimate"
execution: atomic|streaming
triggers:
  - "trigger phrase 1"
  - "trigger phrase 2"
  - "alternative phrasing"
allowed_tools:
  - Read
  - Bash(specific-cmd *)
  - Write
---
```

**Fields:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | ✅ | string | kebab-case slug (becomes `/skill-name`) |
| `description` | ✅ | string | One-line summary (visible in skill index) |
| `dependencies` | ✅ | array | Required packages/tools |
| `phases` | ✅ | array | Pipeline phases this skill covers |
| `cost_estimate` | ✅ | string | "$X-Y per unit" or "$0.00 (free)" |
| `triggers` | ✅ | array | Natural language phrases that invoke skill |
| `execution` | ✅ | enum | `atomic` (runs to completion) or `streaming` (long-running) |
| `allowed_tools` | ✅ | array | Explicit tool boundaries (not inherited from role) |

---

## Frontmatter Examples

**Crawl Skill (Playwright automation):**
```yaml
---
name: crawl-jobs
description: Fetch job listings via Playwright
phases: [crawl, preprocess]
cost_estimate: "$0.00 (local)"
execution: atomic
triggers:
  - "crawl jobs"
  - "fetch career pages"
allowed_tools:
  - Read
  - Bash(uv run *)
  - Bash(python *)
---
```

**Assess Skill (API calls):**
```yaml
---
name: assess-jobs
description: Run Claude assessment for CV fit
phases: [assess, verify]
cost_estimate: "$0.50-5.00 per 100 jobs"
execution: streaming
triggers:
  - "assess candidates"
  - "score jobs"
allowed_tools:
  - Read
  - Bash(uv run *)
---
```

**Pre-Commit Skill (Git hooks):**
```yaml
---
name: pre-commit-enforce
description: Block commits to protected branches
phases: [meta]
cost_estimate: "$0.00 (hook)"
execution: atomic
triggers:
  - "enforce branch protection"
allowed_tools:
  - Read
  - Write
  - Bash(git *)
---
```

---

## Content Structure (After Frontmatter)

### 1. Overview (50–100 words)
What does the skill do? What problem does it solve?

```markdown
## Workflow: [Name]

Brief description of what runs and why.
```

### 2. Prerequisites
Dependencies, setup, environment vars.

```markdown
### Prerequisites

```bash
# Commands to install/configure
uv sync
export VAR=value
```
```

### 3. Step-by-Step Execution
Clear numbered steps with code blocks.

```markdown
### Step 1: [Action]

Brief description.

```bash
command
```
```

### 4. Verification
How to verify the skill ran correctly.

```markdown
### Verification

```bash
# Test commands
pytest tests/
```
```

### 5. Troubleshooting
Common errors + fixes.

```markdown
### Troubleshooting

**Error X:** Solution
```

### 6. Related Skills/Documentation
Links to connected skills or docs.

```markdown
### Related

- [[skill-name]] – Prerequisite
- [docs/](docs/) – Architecture
```

---

## Tool Boundaries (allowed_tools)

Define explicit tools each skill can use. Inherited from role permissions, but skill can be more restrictive.

**Examples:**

```yaml
# Read-only skill
allowed_tools:
  - Read
  - Bash(grep *)

# Full autonomy (rare)
allowed_tools:
  - Read
  - Edit
  - Write
  - Bash(*)

# Restricted to one tool
allowed_tools:
  - Bash(python *)
```

**Patterns:**

- `Read` – Read any file
- `Bash(uv run *)` – Only `uv run` subcommands
- `Bash(git *)` – Only git commands
- `Write` – Write any file
- `Edit` – Edit existing files

---

## Validation Checklist

Before publishing new skill:

- [ ] YAML frontmatter present and valid
- [ ] `name`, `description`, `phases`, `triggers` filled in
- [ ] `allowed_tools` explicitly defined (not empty)
- [ ] `cost_estimate` included
- [ ] No hardcoded API keys or secrets
- [ ] Markdown renders without errors
- [ ] Links to prerequisites are valid
- [ ] Troubleshooting section covers common errors
- [ ] Related skills/docs linked
- [ ] Tested locally (runs to completion without errors)

---

## File Location

```
.claude/skills/[skill-name]/
├── SKILL.md          (this file structure)
├── setup.sh          (optional: installation)
└── docs/             (optional: detailed guides)
    ├── architecture.md
    ├── examples.md
    └── faq.md
```

---

## See Also

- **AGENTS.md** – Agent roles + permissions
- **CLAUDE.md** – Project instructions
- **DESIGN.md** – Architecture decisions
- Existing skills: `crawl-jobs/`, `assess-jobs/`, `pre-commit-enforce/`

---

**Version:** 1.0
**Last Updated:** 2026-08-02
**Status:** Reference template for Phase 1 config tuning

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

# GitHub Copilot Instructions

Copilot integration for ATS Playground. Routes to modular phase guidance in `.claude/rules/`.

For detailed context, see [CLAUDE.md](../CLAUDE.md) and [AGENTS.md](../AGENTS.md).

---

## Phase-Specific Rules

Each phase has dedicated guidance. Copilot loads rules matching your current file:

| File Pattern | Phase | Rules | Guidance |
|--------------|-------|-------|----------|
| `src/browser/**` | Crawl | [crawl.md](../.claude/rules/crawl.md) | Playwright, CSS selectors, rate limiting |
| `src/parsers/**` | Preprocess | [preprocess.md](../.claude/rules/preprocess.md) | HTML cleaning, token counting |
| `src/tokenization/**` | Preprocess | [preprocess.md](../.claude/rules/preprocess.md) | Chunking, token estimation |
| `src/llm/**` | Assess | [assess.md](../.claude/rules/assess.md) | Claude API, retries, cost tracking |
| `src/cli.py` | CLI | [cli.md](../.claude/rules/cli.md) | Typer commands, async patterns |
| `src/cli/**` | Verify | [verify.md](../.claude/rules/verify.md) | Interactive flows, status tracking |
| `src/storage/**` | Storage | [storage.md](../.claude/rules/storage.md) | SQLite, FTS5, schema design |
| `src/tui/**` | TUI | [tui/](../.claude/rules/tui/) | Textual, async, state management |

**Find the right file → read the linked `.claude/rules/` guide → implement following patterns.**

---

## Quick Setup

```bash
uv sync && uv run python -m spacy download en_core_web_md && uv run playwright install
cp .env.example .env  # Set ANTHROPIC_API_KEY
uv run python -m src.cli all --cv data/cv.json --config config/companies.json
```

Full commands: [CLAUDE.md](../CLAUDE.md)

---

## Key Constraints

**NEVER:**
- Assess unconfirmed jobs (use `--confirmed-only`)
- Run concurrent assessment processes (SQLite single-writer)
- Send raw HTML to Claude (preprocess first)
- Skip verification step
- Commit directly to `main` (pre-commit hook blocks)

**ALWAYS:**
- Show cost estimate before API calls
- Use semantic chunking (spaCy sentences, not tokens)
- Test before commit (`pytest`, `ruff check`)
- Link to phase-specific rules in `.claude/rules/`

See [CLAUDE.md § NEVER DO THIS](../CLAUDE.md#never-do-this) for full constraints.

---

## Tool Constraints (Enforced)

The following dangerous operations are **DENIED**:
- `rm -rf` – Recursive file deletion forbidden
- `git push --force` – Force push forbidden
- `git reset --hard` – Hard reset forbidden
- `git clean -fd` – Force clean forbidden
- `.env` read/edit – Credentials protection

Request user confirmation for:
- `git push` – Normal (non-force) push
- `git rebase` – Interactive rebasing
- `.github/*` write operations
- `npm`/`yarn` package manager

---

## Roles & Handoff

**Architect** (plan) → **Coder** (implement) → **Reviewer** (verify)

Gate 1 (plan approval) + Gate 2 (evidence-based verification) before merge.

See [AGENTS.md](../AGENTS.md) for role boundaries and permissions.

---

## Skills

Modular workflows in `.claude/skills/`:
- **crawl-jobs** – Fetch listings + preprocess
- **assess-jobs** – Review + assess with cost transparency
- **pre-commit-enforce** – Git workflow enforcement

See [.claude/skills/TEMPLATE.md](../.claude/skills/TEMPLATE.md) for creating new skills.

---

## Testing

```bash
bash .claude/scripts/run-local-ci.sh              # Pre-commit checks
uv run pytest tests/ -v --cov=src               # Full test suite
uv run pytest tests/ -v --cov=src --strict      # With mypy
```

---

**Last Updated:** 2026-08-02
**Status:** Integrated with modular phase rules & path-scoping

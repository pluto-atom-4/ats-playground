---
applyTo:
  - "src/**/*"
  - ".claude/rules/**/*"
  - ".claude/skills/**/*"
excludeFrom:
  - "node_modules/**/*"
  - "vendor/**/*"
priority: high
---

# Copilot Instructions for ATS Playground

Auto-loaded guidance for GitHub Copilot. See [CLAUDE.md](../CLAUDE.md) for core rules.

---

## Quick Reference

**Setup:**
```bash
uv sync && uv run python -m spacy download en_core_web_md && uv run playwright install
cp .env.example .env  # Set ANTHROPIC_API_KEY
```

**Full Workflow:**
```bash
uv run python -m src.cli --all --cv data/cv.json --config config/companies.json
```

See CLAUDE.md for complete command list.

---

## Architecture

6-phase pipeline: CONFIG → CRAWL → PREPROCESS → VERIFY → ASSESS → EXPORT

**Key Design:** Local preprocessing reduces LLM costs 80–90%.

| Phase | Purpose | Rules |
|-------|---------|-------|
| Crawl | Playwright automation | [crawl.md](../.claude/rules/crawl.md) |
| Preprocess | HTML cleaning, NLP, tokens | [preprocess.md](../.claude/rules/preprocess.md) |
| Verify | Interactive review + cost | [verify.md](../.claude/rules/verify.md) |
| Assess | Claude scoring | [assess.md](../.claude/rules/assess.md) |
| Storage | SQLite + FTS5 | [storage.md](../.claude/rules/storage.md) |

Full architecture: [DESIGN.md](../DESIGN.md)

---

## Key Patterns

1. **Semantic Chunking** – Split at sentences (spaCy), not random tokens
2. **Token Transparency** – Show cost before LLM calls
3. **MarkItDown Primary** – HTML cleaning with BeautifulSoup fallback
4. **User Confirmation** – Verify before assessment
5. **SQLite + FTS5** – Fast local search; no external DB
6. **Claude 3.5 Sonnet** – Rate limits + exponential backoff
7. **Typer Async CLI** – Type hints, sub-commands, async patterns

---

## Files

**Core:**
- CLAUDE.md – Quick workflows, git, setup
- AGENTS.md – Roles (Architect, Coder, Reviewer)
- DESIGN.md – Architecture decisions

**Detailed:**
- .claude/rules/ – Phase-specific patterns
- .claude/rules/tui/ – Text UI (Textual framework)
- .github/instructions/ – CLI usage, code patterns

---

## Testing

```bash
uv run pytest tests/ -v --cov=src  # All tests
uv run black src/ && uv run ruff check src/ --fix  # Format + lint
tail -f logs/app.log  # Watch logs
```

See [CLAUDE.md § Verification Commands](../CLAUDE.md#verification-commands) for details.

---

## Tool Constraints Matrix

| Tool | Constraint | Reason |
|------|-----------|--------|
| `rm -rf` | **DENY** | Destructive; use `git clean` or `rm` (single file) |
| `git push --force` | **ASK** | Risk of overwriting upstream; blocked except explicit approval |
| `git reset --hard` | **ASK** | Destroys uncommitted work; use `git restore` or `git stash` |
| `git rebase -i` | **ALLOW** | OK on feature branches; interactive rebase is safe locally |
| `pytest` | **ALLOW** | Always encouraged; verify before commits |
| `black` / `ruff` | **ALLOW** | Auto-run via PostToolUse hook on file edits |
| `uv sync` | **ALLOW** | Safe; updates lock file only if needed |
| `.env` edits | **DENY** | Secrets; manual process only |

**Policy:**
- **ALLOW:** Safe, reversible, encouraged (tests, linters, format)
- **ASK:** Risky, prompt user for confirmation (git force, destructive ops)
- **DENY:** Never auto-execute; manual intervention only (secrets, destructive bulk ops)

---

## Roles & Governance

**Architect:** Design, write tasks.md, read-only codebase
**Coder:** Implement, write tests, create PRs
**Reviewer:** Verify tests, check quality, approve/block

See [AGENTS.md](../AGENTS.md) for details.

---

**Last Updated:** 2026-07-25
**Status:** Enhanced with path-scoped rules & tool matrix

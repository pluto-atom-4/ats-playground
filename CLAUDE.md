# CLAUDE.md

@AGENTS.md

ATS Playground: CV-to-jobs assessment system. Crawls career pages, preprocesses HTML, sends to Claude for scoring.

**See [Core Constraints](.claude/CONSTRAINTS.md) for NEVER/ALWAYS rules.**

---

## Git Workflow & CI

Feature branches enforced. Pre-commit runs ruff, mypy, secrets.

```bash
git checkout -b feat/issue-XXX-description
bash .claude/scripts/run-local-ci.sh          # Pre-commit checks
bash .claude/scripts/run-local-ci.sh --tests  # Include tests
```

Setup: `bash .claude/skills/pre-commit-enforce/setup.sh`.

---

## Setup

```bash
uv sync
uv run python -m spacy download en_core_web_md
uv run playwright install chromium
cp .env.example .env  # Set ANTHROPIC_API_KEY
uv run python src/storage/db.py --init
```

---

## Quick Workflow

```bash
# Full pipeline (Sonnet, $3/$15 per 1M)
uv run python -m src.cli all --cv data/cv.json --config config/companies.json

# Cheaper version (Haiku, $0.80/$4 per 1M)
uv run python -m src.cli all --cv data/cv.json --config config/companies.json --model haiku

# Stop before assess (cost verify)
uv run python -m src.cli all --cv data/cv.json --config config/companies.json --up-to review
```

**HTML Preprocessing:** Phases 1-4 complete (Issue #230). See [DESIGN.md](DESIGN.md) for details. [CLI reference](.github/instructions/cli-usage.instructions.md).

---

## Verification Commands

```bash
bash .claude/scripts/run-local-ci.sh              # Pre-commit checks + mypy
uv run pytest tests/ -v                          # All tests
uv run pytest tests/ -v --cov=src               # With coverage
uv run python -m src.cli query --keyword "python" --min-score 75  # Query DB
uv run python -m src.cli stats --show-token-usage              # Cost breakdown
tail -f logs/app.log                             # Watch logs
```

---

## Reference

**Docs**: [Constraints](.claude/CONSTRAINTS.md) • [Architecture](DESIGN.md) • [Rules](.claude/rules/) • [CLI](.github/instructions/cli-usage.instructions.md) • [Agents](AGENTS.md)

**Effort Tuning:** [Local Overrides](docs/dev-note/ai-config-maintenance.md#local-overrides-claudesettingslocaljson) – set `CLAUDE_CODE_EFFORT_LEVEL`, `MAX_THINKING_TOKENS` per session

**Updated**: 2026-08-16 (Phase 2 residual gaps)

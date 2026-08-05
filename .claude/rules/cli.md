# CLI Phase Rules

Typer command patterns, sub-command organization, async orchestration, help text.

## Typer Command Structure

**Sub-apps for phase organization:**

```python
# In src/cli.py
from typer import Typer

app = Typer()

@app.command()
def crawl(
    config: str = typer.Option(..., help="Config file path"),
) -> None:
    """Crawl job listings from configured companies."""
    logger.info(f"Crawling with config: {config}")
    # implementation
```

**All commands must include:**
- Docstring (visible in `--help`)
- Type hints on all parameters
- `typer.Option()` or `typer.Argument()` for CLI clarity
- Logging of key actions

## Phase Commands

| Command | Purpose |
|---------|---------|
| `crawl` | Fetch raw HTML from career pages |
| `preprocess` | Clean HTML (with consolidated clean_html + 70+ boilerplate patterns), chunk text, count tokens |
| `review` | Interactive verification before LLM |
| `assess` | Claude API evaluation of CV fit |
| `export` | Generate markdown reports |
| `query` | Search database by keyword/score |
| `stats` | Show token usage analytics |

**Preprocessing Pipeline (Issue #230 + #231):**
The `preprocess` command uses consolidated `clean_html()` with 70+ boilerplate patterns (7 categories) and 3-tier fallback chain (MarkItDown → BeautifulSoup → Original HTML). Ensures robustness: preprocessing never fails catastrophically.

**Full workflow (single config):**
```bash
uv run python -m src.cli --all --cv data/cv.json --config config/companies.json
```

**Full workflow (directory):**
```bash
uv run python -m src.cli --all --cv data/cv.json --config-dir ./config
```

## Async Patterns

**Use async for concurrent crawling:**

```python
import asyncio

@app.command()
async def crawl(...) -> None:
    async with BrowserManager() as browser:
        tasks = [browser.fetch_jobs(cfg) for cfg in configs]
        results = await asyncio.gather(*tasks)
```

**Don't use sync/async mix.** If any step is async, entire command should be.

## Help Text Guidelines

- One-line docstring: what it does (visible in `--help`)
- `help=` parameter on each option: why user needs this
- Example: `help="Config file (JSON with selectors, delays)"`

## Error Handling

- **Log all errors** before raising
- **Fail fast**: If config invalid, exit immediately
- **Show user-friendly messages**: "Config file not found: ./config/companies.json"
- **Exit codes**: 0 (success), 1 (user error), 2 (internal error)

## Verification Commands

```bash
# Test command help
uv run python -m src.cli --help
uv run python -m src.cli crawl --help

# Preprocess with token estimates
uv run python -m src.cli preprocess --show-estimates

# Dry-run (if supported)
uv run python -m src.cli crawl --config config/companies.json

# Watch logs
tail -f logs/app.log
```

## Preprocessing Version Tracking (Phase 2 – IMPLEMENTED)

**Overview:** Phase 2 (Issue #230) adds `preprocessing_version` column to `job_reviews` table for version tracking:
- `v1.0` – Legacy (no boilerplate removal)
- `v2.0` – New (70+ boilerplate patterns removed, 3-tier fallback)

**CLI Flags:**
```bash
# Show preprocessing version statistics
uv run python -m src.cli preprocess --show-version-stats

# Force specific version (default 2.0)
uv run python -m src.cli preprocess \
  --cv data/cv.json \
  --preprocessing-version 2.0

# Re-preprocess only legacy v1.0 jobs to v2.0
uv run python -m src.cli preprocess \
  --cv data/cv.json \
  --re-preprocess-only-v1
```

**Use Cases:**
1. **Selective re-preprocessing**: Query old jobs, update to new pipeline
2. **Cost analysis**: Compare token usage across versions
3. **Gradual rollout**: Process subset with v2.0, compare results before bulk update
4. **Backward compatibility**: Old jobs queryable by version, revert if issues arise

**Implementation (Tasks 1-6 merged):**
- Schema: `preprocessing_version TEXT DEFAULT 'v2.0'` in `job_reviews` table with migration support
- JobStore API: `update_preprocessing_version()`, `get_jobs_by_version()`, `get_version_stats()`
- CLI integration: Version flags + version stats reporting
- Backward compatibility: All queries work regardless of version; migration marks existing jobs as v1.0

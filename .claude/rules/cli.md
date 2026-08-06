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
| `preprocess` | Clean HTML, chunk text, count tokens |
| `review` | Interactive verification before LLM |
| `assess` | Claude API evaluation of CV fit |
| `export` | Generate markdown reports |
| `query` | Search database by keyword/score |
| `stats` | Show token usage analytics |

See [CLI Usage](.../instructions/cli-usage.instructions.md) for full command reference.


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

## Preprocessing Version Tracking

Tracks preprocessing pipeline versions in `job_reviews.preprocessing_version` (default: `v2.0`).

**Versions:**
- `v1.0` – Legacy (no boilerplate removal)
- `v2.0` – Current (70+ patterns, 3-tier fallback)

**CLI:** `--preprocessing-version 2.0`, `--show-version-stats`, `--re-preprocess-only-v1`

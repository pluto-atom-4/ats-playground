# Preprocess Phase Rules

MarkItDown HTML cleaning, spaCy semantic chunking, token counting via tiktoken.

## HTML Cleaning Strategy

**Precedence:**
1. **MarkItDown** (primary) – Preserves structure, handles tables/code
2. **BeautifulSoup + lxml** (fallback) – If MarkItDown unavailable

Raw HTML (~6,000 tokens) → clean text (~400 tokens).

```python
from src.parsers.html import parse_html

clean_text = parse_html(raw_html)  # Automatic fallback if MarkItDown fails
```

**HTML→Markdown normalization runs first (Issue #228)**: crawl stores the raw extracted description as-is; `_build_preprocess_clean_text` (`src/cli.py`) calls `src.parsers.html_to_markdown.normalize_description()` — HTML→Markdown conversion + synthesized `##`/`###` section headers + `---` dividers — as the first step of preprocess, before chunking. This used to run inline in `Crawler` at crawl time; it does not anymore.

## Semantic Chunking (Sentences, Not Tokens)

Split at semantic boundaries: "Requires 5+ years MES. Must know Wonderware." stays together. Chunks vary 100–600 tokens (intentional).

```python
from src.tokenization.chunking import chunk_by_sentences

chunks = chunk_by_sentences(clean_text, target_tokens=400)
```

Target: ~400 tokens/chunk (safe for LLM).

## Token Counting & Cost Transparency

Always count before API calls.

```python
from src.tokenization.counter import count_tokens

tokens = count_tokens(text)
cost_usd = tokens * 0.000003  # Claude 3.5 Sonnet input rate
```

Show estimate before assessment. Track actual vs estimated in cost_tracking table.

## Key Non-Obvious Behavior

- **Chunk sizes vary intentionally**: Semantic boundaries, not token-aligned. Don't force uniform counts.
- **Cost estimates pre-API**: tiktoken estimates differ slightly from Claude's actual token count.
- **Fallback parsing**: If MarkItDown fails, BeautifulSoup activates automatically. Check logs if content missing.
- **Section skip-list (Issue #221)**: `Preprocessor.SKIP_SECTIONS` (`preprocessor.py`) excludes benefits/legal/hiring-process sections (e.g. `e-verify`, `union`, `technical assessment`, `contingent upon award`) from entity extraction. `technical assessment` closes a real gap: it contains "technical", one of `skills_section_keywords`, so without an explicit skip entry such a section risked being misrouted into skills instead of skipped.

## Implementation Details (Phases 5–7)

Technical keyword expansion (Issue #192), boilerplate removal (Issue #193), company name filtering (Issue #194) documented in [DESIGN.md](../../DESIGN.md).


## Verification Commands

```bash
# Token estimates for all jobs
uv run python -m src.cli preprocess --show-estimates

# Query by keyword
uv run python -m src.cli query --keyword "python" --min-score 0

# Run tokenization tests
uv run pytest tests/tokenization/ -v
```

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

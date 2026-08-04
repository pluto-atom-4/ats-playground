# Preprocess Phase Rules

MarkItDown HTML cleaning, spaCy semantic chunking, token counting via tiktoken.

## HTML Cleaning Strategy

**Primary API (Issue #230 Phase 1):**

Use `clean_html()` for consolidated HTML preprocessing with 70+ boilerplate patterns:

```python
from src.parsers.html_to_markdown import clean_html

# Clean HTML, remove boilerplate, preserve important sections
clean_text = clean_html(
    raw_html,
    include_section_headers=True,       # Keep synthesized headers
    skip_boilerplate_categories={'salary_benefits', 'legal'}
)
```

**Boilerplate Categories (7 total):**
- `legal` – Legal disclaimers, EEO statements, compliance notices
- `section_headers` – Navigation headers, redundant section labels
- `company_info` – Company taglines, about blurbs (not job-specific)
- `time_refs` – Posted dates, application deadlines, timestamps
- `salary_benefits` – Salary ranges, benefits details (optional removal)
- `formatting` – Extra whitespace, CSS classes, metadata attributes
- `navigation` – Page navigation, breadcrumbs, menus

**Example output comparison:**
```
Before (raw HTML, ~6,000 tokens):
  <div class="job-post">
    <h2>Senior Python Developer</h2>
    ...
    <p>© 2026 Company Inc. All rights reserved. Equal Opportunity Employer...</p>
    <nav><a href="/careers">Back to jobs</a></nav>
  </div>

After clean_html() (boilerplate removed, ~400 tokens):
  ## Senior Python Developer

  [job description and requirements, no legal/nav]
```

**Performance benefit:** 70+ pre-compiled regex patterns (10x faster than sequential regex per job). Backward compat: old jobs without boilerplate removal still queryable.

**HTML→Markdown normalization (Issue #228):** crawl stores raw extracted description as-is; `_build_preprocess_clean_text` (`src/cli.py`) calls `src.parsers.html_to_markdown.normalize_description()` — HTML→Markdown conversion + synthesized `##`/`###` section headers + `---` dividers + boilerplate removal — as the first step of preprocess, before chunking. This used to run inline in `Crawler` at crawl time; it does not anymore.

**3-Tier Fallback Chain (Issue #231):**
1. **MarkItDown** (primary) – Preserves structure, ~50ms/job
2. **BeautifulSoup + lxml** (fallback) – Basic text extraction, ~100ms/job
3. **Original HTML** (safe) – Worst case, ~6K tokens, never fails

```python
from src.parsers.html_to_markdown import html_to_markdown

clean_text = html_to_markdown(raw_html)
# Automatically uses fallback chain: MarkItDown → BeautifulSoup → Original HTML
```

Robustness: Preprocessing never fails catastrophically (tests: `test_exception_fallback_returns_original_html`, `test_malformed_html_does_not_raise`).

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

- **Boilerplate removal (Issue #230)**: 70+ patterns pre-compiled across 7 categories (legal, headers, company, time, salary, formatting, navigation). Removes ~30% of text while preserving job requirements. Backward compatible: old jobs queryable via `preprocessing_version` column (Phase 2 feature).
- **Chunk sizes vary intentionally**: Semantic boundaries, not token-aligned. Don't force uniform counts.
- **Cost estimates pre-API**: tiktoken estimates differ slightly from Claude's actual token count.
- **Fallback parsing (Issue #231)**: 3-tier chain: MarkItDown → BeautifulSoup → Original HTML. Preprocessing never fails, worst-case returns unmodified HTML (~6K tokens vs ~400 expected).
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

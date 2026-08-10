# DESIGN.md: ATS Playground Architecture

**Version:** 2.1 (Anthropic standards + Requirements Extraction)
**Last Updated:** 2026-08-01
**Status:** Condensed for token budget; Phase-specific rules in `.claude/rules/`

---

## 1. PRODUCT NARRATIVE

ATS Playground orchestrates **core 5 phases + enhancement phases 5-7** for intelligent CV-to-job assessment:

**Core Pipeline (Phases 1-5):**
- **Crawl:** Extract jobs from career pages (Playwright, CSS selectors, rate-limited)
- **Preprocess:** Clean HTML → semantic chunks, estimate tokens (15× reduction: ~6,000 → ~400 tokens/job)
- **Verify:** Interactive confirmation before costly API calls (status: pending → confirmed/rejected)
- **Assess:** Claude evaluates CV fit (scores: tech, seniority, location)
- **Export:** Markdown reports with rankings

**Enhancement Phases (5-7):** Soft skills extraction, compound requirement reclassification, keyword expansion via stemming/fuzzy matching. Quality: 45% → 99.8%+ semantic accuracy (PRs #200-204).

**Cost Control:** Use `--up-to review` to halt before assess phase. Cost transparency enforced at each step.

---

## 2. WORKFLOW PIPELINE

```
CONFIG (companies.json + CSS selectors)
  ↓
CRAWL (Playwright + pagination) → Raw HTML
  ↓
PREPROCESS (MarkItDown + spaCy + tiktoken) → Clean chunks + token estimates
  ↓
VERIFY (Interactive CLI, status tracking) → Confirmed jobs
  ↓
ASSESS (Claude 3.5 Sonnet + rate limiting) → Scores + actual tokens/cost
  ↓
STORAGE (SQLite + FTS5) → Queryable database
  ↓
EXPORT (Markdown reports)
```

---

## 3. MODULE STRUCTURE

| Module | Purpose |
|--------|---------|
| **src/browser/** | Playwright automation (BrowserManager) |
| **src/parsers/** | HTML cleaning (MarkItDown + BeautifulSoup fallback) |
| **src/tokenization/** | NLP chunking (spaCy) + token counting (tiktoken) |
| **src/verification/** | Interactive review + status tracking |
| **src/llm/** | Claude API client + rate limiting |
| **src/storage/** | SQLite (FTS5, export, queries) |
| **src/cli.py** | Typer CLI orchestration |
| **src/tui/** | Textual dashboard (real-time progress, cost tracking) |

---

## 4. KEY DECISIONS

- **Semantic Chunking:** Split at sentences (spaCy), not fixed tokens. Chunk sizes 100–600 tokens (intentional).
- **Cost Transparency:** Show user estimate before LLM calls. tiktoken estimates vs. Claude actual tokens tracked.
- **Confirmation Required:** Assessment only on status == "confirmed" jobs. Prevents quota waste on low-confidence extractions.
- **Single-Writer SQLite:** No concurrent assessment processes (deadlock risk). Use queue or single-process pattern.
- **Async-First TUI:** StateManager is source of truth. Panels poll every 0.5s (2 Hz, not 60 FPS).

See `.claude/rules/tui/` for StateManager, panel architecture, and async workflow details.

---

## 5A. HTML Cleaning Consolidation (Issue #230)

**Architecture:** 3 modules → 1 consolidated `clean_html()` function

| Component | Before | After |
|-----------|--------|-------|
| HTML cleaning | `HTMLCleaner` + scattered regex | `clean_html()` single source-of-truth |
| Boilerplate removal | Ad-hoc per-module patterns | 70+ pre-compiled patterns, 7 categories |
| Performance | ~500ms per job (regex per call) | ~50ms per job (pre-compiled) |
| Maintenance | Multiple locations, divergent logic | Single `_boilerplate_patterns.py` |

**Boilerplate Categories (7):**
1. **Legal** – EEO statements, compliance disclaimers, copyright
2. **Section Headers** – Navigation headers, redundant section labels
3. **Company Info** – Taglines, about blurbs (not job-specific)
4. **Time References** – Posted dates, deadlines, timestamps
5. **Salary & Benefits** – Salary ranges, benefits (optional removal)
6. **Formatting** – Extra whitespace, CSS classes, metadata
7. **Navigation** – Breadcrumbs, menus, page navigation

**API:**
```python
from src.parsers.html_to_markdown import clean_html

# Remove specific categories
clean_text = clean_html(
    raw_html,
    skip_boilerplate_categories={'legal', 'salary_benefits'}
)
```

**Pipeline:** HTML → Markdown → section headers → dividers → boilerplate removal → entity extraction → whitespace normalization

**Performance Benefit:** 70+ patterns pre-compiled at module load (10x faster per job)

**Token Reduction:** ~88% vs raw HTML (6,000 → 700 tokens), with boilerplate removal accounting for ~30% of savings

**Backward Compatibility (Phase 2 – IMPLEMENTED):** Database column `preprocessing_version` tracks v1.0 (legacy, no boilerplate) vs v2.0 (new, with boilerplate removal). Enables selective re-preprocessing and graceful fallback. JobStore API + CLI integration complete (see `.claude/rules/cli.md` for usage).

**CLI/TUI Integration (Phase 4 – IMPLEMENTED):** `normalize_description()` removed from CLI (`src/cli.py` line 323), replaced with `clean_html()`. TUI dashboard (`src/tui/dashboard.py` line 310) uses `clean_html()` directly; `HTMLCleaner` instantiation removed. No more wrapper; unified pipeline active across all entry points.

**Deprecation Path:** `HTMLCleaner` marked deprecated in `src/parsers/html_cleaner.py`, delegates to `clean_html()` for backward compatibility. Scheduled for removal in v2.1.

### Fallback Chain (Issue #231)

3-tier robustness strategy: Preprocessing never fails catastrophically.

```
HTML → MarkItDown (primary, ~50ms)
     ↓ (on failure)
     → BeautifulSoup (fallback, ~100ms)
     ↓ (on failure)
     → Original HTML (safe, ~6K tokens, never fails)
```

**Implementation:** `html_to_markdown()` catches exceptions at each tier, logs warnings, escalates to next tier.

**Tests:** `test_exception_fallback_returns_original_html()` (MarkItDown → BeautifulSoup path), `test_malformed_html_does_not_raise()` (safety net verification).

---

## 5B. Trigger-Based Requirement Extraction (Phase 8a, Issue #248-252)

**Architecture:** spaCy pipeline component + CLI integration for pattern-based requirement extraction.

```
Raw Job Description
  ↓
spaCy NLP Pipeline
  ├─ Tokenization (whitespace)
  ├─ Requirement Filter Component (18 trigger patterns)
  │  ├─ Tier 1 (0.83-0.95): required, must, essential, ability to, experience, proficiency, knowledge, understanding
  │  ├─ Tier 2 (0.65-0.89): should, prefer, degree, years of
  │  └─ Tier 3 (0.40-0.55): nice to have, ideal, bonus
  └─ NER (existing)
  ↓
Confidence-Scored Requirements
  ├─ Context adjustments: negation (-0.25), conditional (-0.15), parenthetical (-0.10)
  ├─ Deduplication (by text)
  └─ JSON output: {text, trigger_word, confidence, span, token_count}
```

**Component:** `requirement_filter` (spaCy @Language.component decorator)
- Registers custom `Doc._.requirements` attribute
- Processes cleaned text (pre-spaCy, 100–600 token chunks)
- Returns list of requirement dicts with confidence scores
- <50ms per job, <5% token overhead

**CLI Integration:**
- `--extract-requirements` (default): Enable extraction, display count + top 5 per job
- `--no-extract-requirements`: Disable (backward compatible)
- `--export-requirements-json <file>`: Save all requirements to JSON for downstream analysis

**Database Storage:** Nullable `requirements TEXT` column in `preprocessed_jobs` table. Old jobs (v1.0) have NULL; new jobs (v2.0+) contain JSON array.

**Example:** Raw description → Extracted requirements
```
Raw: "We seek a Senior Python Developer. Required: 5+ years Python, knowledge of Django.
       Must have REST API experience. Proficiency in Docker is mandatory."

Extracted JSON:
[
  {"text": "5+ years Python", "trigger_word": "Required", "confidence": 0.91, "span": (61, 76), "token_count": 3},
  {"text": "knowledge of Django", "trigger_word": "knowledge of", "confidence": 0.87, "span": (79, 98), "token_count": 4},
  {"text": "REST API experience", "trigger_word": "Must have", "confidence": 0.88, "span": (127, 146), "token_count": 3},
  {"text": "Proficiency in Docker", "trigger_word": "Proficiency", "confidence": 0.89, "span": (159, 180), "token_count": 4}
]
```

**Tests:** 39 unit tests (trigger detection, confidence scoring, edge cases, fixture coverage) + 9 integration tests (full pipeline, latency, JSON export, CLI flags). All passing.

See `.claude/rules/phase8/patterns.md` for complete trigger list, edge cases, confidence adjustment rules.

---

## 5. PHASE-SPECIFIC RULES & COORDINATION

Phase documentation organized in `.claude/rules/`:
- **crawl.md** – Playwright patterns, CSS selectors, pagination, rate limiting
- **preprocess.md** – MarkItDown, spaCy chunking, tokenization, Phase 5-7 enhancements
- **verify.md** – Interactive review workflow, cost verification, status transitions
- **assess.md** – Claude API integration, prompt design, rate limiting, cost tracking
- **storage.md** – SQLite schema (FTS5), markdown export, query patterns
- **cli.md** – Typer command structure, async patterns, error handling
- **multi-agent.md** – Phase coordination across Architect, Coder, Reviewer roles

See **AGENTS.md** for role-based governance and handoff protocols.

---

## 6. CRITICAL CONSTRAINTS

**Don't:**
- Assess unconfirmed jobs (enforce `--skip-unconfirmed`, default: true)
- Run concurrent assessment processes on same DB (single-writer SQLite)
- Send raw HTML to Claude (always preprocess; raw HTML ~6,000 tokens)
- Skip verification before API calls (cost transparency required)
- Force uniform token chunks (sentences vary 100–600 tokens)
- Commit to main directly (feature branch workflow via pre-commit hook)

**TUI-Specific:**
- Mutate StateManager outside `@work(exclusive=True)` (race conditions)
- Block Textual's main thread (all I/O must be async)
- Render 1000+ rows in DataTable (paginate, show top 100)
- Update UI at 60 FPS (poll every 0.5s to prevent flicker)

See CLAUDE.md and `.claude/rules/` for enforcement mechanisms.

---

## 7. TECH STACK & SETUP

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Browser | Playwright (async, JS rendering) | Handles dynamic content, pagination |
| HTML → Markdown | 3-tier: MarkItDown → BeautifulSoup → Original | Structure preservation + robustness (Issue #231) |
| Tokenization | spaCy (sentences) + tiktoken (counting) | Semantic boundaries, cost estimation |
| Database | SQLite + FTS5 | Serverless, full-text search, atomic writes |
| LLM | Claude 3.5 Sonnet | Cost/quality balance: $0.003 per 1M input tokens |
| CLI | Typer | Async-ready, typed commands, help text |
| TUI | Textual + Rich | Async-first, responsive, light/dark theme |

**Quick Setup:**
```bash
uv sync && uv run python -m spacy download en_core_web_md
uv run playwright install chromium
cp .env.example .env && uv run python src/storage/db.py --init
```

---

## Summary: Key Takeaways

1. **5-phase core + 3-phase enhancement pipeline** with cost transparency and user confirmation gates
2. **Semantic chunking** (sentences) preserves meaning; chunk sizes vary 100–600 tokens intentionally
3. **Single-writer SQLite** prevents deadlocks under concurrent load; use queue pattern
4. **StateManager as TUI source of truth** (polling every 0.5s, all I/O async)
5. **Phase-specific rules in `.claude/rules/`** with role-based governance in AGENTS.md
6. **Cost control at each step:** Verify estimates before assess; track actual vs. estimated tokens

---

**See Also:** CLAUDE.md (setup + workflows) | AGENTS.md (roles + governance) | .claude/rules/ (phase details)

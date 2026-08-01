# Preprocess Phase Rules

MarkItDown HTML cleaning, spaCy semantic chunking, token counting via tiktoken.

## HTML Cleaning Strategy

**Precedence:**
1. **MarkItDown** (primary) – Preserves structure, Microsoft-maintained, handles tables/code
2. **BeautifulSoup + lxml** (fallback) – If MarkItDown unavailable or too slow

**Always clean before chunking.** Raw HTML (~6,000 tokens per job) → clean text (~400 tokens).

```python
from src.parsers.html import parse_html

raw_html = "<html>...</html>"
clean_text = parse_html(raw_html)  # MarkItDown or BeautifulSoup
```

## Semantic Chunking (Sentences, Not Tokens)

**Why sentences?** Splits at semantic boundaries; "Requires 5+ years MES. Must know Wonderware." stays together. Chunks vary 100–600 tokens (intentional).

```python
from src.tokenization.chunking import chunk_by_sentences

chunks = chunk_by_sentences(clean_text, target_tokens=400)
# chunks: [chunk1, chunk2, ...] where len(chunk_tokens) ≈ 400
```

**Target:** ~400 tokens per chunk (safe for LLM context window).

## Token Counting & Cost Transparency

**Always count before sending to LLM.**

```python
from src.tokenization.counter import count_tokens

tokens = count_tokens(text)
cost_usd = tokens * 0.000003  # Claude 3.5 Sonnet input rate
```

Show user estimate before assessment. Track actual vs estimated in cost_tracking table.

## Key Non-Obvious Behavior

- **Chunks are sentences, not token-aligned**: Chunk sizes vary intentionally. Don't force uniform token counts.
- **Cost estimates are pre-API**: tiktoken estimates. Actual Claude tokens may differ slightly (special tokens, prompt overhead).
- **Fallback HTML parsing**: If MarkItDown fails, BeautifulSoup is automatic. Check logs if content missing.

## Phase 5: Technology Keywords Expansion (Issue #192)

**Keyword Coverage:** 161 keywords across 10 categories (expanded from 128 in Issue #185).

### New Keywords Added (33 total)

**Engineering Tools (9):** ANSYS, Nastran, OptiStruct, Creo, SolidWorks, CATIA, Windchill, Simulink, COMSOL
- Focus: FEA/CAD tools critical for aerospace/defense/manufacturing
- Impact: Improves recognition of design & simulation tools

**Signal Processing (4):** FFT, IFFT, CORDIC, MAC
- Focus: DSP operations in hardware design
- Impact: Better extraction for embedded systems & ASIC roles

**Cloud/DevOps (5):** ArgoCD, Flux, GitOps, Harbor, Quay
- Focus: Modern GitOps and container registries
- Impact: Captures infrastructure-as-code trend

**Data Tools (6):** TimescaleDB, ClickHouse, DVC, Pydantic, SQLAlchemy, Celery
- Focus: Time-series databases, ORMs, and data validation
- Impact: Better data pipeline recognition

**IoT/Protocols (4):** MQTT, AMQP, WebSocket, CoAP
- Focus: Real-time communication protocols
- Impact: Improves IoT and edge computing job matching

**Manufacturing (5):** CAM, CNC, PLM, ERP, MRP
- Focus: Manufacturing systems & lifecycle management
- Impact: Supports aerospace/defense manufacturing domain

### Expected Impact

- **Before Phase 5:** 69.3% tech keyword match rate on aerospace/defense jobs
- **Expected After:** 80-90% match rate (especially for CAD/simulation/manufacturing tools)
- **Key Domains Improved:**
  - Aerospace/Defense: +ANSYS, Nastran, OptiStruct, CATIA (Boeing, Lockheed Martin, Blue Origin)
  - Manufacturing: +CAM, CNC, PLM, ERP (Raytheon, Northrop Grumman)
  - DevOps: +ArgoCD, Flux, GitOps (modern deployment)

### Integration with Extraction

Keywords are used in `src/tokenization/keywords.py` and integrated into:
- `_extract_entities_by_section()` – Tech keyword extraction
- Preprocessor token counting – Cost estimation
- Database FTS queries – Keyword-based search

No changes needed to extraction logic; just expanded keyword set improves recall.

## Verification Commands

```bash
# Show token estimates for all jobs
uv run python -m src.cli preprocess --show-estimates

# Check specific job after crawl
uv run python -m src.cli query --keyword "python" --min-score 0
```

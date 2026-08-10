# Span Extraction Algorithm (Phase 8b, Issue #254)

Algorithm for extracting contiguous requirement spans from cleaned job text using spaCy POS/dependency tagging.

---

## Overview

**Goal:** Extract token span boundaries for requirements identified by Phase 8a trigger patterns.

**Input:** Cleaned text with trigger-based requirements (from Phase 8a requirement_filter)
**Output:** Span boundaries (start_token_idx, end_token_idx), span_type (atomic/compound), full_text

**Performance:** O(n) algorithm where n = token count. Target: <100ms for 1000-token documents.

---

## Algorithm Design

### 1. Span Boundary Rules

**Span Start:**
- Begin at trigger word (e.g., "Required:", "Must have")
- Include immediate next meaningful token (skip articles: "a", "an", "the")
- Example: "Required: 5+ years" → start at "5"

**Span End:**
- Stop at semantic boundaries:
  - **Hard stop (include last token before):**
    - Sentence boundary: period ".", semicolon ";"
    - Comma + conjunction "," → Check if 'and/or' (compound) or new item (atomic)
    - Parenthesis close ")" (if span started in parenthesis)
    - PUNCT token (except hyphen in compound words)

  - **Soft boundary (context-dependent):**
    - Preposition that starts new concept (e.g., "years in Python, but not Java" → stop at "but")
    - Subordinating conjunction ("that", "which", "if") → may include dependent clause or stop

**Boundary Detection Logic:**
```
For each token after trigger:
  1. If token.pos_ in [PUNCT, SPACE]:
     - If token.text in ['.', ';', ')']:  END SPAN (hard stop)
     - If token.text == ',' and next_token.text not in ['and', 'or']:  END SPAN
     - If token.text == ',' and next_token.text in ['and', 'or']:  Mark COMPOUND boundary, continue
     - If token.text == '-' or token.dep_ == 'compound':  Continue (hyphenated compound)

  2. If token.pos_ in [CCONJ] and token.text in ['and', 'or']:
     - If current span is complete:  END SPAN, mark as part of COMPOUND
     - If continuation expected:  Note compound type, continue

  3. If token.pos_ in [SCONJ]:
     - If token in ['that', 'which']:  Include dependent clause
     - If token in ['if', 'unless']:  Optional context, may END SPAN

  4. Otherwise:  Continue accumulating tokens
```

---

## Span Types

### Atomic Spans
Single requirement phrase with one trigger word, no conjunction expansion.

**Examples:**
- "Required: 5+ years Python experience" → Atomic
- "Knowledge of Docker" → Atomic
- "Must understand microservices" → Atomic

**Characteristics:**
- Single trigger word
- No 'and/or' conjunction in scope
- Clear semantic boundary (sentence end, comma, or preposition)

### Compound Spans
Multiple related requirements connected by 'and/or', extracted as single compound span for semantic grouping.

**Examples:**
- "Required: 5+ years Python and strong REST API design skills" → Compound (2 conjuncts)
- "Knowledge of Docker and Kubernetes or equivalent containerization" → Compound (3 conjuncts)
- "Ability to manage teams, mentor junior developers, and communicate findings" → Compound (3 conjuncts via commas)

**Characteristics:**
- Single trigger word
- Contains 'and/or' connecting multiple requirements
- All conjuncts extracted as single span
- Marked with `span_type: "compound"`, `conjunct_count: N`

### Multi-Line Spans (Cross-Sentence)
Requirements that span across sentence/line boundaries (e.g., "Required: 5+ years (see job description for details)").

**Characteristics:**
- Trigger word near end of one sentence
- Continuation hints in next sentence (no new trigger, parenthetical context)
- Merge when: previous span incomplete + next token continues requirement meaning

**Cross-Sentence Rules:**
- If previous token is:
  - Parenthetical context: "Required: 5+ years (in Python)" → continue across ')' if ')' ends parenthetical
  - Ellipsis or incomplete phrase: "Must have knowledge of..." → include next lines until boundary
  - Conjunctive list format: Multiple bulleted items with same trigger → merge only within bullet group

---

## POS/Dependency Tag Logic

**Key spaCy POS/DEP tags used:**

| Tag | Meaning | Handling |
|-----|---------|----------|
| NOUN | Noun phrase | Core of requirement |
| ADJ | Adjective (modifier) | Include (modifies requirement) |
| VERB | Verb (action) | Include (requirement action) |
| NUM | Number (years, count) | Include (quantifier) |
| PUNCT | Punctuation | Use to detect boundaries |
| ADP | Preposition | Include (part of noun phrase) |
| CCONJ | Coordinating conjunction (and, or) | Mark compound boundary |
| SCONJ | Subordinating conjunction (if, that) | Context-dependent |
| DET | Determiner (a, the) | Skip at span start |
| PART | Particle (to in infinitive) | Include (part of verb phrase) |

**DEP Tags (syntactic function):**
- `nsubj` / `obj` – Subject/object of verb (core)
- `nmod` – Nominal modifier (modifier attached to noun)
- `amod` – Adjectival modifier (adjective attached to noun)
- `prep` – Prepositional attachment (e.g., "years of experience")
- `compound` – Compound noun (e.g., "cross-functional")
- `conj` – Conjunction (for compound expansion)

---

## Algorithm Pseudocode

```python
def extract_span(doc, trigger_token):
    """
    Extract span boundaries for a requirement starting at trigger_token.

    Args:
        doc: spaCy Doc object (processed text)
        trigger_token: Token object at trigger word

    Returns:
        span_obj: {
            start_idx: int,
            end_idx: int,
            text: str,
            span_type: "atomic" | "compound",
            token_indices: List[int],
            conjunct_count: int (for compound)
        }
    """

    # Start span after trigger word
    current_idx = trigger_token.i + 1
    start_idx = None
    end_idx = None
    conjunct_boundaries = []

    # Skip initial articles/determiners
    while current_idx < len(doc) and doc[current_idx].pos_ in ['DET', 'SPACE']:
        current_idx += 1

    start_idx = current_idx

    # Expand span token-by-token
    while current_idx < len(doc):
        token = doc[current_idx]

        # Hard boundary conditions
        if token.pos_ == 'PUNCT':
            if token.text in ['.', ';', ')', '!', '?']:
                end_idx = current_idx - 1
                break
            elif token.text == ',':
                # Check if followed by 'and/or' (compound) or new item
                if current_idx + 1 < len(doc):
                    next_token = doc[current_idx + 1]
                    if next_token.text.lower() in ['and', 'or']:
                        # Mark compound boundary, continue
                        conjunct_boundaries.append(current_idx)
                        current_idx += 2  # Skip comma and conjunction
                        continue
                    else:
                        # New item, end span
                        end_idx = current_idx - 1
                        break
            elif token.text == '-' and token.dep_ == 'compound':
                # Hyphenated compound, continue
                current_idx += 1
                continue
            else:
                # Other punctuation, end span
                end_idx = current_idx - 1
                break

        # Coordination (and/or) logic
        if token.pos_ == 'CCONJ' and token.text.lower() in ['and', 'or']:
            conjunct_boundaries.append(current_idx - 1)
            current_idx += 1
            continue

        # Subordination logic
        if token.pos_ == 'SCONJ':
            if token.text.lower() in ['that', 'which']:
                # Include dependent clause (relative clause)
                current_idx += 1
                continue
            elif token.text.lower() in ['if', 'unless', 'because']:
                # Conditional/causal context
                # Decision: for "required if...", include conditional
                # For "years if preferred", end at "if"
                if trigger_token.text.lower() in ['required', 'must', 'essential']:
                    current_idx += 1
                    continue
                else:
                    end_idx = current_idx - 1
                    break

        # Continue accumulating
        current_idx += 1

    # Set end index (default to last token if not explicitly stopped)
    if end_idx is None:
        end_idx = current_idx - 1

    # Extract span text and determine type
    span_tokens = list(range(start_idx, end_idx + 1))
    span_text = ' '.join([doc[i].text for i in span_tokens])

    # Determine span type
    has_conjunction = len(conjunct_boundaries) > 0
    span_type = 'compound' if has_conjunction else 'atomic'
    conjunct_count = len(conjunct_boundaries) + 1 if has_conjunction else 1

    return {
        'start_idx': start_idx,
        'end_idx': end_idx,
        'text': span_text,
        'span_type': span_type,
        'token_indices': span_tokens,
        'conjunct_count': conjunct_count,
        'conjunct_boundaries': conjunct_boundaries
    }
```

---

## Edge Cases & Handling

### 1. Negations
**Example:** "No experience required" → Exclude requirement

**Rule:** If trigger precedes negation ("no", "not", "don't"), skip span extraction. Phase 8a already filters these (confidence = 0.0).

### 2. Parenthetical Context
**Example:** "Required: 5+ years (in production environments)"

**Rule:** If span contains parenthesis:
- If '(' immediately after requirement keyword: include content until ')'
- If '(' mid-span: end span at '(', treat parenthetical as separate context

### 3. Compound Nouns (Hyphenated)
**Example:** "cross-functional team management"

**Rule:** Include hyphenated tokens as single noun (token.dep_ == 'compound'). Don't stop at hyphen.

### 4. Infinitive Phrases
**Example:** "Ability to manage teams and mentor developers"

**Rule:** Include 'to' particle + verb + object. Continue through 'and' to capture full scope.

### 5. Prepositional Phrases
**Example:** "Knowledge of Docker, Kubernetes, or Terraform"

**Rule:** Continue through preposition + object list. List items connected by commas + 'or' = single compound span.

### 6. Multiple Modifiers
**Example:** "Strong communication and analytical problem-solving skills"

**Rule:** Include all adjectives + nouns. Multiple modifiers separated by 'and' = compound.

### 7. Relative Clauses
**Example:** "Experience with Java, which powers 80% of enterprise systems"

**Rule:** Optional: include relative clause (which/that). By default, stop before 'which' to keep requirement core focused.

### 8. Degree/Certification Mentions
**Example:** "Bachelor's degree in Computer Science or equivalent"

**Rule:** Include alternate degrees (or equivalent). 'or' triggers compound extraction.

### 9. Future/Aspirational ("Nice to Have")
**Example:** "Nice to have: 3+ years Rust (if available)"

**Rule:** Same boundary rules. Parenthetical "(if available)" does not extend span past ')'.

### 10. List Format
**Example:** "Required: (1) 5+ years Python, (2) Strong communication, (3) Leadership"

**Rule:** Each numbered item = separate span. Don't merge across item markers.

---

## Cross-Sentence Boundary Rules

**When to merge spans across sentence boundaries:**

1. **Incomplete phrase at sentence end:**
   ```
   "Must have knowledge of..."
   [NEW SENTENCE] "...production systems and cloud platforms."
   ```
   → Merge if next sentence continues without new trigger

2. **Parenthetical continuation:**
   ```
   "Required: 5+ years (see job description)."
   [SAME PARAGRAPH] "Experience should include hands-on work."
   ```
   → Don't merge; new sentence = new requirement (or same trigger scope?)

3. **Bullet list format:**
   ```
   - Required: 5+ years Python
   - Must have Docker experience
   ```
   → Each bullet = separate span (even if triggered by same "Required")

**Default behavior:** Stop at sentence boundary (period/semicolon) unless parenthetical context suggests continuation.

---

## Performance Notes

**Algorithm Complexity:** O(n) where n = token count in document

**Expected runtime:**
- 100-token requirement: <1ms
- 1000-token document: <100ms (avg 0.1ms per requirement × ~50 requirements)

**Optimization:**
- Pre-tokenize and cache POS/DEP tags (spaCy already does this)
- Single pass through tokens per requirement
- No backtracking (forward-only scan)
- No nested loops (linear complexity)

---

## Integration with Phase 8a

**Phase 8a outputs (Doc._.requirements list):**
```python
[
    {"text": "5+ years Python", "trigger_word": "Required", "confidence": 0.91, "span": (61, 76)},
    {"text": "knowledge of Django", "trigger_word": "knowledge of", "confidence": 0.87, "span": (79, 98)},
]
```

**Phase 8b input/output:**
- Input: Above requirements list + original doc text
- Output: Enriched requirements with expanded spans, span_type, token_indices

**Example enhancement:**
```python
{
    "text": "5+ years Python",
    "trigger_word": "Required",
    "confidence": 0.91,
    "span": (61, 76),
    "expanded_span": (61, 76),  # New in 8b
    "span_type": "atomic",       # New in 8b
    "token_indices": [10, 11, 12, 13],  # New in 8b
    "full_requirement": "Required: 5+ years Python experience"  # New in 8b
}
```

---

## Next Steps (Phase 8b.2)

1. Implement spaCy component `span_extractor` that:
   - Receives Doc with Doc._.requirements populated by Phase 8a
   - Calls algorithm for each requirement
   - Stores results in new Doc._.requirement_spans attribute

2. Integration test: Full pipeline (8a + 8b) on sample jobs

3. CLI flag: `--extract-requirement-spans` (similar to Phase 8a)

---

**Last Updated:** 2026-08-12
**Status:** Algorithm designed; ready for implementation (Phase 8b.2)

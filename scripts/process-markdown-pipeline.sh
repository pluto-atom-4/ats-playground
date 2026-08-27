#!/bin/bash
# Process HTML through complete markdown pipeline (Issue #299 Phase 6+)
# Demonstrates all 4 stages: HTMLPreprocessor, HTMLMarkdownConverter, MarkdownPolisher, SectionClassification

set -e

# Parse arguments
INPUT_FILE=""
SHOW_HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --input)
            INPUT_FILE="$2"
            shift 2
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            SHOW_HELP=true
            shift
            ;;
    esac
done

# Show help if requested or no input provided
if [ "$SHOW_HELP" = true ] || [ -z "$INPUT_FILE" ]; then
    cat << 'EOF'
Usage: bash scripts/process-markdown-pipeline.sh --input <file>

Process HTML through complete markdown pipeline with all 4 stages:
1. HTMLPreprocessor: Clean HTML, normalize structure, remove non-breaking spaces
2. HTMLMarkdownConverter: Convert HTML to Markdown using MarkItDown
3. MarkdownPolisher: Apply formatting rules (line norm, list tightening, headers, etc.)
4. SectionClassification: Parse markdown into sections, classify by semantic type (SKILLS, QUALIFICATIONS, etc.)

Arguments:
  --input <file>    Path to JSON file containing HTML (required)
                    Expected format: {"description": "<html>..."}
                    Or direct HTML file

  --help            Show this help message

Examples:
  bash scripts/process-markdown-pipeline.sh --input tests/poc/fixtures/raw_html_description-bo.json
  bash scripts/process-markdown-pipeline.sh --input data/job.html

Output:
  - Input file and byte/line counts
  - Stage 1: After preprocessing (nbsp removed, HTML normalized)
  - Stage 2: After conversion (HTML to Markdown)
  - Stage 3: After polishing (formatting rules applied)
  - Stage 4: After classification (sections parsed and classified by type)
  - Final markdown result
  - Summary statistics

EOF
    exit 0
fi

# Verify input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    exit 1
fi

# Run pipeline via Python
uv run python -c "
import json
import sys
import os
from pathlib import Path

# Import pipeline components
from src.poc.tweak.spacy_pipeline import HTMLPreprocessor, HTMLMarkdownConverter, MarkdownPolisher
from src.poc.tweak.multi_line_paragraph import MarkdownSpanRuler
from src.poc.tweak.markdown_section_classifier import SectionClassifier, SectionType

print('✓ Imports successful')
print()

# Load spaCy model
try:
    import spacy
    nlp = spacy.load('en_core_web_md')
    print('✓ spaCy model loaded: en_core_web_md')
except OSError:
    print('Error: spaCy model en_core_web_md not installed')
    print('Install with: uv run python -m spacy download en_core_web_md')
    sys.exit(1)
except ImportError:
    print('Error: spaCy not installed')
    sys.exit(1)

print()

# Load input HTML
input_file = '$INPUT_FILE'
file_size = os.path.getsize(input_file)

# Determine if JSON or plain HTML
if input_file.endswith('.json'):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'description' in data:
        raw_html = data['description']
    else:
        print(f'Error: JSON file must contain \"description\" field')
        sys.exit(1)
else:
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_html = f.read()

print('=' * 70)
print('INPUT FILE')
print('=' * 70)
print(f'File: {input_file}')
print(f'File size: {file_size:,} bytes')
print(f'HTML length: {len(raw_html):,} characters')
print(f'HTML lines: {len(raw_html.splitlines())} lines')
print()

# Initialize components
print('=' * 70)
print('INITIALIZING COMPONENTS')
print('=' * 70)
preprocessor = HTMLPreprocessor()
print(f'✓ HTMLPreprocessor initialized')
converter = HTMLMarkdownConverter()
print(f'✓ HTMLMarkdownConverter initialized')
polisher = MarkdownPolisher()
print(f'✓ MarkdownPolisher initialized (rules={polisher.rules})')
ruler = MarkdownSpanRuler(nlp)
print(f'✓ MarkdownSpanRuler initialized')
classifier = SectionClassifier()
print(f'✓ SectionClassifier initialized')
print()

# Stage 1: Preprocessing
print('=' * 70)
print('STAGE 1: HTML PREPROCESSING')
print('=' * 70)
stage1_output = preprocessor.process(raw_html)
nbsp_count = raw_html.count('\xa0') - stage1_output.count('\xa0')
print(f'✓ Preprocessing complete')
print(f'  - Non-breaking spaces removed: {nbsp_count}')
print(f'  - Output length: {len(stage1_output):,} characters')
print(f'  - Output lines: {len(stage1_output.splitlines())} lines')
print()

# Stage 2: HTML to Markdown conversion
print('=' * 70)
print('STAGE 2: HTML TO MARKDOWN CONVERSION')
print('=' * 70)
stage2_output = converter.process(stage1_output)
reduction_percent = round((1 - len(stage2_output) / len(stage1_output)) * 100, 1)
print(f'✓ Conversion complete')
print(f'  - Markdown length: {len(stage2_output):,} characters')
print(f'  - Markdown lines: {len(stage2_output.splitlines())} lines')
print(f'  - Size reduction: {reduction_percent}% smaller than preprocessed HTML')
print()

# Stage 3: Markdown polishing
print('=' * 70)
print('STAGE 3: MARKDOWN POLISHING')
print('=' * 70)
stage3_output = polisher.process(stage2_output)
print(f'✓ Polishing complete')
print(f'  - Rules applied: {polisher.rules}')
print(f'  - Final length: {len(stage3_output):,} characters')
print(f'  - Final lines: {len(stage3_output.splitlines())} lines')
print()

# Stage 4: Section Classification
print('=' * 70)
print('STAGE 4: SECTION CLASSIFICATION')
print('=' * 70)
sections = ruler.parse(stage3_output)
print(f'✓ Markdown parsing complete')
print(f'  - Sections detected: {len(sections)}')

# Classify each section
classified_sections = []
all_keyword_matches = []
section_types_count = {st.value: 0 for st in SectionType}
skip_count = 0

for section in sections:
    classification = classifier.classify(section)
    classified_sections.append((section, classification))
    all_keyword_matches.extend(classification.keyword_matches)

    # Track section types
    for section_type in classification.labels:
        section_types_count[section_type.value] += 1

    if classification.is_skip:
        skip_count += 1

print(f'✓ Section classification complete')
print(f'  - Sections classified: {len(classified_sections)}')
print(f'  - Total keyword matches: {len(all_keyword_matches)}')
print()

# Display Stage 4 results
print('SECTION CLASSIFICATION RESULTS')
print('-' * 70)
for i, (section, classification) in enumerate(classified_sections, 1):
    section_title = section.title if section.title else '(untitled)'
    print(f'\\nSection {i}: {section_title}')
    print(f'  Level: {section.level}, Words: {section.word_count}, Lines: {section.line_count}')
    print(f'  All Types:')
    for type_class in classification.all_types:
        print(f'    - {type_class.section_type.value}: confidence={type_class.confidence:.2f}, keywords={type_class.matched_keywords}')
    print(f'  Labels: {{{', '.join(t.value for t in classification.labels)}}}')
    print(f'  Is Skip: {classification.is_skip}')
    if classification.keyword_matches:
        print(f'  Keyword Matches:')
        for km in classification.keyword_matches:
            print(f'    - \"{km.keyword}\" ({km.section_type.value}) from {km.source} at position {km.position}')

print()

# Summary statistics
print('=' * 70)
print('PIPELINE SUMMARY')
print('=' * 70)
print(f'Input → Stage 1 (preprocessing):')
print(f'  {len(raw_html):,} chars → {len(stage1_output):,} chars (reduction: {round((1-len(stage1_output)/len(raw_html))*100, 1)}%)')
print()
print(f'Stage 1 → Stage 2 (conversion):')
print(f'  {len(stage1_output):,} chars → {len(stage2_output):,} chars (reduction: {round((1-len(stage2_output)/len(stage1_output))*100, 1)}%)')
print()
print(f'Stage 2 → Stage 3 (polishing):')
print(f'  {len(stage2_output):,} chars → {len(stage3_output):,} chars (change: {round((len(stage3_output)-len(stage2_output))/len(stage2_output)*100, 1)}%)')
print()
print(f'Total reduction (input → output):')
print(f'  {len(raw_html):,} chars → {len(stage3_output):,} chars (reduction: {round((1-len(stage3_output)/len(raw_html))*100, 1)}%)')
print()

# Stage 4 statistics
print('STAGE 4 STATISTICS')
print('-' * 70)
print(f'Total sections: {len(classified_sections)}')
print(f'Skip sections: {skip_count}')
print(f'Classified sections: {len(classified_sections) - skip_count}')
print()

# Section types breakdown
print('Section Types Breakdown:')
for section_type_value, count in sorted(section_types_count.items()):
    if count > 0:
        print(f'  - {section_type_value}: {count}')
print()

# Confidence statistics
if classified_sections:
    confidences = []
    for _, classification in classified_sections:
        if classification.all_types:
            confidences.append(classification.all_types[0].confidence)

    if confidences:
        min_conf = min(confidences)
        max_conf = max(confidences)
        avg_conf = sum(confidences) / len(confidences)
        print(f'Confidence Distribution (primary type):')
        print(f'  - Min: {min_conf:.2f}')
        print(f'  - Max: {max_conf:.2f}')
        print(f'  - Avg: {avg_conf:.2f}')
        print()

print(f'Total keyword matches: {len(all_keyword_matches)}')
print()

# Show sample output
print('=' * 70)
print('FINAL MARKDOWN OUTPUT (first 500 characters)')
print('=' * 70)
sample_len = min(500, len(stage3_output))
print(stage3_output[:sample_len])
if len(stage3_output) > 500:
    print(f'... ({len(stage3_output) - 500} more characters)')
print()

print('=' * 70)
print('✓ Pipeline processing complete (4 stages)')
print('=' * 70)
"

#!/bin/bash
# Process HTML through complete markdown pipeline (Issue #286 Phase 6)
# Demonstrates all 3 stages: HTMLPreprocessor, HTMLMarkdownConverter, MarkdownPolisher

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

Process HTML through complete markdown pipeline with all 3 stages:
1. HTMLPreprocessor: Clean HTML, normalize structure, remove non-breaking spaces
2. HTMLMarkdownConverter: Convert HTML to Markdown using MarkItDown
3. MarkdownPolisher: Apply formatting rules (line norm, list tightening, headers, etc.)

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

print('✓ Imports successful')
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
print('✓ Pipeline processing complete')
print('=' * 70)
"

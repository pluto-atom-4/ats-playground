#!/bin/bash

###############################################################################
# Script: inspect-extract-requirements-2.sh
# Purpose: Inspect POC requirement extraction results from fixture
#
# Reads raw job description from fixture file, passes to
# extract_requirements_from_markdown() function, and pretty-prints results
# showing company name, total requirement count, and top 5 requirements with
# confidence scores.
#
# Usage:
#   ./scripts/inspect-extract-requirements-2.sh
#
# Fixture file: ./tests/poc/fixtures/raw_job_description.md
# Python module: src/poc/extract_requirements.py
###############################################################################

set -e

# Configuration
FIXTURE_FILE="./tests/poc/fixtures/raw_job_description.md"
FALLBACK_FIXTURE="./tests/poc/fixtures/carbon_robotics_job.md"

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if fixture file exists
if [[ ! -f "$FIXTURE_FILE" ]]; then
    if [[ -f "$FALLBACK_FIXTURE" ]]; then
        echo -e "${BLUE}ℹ${NC} Primary fixture not found, using fallback: $FALLBACK_FIXTURE"
        FIXTURE_FILE="$FALLBACK_FIXTURE"
    else
        echo -e "${RED}✗${NC} Error: Fixture file not found ($FIXTURE_FILE or fallback)"
        echo "Available fixtures: $FALLBACK_FIXTURE"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Reading fixture: $FIXTURE_FILE"
echo ""

# Run Python extraction with error handling
uv run python -c "
import sys
import json

# Read fixture file
try:
    with open('$FIXTURE_FILE', 'r') as f:
        job_md = f.read()
    if not job_md.strip():
        print('Error: Fixture file is empty', file=sys.stderr)
        sys.exit(1)
except FileNotFoundError:
    print(f'Error: Fixture file not found: $FIXTURE_FILE', file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'Error reading fixture file: {e}', file=sys.stderr)
    sys.exit(1)

# Import and run extractor
try:
    from src.poc.extract_requirements import extract_requirements_from_markdown

    # Extract requirements
    output = extract_requirements_from_markdown(job_md)

    # Pretty-print results
    print(f'Company: {output.company}')
    print(f'Total Requirements: {output.requirements_count}')

    if output.requirements:
        print('Top Requirements:')
        for i, req in enumerate(output.requirements[:5], 1):
            print(f'  {i}. {req.text}')
            print(f'     Trigger: {req.trigger_word} | Confidence: {req.confidence:.2f} | Type: {req.span_type}')
    else:
        print('No requirements extracted.')

    print('')
    print('Metadata:')
    for key, value in output.metadata.items():
        print(f'  {key}: {value}')

except Exception as e:
    print(f'Error extracting requirements: {e}', file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
" 2>&1

# Exit status
if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✓${NC} Extraction completed successfully"
    exit 0
else
    echo ""
    echo -e "${RED}✗${NC} Extraction failed - see errors above"
    exit 1
fi

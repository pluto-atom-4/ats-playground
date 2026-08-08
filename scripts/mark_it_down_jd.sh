#!/usr/bin/env bash

# Exit immediately if a command fails or a variable is unbound
set -euo pipefail

# Print usage instructions if no arguments are provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <path_to_json_file> [array_index]" >&2
    echo "Example: $0 './data/extracted_jobs/blue origin_jobs.json' 1" >&2
    exit 1
fi

# Configuration from arguments
JSON_FILE="$1"
INDEX="${2:-1}" # Defaults to 1 if the second argument is omitted

# Validate that the target file exists
if [ ! -f "$JSON_FILE" ]; then
    echo "Error: File not found at '$JSON_FILE'" >&2
    exit 1
fi

echo "Converting job index $INDEX from '$JSON_FILE'..." >&2

# Execute the pipeline with the HTML parser fallback
jq -r ".[$INDEX] | .description" "$JSON_FILE" | python3 -c "
import sys, io
from markitdown import MarkItDown
try:
    raw_input = sys.stdin.read()
    if not raw_input.strip() or raw_input.strip() == 'null':
        print(f'Error: Index {sys.argv[1]} is out of bounds or contains no description.', file=sys.stderr)
        sys.exit(1)

    md = MarkItDown()
    byte_stream = io.BytesIO(raw_input.encode('utf-8'))
    result = md.convert_stream(byte_stream, file_extension='.html')
    print(result.text_content)
except Exception as e:
    print(f'Conversion Error: {e}', file=sys.stderr)
    sys.exit(1)
" "$INDEX"

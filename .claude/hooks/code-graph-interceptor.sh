#!/bin/bash
# .claude/hooks/code-graph-interceptor.sh
# Non-blocking PreToolUse hook (Issue #325): nudges toward querying the
# code graph (better-code-review-graph MCP server) before wide Glob/Grep
# scans. Never blocks the underlying tool call — mirrors the fail-open
# contract of pre-commit-no-main.sh.
set -euo pipefail

TOOL_NAME="${1:-}"

if [[ "$TOOL_NAME" == "Grep" || "$TOOL_NAME" == "Glob" ]]; then
  echo "[better-code-review-graph] Consider querying the code graph before broad scans."
fi

exit 0

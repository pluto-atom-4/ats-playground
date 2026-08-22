#!/bin/bash
# Gate 1 Plan Approval Hook
# Enforces that plan modifications (CLAUDE.md, AGENTS.md, .claude/settings.json) are approved
# Check: Requires "Approved:" in commit message or tasks.md reference

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "🔐 Gate 1: Plan Approval Check"

# Get recently modified files from git status
MODIFIED_FILES=$(git status --short 2>/dev/null || echo "")

# Check if any gate-1 files were modified
FILE_TYPE=""
if echo "$MODIFIED_FILES" | grep -E "(CLAUDE\.md|AGENTS\.md|\.claude/settings\.json)" > /dev/null; then
    # Extract the specific file(s) modified
    if echo "$MODIFIED_FILES" | grep -q "CLAUDE\.md"; then
        FILE_TYPE="CLAUDE.md"
    elif echo "$MODIFIED_FILES" | grep -q "AGENTS\.md"; then
        FILE_TYPE="AGENTS.md"
    elif echo "$MODIFIED_FILES" | grep -q "\.claude/settings\.json"; then
        FILE_TYPE=".claude/settings.json"
    else
        exit 0
    fi
else
    # No gate-1 files modified, skip check
    exit 0
fi

echo "📋 Checking plan approval for: $FILE_TYPE"

# Check if tasks.md exists and contains "Approved:"
if [ -f "tasks.md" ]; then
    if grep -q "Approved:" tasks.md; then
        echo "✅ Plan approval found in tasks.md"
        exit 0
    fi
fi

# Check git log for recent commit with "Approved:" or "Gate 1" reference
if git log --oneline -n 5 2>/dev/null | grep -E "(Approved:|Gate 1)" > /dev/null; then
    echo "✅ Plan approval found in recent commits"
    exit 0
fi

# No approval found
echo "⚠️  No plan approval detected for $FILE_TYPE modification"
echo ""
echo "Before modifying instruction files, ensure:"
echo "  1. Tasks are defined in tasks.md with 'Approved:' marker"
echo "  2. Or last commit message includes 'Approved:' or 'Gate 1'"
echo ""
echo "Examples:"
echo "  - 'Approved: Issue #212 Phase 3 implementation'"
echo "  - 'Gate 1: Plan review complete'"
echo ""
echo "⚠️  This is a warning. Changes will be allowed but flagged for review."
exit 0

#!/bin/bash
# Local CI: Run code quality checks on staged files
# Usage: bash .claude/scripts/run-local-ci.sh [--tests] [--strict]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Parse arguments
RUN_TESTS=false
STRICT_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --tests)
            RUN_TESTS=true
            shift
            ;;
        --strict)
            STRICT_MODE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: bash .claude/scripts/run-local-ci.sh [--tests] [--strict]"
            exit 1
            ;;
    esac
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Local CI: Code Quality Checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Step 1: Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Install with: pip install uv"
    exit 1
fi

# Step 2: Validate pre-commit config
echo "📋 Step 1/5: Validating pre-commit config..."
if ! uv run pre-commit validate-config > /dev/null 2>&1; then
    echo "❌ Pre-commit config validation failed"
    exit 1
fi
echo "✅ Pre-commit config valid"
echo

# Step 3: Run pre-commit hooks over the full branch diff vs main
echo "🔍 Step 2/5: Running pre-commit hooks (branch diff vs main)..."

# Resolve a base ref to diff against (prefer local main, fall back to origin/main).
BASE_REF=""
for candidate in main origin/main; do
    if git rev-parse --verify "$candidate" > /dev/null 2>&1; then
        BASE_REF="$candidate"
        break
    fi
done

FROM_REF="HEAD~1"
if [ -n "$BASE_REF" ]; then
    if MERGE_BASE=$(git merge-base "$BASE_REF" HEAD 2>/dev/null); then
        if [ "$MERGE_BASE" = "$(git rev-parse HEAD)" ]; then
            # HEAD has no divergent commits vs the base (e.g. running on main itself).
            # Diffing HEAD..HEAD would check nothing, so fall back to the last commit.
            echo "⚠️  HEAD has no commits ahead of $BASE_REF; falling back to HEAD~1"
        else
            FROM_REF="$MERGE_BASE"
        fi
    else
        echo "⚠️  No merge-base found with $BASE_REF; falling back to HEAD~1 (only last commit will be linted)"
    fi
else
    echo "⚠️  Could not resolve local 'main' or 'origin/main'; falling back to HEAD~1 (only last commit will be linted)"
fi

if ! uv run pre-commit run --from-ref "$FROM_REF" --to-ref HEAD 2>&1 | tee /tmp/precommit.log; then
    echo "❌ Pre-commit hooks failed"
    cat /tmp/precommit.log
    exit 1
fi
echo "✅ Pre-commit hooks passed"
echo

# Step 4: Run mypy type checking
echo "🔎 Step 3/5: Type checking with mypy..."
MYPY_ARGS="--python-version=3.12 --ignore-missing-imports"
if [ "$STRICT_MODE" = true ]; then
    MYPY_ARGS="--strict"
fi

if ! uv run mypy src/ $MYPY_ARGS > /tmp/mypy.log 2>&1; then
    echo "❌ mypy type checking failed"
    cat /tmp/mypy.log
    exit 1
fi
echo "✅ Type checking passed"
echo

# Step 5: Optional - Run tests
if [ "$RUN_TESTS" = true ]; then
    echo "🧪 Step 4/5: Running tests..."
    export PYTHONPATH="${PROJECT_ROOT}/src:$PYTHONPATH"
    if ! uv run pytest tests/ -v --tb=short > /tmp/pytest.log 2>&1; then
        echo "❌ Tests failed"
        cat /tmp/pytest.log
        exit 1
    fi
    echo "✅ All tests passed"
    echo
    STEP_COUNT=5
else
    STEP_COUNT=4
fi

# Final summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All $STEP_COUNT checks passed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "💡 Tip: Use 'git commit' to commit staged changes"
echo "   Use '--tests' to also run pytest: bash .claude/scripts/run-local-ci.sh --tests"
echo "   Use '--strict' for strict mypy mode: bash .claude/scripts/run-local-ci.sh --strict"

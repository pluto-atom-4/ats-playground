#!/bin/bash
# Measure context efficiency: token count in instruction files
# Baseline for Phase 2 improvement tracking

set -e

echo "📊 Context Efficiency Baseline"
echo "================================"
echo ""

# Check if python + tiktoken available
if ! python3 -c "import tiktoken" 2>/dev/null; then
  echo "⚠️  tiktoken not installed. Install: pip install tiktoken"
  echo "Using line count estimation instead (tokens ≈ lines * 4)"
  USE_TIKTOKEN=false
else
  USE_TIKTOKEN=true
fi

# Function to count tokens
count_tokens() {
  local file=$1
  if [ "$USE_TIKTOKEN" = true ]; then
    python3 << EOF
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")
with open("$file", "r") as f:
    text = f.read()
tokens = len(enc.encode(text))
print(tokens)
EOF
  else
    # Fallback: lines * 4 (rough estimate)
    wc -l < "$file" | awk '{print int($1 * 4)}'
  fi
}

# Core instruction files
FILES=(
  "CLAUDE.md"
  "AGENTS.md"
  "DESIGN.md"
  ".github/copilot-instructions.md"
)

# Phase-specific rules
RULES_FILES=(
  ".claude/rules/crawl.md"
  ".claude/rules/preprocess.md"
  ".claude/rules/verify.md"
  ".claude/rules/assess.md"
  ".claude/rules/storage.md"
  ".claude/rules/cli.md"
  ".claude/rules/multi-agent.md"
)

TOTAL_TOKENS=0
TOTAL_LINES=0

echo "📄 Core Instruction Files"
echo "------------------------"
for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    lines=$(wc -l < "$file")
    tokens=$(count_tokens "$file")
    TOTAL_TOKENS=$((TOTAL_TOKENS + tokens))
    TOTAL_LINES=$((TOTAL_LINES + lines))
    printf "%-40s %6d lines | %7d tokens\n" "$file" "$lines" "$tokens"
  fi
done

echo ""
echo "📋 Phase-Specific Rules"
echo "----------------------"
RULES_TOKENS=0
RULES_LINES=0
for file in "${RULES_FILES[@]}"; do
  if [ -f "$file" ]; then
    lines=$(wc -l < "$file")
    tokens=$(count_tokens "$file")
    RULES_TOKENS=$((RULES_TOKENS + tokens))
    RULES_LINES=$((RULES_LINES + lines))
    printf "%-40s %6d lines | %7d tokens\n" "$file" "$lines" "$tokens"
  fi
done

TOTAL_TOKENS=$((TOTAL_TOKENS + RULES_TOKENS))
TOTAL_LINES=$((TOTAL_LINES + RULES_LINES))

echo ""
echo "================================"
printf "%-40s %6d lines | %7d tokens\n" "TOTAL (Core + Rules)" "$TOTAL_LINES" "$TOTAL_TOKENS"
echo "================================"
echo ""
echo "💾 Context Budget: ~150KB (18K tokens @ 8K ctx window)"
echo "📊 Current usage: $(echo "scale=1; $TOTAL_TOKENS / 18000 * 100" | bc)% of budget"
echo ""
echo "🎯 Phase 2 Target: 15% reduction ($(echo "scale=0; $TOTAL_TOKENS * 0.85" | bc) tokens)"
echo ""

# Save baseline
mkdir -p .claude/metrics
cat > .claude/metrics/context-baseline.json << EOF
{
  "phase": "Phase 2",
  "date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total_lines": $TOTAL_LINES,
  "total_tokens": $TOTAL_TOKENS,
  "core_lines": $TOTAL_LINES,
  "core_tokens": $TOTAL_TOKENS,
  "target_tokens": $(echo "scale=0; $TOTAL_TOKENS * 0.85" | bc),
  "encoding": "cl100k_base"
}
EOF

echo "✅ Baseline saved to .claude/metrics/context-baseline.json"

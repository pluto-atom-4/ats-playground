#!/bin/bash
# Validate path-scoping: verify rules load for correct file contexts

set -e

echo "🔍 Path-Scoping Validation"
echo "=========================="
echo ""

ERRORS=0

# 1. Verify settings.json has pathScoping section
echo "1️⃣  Checking settings.json pathScoping..."
if grep -q '"pathScoping"' .claude/settings.json; then
  echo "✅ pathScoping section present"
else
  echo "❌ pathScoping section missing"
  ((ERRORS++))
fi

# 2. Verify all phase rules are referenced
echo ""
echo "2️⃣  Checking phase rule references..."
RULES=(
  "crawl.md:src/browser/**"
  "preprocess.md:src/parsers/**|src/tokenization/**"
  "assess.md:src/llm/**|src/assessment/**"
  "cli.md:src/cli.py"
  "verify.md:src/cli/**"
  "storage.md:src/storage/**"
  "multi-agent.md:tasks.md|.claude/**"
)

for rule in "${RULES[@]}"; do
  rule_file="${rule%%:*}"
  path_patterns="${rule##*:}"

  if [ -f ".claude/rules/$rule_file" ]; then
    echo "✅ .claude/rules/$rule_file exists"
  else
    echo "❌ .claude/rules/$rule_file missing"
    ((ERRORS++))
  fi
done

# 3. Verify copilot-instructions.md has pathScoping directives
echo ""
echo "3️⃣  Checking .github/copilot-instructions.md frontmatter..."
if head -20 .github/copilot-instructions.md | grep -q "pathScoping:"; then
  echo "✅ Copilot instructions have pathScoping directives"
else
  echo "❌ Copilot instructions missing pathScoping"
  ((ERRORS++))
fi

# 4. Verify skill frontmatter has allowed_tools
echo ""
echo "4️⃣  Checking skill frontmatter (allowed_tools)..."
SKILLS=(
  "crawl-jobs"
  "assess-jobs"
  "pre-commit-enforce"
)

for skill in "${SKILLS[@]}"; do
  skill_file=".claude/skills/$skill/SKILL.md"
  if [ -f "$skill_file" ]; then
    if grep -q "^allowed_tools:" "$skill_file"; then
      echo "✅ $skill/SKILL.md has allowed_tools"
    else
      echo "❌ $skill/SKILL.md missing allowed_tools"
      ((ERRORS++))
    fi
  else
    echo "⚠️  $skill_file not found (skipping)"
  fi
done

# 5. Verify consistency: same tool constraints in settings.json + copilot-instructions.md
echo ""
echo "5️⃣  Checking tool constraint sync (settings.json ↔ copilot-instructions.md)..."
CONSTRAINTS=("rm -rf" "git push --force" "git reset --hard" ".env")

for constraint in "${CONSTRAINTS[@]}"; do
  if grep -q "$constraint" .claude/settings.json && grep -q "$constraint" .github/copilot-instructions.md; then
    echo "✅ '$constraint' synced"
  else
    echo "❌ '$constraint' NOT synced"
    ((ERRORS++))
  fi
done

# 6. Verify DESIGN.md links to phase rules (not duplicating)
echo ""
echo "6️⃣  Checking DESIGN.md references (should link, not duplicate)..."
if grep -q ".claude/rules/" DESIGN.md; then
  echo "✅ DESIGN.md references .claude/rules/"
else
  echo "⚠️  DESIGN.md should reference .claude/rules/ (optional)"
fi

# Summary
echo ""
echo "=========================="
if [ $ERRORS -eq 0 ]; then
  echo "✅ All path-scoping validations passed"
  exit 0
else
  echo "❌ $ERRORS path-scoping error(s) found"
  exit 1
fi

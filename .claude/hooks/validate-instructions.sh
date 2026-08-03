#!/bin/bash
# Validation hook: Enforce instruction compliance
# Runs on Edit/Write to CLAUDE.md, AGENTS.md, skills, settings.json
# Checks: line counts, frontmatter validity, no duplication

set -e

ERRORS=0

echo "🔍 Validating instruction files..."

# 1. CLAUDE.md: must be <200 lines
if [ -f CLAUDE.md ]; then
  lines=$(wc -l < CLAUDE.md)
  if [ "$lines" -gt 200 ]; then
    echo "❌ CLAUDE.md: $lines lines (max 200)"
    ((ERRORS++))
  else
    echo "✅ CLAUDE.md: $lines lines (<200)"
  fi
fi

# 2. AGENTS.md: must be <150 lines
if [ -f AGENTS.md ]; then
  lines=$(wc -l < AGENTS.md)
  if [ "$lines" -gt 150 ]; then
    echo "❌ AGENTS.md: $lines lines (max 150)"
    ((ERRORS++))
  else
    echo "✅ AGENTS.md: $lines lines (<150)"
  fi
fi

# 3. Check all skills have frontmatter with allowed_tools
if [ -d .claude/skills ]; then
  while IFS= read -r skill_file; do
    skill_name=$(basename "$(dirname "$skill_file")")

    # Check for frontmatter
    if ! head -5 "$skill_file" | grep -q "^---$"; then
      echo "❌ $skill_name/SKILL.md: missing frontmatter (---)"
      ((ERRORS++))
      continue
    fi

    # Check for allowed_tools
    if ! grep -q "^allowed_tools:" "$skill_file"; then
      echo "❌ $skill_name/SKILL.md: missing allowed_tools field"
      ((ERRORS++))
    else
      echo "✅ $skill_name/SKILL.md: has allowed_tools"
    fi
  done < <(find .claude/skills -name "SKILL.md" -type f | grep -v TEMPLATE)
fi

# 4. Validate settings.json JSON syntax
if [ -f .claude/settings.json ]; then
  if ! python3 -m json.tool .claude/settings.json > /dev/null 2>&1; then
    echo "❌ .claude/settings.json: invalid JSON"
    ((ERRORS++))
  else
    echo "✅ .claude/settings.json: valid JSON"
  fi

  # Check for pathScoping field
  if ! grep -q '"pathScoping"' .claude/settings.json; then
    echo "⚠️  .claude/settings.json: missing pathScoping (optional but recommended)"
  else
    echo "✅ .claude/settings.json: has pathScoping"
  fi
fi

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
  echo "✅ All instruction validations passed"
  exit 0
else
  echo "❌ $ERRORS validation error(s) found"
  exit 1
fi

---
name: reviewer
description: Verify code quality and implementation requirements against test suite and linting standards
model: claude-haiku-4.5 # Haiku provides cost-efficient, lightning-fast code reviews
tools:
  - Read
  - Grep
  - Bash
permissions:
  bash:
    ask: ["gh pr comment"]
---

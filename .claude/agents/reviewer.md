---
name: reviewer
description: Verify code quality and implementation requirements against test suite and linting standards
model: haiku # Haiku provides cost-efficient, lightning-fast code reviews
tools:
  - Read
  - Grep
  - Bash
permissions:
  bash:
    ask: ["gh pr comment"]
---

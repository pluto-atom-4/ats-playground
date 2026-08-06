---
model: claude-3-5-haiku # Haiku provides cost-efficient, lightning-fast code reviews
tools:
  - Read
  - Grep
  - Bash
permissions:
  bash:
    ask: ["gh pr comment"]
---

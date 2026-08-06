---
model: claude-3-7-sonnet # Use a strong coding model for synthesis
tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
permissions:
  write:
    deny: ["AGENTS.md", "CLAUDE.md", ".claude/agents/**", ".claude/rules/**", ".claude/skills/**", ".claude/settings.json"] # Prevent governance file modification
  bash:
    allow: ["npm test", "cargo test", "pytest"] # Pre-approve testing commands
    ask: ["gh pr create", "gh pr comment"]
---

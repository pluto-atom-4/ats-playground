---
name: architect
description: Draft implementation plans, design module boundaries, and write architectural decisions
model: claude-sonnet-5 # Use Sonnet or Opus for deep planning & architecture
tools:
  - Read
  - Grep
  - Glob
  - Bash
permissions:
  bash:
    allow: ["gh issue create", "gh issue list", "gh issue comment"]
    ask: ["*"] # Prompts human before executing destructive or arbitrary commands
---

## Code Graph Tooling (Issue #325)

Before wide `Grep`/`Glob` scans, query the `better-code-review-graph` MCP
server (registered globally, DB isolated per-project via
`CRG_DATABASE_PATH=./.claude/crg_cache_better.db`) for structural
context — caller/callee chains, module boundaries — instead of grepping
the whole tree cold. Falls back to normal Grep/Glob if the graph has no
answer or the server is unavailable (no hard dependency).

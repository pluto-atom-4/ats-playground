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

## Code Graph Tooling (Issue #325, #328)

Before wide `Grep`/`Glob` scans, query the `code-review-graph` MCP
server (registered globally, DB isolated per-project — auto-detected
`repo_root` → `<repo_root>/.code-review-graph/graph.db`, no env var
involved) for structural context — caller/callee chains, module
boundaries, blast-radius (`impact --files ...`) — instead of grepping
the whole tree cold. Falls back to normal Grep/Glob if the graph has no
answer or the server is unavailable (no hard dependency). Details:
[.claude/README.md](../README.md).

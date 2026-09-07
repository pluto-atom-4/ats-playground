# .claude/ Directory

Claude Code configuration for ATS Playground. See [AGENTS.md](../AGENTS.md) for
role governance and [CLAUDE.md](../CLAUDE.md) for setup/workflow.

## Code Graph Tooling (Issue #325)

**Tool:** [`better-code-review-graph`](https://github.com/n24q02m/better-code-review-graph)
(AST/Tree-sitter + SQLite structural analysis) — MCP server, registered
**globally** at `~/.claude/settings.json`, DB isolated per-project.

```jsonc
// ~/.claude/settings.json (excerpt)
"mcpServers": {
  "better-code-review-graph": {
    "type": "stdio",
    "command": "better-code-review-graph",
    "args": [],
    "env": {
      "MCP_TRANSPORT": "stdio",
      "CRG_DATABASE_PATH": "./.claude/crg_cache_better.db"
    }
  }
}
```

Uses the tool already on `PATH` (`uv tool install "better-code-review-graph[security]==3.24.0"`,
resolved at `~/.local/bin/better-code-review-graph`) directly — no `uvx`
re-resolution per launch. Check/upgrade the pinned version with:
```bash
uv tool list | grep better-code-review-graph
uv tool install --force "better-code-review-graph[security]==3.24.0"
```

- **DB isolation:** `CRG_DATABASE_PATH` is a `./`-relative path, resolved
  against each project's cwd — prevents cross-project SQLite contamination
  when the same global MCP entry is used from multiple repos.
- **Usage:** Architect queries the graph for caller/callee chains and
  module boundaries before wide `Grep`/`Glob` scans (see
  `.claude/agents/architect.md` and `.claude/rules/multi-agent.md`).
- **Advisory hook:** `.claude/hooks/graphify-interceptor.sh` fires on
  `Grep`/`Glob` `PreToolUse` and prints a one-line reminder to check the
  graph first. Never blocks the tool call (fail-open, matches
  `pre-commit-no-main.sh`'s contract).
- **Re-indexing:** `.pre-commit-config.yaml`'s `graph-reindex` hook
  (`stages: [post-checkout]`) rebuilds the graph on branch switch. Non-
  fatal — no-ops if `better-code-review-graph` isn't installed. Installed
  locally via `uv run pre-commit install --hook-type post-checkout`.
- **Manual rebuild:**
  ```bash
  CRG_DATABASE_PATH=./.claude/crg_cache_better.db \
    better-code-review-graph graph build \
    --exclude "**/tests/**,**/.venv/**,**/data/**,**/logs/**,**/models/**,**/.spacy_models/**,**/htmlcov/**,**/*.db"
  ```
- **Verify operational:** run `/status` inside Claude Code and confirm
  `better-code-review-graph` is listed as a connected MCP server.

## Considered and Declined

- **Graphify** (multi-modal code+PR+docs+schema graph, `GRAPH_REPORT.md`
  generation, `/graphify` slash commands): install path unverifiable at
  plan time (no confirmed PyPI/uv package). Dropped from scope. Revisit if
  a verifiable install path surfaces.
- **Base `code-review-graph`** (upstream of the `better-` fork): same
  unverifiable-install-path concern; the `better-code-review-graph` fork
  alone covers the structural-analysis need. Dropped from scope.
- **Network allowlist expansion**: no new domains required — `uv tool
  install` pulls from PyPI, already allowed in `.claude/settings.json`'s
  `sandbox.network.allowedDomains`; the MCP server itself invokes the
  already-installed binary directly, no network use at launch.

See the [Issue #325 plan comment](https://github.com/pluto-atom-4/ats-showcase/issues/325#issuecomment-5561445016)
for the full decision record.

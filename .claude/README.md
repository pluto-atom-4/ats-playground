# .claude/ Directory

Claude Code configuration for ATS Playground. See [AGENTS.md](../AGENTS.md) for
role governance and [CLAUDE.md](../CLAUDE.md) for setup/workflow.

## Code Graph Tooling (Issue #325)

**Tool:** [`better-code-review-graph`](https://github.com/n24q02m/better-code-review-graph)
(AST/Tree-sitter + SQLite structural analysis) — MCP server, registered
**globally** at `~/.claude/settings.json`, DB isolated per-project.

```jsonc
// ~/.claude/settings.json (excerpt, matches actual applied config)
"mcpServers": {
  "better-code-review-graph": {
    "type": "stdio",
    "command": "better-code-review-graph",
    "args": []
  }
}
```

No `env` block needed: `MCP_TRANSPORT` only matters when set to `"http"`
(verified against installed source — `credential_state.py`/`server.py`
both check `== "http"`); omitting it defaults to stdio, which is what's
wanted here.

Uses the tool already on `PATH` (`uv tool install "better-code-review-graph[security]==3.24.0"`,
resolved at `~/.local/bin/better-code-review-graph`) directly — no `uvx`
re-resolution per launch. Check/upgrade the pinned version with:
```bash
uv tool list | grep better-code-review-graph
uv tool install --force "better-code-review-graph[security]==3.24.0"
```

- **DB isolation:** no `CRG_DATABASE_PATH` env var exists in v3.24.0 (verified
  against installed package source — invented in the original issue draft).
  Isolation instead comes from the tool's own auto-detection: it resolves
  `repo_root` from cwd and stores the graph at
  `<repo_root>/.code-review-graph/graph.db` — one directory per repo,
  no cross-project contamination as long as Claude Code launches the MCP
  server with this repo as cwd (the default for project-scoped sessions).
- **Usage:** Architect queries the graph for caller/callee chains and
  module boundaries before wide `Grep`/`Glob` scans (see
  `.claude/agents/architect.md` and `.claude/rules/multi-agent.md`).
- **Advisory hook:** `.claude/hooks/code-graph-interceptor.sh` fires on
  `Grep`/`Glob` `PreToolUse` and prints a one-line reminder to check the
  graph first. Never blocks the tool call (fail-open, matches
  `pre-commit-no-main.sh`'s contract).
- **Re-indexing:** `.pre-commit-config.yaml`'s `graph-reindex` hook
  (`stages: [post-checkout]`) rebuilds the graph on branch switch. Non-
  fatal — no-ops if `better-code-review-graph` isn't installed. Installed
  locally via `uv run pre-commit install --hook-type post-checkout`.
- **Manual rebuild:**
  ```bash
  better-code-review-graph graph build
  ```
  No `--exclude` flag exists (verified against installed CLI: `graph build`
  takes no such option). Excludes come from `.gitignore` (respected
  automatically, on top of the tool's own defaults — `.venv/`, `node_modules/`,
  `.git/`, `__pycache__/`, `dist/`, `build/`, etc.) plus its default
  `.code-review-graph/**` self-exclude. `tests/` is not gitignored in this
  repo, so it gets parsed too — harmless, just extra nodes in the graph.
- **Verify operational:** run `/status` inside Claude Code and confirm
  `better-code-review-graph` is listed as a connected MCP server.

## Graphify (Issue #325 — revisited)

**Tool:** [`graphify`](https://github.com/Graphify-Labs/graphify) — PyPI
package `graphifyy` (installed as `graphify` CLI + `graphify-mcp` MCP
server, `uv tool install graphifyy`). Originally declined for an
unverifiable install path; that path is now verified (`graphifyy==0.9.55`
resolves from PyPI, both binaries confirmed on `PATH`).

- **What it's for:** multi-modal macro map (code + docs + PDFs + DB
  schemas), Leiden-clustered "communities", `GRAPH_REPORT.md` — the
  high-level counterpart to `better-code-review-graph`'s low-level
  AST/blast-radius queries. Phase 1 (macro) → Phase 2 (micro) handoff.
- **Global MCP registration** (`~/.claude/settings.json`, alongside
  `better-code-review-graph`):
  ```jsonc
  "graphify": {
    "type": "stdio",
    "command": "graphify-mcp",
    "args": []
  }
  ```
  `args: []` — the positional `graph_path` defaults to
  `graphify-out/graph.json`, resolved from Claude Code's cwd (same
  per-repo isolation pattern as `better-code-review-graph`; no cross-
  project contamination as long as each session's cwd is this repo).
- **Project permissions** (`.claude/settings.json`): `Bash(graphify
  query *)`, `Bash(graphify path *)`, `Bash(graphify explain *)`,
  `Bash(graphify affected *)`, `Bash(graphify god-nodes*)`,
  `Bash(graphify update .)` allow-listed.
- **Build the graph:** `graphify update .` — AST-only, no LLM/API key,
  incremental by default (`--force` for a clean rebuild). Full
  multi-modal extraction (docs/PDFs/schemas via LLM) is a separate,
  explicit opt-in: `graphify extract . --backend claude`.
- **CLAUDE.md wiring:** `graphify claude install` writes a routing
  section into [CLAUDE.md](../CLAUDE.md) and registers its own
  PreToolUse hook (surfaces `graphify-out/GRAPH_REPORT.md` before a
  broad Grep/Glob) — no hand-written interceptor script for this one;
  `graphify claude uninstall` removes both cleanly.
- **Re-indexing:** *not* wired via `graphify hook install` — that
  command manages `.git/hooks/post-checkout` directly, which would
  clobber the pre-commit-managed hook already installed for
  `better-code-review-graph`'s reindex. Instead, `.pre-commit-config.yaml`'s
  `graph-reindex` local hooks block runs `graphify update .` alongside
  `better-code-review-graph graph build`, both non-fatal, both
  `stages: [post-checkout]`.
- **gitignore:** `graphify-out/`, `.graphify_cache/`, `GRAPH_REPORT.md`
  added — unlike `.code-review-graph/`, graphify's output isn't
  self-ignoring.

## Considered and Declined

- **Base `code-review-graph`** (upstream of the `better-` fork): same
  unverifiable-install-path concern that originally applied to Graphify;
  the `better-code-review-graph` fork alone covers the structural-
  analysis need. Still dropped from scope.
- **Network allowlist expansion**: no new domains required — `uv tool
  install` pulls from PyPI, already allowed in `.claude/settings.json`'s
  `sandbox.network.allowedDomains`; both MCP servers invoke already-
  installed binaries directly, no network use at launch.

See the [Issue #325 plan comment](https://github.com/pluto-atom-4/ats-showcase/issues/325#issuecomment-5561445016)
for the original decision record (Graphify's decline is superseded by
the section above).

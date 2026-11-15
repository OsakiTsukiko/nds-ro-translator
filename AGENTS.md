# Codex instructions

Read `CLAUDE.md` before working: it holds the shared instructions for every AI agent in this project.
Follow its reading order (`guides/00_WORKFLOW.md`, `docs/STATUS.md`, then the relevant phase guide).
Run project commands from the repository root and update `docs/STATUS.md` at the end of the session.

## REA tools

- Use the REA MCP tools exposed by your client. Discover available tools and their schemas before calling them;
  tool names and discovery mechanisms vary between clients. The `mcp__rea__*` names in the guides identify
  REA operations, not a required Codex namespace.
- `ToolSearch` examples in the guides apply to Claude Code. In Codex, use the available tool discovery
  mechanism; if tools are already exposed, use their supplied schemas directly.
- If REA is unavailable, continue work that uses the local Python tools. Report the missing connection when
  the next step requires REA; never invent reverse-engineering results.

See `README.md` for Codex launch and MCP setup instructions.

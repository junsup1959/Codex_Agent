# Codex Context Ledger MCP

SQLite-backed stdio MCP server for Codex run-level orchestration state. It is intended to replace fragile resident-agent memory with a durable context authority that stores `context_packet` revisions, artifact references, stage passes, readiness flags, stale markers, and MCP cleanup snapshots.

## Framework

This project uses the Python MCP SDK `FastMCP` framework:

```python
from mcp.server.fastmcp import FastMCP
```

`FastMCP` handles stdio JSON-RPC framing and tool registration, so the server code can stay focused on ledger operations.

## Run

```powershell
cd C:\project\mcp\context-ledger
uv run codex-context-ledger
```

By default the database is created at `data/context-ledger.sqlite`. Override it with:

```powershell
$env:CODEX_CONTEXT_LEDGER_DB='C:\Users\junsu\.codex\state\context-ledger.sqlite'
uv run codex-context-ledger
```

## Codex Registration

```powershell
cmd /c codex mcp add codex-context-ledger -- uv --directory C:\project\mcp\context-ledger run codex-context-ledger
```

## Tools

- `initialize_run`: create or reopen a run.
- `read_context_packet`: read the latest or requested context revision.
- `write_context_packet`: append a new context packet revision.
- `record_artifact_ref`: attach an artifact reference to a run.
- `append_stage_pass`: append stage pass evidence.
- `set_role_pass_readiness`: set readiness for a role pass.
- `mark_stale`: record stale context or artifact markers.
- `record_mcp_quiescence`: store MCP cleanup evidence.
- `validate_context_revision`: check whether a caller has the current revision.
- `query_run_ledger`: return a compact run ledger snapshot.
- `close_run`: mark a run closed.


# Codex Context Ledger MCP

SQLite-backed localhost MCP server for Codex run-level orchestration state. It is intended to replace fragile resident-agent memory with a durable context authority that stores `context_packet` revisions, artifact references, stage passes, readiness flags, stale markers, and MCP cleanup snapshots.

## Framework

This project uses the Python MCP SDK `FastMCP` framework:

```python
from mcp.server.fastmcp import FastMCP
```

`FastMCP` handles streamable HTTP packet framing and tool registration, so the server code can stay focused on ledger operations. The Codex architecture registration uses localhost streamable HTTP only.

## Run

```powershell
cd .\mcp\context-ledger
uv run codex-context-ledger
```

The default transport is local streamable HTTP at `http://127.0.0.1:8765/mcp`.

```powershell
.\scripts\start-http.ps1
```

By default the database is created at `data/context-ledger.sqlite`. Override it with:

```powershell
$env:CODEX_CONTEXT_LEDGER_DB=(Join-Path $env:CODEX_HOME 'state\context-ledger.sqlite')
uv run codex-context-ledger
```

## Codex Registration

```powershell
codex mcp add codex-context-ledger --url http://127.0.0.1:8765/mcp
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
- `validate_stage_packet`: validate each architecture stage packet through the MCP API.
- `validate_tool_sequence`: validate that the stage called the required MCP tools in order.
- `query_run_ledger`: return a compact run ledger snapshot.
- `close_run`: mark a run closed.

## Stage Validation Flow

Every mandatory skill calls the MCP tools in this order:

1. `read_context_packet`
2. `validate_context_revision`
3. `append_stage_pass`
4. `validate_stage_packet`
5. `write_context_packet`
6. `record_mcp_quiescence`
7. `validate_tool_sequence`

`orchestrator` additionally calls `initialize_run` before reading context. `context-ledger` additionally calls `set_role_pass_readiness` before writing the next packet.

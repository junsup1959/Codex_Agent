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
- `validate_stage_packet`: validate each architecture stage packet through the MCP API, including `sequential_thinking_ref` or `sequential_thinking_waiver` for orchestrator.
- `validate_task_design`: validate task design options, selected option, rationale, distribution boundaries, artifact profile, and `sequential_thinking_ref` or `sequential_thinking_waiver`.
- `validate_execution_plan`: validate task distribution criteria references, worker lanes, dependencies, fanout shape, artifact profile, and `sequential_thinking_ref` or `sequential_thinking_waiver`.
- `validate_review_plan`: validate review distribution criteria references, reviewer lanes, coverage shape, artifact profile, and `sequential_thinking_ref` or `sequential_thinking_waiver`.
- `validate_stage_completion`: validate completion readiness separately from packet shape.
- `validate_tool_sequence`: validate that the stage called the required MCP tools in order.
- `query_run_ledger`: return a compact run ledger snapshot.
- `close_run`: mark a run closed.

## Next Stage Guidance

`validate_stage_packet`, `write_context_packet`, and `read_context_packet` return a `next_stage` object when a next owner is known. This makes the handoff explicit in the MCP response instead of requiring the caller to infer it from docs.

Example:

```json
{
  "next_stage": {
    "owner": "worker",
    "activation_ref": "$worker",
    "contract_ref": "skills/worker/contract.json",
    "source_docs": ["03-worker-materialization.md", "06-agent-roster-models.md"],
    "required_input_artifacts": ["execution_plan", "task_distribution_criteria_ref", "context_packet", "fanout_budget"],
    "required_mcp_tools": [
      "read_context_packet",
      "validate_context_revision",
      "append_stage_pass",
      "validate_stage_packet",
      "validate_stage_completion",
      "write_context_packet",
      "record_mcp_quiescence",
      "validate_tool_sequence"
    ],
    "action": "activate $worker; read only its SKILL.md, adjacent contract.json, and the listed source_docs"
  }
}
```

`validate_stage_packet.next_stage` is based on the expected next owner for the current stage. `write_context_packet.next_stage` and `read_context_packet.next_stage` are based on the persisted packet's `next_owner`.

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

`orchestrator`, `task-designer`, `task-distributor`, and `review-distributor` must attempt external `MCP_DOCKER.sequentialthinking` before finalizing their artifacts and must preserve `sequential_thinking_ref` or `sequential_thinking_waiver`. Tool failure is recorded as waiver evidence and does not stop the stage. This is required reasoning evidence, but it is not part of the ordered `codex-context-ledger` tool sequence.

`task-designer` calls `validate_task_design` between `validate_stage_packet` and `write_context_packet`. `task-distributor` calls `validate_execution_plan` in that same position. `review-distributor` calls `validate_review_plan`.

`worker`, `review`, and `feedbackgate` also call `validate_stage_completion` between `validate_stage_packet` and `write_context_packet`; `validate_tool_sequence` requires that call for those stages.

`validate_stage_packet` is a schema and barrier check. Empty worker or review handoff lists can be schema-valid when the packet is still only a minimal stage shape. Use `validate_stage_completion` for final-readiness checks that require worker/review handoffs, well-formed missing-lane classifications, well-formed review waivers, feedback gate evidence, current pass evidence, and feedback-loop `task_design_reentry_decision`. Feedback loops also require `reentry_cache` in the next context packet.

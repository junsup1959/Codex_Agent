---
name: context-ledger
description: Execute the mandatory global Codex Context Ledger stage. Use when architecture-required work must sync approved facts, constraints, artifacts, and stale markers through the codex-context-ledger MCP before task planning.
---

# Context Ledger

Use this skill after `$orchestrator`. The source of truth is the localhost `codex-context-ledger` MCP API, not chat memory or a physical resident context agent.

## MCP Tool Sequence

Call these tools in order with `stage_name="context-ledger"` where accepted.

1. `read_context_packet(run_id, stage_name)`
2. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
3. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
4. Build `context_packet` with `stage_pass_ref="stage_pass:context-ledger:<append.id>"`.
5. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
6. `set_role_pass_readiness(run_id, role_name="task-planner", ready=true, context_revision=<read.context_revision>, stage_name)`
7. `write_context_packet(run_id, packet=<context_packet>, expected_revision=<read.context_revision>, stage_name)`
8. `record_mcp_quiescence(run_id, stage_name, snapshot)`
9. `validate_tool_sequence(run_id, stage_name)`

Use `mark_stale(run_id, target_ref, reason, context_revision, stage_name)` between steps 5 and 7 for superseded artifacts or assumptions.

## Required Return Values

- `read.context_packet` and `read.context_revision`
- `validate_context_revision.valid=true`
- `append.id` converted to `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `set_role_pass_readiness.ready=true`
- `write.context_revision` as the new current revision
- `validate_tool_sequence.valid=true`

## Output

Emit one MCP-backed `context_packet` with approved facts, constraints, artifact inventory, stale markers, blockers, readiness, `context_delta`, and `next_owner="task-planner"`.

## Hard Rules

- Do not spawn a physical resident context agent.
- Do not plan lanes, route work, review, or judge final output.
- Do not use Docker Memory as the run-local ledger.

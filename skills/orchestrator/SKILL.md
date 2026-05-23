---
name: orchestrator
description: Execute the global Codex Orchestrator stage as a main-agent skill. Use when architecture-required work must be classified, scoped, assigned run identifiers, and converted into a canonical orchestration_request before context-ledger sync.
---

# Orchestrator

Use this skill first for `architecture_required=true` work, and again when `$feedbackgate` returns bounded feedback.

## MCP Tool Sequence

Call `codex-context-ledger` tools in this exact logical order. Pass `stage_name="orchestrator"` on every call that accepts it.

1. `initialize_run(run_id, goal, metadata, stage_name)`
2. `read_context_packet(run_id, stage_name)`
3. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
4. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
5. Build `orchestration_request` with `stage_pass_ref="stage_pass:orchestrator:<append.id>"`.
6. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
7. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
8. `record_mcp_quiescence(run_id, stage_name, snapshot)`
9. `validate_tool_sequence(run_id, stage_name)`

## Required Return Values

Return only after these API results are present:

- `read.context_revision` as `consumed_context_revision`
- `validate_context_revision.valid=true`
- `append.id` as `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `write.context_revision` as the new `context_revision`
- `validate_tool_sequence.valid=true`
- `mcp_quiescence_snapshot.open_mcp_process_count=0`

## Output

Emit one `orchestration_request` with scope, exclusions, success criteria, risk flags, feedback carryover, `context_delta`, artifact/evidence refs, and `next_owner="context-ledger"`.

## Hard Rules

- Do not spawn control-stage agents.
- Do not emit plan, worker result, review result, or final judgment.
- Do not proceed if MCP API validation fails.

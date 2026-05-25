---
name: orchestrator
description: Execute the Codex Orchestrator stage as a main-agent skill. Use when the user explicitly asks to start the architecture/orchestration flow or when feedbackgate routes bounded feedback back to orchestrator.
---

# Orchestrator

Use this skill to enter the architecture flow. This skill sets `architecture_required=true` for the run; do not rely on a global non-trivial-task classifier to force the architecture before `$orchestrator` is used. Use it again when `$feedbackgate` returns bounded feedback.

## Reference Scope

Read only this skill, adjacent `contract.json`, and the `source_docs` listed there. Do not load the full architecture index unless changing the architecture contract itself.

## MCP Tool Sequence

Call `codex-context-ledger` tools in this exact logical order. Pass `stage_name="orchestrator"` on every call that accepts it.

1. `initialize_run(run_id, goal, metadata, stage_name)`
2. `read_context_packet(run_id, stage_name)`
3. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
4. Call `MCP_DOCKER.sequentialthinking` to structure scope, risks, success criteria, feedback carryover, and next-stage handoff.
5. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
6. Build `orchestration_request` with `stage_pass_ref="stage_pass:orchestrator:<append.id>"` and `sequential_thinking_ref` or `sequential_thinking_waiver`.
7. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
8. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
9. `record_mcp_quiescence(run_id, stage_name, snapshot)`
10. `validate_tool_sequence(run_id, stage_name)`

## Required Return Values

Return only after these API results are present:

- `read.context_revision` as `consumed_context_revision`
- `validate_context_revision.valid=true`
- `sequential_thinking_ref` or `sequential_thinking_waiver` proving `MCP_DOCKER.sequentialthinking` was attempted before finalizing `orchestration_request`
- `append.id` as `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `write.context_revision` as the new `context_revision`
- `validate_tool_sequence.valid=true`
- `mcp_quiescence_snapshot.open_mcp_process_count=0`

## Output

Emit one `orchestration_request` with scope, exclusions, success criteria, risk flags, feedback carryover, any `task_design_reentry_decision`, `sequential_thinking_ref` or `sequential_thinking_waiver`, `context_delta`, artifact/evidence refs, and `next_owner="context-ledger"`.

## Hard Rules

- Do not spawn control-stage agents.
- Do not emit task design, execution plan, worker result, review result, or final judgment.
- Attempt `MCP_DOCKER.sequentialthinking` before finalization. If it fails, record `sequential_thinking_waiver` with `status`, `reason`, and `fallback_summary`, then continue with fallback reasoning.
- Do not proceed if MCP API validation fails.

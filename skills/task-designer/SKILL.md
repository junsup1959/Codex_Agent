---
name: task-designer
description: Execute the Codex Task Designer stage inside an orchestrator-started architecture run. Use when an MCP-backed context_packet must become a task_design with multiple design options, comparison criteria, selected option, rationale, and distribution boundaries before work is distributed.
---

# Task Designer

Use this skill after `$context-ledger` emits a current `context_packet`.

## Reference Scope

Read only this skill, adjacent `contract.json`, and the `source_docs` listed there. Do not load worker, review, or feedback docs while designing the task.

## MCP Tool Sequence

Call these tools in order with `stage_name="task-designer"` where accepted.

1. `read_context_packet(run_id, stage_name)`
2. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
3. Call `MCP_DOCKER.sequentialthinking` to compare options, assumptions, risks, and distribution boundaries.
4. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
5. Build `task_design` with `stage_pass_ref="stage_pass:task-designer:<append.id>"` and `sequential_thinking_ref` or `sequential_thinking_waiver`.
6. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
7. `validate_task_design(run_id, packet=<stage_packet>, stage_name)`
8. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
9. `record_mcp_quiescence(run_id, stage_name, snapshot)`
10. `validate_tool_sequence(run_id, stage_name)`

## Required Return Values

- `read.context_packet.role_pass_readiness.task-designer=true`
- `validate_context_revision.valid=true`
- `sequential_thinking_ref` or `sequential_thinking_waiver` proving `MCP_DOCKER.sequentialthinking` was attempted before finalizing `task_design`
- `append.id` converted to `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `validate_task_design.valid=true`
- `write.context_revision` as the new current revision
- `validate_tool_sequence.valid=true`

If `validate_task_design` is not callable in the current session, stop before emitting design options. Record the missing tool as blocker evidence through the ledger when possible, and return only a blocked handoff status. Do not provide an informal fallback `task_design`, option comparison, or selected recommendation.

## Output

Emit `task_design.md` and `task_design` with:

- problem definition
- assumptions
- at least three design options
- comparison criteria
- selected option id
- selection rationale
- selected option risks
- distribution boundaries for `$task-distributor`
- `artifact_profile` with `version`, `source_stage="task-designer"`, `reuse_policy`, and `invalidated_by`
- `sequential_thinking_ref` or `sequential_thinking_waiver`
- `context_delta`
- `next_owner="task-distributor"`

## Hard Rules

- Do not emit `task_design`, `task_design.md`, option 1/2/3 comparisons, or a selected option unless `validate_task_design.valid=true` is present from the MCP tool call.
- Do not create worker lanes.
- Do not choose concrete agents.
- Do not allocate fanout or file ownership.
- Treat `${CODEX_HOME}/agents` as optional role guidance only; do not call or require agents from this stage.
- Attempt `MCP_DOCKER.sequentialthinking` before finalization. If it fails, record `sequential_thinking_waiver` with `status`, `reason`, and `fallback_summary`, then continue with fallback reasoning.

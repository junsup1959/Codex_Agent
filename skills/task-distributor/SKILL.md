---
name: task-distributor
description: Execute the Codex Task Distributor stage inside an orchestrator-started architecture run. Use when a selected task_design must become task_distribution_criteria.md plus an execution_plan with bounded lanes, dependencies, fanout, ownership, and handoff evidence before worker execution.
---

# Task Distributor

Use this skill after `$task-designer` emits a valid `task_design`.

## Reference Scope

Read only this skill, adjacent `contract.json`, and the `source_docs` listed there. Do not load review or feedback docs while distributing work.

## MCP Tool Sequence

Call these tools in order with `stage_name="task-distributor"` where accepted.

1. `read_context_packet(run_id, stage_name)`
2. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
3. Call `MCP_DOCKER.sequentialthinking` to derive lane boundaries, dependencies, fanout use, ownership, and MCP limits from the selected design.
4. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
5. Build `task_distribution_criteria.md` and `execution_plan` with `stage_pass_ref="stage_pass:task-distributor:<append.id>"` and `sequential_thinking_ref` or `sequential_thinking_waiver`.
6. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
7. `validate_execution_plan(run_id, packet=<stage_packet>, stage_name)`
8. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
9. `record_mcp_quiescence(run_id, stage_name, snapshot)`
10. `validate_tool_sequence(run_id, stage_name)`

## Required Return Values

- `read.context_packet.role_pass_readiness.task-distributor=true`
- `validate_context_revision.valid=true`
- `sequential_thinking_ref` or `sequential_thinking_waiver` proving `MCP_DOCKER.sequentialthinking` was attempted before finalizing `execution_plan`
- `append.id` converted to `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `validate_execution_plan.valid=true`
- `write.context_revision` as the new current revision
- `validate_tool_sequence.valid=true`

## Output

Emit `task_distribution_criteria.md` and `execution_plan` with:

- selected task design reference
- distribution criteria reference
- distribution principles
- worker lane list
- lane dependencies
- fanout budget use
- file or domain ownership
- specialist category guidance
- MCP usage limits per lane
- expected outputs and handoff evidence
- `artifact_profile` with `version`, `source_stage="task-distributor"`, `reuse_policy`, and `invalidated_by`
- `sequential_thinking_ref` or `sequential_thinking_waiver`
- `context_delta`
- `next_owner="worker"`

## Hard Rules

- Do not redefine the selected task design.
- Do not change the selected option or success criteria.
- Do not spawn workers.
- Treat `${CODEX_HOME}/agents` as optional role guidance for category fit; do not force agent calls from the distributor.
- Attempt `MCP_DOCKER.sequentialthinking` before finalization. If it fails, record `sequential_thinking_waiver` with `status`, `reason`, and `fallback_summary`, then continue with fallback reasoning.

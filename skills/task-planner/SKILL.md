---
name: task-planner
description: Execute the global Codex Task Planner stage as a main-agent skill. Use when a current MCP-backed context_packet must become a bounded execution_plan before worker specialist materialization.
---

# Task Planner

Use this skill after `$context-ledger` emits a current `context_packet`.

## MCP Tool Sequence

Call these tools in order with `stage_name="task-planner"` where accepted.

1. `read_context_packet(run_id, stage_name)`
2. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
3. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
4. Build `execution_plan` with `stage_pass_ref="stage_pass:task-planner:<append.id>"`.
5. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
6. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
7. `record_mcp_quiescence(run_id, stage_name, snapshot)`
8. `validate_tool_sequence(run_id, stage_name)`

## Required Return Values

- `read.context_packet.role_pass_readiness.task-planner=true`
- `validate_context_revision.valid=true`
- `append.id` converted to `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `write.context_revision` as the new current revision
- `validate_tool_sequence.valid=true`

## Output

Emit one bounded `execution_plan` with worker lanes, file scope, merge points, expected artifacts, validation prompts, review hints, fanout budget, `context_delta`, and `next_owner="worker"`.

## Hard Rules

- Do not spawn workers or reviewers.
- Do not select worker roles from memory; `$worker` must enumerate the TOML catalog.
- Do not proceed if ledger revision or API validation fails.

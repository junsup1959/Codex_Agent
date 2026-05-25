---
name: feedbackgate
description: Execute the Codex Feedback Gate stage inside an orchestrator-started architecture run. Use when specialist review results must determine final output or bounded feedback back to orchestrator.
---

# Feedbackgate

Use this skill after `$review` returns reviewer results or explicit waivers. It is the only stage that may allow final output.

## Reference Scope

Read only this skill, adjacent `contract.json`, and the `source_docs` listed there. Do not load planning, worker, or review-distributor docs unless resolving a missing-evidence blocker.

## MCP Tool Sequence

Call these tools in order with `stage_name="feedbackgate"` where accepted.

1. `read_context_packet(run_id, stage_name)`
2. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
3. Judge worker and review evidence, waivers, MCP validation results, blockers, and MCP/tool cleanup.
4. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
5. Build `judgment_envelope` with `stage_pass_ref="stage_pass:feedbackgate:<append.id>"`.
6. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
7. `validate_stage_completion(run_id, stage_name, packet=<stage_packet>)`
8. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
9. `record_mcp_quiescence(run_id, stage_name, snapshot)`
10. `validate_tool_sequence(run_id, stage_name)`

## Required Return Values

- `validate_context_revision.valid=true`
- current review inputs or explicit waivers
- non-empty `feedback_gate_evidence`
- `append.id` converted to `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `validate_stage_completion.valid=true`
- `write.context_revision`
- `validate_tool_sequence.valid=true`
- clean `mcp_quiescence_snapshot`

## Output

Return `judgment_envelope`. If `feedback_required=true`, set `next_owner="orchestrator"`, bounded rework scope, and `task_design_reentry_decision`. If approved, set `next_owner="final"` and allow the user-facing final response.

`task_design_reentry_decision.action` must be one of:

- `revise_task_design`
- `reuse_task_design`
- `skip_to_distribution`

For `reuse_task_design` or `skip_to_distribution`, include `task_design_ref` and `reason`.

Every feedback reentry decision must also include:

- `reusable_artifacts`
- `invalidated_artifacts`
- `distribution_action`: `reuse_execution_plan`, `revise_execution_plan`, or `skip_distribution`
- `review_distribution_action`: `reuse_review_criteria`, `revise_review_plan`, or `skip_review_distribution`

## Hard Rules

- Do not approve with stale context, missing waits, invalid review evidence, missing waivers, or open MCP/tool residue.
- Feedback always returns to `$orchestrator`; it never jumps directly to a mid-loop stage.
- Do not require a full task redesign on every feedback loop; make the reentry decision explicit.
- Do not emit feedback without artifact reuse and invalidation scope.

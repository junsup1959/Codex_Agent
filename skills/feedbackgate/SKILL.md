---
name: feedbackgate
description: Execute the mandatory global Codex Feedback Gate stage. Use when specialist review results must determine final output or bounded feedback back to orchestrator.
---

# Feedbackgate

Use this skill after `$review` returns reviewer results or explicit waivers. It is the only stage that may allow final output.

## MCP Tool Sequence

Call these tools in order with `stage_name="feedbackgate"` where accepted.

1. `read_context_packet(run_id, stage_name)`
2. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
3. Judge worker and review evidence, waivers, MCP validation results, blockers, and MCP/tool cleanup.
4. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
5. Build `judgment_envelope` with `stage_pass_ref="stage_pass:feedbackgate:<append.id>"`.
6. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
7. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
8. `record_mcp_quiescence(run_id, stage_name, snapshot)`
9. `validate_tool_sequence(run_id, stage_name)`

## Required Return Values

- `validate_context_revision.valid=true`
- current review inputs or explicit waivers
- non-empty `feedback_gate_evidence`
- `append.id` converted to `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `write.context_revision`
- `validate_tool_sequence.valid=true`
- clean `mcp_quiescence_snapshot`

## Output

Return `judgment_envelope`. If `feedback_required=true`, set `next_owner="orchestrator"` and bounded rework scope. If approved, set `next_owner="final"` and allow the user-facing final response.

## Hard Rules

- Do not approve with stale context, missing waits, invalid review evidence, missing waivers, or open MCP/tool residue.
- Feedback always returns to `$orchestrator`; it never jumps directly to a mid-loop stage.

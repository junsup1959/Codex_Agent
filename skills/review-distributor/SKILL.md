---
name: review-distributor
description: Execute the mandatory global Codex Review Distributor stage. Use when completed specialist worker evidence must be routed into bounded spawned specialist review lanes before feedbackgate judgment.
---

# Review Distributor

Use this skill after `$worker` returns or classifies all worker lanes. It creates the review plan; `$review` owns reviewer spawning.

## MCP Tool Sequence

Call these tools in order with `stage_name="review-distributor"` where accepted.

1. `read_context_packet(run_id, stage_name)`
2. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
3. Confirm all worker lanes are returned or explicitly classified.
4. Enumerate review-capable TOML specialists and build a bounded `review_plan`.
5. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
6. Add `stage_pass_ref="stage_pass:review-distributor:<append.id>"`.
7. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
8. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
9. `record_mcp_quiescence(run_id, stage_name, snapshot)`
10. `validate_tool_sequence(run_id, stage_name)`

## Required Return Values

- `validate_context_revision.valid=true`
- complete specialist catalog enumeration evidence
- `append.id` converted to `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `write.context_revision`
- `validate_tool_sequence.valid=true`

## Output

Emit `review_plan`, explicit `review_waivers` if any, review coverage evidence, `context_delta`, and `next_owner="review"`.

## Hard Rules

- Do not call `spawn_agent`.
- Do not judge final readiness.
- Do not route from memory, family aliases, skill names, or partial specialist lists.

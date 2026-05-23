---
name: review
description: Execute the mandatory global Codex Review materialization stage. Use when a review distribution plan must become spawned specialist reviewer agents, waited review results, and classified review evidence.
---

# Review

Use this skill after `$review-distributor`. The main agent spawns concrete reviewer specialists and waits for every reviewer.

## MCP Tool Sequence

Call these tools in order with `stage_name="review"` where accepted.

1. `read_context_packet(run_id, stage_name)`
2. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
3. Spawn TOML-backed reviewer specialists from the `review_plan`, then call `wait_agent` for each one.
4. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
5. Build `review_handoff_results` with `stage_pass_ref="stage_pass:review:<append.id>"`.
6. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
7. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
8. `record_mcp_quiescence(run_id, stage_name, snapshot)`
9. `validate_tool_sequence(run_id, stage_name)`

Use `record_artifact_ref` for review artifacts and `mark_stale` for superseded review assumptions before step 7.

## Required Return Values

- `validate_context_revision.valid=true`
- reviewer `spawn_receipt_ref`, `agent_id` or `submission_id`, and `wait_agent` evidence
- `append.id` converted to `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `write.context_revision`
- `validate_tool_sequence.valid=true`

## Output

Return `review_handoff_results`, `review_waivers`, coverage evidence, artifact/evidence refs, `context_delta`, and `next_owner="feedbackgate"`.

## Hard Rules

- Do not approve final output.
- Do not continue with unwaited review children unless explicitly classified.
- Do not use canonical stage owners as reviewer specialists.

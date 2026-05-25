---
name: review
description: Execute the Codex Review materialization stage inside an orchestrator-started architecture run. Use when a review distribution plan must become forced specialist reviewer agent calls, waited review results, and classified review evidence.
---

# Review

Use this skill after `$review-distributor`. The main agent must spawn concrete reviewer specialists for every non-waived review lane and wait for every reviewer.

## Reference Scope

Read only this skill, adjacent `contract.json`, and the `source_docs` listed there. Do not load worker or feedbackgate docs while materializing reviews.

## MCP Tool Sequence

Call these tools in order with `stage_name="review"` where accepted.

1. `read_context_packet(run_id, stage_name)`
2. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
3. Read `review_plan` plus `review_distribution_criteria_ref`; spawn TOML-backed reviewer specialists from non-waived review lanes, then call `wait_agent` for each one.
4. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
5. Build `review_handoff_results` with `stage_pass_ref="stage_pass:review:<append.id>"`.
6. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
7. `validate_stage_completion(run_id, stage_name, packet=<stage_packet>)`
8. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
9. `record_mcp_quiescence(run_id, stage_name, snapshot)`
10. `validate_tool_sequence(run_id, stage_name)`

Use `record_artifact_ref` for review artifacts and `mark_stale` for superseded review assumptions before step 8.

## Required Return Values

- `validate_context_revision.valid=true`
- reviewer `spawn_receipt_ref`, `agent_id` or `submission_id`, `wait_handle`, and `wait_agent` evidence
- `append.id` converted to `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `validate_stage_completion.valid=true`
- `write.context_revision`
- `validate_tool_sequence.valid=true`

## Output

Return `review_handoff_results`, `review_waivers`, coverage evidence, artifact/evidence refs, `context_delta`, and `next_owner="feedbackgate"`.

## Hard Rules

- Do not approve final output.
- Do not treat review agents as optional guidance for non-waived review lanes.
- Do not continue with unwaited review children unless explicitly classified.
- Do not use canonical stage owners as reviewer specialists.

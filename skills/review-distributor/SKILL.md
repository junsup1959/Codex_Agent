---
name: review-distributor
description: Execute the Codex Review Distributor stage inside an orchestrator-started architecture run. Use when completed specialist worker evidence must be routed into bounded spawned specialist review lanes before feedbackgate judgment.
---

# Review Distributor

Use this skill after `$worker` returns or classifies all worker lanes. It creates `review_distribution_criteria.md` and the review plan; `$review` owns reviewer spawning.

## Reference Scope

Read only this skill, adjacent `contract.json`, and the `source_docs` listed there. Do not load worker materialization or feedbackgate docs unless resolving an evidence handoff blocker.

## MCP Tool Sequence

Call these tools in order with `stage_name="review-distributor"` where accepted.

1. `read_context_packet(run_id, stage_name)`
2. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
3. Confirm all worker lanes are returned or explicitly classified.
4. Call `MCP_DOCKER.sequentialthinking` to derive review axes, reviewer lane boundaries, waivers, coverage, fanout, and handoff evidence rules.
5. Build `review_distribution_criteria.md` with reviewer lane, coverage, fanout, waiver, and handoff evidence criteria.
6. Use review-capable TOML specialists as category guidance and build a bounded `review_plan`.
7. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
8. Add `stage_pass_ref="stage_pass:review-distributor:<append.id>"` and `sequential_thinking_ref` or `sequential_thinking_waiver`.
9. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
10. `validate_review_plan(run_id, packet=<stage_packet>, stage_name)`
11. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
12. `record_mcp_quiescence(run_id, stage_name, snapshot)`
13. `validate_tool_sequence(run_id, stage_name)`

## Required Return Values

- `validate_context_revision.valid=true`
- complete specialist catalog enumeration evidence
- `sequential_thinking_ref` or `sequential_thinking_waiver` proving `MCP_DOCKER.sequentialthinking` was attempted before finalizing `review_plan`
- `append.id` converted to `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `validate_review_plan.valid=true`
- `write.context_revision`
- `validate_tool_sequence.valid=true`

## Output

Emit `review_distribution_criteria.md`, `review_plan`, explicit `review_waivers` if any, review coverage evidence, `artifact_profile` with `source_stage="review-distributor"`, `sequential_thinking_ref` or `sequential_thinking_waiver`, `context_delta`, and `next_owner="review"`.

## Hard Rules

- Do not call `spawn_agent`.
- Do not judge final readiness.
- Do not route from memory, family aliases, skill names, or partial specialist lists.
- Attempt `MCP_DOCKER.sequentialthinking` before finalization. If it fails, record `sequential_thinking_waiver` with `status`, `reason`, and `fallback_summary`, then continue with fallback reasoning.

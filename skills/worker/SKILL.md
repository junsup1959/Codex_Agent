---
name: worker
description: Execute the Codex Worker materialization stage inside an orchestrator-started architecture run. Use when a task-distributor execution_plan must become forced specialist worker agent calls, waited results, and classified worker handoff evidence.
---

# Worker

Use this skill after `$task-distributor`. The main agent must spawn concrete specialist workers for worker lanes and wait for their results.

## Reference Scope

Read only this skill, adjacent `contract.json`, and the `source_docs` listed there. Do not load review or feedback docs while materializing workers.

## MCP Tool Sequence

Call these ledger tools in order with `stage_name="worker"` where accepted.

1. `read_context_packet(run_id, stage_name)`
2. `validate_context_revision(run_id, context_revision=<read.context_revision>, stage_name)`
3. Read `execution_plan` plus `task_distribution_criteria_ref`; enumerate `${CODEX_HOME}/agents/<category>/*.toml`, select bounded worker specialists, then call `spawn_agent`/`wait_agent` outside the ledger API.
4. `append_stage_pass(run_id, stage_name, stage_execution_mode="main_agent_role_pass", evidence, context_revision=<read.context_revision>)`
5. Build `worker_handoff_results` with `stage_pass_ref="stage_pass:worker:<append.id>"`.
6. `validate_stage_packet(run_id, stage_name, packet=<stage_packet>)`
7. `validate_stage_completion(run_id, stage_name, packet=<stage_packet>)`
8. `write_context_packet(run_id, packet=<context_delta_applied_packet>, expected_revision=<read.context_revision>, stage_name)`
9. `record_mcp_quiescence(run_id, stage_name, snapshot)`
10. `validate_tool_sequence(run_id, stage_name)`

Use `record_artifact_ref` for returned artifacts and `mark_stale` for superseded inputs before step 8.

## Required Return Values

- `validate_context_revision.valid=true`
- `spawn_receipt_ref`, `agent_id` or `submission_id`, `wait_handle`, and `wait_agent` evidence for every spawned child
- `append.id` converted to `stage_pass_ref`
- `validate_stage_packet.valid=true`
- `validate_stage_completion.valid=true`
- `write.context_revision`
- `validate_tool_sequence.valid=true`

## Output

Return `worker_handoff_results`, `active_passes`, missing-lane classifications, artifact/evidence refs, `context_delta`, and `next_owner="review-distributor"`.

## Hard Rules

- Do not treat worker agents as optional guidance; worker lanes require concrete specialist worker calls unless explicitly classified as impossible.
- Do not spawn generic `worker` roles.
- Do not continue with unwaited children.
- `close_agent` is cleanup only, not result evidence.

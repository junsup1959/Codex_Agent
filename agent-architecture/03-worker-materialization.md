# Worker Materialization

`$worker` owns specialist worker materialization.

## Inputs

- current `execution_plan`
- `task_distribution_criteria_ref`
- validated `context_packet`
- `fanout_budget`
- complete specialist catalog under `${CODEX_HOME}/agents/<category>/*.toml`

## Flow

1. Read and validate the latest ledger revision.
2. Enumerate the full TOML specialist catalog.
3. Select the minimum concrete worker specialists that cover the plan.
4. Build scoped spawn packets for each lane.
5. Enforce fanout budget; coalesce or classify overflow.
6. Call `spawn_agent`.
7. Record `spawn_receipt_ref`, `agent_id` or `submission_id`, and `wait_handle`.
8. Call `wait_agent` for every spawned specialist.
9. Classify each lane as returned, timed_out, failed, superseded, schema_invalid, no_wait_handle, or thread_limit_reached.
10. Write worker evidence and context delta through `$context-ledger`.

## Output

`$worker` returns `worker_handoff_results`, `active_passes`, missing-lane classifications, context refs, and `stage_pass_ref`.

## Hard Rules

- Do not spawn a generic worker role.
- Do not spawn from memory, family aliases, or skill names.
- Do not continue with unwaited children.
- `close_agent` is cleanup only.

## Required API Checks

Before handoff, `$worker` must call `validate_stage_packet`, `validate_stage_completion`, and then `validate_tool_sequence` through `codex-context-ledger`. All must return `valid=true`.

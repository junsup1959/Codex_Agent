# Runtime Orchestration Steps

This is the mandatory sequence for `architecture_required=true` work.

## Canonical Flow

`orchestrator -> context-ledger -> task-planner -> worker -> review-distributor -> review -> feedbackgate`

## Startup Gate

1. Classify the request. Simple direct answers may bypass the loop.
2. For non-trivial work, set `architecture_required=true`.
3. Use available MCP or record `mcp_usage_blocked=true`.
4. Activate `$orchestrator`; create `run_id`, `loop_id`, scope, success criteria, and `orchestration_request`.
5. Activate `$context-ledger`; initialize/read/update `codex-context-ledger` and emit `context_packet`.

## Context Ledger Barrier

`context_ledger_barrier_required=true`.

Every mandatory stage must:

1. Call `$context-ledger` to `read_context_packet`.
2. Call `validate_context_revision` for `consumed_context_revision`.
3. Check `role_pass_readiness.<stage>=true`.
4. Refuse stale blockers instead of acting from chat memory.
5. Call `append_stage_pass` and use its `id` to set `stage_pass_ref`.
6. Emit `context_packet_version`, `context_delta`, `new_artifact_refs`, and `new_evidence_refs`.
7. Call `validate_stage_packet`; it must return `valid=true`.
8. Call `write_context_packet` with `expected_revision=consumed_context_revision`.
9. Call `record_mcp_quiescence`.
10. Call `validate_tool_sequence`; it must return `valid=true`.
11. Call `mark_stale` for superseded artifacts or assumptions when needed.

## Control Loop

1. `$orchestrator` emits `orchestration_request` with `next_owner="context-ledger"`.
2. `$context-ledger` is mandatory. It owns run-local approved facts, constraints, artifact inventory, stale markers, context revision, and role-pass readiness. It emits `context_packet` with `next_owner="task-planner"`.
3. `$task-planner` emits an `execution_plan` with bounded worker lanes, validation prompts, review hints, and `fanout_budget`. It does not spawn.
4. `$worker` enumerates `${CODEX_HOME}/agents/<category>/*.toml`, selects concrete specialist workers, calls `spawn_agent`, records `active_passes`, calls `wait_agent`, and returns worker `handoff_result` evidence plus missing-lane classifications.
5. `$review-distributor` reads worker evidence, determines required review axes, enumerates review-capable specialists, and emits a bounded `review_plan`.
6. `$review` materializes specialist reviews with `spawn_agent`, records wait handles, calls `wait_agent`, and returns review `handoff_result` values, waivers, and coverage.
7. `$feedbackgate` judges worker/review evidence, MCP validation results, MCP/tool cleanup, and risk. It either allows final output or returns bounded feedback to `$orchestrator`.

## Physical Specialist Rules

- Specialist workers and specialist reviews are physical spawned agents.
- Every spawned child must be waited before it can feed review or feedbackgate.
- `close_agent` is cleanup only, not result evidence.
- Fanout defaults: max 2 worker lanes, max 2 review lanes, max 4 total child agents, max 1 same-role parallel lane, max 1 MCP-using child lane active.

## Feedback

- `feedback_gate_mandatory=true`.
- Final output is forbidden while `feedback_required=true`.
- Feedback always returns to `$orchestrator`; the next loop then runs `$context-ledger`.
- Repeated no-progress feedback must become user/tool/schema/doc repair, not prompt-only retries.

## Optional Memory

`$docker-memory` may help with durable cross-run observations. It is optional and does not replace `codex-context-ledger`, MCP validation evidence, specialist review evidence, or `$feedbackgate`.

## MCP Runtime Validation

No repository-side script validates the runtime. The mandatory proof is the ordered MCP tool return sequence for each stage.

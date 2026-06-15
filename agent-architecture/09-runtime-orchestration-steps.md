# Runtime Orchestration Steps

This is the mandatory sequence after `$orchestrator` has been explicitly activated and has emitted `architecture_required=true` for the run. If `$orchestrator` classifies the task as express-direct and emits `architecture_required=false`, follow the compact direct path instead.

## Canonical Flow

Full architecture flow:

`orchestrator -> context-ledger -> task-designer -> task-distributor -> worker -> review-distributor -> review -> feedbackgate`

Compact direct flow:

`orchestrator -> direct-workflow`

## Startup Gate

1. Stay in the normal direct workflow unless the user explicitly invokes `$orchestrator`, asks to run the architecture/orchestration flow, or a current `$feedbackgate` result routes bounded feedback back to `$orchestrator`.
2. Activate `$orchestrator`; call `MCP_DOCKER.sequentialthinking`; create `run_id`, `loop_id`, scope, success criteria, `sequential_thinking_ref` or `sequential_thinking_waiver`, and `orchestration_request`.
3. `$orchestrator` sets `architecture_required=true` for a full run or `architecture_required=false` with `workflow_mode="express-direct"` for a compact direct handoff.
4. Use available MCP or record `mcp_usage_blocked=true`.
5. If `architecture_required=true`, activate `$context-ledger`; initialize/read/update `codex-context-ledger` and emit `context_packet`.
6. If `architecture_required=false`, validate the orchestrator stage packet and return to normal direct workflow; do not activate downstream architecture stages.

## Compact Direct Path

This path mirrors Maestro's Express workflow for simple tasks. It is allowed only when all of these are true:

1. The work is simple, low-risk, and single-lane.
2. The work does not require specialist fanout, task-design alternatives, formal review distribution, feedbackgate judgment, or feedback-loop artifact reuse.
3. `$orchestrator` attempted `MCP_DOCKER.sequentialthinking` or recorded `sequential_thinking_waiver`.
4. `$orchestrator` emits `orchestration_request` with `architecture_required=false`, `workflow_mode="express-direct"`, `complexity_classification` in `simple`, `direct`, or `low-risk`, `direct_workflow_scope.allowed_actions`, `direct_workflow_scope.excluded_actions`, `direct_workflow_scope.cleanup_actions`, `express_direct_reason`, and `next_owner="direct-workflow"`.
5. `validate_stage_packet.valid=true`, `validate_tool_sequence.valid=true`, and MCP quiescence evidence are present.

After this handoff, resume the normal direct workflow: implement, test, commit, PR, or answer as the user requested. Complete or explicitly defer the declared `cleanup_actions`; for PR work this should distinguish local branch/worktree cleanup from any remote head branch that must remain until merge. Do not claim architecture completion, reviewer coverage, or feedbackgate approval from an express-direct handoff.

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

1. For full architecture runs, `$orchestrator` emits `orchestration_request` with `architecture_required=true` and `next_owner="context-ledger"`.
2. `$context-ledger` is mandatory. It owns run-local approved facts, constraints, artifact inventory, stale markers, context revision, and role-pass readiness. It normally emits `context_packet` with `next_owner="task-designer"`.
3. `$task-designer` calls `MCP_DOCKER.sequentialthinking`, then emits `task_design.md` and `task_design` with multiple options, comparison criteria, selected option, rationale, distribution boundaries, `artifact_profile`, and `sequential_thinking_ref` or `sequential_thinking_waiver`. It does not create lanes or call agents.
4. `$task-distributor` calls `MCP_DOCKER.sequentialthinking`, then emits `task_distribution_criteria.md` and an `execution_plan` with bounded worker lanes, dependencies, ownership, validation prompts, review hints, `fanout_budget`, `artifact_profile`, and `sequential_thinking_ref` or `sequential_thinking_waiver`. It does not spawn.
5. `$worker` enumerates `${CODEX_HOME}/agents/<category>/*.toml`, selects concrete specialist workers, calls `spawn_agent`, records `active_passes`, calls `wait_agent`, and returns worker `handoff_result` evidence plus missing-lane classifications.
6. `$review-distributor` reads worker evidence, calls `MCP_DOCKER.sequentialthinking`, determines required review axes, emits `review_distribution_criteria.md`, and creates a bounded `review_plan` with `artifact_profile` and `sequential_thinking_ref` or `sequential_thinking_waiver` for specialist reviewers.
7. `$review` materializes specialist reviews with `spawn_agent`, records wait handles, calls `wait_agent`, and returns review `handoff_result` values, waivers, and coverage.
8. `$feedbackgate` judges worker/review evidence, MCP validation results, MCP/tool cleanup, and risk. It either allows final output or returns bounded feedback to `$orchestrator` with `task_design_reentry_decision`.

## Physical Specialist Rules

- Specialist workers and specialist reviewers are physical spawned agents.
- Every spawned child must be waited before it can feed review or feedbackgate.
- `close_agent` is cleanup only, not result evidence.
- Fanout defaults: max 2 worker lanes, max 2 review lanes, max 4 total child agents, max 1 same-role parallel lane, max 1 MCP-using child lane active.

## Feedback

- `feedback_gate_mandatory=true` for full architecture runs with `architecture_required=true`.
- Express-direct handoffs do not enter `$feedbackgate`; they return to direct workflow and cannot be used as final architecture approval evidence.
- Final output is forbidden while `feedback_required=true`.
- Feedback always returns to `$orchestrator`; the next loop then runs `$context-ledger`.
- On feedback loops, `$feedbackgate` must declare whether to `revise_task_design`, `reuse_task_design`, or `skip_to_distribution`, plus reusable/invalidated artifacts and downstream distribution actions. `$context-ledger` preserves this as `reentry_cache` and may hand off directly to `$task-distributor` only when that reentry decision is valid.
- Repeated no-progress feedback must become user/tool/schema/doc repair, not prompt-only retries.

## Optional Memory

`$docker-memory` may help with durable cross-run observations. It is optional and does not replace `codex-context-ledger`, MCP validation evidence, specialist review evidence, or `$feedbackgate`.

## MCP Runtime Validation

No repository-side script validates the runtime. The mandatory proof is the ordered MCP tool return sequence for each stage.

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

## Control Loop

1. `$orchestrator` emits `orchestration_request` with `next_owner="context-ledger"`.
2. `$context-ledger` is mandatory. It owns run-local approved facts, constraints, artifact inventory, stale markers, context revision, and role-pass readiness. It emits `context_packet` with `next_owner="task-planner"`.
3. `$task-planner` emits an `execution_plan` with bounded worker lanes, validation prompts, review hints, and `fanout_budget`. It does not spawn.
4. `$worker` enumerates `${CODEX_HOME}/agents/<category>/*.toml`, selects concrete specialist workers, calls `spawn_agent`, records `active_passes`, calls `wait_agent`, and returns worker `handoff_result` evidence plus missing-lane classifications.
5. `$review-distributor` reads worker evidence, determines required review axes, enumerates review-capable specialists, and emits a bounded `review_plan`.
6. `$review` materializes specialist reviews with `spawn_agent`, records wait handles, calls `wait_agent`, and returns review `handoff_result` values, waivers, and coverage.
7. `$feedbackgate` judges worker/review evidence, validators, MCP/tool cleanup, and risk. It either allows final output or returns bounded feedback to `$orchestrator`.

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

`$docker-memory` may help with durable cross-run observations. It is optional and does not replace `codex-context-ledger`, validators, specialist review evidence, or `$feedbackgate`.

## Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, stage skills, or detects architecture drift, emit `architecture_validation_required=true`. Run:

```powershell
python "$env:CODEX_HOME/agent-architecture/validate-skill-contracts.py"
python "$env:CODEX_HOME/agent-architecture/validate-agent-architecture.py"
```

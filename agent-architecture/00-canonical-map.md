# Canonical Map

This file is the top-level map for Codex architecture runs after `$orchestrator` is explicitly activated.

## Flow

`orchestrator -> context-ledger -> task-designer -> task-distributor -> worker -> review-distributor -> review -> feedbackgate`

The shorter mental model is `design -> distribute -> specialist workers -> reviews -> feedback`, but orchestrator-started runtime must include `$context-ledger`.

## Stage Types

| Stage | Type | Output |
| --- | --- | --- |
| `$orchestrator` | main-agent skill | `orchestration_request` |
| `$context-ledger` | main-agent skill backed by MCP | `context_packet` |
| `$task-designer` | main-agent skill | `task_design` and `task_design.md` |
| `$task-distributor` | main-agent skill | `task_distribution_criteria.md` and `execution_plan` |
| `$worker` | main-agent skill spawning required worker specialists | `worker_handoff_results` |
| `$review-distributor` | main-agent skill | `review_distribution_criteria.md` and `review_plan` |
| `$review` | main-agent skill spawning required reviewer specialists | `review_handoff_results` |
| `$feedbackgate` | main-agent skill | `judgment_envelope` |

## Hard Boundaries

- Control stages are not physical subagents.
- `${CODEX_HOME}/agents/<category>/*.toml` guides non-worker control stages, but they do not force agent calls.
- `$worker` must use physical `spawn_agent` for worker lanes in the validated execution plan.
- `$review` must use physical `spawn_agent` for non-waived review lanes in the validated review plan.
- Every spawned specialist must be followed by `wait_agent` before its evidence can be consumed.
- `$context-ledger` owns run facts, constraints, artifact inventory, stale markers, context revision, and readiness only.
- `$docker-memory` is optional cross-run memory and cannot replace the ledger.

## Ledger Barrier

`context_ledger_barrier_required=true`: each mandatory stage reads and validates the latest context revision before acting, then writes a delta and `stage_pass_ref` before handoff.

## MCP Runtime Validation

Runtime validation is not a repository-side script. Each mandatory stage must call `validate_context_revision`, `validate_stage_packet`, and `validate_tool_sequence` through `codex-context-ledger` before handoff. Stage-specific validators are mandatory where documented: `validate_task_design`, `validate_execution_plan`, `validate_review_plan`, and `validate_stage_completion`.

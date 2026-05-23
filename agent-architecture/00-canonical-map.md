# Canonical Map

This file is the top-level map for architecture-required Codex runs.

## Flow

`orchestrator -> context-ledger -> task-planner -> worker -> review-distributor -> review -> feedbackgate`

The shorter mental model is `plan -> specialist workers -> specialist reviews -> feedback`, but the runtime must include `$context-ledger`.

## Stage Types

| Stage | Type | Output |
| --- | --- | --- |
| `$orchestrator` | main-agent skill | `orchestration_request` |
| `$context-ledger` | main-agent skill backed by MCP | `context_packet` |
| `$task-planner` | main-agent skill | `execution_plan` |
| `$worker` | main-agent skill spawning specialists | `worker_handoff_results` |
| `$review-distributor` | main-agent skill | `review_plan` |
| `$review` | main-agent skill spawning specialists | `review_handoff_results` |
| `$feedbackgate` | main-agent skill | `judgment_envelope` |

## Hard Boundaries

- Control stages are not physical subagents.
- Only specialist workers and specialist reviews use physical `spawn_agent`.
- Every spawned specialist must be followed by `wait_agent` before its evidence can be consumed.
- `$context-ledger` owns run facts, constraints, artifact inventory, stale markers, context revision, and readiness only.
- `$docker-memory` is optional cross-run memory and cannot replace the ledger.

## Ledger Barrier

`context_ledger_barrier_required=true`: each mandatory stage reads and validates the latest context revision before acting, then writes a delta and `stage_pass_ref` before handoff.

## MCP Runtime Validation

Runtime validation is not a repository-side script. Each mandatory stage must call `validate_context_revision`, `validate_stage_packet`, and `validate_tool_sequence` through `codex-context-ledger` before handoff.

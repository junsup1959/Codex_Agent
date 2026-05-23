# Global Codex Architecture Pointer

This file is the compact global guardrail. Detailed contracts live under `${CODEX_HOME}/agent-architecture/`.

## Read First

- Architecture source: `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md`
- Architecture mapper: `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE-MAPPER.md`
- Runtime sequence: `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Canonical Flow

`orchestrator -> context-ledger -> task-planner -> worker -> review-distributor -> review -> feedbackgate`

User-facing shorthand may omit the ledger as `orchestrator -> task-planner -> specialist workers -> review-distributor -> specialist reviews -> feedbackgate`, but runtime execution must include the mandatory `$context-ledger` stage.

## Application Rule

- Simple direct-answer tasks may proceed directly.
- Non-trivial audit, implementation, research, comparison, risky, multi-agent, or multi-artifact work sets `architecture_required=true`.
- For architecture-required work, follow `09-runtime-orchestration-steps.md`; do not skip or reorder stages unless `$feedbackgate` blocks the loop.
- `orchestration_stage_skills_required=true`: force `$orchestrator`, `$context-ledger`, `$task-planner`, `$worker`, `$review-distributor`, `$review`, and `$feedbackgate` in that order.
- `context_ledger_mcp_required=true`: `$context-ledger` must use `codex-context-ledger` as the run/session source of truth. Do not spawn a physical context-manager.
- `$worker` and `$review` are main-agent skills that materialize physical specialist agents with `spawn_agent`, wait with `wait_agent`, and classify every lane before handoff.
- Physical parallelism is reserved for specialist workers and specialist reviews selected from `${CODEX_HOME}/agents/<category>/*.toml`.
- Every spawned child must have `spawn_receipt_ref`, `agent_id` or `submission_id`, `wait_handle`, and later `wait_agent` evidence. `close_agent` is cleanup only.
- `agent_fanout_budget_required=true`: default max 2 worker lanes, 2 review lanes, 4 total child agents per loop, 1 same-role parallel lane, and 1 MCP-using child lane at a time.

## Feedback Gate

- `feedback_gate_mandatory=true` for every architecture-required run.
- `$feedbackgate` judges review evidence and either allows final output or returns bounded feedback to `$orchestrator`.
- Final, ready, approve, merge-ready, or completion claims are forbidden without current `feedback_gate_evidence`, reviewer results or waivers, validator evidence, and clean MCP/tool quiescence.
- If review judgment requires feedback, the next stage is always `$orchestrator`; do not jump directly into a worker or review lane.

## MCP Usage

- `mcp_required=true` for architecture-required work.
- MCP calls that fail, return errors, or are unavailable are blocker/waiver evidence, not success evidence.
- `$docker-memory` is optional long-term memory guidance only. It does not replace `$context-ledger`, validators, specialist review evidence, or `$feedbackgate`.

## Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, stage skills, or detects architecture drift, emit `architecture_validation_required=true` and run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.

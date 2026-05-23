# Global Codex Architecture Pointer

This repo inherits the global architecture by reference.

## Read First

- `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md`
- `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE-MAPPER.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Mandatory Flow

`orchestrator -> context-ledger -> task-planner -> worker -> review-distributor -> review -> feedbackgate`

For architecture-required work, activate these skills in order:

`$orchestrator`, `$context-ledger`, `$task-planner`, `$worker`, `$review-distributor`, `$review`, `$feedbackgate`.

`$worker` and `$review` own `spawn_agent` and `wait_agent` for specialist workers and specialist reviews. `$context-ledger` is mandatory and uses `codex-context-ledger`; do not spawn a physical context-manager.

## Guardrails

- Simple direct-answer tasks may proceed directly.
- Non-trivial audit, implementation, research, comparison, risky, multi-agent, or multi-artifact work sets `architecture_required=true`.
- `context_ledger_mcp_required=true`
- `feedback_gate_mandatory=true`
- `agent_fanout_budget_required=true`
- `$docker-memory` is optional and never replaces `$context-ledger` or `$feedbackgate`.

## Validation Hook

If architecture docs, runtime prompts, validators, or stage skills change, emit `architecture_validation_required=true` and run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py`.

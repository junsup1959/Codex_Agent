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

`$worker` and `$review` own `spawn_agent` and `wait_agent` for specialist workers and specialist reviews. `$context-ledger` is mandatory and uses `codex-context-ledger`; do not spawn a physical resident context agent.

## Guardrails

- Simple direct-answer tasks may proceed directly.
- Non-trivial audit, implementation, research, comparison, risky, multi-agent, or multi-artifact work sets `architecture_required=true`.
- `context_ledger_mcp_required=true`
- `context_ledger_barrier_required=true`
- `mcp_tool_sequence_validation_required=true`
- `feedback_gate_mandatory=true`
- `agent_fanout_budget_required=true`
- `$docker-memory` is optional and never replaces `$context-ledger` or `$feedbackgate`.
- Every mandatory skill consumes `consumed_context_revision` and returns `context_delta`, `new_artifact_refs`, `new_evidence_refs`, and `stage_pass_ref` before the next stage starts.
- Every mandatory skill must call `validate_stage_packet` and `validate_tool_sequence` through localhost `codex-context-ledger` and preserve their return values.

## MCP Runtime Validation

Do not add repository-side validation scripts. Runtime validation must come from the mandatory `codex-context-ledger` MCP calls and their preserved return values.

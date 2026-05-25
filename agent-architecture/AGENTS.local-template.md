# Orchestrator-Scoped Codex Architecture Pointer

This repo inherits the orchestrator-scoped architecture by reference.

## Reference Scope

- During normal direct work, do not load the full architecture docs.
- When a stage skill is active, read only that skill's `SKILL.md`, adjacent `contract.json`, and the `source_docs` listed in that contract.
- Use the full architecture index, mapper, or runtime sequence only when changing the architecture itself or resolving a stage-order blocker.

## Orchestrator-Started Flow

`orchestrator -> context-ledger -> task-designer -> task-distributor -> worker -> review-distributor -> review -> feedbackgate`

After `$orchestrator` is explicitly used and emits `architecture_required=true`, activate these skills in order:

`$orchestrator`, `$context-ledger`, `$task-designer`, `$task-distributor`, `$worker`, `$review-distributor`, `$review`, `$feedbackgate`.

`$task-designer` owns option-based design selection. `$task-distributor` owns distribution criteria and execution planning. `$worker` and `$review` own `spawn_agent` and `wait_agent` for specialist workers and specialist reviews. Non-worker control stages may use `${CODEX_HOME}/agents` as guidance but do not force agent calls. `$context-ledger` is mandatory and uses `codex-context-ledger`; do not spawn a physical resident context agent.

## Guardrails

- Direct-answer, implementation, research, audit, comparison, risky, multi-agent, or multi-artifact work may proceed through the normal direct workflow unless the user explicitly invokes `$orchestrator`, asks to run the architecture/orchestration flow, or a current `$feedbackgate` result routes bounded feedback back to `$orchestrator`.
- `$orchestrator` activation is the entry point that sets `architecture_required=true` for that run. Do not set it from a global/non-trivial-task classifier alone.
- `context_ledger_mcp_required=true`
- `context_ledger_barrier_required=true`
- `mcp_tool_sequence_validation_required=true`
- `sequential_thinking_required=true` for `$orchestrator`, `$task-designer`, `$task-distributor`, and `$review-distributor`; each must attempt `MCP_DOCKER.sequentialthinking` and emit `sequential_thinking_ref` or `sequential_thinking_waiver`.
- `feedback_gate_mandatory=true`
- `agent_fanout_budget_required=true`
- `$docker-memory` is optional and never replaces `$context-ledger` or `$feedbackgate`.
- Every mandatory skill consumes `consumed_context_revision` and returns `context_delta`, `new_artifact_refs`, `new_evidence_refs`, and `stage_pass_ref` before the next stage starts.
- Every mandatory skill must call `validate_stage_packet` and `validate_tool_sequence` through localhost `codex-context-ledger` and preserve their return values. `$task-designer` also calls `validate_task_design`, `$task-distributor` calls `validate_execution_plan`, `$review-distributor` calls `validate_review_plan`, and completion-bearing stages call `validate_stage_completion`.

## MCP Runtime Validation

Do not add repository-side validation scripts. Runtime validation must come from the mandatory `codex-context-ledger` MCP calls and their preserved return values, including the stage-specific validators above.

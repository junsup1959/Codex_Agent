# Contracts And Ledgers

All architecture-required stages exchange structured artifacts and update `codex-context-ledger`.

## Common Stage Fields

Every mandatory stage packet includes:

- `stage_name`
- `stage_execution_mode`
- `run_id`
- `loop_id`
- `context_packet_version`
- `consumed_context_revision`
- `context_delta`
- `new_artifact_refs`
- `new_evidence_refs`
- `stage_pass_ref`
- `mcp_quiescence_snapshot`

## Context Delta

`context_delta` contains only new or changed run state:

- approved facts
- constraints
- artifact additions
- evidence additions
- blockers
- stale markers
- readiness changes

The ledger merges this into the next `context_packet` through `write_context_packet`.

## Stage Pass

`append_stage_pass` records who ran, which revision was consumed, what evidence was emitted, and whether the stage can hand off.
Every stage handoff must carry `validate_context_revision_result.valid=true` for the consumed context revision.

## Worker And Review Evidence

Worker and review handoffs must preserve:

- lane id
- specialist role
- source packet ref
- spawn receipt ref
- child identity: `agent_id` or `submission_id`
- `wait_agent` evidence for every returned child
- output artifact refs
- validation evidence
- confidence
- blockers
- lane status classification

## Feedback Evidence

`$feedbackgate` requires review inputs or waivers, MCP validation evidence, current context revision, clean MCP/tool quiescence, and non-empty `feedback_gate_evidence`.

Feedback loops must include `task_design_reentry_decision` with reusable artifacts, invalidated artifacts, distribution action, and review distribution action. `$context-ledger` persists this as `reentry_cache` for the next loop.

## Artifact Profile

Reusable planning artifacts must include:

- `artifact_profile.version`
- `artifact_profile.source_stage`
- `artifact_profile.reuse_policy`
- `artifact_profile.invalidated_by`

This applies to `task_design`, `execution_plan`, and `review_plan`.

## Sequential Thinking Evidence

`$orchestrator`, `$task-designer`, `$task-distributor`, and `$review-distributor` must attempt `MCP_DOCKER.sequentialthinking` before finalizing their stage artifacts.

The persisted evidence is `sequential_thinking_ref` on success or `sequential_thinking_waiver` on tool failure, not the reasoning transcript. Missing both fields invalidates the stage packet or stage-specific artifact.

## MCP API Validation

Stage-local Python preflight scripts are not part of the runtime contract. Each mandatory skill calls `validate_context_revision`, `validate_stage_packet`, and `validate_tool_sequence` through `codex-context-ledger`. Stage-specific validators are also part of the contract:

- `$task-designer`: `validate_task_design`
- `$task-distributor`: `validate_execution_plan`
- `$review-distributor`: `validate_review_plan`
- `$worker`, `$review`, `$feedbackgate`: `validate_stage_completion`

The MCP records tool-call events and rejects incomplete or out-of-order stage flows.

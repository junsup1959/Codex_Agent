# Runtime Orchestration Steps

This file is the procedural sequence for `architecture_required=true` runs. Detail files define contracts; this file defines the runtime order. Treat it like Maestro's `orchestration-steps`: do not improvise, skip, or reorder steps unless a direct-answer exception or a valid feedback `judgment_envelope` says the loop is blocked.

## Authority

- `AGENTS.md` stays a compact pointer.
- `AGENT-ARCHITECTURE.md` and `AGENT-ARCHITECTURE-MAPPER.md` route readers to this sequence and the detail contracts.
- Stage detail files remain authoritative for field shapes, validators, and failure classes.
- Runtime TOML prompts must stay consistent with this sequence.

## Startup Gate

1. Classify the request before work starts. If it is simple direct-answer work, record `direct_answer_exception=true` and answer directly.
2. If the request is non-trivial or mentions architecture, orchestration, harness, agent structure, feedback gate, routing, or multi-artifact work, set `architecture_required=true`.
3. Use available MCP before substantive work. For `orchestrator`, `context-manager`, `aggregator`, `review-router`, reviewer lanes, and `meta-judge`, successful evidence must identify `MCP_DOCKER/sequentialthinking:success`; failures are blocker or waiver evidence only.
4. Activate `$orchestrator` and use it to assign `run_id`, `loop_id`, `loop_attempt`, `context_packet_version`, and the default `fanout_budget`.
5. Initialize or update exactly one `codex-context-ledger` MCP run entry; do not spawn a physical `context-manager`.

## Control Loop

1. Main agent activates `$orchestrator` and emits one `orchestration_request` with user goal, allowed scope, constraints, success criteria, MCP evidence, feedback re-entry, `loop_carryover`, `loop_control`, `mcp_quiescence_snapshot`, and `contract_provenance`.
2. Main agent runs the `context-manager` role pass locally, reads/writes `codex-context-ledger`, emits one `context_packet`, owns accepted facts and artifact inventory in the ledger, and marks `role_pass_readiness`.
3. Main agent activates `$task-planner`; `task-planner` consumes the current `context_packet` and emits one `execution_plan` with bounded lanes, expected handoff fields, review hints, and `fanout_budget`.
4. Main agent activates `$worker-router`, summons the full specialist list from `${CODEX_HOME}/agents/<category>/*.toml`, and executes the `worker-router` role pass locally to validate and emit a logical worker `launch_manifest`. It never spawns or waits; caller materialization creates `active_passes`.
5. Main agent activates `$task-distributor`; caller materializes only budget-compliant worker lanes, records concrete `spawn_receipt_ref`, `agent_id`, `submission_id`, `wait_handle`, and later `wait_agent` evidence.
6. Worker specialists return `handoff_result` packets. Every returned or missing lane is classified before aggregation.
7. Main agent activates `$result-aggregator`; `aggregator` consumes returned `handoff_result` values, `active_passes`, missing-lane classes, and schema-invalid outputs. It emits either `aggregation_packet` or `aggregation_ready=false` for judgment.
8. Main agent activates `$review-router`, summons the full specialist list from `${CODEX_HOME}/agents/<category>/*.toml`, and executes the `review-router` role pass locally to emit a logical review `launch_manifest` from a valid `aggregation_packet`; caller materializes reviewers and records `active_passes`.
9. Main agent activates `$task-distributor` again; reviewer specialists return reviewer `handoff_result` packets or explicit missing-review classifications.
10. Main agent activates `$feedback-synthesizer`; `meta-judge` emits `judgment_envelope` and applies the Feedback Trigger Gate.

`$docker-memory` may be activated when durable Docker MCP Memory lookup or recording is useful. It is never required for this sequence.

## Transition Gate

After every canonical stage artifact, run the runtime handoff gate before the next owner acts:

1. Validate artifact shape with `validate-runtime-artifact.py`.
2. Route through `harness_handoff.py` and `harness_gate.py`.
3. Record `stage_passes` with `stage_execution_mode=main_agent_role_pass` unless an explicit physical override is recorded.
4. Reject stale `context_revision`, missing `contract_provenance`, missing MCP cleanup, open tool calls, unwaited children, or unclassified lanes.
5. If a physical child was spawned, it must be targeted by `wait_agent`; `close_agent` is cleanup only.

## Feedback And Resume

1. Final output is forbidden while `feedback_required=true`.
2. Final output also remains forbidden when `meta_judge_stage_pass_ref`, reviewer `review_input_refs` or `review_waivers`, `feedback_gate_evidence`, or `gate_evidence_bundle` is missing or stale.
3. Feedback always returns to `orchestrator`, then restarts at the MCP-backed `context-manager` role pass with preserved `loop_carryover`.
4. Resume starts from the latest valid run ledger, `stage_passes`, `active_passes`, and `judgment_envelope`; never resume from prose memory alone.
5. Archive only after all materialized lanes are waited, returned, superseded, timed out, schema-invalid, or explicitly classified, and MCP/tool quiescence is clean.

## Operating Commands

- Status: read the current run ledger, `stage_passes`, `active_passes`, and latest `judgment_envelope`; do not mutate state.
- Resume: re-enter at the first blocked or pending transition gate with the latest MCP-backed `context_packet`.
- Archive: preserve artifacts, stage ledgers, child pass ledgers, review evidence, feedback judgments, and validator outputs.

## Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.
Hook-level checks that only guard stage skill `contract.json` drift should run `${CODEX_HOME}/agent-architecture/validate-skill-contracts.py`; this is the fast preflight, not a replacement for the full architecture validator.

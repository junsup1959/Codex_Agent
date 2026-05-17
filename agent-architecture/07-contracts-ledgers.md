# Contracts And Ledgers

This document defines the shared artifacts, manifests, ledgers, and field contracts used by the canonical orchestration loop.

## Canonical Artifact Names
| Artifact | Owner | Purpose |
| --- | --- | --- |
| `orchestration_request` | `orchestrator` | run goal, allowed scope, constraints, loop id, feedback re-entry |
| `context_packet` | `context-manager` | compact synced context, accepted evidence, artifact inventory |
| `execution_plan` | `task-planner` | one execution wave and lane ownership design |
| `launch_manifest` | `worker-router`, `review-router` | logical child lanes for caller materialization |
| `active_passes` | caller or harness owner | physical child wait handles and status ledger |
| `stage_passes` | caller or harness owner | control-stage lifecycle ledger |
| `handoff_result` | child workers/reviewers/support specialists | bounded returned result |
| `aggregation_packet` | `aggregator` | review-ready normalized worker output |
| `judgment_envelope` | `meta-judge` or top-level caller | final/feedback decision |

## Contract Provenance Mixin
Every canonical stage artifact carries `contract_provenance`; artifact branches place it inside the artifact, non-artifact failure branches place it top-level.

`contract_provenance` must include:
- `source_contract_refs`
- `contract_lookup_missing`

## Resident Context Fields
`context_packet` must include `context_authority_ref`, `context_packet_version`, `context_revision`, and `role_pass_readiness`. `context_authority_ref` points to the `codex-context-ledger` MCP run entry. `role_pass_readiness` must identify the role-pass names allowed from the current packet and the stages requiring refresh before use. Main-agent role passes record the consumed `context_revision`; stale or missing revision blocks handoff.
## Logical Launch Manifest
`launch_manifest.children[]` is not a waitable child handle. Top-level `launch_manifest` carries `manifest_kind`, `source_parent_ref`, one source ref, `context_packet_version`, `children`, `loop_control`, `fanout_budget`, `contract_provenance`, and `schema_status`.
`execution_plan` and `launch_manifest` must include `fanout_budget` with:

- `max_worker_lanes_per_wave`
- `max_review_lanes_per_wave`
- `max_total_child_agents_per_loop`
- `max_same_role_parallel_lanes`
- `max_mcp_concurrent_child_lanes`
- `budget_reason`
- `overflow_policy`

Each logical child lane must include:

- `lane_id`
- `parent_router_pass_id`
- `agent_category`
- `agent_role`
- `lane_type`
- `owned_scope`
- `expected_artifact`
- `merge_point`
- `return_owner`
- `validation_prompt`
- `context_packet_version`
- `spawn_context_mode`
- `caller_spawn_required`
- `initial_status`

Logical lane rules:

- `agent_fanout_budget_required=true`: default physical fanout is at most 2 worker lanes, 2 reviewer lanes, 4 total child agents per loop, 1 same-role parallel lane, and 1 MCP-using child lane at a time.
- Router-created lanes default to `caller_spawn_required=true` and `initial_status=unmaterialized`.
- `spawn_context_mode` must be one of `fork_context | scoped_packet | scoped_packet_with_waiver`; router/aggregator stages default to `fork_context`, worker/reviewer specialists default to `scoped_packet`. Specialist lanes cannot use `fork_context`; `scoped_packet_with_waiver` requires `spawn_context_waiver={reason,risk,review_axis,evidence_ref}`.
- Runtime spawn API constraint: do not combine `fork_context=true` with explicit `agent_type`. Full-history forked agents inherit the parent type, so dedicated canonical stage owners use curated packets with `fork_context=false`.
- Routers may propose same-role parallel lanes only when `lane_id`, ownership, and merge point are distinct.
- Routers must not invent `agent_id`, `submission_id`, or `wait_handle` for children the caller has not materialized.
- If a caller already provides a concrete child, the router still records it as a lane and the caller mirrors the handle into `active_passes`.

## Launch Manifest Prompt Validation
Runtime prompts that emit `launch_manifest` must run `launch_manifest_schema_gate`: all logical lane fields are present, no logical lane contains `agent_id`, `submission_id`, or `wait_handle`, router-created lanes use `caller_spawn_required=true`, `initial_status=unmaterialized`, and a valid `spawn_context_mode`; invalid manifests return addressable `schema_invalid={manifest_kind, source_parent_ref, context_packet_version, parent_router_pass_id, lane_ids, missing_fields, forbidden_fields}`, not handoff.

## Physical Active Passes Ledger
Caller tracks materialized worker/reviewer passes with:

- `run_id`, `loop_id`, `loop_attempt`, `lane_id`, `pass_id`, `role`
- `agent_category`, `agent_role`, `agent_id`, `submission_id`
- `wait_handle_type`, `wait_handle`
- `source_launch_manifest_ref`, `spawn_tool`, `spawn_receipt_ref`, `spawned_at`, `wait_registered_at`
- `owned_scope`, `merge_point`, `context_packet_version`, `status`

Physical handle rules: use `agent_id` for persistent identity and `submission_id` for queued input or launch identity; never merge them. `wait_handle_type` must be `agent_id` or `submission_id`, and `wait_handle` must copy the exact value the caller should wait on.
- The runtime validator supports `--artifact active_passes` and router materialization must validate this ledger before layer handoff.
- `spawn_tool` must be `spawn_agent`; `spawn_receipt_ref`, `spawned_at`, and `wait_registered_at` are mandatory physical execution witnesses.
- `wait_registered_at` records a `wait_agent` obligation, not a cleanup event. `close_agent` status may be recorded separately, but it is not a substitute for `wait_agent` evidence.
- Completed or classified child passes carry `pass_closure_proof={wait_result_ref|classification_ref|superseded_ref}`; `close_agent_ref` may appear only as cleanup evidence, never as the sole proof.
- A failed `spawn_agent` response creates no active child. Record it as `spawn_failed` or `thread_limit_reached` with `spawn_failure_ref`, `spawn_failure_output`, and `retry_or_classification_required=true`; do not populate `agent_id`, `spawn_receipt_ref`, or `wait_registered_at` from a failed spawn.
## Handoff Result Fields
Every child return starts with:

- `sender`
- `lane_id`
- `pass_id`
- `parent_pass_id`
- `pass_status`
- `owned_scope`
- `artifact_summary`
- `artifact_ref`
- `artifact_kind`
- `evidence_refs`
- `findings`
- `confidence`
- `merge_point`
- `context_packet_version`
- `caller_signals`

Allowed `pass_status`: `returned | superseded | closed | timed_out | schema_invalid`.

## Aggregation Inputs
Aggregator consumes:
- returned `handoff_result` values
- artifact refs/kinds carried from `handoff_result`
- `context_packet_version` carried from child returns
- current `active_passes` status summary
- missing lane classifications
- schema-invalid output list
- `aggregation_input_bundle={handoff_results_ref[], active_passes_ref, missing_lane_classes_ref[], schema_invalid_outputs_ref[], aggregation_input_mode=canonical}`

Aggregator may start only when all lanes are either returned or explicitly classified as:
`unmaterialized_lane | spawn_failed | thread_limit_reached | no_wait_handle | timed_out | superseded | schema_invalid`
Closed-only children are not returned lanes. If a child has `close_agent` evidence but no matching `wait_agent` target/result, classify the lane as `no_wait_handle` or keep the run blocked.
Thread-limit spawn failures are blocking materialization failures until the caller frees capacity and retries or records an explicit missing-lane classification. Aggregator and meta-judge prompts must not treat a failed spawn as a returned `handoff_result`.

`blocked_aggregation.aggregation_inputs.handoff_results[]` must validate as `handoff_result`; `active_passes_summary[]` must validate as active-pass records; `schema_invalid_outputs[]` must validate as `schema_invalid` records.

## Stage Passes Ledger

Control-stage passes are tracked separately from child `active_passes`:

- `run_id`, `loop_id`, `loop_attempt`, `stage_pass_id`, `stage_owner`, `stage_status`
- `artifact_name`, `artifact_ref`, `context_packet_version`, `schema_status`
- `created_at`, `closed_at`, `next_owner`
- `stage_spawn_contract`

Routers and gate agents close after artifact return; they must not remain active watchers. `stage_spawn_contract={spawn_agent_type, spawn_fork_context, spawn_packet_mode}`.

Main-agent role-pass stages record `stage_spawn_contract={spawn_agent_type=main-agent, spawn_fork_context=false, spawn_packet_mode=main_agent_role_pass}`. Physical stage passes record the actual stage owner role and spawn packet mode. Main-agent role-pass control stages are valid only after their canonical artifact passes runtime validation. The resident physical context manager is tracked as a singleton owner; do not spawn duplicate context managers per loop.

## Harness Run Ledger

Non-trivial runs also keep run-level fields: `run_id`, `loop_id`, `user_goal`, `allowed_scope`, `stage`, `stage_artifact_name`, `stage_artifact_ref`, `schema_status`, `validation_evidence`, `context_packet_version`, `loop_attempt`, `repeat_feedback_count`, `feedback_gate_mandatory`, `feedback_required`, `failure_class`, `decision`, `next_owner`, `created_at`, and `updated_at`.

## Schema Rule
Runtime handoff rule: no next stage starts until `${CODEX_HOME}/agent-architecture/harness_handoff.py` calls `${CODEX_HOME}/agent-architecture/validate-runtime-artifact.py` and `${CODEX_HOME}/agent-architecture/harness_gate.py`, then returns `allow_next_stage=true`; the decision records `runtime_validation_required=true`, `expected_next_owner`, optional `expected_source_ref`, optional `expected_context_packet_version`, optional prior `judgment_envelope` via `--previous-judgment-json`, `previous_judgment_checked`, and `route_kind=proceed|retry_same_stage|feedback_restart`. Invalid artifacts use `retry_same_stage`; only a valid feedback `judgment_envelope` uses `feedback_restart`.

`harness_handoff.py --next-input-out` may emit `transport_wrapper=blocked_handoff` when a handoff is blocked. That wrapper is caller transport, not a canonical stage artifact.

Before aggregation and final judgment the caller records `tool_quiescence_snapshot={open_tool_call_count, open_tool_call_ids, snapshot_at}`; non-zero open tool calls block progression.

## MCP Lifecycle Contract
`per_agent_mcp_lifecycle_required=true`: each agent/stage owner initializes required MCP inside its own bounded work scope and never relies on hidden inherited MCP session state.
`mcp_process_shutdown_required=true`: before any stage artifact, `handoff_result`, review result, feedback judgment, or final claim is handed off, the agent closes MCP sessions/processes and records `mcp_quiescence_snapshot`.
`mcp_quiescence_snapshot` fields are `open_mcp_process_count`, `open_mcp_process_ids`, `cleanup_status`, and `snapshot_at`. `mcp_process_residue_forbidden=true`: `open_mcp_process_count` must be `0`, `open_mcp_process_ids` must be empty, and `cleanup_status` must be `clean`.

## Completion Evidence Resolution
Final or feedback completion is valid only when `meta_judge_stage_pass_ref` resolves to a closed same-loop `stage_pass`, every `review_input_refs[]` item resolves to a returned reviewer `handoff_result`, or `review_waivers[]` explicitly covers the axis. String-only refs are invalid completion evidence.
## Judgment Envelope Fields
`judgment_envelope` must include: `loop_id`, `loop_stage`, `decision`, `feedback_required`, `feedback_target`, `next_owner`, `next_loop_start`, `final_blocked_reason`, `bounded_rework_request`, `success_criteria`, `confidence`, `validation_evidence`, `review_input_refs`, `meta_judge_stage_pass_ref`, `feedback_gate_evidence`, `review_coverage`, `review_waivers`, `source_aggregation_packet_ref`, `source_blocked_aggregation_ref`, `loop_carryover`, `loop_control`, `gate_evidence_bundle`, `tool_quiescence_snapshot`, and `contract_provenance`.

Allowed `loop_stage`: `context-sync | planning | execution | aggregation | review | judgment | refinement | complete`.

## Loop Carryover Fields
`loop_carryover` must include: `preserved_allowed_scope`, `unmet_success_criteria`, `unresolved_blockers`, `rejected_assumptions`, `required_validation_evidence`, `context_packet_version`, and `source_judgment_ref`.

## Loop Control Fields
`loop_control` must include: `loop_attempt`, `repeat_feedback_count`, `max_loop_attempts`, `progress_delta`, and `no_progress_action`.

`progress_delta[]` entries carry `new_artifact_refs`, `new_evidence_refs`, `changed_blocker_fingerprint`, and `changed_context_packet_version`.

## Feedback Gate Fields
`judgment_envelope` and run ledger record `feedback_gate_mandatory=true` and `feedback_required`; when `feedback_required=true`, final output is forbidden, `final_blocked_reason` is required, and feedback entries require `next_loop_start=context-manager`, `bounded_rework_request`, and non-empty `success_criteria`. Final output is also forbidden when `feedback_gate_evidence` is missing or stale, `meta_judge_stage_pass_ref` is absent, reviewer `review_input_refs` or explicit `review_waivers` are absent, or any required layer remains unmaterialized, timed out, schema-invalid, superseded, conflicting, or unclassified.

Formal feedback-gate evidence requires `meta_judge_stage_pass_ref`, reviewer `review_input_refs` or explicit `review_waivers`, and non-empty `feedback_gate_evidence`. Synthetic schema checks alone are not evidence that reviewer/meta-judge passes physically ran.

Final judgment also requires `gate_evidence_bundle={stage_passes_ref, active_passes_ref, review_results_ref, mcp_evidence_summary}`.

`unresolved_blockers[]` preserves `blocker_type`, `source_pass_id`, `artifact_ref`, and `evidence_refs`.

Downstream lineage refs: `execution_plan.source_context_packet_ref`, worker `launch_manifest.source_execution_plan_ref`, review `launch_manifest.source_aggregation_packet_ref`, `aggregation_packet.source_launch_manifest_ref`, blocked branch `source_blocked_aggregation_ref`, `judgment_envelope.source_aggregation_packet_ref`, and `judgment_envelope.source_blocked_aggregation_ref` bind artifacts to the current loop chain.

`bounded_rework_request` is delta-only: `target`, `reason`, `source_judgment_ref`, `requested_scope_refs`, `allowed_scope_subset_of`, `requested_actions`, `success_criteria_delta`, and `blocker_refs`; full `loop_carryover`/`loop_control` stays authoritative on `judgment_envelope`.
## Architecture Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.

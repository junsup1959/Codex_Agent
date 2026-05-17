# Feedback And Lifecycle

This document defines `meta-judge`, feedback restart, loop integrity, and pass cleanup. Feedback is a bounded restart contract, not an unstructured retry.

## Meta Judge

### Owns

- final approval versus bounded feedback
- reviewer output interpretation
- harness failure classification check
- residual risk statement
- one explicit `judgment_envelope`

### Does Not Own

- worker execution
- reviewer routing
- context packet rewrite
- direct mid-stage restart

## Judgment Envelope

Required fields:

- `loop_id`
- `loop_stage`
- `decision`
- `feedback_required`
- `feedback_target`
- `next_owner`
- `next_loop_start`
- `final_blocked_reason`
- `bounded_rework_request`
- `success_criteria`
- `confidence`
- `validation_evidence`
- `review_input_refs`
- `meta_judge_stage_pass_ref`
- `feedback_gate_evidence`
- `review_coverage`
- `review_waivers`
- `source_aggregation_packet_ref`
- `source_blocked_aggregation_ref`
- `loop_carryover`
- `loop_control`
- `gate_evidence_bundle`
- `tool_quiescence_snapshot`
- `contract_provenance`

Allowed `loop_stage`:

`context-sync | planning | execution | aggregation | review | judgment | refinement | complete`

Allowed `decision`:

`feedback | final output`

Allowed `feedback_target`:

`context-manager | task-planner | worker-layer | aggregator | review-router | review-layer | orchestrator | user | none`

Feedback target mapping:

| feedback_target | bounded rework scope | next_owner | next_loop_start |
| --- | --- | --- | --- |
| `context-manager` | context correction | `orchestrator` | `context-manager` |
| `task-planner` | plan refinement | `orchestrator` | `context-manager` |
| `worker-layer` | worker rerun or new lane | `orchestrator` | `context-manager` |
| `aggregator` | merge/classification repair | `orchestrator` | `context-manager` |
| `review-router` | review lane redesign | `orchestrator` | `context-manager` |
| `review-layer` | reviewer rerun or extra lens | `orchestrator` | `context-manager` |
| `orchestrator` | scope/governance decision | `orchestrator` | `context-manager` |
| `user` | missing external input | `orchestrator` | `context-manager` |
| `none` | no feedback path | `orchestrator` | `none` |

## Feedback Trigger Gate

- `feedback_gate_mandatory=true`; the gate is mandatory before every ready/final/approve/safe-to-proceed/completion claim.
- Before any ready/final/approve/safe-to-proceed response, `meta-judge` checks unmet requirements, reviewer findings, schema failures, low confidence, missing lanes, and validation evidence gaps.
- If feedback is needed, set `feedback_required=true`; final output is forbidden while `feedback_required=true`.
- If gate evidence is absent, stale, string-only, missing reviewer refs/waivers, or missing the physical `meta-judge` stage pass ref, the default is fail-closed and final output is forbidden.
- If any materialized child was never targeted by `wait_agent`, or if only `close_agent` evidence exists for that child, gate evidence is incomplete and final output is forbidden.
- If MCP usage was required but every available MCP call failed, was blocked, returned unusable error output, or the MCP-required evidence was dropped by `context-manager`, `task-planner`, `aggregator`, `review-router`, reviewer lanes, or `meta-judge`, record an MCP waiver or blocker; do not count that as successful MCP evidence.
- `per_agent_mcp_lifecycle_required=true` and `mcp_process_shutdown_required=true` for `meta-judge` and feedback handling. `meta-judge` may initialize MCP in its own judgment scope, but it must close MCP sessions/processes and attach `mcp_quiescence_snapshot` before returning `judgment_envelope`.
- `docker_mcp_sequentialthinking_required=true` for `meta-judge`; final approval is forbidden unless current gate evidence identifies `MCP_DOCKER/sequentialthinking:success`. `Transport closed` forces feedback or MCP repair.
- Final gate input must carry a physical evidence bundle: `stage_passes`, `active_passes`, and reviewer evidence via `review_results`, `review_input_refs`, or `review_waivers`. A final prompt without that bundle is not eligible for approval.
- Final approval is forbidden when any stage/reviewer `mcp_quiescence_snapshot` is missing, has `open_mcp_process_count>0`, or has `cleanup_status!="clean"`.
- Every blocked final sets `final_blocked_reason`, `bounded_rework_request`, and non-empty `success_criteria`.
- Every feedback decision preserves `loop_carryover={preserved_allowed_scope, unmet_success_criteria, unresolved_blockers, rejected_assumptions, required_validation_evidence, context_packet_version, source_judgment_ref}`.
- Every feedback decision updates `loop_control={loop_attempt, repeat_feedback_count, max_loop_attempts, progress_delta, no_progress_action}`.
- Every feedback decision sets `next_loop_start=context-manager`; the loop returns to `orchestrator` first, then restarts from `context-manager`.
- If the same blocker and same evidence repeat, increment `loop_control.repeat_feedback_count`; repeated no-progress feedback must `respond to user` or require `schema/tool/doc repair` instead of silently looping.

Gate boundary: `Feedback Trigger Gate` is required logic inside `meta-judge`, not a separate long-lived worker. Its output is the `judgment_envelope` fields that either permit final output or force feedback re-entry.

## Feedback Rule

- `meta-judge` returns either final output or bounded feedback.
- Feedback always returns to `orchestrator`.
- Feedback never re-enters a mid-loop stage directly.
- `feedback_target` is a hint for the restarted loop, not a stage-jump permission.
- `orchestrator` restarts from `context-manager`, then routes toward the hinted refinement stage with the bounded rework request.
- Feedback re-entry must not widen `loop_carryover.preserved_allowed_scope`, drop unmet criteria, change `loop_id`, change `source_judgment_ref`, or collapse `loop_carryover.unresolved_blockers[]` lineage into prose.
- If a previous `judgment_envelope` is available, the harness passes it as `--previous-judgment-json` so lineage can be checked mechanically across 2, 3, 4, or later loop attempts; the decision records `previous_judgment_checked=true`.
- A claim that `Feedback Trigger Gate` ran formally requires a physical `meta-judge` stage pass reference, reviewer `handoff_result` refs or explicit review waivers, and non-empty `feedback_gate_evidence`.

## Pass Status Transitions

| Current | Actor | Trigger | Next | Note |
| --- | --- | --- | --- | --- |
| none | caller | spawn pass | `active` | register in `active_passes` |
| `active` | child | return artifact | `returned` | normal child return in `handoff_result` |
| `active` | caller | timeout checkpoint | `timed_out` | classify before aggregation |
| `active` | caller/gate | invalid child output | `schema_invalid` | attach `schema_invalid_outputs[]` |
| `active` | router | return logical `launch_manifest` | `closed` | caller handles physical child registration |
| `active` | caller | stale ownership/context/merge point | `superseded` | stale output needs revalidation |
| `returned` | caller | result integrated | `closed` | normal cleanup |
| `returned` | caller | better pass replaces same merge point | `superseded` | keep record, exclude from active judgment |
| `superseded` | caller | cleanup complete | `closed` | terminal state |
| `timed_out` | caller | classification recorded | `closed` | terminal state |
| `schema_invalid` | caller | invalid output recorded | `closed` | terminal state |

## Cleanup Rule

- Returned control passes should not remain open as active workers.
- `context-manager`, `task-planner`, `worker-router`, `aggregator`, `review-router`, and `meta-judge` are stage passes; close them after artifact return.
- Close after wait, not instead of wait. `close_agent` can clean up a completed child, but it cannot create or replace `wait_agent` result evidence.
- If a returned pass still appears `running` or `pending_init`, classify it as `runtime_residue` and close unless the user explicitly asks to keep it.
- Long-lived ownership belongs only to caller-materialized specialists/reviewers with concrete wait handles.

## Formal Gate Evidence

`Feedback Trigger Gate` is logic inside `meta-judge`, not a separate long-lived gate agent. It may only be reported as formally executed when `judgment_envelope` records `meta_judge_stage_pass_ref`, `review_input_refs` or `review_waivers`, and `feedback_gate_evidence`.

Formal gate evidence must be current for the same `loop_id`, `context_packet_version`, and aggregation/review inputs. Older successful gate evidence cannot approve a later changed artifact.

## Architecture Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.


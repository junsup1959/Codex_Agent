# Feedback Lifecycle

`$feedbackgate` is the mandatory final gate after `$orchestrator` has explicitly started an architecture run.

## Inputs

- worker handoff results and lane classifications
- review handoff results or review waivers
- MCP validation evidence
- MCP/tool quiescence evidence
- latest context packet and blockers

## Judgment

`feedback_gate_mandatory=true`: final, ready, approve, merge-ready, safe-to-proceed, or completion claims are forbidden until `$feedbackgate` passes.

`$feedbackgate` must verify:

- every spawned worker and reviewer was waited or explicitly classified
- review coverage is sufficient or waived with reason
- MCP validations passed or blockers are recorded
- context revision is current
- `feedback_gate_evidence` is non-empty
- MCP/tool residue is clean

## Outcomes

If checks pass, `$feedbackgate` emits final approval evidence.

If checks fail, it emits `feedback_required=true`, bounded rework scope, and `next_owner="orchestrator"`. Feedback always restarts at `$orchestrator`, then `$context-ledger`; it never jumps directly into a worker or review lane.

Feedback loops must also emit `task_design_reentry_decision` so the next loop does not redesign work unnecessarily:

- `revise_task_design`: assumptions, goals, success criteria, or selected option changed; rerun `$task-designer`.
- `reuse_task_design`: design is still valid; keep the existing `task_design_ref` and continue with downstream adjustment.
- `skip_to_distribution`: design is valid and only distribution/lane routing needs adjustment; `$context-ledger` may hand off to `$task-distributor`.

`reuse_task_design` and `skip_to_distribution` require `task_design_ref` plus a reason.

Every feedback reentry decision must also declare:

- `reusable_artifacts`
- `invalidated_artifacts`
- `distribution_action`
- `review_distribution_action`

`$context-ledger` preserves that decision as `reentry_cache` so the next loop can skip unchanged design/distribution work without losing artifact provenance.

## Ledger Handoff

Before final or feedback handoff, `$feedbackgate` writes `context_delta`, `new_artifact_refs`, `new_evidence_refs`, and `stage_pass_ref` through `$context-ledger`.

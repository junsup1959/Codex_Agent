# Feedback Lifecycle

`$feedbackgate` is the mandatory final gate for architecture-required work.

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

## Ledger Handoff

Before final or feedback handoff, `$feedbackgate` writes `context_delta`, `new_artifact_refs`, `new_evidence_refs`, and `stage_pass_ref` through `$context-ledger`.

---
name: review-aggregator-handoff
description: Package worker, reviewer, and synthesis outputs into canonical envelopes for `aggregator`, `review-router`, and `meta-judge` without dropping scope, evidence, confidence, or merge assumptions. Use when an agent must hand off bounded results, return from a spawned pass, prepare review-ready packets, report contradictions, or write a final judgment envelope inside the canonical orchestration loop.
---

# Review Aggregator Handoff

## Overview

Use this skill to turn a pass result into a compact handoff that the next agent can merge without guessing.
Load [references/handoff-templates.md](references/handoff-templates.md) when you need copy-ready envelopes for `handoff_result`, aggregation packets, review packets, or judgment outputs.

## Agent Coordination

Use this skill first in the `result-collection/synthesis` lane, and also apply it at the end of any worker or reviewer pass that is about to return control.
Escalate to `adviser` instead of forcing a handoff when `owned_scope`, `merge_point`, `context_packet_version`, or required evidence is missing.
Escalate to `governor` or the active risk-review lane before handing off when scope expansion, policy risk, destructive actions, or unverifiable claims appear.
Keep this skill as a packaging helper for the active stage; do not use it to bypass `aggregator`, `review-router`, `meta-judge`, or top-level orchestration.

## Handoff Workflow

1. Restate the exact owned scope in one line.
2. Summarize only the artifact that was actually produced.
3. Attach evidence references instead of vague claims.
4. State confidence as a bounded judgment.
5. Name the merge point and `context_packet_version`.
6. Surface blockers, contradictions, and follow-up needs in `caller_signals`.
7. Choose the matching template from [references/handoff-templates.md](references/handoff-templates.md).
8. Stop after transfer unless the caller explicitly keeps ownership with you.

## Stage Rules

### Return To `aggregator`

Use the shared `handoff_result` envelope.
Include touched scope, completion status, missing evidence, and contradictions.
Prefer short factual statements so the aggregator does not have to infer hidden work.

### Return From `aggregator` To Review

Produce one normalized packet that compares worker outputs, identifies contradictions, and lists unanswered questions.
Mark each risk as evidence-backed, inferred, or unknown.
Do not approve the work; only prepare it for review.

### Return From Reviewers To `meta-judge`

Keep findings severity-ordered and tied to evidence.
Separate confirmed defects, residual risk, and missing validation.
Recommend whether the loop should continue, but leave the decision to `meta-judge`.

### Emit Final Judgment

Use the judgment envelope exactly once per judgment pass.
Set `decision`, `next_owner`, and `feedback_target` explicitly.
If refinement is needed, return to `orchestrator`; do not jump directly to a mid-loop stage.

## Quality Bar

Reject the handoff as incomplete if any of the following is missing:

- `owned_scope`
- `artifact_summary`
- at least one concrete `evidence_ref` for non-trivial claims
- `confidence`
- `merge_point`
- `context_packet_version`

Prefer `unknown` over invented certainty.
Prefer `not executed` over implying validation happened.
Label inference when evidence does not directly prove the claim.
Keep the envelope compact enough that the receiving agent can skim it in one pass.

---
name: feedbackgate
description: Execute the mandatory global Codex Feedback Gate stage. Use when specialist review results must determine final output or bounded feedback back to orchestrator.
---

# Feedbackgate

Use this skill after specialist review lanes return or receive explicit waivers. The main agent performs the final judgment locally and either allows final output or loops back to `$orchestrator`.

## Contract Gate

Before running this skill, read the adjacent `contract.json`. Treat `input_artifacts`, `output_artifacts`, `forbidden_outputs`, `required_evidence`, and `source_docs` as the local checklist. Load the listed `${CODEX_HOME}/agent-architecture/<source_doc>` files before emitting the stage artifact. Prefer `scripts/check_feedbackgate.py` before final output. If this skill, its contract, scripts, or source docs change, run `python ${CODEX_HOME}/agent-architecture/validate-skill-contracts.py`.

## Inputs

Read these before judgment:

- worker `handoff_result` packets and worker lane classifications
- specialist review `handoff_result` packets or explicit review waivers
- current `stage_passes`, `active_passes`, validator evidence, and MCP evidence
- latest `context_packet_version`, blockers, and loop carryover
- `${CODEX_HOME}/agent-architecture/05-feedback-lifecycle.md`
- `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md`
- `${CODEX_HOME}/agent-architecture/08-quality-evals.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Workflow

1. Verify all spawned worker and review specialists were waited or explicitly classified.
2. Verify review coverage, waivers, validator evidence, MCP evidence, and tool cleanup.
3. If any blocker remains, emit `feedback_required=true`, bounded rework scope, and `next_owner="orchestrator"`.
4. If all checks pass, emit final approval evidence and allow the user-facing final output.
5. Preserve `loop_carryover` and do not widen scope on feedback.

## Hard Rules

- Do not issue final, ready, complete, approve, or merge-ready language before this gate passes.
- Do not accept prose-only review evidence.
- Do not approve with missing waits, stale context, schema-invalid outputs, open MCP/tool residue, or unresolved review blockers.
- Feedback always returns to `$orchestrator`; it never jumps directly into a mid-loop specialist.

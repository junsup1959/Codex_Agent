---
name: result-aggregator
description: Execute the global Codex Aggregator stage as a main-agent skill. Use when returned worker or reviewer handoff_results must be reconciled into one evidence-grounded aggregation_packet.
---

# Result Aggregator

Use this skill after materialized lanes have been waited and classified. The main agent performs the aggregation stage locally and records it as `stage_execution_mode=main_agent_role_pass`.

## Contract Gate

Before running this skill, read the adjacent `contract.json`. Treat `input_artifacts`, `output_artifacts`, `forbidden_outputs`, `required_evidence`, and `source_docs` as the local checklist. Load the listed `${CODEX_HOME}/agent-architecture/<source_doc>` files before emitting the stage artifact. If this skill, its contract, or its source docs change, run `python ${CODEX_HOME}/agent-architecture/validate-skill-contracts.py` before handoff.

## Inputs

Read these before aggregating:

- returned `handoff_result` packets
- `active_passes` and source pass statuses
- artifact refs, changed files, confidence, blockers, and contradictions
- `context_packet_version`
- `${CODEX_HOME}/agent-architecture/04-aggregation-review.md`
- `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Workflow

1. Confirm every materialized child was waited or explicitly classified.
2. Reject prose-only summaries that lack handoff packet evidence.
3. Normalize claims, artifact refs, confidence, blockers, and unresolved assumptions.
4. Surface contradictions instead of silently choosing one result.
5. Decide whether `aggregation_ready=true`; if not, return a blocked aggregation packet.
6. Return exactly one canonical `aggregation_packet`.

## Hard Rules

- Do not review, approve, or claim final readiness.
- Do not drop failed, timed-out, schema-invalid, or conflicting lanes.
- Do not treat unwaited lanes as complete.
- Do not spawn reviewers; `$review-router` handles review lane selection after aggregation.

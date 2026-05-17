---
name: task-distributor
description: Materialize validated worker or reviewer launch manifests into bounded child-agent waves. Use when the main agent must spawn, wait, classify, and ledger physical specialist lanes without changing router decisions.
---

# Task Distributor

Use this skill after `$worker-router` or `$review-router` returns a schema-valid `launch_manifest`. The main agent owns physical materialization; router skills never spawn or wait.

## Contract Gate

Before running this skill, read the adjacent `contract.json`. Treat `input_artifacts`, `output_artifacts`, `forbidden_outputs`, `required_evidence`, and `source_docs` as the local checklist. Load the listed `${CODEX_HOME}/agent-architecture/<source_doc>` files before emitting the stage artifact. If this skill, its contract, or its source docs change, run `python ${CODEX_HOME}/agent-architecture/validate-skill-contracts.py` before handoff.

## Inputs

Read these before materializing lanes:

- current `launch_manifest`
- `fanout_budget`
- `context_packet_version`
- current `active_passes`
- `${CODEX_HOME}/agent-architecture/03-worker-routing.md`
- `${CODEX_HOME}/agent-architecture/04-aggregation-review.md`
- `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Workflow

1. Confirm every lane has `caller_spawn_required=true` and `initial_status=unmaterialized`.
2. Materialize only the next budget-compliant wave.
3. Call `spawn_agent` only for concrete TOML-backed specialist roles from the manifest.
4. Record `spawn_receipt_ref`, `agent_id`, `submission_id`, and `wait_handle` in `active_passes`.
5. Call `wait_agent` for every materialized child before aggregation or judgment.
6. Classify every lane as returned, superseded, timed out, schema-invalid, blocked, or failed.
7. Return updated `active_passes` and handoff evidence for aggregation.

## Hard Rules

- Do not change router role selection; if selection is invalid, return to the router skill.
- Do not exceed `fanout_budget`.
- Do not use generic `worker` when the manifest names a concrete specialist.
- Do not aggregate unwaited lanes.
- `close_agent` is cleanup only; it is not wait evidence.

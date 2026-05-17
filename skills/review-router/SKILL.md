---
name: review-router
description: Execute the global Codex Review Router stage as a main-agent skill. Use when architecture-required work has a valid aggregation_packet and the main agent must produce a schema-valid review launch_manifest without spawning the review-router as a physical subagent.
---

# Review Router

Use this skill only inside the global architecture loop after `aggregator` emits `aggregation_ready=true` with an `aggregation_packet`. The main agent performs the router stage locally and records it as `stage_execution_mode=main_agent_role_pass`.

## Contract Gate

Before running this skill, read the adjacent `contract.json`. Treat `input_artifacts`, `output_artifacts`, `forbidden_outputs`, `required_evidence`, and `source_docs` as the local checklist. Load the listed `${CODEX_HOME}/agent-architecture/<source_doc>` files before emitting the stage artifact. If this skill, its contract, or its source docs change, run `python ${CODEX_HOME}/agent-architecture/validate-skill-contracts.py` before handoff.

## Inputs

Read these before routing:

- current `aggregation_packet`
- `required_review_axes`, coverage gaps, MCP/tool evidence gaps, and review hints
- `context_packet_version`
- `fanout_budget`
- `${CODEX_HOME}/agent-architecture/04-aggregation-review.md`
- `${CODEX_HOME}/agent-architecture/06-agent-roster-models.md`
- `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`
- runtime agent catalog under `${CODEX_HOME}/agents/<category>/*.toml`

## Specialist List Gate

Before selecting any reviewer lane owner, summon the complete specialist list by enumerating `${CODEX_HOME}/agents/<category>/*.toml`. Then restrict review routing to concrete TOML roles that are allowed for review lanes. Do not route from memory, family aliases, skill names, canonical stage owners, or a partial category view.

## Workflow

1. Confirm the caller is in the Review Router stage and that a valid `aggregation_packet` exists.
2. Build the candidate reviewer list from the enumerated TOML catalog and review-allowed roles.
3. Select the minimum concrete TOML-backed reviewer roles for the required review axes.
4. Preserve explicit review waivers for `meta-judge`; do not silently drop uncovered axes.
5. Enforce `fanout_budget`; coalesce related review axes instead of emitting extra reviewer lanes.
6. Use `spawn_context_mode="scoped_packet"` for review lanes unless a visible `scoped_packet_with_waiver` is required.
7. Write one concrete `validation_prompt` per lane, covering artifacts, risks, MCP evidence, and expected reviewer `handoff_result`.
8. Run `launch_manifest_schema_gate` mentally before returning.
9. Return only the review `launch_manifest` branch or the `schema_invalid` branch required by the global contract.

## Hard Rules

- Do not call `spawn_agent`, `wait_agent`, or `close_agent`; caller materialization owns physical reviewers.
- Do not emit a review `launch_manifest` until the specialist list has been enumerated for this routing pass.
- Do not put `agent_id`, `submission_id`, or `wait_handle` inside `launch_manifest.children[]`.
- Use only review-allowed concrete roles; do not route review work to canonical stage owners.
- Do not ask reviewers to start MCP servers or configure MCP profiles; they may verify MCP evidence inside their own bounded scope only when available.
- Do not emit `context_packet`, `execution_plan`, `aggregation_packet`, or `judgment_envelope`.
- Include `mcp_quiescence_snapshot` and `contract_provenance` exactly as required by the architecture contracts.

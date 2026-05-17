---
name: worker-router
description: Execute the global Codex Worker Router stage as a main-agent skill. Use when architecture-required work has a validated execution_plan and the main agent must produce a schema-valid worker launch_manifest without spawning the worker-router as a physical subagent.
---

# Worker Router

Use this skill only inside the global architecture loop after `task-planner` emits an `execution_plan`. The main agent performs the router stage locally and records it as `stage_execution_mode=main_agent_role_pass`.

## Contract Gate

Before running this skill, read the adjacent `contract.json`. Treat `input_artifacts`, `output_artifacts`, `forbidden_outputs`, `required_evidence`, and `source_docs` as the local checklist. Load the listed `${CODEX_HOME}/agent-architecture/<source_doc>` files before emitting the stage artifact. If this skill, its contract, or its source docs change, run `python ${CODEX_HOME}/agent-architecture/validate-skill-contracts.py` before handoff.

## Inputs

Read these before routing:

- current `execution_plan`
- `context_packet_version`
- `fanout_budget`
- `${CODEX_HOME}/agent-architecture/03-worker-routing.md`
- `${CODEX_HOME}/agent-architecture/06-agent-roster-models.md`
- `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`
- runtime agent catalog under `${CODEX_HOME}/agents/<category>/*.toml`

## Specialist List Gate

Before selecting any lane owner, summon the complete specialist list by enumerating `${CODEX_HOME}/agents/<category>/*.toml`. Treat that list as the only source of spawnable `agent_role` values. Do not route from memory, family aliases, skill names, or a partial category view.

## Workflow

1. Confirm the caller is in the Worker Router stage and that a valid `execution_plan` exists.
2. Build the candidate specialist list from the enumerated TOML catalog.
3. Select the minimum concrete TOML-backed specialist roles for each executable lane.
4. Enforce `fanout_budget`; coalesce related axes rather than emitting extra child lanes.
5. Use `spawn_context_mode="scoped_packet"` for worker lanes unless a visible `scoped_packet_with_waiver` is required.
6. Copy each lane's `validation_prompt`, ownership, merge point, expected artifact, and `context_packet_version`.
7. Run `launch_manifest_schema_gate` mentally before returning.
8. Return only the worker `launch_manifest` branch or the `schema_invalid` branch required by the global contract.

## Hard Rules

- Do not call `spawn_agent`, `wait_agent`, or `close_agent`; caller materialization owns physical children.
- Do not emit a worker `launch_manifest` until the specialist list has been enumerated for this routing pass.
- Do not put `agent_id`, `submission_id`, or `wait_handle` inside `launch_manifest.children[]`.
- Do not use generic `worker` when a concrete specialist role exists.
- Do not use skill names as `agent_role`; select a real TOML role and mention needed skills in `validation_prompt`.
- Do not emit `context_packet`, `execution_plan`, `aggregation_packet`, or `judgment_envelope`.
- Include `mcp_quiescence_snapshot` and `contract_provenance` exactly as required by the architecture contracts.

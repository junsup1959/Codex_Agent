---
name: orchestrator
description: Execute the global Codex Orchestrator stage as a main-agent skill. Use when architecture-required work must be classified, scoped, assigned run identifiers, and converted into a canonical orchestration_request before context-ledger sync.
---

# Orchestrator

Use this skill at the start of architecture-required work or when `$feedbackgate` restarts the loop. The main agent performs this stage locally and records it as `stage_execution_mode=main_agent_role_pass`.

## Contract Gate

Before running this skill, read the adjacent `contract.json`. Treat `input_artifacts`, `output_artifacts`, `forbidden_outputs`, `required_evidence`, and `source_docs` as the local checklist. Load the listed `${CODEX_HOME}/agent-architecture/<source_doc>` files before emitting the stage artifact. Prefer `scripts/check_orchestration_request.py` before handoff. If this skill, its contract, scripts, or source docs change, run `python ${CODEX_HOME}/agent-architecture/validate-skill-contracts.py`.

## Inputs

Read these before emitting an orchestration request:

- user goal and latest user message
- direct-answer exception status
- allowed scope and explicit exclusions
- known constraints, blockers, risk flags, and success criteria
- latest feedback or loop carryover when resuming
- `${CODEX_HOME}/agent-architecture/00-canonical-map.md`
- `${CODEX_HOME}/agent-architecture/01-harness-layer.md`
- `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Workflow

1. Classify the request as direct-answer or `architecture_required=true`.
2. For architecture-required work, assign `run_id`, `loop_id`, `loop_attempt`, and default `fanout_budget`.
3. Use available MCP before substantive work; record successful evidence or `mcp_usage_blocked=true`.
4. Define allowed scope, exclusions, success criteria, risk flags, and feedback re-entry.
5. Preserve `loop_carryover` exactly when feedback restarted the loop.
6. Return exactly one canonical `orchestration_request` branch with `next_owner="context-ledger"`.

## Hard Rules

- Do not emit `context_packet`, `execution_plan`, `launch_manifest`, `aggregation_packet`, or `judgment_envelope`.
- Do not spawn control-stage agents.
- Do not widen feedback scope.
- Do not claim final readiness.
- Include `mcp_quiescence_snapshot` and `contract_provenance` when the surrounding architecture contract requires them.

---
name: task-planner
description: Execute the global Codex Task Planner stage as a main-agent skill. Use when a current MCP-backed context_packet must become a bounded execution_plan before worker specialist materialization.
---

# Task Planner

Use this skill after `$context-ledger` emits a valid `context_packet`. The main agent performs the planner stage locally and records it as `stage_execution_mode=main_agent_role_pass`.

## Contract Gate

Before running this skill, read the adjacent `contract.json`. Treat `input_artifacts`, `output_artifacts`, `forbidden_outputs`, `required_evidence`, and `source_docs` as the local checklist. Load the listed `${CODEX_HOME}/agent-architecture/<source_doc>` files before emitting the stage artifact. Prefer `scripts/check_execution_plan.py` before handoff. If this skill, its contract, scripts, or source docs change, run `python ${CODEX_HOME}/agent-architecture/validate-skill-contracts.py`.

## Inputs

Read these before planning:

- current `context_packet`
- `context_authority_ref`, `context_packet_version`, and `context_revision`
- `role_pass_readiness`
- accepted evidence, constraints, stale markers, and artifact inventory
- `${CODEX_HOME}/agent-architecture/02-context-planning.md`
- `${CODEX_HOME}/agent-architecture/03-worker-routing.md`
- `${CODEX_HOME}/agent-architecture/06-agent-roster-models.md`
- `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Workflow

1. Confirm `role_pass_readiness` allows `task-planner`.
2. Reject stale or missing `context_revision`; request context refresh instead of planning from chat memory.
3. Convert success criteria into bounded executable lanes.
4. Define lane ownership, file scope, merge point, expected artifacts, validation prompt, review hints, and direct blockers.
5. Set `fanout_budget`; coalesce lanes when budget would be exceeded.
6. Return exactly one canonical `execution_plan` branch with `next_owner="worker"`.

## Hard Rules

- Do not select final worker agents from memory; `$worker` must enumerate the concrete TOML specialist list before spawning.
- Do not spawn workers, reviewers, or control-stage agents.
- Do not emit review results, feedback judgments, or final output.
- Do not hide MCP/tool gaps; carry them into lane validation evidence or unresolved assumptions.

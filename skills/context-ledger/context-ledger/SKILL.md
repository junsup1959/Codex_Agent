---
name: context-ledger
description: Execute the mandatory global Codex Context Ledger stage. Use when architecture-required work must sync approved facts, constraints, artifacts, and stale markers through the codex-context-ledger MCP before task planning.
---

# Context Ledger

Use this skill after `$orchestrator` and before `$task-planner`. The main agent performs this stage locally, but the source of truth is the `codex-context-ledger` MCP.

## Contract Gate

Before running this skill, read the adjacent `contract.json`. Treat `input_artifacts`, `output_artifacts`, `forbidden_outputs`, `required_evidence`, and `source_docs` as the local checklist. Load the listed `${CODEX_HOME}/agent-architecture/<source_doc>` files before emitting the stage artifact. Prefer `scripts/check_context_packet.py` before handoff. If this skill, its contract, scripts, or source docs change, run `python ${CODEX_HOME}/agent-architecture/validate-skill-contracts.py`.

## Inputs

Read these before context sync:

- current `orchestration_request`
- latest user goal, allowed scope, constraints, blockers, and feedback carryover
- current `codex-context-ledger` run entry and latest `context_packet`
- `${CODEX_HOME}/agent-architecture/02-context-planning.md`
- `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Workflow

1. Initialize or reopen the run in `codex-context-ledger`.
2. Read the latest `context_packet`; if absent, create the first revision from `orchestration_request`.
3. Update approved facts, constraints, artifact inventory, stale markers, blockers, and readiness.
4. Mark `role_pass_readiness.task-planner=true` only when planning can proceed.
5. Return exactly one `context_packet` branch with `next_owner="task-planner"`.

## Hard Rules

- Do not spawn a `context-manager` physical agent.
- Do not plan lanes, select specialists, aggregate results, review, or judge final output.
- Do not use Docker Memory as the run-local source of truth.
- Do not proceed to `$task-planner` from chat memory when the ledger is unavailable unless an explicit MCP waiver is recorded.

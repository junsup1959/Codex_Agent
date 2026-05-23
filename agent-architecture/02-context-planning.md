# Context And Planning

This document defines `$context-ledger` and `$task-planner`.

## Context Ledger

`context_ledger_mcp_required=true`: `codex-context-ledger` is the run/session context authority.

The ledger owns:

- approved facts
- constraints
- artifact inventory
- stale markers
- blockers
- context revision
- `role_pass_readiness`

It does not plan lanes, route workers, spawn agents, review, or judge final output.

## Barrier Protocol

`context_ledger_barrier_required=true`.

At stage start:

1. `read_context_packet(run_id)`.
2. `validate_context_revision(run_id, consumed_context_revision)`.
3. Check `role_pass_readiness.<stage>=true`.
4. Stop if blockers or stale markers affect the stage input.

At stage handoff:

1. Emit `context_delta`.
2. Emit `new_artifact_refs` and `new_evidence_refs`.
3. Emit `stage_pass_ref`.
4. Call `write_context_packet(expected_revision=consumed_context_revision, packet=...)`.
5. Call `append_stage_pass(...)`.
6. Call `mark_stale(...)` for superseded inputs.

## Task Planner

`$task-planner` converts the current `context_packet` into one bounded `execution_plan`.

The plan must include worker lanes, scope, success criteria, expected artifacts, validation prompts, review hints, fanout budget, and blockers. It does not spawn specialists.

## Required API Checks

Use `validate_stage_packet` for barrier and artifact shape, then `validate_tool_sequence` for the stage MCP call order. Both checks run through the localhost `codex-context-ledger` MCP API.

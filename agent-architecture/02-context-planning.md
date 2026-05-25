# Context And Planning

This document defines `$context-ledger`, `$task-designer`, and `$task-distributor`.

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

It does not design task options, plan lanes, route workers, spawn agents, review, or judge final output.

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

## Task Designer

`$task-designer` converts the current `context_packet` into `task_design.md` and a structured `task_design`.

The design must include:

- problem definition
- assumptions
- at least three options
- comparison criteria
- selected option
- selection rationale
- risks for the selected option
- distribution boundaries for `$task-distributor`
- `artifact_profile` with source stage, reuse policy, and invalidation conditions
- `sequential_thinking_ref` or `sequential_thinking_waiver` proving `MCP_DOCKER.sequentialthinking` was attempted before finalizing the design

It may use `${CODEX_HOME}/agents/<category>/*.toml` as role guidance, but it must not select concrete agents, create worker lanes, allocate fanout, or spawn specialists.

## Task Distributor

`$task-distributor` converts the selected `task_design` into `task_distribution_criteria.md` and one bounded `execution_plan`.

The distribution criteria document must explain lane creation, dependency, fanout, ownership, specialist-category guidance, MCP usage, and handoff evidence rules. The execution plan must reference both the selected task design and the distribution criteria. It must not redefine the selected option, success criteria, or design decisions.

The execution plan must include `artifact_profile` so feedback loops can decide whether it can be reused or must be invalidated.
It must also include `sequential_thinking_ref` or `sequential_thinking_waiver` proving `MCP_DOCKER.sequentialthinking` was attempted before finalizing lane boundaries, dependencies, fanout, ownership, and MCP usage limits.

The distributor may consult the agent roster for category fit, but it does not call agents. `$worker` is responsible for forced specialist worker materialization.

## Required API Checks

Use `validate_stage_packet` for barrier and artifact shape, `validate_task_design` for `$task-designer`, `validate_execution_plan` for `$task-distributor`, then `validate_tool_sequence` for the stage MCP call order. These checks run through the localhost `codex-context-ledger` MCP API.

If a required stage-specific validator is not callable in the active session, the stage is blocked. The agent must not replace the missing validation with an informal draft, option list, recommendation, or "best effort" handoff. For `$task-designer`, missing `validate_task_design` means no `task_design` or 1/2/3 design comparison may be emitted as a completed stage artifact.

`validate_stage_packet` and context packet read/write responses include `next_stage.stage_packet_template` where available. The next stage must follow that top-level wrapper shape before attempting validation; do not discover the schema by repeated failed validation calls.

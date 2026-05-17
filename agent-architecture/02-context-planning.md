# Context And Planning

This document defines the boundary between `context-manager` and `task-planner`.

## Context Manager

`context_ledger_mcp_required=true`: `codex-context-ledger` is the single resident context authority for the run/session. The caller updates the MCP ledger across loops instead of spawning a physical context-manager per loop or closing it as a one-shot stage. Resident context continuity does not excuse missing `context_packet_version`, stale-context marking, MCP cleanup evidence, or validator checks.

## MCP Context Authority

`context_manager_authority_required=true`: after control stages move to `main_agent_role_pass`, `codex-context-ledger` is the authoritative context surface for those role passes. Every main-agent role pass must read the latest `context_packet` before acting and must return new artifact/evidence/blocker refs for a context update after acting.

The MCP context authority owns `context_authority_ref`, `context_packet_version`, `context_revision`, `approved_facts`, constraints, exclusions, accepted evidence, artifact inventory, stale markers, evidence gaps, loop carryover, and `role_pass_readiness`. It does not own worker planning, worker/reviewer routing, aggregation, review judgment, final approval, or user-facing completion claims.

`role_pass_readiness` states whether `task-planner`, `worker-router`, `aggregator`, `review-router`, and `meta-judge` may run from the current packet. If readiness is false, the next main-agent role pass must request a context refresh instead of proceeding from chat memory.

### Owns

- explicit user constraints and allowed scope
- approved repo/interface facts
- reusable evidence from prior worker/reviewer outputs
- MCP context authority and update ledger
- compact `context_packet`
- `context_packet_version`
- `context_revision`
- `role_pass_readiness`
- stale, superseded, missing, or excluded context flags
- heavy artifact inventory and worker-analysis hints

### Does Not Own

- next-owner selection beyond `next_stage_consumer=task-planner`
- worker instance assignment
- broad search execution
- approval, rejection, or final judgment
- final merge of child outputs
- role-pass decisions; it marks readiness and gaps only

### Required Return

- `context_packet`
- `context_packet_version`
- `context_authority_ref`
- `context_revision`
- `role_pass_readiness`
- source `orchestration_request`
- allowed scope
- next-stage consumer
- accepted evidence
- stale or excluded items
- missing-context gaps
- artifact inventory for large/binary/dump/archive/directory inputs
- feedback carryover: `loop_carryover` and `loop_control`
- `contract_provenance`

## Context Gate

- In a non-trivial loop, `context-manager` completes before `task-planner`.
- `context-manager` and `task-planner` are not sibling passes in the same loop.
- If `context_packet_version` is missing or stale, `task-planner` returns `needs_context_manager=true` instead of planning lanes.
- Feedback re-entry must preserve `loop_carryover.preserved_allowed_scope` and blocker/evidence lineage.
- Large raw/binary/dump/archive/directory analysis is worker-stage work; context only inventories and bounds it.
- If context is incomplete, return a compact checkpoint or `missing_context`; do not hide the gap.

## MCP Evidence Boundary

`context-manager` is an MCP-critical main-agent role pass. It records MCP usage evidence, MCP availability checks, and `mcp_usage_blocked=true` reasons inside `accepted_evidence`, `validation_evidence`, `artifact_inventory`, or `evidence_gaps`; it does not depend on implicit chat memory.

`per_agent_mcp_lifecycle_required=true` and `mcp_process_shutdown_required=true` apply here. `context-manager` initializes required MCP inside its own bounded work scope, then closes MCP sessions/processes and records `mcp_quiescence_snapshot` before emitting `context_packet`.

`docker_mcp_sequentialthinking_required=true` for `context-manager`: `context_packet` evidence must identify `MCP_DOCKER/sequentialthinking:success`; `Transport closed` is retry/blocker evidence only.

## Context Manager MCP Gate

`mcp_context_sync_required=true` for architecture-required runs. Before emitting `context_packet`, `context-manager` must use available MCP tools to structure context, verify context/tool availability, or collect supporting context evidence. If MCP is unavailable, irrelevant to the bounded step, blocked, inactive, or error-shaped, record `mcp_usage_blocked=true` with the reason in `evidence_gaps`, `accepted_evidence`, or `validation_evidence`; do not treat the failed call as successful MCP evidence.

`context_packet` handoff is invalid unless `mcp_quiescence_snapshot.open_mcp_process_count=0` and `cleanup_status=clean`.

## Task Planner

`task-planner` defaults to `stage_execution_mode=main_agent_role_pass`. It is usually a main-agent role pass that reads the current MCP-backed `context_packet` and emits `execution_plan`; physical task-planner spawning is reserved for exceptional context size or independence requirements.

### Owns

- worker family candidates
- concrete specialist role candidates
- same-role parallel split rules
- instance count
- fanout budget and overflow policy
- lane ownership
- expected artifact
- expected `handoff_result` fields
- validation evidence per lane
- merge point
- review hint

### Does Not Own

- worker task execution
- physical child materialization
- child waiting
- aggregation
- final approval

### Required Return

- `execution_plan`
- source `context_packet`
- concrete specialist launch map for one `worker-router`
- `fanout_budget`
- same-role parallel split rules when relevant
- per-lane ownership and expected artifact
- expected `handoff_result` fields and validation evidence
- merge points and review hints
- planning risks or unresolved assumptions
- `needs_context_manager=true` when context is missing/stale
- `loop_carryover`, `loop_control`, and `contract_provenance`

## Planning Quality Gate

Every planned lane must answer:

1. What exact scope does this worker own?
2. What artifact must it return?
3. What evidence validates completion?
4. Where will the artifact merge?
5. Which reviewer lens is likely needed?
6. Does it require a separate specialist, or can another lane own it cleanly?

MCP-required context or tool gaps must become lane `validation_evidence`, `review_hint`, or `unresolved_assumptions`; they must not disappear between `context_packet` and `execution_plan`.

Planning must stay within `agent_fanout_budget_required=true`. Default planning limits are `max_worker_lanes_per_wave=2`, `max_review_lanes_per_wave=2`, `max_total_child_agents_per_loop=4`, `max_same_role_parallel_lanes=1`, and `max_mcp_concurrent_child_lanes=1`. If the work appears to need more axes, coalesce related evidence questions into fewer lanes or record overflow as `unresolved_assumptions`; do not plan broad "all specialists" fanout.

## Stage Chain

`context_packet` feeds `execution_plan`; `execution_plan` feeds `worker-router`. `worker-router` receives only planner-owned lane design, not raw unbounded context.

## Architecture Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.

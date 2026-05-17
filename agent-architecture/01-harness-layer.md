# Harness Layer

The harness layer is the caller-owned runtime substrate that makes the orchestration architecture executable, waitable, and auditable. It is not a separate long-lived agent.

## Core Rule

The canonical loop defines topology. The harness layer enforces actual execution: child materialization, schema validation, lineage checks, handoff blocking, pass cleanup, and replayable evidence.

## Enforcement Trigger

Before non-trivial work begins, the caller classifies the request. Explicit architecture/orchestration/harness/agent-structure language or non-trivial audit, implementation, research, comparison, risky, multi-agent, or multi-artifact work sets `architecture_required=true`. When this trigger is set, control stages must be validated artifact passes; main-agent role passes are valid when their `stage_pass` records `stage_execution_mode=main_agent_role_pass`.

## Orchestrator MCP Gate

`mcp_orchestration_required=true` for architecture-required runs. Before emitting `orchestration_request`, `orchestrator` must use available MCP tools to structure the request, verify context/tool availability, or collect supporting orchestration evidence. Record successful MCP usage in `validation_evidence`; record unavailable, irrelevant, blocked, inactive, failed, or error-shaped MCP calls as `mcp_usage_blocked=true` in `validation_evidence`, `constraints`, or `risk_flags`. Failed MCP calls are blocker/waiver evidence only, not successful MCP evidence.

For `docker_mcp_sequentialthinking_required=true`, successful evidence must identify `MCP_DOCKER/sequentialthinking:success`; error-shaped MCP output is blocker evidence only.

## Harness Owner Responsibilities

- Assign `run_id`, `loop_id`, `loop_attempt`, and `context_packet_version` for non-trivial work.
- Record `active_passes`, `stage_passes`, stage artifacts, decisions, validation evidence, and failure classes in a run ledger.
- Keep exactly one MCP-backed context authority for the run/session: `codex-context-ledger`.
- Enforce `context_manager_authority_required=true`: every main-agent role pass reads the latest MCP-backed `context_packet` and records the consumed `context_revision` before producing a canonical artifact.
- Choose `stage_execution_mode=main_agent_role_pass` for `orchestrator`, `task-planner`, `worker-router`, `aggregator`, `review-router`, and `meta-judge` unless independent physical execution is justified.
- Materialize router `launch_manifest.children[]` into real child agents and copy concrete `agent_id`, `submission_id`, `wait_handle_type`, and `wait_handle` into `active_passes`.
- Enforce `per_agent_mcp_lifecycle_required=true`: each agent/stage owner initializes required MCP inside its own bounded work scope.
- Enforce `mcp_process_shutdown_required=true`: every returned stage artifact and `handoff_result` must include `mcp_quiescence_snapshot` proving MCP sessions/processes were closed before handoff.
- Block handoff when `mcp_process_residue_forbidden=true` is violated: missing snapshot, non-zero open MCP process count, or cleanup_status other than `clean`.
- Enforce `agent_fanout_budget_required=true`: reject or classify any execution/review wave that exceeds `fanout_budget` before materializing child agents.
- Run runtime validators before each next-stage handoff.
- Classify missing handles, unmaterialized lanes, schema-invalid outputs, stale context, timeout, and runtime residue before aggregation or final judgment.
- Convert repeated manual repairs into schema, tool, prompt, doc, or eval hardening.

## Mandatory Physical Pass Rule

For non-trivial work, the loop may not claim specialist execution, review execution, or formal gate completion from prose alone. After any `launch_manifest`, progress beyond routing requires either matching `active_passes` with `spawn_tool=spawn_agent`, `spawn_receipt_ref`, `spawned_at`, and `wait_registered_at`, or an explicit missing-lane class. A router success with `next_owner=caller` is only `materialization_pending`, not worker/review execution. Final or feedback claims require resolvable `stage_passes` and reviewer `handoff_result` refs or explicit review waivers.

Required control stages are validated passes, not local procedure labels. `context_ledger_mcp_required=true`: `codex-context-ledger` is the one long-lived context authority for context continuity. `orchestrator`, `context-manager`, `task-planner`, `worker-router`, `aggregator`, `review-router`, and `meta-judge` should normally run as `main_agent_role_pass` stages to avoid unnecessary subagent load. A valid main-agent role pass emits the canonical artifact, records `stage_spawn_contract={spawn_agent_type=main-agent, spawn_fork_context=false, spawn_packet_mode=main_agent_role_pass}`, and passes the same runtime validator before handoff.

`orchestration_stage_skills_required=true`: use `$orchestrator`, `$task-planner`, `$worker-router`, `$task-distributor`, `$result-aggregator`, `$review-router`, and `$feedback-synthesizer` as mandatory procedural adapters for their matching stages. They do not replace validators, stage artifacts, handoff gates, or physical specialist lanes.

Main-agent role passes are invalid if they rely on unstructured chat memory while `context_packet.role_pass_readiness` says the stage is not ready. New artifacts, evidence, blockers, and stale findings must be sent back to `codex-context-ledger` for a packet revision before downstream role passes consume them.

Physical worker specialists and review specialists are the default mechanism for parallel work. `physical_control_override_required=true`: other physical control passes may be used only when independent context isolation or judgment is worth the runtime cost and the stage packet records `stage_execution_mode=physical` plus `physical_override_reason`. If any stage is marked `stage_execution_mode=physical` and cannot be spawned, the run is blocked with `architecture_physical_execution_blocked=true`. Direct specialist/explorer creation before `worker-router` launch-manifest evidence is a contract failure.

## Spawn And Wait Evidence Rule

The caller must not call `spawn_agent` with both `fork_context=true` and an explicit `agent_type`. Full-history forked agents inherit the parent role; dedicated canonical stage owners and specialists must receive curated packets with `fork_context=false`.

Every successful `spawn_agent` materialization creates a wait obligation. The child id must appear in a later `wait_agent.targets[]` entry before its result can feed `aggregation_packet`, `review_input_refs`, or `judgment_envelope`. `close_agent` is cleanup only; a completed close status is not a substitute for wait evidence.

Failed `spawn_agent` calls are physical materialization failures, not advisory warnings. If spawning fails because the agent/thread/concurrency limit was reached, classify the lane or stage as `thread_limit_reached`, close or wait stale children as appropriate, and retry only after capacity is available. Until then, aggregation and final judgment are blocked.

If any spawn failed, any materialized child is unwaited, any tool call is still open, or any child reports `architecture_physical_execution_blocked=true` without a later bounded repair path, the caller must fail closed and route to feedback or user/tool repair instead of continuing as if the layer completed.

## Fanout Budget Gate

`agent_fanout_budget_required=true` prevents one loop from exhausting the runtime. Unless an explicit user-approved override is recorded in the run ledger, the caller enforces `max_worker_lanes_per_wave=2`, `max_review_lanes_per_wave=2`, `max_total_child_agents_per_loop=4`, `max_same_role_parallel_lanes=1`, and `max_mcp_concurrent_child_lanes=1`.

`execution_plan` and `launch_manifest` must carry `fanout_budget`. The caller must run the runtime validator before spawning; if a manifest exceeds the budget, classify the excess as `schema_invalid` or route bounded feedback instead of materializing extra children.

## Stage Transition Gates

| Transition | Required artifact | Harness gate |
| --- | --- | --- |
| `Orchestrator -> Context Manager` | `orchestration_request` | run id, loop id, goal, allowed scope, direct-answer exception, MCP evidence or blocker |
| `Context Manager -> Task Planner` | `context_packet` | `context_packet_version`, accepted evidence, stale-context flags |
| `Task Planner -> Worker Router` | `execution_plan` | ownership, expected artifact, merge point, review hint |
| `Worker Router -> Worker Layer` | `launch_manifest` | caller materialization and wait-handle registration |
| `Worker Layer -> Aggregator` | `handoff_result` | returned lane or explicit missing-lane classification |
| `Aggregator -> Review Router` | `aggregation_packet` | contradiction, evidence gap, provenance, coverage axes |
| `Aggregator -> Meta Judge` | blocked aggregation branch | `aggregation_ready=false`; feedback `judgment_envelope` before restart |
| `Review Router -> Review Layer` | `launch_manifest` | reviewer materialization and wait-handle registration |
| `Review Layer -> Meta Judge` | reviewer `handoff_result` | reviewer gap, dissent, missing review classification |
| `Meta Judge -> Feedback Trigger Gate` | `judgment_envelope` | `feedback_required`, `final_blocked_reason`, residual risk |
| `Feedback Trigger Gate -> Orchestrator/User` | `judgment_envelope` | feedback restart or final output approval |

## Failure Classes

- `schema_invalid`: required fields or artifact shape do not match contract.
- `input_invalid`: JSON or CLI input cannot be parsed.
- `io_error`: a required read/write path failed.
- `validator_bug`: validator implementation failed unexpectedly.
- `contract_invalid`: stage ownership, next owner, or handoff contract is invalid.
- `loop_invalid`: feedback lineage, carryover, or loop-control contract is invalid.
- `no_wait_handle`: physical child lacks a concrete wait handle.
- `unmaterialized_lane`: logical lane exists but caller did not create a child.
- `spawn_failed`: `spawn_agent` returned an error or no child id, so the lane or stage was not materialized.
- `thread_limit_reached`: `spawn_agent` failed because the active agent/thread/concurrency limit was reached.
- `timed_out`: child or stage pass exceeded its checkpoint.
- `superseded`: output was replaced by a newer pass or context version.
- `runtime_residue`: returned stage still appears `running` or `pending_init`.
- `stale_context`: output references a stale `context_packet_version`.
- `evidence_gap`: final/review judgment lacks required evidence.

## Runtime Contract Enforcement

- The caller runs `${CODEX_HOME}/agent-architecture/validate-runtime-artifact.py` on actual stage JSON before handoff.
- The caller may run `${CODEX_HOME}/agent-architecture/validate-session-runtime.py` on Codex session JSONL when a completed thread claims it physically followed the architecture.
- The caller runs `${CODEX_HOME}/agent-architecture/harness_gate.py` to convert validation into allow/block routing.
- The caller uses `${CODEX_HOME}/agent-architecture/harness_handoff.py` as the wired handoff entrypoint for non-trivial stage transitions.
- Handoff decisions carry `runtime_validation_required=true`, `allow_next_stage`, `route_kind=proceed|retry_same_stage|feedback_restart`, `expected_next_owner`, optional `expected_source_ref`, and optional `expected_context_packet_version`.
- Router-to-layer handoff requires materialized `active_passes` before `next_owner=worker-layer` or `next_owner=review-layer`.
- Aggregator and meta-judge handoff require all materialized children to be waited, returned, timed out, superseded, schema-invalid, or explicitly classified; closed-only children remain invalid evidence.
- Feedback lineage checks may pass a prior `judgment_envelope` through `--previous-judgment-json` to prevent scope widening, blocker loss, or no-progress looping.
- Non-zero validator or handoff exit code blocks the next stage; stdout is machine-readable, not advisory prose.

## Lifecycle Notes

- Routers return logical manifests and close immediately.
- Aggregator is not a live child watcher; it consumes returned or explicitly classified lane outcomes.
- `meta-judge` cannot approve final output until schema, missing-lane, feedback, and coverage gates are classified.
- Stage passes close after artifact return; only caller-materialized specialists/reviewers stay active while work is pending.

## Architecture Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.

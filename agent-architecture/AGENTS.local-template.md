# AGENTS.md

## Global Architecture Inheritance

This project inherits the global Codex architecture by reference:

- `${CODEX_HOME}/AGENTS.md`
- `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md`
- `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE-MAPPER.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

Do not copy the global architecture body into this project file. Keep project-specific rules below.

Architecture trigger: explicit mentions of architecture/orchestration/harness/agent structure, or any non-trivial audit/implementation/research/comparison/risky/multi-artifact request, set `architecture_required=true` before work begins.

For architecture-required work, `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md` is the procedural sequence. Do not skip or reorder it unless a direct-answer exception or valid feedback judgment blocks the loop.

`context_ledger_mcp_required=true`: use the `codex-context-ledger` MCP as the resident context authority for the run/session. Do not spawn `context-manager` as a physical resident agent; context state must be read from and written to the MCP ledger.

`context_manager_authority_required=true`: every main-agent role pass must read the latest MCP-backed `context_packet` before acting and must return new evidence/artifact refs for context update. The context ledger owns approved facts, constraints, artifact inventory, stale markers, context revision, and role-pass readiness; it does not plan lanes, route workers, aggregate, review, or judge final output.

`orchestration_stage_skills_required=true`: architecture-required control flow must activate and follow `$orchestrator`, `$task-planner`, `$worker-router`, `$task-distributor`, `$result-aggregator`, `$review-router`, and `$feedback-synthesizer` at their matching stages. These skills are procedural adapters, not spawnable agent roles. `$docker-memory` is optional helper guidance for Docker MCP Memory and is not a mandatory architecture gate.

Do not silently simulate architecture stages. `orchestrator`, `task-planner`, `worker-router`, `aggregator`, `review-router`, and `meta-judge` default to `stage_execution_mode=main_agent_role_pass`. Physical parallelism is reserved for worker specialists and review specialists selected from validated manifests. Inline/main-agent role passes must still emit canonical artifacts, record a `stage_pass`, and pass runtime validators before handoff. If a stage is marked `stage_execution_mode=physical` but cannot be spawned, state `architecture_physical_execution_blocked=true` instead of claiming that physical stage ran.

`physical_control_override_required=true`: spawning `task-planner`, `worker-router`, `aggregator`, `review-router`, or `meta-judge` as physical subagents is forbidden unless the stage packet records both `stage_execution_mode=physical` and `physical_override_reason`. Repeated physical control-stage spawning is architecture drift, not diligence.

Do not call `spawn_agent` with both `fork_context=true` and an explicit `agent_type`; full-history forked agents inherit the parent type. Dedicated stage owners must receive a curated stage packet with `fork_context=false`, or fork without `agent_type` only when preserving the parent role is intended.

A failed `spawn_agent` call is a physical materialization failure. If the failure is caused by thread/concurrency limits, classify it as `thread_limit_reached`, fail closed, and do not aggregate or judge that lane until it is retried after cleanup or explicitly classified.

Every successfully materialized child must be targeted by `wait_agent` before its result can be aggregated or judged. `close_agent` is cleanup only and is not wait evidence.

`agent_fanout_budget_required=true` for architecture-required runs. Default physical fanout is conservative: at most 2 worker lanes per execution wave, at most 2 reviewer lanes per review wave, at most 4 total child agents per loop, at most 1 same-role parallel lane, and at most 1 MCP-using child lane active at a time. "Use all specialists" means evaluate the specialist catalog for coverage and select the minimum bounded set; it does not mean spawning every relevant specialist.

`feedback_gate_mandatory=true` for architecture-required runs. Final/ready/approve/completion claims require current `meta_judge_stage_pass_ref`, reviewer `review_input_refs` or explicit `review_waivers`, and non-empty `feedback_gate_evidence`; otherwise fail closed and route through bounded feedback.

`mcp_required=true` for architecture-required runs. Use available MCP tools before substantive architecture, orchestration, audit, research, implementation, or final-judgment work; if MCP is unavailable, blocked, irrelevant, or returns an error/path/inactive-server failure, state `mcp_usage_blocked=true` or record an explicit MCP waiver. `per_agent_mcp_lifecycle_required=true`: each agent/stage owner initializes required MCP inside its own bounded work scope. `mcp_process_shutdown_required=true`: before any stage artifact, `handoff_result`, review result, feedback judgment, or final claim is handed off, the agent must close MCP sessions/processes and attach `mcp_quiescence_snapshot={open_mcp_process_count, open_mcp_process_ids, cleanup_status, snapshot_at}`. `mcp_process_residue_forbidden=true`: `open_mcp_process_count` must be `0`, or handoff/final approval is blocked. `docker_mcp_sequentialthinking_required=true` for `orchestrator`, `context-manager`, `aggregator`, `review-router`, reviewer lanes, and `meta-judge`; evidence must identify `MCP_DOCKER/sequentialthinking:success`, not standalone `sequentialthinking` or `Transport closed`. MCP usage is prompt-level policy only except for the dedicated `codex-context-ledger` context authority; it does not replace `meta-judge`, validators, reviewer evidence, or feedback gate evidence.

## Project Scope

- Describe this repository's purpose here.
- Add only project-local constraints here.
- If a project rule conflicts with the global architecture, this file may narrow scope more strictly but should not weaken safety, validation, or handoff contracts.

## Build, Test, And Validation

- Add project-specific commands here.

## Notes For Agents

- Keep this file concise.
- Link to detailed project docs instead of duplicating long content.

## Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true` and run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.

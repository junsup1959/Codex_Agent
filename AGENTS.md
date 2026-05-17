# Global Codex Architecture Pointer

This file is a compact pointer with mandatory global guardrails. Detailed operational contracts live in the referenced architecture docs.

## Read First

- Architecture source: `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md`
- Architecture mapper: `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE-MAPPER.md`
- Runtime sequence: `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Application Rule

- When creating or refreshing a repo-local `AGENTS.md` through `/init`, start from `${CODEX_HOME}/agent-architecture/AGENTS.local-template.md` so the global architecture is inherited by reference.
- A repo-local `AGENTS.md` may narrow scope more strictly.
- Simple direct-answer tasks may proceed directly.
- Non-trivial audit, implementation, research, comparison, risky, multi-agent, or multi-artifact work must follow the referenced architecture docs.
- Architecture trigger: explicit mentions of architecture/orchestration/harness/agent structure, or any non-trivial audit/implementation/research/comparison/risky/multi-artifact request, set `architecture_required=true` before work begins.
- For architecture-required work, `09-runtime-orchestration-steps.md` is the procedural sequence. Do not skip or reorder it unless a direct-answer exception or valid feedback judgment blocks the loop.
- `context_ledger_mcp_required=true`: use the `codex-context-ledger` MCP as the resident context authority for the run/session. Do not spawn `context-manager` as a physical resident agent; context state must be read from and written to the MCP ledger.
- `context_manager_authority_required=true`: every main-agent role pass must read the latest MCP-backed `context_packet` before acting and must return new evidence/artifact refs for context update. The context ledger owns approved facts, constraints, artifact inventory, stale markers, context revision, and role-pass readiness; it does not plan lanes, route workers, aggregate, review, or judge final output.
- `orchestration_stage_skills_required=true`: architecture-required control flow must activate and follow `$orchestrator`, `$task-planner`, `$worker-router`, `$task-distributor`, `$result-aggregator`, `$review-router`, and `$feedback-synthesizer` at their matching stages. These skills are procedural adapters, not spawnable agent roles.
- `$docker-memory` is optional helper guidance for Docker MCP Memory. Do not treat it as a mandatory architecture gate.
- Do not silently simulate architecture stages. `orchestrator`, `task-planner`, `worker-router`, `aggregator`, `review-router`, and `meta-judge` default to `stage_execution_mode=main_agent_role_pass`. These stages are main-agent role passes, not physical subagents, unless a run explicitly records a physical override.
- `physical_control_override_required=true`: spawning `task-planner`, `worker-router`, `aggregator`, `review-router`, or `meta-judge` as physical subagents is forbidden unless the stage packet records both `stage_execution_mode=physical` and `physical_override_reason`. Repeated physical control-stage spawning is architecture drift, not diligence.
- Physical parallelism is reserved for worker specialists and review specialists selected from validated manifests. Inline/main-agent role passes must still emit canonical artifacts, record a `stage_pass`, and pass runtime validators before handoff.
- If a stage is marked `stage_execution_mode=physical` but cannot be spawned, state `architecture_physical_execution_blocked=true` instead of claiming that physical stage ran.
- Do not call `spawn_agent` with both `fork_context=true` and an explicit `agent_type`; full-history forked agents inherit the parent type. Dedicated stage owners must receive a curated stage packet with `fork_context=false`, or fork without `agent_type` only when preserving the parent role is intended.
- A failed `spawn_agent` call is a physical materialization failure. If the failure is caused by thread/concurrency limits, classify it as `thread_limit_reached`, fail closed, and do not aggregate or judge that lane until it is retried after cleanup or explicitly classified.
- Every successfully materialized child must be targeted by `wait_agent` before its result can be aggregated or judged. `close_agent` is cleanup only and is not wait evidence.
- `agent_fanout_budget_required=true` for every architecture-required run. Default physical fanout is conservative: at most 2 worker lanes per execution wave, at most 2 reviewer lanes per review wave, at most 4 total child agents per loop, at most 1 same-role parallel lane, and at most 1 MCP-using child lane active at a time.
- "Use all specialists" means evaluate the specialist catalog for coverage and select the minimum bounded set. It does not mean spawning every relevant specialist. If required axes exceed the budget, coalesce axes into fewer lanes or return feedback/user/tool repair instead of over-spawning.

## Mandatory Feedback Gate

- `feedback_gate_mandatory=true` for every architecture-required run.
- Before any final, ready, approve, safe-to-proceed, merge-ready, or completion claim, a current `meta-judge` `judgment_envelope` must include `meta_judge_stage_pass_ref`, reviewer `review_input_refs` or explicit `review_waivers`, and non-empty `feedback_gate_evidence`.
- If `feedback_required=true`, gate evidence is missing or stale, reviewer evidence is missing, or any required runtime layer is unmaterialized, timed out, schema-invalid, superseded, conflicting, or unclassified, final output is forbidden.
- The default behavior is fail-closed: report the missing validation and route through bounded feedback instead of claiming completion.
- Previous successful gate evidence cannot approve later changed artifacts, prompts, validators, or runtime handoff contracts.

## Mandatory MCP Usage

- `mcp_required=true` for every architecture-required run.
- Before substantive architecture, orchestration, audit, research, implementation, or final-judgment work begins, use available MCP tools to structure reasoning, verify tool availability, or collect supporting context.
- If MCP tools are unavailable, blocked, or irrelevant to the specific step, state `mcp_usage_blocked=true` with the reason.
- MCP calls that return errors, path failures, inactive-server failures, or unavailable-tool failures are blocker/waiver evidence, not successful MCP usage evidence.
- Do not claim the architecture was fully followed unless MCP usage evidence is present or an explicit MCP waiver is recorded.
- `per_agent_mcp_lifecycle_required=true`: each agent/stage owner initializes any required MCP server/session inside its own bounded work scope; MCP state must not be inherited as a hidden long-lived dependency.
- `mcp_process_shutdown_required=true`: before any stage artifact, `handoff_result`, review result, feedback judgment, or final claim is handed off, the agent must close its MCP sessions/processes and attach `mcp_quiescence_snapshot={open_mcp_process_count, open_mcp_process_ids, cleanup_status, snapshot_at}`.
- `mcp_process_residue_forbidden=true`: `mcp_quiescence_snapshot.open_mcp_process_count` must be `0`; non-zero MCP residue, missing snapshot, or cleanup_status other than `clean` blocks handoff/final approval.
- `docker_mcp_sequentialthinking_required=true` for `orchestrator`, `context-manager`, `aggregator`, `review-router`, reviewer lanes, and `meta-judge`. Evidence must identify `MCP_DOCKER/sequentialthinking:success`; standalone `sequentialthinking` MCP evidence, `Transport closed`, or error-shaped MCP output is not sufficient.
- MCP usage is prompt-level policy only except for the dedicated `codex-context-ledger` context authority. It does not replace `meta-judge`, validator checks, reviewer evidence, or feedback gate evidence.

## Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true` and run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.

# Canonical Map

이 파일은 전역 agent architecture 의 최상위 지도다. 세부 계약은 sibling 문서로 분리한다.

## Canonical Loop

`Orchestrator <-> Context Manager -> Task Planner -> Worker Router -> Specialist Worker Layer -> Aggregator -> Review Router -> Specialist Review Layer -> Meta Judge -> Feedback Trigger Gate -> Feedback to Orchestrator then Context Manager restart or Final Output`

## Source Hierarchy

| Layer | File | Purpose |
| --- | --- | --- |
| Compact runtime map | `${CODEX_HOME}/AGENTS.md` | 모든 작업에 주입되는 짧은 목차와 필수 규칙 |
| Architecture index | `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md` | 상세 문서 위치와 읽기 순서 |
| Stage details | `${CODEX_HOME}/agent-architecture/*.md` | 단계별 lifecycle, artifact, guardrail |
| Runtime prompts | `${CODEX_HOME}/agents/<category>/*.toml` | 실제 subagent role 지침, recursive category catalog |
| Personal record | Obsidian `오케스트레이션_하네스 엔지니어링` | 개인 기록용이며 source of truth 또는 validation/test 대상이 아님 |

## Plane Model

| Plane | Owners | Responsibility |
| --- | --- | --- |
| Control plane | `orchestrator`, `context-manager`, `task-planner`, routers, `aggregator`, `meta-judge` | stage order, routing, packetization, judgment |
| Execution plane | caller-materialized workers and support specialists | bounded artifact production |
| Review plane | caller-materialized reviewers and review support specialists | validation and risk review |
| Harness plane | top-level caller / `orchestrator` | run ledger, schema gates, physical materialization, waits, cleanup, replay/eval |

## Fork Context Policy

Default spawn context policy:

| Stage family | `fork_context` default | Reason |
| --- | --- | --- |
| control/router stages | `false` with explicit `agent_type`; `true` only when omitting `agent_type` | the current runtime rejects `fork_context=true` combined with an explicit stage owner role |
| aggregator / collector stages | `false` with explicit `agent_type`; `true` only when omitting `agent_type` | collection needs rich context, but dedicated role identity requires a curated stage packet |
| worker specialists | `false` | execution should be scoped to one typed work order and bounded evidence packet |
| reviewer specialists | `false` | review independence is stronger with a curated evidence packet than full producer context |
| feedback gate / meta-judge input | `false` with explicit `meta-judge` role; `true` only when omitting `agent_type` | gate decisions must be evidence-bound and not rely on unstructured conversation memory |

`spawn_agent` must not be called with both `fork_context=true` and an explicit `agent_type`; full-history forked agents inherit the parent agent type, model, and reasoning effort. Dedicated stage owners therefore receive a curated stage packet with `fork_context=false`. If preserving full parent history is more important than role identity, omit `agent_type` and record that the pass is not a dedicated canonical stage owner.

When a curated packet is used for a control, router, aggregator, or meta-judge stage, the packet must include user goal, allowed scope, constraints, prior decisions, loop ids, `context_packet_version`, active blockers, and relevant artifact refs so the stage does not depend on hidden conversation memory.

## Control Stage Execution Policy

Canonical control stages are artifact-required, not always subagent-required. `context_ledger_mcp_required=true`: keep exactly one resident MCP context authority, `codex-context-ledger`, for the run/session so context continuity is not rebuilt every loop.

`orchestrator`, `task-planner`, `worker-router`, `aggregator`, `review-router`, and `meta-judge` default to `stage_execution_mode=main_agent_role_pass`. They run as explicit role passes by the main agent and must still produce the same canonical artifact, run the same runtime validator, and record a `stage_pass` with `stage_spawn_contract={spawn_agent_type=main-agent, spawn_fork_context=false, spawn_packet_mode=main_agent_role_pass}`.

`orchestration_stage_skills_required=true`: the main agent must activate `$orchestrator`, `$task-planner`, `$worker-router`, `$task-distributor`, `$result-aggregator`, `$review-router`, and `$feedback-synthesizer` at their matching stages. `$docker-memory` remains optional helper guidance only.

Physical parallelism is reserved for worker specialists and review specialists selected from validated manifests. `physical_control_override_required=true`: physical control stages remain allowed only when independence, context size, or risk justifies the cost; those stage passes must record `stage_execution_mode=physical`, `physical_override_reason`, and normal spawn/wait evidence.

`context_manager_authority_required=true`: main-agent role passes must use `codex-context-ledger` as the shared memory boundary. They read `context_packet.context_revision`, `context_authority_ref`, and `role_pass_readiness` before acting, then return artifact/evidence/blocker refs so the MCP ledger can update the next packet.

## MCP Usage Policy

For every architecture-required run, set `mcp_required=true`.

MCP usage is a prompt-level operating requirement, not a validator-level runtime gate unless a future architecture change explicitly promotes it. Before substantive architecture, orchestration, audit, research, implementation, or final-judgment work begins, the caller should use available MCP tools to structure reasoning, verify tool availability, or collect supporting context.

If MCP tools are unavailable, blocked, or irrelevant to the specific step, the caller must state `mcp_usage_blocked=true` with the reason. The caller must not claim the architecture was fully followed unless MCP usage evidence is present or an explicit MCP waiver is recorded.

MCP calls that return errors, path failures, inactive-server failures, unavailable-tool failures, or empty unusable results count as blocker/waiver evidence only. They must not be counted as successful MCP usage evidence.

MCP-critical stages are `orchestrator`, `context-manager`, `task-planner`, `aggregator`, `review-router`, reviewer lanes, and `meta-judge`. These stages must preserve MCP usage evidence, MCP gaps, and MCP waivers in their existing evidence fields instead of relying on unstructured conversation memory.

`docker_mcp_sequentialthinking_required=true` for `orchestrator`, `context-manager`, `aggregator`, `review-router`, reviewer lanes, and `meta-judge`. Each owning agent must execute or provide successful evidence from `MCP_DOCKER/sequentialthinking:success`; standalone `sequentialthinking` MCP evidence and error-shaped output such as `Transport closed` do not satisfy this requirement.

## MCP Broker Rule

`per_agent_mcp_lifecycle_required=true`: every agent/stage owner initializes any required MCP server/session inside its own bounded work scope. MCP state must not be inherited as a hidden long-lived dependency.

`mcp_process_shutdown_required=true`: before any stage artifact, `handoff_result`, review result, feedback judgment, or final claim is handed off, the agent closes MCP sessions/processes and records `mcp_quiescence_snapshot={open_mcp_process_count, open_mcp_process_ids, cleanup_status, snapshot_at}`.

`mcp_process_residue_forbidden=true`: `mcp_quiescence_snapshot.open_mcp_process_count` must be `0`; non-zero MCP residue, a missing snapshot, or `cleanup_status!="clean"` blocks handoff/final approval.

MCP usage does not replace physical architecture stages, `meta-judge`, validator checks, reviewer evidence, or feedback gate evidence.

## Fanout Budget Policy

`agent_fanout_budget_required=true` for every architecture-required run. The default budget is:

- `max_worker_lanes_per_wave=2`
- `max_review_lanes_per_wave=2`
- `max_total_child_agents_per_loop=4`
- `max_same_role_parallel_lanes=1`
- `max_mcp_concurrent_child_lanes=1`

"Use all specialists" means evaluate the specialist catalog for dependency coverage, then select the minimum bounded set that satisfies the current evidence gap. It does not mean spawning every matching role. If required axes exceed the budget, the planner/router must coalesce related axes into one owned lane, preserve overflow as `unresolved_assumptions` or review waivers, or route to feedback/user/tool repair.

Worker and reviewer child waves default to sequential or low-concurrency materialization when MCP is required. The caller must not materialize more children than the current `fanout_budget` allows, even if `launch_manifest.children[]` contains additional proposed lanes.

## Stage Owners

| Stage | Dedicated owner | Detail file |
| --- | --- | --- |
| Canonical map / model tiers | all callers | `00-canonical-map.md` |
| Harness runtime | caller / `orchestrator` | `01-harness-layer.md` |
| Context sync and planning | `context-manager`, `task-planner` | `02-context-planning.md` |
| Worker routing and execution | `worker-router`, worker specialists | `03-worker-routing.md` |
| Aggregation and review | `aggregator`, `review-router`, reviewers | `04-aggregation-review.md` |
| Feedback and lifecycle cleanup | `meta-judge`, `orchestrator`, caller | `05-feedback-lifecycle.md` |
| Agent roster and model tiers | all callers | `06-agent-roster-models.md` |
| Shared contracts and ledgers | all callers | `07-contracts-ledgers.md` |
| Harness quality and evals | harness owner, `meta-judge`, reviewers | `08-quality-evals.md` |
| Runtime orchestration sequence | all callers | `09-runtime-orchestration-steps.md` |

## Non-Trivial Work Default

Architecture trigger: set `architecture_required=true` before work begins when the user explicitly mentions architecture, orchestration, harness, agent structure, feedback gate, specialist routing, or when the request is non-trivial audit, implementation, research, comparison, risky, multi-agent, or multi-artifact work. The trigger fires even if the user does not explicitly say "use agents".

Validated stage execution is mandatory when the architecture is invoked. The caller must not replace `context-manager`, `task-planner`, `worker-router`, `aggregator`, `review-router`, or `meta-judge` with prose-only simulation. Main-agent role passes are valid only when they emit canonical artifacts, record `stage_execution_mode=main_agent_role_pass`, and pass validators. If a stage is explicitly marked physical and cannot be spawned, emit `architecture_physical_execution_blocked=true` and do not claim that physical stage ran.

The procedural order is defined in `09-runtime-orchestration-steps.md`. Detail files define the contracts for each artifact; the runtime sequence defines the order, status/resume/archive behavior, and transition gates.

1. Start from `orchestrator` perspective and form an `orchestration_request`.
2. Run the `context-manager` role pass locally and persist/read context through `codex-context-ledger`.
3. Plan from a valid `context_packet_version`.
4. Use exactly one `worker-router` per execution wave.
5. Caller materializes specialist children and registers concrete wait handles.
6. Aggregate only returned or explicitly classified lanes.
7. Use exactly one `review-router` per review wave.
8. `meta-judge` runs the `Feedback Trigger Gate`; if `feedback_required=true`, final output is forbidden and `final_blocked_reason` is recorded.
9. Feedback always returns to `orchestrator`; `next_loop_start=context-manager` restarts with a new MCP-backed context packet.
10. Repeated failure patterns become harness/tooling/eval improvements, not prompt-only retries.

Direct specialist/explorer spawning before `worker-router` is invalid for architecture-claimed non-trivial work. Specialists are materialized only from a valid `launch_manifest`.

## Direct Answer Exception

Simple direct-answer tasks may skip the full loop. Complex audit, implementation, research, comparison, risky, or multi-artifact work must follow the mapped architecture.
## Architecture Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.






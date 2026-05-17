# Worker Routing And Execution

이 문서는 `worker-router`와 Specialist Worker Layer 의 계약을 정의한다.

## Single Router Rule

One execution wave owns exactly one `worker-router` pass. Concurrency scales through caller-materialized specialist children, not by stacking router agents.

## Worker Router Lifecycle

1. Read execution plan, `context_packet_version`, ownership map, and wave boundary.
2. For main-agent execution, activate `$worker-router`; the skill is procedural guidance, not a spawnable `agent_role`.
3. Summon the full specialist list by enumerating `${CODEX_HOME}/agents/<category>/*.toml`; route only to concrete roles found in that list.
4. Read and preserve `fanout_budget`; do not exceed it.
5. Choose the minimum concrete specialists for bounded execution scopes.
6. Produce logical child lanes, including same-role parallel lanes only when the budget allows.
7. Set `caller_spawn_required=true` and `initial_status=unmaterialized`; concrete wait handles stay only in `active_passes`.
8. Run `launch_manifest_schema_gate`; return only schema-valid `launch_manifest`.
9. Close the inline or physical router stage immediately after handoff.

## Fork Context Rule

`worker-router` is a control/router stage and defaults to `stage_execution_mode=main_agent_role_pass`. Main-agent role execution uses `$worker-router` as the procedural skill because routing is a bounded schema transformation and does not need a physical subagent. If a physical dedicated stage-owner spawn is explicitly chosen, use `fork_context=false` with a curated stage packet; use `fork_context=true` only when omitting `agent_type`, and do not claim that pass is the dedicated worker-router unless the runtime role is actually `worker-router`.

Worker specialists default to `fork_context=false`. They receive only the typed logical lane, execution-plan slice, context packet reference, owned scope, allowed tools, validation prompt, and expected artifact. If extra background is required, the router adds it to the lane packet instead of relying on full conversation memory.

## MCP Tool Request Boundary

`per_agent_mcp_lifecycle_required=true` and `mcp_process_shutdown_required=true` for worker-router and worker specialists. Worker lanes may require MCP evidence; the owning worker initializes MCP inside its own bounded work scope, uses it, then closes MCP sessions/processes before returning `handoff_result`. Worker-router and worker returns are invalid unless `mcp_quiescence_snapshot.open_mcp_process_count=0` and `cleanup_status=clean`.

## Worker Router Must Not

- stay alive as watcher
- privately spawn children and pretend caller can wait on them
- leave MCP server/session processes running after returning
- create another default router under itself
- prepare aggregator schema while children run
- normalize child output
- bypass `aggregator`

## Category Router Layer

The `worker-router` uses the category catalog at `${CODEX_HOME}/agents/<category>/*.toml` instead of a flat role pool.

Routing order:

1. classify task family and risk axis
2. choose one or more categories
3. choose concrete agent TOML files inside each category
4. emit `launch_manifest.children[].lane_id`, `agent_category`, and `agent_role`
5. close the router pass after handoff

Category routing is a dispatch contract. It must not become a persistent watcher or spawn hidden children. Logical lanes are not waitable until the caller records physical handles in `active_passes`.

## Fanout Budget

`agent_fanout_budget_required=true` applies before any worker child is materialized. Default worker routing limits are:

- `max_worker_lanes_per_wave=2`
- `max_total_child_agents_per_loop=4`
- `max_same_role_parallel_lanes=1`
- `max_mcp_concurrent_child_lanes=1`

The router must copy `fanout_budget` from `execution_plan` into `launch_manifest`. If `execution_plan.lanes[]` exceeds the budget, the router returns `schema_invalid` or a bounded overflow classification instead of expanding the manifest.

"Use all specialists" is a catalog coverage check, not a physical spawn instruction. The router evaluates candidate specialists and emits only the smallest role set that covers the lane evidence gap. Related validation axes should be coalesced into one lane when separate child agents would exceed the budget.

The specialist list must be enumerated fresh for every worker routing pass. A worker `launch_manifest` emitted from memory, aliases, skill names, or a partial specialist list is invalid.

## Launch Manifest Schema Gate

Before any router or review-router returns `launch_manifest`, it must validate every `launch_manifest.children[]` lane against `07-contracts-ledgers.md`. Logical lanes must include required fields, must not contain `agent_id`, `submission_id`, or `wait_handle`, and must default router-created lanes to `caller_spawn_required=true` and `initial_status=unmaterialized`. Invalid manifests are returned as `schema_invalid` and cannot be materialized.

Logical worker lanes must carry `spawn_context_mode=scoped_packet` unless the caller records an explicit waiver. A waiver must name the reason, risk, and reviewer/gate evidence that will re-check the wider context use.

## Specialist Families

| Family | Candidate specialists | Intended use |
| --- | --- | --- |
| analysis | `analysis-specialist`, `debugger`, `error-detective`, `performance-monitor`, `data-researcher`, `search-specialist` | root-cause isolation, anomaly slicing, metric interpretation, evidence expansion |
| engineering | `engineering-specialist`, `python-pro`, `build-engineer`, `test-automator`, `refactoring-specialist`, `documentation-engineer`, `analysis-specialist` | bounded implementation, build/test repair, structural cleanup, implementation notes |
| search | `search-specialist`, `docs-researcher`, `research-analyst`, `competitive-analyst`, `data-researcher` | source expansion, official-doc validation, option comparison, evidence shaping |

## Specialist Coverage Contract

The router must map every executable capability axis in `execution_plan.lanes[]` to concrete specialist roles from the category catalog. It must not use generic `worker` when a more specific specialist exists. The launch manifest evidence is sufficient only when each lane records a concrete `agent_category`, concrete `agent_role`, scoped `validation_prompt`, and distinct merge point.

Specialist coverage means all required capability axes are covered by selected lanes; it does not mean spawning every available specialist role.

Skill names are not spawnable `agent_role` values. If a lane needs a skill such as `reverse-engineering-expert`, attach it as a required skill/reference inside `validation_prompt` while selecting a real TOML-backed specialist role such as `debugger`, `search-specialist`, `cpp-pro`, or another catalog role.

## Same-Role Parallelism

Same specialist role can run multiple concurrent instances when these are distinct:

- `ownership`
- `expected_artifact`
- `merge_point`
- `context_packet_version`
- validation evidence

Examples:

- `debugger A`, `debugger B`, `error-detective C`
- `python-pro A`, `python-pro B`, `test-automator C`
- `docs-researcher A`, `docs-researcher B`, `competitive-analyst C`

## Specialist Worker Layer

`Worker` is a layer name, not a required generic agent role. The `worker-router` must select concrete specialist roles from the category catalog for every executable lane. A generic worker lane is valid only when no more specific specialist exists and the owned scope explains why.

| Contract | Rule |
| --- | --- |
| Owner | caller-materialized specialist worker |
| Required input artifact | one logical lane, `execution_plan` slice, `context_packet_version`, owned scope |
| Required output artifact | `handoff_result` with `artifact_ref`, `artifact_kind`, evidence, confidence, merge point |
| Terminal states | `returned`, `timed_out`, `superseded`, `schema_invalid` |
| Next handoff | `aggregator`; worker must not return to router as continuing owner |

## Caller Materialization

After router returns:

1. Caller reads `launch_manifest.children[]`.
2. The caller materializes physical child agents from logical category lanes; caller materializes only after valid logical routing.
3. Caller records `agent_id`, `submission_id`, `wait_handle`, `spawn_receipt_ref`, `spawned_at`, and `wait_registered_at` in `active_passes`.
4. Until all lanes are materialized, the state is `materialization_pending`; router closure is not worker execution.
5. Caller waits for every materialized child with `wait_agent`; `close_agent` cleanup is not wait evidence.
6. Aggregation may start only after every lane is returned or explicitly classified.
6. Missing lanes are classified before aggregation.

## Worker Return

Worker and support specialists return directly to `aggregator` through `handoff_result`; they do not return to the router as a continuing owner.
## Architecture Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.






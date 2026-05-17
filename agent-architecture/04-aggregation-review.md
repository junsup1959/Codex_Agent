# Aggregation And Review

이 문서는 `aggregator`, `review-router`, Specialist Review Layer 의 계약을 정의한다.

## Aggregator

### Owns

- worker `handoff_result` collection after workers return
- `active_passes` status reconciliation before merge
- schema validation before merge
- deduplication
- contradiction marking
- evidence gap marking
- stale-context marking
- review-ready `aggregation_packet`

### Does Not Own

- live child waiting
- reviewer family final selection beyond suggestions
- approval/final judgment
- worker task execution

### Fork Context

`aggregator` is a collector stage and defaults to `stage_execution_mode=main_agent_role_pass`. Main-agent role execution is preferred because aggregation is a bounded normalization over returned packets and active-pass classifications. If a physical dedicated stage-owner spawn is explicitly chosen, use `fork_context=false` with a curated aggregation packet; use `fork_context=true` only when omitting `agent_type`, and do not claim that pass is the dedicated aggregator unless the runtime role is actually `aggregator`.

### Aggregator Gate

Aggregator starts only after all lanes are either returned or explicitly classified by the caller. Missing lanes must be marked as:

- `unmaterialized_lane`
- `no_wait_handle`
- `timed_out`
- `superseded`
- `schema_invalid`

`close_agent` output is not a returned worker result. A lane is aggregatable only when a `wait_agent` result or explicit caller classification records `returned`, `timed_out`, `superseded`, or `schema_invalid`.

### MCP Evidence Handling

`aggregator` is an MCP-critical collector. It preserves MCP evidence, MCP gaps, and MCP waivers from child `handoff_result` packets; if MCP-required evidence is missing, error-shaped, or unclassified, return `aggregation_ready=false` with required validation evidence instead of producing a ready packet.

### Aggregator MCP Gate

`mcp_aggregation_required=true` for architecture-required runs. Before emitting `aggregation_ready=true`, `aggregator` must use available MCP tools to organize evidence refs, classify context/tool gaps, detect contradictions, or record a bounded MCP blocker/waiver. MCP calls that fail, return path errors, inactive-server errors, or unavailable-tool errors are blocker evidence only; they must not enter `evidence_refs` as successful MCP evidence.

`docker_mcp_sequentialthinking_required=true` for `aggregator`, `review-router`, and reviewer lanes: aggregation/review evidence must identify `MCP_DOCKER/sequentialthinking:success`; standalone `sequentialthinking` MCP evidence and `Transport closed` are not sufficient.

`per_agent_mcp_lifecycle_required=true` and `mcp_process_shutdown_required=true` for `aggregator`, `review-router`, and reviewer lanes. Each owning agent initializes required MCP inside its own bounded work scope, then closes MCP sessions/processes before returning. Aggregation/review handoff is invalid unless `mcp_quiescence_snapshot.open_mcp_process_count=0` and `cleanup_status=clean`.

### Aggregation Evidence Contract

Aggregator prompts and packets must carry `handoff_result`, `active_passes`, `source_pass_statuses`, and `context_packet_version`. Prose summaries without those physical evidence fields are not aggregation and must be treated as `aggregation_ready=false`.

### Review Fanout Budget

`agent_fanout_budget_required=true` applies to review routing. `aggregation_packet.required_review_axes[]` may contain many axes, but `review-router` must fit physical reviewer lanes within `max_review_lanes_per_wave=2` and `max_total_child_agents_per_loop=4`. Related review axes should be coalesced into one reviewer lane with a combined `validation_prompt`; axes not executed must become explicit `review_waivers[]` or feedback blockers visible to `meta-judge`.

The specialist list must be enumerated fresh for every review routing pass. A review `launch_manifest` emitted from memory, aliases, skill names, canonical stage owners, or a partial specialist list is invalid.

## Aggregation Packet

Minimum content:

- normalized claims
- `context_packet_version`
- evidence refs per claim
- artifact refs and artifact kinds per handoff
- source worker/pass id
- source lane id, parent pass id, and blocker fingerprint
- `loop_carryover` with unresolved blockers and rejected assumptions
- merge point
- required review axes
- coverage status or explicit waiver
- confidence summary
- contradiction list
- missing lanes
- schema-invalid outputs
- stale-context findings
- suggested reviewer families

## Review Router

### Lifecycle

1. Read `aggregation_packet`.
2. For main-agent execution, activate `$review-router`; the skill is procedural guidance, not a spawnable `agent_role`.
3. Summon the full specialist list by enumerating `${CODEX_HOME}/agents/<category>/*.toml`; route only to concrete review-allowed roles found in that list.
4. Identify artifact type, risk axis, confidence gap, and reviewer lens.
5. Read `fanout_budget` and define a bounded reviewer instance count, owned scope, review question, expected artifact.
6. Return common `launch_manifest` for caller materialization with `manifest_kind=review` and `source_aggregation_packet_ref`.
7. Close immediately after handoff.

### Single Router Rule

One review wave owns exactly one `review-router` pass. Reviewer multiplicity lives below the router.

### Fork Context

`review-router` defaults to `stage_execution_mode=main_agent_role_pass`. Main-agent role execution uses `$review-router` as the procedural skill because reviewer selection is a bounded routing decision over `aggregation_packet`. If a physical dedicated stage-owner spawn is explicitly chosen, use `fork_context=false` with a curated review-routing packet; use `fork_context=true` only when omitting `agent_type`, and do not claim that pass is the dedicated review-router unless the runtime role is actually `review-router`.

Specialist reviewers default to `fork_context=false`. They receive a curated evidence packet containing the original request or acceptance criteria, the aggregation packet, the reviewed artifact refs, claimed behavior, test/validation evidence, known risks, and the specific review question. Full conversation context is allowed only by explicit waiver and must be visible to `meta-judge`.

`review-router` and reviewer lanes are MCP-critical when the aggregation packet contains MCP/tool evidence gaps. The router must create concrete review lanes whose `validation_prompt` asks reviewers to verify MCP evidence or explicit waiver coverage.

### MCP Review Request Boundary

Reviewers may initialize MCP for their own review scope, but they must close MCP sessions/processes before returning review `handoff_result`. They must not leave hidden long-lived MCP processes behind after handoff.

### Review Coverage Contract

`review-router` must map every `required_review_axes[]`, coverage gap, MCP/tool gap, architecture-risk gap, and security/safety gap to at least one concrete reviewer lane or an explicit `review_waivers[]` path visible to `meta-judge`.

Mapping every axis does not require one reviewer per axis. Prefer fewer reviewer lanes with combined axes when the evidence packet can be reviewed coherently without losing independence.

## Review Families

| Family | Dedicated reviewer | Supporting lenses |
| --- | --- | --- |
| analysis review | `analysis-reviewer` | `reviewer`, `debugger`, `error-detective`, `performance-monitor` |
| engineering review | `engineering-reviewer` | `code-reviewer`, `architect-reviewer`, `chaos-engineer`, `reviewer` |
| search review | `search-reviewer` | `docs-researcher`, `research-analyst`, `competitive-analyst` |
| policy/safety review | `policy-safety-reviewer` | `reviewer`, `architect-reviewer`, `chaos-engineer`, `docs-researcher` |

## Specialist Review Layer

| Contract | Rule |
| --- | --- |
| Owner | caller-materialized specialist reviewer |
| Required input artifact | one review lane, `aggregation_packet`, `validation_prompt`, `context_packet_version` |
| Required output artifact | `handoff_result` with `artifact_ref`, `artifact_kind`, `findings`, evidence, confidence |
| Terminal states | `returned`, `timed_out`, `superseded`, `schema_invalid` |
| Next handoff | `meta-judge`; reviewer must not return to review-router as continuing owner |

## Reviewer Return

Reviewer outputs return directly to `meta-judge` through `handoff_result`. `review-router` does not wait for them.
## Architecture Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.






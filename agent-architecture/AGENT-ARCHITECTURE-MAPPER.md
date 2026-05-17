# Agent Architecture Mapper

This file maps the compact global entrypoint to the detailed architecture files. Keep `AGENTS.md` as a pointer only.

## Canonical Loop

`Orchestrator <-> Context Manager -> Task Planner -> Worker Router -> Specialist Worker Layer -> Aggregator -> Review Router -> Specialist Review Layer -> Meta Judge -> Feedback Trigger Gate -> Feedback to Orchestrator then Context Manager restart or Final Output`

## Detail Map

| Need | Read |
| --- | --- |
| Full index and read order | `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md` |
| Canonical loop, source hierarchy, plane model | `${CODEX_HOME}/agent-architecture/00-canonical-map.md` |
| Harness owner, run ledger, schema gates, failure classes | `${CODEX_HOME}/agent-architecture/01-harness-layer.md` |
| Context Manager and Task Planner boundaries | `${CODEX_HOME}/agent-architecture/02-context-planning.md` |
| Worker Router, specialist fan-out, same-role parallelism | `${CODEX_HOME}/agent-architecture/03-worker-routing.md` |
| Aggregator, Review Router, reviewer layer | `${CODEX_HOME}/agent-architecture/04-aggregation-review.md` |
| Meta Judge, feedback re-entry, pass cleanup | `${CODEX_HOME}/agent-architecture/05-feedback-lifecycle.md` |
| Agent roster, support specialists, model tiers | `${CODEX_HOME}/agent-architecture/06-agent-roster-models.md` |
| Artifact schemas, manifests, ledgers | `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md` |
| Harness quality, evals, drift checks, validator | `${CODEX_HOME}/agent-architecture/08-quality-evals.md` |
| Runtime orchestration step sequence | `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md` |
| Validator modules | `${CODEX_HOME}/agent-architecture/validators/*.py` |
| Runtime artifact validator | `${CODEX_HOME}/agent-architecture/validate-runtime-artifact.py` |
| Harness handoff gate | `${CODEX_HOME}/agent-architecture/harness_gate.py` |
| Caller handoff wiring | `${CODEX_HOME}/agent-architecture/harness_handoff.py` |
| Runtime gate smoke test | `${CODEX_HOME}/agent-architecture/validate-runtime-gate-smoke.py` |
| Runtime agent category catalog | `${CODEX_HOME}/agents/<category>/*.toml` |
| Personal record only | Obsidian `오케스트레이션_하네스 엔지니어링` is not a validation or test target |

## Init Inheritance

When `/init` creates or refreshes a repo-local `AGENTS.md`, use `${CODEX_HOME}/agent-architecture/AGENTS.local-template.md` as the intended starting shape. If `/init` emits its built-in `Repository Guidelines` template instead, immediately run `python ${CODEX_HOME}/agent-architecture/apply-agents-inheritance.py AGENTS.md` to prepend the global inheritance and validation hook block while preserving the generated project-specific content.

## Runtime Routing Map

- Runtime prompts are categorized under `${CODEX_HOME}/agents/<category>/*.toml`.
- Canonical stage owners have exact TOML files under `${CODEX_HOME}/agents/09-meta-orchestration/`.
- Runtime order is defined by `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`; stage detail files define field contracts.
- Main-agent control stages use global skills `$orchestrator`, `$task-planner`, `$worker-router`, `$task-distributor`, `$result-aggregator`, `$review-router`, and `$feedback-synthesizer`; these skills are procedural adapters and are not spawnable agent roles.
- `$docker-memory` is optional Docker MCP Memory guidance and is not a mandatory architecture gate.
- `codex-context-ledger` MCP is the single resident context authority for a run/session.
- `orchestrator`, `context-manager`, `task-planner`, `worker-router`, `aggregator`, `review-router`, and `meta-judge` default to main-agent role passes, not physical subagents.
- Physical parallelism is reserved for worker specialists and review specialists selected from validated manifests.
- Support meta agents must not emit canonical stage artifacts; they hand off to the matching stage owner.
- Routers select by category first, then by role fit.
- Category routers are dispatch contracts, not long-lived workers.
- Routers return `launch_manifest` and close; caller materializes physical children.
- Track physical children in `active_passes` with concrete wait handles.
- Aggregator consumes `handoff_result` values and returns an `aggregation_packet`.
- Meta Judge returns a `judgment_envelope` and decides feedback or final output.

## Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.

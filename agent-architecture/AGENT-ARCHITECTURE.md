# Agent Architecture Index

이 파일은 전역 agent architecture 의 상세 문서 index 다. 실행 진입점은 `AGENTS.md`, 상세 매핑은 `AGENT-ARCHITECTURE-MAPPER.md` 가 담당한다.

## Canonical Loop

`Orchestrator <-> Context Manager -> Task Planner -> Worker Router -> Specialist Worker Layer -> Aggregator -> Review Router -> Specialist Review Layer -> Meta Judge -> Feedback Trigger Gate -> Feedback to Orchestrator then Context Manager restart or Final Output`

## Mapper

- Compact map: `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE-MAPPER.md`
- Local init template: `${CODEX_HOME}/agent-architecture/AGENTS.local-template.md`
- Post-init normalizer: `${CODEX_HOME}/agent-architecture/apply-agents-inheritance.py`

## Read Order

| Order | File | Contents |
| --- | --- | --- |
| 0 | `${CODEX_HOME}/agent-architecture/00-canonical-map.md` | canonical loop, source hierarchy, plane model, stage owner map |
| 1 | `${CODEX_HOME}/agent-architecture/01-harness-layer.md` | harness owner, run ledger, schema gates, failure taxonomy |
| 2 | `${CODEX_HOME}/agent-architecture/02-context-planning.md` | `context-manager`, `task-planner`, context gate, planning output |
| 3 | `${CODEX_HOME}/agent-architecture/03-worker-routing.md` | `worker-router`, specialist fan-out, same-role parallelism, caller materialization |
| 4 | `${CODEX_HOME}/agent-architecture/04-aggregation-review.md` | `aggregator`, `review-router`, reviewer clusters, review returns |
| 5 | `${CODEX_HOME}/agent-architecture/05-feedback-lifecycle.md` | `meta-judge`, feedback rule, pass status transitions, cleanup |
| 6 | `${CODEX_HOME}/agent-architecture/06-agent-roster-models.md` | canonical agents, support specialists, model tiers |
| 7 | `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md` | artifact names, manifest fields, handoff fields, ledgers |
| 8 | `${CODEX_HOME}/agent-architecture/08-quality-evals.md` | harness quality score, eval checks, doc drift, validator modules, improvement loop |
| 9 | `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md` | Maestro-style runtime step sequence, status, resume, archive |

## Runtime Prompt Files

Runtime prompts are discovered recursively from `${CODEX_HOME}/agents/<category>/*.toml`.

Runtime execution policy: keep context state in the `codex-context-ledger` MCP; run control stages as main-agent role passes; reserve physical subagents for worker/review specialists. Mandatory procedural skills: architecture-required runs must activate `$orchestrator`, `$task-planner`, `$worker-router`, `$task-distributor`, `$result-aggregator`, `$review-router`, and `$feedback-synthesizer` at their matching stages. `$docker-memory` is optional and must not be treated as a mandatory gate.

| Category | Route scope |
| --- | --- |
| `01-core-development` | app, API, frontend, backend, mobile, UI, service design |
| `02-language-specialists` | language/framework-specific implementation and review |
| `03-infrastructure` | cloud, platform, deployment, network, SRE, Windows infrastructure |
| `04-quality-security` | review, testing, debugging, security, compliance, chaos/performance |
| `05-data-ai` | data, database, ML, AI, prompt, LLM architecture |
| `06-developer-experience` | build, docs, refactor, CLI, tooling, dependency, workflow support |
| `07-specialized-domains` | domain specialists such as embedded, fintech, IoT, payment, SEO |
| `08-business-product` | product, project, legal, business, writing, customer-facing lanes |
| `09-meta-orchestration` | coordination, context, task distribution, synthesis, workflow orchestration |
| `10-research-analysis` | search, docs research, competitive/data/market/trend analysis |

Canonical loop role names remain architectural stage names. Physical agents are selected from the category catalog by router/caller fit.

## Source Of Truth Rule

- `AGENTS.md` is only the compact pointer.
- `AGENT-ARCHITECTURE-MAPPER.md` is the runtime detail map.
- This file is the architecture index.
- `agent-architecture/*.md` files hold the detailed rules.
- `09-runtime-orchestration-steps.md` is the procedural runtime sequence for architecture-required work.
- Runtime TOML files must stay consistent with those detailed rules.
- Obsidian `오케스트레이션_하네스 엔지니어링` is a personal record only, not a source of truth and not a validation/test target.

## Update Rule

When changing the architecture:

1. Update the relevant `agent-architecture/*.md` detail file first.
2. Update this index only if a file, stage, or read order changes.
3. Update `AGENT-ARCHITECTURE-MAPPER.md` when the compact runtime map changes.
4. Update `AGENTS.md` only when the pointer targets change.
5. Update runtime TOML prompts when behavior expected from actual agents changes.
6. Update `08-quality-evals.md` and `validators/*.py` when repeated failures reveal a new measurable invariant.
7. Update `09-runtime-orchestration-steps.md` when the runtime order changes.
## Architecture Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.






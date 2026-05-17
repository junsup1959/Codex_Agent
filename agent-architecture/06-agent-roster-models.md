# Agent Roster And Models

이 문서는 category-based agent catalog, routing family, model tier 를 정의한다.

## Runtime Catalog Layout

Runtime prompts live under `${CODEX_HOME}/agents/<category>/*.toml`. The category folder is part of routing metadata.

| Category | Primary route |
| --- | --- |
| `01-core-development` | product code, API, UI, service implementation |
| `02-language-specialists` | language/framework-specific work |
| `03-infrastructure` | cloud, platform, deployment, network, SRE, Windows ops |
| `04-quality-security` | review, test, debug, security, compliance, performance |
| `05-data-ai` | data, database, ML, AI, LLM, prompt work |
| `06-developer-experience` | build, docs, refactor, tooling, CLI, dependency workflows |
| `07-specialized-domains` | domain experts and vertical specialists |
| `08-business-product` | product, project, legal, business, writing support |
| `09-meta-orchestration` | context, planning, coordination, synthesis, workflow control |
| `10-research-analysis` | search, documentation research, market/data/trend analysis |

## Category Router Rule

Routers first choose one or more categories, then select concrete TOML roles inside those categories. Same category and same role may be selected multiple times when ownership, artifact, or evidence scope differs.

Category routing returns logical lanes only. The caller still materializes physical child agents, records `agent_id` and `submission_id`, and closes the router pass after handoff.

## Dependency Enforcement

Every logical lane must resolve `agent_category/agent_role` to an existing `${CODEX_HOME}/agents/<category>/<role>.toml`. Canonical stage owners are not specialist lanes. `worker-router` must choose concrete non-stage specialists; `review-router` must choose reviewer or review-support specialists.

Skills are instructions, not agent types. A skill such as `reverse-engineering-expert` may be required in the lane prompt, but it must not appear as `launch_manifest.children[].agent_role` unless a matching TOML role exists in the catalog.

## Architectural Roles

Canonical loop role names are stage responsibilities, not guaranteed TOML filenames. If a direct TOML does not exist, select the nearest category role:

| Stage responsibility | Preferred category |
| --- | --- |
| orchestration/planning | `09-meta-orchestration` |
| context sync/synthesis | `09-meta-orchestration`, `10-research-analysis` |
| worker implementation | `01-core-development`, `02-language-specialists`, `06-developer-experience` |
| analysis/search | `10-research-analysis`, `05-data-ai`, `04-quality-security` |
| review/governance | `04-quality-security`, `08-business-product`, `09-meta-orchestration` |

## Canonical Stage Runtime Map

The canonical stage name is the architecture contract. The runtime TOML below owns the exact stage return shape.

| Canonical stage | Runtime TOML | Required return |
| --- | --- | --- |
| `orchestrator` | `09-meta-orchestration/orchestrator.toml` | `orchestration_request` |
| `context-manager` | `09-meta-orchestration/context-manager.toml` | `context_packet` |
| `task-planner` | `09-meta-orchestration/task-planner.toml` | `execution_plan` |
| `worker-router` | `09-meta-orchestration/worker-router.toml` | `launch_manifest` or `schema_invalid` |
| `aggregator` | `09-meta-orchestration/aggregator.toml` | `aggregation_packet` or `aggregation_ready=false` |
| `review-router` | `09-meta-orchestration/review-router.toml` | review `launch_manifest` or `schema_invalid` |
| `meta-judge` | `09-meta-orchestration/meta-judge.toml` | `judgment_envelope` |

## Model Tier Policy

| Tier | Default use |
| --- | --- |
| `gpt-5.5` | core loop control, routing, aggregation, meta judgment, high-impact review |
| `gpt-5.4` | complex continuing specialists needing deeper reasoning |
| `gpt-5.4-mini` | high-throughput engineering/test lanes where fan-out matters |
| `gpt-5.3-codex-spark` | fast setup, evidence gathering, documentation, metrics, distribution helpers |

## Tier Rationale

- Router passes are short-lived but high-leverage; wrong routing multiplies downstream cost.
- Category selection prevents scanning every role as a flat pool.
- Continuing worker lanes may use lighter models when many instances run in parallel.
- Explicit user instruction can override model tier for a bounded task.

## Architecture Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.

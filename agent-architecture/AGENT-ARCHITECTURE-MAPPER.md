# Agent Architecture Mapper

Keep `AGENTS.md` compact and route detailed work here.

## Canonical Flow

`orchestrator -> context-ledger -> task-planner -> worker -> review-distributor -> review -> feedbackgate`

## Runtime Map

- `$orchestrator`: main-agent skill; emits `orchestration_request`.
- `$context-ledger`: main-agent skill; mandatory MCP stage backed by `codex-context-ledger`.
- `$task-planner`: main-agent skill; emits bounded `execution_plan`.
- `$worker`: main-agent skill; enumerates concrete worker specialists, calls `spawn_agent`, calls `wait_agent`, and returns worker evidence.
- `$review-distributor`: main-agent skill; maps worker evidence to required review axes and reviewer plan.
- `$review`: main-agent skill; enumerates concrete reviewer specialists, calls `spawn_agent`, calls `wait_agent`, and returns review evidence.
- `$feedbackgate`: main-agent skill; judges review results and returns final output approval or feedback to `$orchestrator`.

## Detail Map

| Need | Read |
| --- | --- |
| Full index | `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md` |
| Runtime order | `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md` |
| Context ledger and planning | `${CODEX_HOME}/agent-architecture/02-context-planning.md` |
| Worker specialist materialization | `${CODEX_HOME}/agent-architecture/03-worker-routing.md` |
| Review distribution and review specialists | `${CODEX_HOME}/agent-architecture/04-aggregation-review.md` |
| Feedbackgate | `${CODEX_HOME}/agent-architecture/05-feedback-lifecycle.md` |
| Contracts and ledgers | `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md` |
| Validation | `${CODEX_HOME}/agent-architecture/08-quality-evals.md` |

## Skill Script Boundary

Each mandatory stage skill owns stage-local scripts under `${CODEX_HOME}/skills/<skill>/scripts/`. Shared global validators stay under `${CODEX_HOME}/agent-architecture/`.

## Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, stage skills, or detects architecture drift, emit `architecture_validation_required=true`.

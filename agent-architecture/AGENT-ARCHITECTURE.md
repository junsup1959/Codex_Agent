# Agent Architecture Index

This is the concise source index for the global Codex architecture.

## Canonical Flow

`orchestrator -> context-ledger -> task-planner -> worker -> review-distributor -> review -> feedbackgate`

The visible work shape is:

`orchestrator -> task-planner -> specialist workers -> review-distributor -> specialist reviews -> feedbackgate`

The mandatory `context-ledger` stage sits between `$orchestrator` and `$task-planner` because run-local state must be synchronized through MCP before planning.

## Mandatory Stage Skills

| Order | Skill | Responsibility |
| --- | --- | --- |
| 1 | `$orchestrator` | classify scope, assign ids, create `orchestration_request` |
| 2 | `$context-ledger` | read/write `codex-context-ledger`, emit `context_packet` |
| 3 | `$task-planner` | create bounded `execution_plan` |
| 4 | `$worker` | enumerate specialists, `spawn_agent`, `wait_agent`, return worker evidence |
| 5 | `$review-distributor` | select required review axes and reviewer plan |
| 6 | `$review` | enumerate reviewers, `spawn_agent`, `wait_agent`, return review evidence |
| 7 | `$feedbackgate` | judge review evidence; final output or feedback to `$orchestrator` |

## Read Order

| File | Purpose |
| --- | --- |
| `AGENT-ARCHITECTURE-MAPPER.md` | compact map from entrypoint to details |
| `09-runtime-orchestration-steps.md` | mandatory runtime order |
| `02-context-planning.md` | context ledger and planning boundary |
| `03-worker-routing.md` | worker specialist materialization |
| `04-aggregation-review.md` | review distribution and specialist reviews |
| `05-feedback-lifecycle.md` | feedbackgate and loop return |
| `07-contracts-ledgers.md` | artifact, pass, and evidence fields |
| `08-quality-evals.md` | validation expectations |

## Script Boundary

Global scripts under `agent-architecture/` are shared validators and harness tools. Stage-local preflight scripts live under each mandatory skill's `scripts/` directory.

## Update Rule

When the architecture changes, update the affected docs, stage skills, skill `contract.json`, and validators together. Then run:

```powershell
python "$env:CODEX_HOME/agent-architecture/validate-skill-contracts.py"
python "$env:CODEX_HOME/agent-architecture/validate-agent-architecture.py"
```

## Architecture Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, stage skills, or detects architecture drift, emit `architecture_validation_required=true`.

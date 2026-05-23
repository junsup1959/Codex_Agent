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

## Context Ledger Barrier

`context_ledger_barrier_required=true`: every mandatory stage starts by reading the latest `codex-context-ledger` packet and validating `consumed_context_revision`. A stage may not act from chat memory when the ledger is stale or unavailable.

Before handoff, each stage writes its delta through `$context-ledger` and records `stage_pass_ref`. Required packet fields are `context_packet_version`, `consumed_context_revision`, `context_delta`, `new_artifact_refs`, `new_evidence_refs`, and `stage_pass_ref`.

## Read Order

| File | Purpose |
| --- | --- |
| `AGENT-ARCHITECTURE-MAPPER.md` | compact map from entrypoint to details |
| `09-runtime-orchestration-steps.md` | mandatory runtime order |
| `02-context-planning.md` | context ledger and planning boundary |
| `03-worker-materialization.md` | worker specialist materialization |
| `04-review-flow.md` | review distribution and specialist reviews |
| `05-feedback-lifecycle.md` | feedbackgate and loop return |
| `07-contracts-ledgers.md` | artifact, pass, and evidence fields |
| `08-quality-evals.md` | MCP validation expectations |

## MCP Validation Boundary

Runtime stage validation is performed only through `codex-context-ledger` MCP tools, especially `validate_context_revision`, `validate_stage_packet`, and `validate_tool_sequence`. Static repository scripts and external wrappers are not part of the architecture gate.

## Update Rule

When the architecture changes, update the affected docs, stage skills, and skill `contract.json` together. The next architecture-required run must prove the flow through MCP tool return values.

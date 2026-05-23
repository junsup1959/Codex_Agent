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

`context_ledger_barrier_required=true`: every runtime map entry consumes the latest ledger revision and emits a context delta plus `stage_pass_ref` before the next owner runs.

## Detail Map

| Need | Read |
| --- | --- |
| Full index | `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md` |
| Runtime order | `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md` |
| Context ledger and planning | `${CODEX_HOME}/agent-architecture/02-context-planning.md` |
| Worker specialist materialization | `${CODEX_HOME}/agent-architecture/03-worker-materialization.md` |
| Review distribution and review specialists | `${CODEX_HOME}/agent-architecture/04-review-flow.md` |
| Feedbackgate | `${CODEX_HOME}/agent-architecture/05-feedback-lifecycle.md` |
| Contracts and ledgers | `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md` |
| MCP validation | `${CODEX_HOME}/agent-architecture/08-quality-evals.md` |

## MCP Validation Boundary

Runtime validation is API-based: each mandatory stage skill calls `validate_context_revision`, `validate_stage_packet`, and `validate_tool_sequence` through localhost `codex-context-ledger`. Static repository scripts and repository-side wrappers are not part of the architecture gate.

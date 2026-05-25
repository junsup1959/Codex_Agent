# Agent Architecture Mapper

Keep `AGENTS.md` compact and route orchestrator-started architecture details here.

## Canonical Flow

`orchestrator -> context-ledger -> task-designer -> task-distributor -> worker -> review-distributor -> review -> feedbackgate`

## Runtime Map

- `$orchestrator`: main-agent skill; uses `MCP_DOCKER.sequentialthinking` and emits `orchestration_request`.
- `$context-ledger`: main-agent skill; mandatory MCP stage backed by `codex-context-ledger` after `$orchestrator` starts the run.
- `$task-designer`: main-agent skill; uses `MCP_DOCKER.sequentialthinking` and emits option-based `task_design.md`, selected design, and `artifact_profile`.
- `$task-distributor`: main-agent skill; uses `MCP_DOCKER.sequentialthinking` and emits `task_distribution_criteria.md`, bounded `execution_plan`, and `artifact_profile`.
- `$worker`: main-agent skill; must call concrete worker specialists with `spawn_agent`, call `wait_agent`, and return worker evidence.
- `$review-distributor`: main-agent skill; uses `MCP_DOCKER.sequentialthinking` and maps worker evidence to `review_distribution_criteria.md`, reviewer plan, and `artifact_profile`.
- `$review`: main-agent skill; must call concrete reviewer specialists for non-waived review lanes, call `wait_agent`, and return review evidence.
- `$feedbackgate`: main-agent skill; judges review results and returns final output approval or feedback to `$orchestrator`.
- `$context-ledger`: preserves feedback-loop reuse decisions as `reentry_cache` when feedback returns to a new loop.

`context_ledger_barrier_required=true`: every runtime map entry consumes the latest ledger revision and emits a context delta plus `stage_pass_ref` before the next owner runs.

## Detail Map

For normal stage execution, prefer the active skill's adjacent `contract.json` and its `source_docs` over this broad map. Use this map for architecture maintenance or when a stage-order blocker needs cross-stage context.

| Need | Read |
| --- | --- |
| Full index | `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md` |
| Runtime order | `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md` |
| Context ledger, design, and distribution | `${CODEX_HOME}/agent-architecture/02-context-planning.md` |
| Worker specialist materialization | `${CODEX_HOME}/agent-architecture/03-worker-materialization.md` |
| Review distribution criteria and review specialists | `${CODEX_HOME}/agent-architecture/04-review-flow.md` |
| Feedbackgate | `${CODEX_HOME}/agent-architecture/05-feedback-lifecycle.md` |
| Contracts and ledgers | `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md` |
| MCP validation | `${CODEX_HOME}/agent-architecture/08-quality-evals.md` |

## MCP Validation Boundary

Runtime validation is API-based: each mandatory stage skill calls `validate_context_revision`, `validate_stage_packet`, and `validate_tool_sequence` through localhost `codex-context-ledger`. `$task-designer`, `$task-distributor`, `$review-distributor`, and completion-bearing stages also call their documented stage-specific validators. Static repository scripts and repository-side wrappers are not part of the architecture gate.
The reasoning-heavy stages `$orchestrator`, `$task-designer`, `$task-distributor`, and `$review-distributor` must additionally emit `sequential_thinking_ref` from `MCP_DOCKER.sequentialthinking`.

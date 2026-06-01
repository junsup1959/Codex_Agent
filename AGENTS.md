# Orchestrator-Scoped Codex Architecture Pointer

This file is the compact project guardrail. Detailed contracts live under `${CODEX_HOME}/agent-architecture/`.

## Reference Scope

- During normal direct work, do not load the full architecture docs.
- When a stage skill is active, read only that skill's `SKILL.md`, adjacent `contract.json`, and the `source_docs` listed in that contract.
- Use `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md`, `AGENT-ARCHITECTURE-MAPPER.md`, or `09-runtime-orchestration-steps.md` only when changing the architecture itself or resolving a stage-order blocker.

## Canonical Flow

`orchestrator -> context-ledger -> task-designer -> task-distributor -> worker -> review-distributor -> review -> feedbackgate`

User-facing shorthand may omit the ledger as `orchestrator -> task-designer -> task-distributor -> specialist workers -> review-distributor -> reviews -> feedbackgate`, but runtime execution must include the mandatory `$context-ledger` stage when `architecture_required=true`.

Simple tasks may use the compact path `orchestrator -> direct-workflow` when `$orchestrator` explicitly emits `architecture_required=false`, `workflow_mode="express-direct"`, and `next_owner="direct-workflow"`.

## Application Rule

- Direct-answer, implementation, research, audit, comparison, risky, multi-agent, or multi-artifact work may proceed through the normal direct workflow unless the user explicitly invokes `$orchestrator`, asks to run the architecture/orchestration flow, or a current `$feedbackgate` result returns bounded feedback to `$orchestrator`.
- `$orchestrator` activation is the entry point that either sets `architecture_required=true` for a full run or returns simple work to the direct workflow with `architecture_required=false`. Do not set `architecture_required=true` from a global/non-trivial-task classifier alone.
- After `$orchestrator` emits an `orchestration_request`, follow `09-runtime-orchestration-steps.md`. When `architecture_required=true`, do not skip or reorder stages unless `$feedbackgate` blocks the loop.
- `express_direct_allowed=true`: for simple, low-risk, single-lane work that does not need specialist fanout, task-design alternatives, or feedbackgate judgment, `$orchestrator` may emit `workflow_mode="express-direct"` with `next_owner="direct-workflow"`. This exits the architecture stage chain and resumes normal direct implementation, validation, and user reporting.
- `orchestration_stage_skills_required=true` applies only inside a full architecture run with `architecture_required=true`: force `$orchestrator`, `$context-ledger`, `$task-designer`, `$task-distributor`, `$worker`, `$review-distributor`, `$review`, and `$feedbackgate` in that order.
- `context_ledger_mcp_required=true`: `$context-ledger` must use localhost `codex-context-ledger` as the run/session source of truth. Do not spawn a physical resident context agent.
- `context_ledger_barrier_required=true`: every mandatory stage must read and validate the latest ledger revision before acting, then write a context delta and `stage_pass_ref` before handoff.
- `mcp_tool_sequence_validation_required=true`: every mandatory skill must call its documented `codex-context-ledger` tools in order and require `validate_stage_packet.valid=true` plus `validate_tool_sequence.valid=true`; `$task-designer` also requires `validate_task_design.valid=true`, `$task-distributor` also requires `validate_execution_plan.valid=true`, `$review-distributor` also requires `validate_review_plan.valid=true`, and `$worker`, `$review`, and `$feedbackgate` also require `validate_stage_completion.valid=true`.
- `sequential_thinking_required=true` for `$orchestrator`, `$task-designer`, `$task-distributor`, and `$review-distributor`: each must attempt `MCP_DOCKER.sequentialthinking` before finalizing its stage artifact and must emit `sequential_thinking_ref` or `sequential_thinking_waiver`; tool failure records waiver evidence and does not stop the stage.
- `$task-designer` emits `task_design.md` with multiple options, comparison criteria, selected option, rationale, distribution boundaries, and `artifact_profile`.
- `$task-distributor` emits `task_distribution_criteria.md` plus `execution_plan` with `artifact_profile`; it must not redefine the selected task design.
- `${CODEX_HOME}/agents/<category>/*.toml` is guidance for non-worker control stages. Do not force agent calls for `$orchestrator`, `$task-designer`, `$task-distributor`, or `$review-distributor`.
- `$worker` is the forced specialist materialization stage for worker lanes: it must select concrete worker specialists, call `spawn_agent`, wait with `wait_agent`, and classify every lane before handoff.
- `$review` is the forced specialist reviewer materialization stage for non-waived review lanes: it must select concrete reviewer specialists, call `spawn_agent`, wait with `wait_agent`, and classify every review lane before handoff.
- Physical parallelism is reserved for specialist workers and specialist reviewers.
- Every spawned child must have `spawn_receipt_ref`, `agent_id` or `submission_id`, `wait_handle`, and later `wait_agent` evidence. `close_agent` is cleanup only.
- `agent_fanout_budget_required=true`: default max 2 worker lanes, 2 review lanes, 4 total child agents per loop, 1 same-role parallel lane, and 1 MCP-using child lane at a time.

## Feedback Gate

- `feedback_gate_mandatory=true` for every full architecture run with `architecture_required=true`.
- Express-direct handoffs are not architecture completions and must not claim feedbackgate approval, reviewer coverage, or merge-readiness.
- `$feedbackgate` judges review evidence and either allows final output or returns bounded feedback to `$orchestrator`.
- Feedback loops must preserve artifact reuse scope through `task_design_reentry_decision` and `$context-ledger.reentry_cache`.
- Final, ready, approve, merge-ready, or completion claims are forbidden without current `feedback_gate_evidence`, reviewer results or waivers, MCP validation evidence, and clean MCP/tool quiescence.
- If review judgment requires feedback, the next stage is always `$orchestrator`; do not jump directly into a worker or review lane.

## MCP Usage

- `mcp_required=true` for orchestrator-started architecture work.
- MCP calls that fail, return errors, or are unavailable are blocker/waiver evidence, not success evidence.
- `$docker-memory` is optional long-term memory guidance only. It does not replace `$context-ledger`, MCP validation evidence, specialist review evidence, or `$feedbackgate`.

## MCP Runtime Validation

Do not use repository-side scripts as runtime gates. Each mandatory skill must prove its own handoff through `codex-context-ledger` MCP calls. All stages call `validate_context_revision`, `validate_stage_packet`, and `validate_tool_sequence`; design/distribution stages additionally call `validate_task_design`, `validate_execution_plan`, or `validate_review_plan`; completion-bearing stages additionally call `validate_stage_completion`.

## Local MCP Approval Helper

- Use `scripts/ensure-mcp-tool-approvals.ps1` to keep `MCP_DOCKER` and `codex-context-ledger` tool approvals synchronized in `${CODEX_HOME}/config.toml`.
- The helper adds missing approval blocks and removes stale approval blocks for managed servers when a tool disappears from the maintained tool manifest.
- Preferred command: `powershell -ExecutionPolicy Bypass -File .\scripts\ensure-mcp-tool-approvals.ps1`.
- Before changing the helper's TOML regex logic, run `powershell -ExecutionPolicy Bypass -File .\scripts\ensure-mcp-tool-approvals.ps1 -SelfTest`.
- Agents without full filesystem access may still use the helper in workspace-safe mode:
  - Check only: `powershell -ExecutionPolicy Bypass -File .\scripts\ensure-mcp-tool-approvals.ps1 -Check`
  - Print updated config: `powershell -ExecutionPolicy Bypass -File .\scripts\ensure-mcp-tool-approvals.ps1 -PrintOnly`
  - Write a workspace-local candidate: `powershell -ExecutionPolicy Bypass -File .\scripts\ensure-mcp-tool-approvals.ps1 -OutputPath .\.codex-generated\config.toml`
- This helper is not a runtime validation gate. It only prevents repetitive MCP approval prompts by adding explicit `[mcp_servers.<server>.tools.<tool>] approval_mode = "approve"` entries where Codex has no wildcard approval syntax.

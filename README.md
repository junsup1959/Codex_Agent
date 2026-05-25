# Codex Agent Architecture Workspace

This workspace mirrors the Codex agent architecture so changes can be reviewed before they are copied into `${CODEX_HOME}`.

## Current Flow

```text
orchestrator -> context-ledger -> task-designer -> task-distributor -> worker -> review-distributor -> review -> feedbackgate
```

- The architecture flow is enforced only after `$orchestrator` is explicitly used or a prior `$feedbackgate` result routes bounded feedback back to `$orchestrator`.
- `orchestrator`, `context-ledger`, `task-designer`, `task-distributor`, `worker`, `review-distributor`, `review`, and `feedbackgate` are stage skills inside that orchestrator-started run.
- The mandatory `context-ledger` stage runs between `$orchestrator` and `$task-designer` inside the architecture flow, even when user-facing shorthand omits it.
- `$orchestrator`, `$task-designer`, `$task-distributor`, and `$review-distributor` must attempt `MCP_DOCKER.sequentialthinking` before finalizing their stage artifacts and must emit `sequential_thinking_ref` or `sequential_thinking_waiver`.
- `$task-designer` creates option-based `task_design.md`; `$task-distributor` creates `task_distribution_criteria.md` and `execution_plan`; reusable planning artifacts carry `artifact_profile`.
- Feedback loops carry artifact reuse and invalidation scope through `task_design_reentry_decision` and `reentry_cache`.
- `${CODEX_HOME}\agents\` is guidance for control/distribution stages. `$worker` and `$review` are the forced specialist agent materialization stages for worker lanes and non-waived review lanes.
- Every mandatory stage proves handoff through `codex-context-ledger` MCP tool results, especially `validate_context_revision`, `validate_stage_packet`, and `validate_tool_sequence`; `worker`, `review`, and `feedbackgate` also require `validate_stage_completion`.
- Static scripts may support local checks, but they are not runtime gates.

## Key Paths

- Global pointer: `${CODEX_HOME}\AGENTS.md`
- Global architecture docs: `${CODEX_HOME}\agent-architecture\`
- Project architecture mirror: `.\agent-architecture\`
- Global skills: `${CODEX_HOME}\skills\`
- Project skills mirror: `.\skills\`
- Context Ledger MCP mirror: `.\mcp\context-ledger\`

## MCP

- Docker MCP `sequentialthinking` is mandatory for `$orchestrator`, `$task-designer`, `$task-distributor`, and `$review-distributor`; store only `sequential_thinking_ref` or `sequential_thinking_waiver`, not the reasoning transcript.
- [`context-ledger`](./mcp/context-ledger/README.md) documents the localhost MCP tool sequence and stage validation API.
- Use `scripts/ensure-mcp-tool-approvals.ps1` only to synchronize Codex MCP tool approval blocks in `${CODEX_HOME}\config.toml`; it is not runtime validation evidence.
- Use `scripts/ensure-mcp-tool-approvals.ps1 -SelfTest` before regex changes to verify the TOML block fixtures without touching `${CODEX_HOME}\config.toml`.

## Skill Mirror Policy

The repository `skills\` tree is a mirror, not the sole source of truth. Before deleting a mirrored skill directory, classify the intended state:

- `global-only`: remove the repository mirror, keep `${CODEX_HOME}\skills\<name>` installed.
- `repo-mirror`: keep the repository copy aligned with the global skill.
- `removed-everywhere`: remove both the repository mirror and the global skill intentionally.

For skill deletion reviews, record which classification applies and verify references with `rg <skill-name> .` plus a direct `${CODEX_HOME}\skills\<name>` existence check.

## Agent Sources & Attribution

This project directly uses and adapts subagent definitions from the MIT-licensed repository:

- https://github.com/VoltAgent/awesome-codex-subagents

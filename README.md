# Codex Agent Architecture Workspace

This workspace mirrors the global Codex agent architecture so changes can be reviewed before they are copied into `${CODEX_HOME}`.

## Current Flow

```text
orchestrator -> context-ledger -> task-planner -> worker -> review-distributor -> review -> feedbackgate
```

- `orchestrator`, `context-ledger`, `task-planner`, `worker`, `review-distributor`, `review`, and `feedbackgate` are stage skills.
- The mandatory `context-ledger` stage runs between `$orchestrator` and `$task-planner`, even when user-facing shorthand omits it.
- Physical `spawn_agent` / `wait_agent` usage is reserved for specialist worker and specialist review stages.
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

- Docker MCP `sequentialthinking` may be used as supporting reasoning evidence where required by a skill.
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

# Codex Agent Architecture

전역 Codex Agents 구조를 프로젝트에 반영하기 위한 작업 영역이다. 현재 기준은 repository-side script가 아니라 `codex-context-ledger` MCP tool 호출 순서다.

## Current Flow

```text
orchestrator -> context-ledger -> task-planner -> worker -> review-distributor -> review -> feedbackgate
```

- `orchestrator`, `context-ledger`, `task-planner`, `worker`, `review-distributor`, `review`, `feedbackgate`는 stage skill 기준으로 동작한다.
- physical spawn은 specialist worker와 specialist review 단계에서만 사용한다.
- 각 stage는 `codex-context-ledger` MCP의 `validate_context_revision`, `validate_stage_packet`, `validate_tool_sequence` 결과로 handoff 가능 여부를 증명한다.
- static script나 외부 wrapper는 런타임 gate로 사용하지 않는다.

## Key Paths

- Global pointer: `C:\Users\junsu\.codex\AGENTS.md`
- Global architecture docs: `C:\Users\junsu\.codex\agent-architecture\`
- Project architecture mirror: `.\agent-architecture\`
- Global skills: `C:\Users\junsu\.codex\skills\`
- Project skills mirror: `.\skills\`
- Context Ledger MCP: `C:\project\mcp\context-ledger`

## MCP

- Docker MCP `sequentialthinking` may be used as supporting reasoning evidence where required by a skill.
- [`context-ledger`](./mcp/context-ledger/README.md) documents the localhost MCP tool sequence and stage validation API.

## Agent Sources & Attribution

This project directly uses and adapts subagent definitions from the MIT-licensed repository:

- https://github.com/VoltAgent/awesome-codex-subagents

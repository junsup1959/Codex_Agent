# 09. Meta & Orchestration

Agents that help plan or coordinate multi-agent Codex workflows without inventing unsupported mechanics.

Canonical architecture control stages are skills, not spawnable agents:
`$orchestrator`, `$context-ledger`, `$task-designer`, `$task-distributor`, `$worker`, `$review-distributor`, `$review`, and `$feedbackgate`.

Included agents:

- `agent-installer` - Help pick and install agents from this repository.
- `agent-organizer` - Pick the right subagents and divide the work cleanly.
- `error-coordinator` - Group and prioritize multiple error threads.
- `it-ops-orchestrator` - Coordinate cross-domain IT and operations workflows.
- `knowledge-synthesizer` - Merge findings from multiple agents into a usable summary.
- `multi-agent-coordinator` - Design explicit multi-agent task plans.
- `performance-monitor` - Turn performance signals into actionable summaries.
- `workflow-orchestrator` - Design explicit delegation flows for larger tasks.

# Quality And Evals

Validation is MCP-backed and fail-closed.

## MCP API Checks

Each mandatory skill calls these through localhost `codex-context-ledger`:

- `validate_stage_packet`: validates barrier fields, expected artifact, next owner, current revision, and stage transition.
- `validate_task_design`: validates task design options, selected option, selection rationale, and distribution boundaries.
- `validate_execution_plan`: validates task distribution criteria, worker lanes, dependencies, fanout shape, and handoff evidence shape.
- `validate_review_plan`: validates review distribution criteria, reviewer lanes, coverage contract, and review handoff evidence shape.
- `validate_stage_completion`: validates completion readiness for worker, review, and feedbackgate.
- `validate_tool_sequence`: validates that the required MCP tools were called in the correct order.

Stage-local Python preflight scripts are intentionally not required.
Static architecture scripts and external wrappers are not runtime gates.
`$orchestrator`, `$task-designer`, `$task-distributor`, and `$review-distributor` must also use `MCP_DOCKER.sequentialthinking` before finalizing their artifacts; validators require `sequential_thinking_ref` or `sequential_thinking_waiver` as proof and do not store the reasoning transcript.

## Runtime Evidence

Before claiming completion for an orchestrator-started architecture run, evidence must show:

- current context revision
- no stale blockers
- required stage pass refs
- waited worker and review children
- review results or explicit waivers
- MCP validation results from `validate_context_revision`, `validate_stage_packet`, each stage-specific validator, and `validate_tool_sequence`
- artifact profiles on reusable planning artifacts
- `sequential_thinking_ref` or `sequential_thinking_waiver` on orchestration, task design, task distribution, and review distribution artifacts
- feedback reentry cache with reusable and invalidated artifacts when feedback loops continue
- clean MCP/tool quiescence
- feedbackgate approval

Missing evidence blocks final output and routes to bounded feedback or repair.

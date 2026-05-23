# Quality And Evals

Validation is MCP-backed and fail-closed.

## MCP API Checks

Each mandatory skill calls these through localhost `codex-context-ledger`:

- `validate_stage_packet`: validates barrier fields, expected artifact, next owner, current revision, and stage transition.
- `validate_tool_sequence`: validates that the required MCP tools were called in the correct order.

Stage-local Python preflight scripts are intentionally not required.
Static architecture scripts and external wrappers are not runtime gates.

## Runtime Evidence

Before claiming completion, evidence must show:

- current context revision
- no stale blockers
- required stage pass refs
- waited worker and review children
- review results or explicit waivers
- MCP validation results from `validate_context_revision`, `validate_stage_packet`, and `validate_tool_sequence`
- clean MCP/tool quiescence
- feedbackgate approval

Missing evidence blocks final output and routes to bounded feedback or repair.

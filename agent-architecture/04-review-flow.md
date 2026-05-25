# Review Distribution And Review

Worker evidence flows directly into `$review-distributor`, then `$review`.

## Review Distributor

`$review-distributor` is a main-agent skill. It reads classified worker results and creates `review_distribution_criteria.md` plus a bounded `review_plan`.

It must:

- read and validate the latest ledger revision
- confirm every worker lane is returned or explicitly classified
- determine review axes from risk, changed artifacts, tests, security, architecture, and user-facing impact
- define review distribution criteria: lane creation, reviewer category fit, coverage, fanout, dependency, waiver, and handoff evidence rules
- use review-capable TOML specialists as category guidance
- choose the minimum bounded reviewer set for `$review` to materialize
- include `artifact_profile` on `review_plan` so feedback loops can reuse or invalidate review distribution criteria explicitly
- include `sequential_thinking_ref` or `sequential_thinking_waiver` proving `MCP_DOCKER.sequentialthinking` was attempted before finalizing review axes, waivers, coverage, fanout, and handoff rules
- preserve explicit review waivers
- write its context delta and `stage_pass_ref`

It does not call `spawn_agent`.

## Review

`$review` is a main-agent skill that materializes physical specialist reviewers selected by `$review-distributor`.

It must:

- read and validate the latest ledger revision
- spawn concrete TOML-backed reviewer specialists for every non-waived review lane
- record spawn receipts and wait handles
- call `wait_agent` for every reviewer
- classify every review lane
- return `review_handoff_results`, `review_waivers`, coverage evidence, and `stage_pass_ref`

## Required API Checks

Before handoff, `$review-distributor` must call `validate_stage_packet`, `validate_review_plan`, and then `validate_tool_sequence` through `codex-context-ledger`. `$review` must call `validate_stage_packet`, `validate_stage_completion`, and then `validate_tool_sequence`. API checks must return `valid=true`.

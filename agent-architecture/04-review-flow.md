# Review Distribution And Review

Worker evidence flows directly into `$review-distributor`, then `$review`.

## Review Distributor

`$review-distributor` is a main-agent skill. It reads classified worker results and creates a bounded `review_plan`.

It must:

- read and validate the latest ledger revision
- confirm every worker lane is returned or explicitly classified
- determine review axes from risk, changed artifacts, tests, security, architecture, and user-facing impact
- enumerate review-capable TOML specialists
- choose the minimum bounded reviewer set
- preserve explicit review waivers
- write its context delta and `stage_pass_ref`

It does not call `spawn_agent`.

## Review

`$review` is a main-agent skill that materializes physical specialist reviewers.

It must:

- read and validate the latest ledger revision
- spawn only concrete TOML-backed reviewer specialists
- record spawn receipts and wait handles
- call `wait_agent` for every reviewer
- classify every review lane
- return `review_handoff_results`, `review_waivers`, coverage evidence, and `stage_pass_ref`

## Required API Checks

Before handoff, `$review-distributor` and `$review` must call `validate_stage_packet` and then `validate_tool_sequence` through `codex-context-ledger`. Both API checks must return `valid=true`.

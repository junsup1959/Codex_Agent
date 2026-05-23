---
name: review
description: Execute the mandatory global Codex Review materialization stage. Use when a review distribution plan must become spawned specialist reviewer agents, waited review results, and classified review evidence.
---

# Review

Use this skill after `$review-distributor`. The main agent uses this skill to spawn concrete specialist reviewers, wait for them, classify review outcomes, and prepare evidence for `$feedbackgate`.

## Contract Gate

Before running this skill, read the adjacent `contract.json`. Prefer `scripts/check_review_wave.py` for a local preflight of the review wave packet before spawning. If this skill, its contract, or its scripts change, run `python ${CODEX_HOME}/agent-architecture/validate-skill-contracts.py` before handoff.

## Inputs

- current `review_plan` or review `launch_manifest`
- worker `handoff_result` evidence and missing-lane classifications
- `fanout_budget`
- full specialist catalog from `${CODEX_HOME}/agents/<category>/*.toml`
- `${CODEX_HOME}/agent-architecture/04-aggregation-review.md`
- `${CODEX_HOME}/agent-architecture/06-agent-roster-models.md`
- `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Workflow

1. Enumerate review-capable specialist TOML roles.
2. Convert each review axis into a scoped reviewer spawn packet.
3. Enforce review fanout budget and preserve waivers for uncovered axes.
4. Call `spawn_agent` for each selected specialist reviewer.
5. Record spawn and wait evidence in `active_passes`.
6. Call `wait_agent` for every spawned reviewer.
7. Classify every review as returned, timed_out, failed, superseded, schema_invalid, no_wait_handle, or thread_limit_reached.
8. Return `review_handoff_results`, `review_waivers`, and coverage evidence.

## Hard Rules

- Do not approve final output.
- Do not review from prose-only worker summaries.
- Do not use canonical stage owners as reviewer specialists.
- Do not continue to `$feedbackgate` with unwaited review children unless they are explicitly classified.
- Do not ask reviewers to configure global MCP profiles; they may only use available tools in their bounded scope.

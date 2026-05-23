---
name: review-distributor
description: Execute the mandatory global Codex Review Distributor stage. Use when completed specialist worker evidence must be routed into bounded spawned specialist review lanes before feedbackgate judgment.
---

# Review Distributor

Use this skill after specialist worker lanes have returned or been explicitly classified. The main agent performs review distribution locally, then spawns concrete reviewer specialists from the TOML catalog.

## Contract Gate

Before running this skill, read the adjacent `contract.json`. Treat `input_artifacts`, `output_artifacts`, `forbidden_outputs`, `required_evidence`, and `source_docs` as the local checklist. Load the listed `${CODEX_HOME}/agent-architecture/<source_doc>` files before emitting the stage artifact. Prefer `scripts/check_review_distribution.py` before handing work to `$review`. If this skill, its contract, scripts, or source docs change, run `python ${CODEX_HOME}/agent-architecture/validate-skill-contracts.py`.

## Inputs

Read these before routing review:

- returned worker `handoff_result` packets and missing-lane classifications
- changed artifacts, validation evidence, blockers, and unresolved assumptions
- current `context_packet_version` and `fanout_budget`
- full specialist catalog under `${CODEX_HOME}/agents/<category>/*.toml`
- `${CODEX_HOME}/agent-architecture/04-aggregation-review.md`
- `${CODEX_HOME}/agent-architecture/06-agent-roster-models.md`
- `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Specialist List Gate

Before selecting any reviewer lane, enumerate the complete specialist list from `${CODEX_HOME}/agents/<category>/*.toml`. Use only concrete TOML roles that are valid review specialists. Do not route from memory, family aliases, skill names, or partial category views.

## Workflow

1. Confirm every worker lane is returned, timed out, failed, superseded, schema-invalid, or explicitly classified.
2. Determine required review axes from risk, code changes, MCP evidence, tests, security, architecture, and user-facing impact.
3. Select the minimum bounded reviewer specialists that satisfy coverage within `fanout_budget`.
4. Emit a `review_plan` with scoped packets and concrete validation prompts.
5. Hand the plan to `$review`; `$review` owns reviewer `spawn_agent` and `wait_agent`.
6. Preserve explicit review waivers for `$feedbackgate`.

## Hard Rules

- Do not judge final readiness.
- Do not skip review when worker evidence is incomplete unless an explicit review waiver is recorded.
- Do not route review work to canonical stage owners.
- Do not aggregate from prose-only worker summaries.
- Do not exceed the review fanout budget.

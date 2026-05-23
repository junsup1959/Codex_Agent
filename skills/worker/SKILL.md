---
name: worker
description: Execute the mandatory global Codex Worker materialization stage. Use when a task plan must become spawned specialist worker agents, waited results, and classified worker handoff evidence.
---

# Worker

Use this skill after `$task-planner`. The main agent uses this skill to enumerate specialist TOML roles, spawn bounded worker specialists, wait for every spawned child, and classify every lane before review distribution.

## Contract Gate

Before running this skill, read the adjacent `contract.json`. Prefer `scripts/check_worker_wave.py` for a local preflight of the worker wave packet before spawning. If this skill, its contract, or its scripts change, run `python ${CODEX_HOME}/agent-architecture/validate-skill-contracts.py` before handoff.

## Inputs

- current `execution_plan`
- `fanout_budget`
- latest `context_packet_version`
- full specialist catalog from `${CODEX_HOME}/agents/<category>/*.toml`
- `${CODEX_HOME}/agent-architecture/03-worker-routing.md`
- `${CODEX_HOME}/agent-architecture/06-agent-roster-models.md`
- `${CODEX_HOME}/agent-architecture/07-contracts-ledgers.md`
- `${CODEX_HOME}/agent-architecture/09-runtime-orchestration-steps.md`

## Workflow

1. Enumerate the complete specialist catalog; select concrete TOML-backed worker roles only.
2. Convert each plan lane into a scoped specialist spawn packet.
3. Enforce `fanout_budget`; coalesce or classify overflow instead of over-spawning.
4. Call `spawn_agent` for each selected specialist worker.
5. Record `spawn_receipt_ref`, `agent_id`, `submission_id`, and `wait_handle` in `active_passes`.
6. Call `wait_agent` for every spawned worker before review distribution.
7. Classify each lane as returned, timed_out, failed, superseded, schema_invalid, no_wait_handle, or thread_limit_reached.
8. Return `worker_handoff_results`, `active_passes`, and missing-lane classifications.

## Hard Rules

- Do not use generic `worker` as a spawned `agent_role`.
- Do not spawn from memory, skill names, or family aliases.
- Do not continue with an unwaited spawned child.
- `close_agent` is cleanup only; it is not wait evidence.
- Do not review or approve final output.

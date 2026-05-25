# Harness Layer

After `$orchestrator` starts an architecture run, the harness enforces stage order, evidence shape, and fail-closed handoff.

## Mandatory Order

`orchestrator -> context-ledger -> task-designer -> task-distributor -> worker -> review-distributor -> review -> feedbackgate`

`orchestration_stage_skills_required=true`: the main agent must activate the matching skill at each stage.

## Main-Agent Stages

The following run as `stage_execution_mode=main_agent_role_pass`:

- `$orchestrator`
- `$context-ledger`
- `$task-designer`
- `$task-distributor`
- `$worker`
- `$review-distributor`
- `$review`
- `$feedbackgate`

They must still emit canonical artifacts, MCP validation evidence, MCP/tool cleanup evidence, and a `stage_pass_ref`.

## Physical Specialist Stages

`${CODEX_HOME}/agents/<category>/*.toml` is guidance for control and planning stages. `$orchestrator`, `$task-designer`, `$task-distributor`, and `$review-distributor` do not force agent calls.

`$worker` is the forced physical specialist stage for worker lanes. `$review` is the forced physical specialist stage for non-waived review lanes. They must select concrete TOML-backed specialists, call `spawn_agent`, record receipt and wait handles, call `wait_agent`, and classify every lane.

Default fanout:

- max 2 worker lanes per wave
- max 2 review lanes per wave
- max 4 total child agents per loop
- max 1 same-role parallel lane
- max 1 MCP-using child lane at a time

## Ledger Barrier

`context_ledger_barrier_required=true`: no stage starts from stale context. The stage must consume a validated ledger revision and return `context_delta`, artifact refs, evidence refs, stale markers, and `stage_pass_ref`.

## Failure Policy

Missing ledger evidence, missing waits, invalid schema, open MCP/tool residue, or unresolved review blockers stop the loop. The next step is bounded feedback or repair, not a completion claim.

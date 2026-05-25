# Agent Roster Models

Specialists are physical subagents selected from TOML files under `${CODEX_HOME}/agents/<category>/*.toml`.

The roster is guidance for control stages such as `$orchestrator`, `$task-designer`, `$task-distributor`, and `$review-distributor`; those stages may use it to describe category fit but must not force agent calls. `$worker` and `$review` are the physical specialist stages.

## Selection Rule

`$worker` must enumerate the complete relevant specialist list before selecting worker lanes. `$review` must enumerate the complete relevant reviewer list before selecting non-waived review lanes. "Use all specialists" means evaluate catalog coverage and choose the minimum bounded set; it does not mean spawning every role.

## Valid Specialist Packet

Each selected specialist lane records:

- `agent_category`
- `agent_role`
- `lane_id`
- `scope`
- `input_artifact_refs`
- `expected_output`
- `validation_prompt`
- `return_owner`
- `context_packet_version`
- `consumed_context_revision`

## Invalid Sources

Do not spawn from:

- memory-only role names
- skill names
- family aliases
- partial category views
- canonical control stage names

## Fanout

Default budgets are conservative: two worker lanes, two review lanes, four total child agents per loop, one same-role parallel lane, and one MCP-using child lane at a time.

# Quality Evals And Drift Checks

This document defines the mechanical checks that keep the orchestration and harness-engineering architecture executable instead of advisory.

## Why This Exists

Prompts alone do not make a loop reliable. The architecture must be backed by schema, runtime gates, CLI exit codes, smoke tests, and concise doc gardening.

## Harness Quality Score

| Check | Pass condition |
| --- | --- |
| `map_readability` | `AGENTS.md` stays a pointer and routes to detail docs |
| `context_gate` | planning starts from a valid `context_packet_version` |
| `materialization` | router logical lanes become caller-created physical children |
| `launch_manifest_schema_gate` | logical lanes have required fields and no wait handles |
| `waitability` | every active child has concrete `wait_handle` |
| `schema_validity` | stage artifact required fields are present |
| `contract_provenance` | canonical stage artifacts carry source refs and lookup status |
| `feedback_gate` | final is blocked whenever `feedback_required=true`; formal claim includes `meta_judge_stage_pass_ref`, reviewer inputs/waivers, and `feedback_gate_evidence` |
| `loop_integrity` | feedback re-entry preserves `loop_carryover` and updates `loop_control` |
| `evidence_trace` | final/review claim links to worker evidence refs |
| `review_coverage` | risk axis has reviewer coverage or explicit waiver |
| `cleanup` | returned routers/stage passes are closed or classified |
| `drift_control` | stale docs/prompts are updated or marked |

## Minimum Evaluation Loop

1. Run the canonical loop on the task.
2. Record run ledger and active pass outcomes.
3. Check failure classes before aggregation or final judgment.
4. Verify reviewer coverage for important risk axes.
5. Run the `Feedback Trigger Gate`; if blocked, return feedback to `orchestrator` and restart from `context-manager`.
6. Before restart, verify `loop_carryover` is carried forward and `loop_control` records attempt/progress.
7. If final output is approved, record residual risk.
8. If feedback repeats without new evidence, stop and update docs, schema, script, or tool boundary.

## Mechanical Validation

Run this validator after architecture edits:

```powershell
python "$env:CODEX_HOME/agent-architecture/validate-agent-architecture.py"
```

Validate actual runtime artifacts before handoff:

```powershell
python "$env:CODEX_HOME/agent-architecture/validate-runtime-artifact.py" --stage-owner worker-router --input .\stage-output.json
python "$env:CODEX_HOME/agent-architecture/validate-runtime-artifact.py" --artifact active_passes --input .\active-passes.json
python "$env:CODEX_HOME/agent-architecture/harness_gate.py" --stage-owner worker-router --input .\stage-output.json
python "$env:CODEX_HOME/agent-architecture/harness_handoff.py" --stage-owner worker-router --expected-next-owner worker-layer --expected-context-packet-version ctx-1 --active-passes-json .\active-passes.json --input .\stage-output.json --decision-out .\handoff-decision.json
python "$env:CODEX_HOME/agent-architecture/harness_handoff.py" --stage-owner meta-judge --previous-judgment-json .\previous-judgment.json --input .\current-judgment.json
python "$env:CODEX_HOME/agent-architecture/validate-runtime-gate-smoke.py"
```

To see how script variables map to files and agent prompt contracts:

```powershell
python "$env:CODEX_HOME/agent-architecture/validate-agent-architecture.py" --explain
```

The validator checks only `.codex` architecture and runtime prompt files. Obsidian notes are personal records and are intentionally excluded from the test target set.

Important boundary: this validator does not inspect a live spawned agent's hidden runtime state. Runtime enforcement comes from `validate-runtime-artifact.py`, `harness_gate.py`, `harness_handoff.py`, and the caller wiring that refuses to start the next stage unless `allow_next_stage=true`. A formal `Feedback Trigger Gate` claim requires recorded reviewer/meta-judge pass evidence, not only a synthetic smoke fixture.

## Current Validator Scope

- required architecture files and root/index placement
- compact line limits for `AGENTS.md`, index, and detail docs
- canonical loop consistency across map/index files
- required detail-document mappings
- deprecated contract names and old path references
- recursive TOML parse, required keys, category folder discovery, role name/file-name match
- allowed model tier, reasoning effort, sandbox mode, and category routing invariants
- canonical stage TOML inventory and exact stage return contracts
- stage artifact synthetic fixtures for orchestration, context, plan, aggregation, judgment, and rework request
- canonical stage prompts forbid non-owned stage artifacts and preserve required ledger markers
- mandatory stage skill `contract.json` files bind `$orchestrator`, `$task-planner`, `$worker-router`, `$task-distributor`, `$result-aggregator`, `$review-router`, and `$feedback-synthesizer` to validator-readable contracts
- hook-level contract checks run `validate-skill-contracts.py`; full final approval still runs `validate-agent-architecture.py`
- logical launch manifest versus physical active_passes schema separation
- runtime prompts enforce `launch_manifest_schema_gate` before handoff
- meta prompts require `source_contract_refs`, `contract_lookup_missing`, `aggregation_inputs`, `aggregation_ready=false`, and validation ownership/status markers
- synthetic routing-to-aggregation fixture for lane materialization and missing-lane classification
- `stage_passes`, `handoff_result.artifact_ref`, and `judgment_envelope` schema/doc parity
- `05-feedback-lifecycle.md`, `07-contracts-ledgers.md`, and validator constants stay aligned for `judgment_envelope`
- feedback fixture preserves loop carryover fields and blocks no-progress repeated feedback
- 2~4 pass feedback history fixture detects unchanged blocker/no-progress escape requirements
- runtime gate smoke executes positive/negative fixtures for invalid manifest, wrong stage owner, router materialization, blocked aggregation taxonomy/parity/source ref, feedback/final judgment, stale source/context lineage, previous-judgment loop lineage, active_passes validation, CLI exit codes, output-file paths, review waiver parity, aggregation missing-lane shape, and no-progress loop escape
- runtime gate smoke blocks missing specialist roles, canonical stage owners used as worker lanes, and non-review specialists used as review lanes
- session replay validation fails invalid `spawn_agent` calls that combine `fork_context=true` with explicit `agent_type`, failed spawn materialization including thread-limit failures, materialized children without matching `wait_agent` targets, closed-only child evidence, and sessions ending with open tool calls
- session replay synthetic fixtures fail prose-shaped aggregators, generic `worker` direct spawns, and final meta-judge prompts that lack `stage_passes`, `active_passes`, and reviewer evidence
- contract provenance mixin and review coverage fields stay first-class in stage artifacts
- documented specialist aliases resolve to real category TOML files
- logical lane `agent_category/agent_role` dependencies resolve to real TOML files
- unexpected top-level architecture `.md` files fail inventory checks
- required runtime prompt sections and critical lifecycle phrases
- canonical entrypoint delegation to `validators/docs.py`, `validators/prompt_contracts.py`, and `validators/contracts.py`

## Validator-To-Agent Mapping

| Validator item | Reads | Agent contract checked |
| --- | --- | --- |
| `$RequiredFiles` | `AGENTS.md`, `agent-architecture/*.md` | map/index/detail docs exist |
| `$RequiredText` | architecture markdown | shared artifact names and ledgers are documented |
| `$ForbiddenText` | architecture markdown + `agents/<category>/*.toml` | deprecated paths and field names do not return |
| `$TomlCheck.required` | `agents/<category>/*.toml` | each agent prompt has required TOML keys |
| `$TomlCheck.expected` | recursive category TOML catalog | model tier, reasoning effort, sandbox match allowed policy |
| `$PromptChecks` | architecture docs + meta-orchestration prompts | category router and lifecycle phrases remain discoverable |
| `$DocsModule` | `validators/docs.py` | map/index/detail docs and deprecated document tokens |
| `$PromptModule` | `validators/prompt_contracts.py` | TOML shape, runtime prompt hooks, launch manifest prompt gate |
| `$SkillContractsModule` | `validators/skill_contracts.py` | mandatory skill `contract.json` bindings and optional helper boundaries |
| `$ContractsModule` | `validators/contracts.py` | logical/physical ledger fixtures and feedback final-blocking fixture |
| `$RuntimeArtifactValidator` | `validate-runtime-artifact.py` | actual JSON artifact shape, branch, loop, and manifest validation |
| `$HarnessGate` | `harness_gate.py` | hard allow/block decision before next-stage handoff |
| `$HarnessHandoff` | `harness_handoff.py` | caller wiring that wraps stage output before any next-owner handoff |
| `$RuntimeGateSmoke` | `validate-runtime-gate-smoke.py` | positive/negative fixtures for runtime validator, gate, handoff, and CLI paths |

## Architecture Drift Signals

- `AGENTS.md` grows into a manual instead of a map.
- Category folder disappears or router docs fall back to flat `agents/*.toml` discovery.
- Detail docs duplicate stale or conflicting rules.
- Router wording says it physically creates children without caller materialization.
- `agent_id` and `submission_id` are merged or ambiguous.
- `aggregator` opens before child outputs or missing-lane classification.
- `meta-judge` approves with unclassified missing lanes.
- `meta-judge` emits final output while `feedback_required=true`.
- A runtime residue remains `running` or `pending_init` after artifact return.
- Repeated manual fixes are not converted into schema/tool/eval improvements.

## Improvement Rule

When a drift signal repeats twice, add or update one of: detail md contract, runtime TOML prompt, validation script, checklist/eval item, or architecture index link.

Do not bury repeated failures in a chat transcript only.

## Doc Gardening Rule

- `AGENTS.md` must stay concise.
- `AGENT-ARCHITECTURE.md` must stay an index.
- Detailed rules belong in numbered `agent-architecture/*.md` files.
- Obsidian notes are personal records only and must not be used as validation/test targets.

## Architecture Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true`. The top-level caller or harness owner must run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.


## Physical Execution Evidence

The trigger invariant is `architecture_required=true`: explicit architecture/orchestration/harness/agent-structure language and non-trivial audit, implementation, research, comparison, risky, multi-agent, or multi-artifact work must enter the physical stage chain before execution.

Runtime tests separate `logical_manifest_valid`, `physical_spawn_witness`, and `wait_registration`. A final/feedback path with only string refs must fail unless `stage_passes` and reviewer `handoff_result` evidence resolves mechanically.

`validate-session-runtime.py` replays Codex session JSONL and fails architecture claims when `context-manager` is physically spawned instead of using `codex-context-ledger`, main-agent role-pass control stages are physically spawned without `physical_control_override_required=true` evidence, fanout bursts exceed budget, `spawn_agent` failed including thread-limit failures, specialists were spawned without router manifest evidence, spawned children were not waited, `wait_agent` returned empty, reviewer/aggregator stages were prose-only, or final meta-judge prompts lack physical evidence bundles.

`close_agent` cleanup is not wait evidence. A completed close status can clean the process tree only after `wait_agent` has targeted the child or the lane has been explicitly classified.

MCP calls with error-shaped results are blocker or waiver evidence. They are not successful MCP evidence for architecture-required work.

Any phrase equivalent to "apply the same stages locally" is invalid for non-trivial architecture-claimed work. The correct failure output is `architecture_physical_execution_blocked=true`, not a simulated stage chain.

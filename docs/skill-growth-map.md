# Skill Growth Map

Last updated: 2026-06-16

## Evidence Base

- PR #9, "[codex] Require express direct cleanup scope", is open as a draft on branch `codex/express-direct-cleanup-scope` at `1a0db5475e7e89ea45da278deb05bd2d3342d372`. It extends the express-direct handoff with explicit `direct_workflow_scope.cleanup_actions` and documents the local-vs-remote branch cleanup distinction.
- PR #8, "[codex] Validate express direct handoff fields", was merged into `master` on 2026-06-14. It made express-direct `allowed_actions`, `excluded_actions`, and `express_direct_reason` required validator fields.
- PR #7, "Add compact orchestrator direct workflow", was merged into `master` on 2026-06-01. It added the `orchestrator -> direct-workflow` path, express-direct validation, contract/docs updates, and runtime smoke evidence for `build_next_stage_guidance('direct-workflow')`.
- PR #6, "Fix meta orchestration stage references", was merged into `master` on 2026-06-01. It replaced stale `task-planner` references with the current `task-designer` / `task-distributor` split across `agents/09-meta-orchestration`.
- PR #5, "Block unvalidated task design fallback", fixed validator exposure, stage packet shape guidance, and top-level orchestrator packet mismatches after runtime sessions exposed unvalidated fallback behavior.
- PR #4, "Split planning stages and add reentry evidence", introduced the task-designer/task-distributor split, `artifact_profile`, `reentry_cache`, sequential-thinking waiver evidence, and broader flow validation.
- GitHub review, inline review-comment, and issue-comment endpoints for PR #8 and PR #9 returned empty arrays on 2026-06-16. The recommendations below therefore rely on PR subjects, PR bodies, diffs, validation notes, branch state, and repeated automation findings rather than reviewer comments.

## Recommended Growth Areas

### 1. PR Evidence Packet Discipline

Evidence:
- PR #8 and PR #9 both changed express-direct contracts, but PR #9 is still open while `origin/master` points at PR #8's merge commit `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`.
- Recent automation runs repeatedly needed to explain which source was authoritative: GitHub PR metadata, `git ls-remote`, local remote-tracking refs, or the checked-out branch.
- PR #9's cleanup scope made branch cleanup a first-class concern, but the PR must still retain its remote head branch while review is pending.

Practice:
- Before opening a follow-up automation PR, produce a compact evidence packet with current open PRs, default-branch SHA, branch head SHA, review/comment counts, validation commands, and branch cleanup policy.
- State whether the new work is independent of open PRs or stacked on top of one, and cite the exact conflicting files if it is not independent.
- Keep local branch deletion separate from remote PR head branch deletion unless the PR has been merged or intentionally closed.

Done when:
- A PR body can prove its base, dependency relationship, review evidence, validation evidence, and cleanup choice without relying on memory from a prior automation run.

Repository drill:
- Use `docs/automation-pr-evidence-checklist.md` for the command set and PR-body evidence template.

### 2. Express-Direct Contract Layering

Evidence:
- PR #7 introduced `workflow_mode="express-direct"` and `next_owner="direct-workflow"` for simple, low-risk, single-lane work.
- PR #8 promoted express-direct scope/rationale from prose into validator-required packet fields.
- PR #9 extends that same packet surface with cleanup obligations, showing that compact paths still need explicit operational boundaries.

Practice:
- Maintain a field-by-field map for express-direct handoffs: routing fields, scope fields, rationale fields, cleanup fields, and forbidden completion claims.
- For every new field, add a paired invalid fixture: missing field, wrong type, empty list, and field present only in nested or top-level location when both are required.
- Keep compact-path changes small enough that a reviewer can see whether the field belongs in validator logic, docs, or PR-body evidence.

Done when:
- The express-direct decision and its follow-up obligations can be audited from packet fields and tests, not from implied workflow knowledge.

### 3. Branch State and Remote Drift Verification

Evidence:
- PR #6 and PR #7 were previously merged on GitHub while local refs could still appear stale under constrained fetch or credential conditions.
- On 2026-06-16, `git ls-remote` showed `refs/heads/master` at `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1` and PR #9's remote head at `1a0db5475e7e89ea45da278deb05bd2d3342d372`.

Practice:
- Compare local branch, remote-tracking branch, GitHub PR merge SHA, PR head SHA, and `git ls-remote` SHA before claiming merge state.
- Include fallback paths for blocked `git fetch`: GitHub connector PR metadata, GitHub web page, and `git ls-remote`.
- Record whether the source of truth is local Git, GitHub connector, REST API, or GitHub web before publishing conclusions.

Done when:
- You can explain the difference between branch head SHA, PR head SHA, base SHA, and merge commit SHA for a current PR without relying on a single tool.

### 4. Stale Reference Sweep Discipline

Evidence:
- PR #6 fixed repeated stale `task-planner` references after the canonical flow had already moved to `task-designer` and `task-distributor`.
- Earlier automation memory also showed the same stale-stage issue remaining in support-agent guidance after core architecture docs changed.

Practice:
- Create a sweep pattern for every canonical rename: exact string search, hyphen/underscore variants, TOML guidance blocks, README summaries, and generated mirror docs.
- Run the sweep before and after edits, and store the negative search evidence in the PR body.
- Treat support-agent guidance as part of the compatibility surface, not as secondary prose.

Done when:
- A future stage rename can be verified with one command list and one PR-body evidence block.

### 5. Validator Negative-Shape Testing

Evidence:
- PR #5 exists because runtime sessions exposed validator availability and packet wrapper mismatches.
- PR #8 added tests for direct-workflow routing, including invalid express-direct packets where required scope/rationale fields are absent or malformed.
- PR #4 and PR #5 repeatedly tightened the distinction between valid schema shape and valid completion evidence.

Practice:
- For each validator, add paired positive and negative fixtures.
- Negative fixtures should cover wrong owner, missing wrapper fields, conflicting nested fields, empty evidence lists, and valid-looking placeholders with the wrong type.
- Name tests by contract risk, not by implementation helper name.

Done when:
- A new packet feature cannot be merged with only a happy-path test.

### 6. Runtime Tool Exposure and Approval Hygiene

Evidence:
- PR #5 added approval entries for `validate_task_design`, `validate_execution_plan`, and `validate_review_plan`.
- The same PR blocked task-designer from emitting unvalidated fallback design text when the required validator is not callable.
- PR #7 repeated runtime sync and smoke validation as part of the merge evidence.

Practice:
- Maintain a tool-surface smoke check that separates four cases: defined but not callable, callable but not approved, approved but stale, and callable with valid sequence.
- Run the approval helper `-Check` before PR publication and `-SelfTest` before changing TOML regex logic.
- Include the current runtime source path in validation notes when the local repo and runtime checkout can drift.

Done when:
- You can diagnose a missing validator as approval drift, runtime-source drift, session hot-reload drift, or contract drift within one pass.

## Next Concrete Drill

Use the PR evidence packet checklist before the next automation-created PR. It directly addresses the newest recurring pattern: compact workflow changes now span PR #7, PR #8, and open PR #9, while merge state, review evidence, validation evidence, and branch cleanup policy can drift independently.

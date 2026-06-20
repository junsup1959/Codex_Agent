# Skill Growth Map

Last updated: 2026-06-20

## Evidence Base

- PR #10, "[codex] Document automation PR evidence checklist", is open as a draft on branch `codex/pr-evidence-growth-map-20260616`. It adds this growth map and the automation PR evidence checklist, and is intentionally documentation-only so it does not overlap PR #9's validator/test files. Because PR #10 updates this same document, fetch the live PR head SHA before citing it.
- PR #9, "[codex] Require express direct cleanup scope", is open as a draft on branch `codex/express-direct-cleanup-scope` at `1a0db5475e7e89ea45da278deb05bd2d3342d372`. It extends the express-direct handoff with explicit `direct_workflow_scope.cleanup_actions` and documents the local-vs-remote branch cleanup distinction.
- PR #8, "[codex] Validate express direct handoff fields", was merged into `master` on 2026-06-14. It made express-direct `allowed_actions`, `excluded_actions`, and `express_direct_reason` required validator fields.
- PR #7, "Add compact orchestrator direct workflow", was merged into `master` on 2026-06-01. It added the `orchestrator -> direct-workflow` path, express-direct validation, contract/docs updates, and runtime smoke evidence for `build_next_stage_guidance('direct-workflow')`.
- PR #6, "Fix meta orchestration stage references", was merged into `master` on 2026-06-01. It replaced stale `task-planner` references with the current `task-designer` / `task-distributor` split across `agents/09-meta-orchestration`.
- PR #5, "Block unvalidated task design fallback", fixed validator exposure, stage packet shape guidance, and top-level orchestrator packet mismatches after runtime sessions exposed unvalidated fallback behavior.
- PR #4, "Split planning stages and add reentry evidence", introduced the task-designer/task-distributor split, `artifact_profile`, `reentry_cache`, sequential-thinking waiver evidence, and broader flow validation.
- PR #10 review threads were empty on 2026-06-20.
- GitHub's combined PR discussion fetch returned no comments for PR #8, PR #9, and PR #10 on 2026-06-20 and 2026-06-19. Earlier automation notes also recorded no fetched comments or review threads for PR #8 and PR #9 on 2026-06-16. The recommendations below therefore rely on PR subjects, PR bodies, diffs, validation notes, branch state, and repeated automation findings rather than reviewer comments.
- The local automation environment currently has no `gh` CLI; publication must combine Git operations (`push`/branch handling) with GitHub connector PR metadata operations (create/update comments/labels).

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

### 3. Open PR Stack Hygiene

Evidence:
- PR #9 and PR #10 are both open draft PRs against `master` at `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`.
- PR #9 changes `AGENTS.md`, `agent-architecture/09-runtime-orchestration-steps.md`, `mcp/context-ledger/src/context_ledger_mcp/validation.py`, `mcp/context-ledger/tests/test_ledger.py`, and `skills/orchestrator/SKILL.md`.
- PR #10 changes only `docs/automation-pr-evidence-checklist.md` and `docs/skill-growth-map.md`, so it is independent of PR #9 by file ownership even though both are part of the same express-direct automation learning thread.

Practice:
- Before creating or updating an automation PR, classify the relationship to every open automation PR as `independent`, `stacked`, or `blocked`.
- Use changed-file lists, not just PR titles, to prove the relationship. If the relationship is `stacked`, name the upstream PR and base branch explicitly in the PR body.
- Avoid creating another PR for the same growth-map artifact when an open draft PR already owns that file; update the existing draft instead.

Done when:
- Multiple open automation PRs can be reviewed in any order without hidden file conflicts, duplicate documents, or ambiguous merge sequencing.

### 4. Branch State and Remote Drift Verification

Evidence:
- PR #6 and PR #7 were previously merged on GitHub while local refs could still appear stale under constrained fetch or credential conditions.
- On 2026-06-18, `git ls-remote` showed `refs/heads/master` at `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1` and PR #9's remote head at `1a0db5475e7e89ea45da278deb05bd2d3342d372`. PR #10 updates this document on its own head branch, so its current head SHA should be fetched live before publication.
- PR #9/#10 workflows currently require a fallback publication path: Git handles branch, commit, and push; GitHub connector handles PR metadata/actions when `gh` CLI is unavailable.

Practice:
- Compare local branch, remote-tracking branch, GitHub PR merge SHA, PR head SHA, and `git ls-remote` SHA before claiming merge state.
- Include fallback paths for blocked `git fetch`: GitHub connector PR metadata, GitHub web page, and `git ls-remote`.
- Record whether the source of truth is local Git, GitHub connector, REST API, or GitHub web before publishing conclusions.

Done when:
- You can explain the difference between branch head SHA, PR head SHA, base SHA, and merge commit SHA for a current PR without relying on a single tool.

### 5. Stale Reference Sweep Discipline

Evidence:
- PR #6 fixed repeated stale `task-planner` references after the canonical flow had already moved to `task-designer` and `task-distributor`.
- Earlier automation memory also showed the same stale-stage issue remaining in support-agent guidance after core architecture docs changed.

Practice:
- Create a sweep pattern for every canonical rename: exact string search, hyphen/underscore variants, TOML guidance blocks, README summaries, and generated mirror docs.
- Run the sweep before and after edits, and store the negative search evidence in the PR body.
- Treat support-agent guidance as part of the compatibility surface, not as secondary prose.

Done when:
- A future stage rename can be verified with one command list and one PR-body evidence block.

### 6. Validator Negative-Shape Testing

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

### 7. Runtime Tool Exposure and Approval Hygiene

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

### 8. Publication Fallback Discipline (No `gh` CLI)

Evidence:
- PR #8 is merged and PR #9/#10 are current drafts in a local environment with no `gh` CLI.
- PR #9 added cleanup behavior that retains remote PR head branch while deleting local branch after publish.
- PR #10 is documentation-only and currently relies on an open-draft PR workflow, so branch lifecycle evidence is part of the recommendation, not implicit release behavior.
- Combined PR/review/comment fetches were empty for PR #8, PR #9, and PR #10 on 2026-06-20 (and 2026-06-19), so review evidence is represented by explicit fetch results and counts only.

Practice:
- Define a hard publication split:
  1. Use Git for branch creation/updates, commits, and `git push`.
  2. Use GitHub connector APIs for PR metadata, labels, comments, and PR-state reads when `gh` is unavailable.
  3. Record source-of-truth for each data point (`git`, `git ls-remote`, connector payload, connector PR body state).
- Set explicit cleanup policy in PR docs and automation evidence:
  - Local branch: delete only after a successful publication push when PR remains draft/open.
  - Remote PR head branch: retain until merge/close decision is final.
- Treat "no review comments returned" as explicit evidence, and do not infer review intent beyond the returned counts.

Done when:
- The same recommendation can be executed from an environment without `gh` and still prove publication, cleanup choice, and review-state evidence without assumptions.

### 9. Evidence Freshness and Timestamp Discipline

Evidence:
- PR #10 is a docs-only follow-up that references itself (`docs/automation-pr-evidence-checklist.md` and `docs/skill-growth-map.md`), so automation repeatedly had to avoid stale `checked_at` and stale head SHA/date values in self-referential evidence.
- PR #10 head hash `6136e59` is fixed historical evidence observed at 2026-06-20T00:05:22Z before this follow-up commit; current PR head values must be re-fetched live before each evidence claim to prevent stale citations and date drift.
- PR discussion/threads for PR #10 were empty on 2026-06-20, matching the prior-day empty comment runs; this can only be trusted if evidence has explicit freshness context.

Practice:
- Capture `checked_at` for every evidence run and persist it in PR body and automation memory.
- For each PR claim, record source-of-truth (`git`, `git ls-remote`, connector payload, REST, or GitHub UI).
- Record freshness trigger (`before-open`, `before-update`, `before-push`, `before-merge-check`) and refresh policy when trigger time is exceeded.
- For each SHA/date value, explicitly mark capture mode: `live-fetched` (current lookup) or `fixed` (historical reference with reason + TTL).

Done when:
- A future reviewer can detect, per evidence item, whether PR state is current or intentionally historical without asking for a fresh fetch.

## Next Concrete Drill

Use the PR evidence packet checklist before the next automation-created PR, and include `checked_at`, evidence source, freshness trigger, and SHA/date mode (`live-fetched` or `fixed`) in the PR-body evidence block. It directly addresses the recurring pattern in PR #10 where review fetches stayed empty and branch/SHA fields can look stable while still becoming stale.

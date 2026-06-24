# Skill Growth Map

Last updated: 2026-06-24

## Evidence Base

- PR #10, "[codex] Document automation PR evidence checklist", is open as a draft on branch `codex/pr-evidence-growth-map-20260616`. It adds this growth map and the automation PR evidence checklist, and is intentionally documentation-only so it does not overlap PR #9's validator/test files. Because PR #10 updates this same document, fetch the live PR head SHA before citing it instead of storing it as a fixed value here. This PR is also the source for its own evidence protocol, so publication updates must verify post-push self-refresh before claiming current evidence.
- PR #9, "[codex] Require express direct cleanup scope", is open as a draft on branch `codex/express-direct-cleanup-scope` at `1a0db5475e7e89ea45da278deb05bd2d3342d372`. It extends the express-direct handoff with explicit `direct_workflow_scope.cleanup_actions` and documents the local-vs-remote branch cleanup distinction.
- PR #8, "[codex] Validate express direct handoff fields", was merged into `master` on 2026-06-14. It made express-direct `allowed_actions`, `excluded_actions`, and `express_direct_reason` required validator fields.
- PR #7, "Add compact orchestrator direct workflow", was merged into `master` on 2026-06-01. It added the `orchestrator -> direct-workflow` path, express-direct validation, contract/docs updates, and runtime smoke evidence for `build_next_stage_guidance('direct-workflow')`.
- PR #6, "Fix meta orchestration stage references", was merged into `master` on 2026-06-01. It replaced stale `task-planner` references with the current `task-designer` / `task-distributor` split across `agents/09-meta-orchestration`.
- PR #5, "Block unvalidated task design fallback", fixed validator exposure, stage packet shape guidance, and top-level orchestrator packet mismatches after runtime sessions exposed unvalidated fallback behavior.
- PR #4, "Split planning stages and add reentry evidence", introduced the task-designer/task-distributor split, `artifact_profile`, `reentry_cache`, sequential-thinking waiver evidence, and broader flow validation.
- PR #10 inline comments and issue comments were empty via connector on 2026-06-22.
- On 2026-06-23, PR #10 pre-push head was `cbc5ee20550ae0be035d0e182baa82c607f192ea`; live fetch is still required after push.
- GitHub's combined PR discussion fetch returned no reviews, inline comments, or issue comments for PR #8, PR #9, and PR #10 on 2026-06-22; PR #8, PR #9, and PR #10 also had empty review-thread connector results. The recommendations below therefore rely on PR subjects, PR bodies, diffs, validation notes, branch state, and repeated automation findings rather than reviewer comments.
- The local automation environment currently has no `gh` CLI; publication must combine Git operations (`push`/branch handling) with GitHub connector PR metadata operations (create/update comments/labels).
- On 2026-06-24, PR #9 remained open draft at `1a0db5475e7e89ea45da278deb05bd2d3342d372` and PR #10 remained open draft on branch `codex/pr-evidence-growth-map-20260616`, whose current head must be live-fetched before citation; connector comment fetches and review-thread fetches for both PRs returned empty arrays.
- On 2026-06-24, a GitHub PR list page rendered `0 Open / 7 Closed` and did not show PR #8-#10.
- The GitHub PR API showed PR #9 and PR #10 as open drafts.
- `git ls-remote` separately showed their remote branch heads and `origin/master` at PR #8's merge commit. Treat this as an evidence-surface mismatch to reconcile, not as a reason to trust the first surface checked.

## Recommended Growth Areas

### 1. Open PR Dependency and Rebase Readiness

Evidence:
- PR #9 and PR #10 are both open drafts against the same base SHA `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`, so they are independent by file ownership but still part of the same publication queue.
- PR #9 changes `AGENTS.md`, `agent-architecture/09-runtime-orchestration-steps.md`, `mcp/context-ledger/src/context_ledger_mcp/validation.py`, `mcp/context-ledger/tests/test_ledger.py`, and `skills/orchestrator/SKILL.md`; PR #10 changes only docs files.
- PR #9 and PR #10 must still pass rebase-readiness checks before any publish/update because both target the same base SHA at the same moment.

Practice:
- Before updating an existing automation PR, collect an explicit dependency matrix for all open automation PRs:
  - PR id, title, state, base branch, base SHA, head SHA, labels
  - changed-file overlap result (`independent`, `stacked`, or `blocked`)
  - compare/readiness (`ahead`, `behind`, conflict-ready, rebase-ready, blocked)
  - review state (`reviews`, `inline comments`, `issue comments`)
  - evidence source for each field (`git`, `git ls-remote`, connector payload, REST, UI)
- Use changed-file ownership as the primary dependency signal; only use review/comment state to elevate from `independent` to `blocked`.
- When `compare/readiness` is `needs-rebase`, require a rebase/refresh step and a second compare check before any PR-body updates.
- Add one matrix row in the PR body and a short section in automation evidence showing whether each open PR is independent, stacked, blocked, or rebase-needed.

Done when:
- Every follow-up PR update includes an explicit matrix of open-PR dependency plus compare state and rebase readiness.
- No PR update is published while any open dependency is `blocked` or `needs-rebase` unless the update includes the explicit rebase/retune action.

### 2. PR Evidence Packet Discipline

Evidence:
- PR #8 and PR #9 both changed express-direct contracts, but PR #9 is still open while `origin/master` points at PR #8's merge commit `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`.
- Recent automation runs repeatedly needed to explain which source was authoritative: GitHub PR metadata, `git ls-remote`, local remote-tracking refs, or the checked-out branch.
- PR #9's cleanup scope made branch cleanup a first-class concern, but the PR must still retain its remote head branch while review is pending.

Practice:
- Before opening a follow-up automation PR, produce a compact evidence packet with current open PRs, default-branch SHA, branch head SHA, review/comment counts, validation commands, and branch cleanup policy.
- State whether the new work is independent of open PRs or stacked on one, and cite the exact conflicting files if it is not independent.
- Keep local branch deletion separate from remote PR head branch deletion unless the PR has been merged or intentionally closed.

Done when:
- A PR body can prove its base, dependency relationship, review evidence, validation evidence, and cleanup choice without relying on memory from a prior automation run.

Repository drill:
- Use `docs/automation-pr-evidence-checklist.md` for the command set and PR-body evidence template.

### 3. Express-Direct Contract Layering

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

### 4. Open PR Stack Hygiene

Evidence:
- PR #9 and PR #10 are both open draft PRs against `master` at `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`.
- PR #9 changes `AGENTS.md`, `agent-architecture/09-runtime-orchestration-steps.md`, `mcp/context-ledger/src/context_ledger_mcp/validation.py`, `mcp/context-ledger/tests/test_ledger.py`, and `skills/orchestrator/SKILL.md`.
- PR #10 changes only `docs/automation-pr-evidence-checklist.md` and `docs/skill-growth-map.md`, so it is independent of PR #9 by file ownership even though both target the same base.

Practice:
- Before creating or updating an automation PR, classify the relationship to every open automation PR as `independent`, `stacked`, or `blocked`.
- Use changed-file lists, not just PR titles, to prove the relationship.
- If the relationship is `stacked`, name the upstream PR and base branch explicitly in the PR body.
- Before publication updates, also run a compare-state readiness check for both `stacked` and `independent` candidates to detect required rebase.
- Avoid creating another PR for the same growth-map artifact when an open draft PR already owns that file; update the existing draft instead.

Done when:
- Multiple open automation PRs can be reviewed in any order without hidden file conflicts, duplicate documents, or ambiguous merge sequencing.

### 5. Branch State and Remote Drift Verification

Evidence:
- PR #6 and PR #7 were previously merged on GitHub while local refs could still appear stale under constrained fetch or credential conditions.
- Current evidence for this run uses live `git ls-remote` checks plus connector metadata; PR #9 remote head was observed as `1a0db5475e7e89ea45da278deb05bd2d3342d372`, and PR #10 head must be fetched live from its branch before publication.
- PR #9/#10 workflows currently require a fallback publication path: Git handles branch, commit, and push; GitHub connector handles PR metadata, labels/comments when `gh` CLI is unavailable.

Practice:
- Compare local branch, remote-tracking branch, GitHub PR merge SHA, PR head SHA, and `git ls-remote` SHA before claiming merge state.
- Include fallback paths for blocked `git fetch`: GitHub connector PR metadata, GitHub web page, and `git ls-remote`.
- Record whether the source of truth is local Git, GitHub connector, REST API, or GitHub web before publishing conclusions.

Done when:
- You can explain the difference between branch head SHA, PR head SHA, base SHA, and merge commit SHA for a current PR without relying on a single tool.

### 6. Stale Reference Sweep Discipline

Evidence:
- PR #6 fixed repeated stale `task-planner` references after the canonical flow had already moved to `task-designer` and `task-distributor`.
- Earlier automation notes also showed stale-stage wording remaining in support-agent guidance after architecture docs moved.

Practice:
- Create a sweep pattern for every canonical rename: exact string search, hyphen/underscore variants, TOML guidance blocks, README summaries, and generated mirror docs.
- Run the sweep before and after edits, and store negative search evidence in the PR body.
- Treat support-agent guidance as part of the compatibility surface, not as secondary prose.

Done when:
- A future stage rename can be verified with one command list and one PR-body evidence block.

### 7. Validator Negative-Shape Testing

Evidence:
- PR #5 exists because runtime sessions exposed validator availability and packet wrapper mismatches.
- PR #8 added tests for direct-workflow routing, including invalid express-direct packets where required scope/rationale fields are absent or malformed.
- PR #4 and PR #5 repeatedly tightened the distinction between valid schema shape and valid completion evidence.

Practice:
- For each validator, add paired positive and negative fixtures.
- Negative fixtures should cover wrong owner, missing wrapper fields, conflicting nested fields, empty evidence lists, and valid-looking placeholders with wrong type.
- Name tests by contract risk, not by implementation helper name.

Done when:
- A new packet feature cannot be merged with only a happy-path test.

### 8. Runtime Tool Exposure and Approval Hygiene

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

### 9. Publication Fallback Discipline (No `gh` CLI)

Evidence:
- PR #8 is merged and PR #9/#10 are current drafts in a local environment with no `gh` CLI.
- PR #9 added cleanup behavior that retains remote PR head branch while deleting local branch after publish.
- PR #10 is documentation-only and currently relies on an open-draft PR workflow, so branch lifecycle evidence is part of the recommendation, not implicit release behavior.
- Combined PR/review/comment fetches were empty for PR #8, PR #9, and PR #10 on 2026-06-22, so review evidence is represented by explicit fetch results and counts only.

Practice:
- Define a hard publication split:
  1. Use Git for branch creation/updates, commits, and `git push`.
  2. Use GitHub connector APIs for PR metadata, labels, comments, and PR-state reads when `gh` is unavailable.
  3. Record source-of-truth for each data point (`git`, `git ls-remote`, connector payload, connector PR body state).
- Set explicit cleanup policy in PR docs and automation evidence:
  - Local branch: delete only after successful publication push when PR remains draft/open.
  - Remote PR head branch: retain until merge/close decision is final.
- Treat "no review comments returned" as explicit evidence, and do not infer review intent beyond returned counts.

Done when:
- The same recommendation can be executed from an environment without `gh` and still prove publication, cleanup choice, and review-state evidence without assumptions.

### 10. Self-Referential PR Evidence Freshness

Evidence:
- PR #10 is a docs-only follow-up that references itself (`docs/automation-pr-evidence-checklist.md` and `docs/skill-growth-map.md`), so automation repeatedly had to avoid stale `checked_at` and stale head SHA/date values in self-referential evidence.
- PR #10 head for each run must be live-fetched before evidence claims; do not store the current PR's own moving head SHA as a fixed value in this document.
- PR #10 inline comments and issue comments were empty on 2026-06-22; this can only be trusted if evidence has explicit freshness context.
- PR #10's branch can be pushed successfully while the PR body still cites a previous current head or previous `checked_at`, so body refresh is a separate publication obligation.

Practice:
- Before updating a docs-only PR body that cites itself, capture pre-push and post-push values for `checked_at`, PR head SHA, and the PR body evidence block.
- Use this sequence: push, refetch remote head, regenerate evidence, overwrite PR body, then verify stale values were removed.
- Treat stale `checked_at` or stale current-head values in the PR body as an update failure, even when compare/readiness and review/comment data are otherwise valid.
- Keep historical SHAs only when they are explicitly marked `fixed` with a reason; current PR head values must be `live-fetched`.

Done when:
- A future reviewer can tell that the PR body was refreshed after the latest push and no longer carries previous live-evidence values as if they were current.

### 11. Publication Closure Verification

Evidence:
- PR #9 introduced cleanup-actions that separate local branch cleanup from remote PR-head retention during publication.
- PR #10 is self-referential to these docs and requires post-push PR-body refresh to keep evidence current.
- Current run context requires closure checks for PR #10 after every push: labels retrieved from GitHub metadata, body head updated, local cleanup completed, remote branch retained for draft review, and memory sync completed.

Practice:
- Before finalizing PR #10, execute closure in order:
  1. Push follow-up commit(s) to existing PR #10 branch.
  2. Fetch `origin/codex/pr-evidence-growth-map-20260616` and capture the post-push head.
  3. Fetch PR #10 metadata through the GitHub connector or REST API and capture labels.
  4. Rewrite PR body and re-fetch it to verify the post-push head and labels are reflected as live evidence.
  5. Verify PR body has no stale pre-push `checked_at`/head values.
  6. Apply local branch cleanup only after successful push/body refresh.
  7. Keep remote PR branch retained while PR #10 remains open draft.
  8. Append the same closure facts to automation memory.

Done when:
- PR #10 body shows post-push `head` and labels.
- PR body stale-check passes for prior `checked_at`/head.
- Local branch cleanup is recorded with timestamp/reason.
- Remote PR branch is recorded as retained.
- Automation memory entries match PR body for labels/head/cleanup state/sources.

### 12. Evidence Surface Reconciliation

Evidence:
- On 2026-06-24, the GitHub PR list page rendered `0 Open / 7 Closed` and omitted PR #8-#10.
- Connector reads returned PR #9 and PR #10 as open drafts.
- `git ls-remote` separately showed their remote head branches.
- Automation memory also contained prior #10 publication facts that were not present on `origin/master`, because those docs live only on the open PR #10 branch until merge.
- PR #9 and PR #10 review/comment fetches returned empty arrays on 2026-06-24, so there are still no reviewer comments to interpret; the new learning comes from conflicting repository-state surfaces, not review feedback.

Practice:
- Before making a recommendation from "latest PRs", check at least three surfaces when they are available: GitHub connector PR payload, `git ls-remote` branch heads, and local `origin/*` refs after fetch.
- If GitHub UI/search output disagrees with connector/API or Git data, record the disagreement in the evidence packet and choose the source that directly answers the claim:
  - PR open/closed state: connector/API PR payload.
  - Remote branch existence/head: `git ls-remote`.
  - Local checkout state: `git status`, `git branch -vv`, and `git rev-parse`.
  - Published doc availability on default branch: `origin/master` file tree, not the open PR branch.
- For automation memory, classify each prior fact as `merged-current`, `open-pr-current`, or `historical-only` before reusing it in a PR body.
- When a branch was created only as a temporary publication helper, delete it locally before final reporting and keep the remote PR branch only when an open draft still needs it.

Done when:
- A future run can explain why PR #10 docs exist on the PR branch but not on `origin/master`, why PR #9/#10 are still current despite a stale PR list page, and which command or connector result supports each claim.
- The PR body and automation memory agree on two separate labels: memory facts use `merged-current`, `open-pr-current`, `historical-only`, or `superseded`, while live evidence values declare `live-fetched` or `fixed`.

## Next Concrete Drill

Before the next PR update, execute the closure sequence for PR #10 and add evidence-surface reconciliation: push -> fetch live head with Git -> fetch labels with GitHub metadata -> PR-body rewrite -> re-fetch -> stale-check -> local cleanup -> automation-memory sync -> compare GitHub UI/API/Git surfaces -> final readiness checks.

# Skill Growth Map

Last updated: 2026-07-02

- On 2026-07-02, PR #9 and PR #10 head branches were retired after explicit merge-state and remote-head checks.
  - `git push origin --delete codex/express-direct-cleanup-scope codex/pr-evidence-growth-map-20260616` was executed after both PRs were confirmed merged.
  - `git ls-remote` was re-run afterward and returned only `codex/post-merge-branch-retirement-20260701` for `origin` PR-head scope.
  - PR #11 remains open draft at branch `codex/post-merge-branch-retirement-20260701` (head `bf419563318156daf3ca3eb844ef0ba680da2e12`), so it is retained under the current open/draft guardrail.
- On 2026-06-26, PR #9 ("[codex] Require express direct cleanup scope") and PR #10 ("[codex] Document automation PR evidence checklist") were merged into `master`; before the 2026-07-02 retirement action, both remote head branches were still visible from `git ls-remote` as `codex/express-direct-cleanup-scope` and `codex/pr-evidence-growth-map-20260616`.
  - Post-merge interpretation: treat remaining remote head branches as post-merge retirement evidence, not open-draft evidence.
  - This run moved those retention candidates into completed post-merge branch-retirement evidence.

## Evidence Base

Note: all explicit `open draft` status references below are historical unless explicitly labeled as current in a later dated bullet.

- PR #10, "[codex] Document automation PR evidence checklist", was open as a draft on branch `codex/pr-evidence-growth-map-20260616`; it is now merged into `master` at `b05b71c29befc10f43a77441711cbe9f5f9f7f0d` (2026-06-26T12:50:20Z). It adds this growth map and the automation PR evidence checklist, and is intentionally documentation-only so it does not overlap PR #9's validator/test files. Because PR #10 updates this same document, fetch the live PR head SHA before citing it instead of storing it as a fixed value here. This PR is also the source for its own evidence protocol, so publication updates must verify post-push self-refresh before claiming current evidence.
- PR #9, "[codex] Require express direct cleanup scope", was open as a draft on branch `codex/express-direct-cleanup-scope` at `1a0db5475e7e89ea45da278deb05bd2d3342d372`; it is now merged into `master` at `23c9a929910d9265f84eee0d5fcb018f32502370` (2026-06-26T12:49:57Z). It extends the express-direct handoff with explicit `direct_workflow_scope.cleanup_actions` and documents the local-vs-remote branch cleanup distinction.
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
- The GitHub PR API historically showed PR #9 and PR #10 as open drafts.
- `git ls-remote` separately showed their remote branch heads and `origin/master` at PR #8's merge commit. Treat this as an evidence-surface mismatch to reconcile, not as a reason to trust the first surface checked.
- On 2026-06-25, PR #9 remained open draft at `1a0db5475e7e89ea45da278deb05bd2d3342d372`; PR #10 remained open draft on branch `codex/pr-evidence-growth-map-20260616` with pre-push head `952bba7d13f96224f5146f3a971aa2582b40f519`.
- Connector review, combined comment, and review-thread reads for PR #9 and PR #10 returned empty arrays on 2026-06-25, so the next growth target is still based on PR topics, branch state, PR-body evidence, and repeated automation-memory freshness issues rather than reviewer prose.
- The 2026-06-24 automation memory entry contains valid historical closure facts for the previous run, but those facts are not automatically current after the next PR #10 push. Treat automation memory as an input that must be reclassified before reuse, not as a live source of PR state.

## Recommended Growth Areas

### 1. Open PR Dependency and Rebase Readiness

Evidence:
- PR #9 and PR #10 were both open drafts against the same base SHA `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1` and later merged; they remain independently owned by file and now sit in post-merge history.
- PR #9 changes `AGENTS.md`, `agent-architecture/09-runtime-orchestration-steps.md`, `mcp/context-ledger/src/context_ledger_mcp/validation.py`, `mcp/context-ledger/tests/test_ledger.py`, and `skills/orchestrator/SKILL.md`; PR #10 changes only docs files.
- Historical publication updates for PR #9 and PR #10 needed rebase-readiness checks because both targeted the same base SHA at the same moment.

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
- PR #8 and PR #9 both changed express-direct contracts; PR #9 is now merged, so its cleanup guidance has moved from open-PR retention to post-merge remote-head retirement.
- Recent automation runs repeatedly needed to explain which source was authoritative: GitHub PR metadata, `git ls-remote`, local remote-tracking refs, or the checked-out branch.
- PR #9's cleanup scope made branch cleanup a first-class concern, and the merged remote head branches required explicit retirement evidence before deletion.

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
- PR #9 and PR #10 were both open draft PRs against `master` at `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1` before merging.
- PR #9 changes `AGENTS.md`, `agent-architecture/09-runtime-orchestration-steps.md`, `mcp/context-ledger/src/context_ledger_mcp/validation.py`, `mcp/context-ledger/tests/test_ledger.py`, and `skills/orchestrator/SKILL.md`.
- PR #10 changes only `docs/automation-pr-evidence-checklist.md` and `docs/skill-growth-map.md`, so it is independent of PR #9 by file ownership even though both target the same base.

Practice:
- Before creating or updating an automation PR, classify the relationship to every open automation PR as `independent`, `stacked`, or `blocked`.
- Use changed-file lists, not just PR titles, to prove the relationship.
- If the relationship is `stacked`, name the upstream PR and base branch explicitly in the PR body.
- Before publication updates, also run a compare-state readiness check for both `stacked` and `independent` candidates to detect required rebase.
- Avoid creating another PR for the same growth-map artifact when an open draft PR already owns that file; after merge, treat any follow-up as a new post-merge cleanup PR.

Done when:
- Multiple open automation PRs can be reviewed in any order without hidden file conflicts, duplicate documents, or ambiguous merge sequencing.

### 5. Branch State and Remote Drift Verification

Evidence:
- PR #6 and PR #7 were previously merged on GitHub while local refs could still appear stale under constrained fetch or credential conditions.
- Current evidence for this run uses live `git ls-remote` checks plus connector metadata; PR #9 remote head was observed as `1a0db5475e7e89ea45da278deb05bd2d3342d372`, and PR #10 remote head was observed as `a2b9e9eb22df56bfe691fb2156dc28f3f7e75120` after merge.
- PR #9/#10 workflows required a fallback publication path while open; post-merge, remote head retention/deletion is now tracked as retirement evidence.

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
- PR #8, PR #9, and PR #10 are all merged; no `gh` CLI is available in this environment.
- PR #9 added cleanup behavior that retains remote PR head branch while deleting local branch after publish.
- PR #10 was documentation-only and required an open-draft workflow while open, while merged-branch retirement evidence is now the operational model.
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
- PR #10 head for each run was live-fetched before evidence claims; do not store a moving head SHA as a fixed current value in this document.
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
- Historical (pre-merge): PR #10 was self-referential to these docs and required post-push PR-body refresh to keep evidence current.
- Historical PR #10 draft updates required closure checks after every push: labels retrieved from GitHub metadata, body head updated, local cleanup completed, remote branch retained for draft review, and memory sync completed.

Practice:
- Before finalizing PR #10, execute closure in order:
  1. Push follow-up commit(s) to existing PR #10 branch.
  2. Fetch `origin/codex/pr-evidence-growth-map-20260616` and capture the post-push head.
  3. Fetch PR #10 metadata through the GitHub connector or REST API and capture labels.
  4. Rewrite PR body and re-fetch it to verify the post-push head and labels are reflected as live evidence.
  5. Verify PR body has no stale pre-push `checked_at`/head values.
  6. Apply local branch cleanup only after successful push/body refresh.
  7. Keep remote PR branch retained while PR #10 is open; once merged, record the remote-branch action as post-merge branch retirement evidence.
  8. Append the same closure facts to automation memory.

Done when:
- PR #10 body shows post-push `head` and labels.
- PR body stale-check passes for prior `checked_at`/head.
- Local branch cleanup is recorded with timestamp/reason.
- Remote PR branch action is recorded as `retained` while open or `deleted|retained` after merge, with the reason and evidence source.
- Automation memory entries match PR body for labels/head/cleanup state/sources.

### 12. Evidence Surface Reconciliation

Evidence:
- On 2026-06-24, the GitHub PR list page rendered `0 Open / 7 Closed` and omitted PR #8-#10.
- Connector reads returned PR #9 and PR #10 as open drafts during the pre-merge phase; post-merge evidence now tracks branch retirement.
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
- For automation memory, classify each prior fact as `merged-current`, `open-pr-current`, `historical-only`, or `superseded` before reusing it in a PR body.
- When a branch was created only as a temporary publication helper, delete it locally before final reporting; keep remote PR branches while an open draft needs them, then reclassify them for retirement once the PR is merged or closed.

Done when:
- A future run can explain whether PR #10 docs are on `origin/master`, whether PR #9/#10 are merged or still open, and which command or connector result supports each claim.
- The PR body and automation memory agree on two separate labels: memory facts use `merged-current`, `open-pr-current`, `historical-only`, or `superseded`, while live evidence values declare `live-fetched` or `fixed`.

### 13. Automation Memory Fact Expiration

Evidence:
- The automation memory for 2026-06-24 correctly recorded PR #10's then-current head, labels, local branch cleanup, remote branch retention, and validation state.
- Historical (pre-merge): PR #10 was self-referential and kept moving on the same branch, so the same memory facts became stale immediately after a new push unless they were reclassified.
- PR #10's body now needs to reconcile three kinds of evidence at once: live connector state, live Git remote state, and prior automation memory that may only describe the previous run.

Practice:
- Before reusing any automation memory line in a PR body, classify it as `open-pr-current`, `merged-current`, `historical-only`, or `superseded`.
- Attach an expiration trigger to memory-derived live facts: `after-push`, `after-merge`, `after-close`, or `after-rebase`.
- Only copy memory facts into PR body evidence when the current connector or Git check confirms them; otherwise cite the memory entry as historical context and replace current values with live-fetched values.
- Add one explicit parity check after PR-body refresh: current PR head, labels, local branch action, and remote branch retention must match the latest automation memory entry written in this run.

Done when:
- A future run can explain which facts came from automation memory, which were refreshed live, and which old memory facts expired after the new push.
- PR #10 body and automation memory no longer reuse previous-run head SHAs, `checked_at` values, or cleanup claims as live evidence without a fresh source.

### 14. Post-Merge Remote PR Head Retirement

Evidence:
- On 2026-06-26, PR #9 and PR #10 were both merged, but `git ls-remote` still reported their remote branches (`codex/express-direct-cleanup-scope`, `codex/pr-evidence-growth-map-20260616`) before the 2026-07-02 retirement execution.
- PR #9 established cleanup-action framing: local branch cleanup is controlled differently from remote PR-head lifecycle after publish.
- PR #10's self-referential update work repeatedly required explicit local-vs-remote cleanup capture; that same mechanism now needs a merged-PR retirement branch for consistency.

Practice:
- Classify each PR before cleanup with a fixed state tuple:
  - `pr_state`: `merged|closed|open`
  - `pr_open_for_update`: `true|false`
  - `remote_head_exists`: `true|false` from `git ls-remote`
  - `dependent_open_prs`: count of open PRs still referencing the head branch
- Apply this guardrail:
  - if `pr_state=open` or `pr_open_for_update=true`, forbid remote head deletion.
  - if `pr_state=merged` and `pr_open_for_update=false` and no dependent open PRs, allow deletion.
  - if `pr_state=closed` with `pr_open_for_update=false`, allow deletion only after explicit retirement action is recorded.
- Record retirement evidence in the PR body and automation memory: pre-delete check, delete action result, and post-delete confirmation.

Done when:
- Merged PR closure runs include retirement evidence fields and never show a deleted remote branch for still-open PRs or draft PRs.
- PR #9/#10 are no longer omitted from branch-retirement accounting after merge and their head-branch actions are explicitly recorded.

### 15. Remote Branch Retirement Execution Audit

Evidence:
- On 2026-07-02, PR #9 (`codex/express-direct-cleanup-scope`) and PR #10 (`codex/pr-evidence-growth-map-20260616`) moved from `merged` state to retired remote head state in one execution sequence.
- `checked_at` used for retirement evidence was `2026-07-02T00:05:00Z` (UTC).
- PR #11 is currently open draft and therefore excluded from remote-head deletion by the current PR-state guardrail.

Practice:
- For each closed/merged automation PR with remaining `git ls-remote` head presence, run execution evidence in one bounded packet:
  - classify PR lifecycle (`merged|closed|open`) from connector payload,
  - capture pre-delete branch refs (`head_branch`, `head_sha_pre`, `pr_state`),
  - run remote delete command and persist stdout/stderr,
  - run post-delete `git ls-remote` confirmation and record `absent`/`present`,
  - classify dependent open PRs and enforce open/draft retention.
- Treat execution evidence as mandatory when remediation has already been documented as a growth target.
- Keep PRs like #11 retained and explicitly logged as `open/draft->retained` to avoid false positives in cleanup completion claims.

Done when:
- Retired merged PRs have pre-delete refs, command output, and post-delete absence proof in the same PR body.
- Current open or draft PR branches are explicitly logged as retained with source-of-truth evidence.

## Next Concrete Drill

Before the next branch-cleanup update, execute one complete remote-branch retirement evidence packet:
- capture current PR state for each merged/closed automation PR candidate,
- log `checked_at`, `pre-delete branch refs`, deletion command output, and `post-delete ls-remote` status,
- apply open/draft guardrail (`open/draft => retained`, merged+no-dependents => deleted),
- and sync the exact memory fields for PR state, branch actions, command output, and evidence sources.

# Automation PR Evidence Checklist

Use this checklist before an automation-created PR claims that a recommendation was implemented, validated, and cleaned up.

## When To Use

- A recurring automation creates a branch, commit, or PR.
- A new PR is based on recent PR history or review evidence.
- There is already an open automation PR.
- Local Git state and GitHub PR state may disagree.

## Evidence Packet

Record these fields in the PR body or automation memory:

| Field | Required Evidence |
| --- | --- |
| checked_at | UTC timestamp when this evidence packet was collected |
| Default branch state | `git ls-remote origin refs/heads/master` or GitHub REST default-branch SHA |
| Evidence source map | Per-item source for each claim (`git`, `git ls-remote`, GitHub connector payload, GitHub REST, GitHub UI) |
| Open PR dependency map | Per open PR: id, title, state, base/head SHA, base branch, reviewed state, and `independent|stacked|blocked` verdict |
| Changed-file ownership proof | Full changed-file list per open PR and explicit overlap reason |
| Open PR state | PR number, title, state, head branch, head SHA, labels |
| Review state | Review, inline comments, and issue comments counts (or explicit empty arrays with source) |
| Compare readiness | Base/head SHA compare result, `ahead/behind` counts, and rebase status (`ready|needs-rebase|blocked`) |
| Freshness trigger | Event that requires this evidence (`before-open`, `before-update`, `before-push`, `before-merge-check`) |
| Dependency decision | Independent of open PRs, stacked on an open PR, blocked by an open PR, or requires rebase before update |
| Conflict check | Files changed by the open PR compared with files changed by this PR |
| Open PR relationship | For every open automation PR: `independent`, `stacked`, or `blocked`, with the exact file-overlap reason |
| SHA/date capture mode | `live-fetched` for current values, `fixed` for intentional historical values with TTL/expiration rationale |
| Post-push self-refresh evidence | For self-referential PR updates, pre-push and post-push `checked_at` plus PR `head` values |
| Validation | Exact commands run and whether failures are functional or formatting-only |
| Publication tooling | Whether `gh` CLI was available; if not, explicit Git+GitHub connector fallback used |
| Cleanup policy | Local branch action and remote PR head branch action with PR-state reason |
| Post-push PR body refresh | After a branch push, whether the PR body was updated to the new head SHA/evidence packet and then re-fetched |
| PR body freshness verification | Search result proving the PR body does not cite stale current-head SHA or stale `checked_at` values for live evidence |

## Command Set

```powershell
(Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
git fetch origin --prune
git remote update --prune
git ls-remote origin refs/heads/master refs/heads/<candidate-branch>
git rev-list --left-right --count <base-ref>...<head-ref>
git log --oneline --decorate --max-count=10 origin/master
git diff --stat origin/master...HEAD
git diff --check
git push origin <candidate-branch>
git fetch origin <candidate-branch> --prune
git rev-parse origin/<candidate-branch>
git log -n 1 --format="%H %aI" origin/<candidate-branch>
git show --no-patch --pretty=fuller origin/<base-branch>..origin/<head-branch>
git ls-remote origin refs/heads/<candidate-branch>
```

When `git fetch` is blocked, use the GitHub connector or REST API for PR metadata and keep `git ls-remote` as the remote SHA check.
When `gh` CLI is unavailable, use the GitHub connector to create/update PR metadata, labels, comments, and per-PR compare state.
After pushing to an existing PR branch, update the PR body with the new evidence packet, fetch the PR again, and verify the body does not still cite the branch's previous current-head SHA as live evidence.

## PR Body Template

```markdown
## Evidence

- checked_at: `<YYYY-MM-DDTHH:mm:ssZ>` (UTC), evidence-source: `<git|connector|rest|ui>`, freshness-trigger: `<before-open|before-update|before-push|before-merge-check>`, sha-date-mode: `<live-fetched|fixed>`.
- Evidence source map: base=`<source>`, open-pr-state=`<source>`, review-state=`<source>`, conflict-check=`<source>`, validation=`<source>`.
- Base branch: `master` at `<sha>` (source: `<source>`, mode: `<live-fetched|fixed>`).
- Open PRs checked: `#<n> <title>` at `<head-sha>`, state `<state>` (source: `<source>`, mode: `<live-fetched|fixed>`).
- Head/base date notes: `<sha/date>` is `<live-fetched|fixed>` at `<checked_at>` because `<reason>`.
- Review evidence: `<reviews>` reviews, `<inline-comments>` inline comments, `<issue-comments>` issue comments (source: `<source>`).
- Tooling path: `<git|github-connector|both>`, `gh` availability `<yes|no>`, fallback `<N/A|connector metadata>`.
- Open PR dependency matrix:
  - `#<n>`: dependency=`<independent|stacked|blocked|needs-rebase>`, reason=`<changed-files|head conflict|review hold>`, overlap=`<files|none>`, compare=`base=<base-sha> head=<head-sha> ahead=<n> behind=<n>`, status=`<ready|needs-rebase|blocked>`, source=`<source>`, mode=`<live-fetched|fixed>`.
- Dependency decision: `<independent|stacked|blocked|needs-rebase>` for the target PR with summary reason and required follow-up.
- Conflict check: `<files>` overlap status.
- Open PR relationship: `#<n>` is `<independent|stacked|blocked>` because `<changed-file comparison>`.
- Rebase readiness action plan: `<action>` (for example: `rebase #<n> before update`, `hold update`, `update independent`).
- Post-push self-refresh: pre-push checked_at=`<YYYY-MM-DDTHH:mm:ssZ>`, pre-push head=`<sha>`, post-push checked_at=`<YYYY-MM-DDTHH:mm:ssZ>`, post-push head=`<sha>`.
- Post-push PR body refresh: branch pushed at `<new-head-sha>`, PR body updated at `<checked_at>`, refreshed PR body source `<connector|rest|ui>`.
- PR body freshness verification: stale live-evidence tokens checked `<previous-current-head-sha|previous-checked_at>` with result `<no matches|historical-only matches with reason>`.

## Validation

- `<command>`: `<result>`
- `<PR body freshness check>`: `<result>`

### Post-Push Self-Refresh

- pre-push checked_at: `<YYYY-MM-DDTHH:mm:ssZ>` (UTC)
- pre-push head: `<sha>` (source: `<source>`, mode: `<live-fetched|fixed>`)
- post-push checked_at: `<YYYY-MM-DDTHH:mm:ssZ>` (UTC)
- post-push head: `<sha>` (source: `<source>`, mode: `live-fetched`)
- stale-body check: PR body no longer contains pre-push `checked_at` or pre-push current-head values as live evidence; PR body includes post-push `checked_at` and current head.
- post-push refresh action: `<updated PR body via GitHub connector|updated PR body via gh|pending update>`

## Cleanup

- Local branch cleanup: `<deleted|retained>` with reason and timestamp.
- Remote branch cleanup: `<retained|deleted|not-created>` with reason and merge/close condition.
```

## Current Example

- PR #8 merged into `master` as `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`.
- PR #9 is open as draft from `codex/express-direct-cleanup-scope` at `1a0db5475e7e89ea45da278deb05bd2d3342d372`.
- PR #10 is open as draft from `codex/pr-evidence-growth-map-20260616`; because this checklist lives on that same PR branch, fetch the live PR head SHA before citing it.
- PR #10 is self-referential to these docs; after any new push to branch `codex/pr-evidence-growth-map-20260616`, refresh and revalidate the PR body before claiming evidence freshness.
- PR relationship snapshot at `2026-06-22T00:03:43Z`:
  - `#9`: state=`open`, head=`1a0db5475e7e89ea45da278deb05bd2d3342d372`, base=`ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`, dependency=`independent`, overlap=`none`, compare=`ahead=1 behind=0`, status=`ready`, review state=`0 reviews, 0 inline comments, 0 issue comments`.
  - `#10` is the current target PR and is not included in the open-PR dependency matrix by definition. review state for current target: `0 reviews, 0 inline comments, 0 issue comments`.
- GitHub's combined PR discussion fetch returned no reviews, no inline comments, and no issue comments for PR #8, PR #9, and PR #10 on 2026-06-22 (live-fetched); PR #8, PR #9, and PR #10 also had empty review-thread connector results.
- PR #9 and PR #10 are independent by changed-file ownership, but both target `master` `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`; rebase/conflict readiness must still be checked before publication updates.
- Local environment has no `gh` CLI; use Git for code movement and the GitHub connector for PR metadata/labels/comments.
- A follow-up that only updates PR #10's `docs/` files should update PR #10 instead of creating a duplicate PR, while PR #9 remains independent because it owns validator, test, and orchestration contract files.
- After every push to PR #10's existing branch, refresh the PR body to the new head SHA and re-fetch it before reporting completion; otherwise the PR body can immediately become stale even when the branch update itself succeeded.

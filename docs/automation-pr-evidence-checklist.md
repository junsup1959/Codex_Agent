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
| Evidence surface reconciliation | Differences between GitHub UI/search, connector/API PR payloads, `git ls-remote`, local `origin/*`, and automation memory |
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
| Publication labels | PR labels and verification source (`GitHub connector payload`) |
| Branch cleanup evidence | Local branch action, remote branch action, and decision source |
| Publication closure verification | Pre-push/post-push evidence comparison and stale-body check |
| Automation-memory sync | Run evidence persisted in automation memory with matching label/branch/head facts |
| Automation-memory fact expiration | Prior memory facts classified as `open-pr-current`, `merged-current`, `historical-only`, or `superseded`, with expiration trigger |
| Post-push self-refresh evidence | For self-referential PR updates, pre-push and post-push `checked_at` plus PR `head` values |
| Validation | Exact commands run and whether failures are functional or formatting-only |
| Publication tooling | Whether `gh` CLI was available; if not, explicit Git+GitHub connector fallback used |
| Merged PR classification | `state`, `merged_at`, `closed_at`, and merge-source evidence source (`connector`/`rest`/`git`) |
| Cleanup policy | Local branch action and remote PR head branch action with PR-state reason |
| Post-push PR body refresh | After a branch push, whether the PR body was updated to the new head SHA/evidence packet and then re-fetched |
| PR body freshness verification | Search result proving the PR body does not cite stale current-head SHA or stale `checked_at` values for live evidence |
| Remote head retirement classification | `pr_state` (`merged|closed|open`), `remote_head_exists` (`true|false` from `git ls-remote`), retirement eligibility (`allow_delete`), and dependent-open-PR check |
| Remote deletion guardrail | explicit statement that remote branch deletion is forbidden while PR state is `open` or `draft` |

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
git show --no-patch --format="%H %aI" HEAD
git branch --list
git branch -d <candidate-branch>
git show --no-patch --pretty=fuller origin/<base-branch>..origin/<head-branch>
git ls-remote origin refs/heads/<candidate-branch>
git ls-remote --heads origin refs/heads/<candidate-branch>
git rev-parse --verify origin/<candidate-branch>
git push origin --delete <candidate-branch>
git show --no-patch --format="%H %aI %s" origin/<candidate-branch>
```

When `git fetch` is blocked, use the GitHub connector or REST API for PR metadata and keep `git ls-remote` as the remote SHA check.
When `gh` CLI is unavailable, use the GitHub connector to create/update PR metadata, labels, comments, per-PR compare state, and closure checks.
After pushing to an existing PR branch, update the PR body with the new evidence packet, fetch the PR again, and verify the body does not still cite the branch's previous current-head SHA as live evidence.
When GitHub UI/search, connector payloads, Git remote refs, local refs, or automation memory disagree, record the mismatch instead of silently choosing one source. Use connector/API PR payloads for PR state, `git ls-remote` for remote branch existence/head, local Git for checkout state, and default-branch file trees for merged-doc availability.

## PR Body Template

```markdown
## Evidence

- checked_at: `<YYYY-MM-DDTHH:mm:ssZ>` (UTC), evidence-source: `<git|connector|rest|ui>`, freshness-trigger: `<before-open|before-update|before-push|before-merge-check>`, sha-date-mode: `<live-fetched|fixed>`.
- Evidence source map: base=`<source>`, open-pr-state=`<source>`, review-state=`<source>`, conflict-check=`<source>`, validation=`<source>`.
- Evidence surface reconciliation: UI/search=`<result>`, connector/API=`<result>`, git-remote=`<result>`, local-ref=`<result>`, automation-memory=`<result>`, chosen-source=`<source>`, reason=`<why this source answers the claim>`.
- Base branch: `master` at `<sha>` (source: `<source>`, mode: `<live-fetched|fixed>`).
- Open PRs checked: `#<n> <title>` at `<head-sha>`, state `<state>` (source: `<source>`, mode: `<live-fetched|fixed>`).
- Head/base date notes: `<sha/date>` is `<live-fetched|fixed>` at `<checked_at>` because `<reason>`.
- Review evidence: `<reviews>` reviews, `<inline-comments>` inline comments, `<issue-comments>` issue comments (source: `<source>`).
- Tooling path: `<git|github-connector|both>`, `gh` availability `<yes|no>`, fallback `<N/A|connector metadata>`.
- Open PR dependency matrix:
  - `#<n>`: dependency=`<independent|stacked|blocked|needs-rebase>`, reason=`<changed-files|head conflict|review hold>`, overlap=`<files|none>`, compare=`base=<base-sha> head=<head-sha> ahead=<n> behind=<n>`, status=`<ready|needs-rebase|blocked>`, source=`<source>`, mode=`<live-fetched|fixed>`.
- Dependency decision: `<independent|stacked|blocked|needs-rebase>` for the target PR with summary reason and required follow-up.
- Labels on PR at collection: `<label1>, <label2>` from `<source>`.
- Conflict check: `<files>` overlap status.
- Open PR relationship: `#<n>` is `<independent|stacked|blocked>` because `<changed-file comparison>`.
- Rebase readiness action plan: `<action>` (for example: `rebase #<n> before update`, `hold update`, `update independent`).
- Post-push self-refresh: pre-push checked_at=`<YYYY-MM-DDTHH:mm:ssZ>`, pre-push head=`<sha>`, post-push checked_at=`<YYYY-MM-DDTHH:mm:ssZ>`, post-push head=`<sha>`.
- Post-push PR body refresh: branch pushed at `<new-head-sha>`, PR body updated at `<checked_at>`, refreshed PR body source `<connector|rest|ui>`.
- PR body freshness verification: stale live-evidence tokens checked `<previous-current-head-sha|previous-checked_at>` with result `<no matches|historical-only matches with reason>`.
- Memory fact classification: `<fact>` is `<merged-current|open-pr-current|historical-only|superseded>` with source `<source>`.
- Branch cleanup and retention evidence: local branch `<deleted|retained>`, remote PR branch `<retained|deleted|not-created>`, remote retention reason, and timestamp.
- Automation-memory sync evidence: memory artifact `<path>`, entry key `<run-id>`, and matching fact checks for `head`, `labels`, `local-branch-action`, `remote-branch-action`.
- Automation-memory fact expiration: prior memory facts `<fact-list>` are classified as `<open-pr-current|merged-current|historical-only|superseded>`, expiration trigger `<after-push|after-merge|after-close|after-rebase>`, refreshed source `<connector|git|git ls-remote>`.
- Merged PR closure check: `state=<merged|closed|open>`, `pr_payload_state=<open|draft|closed|merged>`, `dependent_open_prs=<count or ids>`, dependent source `<connector|rest|git>`, and deletion-eligibility outcome.
- Remote branch retirement evidence: `remote_head_exists_pre` (`exists|absent`), delete action result (`deleted|not-deleted`), `remote_head_exists_post` (`exists|absent`), dependent-open-PR check, and guardrail result (`open/draft delete forbidden|allowed`).

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
- branch labels post-push: `<labels>` and label source `<connector|rest|ui>`.
- post-push cleanup action: local branch `<deleted|retained>`, remote branch `<retained|deleted>`, closure status `<verified|not-verified>`.
- memory sync: `<memory artifact>` updated with same labels/head/branch cleanup facts and `checked_at`.
- memory parity check: PR body and automation memory agree on current `head`, labels, local branch cleanup, remote branch retention, and expired prior-run facts.

## Cleanup

- Local branch cleanup: `<deleted|retained>` with reason and timestamp.
- Remote branch cleanup: `<retained|deleted|not-created>` with reason and merge/close condition.
- Remote branch retirement guardrail: if PR is `open` or `draft`, remote action must be `retained`; if PR is `merged` and no dependents remain, action may be `deleted` (with recorded command output).
```

## Historical Publication Closure (PR #10-specific)

- Historical (pre-merge): PR #10 was self-referential and had to prove post-push body alignment and closure state in the same evidence packet used for checks above.
- Historical (pre-merge): PR #9 cleanup-actions are the precedent for local-vs-remote cleanup policy; PR #10 remained an independent docs PR during draft, so remote PR branch retention applied while it was open draft.
- Closure verification requires one captured set each for:
  - post-push `checked_at` and `head`
  - labels present at push time
  - local branch action and remote branch action
  - post-refresh stale-token check result
  - automation memory sync with source-of-truth parity
  - prior memory fact classification and expiration trigger

## Current Example

- PR #8 merged into `master` as `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`.
- PR #9 merged into `master` on 2026-06-26; remote head branch `codex/express-direct-cleanup-scope` was still present in `git ls-remote` after merge and required explicit retirement evidence before deletion.
- PR #10 merged into `master` on 2026-06-26; remote head branch `codex/pr-evidence-growth-map-20260616` was still present in `git ls-remote` after merge and required explicit retirement evidence before deletion.
- Historical (pre-merge): PR #10 was open as draft from `codex/pr-evidence-growth-map-20260616`; because this checklist lived on that same PR branch, the live PR head SHA had to be fetched before citation.
- On 2026-06-23, PR #10 pre-push head is `cbc5ee20550ae0be035d0e182baa82c607f192ea`; treat this as non-authoritative after push and re-fetch live head immediately.
- Historical (pre-merge): PR #10 was self-referential to these docs; after any new push to branch `codex/pr-evidence-growth-map-20260616`, its PR body had to be refreshed and revalidated before claiming evidence freshness.
Historical PR-relationship snapshot at `2026-06-22T00:03:43Z`:
  - `#9`: state=`open`, head=`1a0db5475e7e89ea45da278deb05bd2d3342d372`, base=`ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`, dependency=`independent`, overlap=`none`, compare=`ahead=1 behind=0`, status=`ready`, review state=`0 reviews, 0 inline comments, 0 issue comments`.
  - `#10` was the current target PR and was not included in the open-PR dependency matrix by definition. review state for that target: `0 reviews, 0 inline comments, 0 issue comments`.
- GitHub's combined PR discussion fetch returned no reviews, no inline comments, and no issue comments for PR #8, PR #9, and PR #10 on 2026-06-22 (live-fetched); PR #8, PR #9, and PR #10 also had empty review-thread connector results.
- Historical (pre-merge): PR #9 and PR #10 were independent by changed-file ownership, but both targeted `master` `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`; rebase/conflict readiness had to be checked before publication updates.
- Local environment has no `gh` CLI; use Git for code movement and the GitHub connector for PR metadata/labels/comments.
- Historical (pre-merge): a follow-up that only updated PR #10's `docs/` files had to update PR #10 instead of creating a duplicate PR, while PR #9 remained independent because it owned validator, test, and orchestration contract files.
- Historical (pre-merge): after every push to PR #10's existing branch, the PR body had to be refreshed to the new head SHA and re-fetched before reporting completion; otherwise the PR body could immediately become stale even when the branch update itself succeeded.
- On 2026-06-24, the GitHub PR list page rendered `0 Open / 7 Closed` and omitted PR #8-#10.
- Connector/API payloads showed PR #9 and PR #10 as open drafts (historical; state later merged on 2026-06-26).
- `git ls-remote` separately showed their remote branch heads. Treat this as an evidence-surface reconciliation case: cite connector/API for PR state, cite `git ls-remote` for branch heads, and cite `origin/master` for default-branch file availability.
- Historical (pre-merge): on 2026-06-25, the next PR #10 update had to treat the 2026-06-24 automation memory entry as historical input until live connector/Git checks refreshed its head, labels, and cleanup claims for the new push.

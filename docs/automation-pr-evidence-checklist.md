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
| Open PR state | PR number, title, state, head branch, head SHA, labels |
| Review state | Review, inline review-comment, and issue-comment counts (or explicit empty arrays with source) |
| Freshness trigger | Event that requires this evidence (`before-open`, `before-update`, `before-push`, `before-merge-check`) |
| Dependency decision | Independent of open PRs, stacked on an open PR, or blocked by an open PR |
| Conflict check | Files changed by the open PR compared with files changed by this PR |
| Open PR relationship | For every open automation PR: `independent`, `stacked`, or `blocked`, with the exact file-overlap reason |
| SHA/date capture mode | `live-fetched` for current values, `fixed` for intentional historical values with TTL/expiration rationale |
| Validation | Exact commands run and whether failures are functional or formatting-only |
| Publication tooling | Whether `gh` CLI was available; if not, explicit Git+GitHub connector fallback used |
| Cleanup policy | Local branch action and remote PR head branch action with PR-state reason |

## Command Set

```powershell
(Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
git fetch origin --prune
git ls-remote origin refs/heads/master refs/heads/<candidate-branch>
git log --oneline --decorate --max-count=10 origin/master
git diff --stat origin/master...HEAD
git diff --check
git push origin <candidate-branch>
```

When `git fetch` is blocked, use the GitHub connector or REST API for PR metadata and keep `git ls-remote` as the remote SHA check.
When `gh` CLI is unavailable, use the GitHub connector to create/update PR metadata, labels, and comments.

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
- Dependency decision: `<independent|stacked|blocked>` because `<reason>`.
- Conflict check: `<files>` overlap status.
- Open PR relationship: `#<n>` is `<independent|stacked|blocked>` because `<changed-file comparison>`.

## Validation

- `<command>`: `<result>`

## Cleanup

- Local branch cleanup: `<deleted|retained>` with reason and timestamp.
- Remote branch cleanup: `<retained|deleted|not-created>` with reason and merge/close condition.
```

## Current Example

- PR #8 merged into `master` as `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`.
- PR #9 is open as draft from `codex/express-direct-cleanup-scope` at `1a0db5475e7e89ea45da278deb05bd2d3342d372`.
- PR #10 is open as draft from `codex/pr-evidence-growth-map-20260616`; because the PR updates this same document, fetch the live PR head SHA before citing it (live-fetched mode only).
- GitHub's combined PR discussion fetch returned no comments for PR #8, PR #9, and PR #10 on 2026-06-20 and 2026-06-19. PR #10 review threads were empty on 2026-06-20, and the GitHub UI showed 0 reviews on 2026-06-20. Earlier automation notes also recorded no fetched comments or review threads for PR #8 and PR #9 on 2026-06-16.
- Local environment has no `gh` CLI; use Git for code movement and the GitHub connector for PR metadata/labels/comments.
- A follow-up that only updates PR #10's `docs/` files should update PR #10 instead of creating a duplicate PR, while PR #9 remains independent because it owns validator, test, and orchestration contract files.

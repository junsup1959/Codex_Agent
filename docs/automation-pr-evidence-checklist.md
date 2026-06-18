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
| Default branch state | `git ls-remote origin refs/heads/master` or GitHub REST default-branch SHA |
| Open PR state | PR number, title, state, head branch, head SHA, labels |
| Review state | Review, inline review-comment, and issue-comment counts |
| Dependency decision | Independent of open PRs, stacked on an open PR, or blocked by an open PR |
| Conflict check | Files changed by the open PR compared with files changed by this PR |
| Open PR relationship | For every open automation PR: `independent`, `stacked`, or `blocked`, with the exact file-overlap reason |
| Validation | Exact commands run and whether failures are functional or formatting-only |
| Cleanup policy | Local branch deleted, remote PR head retained, or remote branch deletion reason |

## Command Set

```powershell
git fetch origin --prune
git ls-remote origin refs/heads/master refs/heads/<candidate-branch>
git log --oneline --decorate --max-count=10 origin/master
git diff --stat origin/master...HEAD
git diff --check
```

When `git fetch` is blocked, use the GitHub connector or REST API for PR metadata and keep `git ls-remote` as the remote SHA check.

## PR Body Template

```markdown
## Evidence

- Base branch: `master` at `<sha>` from `<source>`.
- Open PRs checked: `#<n> <title>` at `<head-sha>`, state `<state>`.
- Review evidence: `<reviews>` reviews, `<inline-comments>` inline comments, `<issue-comments>` issue comments.
- Dependency decision: `<independent|stacked|blocked>` because `<reason>`.
- Conflict check: `<files>` overlap status.
- Open PR relationship: `#<n>` is `<independent|stacked|blocked>` because `<changed-file comparison>`.

## Validation

- `<command>`: `<result>`

## Cleanup

- Local branch cleanup: `<deleted|retained>` because `<reason>`.
- Remote branch cleanup: `<retained|deleted|not-created>` because `<reason>`.
```

## Current Example

- PR #8 merged into `master` as `ccf7fbc333cbff231efad0cc7c92a0e09c37cec1`.
- PR #9 is open as draft from `codex/express-direct-cleanup-scope` at `1a0db5475e7e89ea45da278deb05bd2d3342d372`.
- PR #10 is open as draft from `codex/pr-evidence-growth-map-20260616`; because the PR updates this same document, fetch the live PR head SHA before citing it.
- GitHub's combined PR discussion fetch returned no comments for PR #8, PR #9, and PR #10 on 2026-06-18. Earlier automation notes also recorded no fetched comments or review threads for PR #8 and PR #9 on 2026-06-16.
- A follow-up that only updates PR #10's `docs/` files should update PR #10 instead of creating a duplicate PR, while PR #9 remains independent because it owns validator, test, and orchestration contract files.

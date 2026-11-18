---
name: review
description: Multi-lane fresh-context review of a branch, a PR or a commit range, with every finding independently verified - or, with --external, triage of an external reviewer's findings on a PR. Report-only unless --fix. Use when the user asks to review a branch or PR with gauntlet, to re-review fix commits, or to process an external reviewer's (e.g. CodeRabbit's) comments. For a quick single-pass review of the current diff, the built-in /code-review is enough.
argument-hint: "[branch | PR# | base..head] [--fix] [--delta] [--external]"
---

# Gauntlet: review

Review one change the way `/gauntlet:implement` reviews its own work, without having built it here. Arguments: **$ARGUMENTS**

## Ground rules

- The repo's CLAUDE.md files and the user's memory win over this skill wherever they conflict.
- Load the repo profile `.claude/review/profile.md`. In a worktree without it, read it from the main checkout: parent of `git rev-parse --path-format=absolute --git-common-dir`. No profile: ask the user once for the gate commands and proceed; suggest `/gauntlet:configure`.
- **Report-only by default.** Without `--fix` you change no code, push nothing, post nothing to the PR and file no issues; you offer those at the end.
- You orchestrate; you don't review. If this session wrote the code under review, your own opinion of it stays out of the brief, the reviewer prompts and the verdicts.
- Run state lives in `~/.claude/gauntlet/runs/<repo>/<branch>/` (brief.md, review.md), shared with `/gauntlet:implement`. Never inside the repo.

## 1. Resolve the target

| Argument | Base | Head | Read from |
|---|---|---|---|
| none | merge-base with the default branch | current `HEAD` | current checkout |
| branch name | merge-base with the default branch | that branch | current checkout if it is checked out, else a worktree |
| PR number | the PR's base (`gh pr view <N> --json baseRefName,headRefName,headRefOid,title,body,closingIssuesReferences`) | the PR's head | current checkout if `HEAD` equals the PR head, else a worktree |
| `base..head` | as given | as given | current checkout if `head` is `HEAD`, else a worktree |

- **Worktree:** reviewers read files, so the head must be on disk. `git fetch origin pull/<N>/head` (or the branch), then `git worktree add --detach ~/.claude/gauntlet/worktrees/<repo>/<slug> <sha>`. Remove it when the review ends. A worktree target is always report-only.
- **Dirty tree:** reviewers would read uncommitted edits that the diff doesn't contain. Ask once whether to commit first or review the committed head; the committed head is then read from a worktree (so report-only), leaving the working tree untouched.
- **`--delta`:** base becomes the last reviewed head recorded in `review.md`, provided it is an ancestor of the target head (`git merge-base --is-ancestor`). None recorded, or not an ancestor: say so and the scope becomes `full`.
- **Intent:** linked issue, then spec or plan in the run directory, then PR body, then commit messages. If all are thin, ask the user for one sentence. Record which source you used in the brief.

State the resolved target in one line (base, head, files, changed lines, mode, scope) before starting.

## 2. Run the pipeline

Follow [reference/pipeline.md](reference/pipeline.md) with the mode and scope resolved above, the same ones you stated in the target line. Mode is `fix` only if `--fix` was given and the target is the checked-out branch and not the default branch; otherwise `report`, and say why if `--fix` was asked for.

## 3. Report

In `report` mode, reply with:

```
Target        base..head, N files, +A/-D, lanes run (and lanes skipped, with the routing reason)
Confirmed     by severity: title — path:line — the verifier's deciding fact — fix sketch
Needs a decision   the question, and the precondition that could not be verified
Pre-existing  confirmed, but not introduced by this change
Rejected      count, plus one line each
```

Zero confirmed findings is a valid result; say so plainly and don't pad. Then offer, without doing them: fix the confirmed findings (`--fix`), file the pre-existing ones as issues, post the findings to the PR.

In `fix` mode, report what `/gauntlet:implement` stage 7 would: fixes with commit SHAs, lanes run, filed issues, anything left open. Don't push unless the repo's rules allow pushing this branch without asking.

## `--external`: triage an external reviewer's findings

Follow [reference/external.md](reference/external.md). Takes a PR number, or uses the current branch's PR. It runs in the same effective mode as the pipeline: `--fix` applies only when the PR head is the checked-out branch; any other PR is triaged report-only.

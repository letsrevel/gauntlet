---
name: implement
description: Take an issue or feature request from triage to an open, self-reviewed PR - plan when needed, implement (linear or delegated), update docs, gate, multi-lane fresh-context review with per-finding verification, PR, external review. Use when the user asks to implement, build, fix or ship an issue or feature end to end.
argument-hint: "<issue number | URL | description> [--size S|M|L] [--resume]"
---

# Gauntlet: implement

Ship one change from request to an open PR that has already survived a fresh-context review. Arguments: **$ARGUMENTS**

## Ground rules

- The repo's CLAUDE.md files and the user's memory win over this skill wherever they conflict.
- Read [reference/done.md](reference/done.md) now and again at the start of every stage. It holds the definition of done and the caps; this file only routes.
- Load the repo profile `.claude/review/profile.md` (gate, docs locations, security triggers, external reviewer, merge policy). If the current directory is a worktree without it, read it from the main checkout: parent of `git rev-parse --path-format=absolute --git-common-dir`. No profile: ask the user once for the gate commands and proceed; suggest copying `${CLAUDE_PLUGIN_ROOT}/templates/profile.md`.
- Model routing: Haiku for small mechanical tasks, Sonnet for medium ones, Opus orchestrates, plans and reviews. For a hard design question or a disputed MAJOR finding, consult the user's `/advisor` if configured; otherwise state the question and ask the user.
- Linear by default. Dispatch subagents only for independent tasks, isolation from noisy output, or a fresh pair of eyes (review), never for "a smarter answer".
- Run state lives in `~/.claude/gauntlet/runs/<repo>/<branch>/` (spec.md, plan.md, handoff.md, brief.md, review.md). Never inside the repo; never committed.

## Stages

Announce each stage in one line as you enter it. Stop and ask only where a stage says so.

**0. Triage.** Resolve the request (`gh issue view` for an issue). Read the code it touches. Size it (or take `--size`):
- **S**: one area, obvious approach, under ~150 changed lines. No plan file; state a 3-line plan and go.
- **M**: several files or one non-obvious decision. Write `plan.md` ([reference/plan.md](reference/plan.md)); show the decisions; wait for an OK if the repo's CLAUDE.md requires discussion before non-trivial changes.
- **L**: multi-area, schema plus API plus UI, or real design choices. Spec interview → `spec.md` → `plan.md` → user approval → `handoff.md`, then recommend continuing in a fresh session with `/gauntlet:implement --resume`.
`--resume`: read `handoff.md` and the run files, check the branch state, continue from the recorded stage.

**1. Branch.** Never work on the default branch. Use the repo's branch naming convention.

**2. Implement.** Follow [reference/plan.md](reference/plan.md) § Execution. Bug fix: first write a regression test that fails on the current code, then fix. Run the targeted tests for what you touched as you go.

**3. Docs.** Update every doc the change makes stale, in the same branch: changelog entry for user-visible changes, docs pages, engineering notes, ADRs for decisions, docstrings and help text. Grep the docs for every symbol, setting, env var or endpoint you renamed or changed. The profile lists the doc locations.

**4. Gate.** Run the profile's gate. Red: fix and rerun. No review and no push until green.

**5. Self-review.** Follow `${CLAUDE_PLUGIN_ROOT}/skills/review/reference/pipeline.md` in `fix` mode, `full` scope (the same pipeline `/gauntlet:review` runs standalone): freeze a brief, run the generalist and the lanes the router selects, verify every candidate, fix confirmed ones. At most 2 fix rounds; each reruns the gate and reviews only the fix commits.

**6. PR.** Follow [reference/pr.md](reference/pr.md): one push, PR body with lanes run and assumptions, external review per the profile, its findings verified, fixed or declined, and logged to the escape ledger. Never merge or enable auto-merge without the user's explicit OK for that PR.

**7. Report.** PR link, what changed, docs touched, lanes run and findings fixed or filed, anything left for the user. File every deferred follow-up as an issue; never leave it only in chat.

## When to stop and ask

- The plan would change a public API contract, a migration on a large table, money flows, auth, or anything the repo flags as needing discussion.
- A verifier returns NEEDS-HUMAN, or two fix rounds still leave a MAJOR finding.
- The gate fails for reasons outside the change.

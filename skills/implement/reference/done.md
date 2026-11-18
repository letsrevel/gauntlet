# Definition of done and caps (re-read at every stage)

A change is done when all of these hold:

1. On a feature/fix branch, never `main`.
2. Bug fixes include a regression test that fails before the fix and passes after.
3. New endpoints/flows have success, failure and permission (negative) tests.
4. Targeted tests for the touched code pass (never the full suite unless the repo says so).
5. The profile's gate is green on the final commit.
6. Docs are true: CHANGELOG `[Unreleased]` for user-visible changes; docs/notes/ADRs/docstrings updated; nothing left contradicting the code.
7. Self-review ran on a frozen brief, every CONFIRMED finding is fixed or filed as an issue, and the fix commits got a delta review.
8. The PR is open with lanes run, assumptions and linked follow-up issues in its body.
9. Nothing merged, no auto-merge, unless the user said so for this PR in this conversation.

## Caps

- Fix rounds after self-review: **2**. Still a MAJOR finding after round 2 → stop and ask.
- Implementer resumes: **1** per subagent, for a small follow-up. After that, dispatch a fresh implementer with the diff and the findings, not the old context.
- External reviewer requests per PR: **1** initial + **1** re-review after batched fixes, unless the profile says otherwise. The profile states any rate limit.
- Plan/spec questions to the user: batch them; one round of questions per stage.

## Context hygiene

- Size L: write `handoff.md` at the end of Triage/Plan and recommend a fresh session.
- Any size: if your context passes roughly half its window before Review, write `handoff.md` (stage reached, branch, commits, open findings, next step) and recommend `/implement --resume` in a fresh session.
- Reviewers never see your session. They get `brief.md` only.

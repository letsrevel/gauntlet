---
name: handoff
description: Write a session handoff so a fresh session can pick up the work, or resume from the latest one. Use when the user asks for a handoff, a pick-up prompt for the next session, to wrap up before clearing context, or to resume/continue from a previous session's handoff.
argument-hint: "[topic] [--decide-first] | resume [file]"
---

# Gauntlet: handoff

Arguments: **$ARGUMENTS**

Handoffs live in `~/.claude/gauntlet/handoffs/<repo>/<YYYY-MM-DD>-<slug>.md`, where `<repo>` is the main checkout's directory name (`basename "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"`). Never inside the repo, never committed. A `/gauntlet:implement` run in progress keeps its own `handoff.md` under `~/.claude/gauntlet/runs/`; link it rather than duplicating it.

## Write (default)

1. **Collect state, don't recall it.** Run the commands; never write a SHA, PR state or CI result from memory.
   - Per repo touched this session: branch, `git rev-parse --short HEAD`, whether `main` is synced with origin, uncommitted changes, stashes, worktrees with unmerged work.
   - Open PRs this session created or touched: number, title, state, merge state, failing checks (with the reason if known), unresolved review threads, whether merge is approved.
   - Releases, deploys, background jobs or scheduled tasks still running or pending.
2. **Collect pointers, not content.** Reports, specs, plans and artifacts by path or URL, with one line on what each holds. Note anything stored in a location that may not survive (scratchpads, temp dirs) and copy it somewhere durable first, or say it may be gone.
3. **Write the file** with the template below. Keep it under ~150 lines: the next session reads the linked sources for detail.
4. **Sensitive content.** Unfixed vulnerabilities: say where the details are; never paste exploit narratives into the handoff. No secrets, tokens or personal data. No customer names.
5. **Reply** with the file path and the suggested opening prompt, ready to paste.

`--decide-first`: the next session must present decisions and get the user's answers before changing anything. Put that rule first, under Ground rules.

### Template

```markdown
# Handoff <YYYY-MM-DD>: <topic>

Written by the session that <one line: what it did>. Read top to bottom before acting.

## Ground rules for the next session
- <hard limits: e.g. "decide before acting", "never merge without OK", "security items stay private">
- <what needs the user's explicit approval>

## State at handoff
| Repo | Branch | HEAD | Synced | Notes |
|---|---|---|---|---|
Open PRs / CI / jobs: <list with state and blockers>
Installed tooling or config changed this session: <list>

## Sources
| What | Where |
|---|---|

## Decisions needed
<Grouped. Per item: one-line summary, severity or impact, the recommended option, the question to ask.>

## Next steps (after decisions)
<Ordered; which tool or skill to use for each; what must not be done in parallel.>

## Suggested opening
"<paste-ready prompt for the next session>"
```

## Resume

`/gauntlet:handoff resume [file]`: load the named file, else the newest in the repo's handoff directory (list them if there are several from the same day).

1. Read it in full, then follow its ground rules.
2. **Re-verify the state section**: recheck branches, SHAs, PR states and CI. Report every difference from what the handoff recorded before doing anything else (someone may have merged, pushed or deployed since).
3. Open the sources it lists only as needed.
4. If it has a "Decisions needed" section, present those decisions first, in batches of at most four self-contained questions, each with a recommended option. Act only on what the user approves, and record the decisions in a "Decisions taken" section appended to the handoff.

# Planning and execution

## Spec interview (size L only)

Ask about what you cannot learn from the code: goals and non-goals, user-facing behaviour, permissions/roles, data and migration impact, failure modes, backward compatibility, rollout. Use AskUserQuestion with concrete options and a recommended default. Write `spec.md`: problem, decisions (with the chosen option and why), out of scope, acceptance criteria.

## plan.md (size M and L)

```
# <title>  (issue #N, size M|L, branch <name>)
## Decisions        - what was chosen and why (anything the user must approve is marked APPROVAL)
## Tasks
- T1 <name> [S|M] [deps: -] files: ... | acceptance: ... | verify: <exact command>
- T2 ...
## Docs to update   - CHANGELOG, docs pages, notes, ADR?
## Risks            - which review lanes this will trigger and why
```

Task sizing maps to the implementer model: **S → Haiku**, **M → Sonnet**. Anything that needs judgment across the codebase stays with you.

## Execution

- **Linear (default):** do the tasks yourself in order when they are sequential or small, or when total work is a few files.
- **Delegated:** dispatch a subagent per task only when tasks are independent (no shared files) or the task is large but well specified. Brief each with: the task block from plan.md, files to read first, house rules that apply (link the CLAUDE.md sections), the verify command, and "do not commit; report changed files and test output". Give parallel subagents that run tests a unique DB/test namespace if the profile says so.
- Run independent delegated tasks in parallel; never two tasks touching the same file.
- After each task: read the diff yourself, run its verify command, commit with a conventional message.
- A subagent's report is a claim. Check the diff and the test output before accepting it.

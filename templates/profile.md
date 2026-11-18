# Gauntlet profile: <repo name>

<!-- Copy to .claude/review/profile.md in your repo and fill in. Every section is optional. -->

## About this codebase
<One paragraph: stack, what the product does, who the users/roles are, multi-tenancy model, where money moves.>

## Gate
<Ordered commands that must pass before review and before push. Example:>
1. `make format && make check`
2. Targeted tests: `<command> <test paths for touched modules>` (never the full suite unless stated)
3. <Conditional checks, e.g. "if migrations changed: ...">

Parallel test runs: <how to isolate them, e.g. a unique DB name per run, or "none needed">

## Docs locations
- CHANGELOG: <path, section for unreleased>
- Docs: <paths>
- Decisions: <ADR path>
- Other: <engineering notes, runbooks>

## House rules reviewers should check
<Short list, or "see CLAUDE.md">

## Security triggers
<Path globs and keywords that trigger the security lane on a diff. Example: `src/auth/**`, `**/permissions.py`, `*payment*`, `*token*`, dependency manifests, CI workflows, proxy config.>

## Sibling repos
<Paths hunters may read (not review) for context, e.g. `../infra/Caddyfile`, `../frontend`.>

## External reviewer and merge policy
- External reviewer: <e.g. CodeRabbit, with limits; or none>
- Reviewer login: <the account its PR comments come from, e.g. `coderabbitai`; used to fetch its findings>
- Skip external review for: <e.g. internal/admin-only PRs>
- Merge: <e.g. never without explicit approval; squash only; rebase, never merge main>

## Agent memory
<Where the security/debt hunter memory lives relative to the main checkout. Default: `.claude/agent-memory/<agent>/MEMORY.md` (gitignored).>

## Debt metrics
<Commands that produce deterministic metrics for trend tracking: files over N lines, functions at complexity cap, type-ignore count, migrations per app, dead symbols.>

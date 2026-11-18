# Gauntlet

An implement, review, security and tech-debt loop for [Claude Code](https://code.claude.com). Every change runs the gauntlet: plan when it needs one, implement, update the docs, pass the deterministic gate, then face fresh-context reviewers whose every finding is independently verified before it costs you a fix.

## What's inside

| Piece | What it does |
|---|---|
| `/gauntlet:implement` | Issue or request → open, self-reviewed PR. Sizes the task (S: just do it; M: plan; L: spec interview, plan, fresh-session handoff), implements linearly or with delegated subagents, updates docs, runs your gate, reviews, opens the PR, handles your external reviewer. Never merges without your OK. |
| `/gauntlet:review` | The same review stage on its own: a branch, a PR number or a commit range, including work that wasn't built with `/gauntlet:implement` and other people's PRs. Report-only unless `--fix`; `--delta` reviews only what changed since the last reviewed head; `--external` verifies an external reviewer's PR comments, fixes or declines each with evidence, and logs them. |
| `/gauntlet:vuln-scan` | Full or scoped security sweep: feature-slice hunters, dedup, one verifier per candidate, report outside the repo. |
| `/gauntlet:tech-debt` | Full or scoped debt sweep with deterministic metrics you can trend, verified findings and suggested PR bundles. |
| `/gauntlet:configure` | Guided setup: explores the repo (CI, build scripts, docs, git and PR history), proposes the three config files with every value marked found, default or open, asks only what it couldn't find, then checks that the gate commands resolve and the regions cover every source file. `--update` reports drift in an existing config. |
| `/gauntlet:handoff` | Writes a session handoff (verified state, sources, decisions needed, next steps, a paste-ready opening prompt) outside the repo; `/gauntlet:handoff resume` picks up the latest one, re-checks the recorded state and presents pending decisions before acting. |
| Review lanes | `sibling-path-reviewer` (a rule enforced on one entry point but bypassed by admin, bulk, tasks, webhooks…), `docs-truth-reviewer` (prose vs code, both directions), `test-strength-reviewer` (assertions that cannot fail), `security-hunter` and `debt-hunter` in diff-lane mode. |
| `finding-verifier` | Tries to disprove each candidate. Decisions go by verdict, never by a score threshold: a confirmed low-severity finding is still fixed or filed. |

## Design choices, and why

- **Reviewers never see the implementer's session.** They get a frozen brief (SHAs, intent, changed files). Models judging work in the context that produced it are measurably more lenient.
- **Lanes target what generalist review misses.** Measured on one production codebase (180 merged PRs): a forked generalist review caught ~80% of what it plus an external AI reviewer found. The remaining ~20% was docs drift, sibling entry points, unfailable tests and unreviewed fix commits.
- **Gate before review.** Lint, types, formatting and targeted tests are deterministic; reviewers don't spend tokens on them.
- **Verify, don't threshold.** Numeric confidence cut-offs drop real findings. One adversarial verifier per candidate, verdict-based filtering.
- **Measure what escapes.** Every valid finding your external reviewer makes on a self-reviewed PR is logged with the lane that should have caught it (`scripts/ledger.py stats`). A lane that keeps showing up gets its prompt tuned; a verifier that rejects nothing is a rubber stamp.
- **Linear by default.** Subagents only for independent tasks or a fresh pair of eyes. Haiku/Sonnet for mechanical work, Opus to orchestrate and review.
- **Nothing lands in your repo by accident.** Reports, run state and the escape ledger live under `~/.claude/gauntlet/`.

## Install

```
claude plugin marketplace add letsrevel/gauntlet
claude plugin install gauntlet@gauntlet
```

Pin a release with `letsrevel/gauntlet#v0.3.0`. Local development: `claude --plugin-dir ./gauntlet`.

## Configure your repo

Gauntlet works without config and asks for your gate commands once. To make it yours, run `/gauntlet:configure` (or copy the templates from `templates/` by hand) and commit the result; the files travel into worktrees:

| File | Purpose |
|---|---|
| `.claude/review/profile.md` | About the codebase, gate commands, docs locations, security triggers, sibling repos, external reviewer and merge policy, debt metric commands |
| `.claude/review/regions.md` | Feature-slice regions for full sweeps (must cover every source file; the sweep checks) |
| `.claude/review/by-design.md` | Intended behaviour reviewers must not report, each with the boundary that is still a bug |

Agent memory (code-level suppressions keyed to commit SHAs, findings ledger) stays out of git in `.claude/agent-memory/` of your main checkout. Add it to `.gitignore`.

Optional stack packs in `stacks/` add framework-specific security surfaces and debt conventions (Django + Django Ninja, SvelteKit).

## Contracts

The candidate and verdict formats, severity mapping, output locations and agent rules are in [CONTRACTS.md](CONTRACTS.md). Every agent and skill follows them, so you can add your own lanes.

## License

MIT

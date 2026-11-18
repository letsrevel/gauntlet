---
name: configure
description: Set up or refresh a repo's Gauntlet config (.claude/review/profile.md, regions.md, by-design.md). Explores the repo first (instructions, CI, build scripts, docs, git history, PR history), then proposes a guided setup with detected values and sensible defaults, asking only what it could not find. Use when the user asks to set up, configure, initialise or onboard gauntlet in a repo, or to check an existing config for drift.
argument-hint: "[profile | regions | by-design] [--update]"
---

# Gauntlet: configure

Produce the three config files the other gauntlet skills read. Arguments: **$ARGUMENTS** (no file named: all three).

## Ground rules

- **Explore before asking.** Every question you ask must be one the repo could not answer. A value you detected is shown with its evidence for correction, never asked.
- **Never invent policy.** Gate commands, merge rules and by-design entries come from the repo or the user. A plausible guess presented as a fact is worse than a blank.
- **Never overwrite.** An existing config file is merged into, with the changes shown first. Without `--update`, a file that already exists is left alone unless the user named it.
- The repo's CLAUDE.md files win over this skill. Don't commit unless the repo's rules allow it on the current branch; never on the default branch.
- Formats and field meanings: `${CLAUDE_PLUGIN_ROOT}/templates/` and `${CLAUDE_PLUGIN_ROOT}/CONTRACTS.md` § 1. Read them now.

## 1. Explore (read-only, no questions)

Work through the table; note for each value where you found it. For a large repo, dispatch one Explore agent for the regions row and do the rest yourself.

| For | Look at |
|---|---|
| About | README, CLAUDE.md / AGENTS.md, CONTRIBUTING, docs index, manifests (stack and versions), top-level layout. Roles, tenancy model and where money moves: models and permission code. |
| Gate | What CI runs on pull requests (`.github/workflows/`, other CI config) is the ground truth. Map each CI step to the local command behind it (Makefile, justfile, package scripts, pyproject, pre-commit). Note any rule about which tests to run locally (targeted vs full suite) and anything needed to run tests in parallel. |
| Docs locations | CHANGELOG and its unreleased section, docs tree and site config, ADR directory, runbooks, engineering notes. |
| House rules | CLAUDE.md / AGENTS.md / CONTRIBUTING. Point at them; don't copy them. |
| Security triggers | Paths and names for auth, sessions, tokens, permissions, payments, webhooks, file uploads, PII, outbound requests; dependency manifests; CI workflows; proxy or server config. |
| Sibling repos | Paths outside the repo that instructions, compose files or docs reference (frontend, infra, shared config). |
| External reviewer | Review authors on the last ~30 merged PRs (`gh pr list --state merged --limit 30 --json number,reviews`): a bot login that reviews most of them is the external reviewer. Its config file in the repo. Any rate limit or exemption the instructions or memory mention. |
| Merge policy and conventions | Branch names and commit subjects in `git log` and merged PRs; squash vs merge commits vs rebase (`git log --merges --oneline -20`, linear history); branch protection or rulesets if `gh` can read them; signing requirements. |
| Debt metrics | Checks that already produce a number: file-length limits, complexity caps, type-ignore counts, migration counts. |
| Stack pack | Whether a pack in `${CLAUDE_PLUGIN_ROOT}/stacks/` matches the stack. |
| Regions | Tracked non-test source files and their line counts (`git ls-files`), grouped by **feature slice across layers**, not by layer. Churn (`git log --since='6 months ago' --name-only --format=`) and the security triggers above set each region's risk and tier. Keep a region under ~15k non-test lines. |
| By design | SECURITY.md (out-of-scope lists), ADRs, engineering notes, comments and docs saying "by design", "intentional", "accepted risk", closed issues labelled wontfix or by-design, and the user's memory if it lists accepted behaviours. Keep only policy-level behaviour with a reference; each needs the boundary that is still a bug. |

`--update`: also read the existing config and look for drift: gate commands that no longer exist or that CI no longer runs, doc paths that moved, security triggers matching nothing, source files no region owns, regions over the size cap, by-design references that no longer resolve.

## 2. Propose

Show one compact proposal, section by section in the files' own order. Mark every value:

- **found**: with its source (`CI: .github/workflows/test.yaml`, `CLAUDE.md § Hard Rules`, `28 of 30 merged PRs`)
- **default**: nothing in the repo decides it; state the default and why it is reasonable
- **open**: needs the user

Then ask the open items with AskUserQuestion, at most four per batch, the recommended option first, each question self-contained. Typical open items: the merge policy when history is mixed, which PR classes skip the external reviewer, whether a detected "intentional" behaviour really is policy, where a region boundary should fall when two features share a module. If nothing is open, don't manufacture a question: ask only for corrections to the proposal.

For regions, show a table (region, globs, non-test lines, risk, tier, focus) and the result of the coverage check before asking anything.

For by-design, list candidate entries with their reference and proposed boundary. An entry the user doesn't confirm is left out. An empty by-design file is a valid result.

## 3. Write

- Write `.claude/review/profile.md`, `regions.md` and `by-design.md` in the templates' structure, without the template comments and without sections that have nothing to say.
- Add `.claude/agent-memory/` to `.gitignore` if it isn't ignored already.
- Existing files: show the diff you are about to apply, then apply it. Keep the user's wording where the meaning hasn't changed.
- No customer names, secrets or exploit detail in any of the three files; they are committed.

## 4. Verify

- **Gate:** confirm every gate command resolves (the target, script or binary exists). Offer to run the gate once; don't run a long gate unasked.
- **Regions:** run the coverage reconcile the sweeps use: `git ls-files`, drop test, fixture, locale, generated and vendored paths, subtract everything matched by a region's `globs`. Anything left: fix the globs and rerun until nothing is.
- **References:** every path named in the profile and every by-design reference exists.

## 5. Report

The files written or changed, the values that are defaults rather than findings (the ones worth a second look), anything left open, and the next step: commit the files so they travel into worktrees, then `/gauntlet:review` on a branch to try the config.

# Review pipeline

Shared by `/gauntlet:review` (standalone) and `/gauntlet:implement` stage 5. The caller supplies the target (base, head, checkout path), the **mode** (`report` or `fix`) and the **scope** (`full` or `delta`).

Why these lanes: on one production codebase (180 merged PRs, 223 external-reviewer findings, measured 2026-11), a forked generalist review caught roughly 80% of what generalist plus external reviewer found together. The rest was systematic: docs and changelog claims contradicted by code, rules enforced on one entry point but bypassed on its siblings, tests that cannot fail, i18n wording, and fix commits nobody re-reviewed. The lanes below target exactly those. Contracts: `${CLAUDE_PLUGIN_ROOT}/CONTRACTS.md`.

## 1. Gate first

Reviewers never spend effort on lint, types or formatting.

- Target is the checked-out branch: run the profile's gate. Red in `fix` mode: fix and rerun. Red in `report` mode: report the failure and ask whether to review anyway.
- Target lives in a worktree (someone else's PR, an arbitrary range): don't run the gate there; read CI instead (`gh pr checks <N>`). Red or missing: say so and ask whether to review anyway.

## 2. Freeze the brief

Write `~/.claude/gauntlet/runs/<repo>/<branch>/brief.md`:

```
repo: <abs path of the checkout to read>   main checkout: <abs path>   branch: <name>   base: <sha>   head: <sha>
mode: report | fix   scope: full | delta
issue/spec: <text or link, plus spec.md path if any>
intent: <one paragraph: what the change should do and what it must not change>
intent source: <issue | spec | PR body | commit messages | user>
author's assumptions: <quoted from the PR body if any; claims to test, not facts>
changed files: <git diff --name-only base..head>
config: <abs paths of .claude/review/profile.md, by-design.md>
```

Reviewers get only this path. Never paste your reasoning, transcript or opinions into a reviewer prompt. Take the intent from what the change was asked to do (issue, spec, PR body), never from reading the diff and describing it: a reviewer told "the code should do what the code does" finds nothing.

## 3. Route lanes

| Lane | When | How | Model |
|---|---|---|---|
| Generalist correctness | always | built-in `/code-review high` on the target (`xhigh` above ~1.5k changed lines) | session |
| Sibling paths and invariants | always, except docs-only or test-only diffs | `gauntlet:sibling-path-reviewer` | opus |
| Docs truth | always | `gauntlet:docs-truth-reviewer` | sonnet |
| Test strength | diff adds or changes tests | `gauntlet:test-strength-reviewer` | sonnet |
| Security | diff touches a profile security trigger (ignore test, locale and generated files) | `gauntlet:security-hunter` in diff-lane mode | opus |
| Tech debt | diff over ~800 lines, or adds a module/app | `gauntlet:debt-hunter` in diff-lane mode | sonnet |

Small diffs (under ~150 lines, no security triggers): generalist and docs truth only.

**Delta scope** (fix commits, or anything since the last reviewed head): `/code-review medium` on `<prev-head>..<head>` plus any lane whose trigger the delta touches. Nothing else.

Dispatch the agent lanes in parallel with the brief path. Hunter prompt: "Diff-lane mode. Brief: <path>. Memory file: <absolute path in the main checkout, from the profile>. CANDIDATE blocks only." The `/gauntlet:vuln-scan` and `/gauntlet:tech-debt` skills are for full sweeps; don't call them from here.

The built-in generalist doesn't emit CANDIDATE blocks. Rewrite each of its findings as one (`lane: generalist`), keeping its wording and locations and adding nothing of your own.

## 4. Verify

Collect candidates; merge duplicates (same root cause; keep all locations and evidence). Strip each candidate's `confidence` line, then dispatch `gauntlet:finding-verifier` per candidate with the brief and the by-design path: sonnet by default, opus for MAJOR or security. Decide by verdict only, never by a score.

| Verdict | `fix` mode | `report` mode |
|---|---|---|
| CONFIRMED | fix, whatever the severity | report with the verifier's reasoning and fix sketch |
| REJECTED | drop; one-line reason in `review.md` | same, and list the one-liners in the report |
| NEEDS-HUMAN | ask the user (consult the advisor first for a disputed MAJOR, if available) | report under "needs a decision" |
| `in_diff: no` (pre-existing) | file an issue rather than fix, except security, which is fixed or filed privately | report separately; offer to file |

## 5. Fix rounds (`fix` mode only, max 2)

Fix confirmed findings with tests. Then: gate → delta-scope review of only the fix commits → verify. When a finding is a pattern, grep for siblings and fix or file them before closing it.

Stop when a round yields no confirmed MAJOR or security finding, or after round 2 (then ask).

## 6. Record

Append to `review.md`, one section per round, headed with the round number and the reviewed head SHA (delta scope reads the last one as its base): lanes run, candidates per lane, verdict counts, fixes (commit SHAs), filed issues. It feeds the PR body.

Then append one `run` row per round to the escape ledger (row contract in CONTRACTS.md § 5):

```
echo '{"kind":"run","branch":"<name>","head":"<sha>","round":0,"scope":"full","lanes":["generalist","docs-truth"],"candidates":12,"confirmed":7,"rejected":4,"needs_human":1}' \
  | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ledger.py" add
```

The ledger's verifier kill rate (rejected ÷ adjudicated) is the health check on this pipeline: near zero means the verifier is rubber-stamping, above ~60% means the lanes are noisy.

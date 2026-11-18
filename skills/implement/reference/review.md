# Self-review stage

Why these lanes: on one production codebase (180 merged PRs, 223 external-reviewer findings, measured 2026-11), a forked generalist review caught roughly 80% of what generalist plus external reviewer found together. The rest was systematic: docs and changelog claims contradicted by code, rules enforced on one entry point but bypassed on its siblings, tests that cannot fail, i18n wording, and fix commits nobody re-reviewed. The lanes below target exactly those. Contracts: `${CLAUDE_PLUGIN_ROOT}/CONTRACTS.md`.

## 1. Gate first

The profile's gate is green. Reviewers never spend effort on lint, types or formatting.

## 2. Freeze the brief

Write `~/.claude/gauntlet/runs/<repo>/<branch>/brief.md`:

```
repo: <abs path>   main checkout: <abs path>   branch: <name>   base: <merge-base sha>   head: <sha>
issue/spec: <text or link, plus spec.md path if any>
intent: <one paragraph: what the change should do and what it must not change>
changed files: <git diff --name-only base..head>
config: <abs paths of .claude/review/profile.md, by-design.md>
```

Reviewers get only this path. Never paste your reasoning, transcript or opinions into a reviewer prompt.

## 3. Route lanes

| Lane | When | How | Model |
|---|---|---|---|
| Generalist correctness | always | built-in `/code-review high` on the branch (`xhigh` above ~1.5k changed lines) | session |
| Sibling paths and invariants | always, except docs-only or test-only diffs | `gauntlet:sibling-path-reviewer` | opus |
| Docs truth | always | `gauntlet:docs-truth-reviewer` | sonnet |
| Test strength | diff adds or changes tests | `gauntlet:test-strength-reviewer` | sonnet |
| Security | diff touches a profile security trigger (ignore test, locale and generated files) | `gauntlet:security-hunter` in diff-lane mode | opus |
| Tech debt | diff over ~800 lines, or adds a module/app | `gauntlet:debt-hunter` in diff-lane mode | sonnet |

Small diffs (under ~150 lines, no security triggers): generalist and docs truth only.

Dispatch the agent lanes in parallel with the brief path. Hunter prompt: "Diff-lane mode. Brief: <path>. Memory file: <absolute path in the main checkout, from the profile>. CANDIDATE blocks only." The `/gauntlet:vuln-scan` and `/gauntlet:tech-debt` skills are for full sweeps; don't call them from here.

## 4. Verify

Collect candidates; merge duplicates (same root cause; keep all locations and evidence). Strip each candidate's `confidence` line, then dispatch `gauntlet:finding-verifier` per candidate with the brief and the by-design path: sonnet by default, opus for MAJOR or security. Decide by verdict only, never by a score.

- CONFIRMED: fix, whatever the severity.
- REJECTED: drop; keep a one-line reason in `review.md`.
- NEEDS-HUMAN: ask the user (consult the advisor first for a disputed MAJOR, if available).
- `in_diff: no` (pre-existing): file an issue rather than fix, except security, which is fixed or filed privately.

## 5. Fix rounds (max 2)

Fix confirmed findings with tests. Then: gate → delta review of only the fix commits (`/code-review medium` on `<prev-head>..HEAD` plus any lane whose trigger the fix touched) → verify. When a finding is a pattern, grep for siblings and fix or file them before closing it.

Stop when a round yields no confirmed MAJOR or security finding, or after round 2 (then ask).

## 6. Record

Append to `review.md`: lanes run, candidates per lane, verdict counts, fixes (commit SHAs), filed issues. It feeds the PR body and the escape metric: valid external-reviewer findings per PR, tagged with the lane that should have caught each.

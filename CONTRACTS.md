# Gauntlet contracts

Every agent and skill in this plugin follows these contracts. Change them here first.

## 1. Repo config (committed in the target repo, travels into worktrees)

All optional. Without them, skills fall back to sensible defaults and say so.

| File | Purpose |
|---|---|
| `.claude/review/profile.md` | About the codebase (one paragraph), gate commands, docs locations, security path triggers, sibling repos hunters may read, external reviewer (e.g. CodeRabbit) and merge policy, model tiers, metric commands for debt sweeps, where agent memory lives |
| `.claude/review/regions.md` | Region map for full sweeps: one region per feature slice (across layers), with globs, focus surfaces, risk and model tier. Must cover every tracked non-test source file |
| `.claude/review/by-design.md` | Policy-level intended behaviour that reviewers must not report, each with its boundary (what is still a bug) and a reference |

Templates: `templates/`. Agent memory (code-level suppressions, findings ledger) lives **outside** git in `.claude/agent-memory/<agent>/` of the main checkout; skills pass its absolute path to agents (`git rev-parse --path-format=absolute --git-common-dir` → parent dir). Agents never write memory; only the orchestrating skill does, and only verifier-confirmed facts after user approval.

## 2. Candidate (every hunter and review lane emits this)

The orchestrating skill rewrites findings from sources that don't speak this format (the built-in generalist review, an external reviewer's PR comments) into the same block, as `lane: generalist` or `lane: external`.

```
## LANE: <lane> — <N> candidate(s)

### CANDIDATE
- id: <lane>-<n>
- lane: security | debt | sibling-path | docs-truth | test-strength | generalist | external
- title: <concise>
- severity: MAJOR | MINOR | TRIVIAL
- native_severity: <CRITICAL|HIGH|MEDIUM|LOW|INFORMATIONAL for security/debt, else none>
- category: <e.g. BOLA, stale docs, vacuous assertion>
- location: <path:line[-line]>, ...
- in_diff: yes | no
- description: <what is wrong and why it matters>
- evidence: <code/doc excerpt, grep result, call sites checked>
- attack_scenario: <security only, else none>
- effort: S | M | L   (debt only, else none)
- recommendation: <specific fix>
- confidence: <0-100, the finder's own; stripped before verification>

## SUMMARY
<2-4 sentences: what was reviewed (files read in full / skimmed / not read), overall posture.>
```

Zero candidates is valid. Never pad.

### Severity mapping (native → lane)

| Native | Lane severity |
|---|---|
| Security CRITICAL, HIGH, MEDIUM | MAJOR |
| Security LOW | MINOR |
| Security INFORMATIONAL | TRIVIAL |
| Debt CRITICAL | MAJOR |
| Debt HIGH | MAJOR if `in_diff: yes`, else MINOR |
| Debt MEDIUM | MINOR |
| Debt LOW | TRIVIAL |

## 3. Verdict (`finding-verifier` emits one per candidate)

Security candidates: one per call. Debt candidates: up to three per call, each passed as its own block and verdicted separately. Candidate ids in sweeps are prefixed with the region or specialist name so they stay unique (`<region>-security-3`).

```
VERDICT: CONFIRMED | REJECTED | NEEDS-HUMAN
confidence: <0-100, confidence in the verdict>
severity: MAJOR | MINOR | TRIVIAL   (may change, with reason)
reasoning: <cite path:line; what was checked; why>
fix_sketch: <if CONFIRMED>
```

**Filtering is by verdict, never by score.** CONFIRMED is reported/fixed at every severity. REJECTED is dropped with its one-line reason kept in the run record. NEEDS-HUMAN goes to a "needs a decision" list with the unverified precondition stated.

## 4. Output locations (never inside the repo)

- Sweep reports: `~/.claude/gauntlet/reports/<repo>/<date>-<kind>.md`
- `/implement` and `/review` run state: `~/.claude/gauntlet/runs/<repo>/<branch>/` (spec, plan, handoff, brief, review)
- Temporary worktrees for reviewing a head that isn't checked out: `~/.claude/gauntlet/worktrees/<repo>/<slug>`, removed when the review ends
- Escape ledger: `~/.claude/gauntlet/ledger/<repo>.jsonl` (§ 5)
- Session handoffs: `~/.claude/gauntlet/handoffs/<repo>/<date>-<slug>.md`

## 5. Escape ledger (`scripts/ledger.py`)

Append-only JSONL, one file per repo, written only through `ledger.py add` (which validates rows, stamps `date` and `repo`, and skips duplicates). Three row kinds:

| `kind` | One per | Fields | Duplicate key |
|---|---|---|---|
| `run` | self-review round | `branch`, `head`, `round` (0 = first), `scope` (full, delta), `lanes` (list), `candidates`, `confirmed`, `rejected`, `needs_human` | branch + head + round |
| `pr` | PR whose external review was triaged | `pr`, `branch`, `self_reviewed` (a `run` preceded the first external review), `changed_lines`, `external_reviews` | none; the latest row wins |
| `finding` | external-reviewer finding | `pr`, `finding_id` (review comment id), `round` (which external review), `title`, `path`, `line`, `severity`, `class` (bug, docs, tests, i18n, security, debt, ci, style), `verdict`, `outcome` (fixed, declined, filed, open), `lane` | pr + finding_id |

`lane` on a finding is the lane that should have caught it: gate, generalist, sibling-path, docs-truth, test-strength, security, debt, i18n or none. The **escape metric** is CONFIRMED findings on PRs with `self_reviewed: true`, per PR and per kLOC; `ledger.py stats` prints it with the breakdown by lane and the verifier kill rate (rejected ÷ adjudicated across `run` rows).

## 6. Models

Only the aliases `haiku`, `sonnet`, `opus`. Hunters: security `opus`, debt `sonnet`. Verifier: `sonnet`, raised to `opus` by the caller for security candidates and for native CRITICAL/HIGH (or lane MAJOR) of any lane.

Memory path default: `<main checkout>/.claude/agent-memory/<agent-name>/MEMORY.md` (e.g. `security-hunter`, `debt-hunter`); the profile's "Agent memory" section overrides it. `<repo>` in output paths is the main checkout's directory name. Reviewer lanes: per agent frontmatter. Hard disputes go to the user's `/advisor` if configured.

## 7. Agent hygiene

Hunters, reviewers and the verifier are read-only (`tools: Read, Grep, Glob, Bash`; Bash only for read-only commands), never dispatch sub-agents, never write files or memory, and never run tests that touch a database.

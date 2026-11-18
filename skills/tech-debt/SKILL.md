---
name: tech-debt
description: Multi-agent technical-debt sweep or diff review. Runs deterministic metrics, fans out gauntlet:debt-hunter per region and specialist, verifies every candidate with gauntlet:finding-verifier, and writes a report with a metrics trend and PR bundles. Manual invocation only.
argument-hint: "[full | <path> | diff | <rev-range>] [--base <ref>] [--fast | --deep]"
disable-model-invocation: true
---

You orchestrate a technical-debt run. You run in the main session; hunters and verifiers cannot dispatch sub-agents. Make a task list, then follow the phases in order. Everything is static analysis: never run tests, migrations or mutating commands. The only files you write are the report and, after approval, memory.

Arguments: `$ARGUMENTS`

## Phase 0: parse, config, metrics

Parse the first non-flag token as scope:
- empty or `full`: full sweep (regions plus specialists).
- a path or glob: single-region run on that path (region tier from the config if it matches one, else sonnet). No specialists unless the path is repo-wide.
- `diff`: changed files of the current branch against the base.
- a revision range (`a..b`, `v1.2.0..HEAD`): same as diff over that range.

Flags: `--base <ref>`, `--fast` (all hunters sonnet, verifiers sonnet even for HIGH), `--deep` (all hunters opus). Default: tiers from the region map.

Base resolution (diff only): `--base`, else `gh pr view --json baseRefName -q .baseRefName` (prefix `origin/`), else `origin/HEAD`. Use `git merge-base <base> HEAD`; never assume a local `main`. If a brief file exists in the run-state directory, prefer its base SHA.

Load config (all optional; say which are missing and what default replaces them): `.claude/review/profile.md`, `.claude/review/regions.md`, `.claude/review/by-design.md`, a stack pack from the plugin's `stacks/` that matches the repo (read its `## Debt conventions`), CLAUDE.md. Resolve the main checkout for memory: `git rev-parse --path-format=absolute --git-common-dir`, parent directory; memory lives in `<main>/.claude/agent-memory/debt-hunter/` (or the profile's override). Agents never receive a relative memory path.

### Diff and rev-range runs (short path)
No metrics, no grade, no history, no memory proposals, no report unless the user asks. Diff the whole repo, not only the source root: `git diff --name-only <base>...HEAD`. Skip test-only, locale and generated files for triggering. If the changed non-test lines are under ~1500, dispatch one `gauntlet:debt-hunter` in Mode C (write a brief: base, head, branch, repo root, changed files, intent if known; the hunter reads the diff itself). Above that, split by region and dispatch one per region with changes. Route dependency manifests and lockfiles to the `dependencies` specialist, migrations to `consistency`. Then jump to Phase 3 and print confirmed findings, tagging `in_diff: no` ones as pre-existing. Never touch sweep history.

### Full and path runs: deterministic metrics
Compute inline, tracked files only (`git ls-files` / `git grep`, never raw grep over the working tree, which sweeps in logs, caches and build output). Use the profile's `## Debt metrics` commands when present. Otherwise use the generic set in [reference/metrics.md](reference/metrics.md): source and test file counts and lines, files over the length cap and within 5 percent of it, top 20 longest files, functions at the complexity cap if a linter reports it, suppression-marker counts, TODO/FIXME counts, schema migrations per app/directory, function-local imports, dependency count and pins. Record each metric with its exact command so the trend is comparable.

Dead-symbol detection is a script, not a hunter task: run the dead-symbol script from reference/metrics.md (or the profile's equivalent). It lists defined top-level symbols with zero tracked references outside their definition and tests. Keep only its hits; they become candidates `deadscan-<n>` for verification. Do not send the whole symbol list anywhere.

Read open tracker issues when `gh` is available (`gh issue list --state open --limit 100`) and cross-reference in the report so tracked work is not presented as a discovery.

Coverage reconcile: list every tracked non-test source file under the source roots, subtract everything matched by a region's globs (and its context globs do not count as ownership), and report the remainder. If the remainder is non-empty, stop and show it: either add regions or accept an ad-hoc catch-all region (sonnet, full dimensions) for it, and note the map gap in the report. Without a regions file, partition by feature slice across layers yourself, each region under ~15k non-test lines, and say the map is ad hoc.

Show the dispatch plan (region/specialist, globs, tier, tracked suspects) as a short table. In an unattended run continue; otherwise let the user object.

## Phase 1: hunters

Dispatch `gauntlet:debt-hunter` through the Agent tool, at most ~6 per wave, a wave in one message. Model tier: sonnet default; opus when `--deep`, or the region's risk is CRITICAL, or the region file says `tier: opus`. Specialists: `dependencies` (manifests and lockfiles), `tests` (test tree, given the metrics: slowest tests if a report exists, sleep counts, mock density; sample), `consistency` (house rules across regions, evolution debt, broad and shallow).

Prompt per hunter: mode A, region name and globs, context globs, focus dimensions from the region (or the stack pack), the stack pack path, profile and by-design paths, the absolute memory path, suspects from the metrics that fall in its globs (files over the cap, complexity hits, dead-scan hits are not given to hunters, they go to verification), open tracker issues relevant to it, and "do not re-flag known-accepted entries whose paths are unchanged since their SHA". For memory entries whose paths changed since their SHA (`git log <sha>..HEAD -- <path>`), list them as stale and to be re-verified.

Collect every CANDIDATE block and every SUMMARY (the coverage lines feed the report's coverage table).

## Phase 2: dedup

Merge candidates with the same root cause (same location or same smell under different titles): union the locations and evidence, keep the higher native severity, note the merge. Do not merge distinct issues that share a file. Add the dead-scan candidates, deduped against hunter dead-code candidates. Then strip `confidence` from every candidate so the verifier is not anchored; keep it only in your own table for the run record.

## Phase 3: verify

For each surviving candidate dispatch `gauntlet:finding-verifier` with the full candidate block (confidence stripped), the repo root, the by-design and profile paths, and the absolute memory path. Model: sonnet by default; opus for native HIGH or CRITICAL candidates (not under `--fast`). Batching: for debt you may send up to 3 candidates in one verifier call, but pass each as its own separate `### CANDIDATE` block and require one `VERDICT` block per id; never merge or summarise candidates. Dead-code candidates tell the verifier to apply the proof standard: whole-tree search including dynamic and string-based references, templates, config, generated artifacts and sibling repos; any unresolved dynamic reference means not confirmed. At most ~6 verifier calls per wave.

Join verdicts to candidates by id.

## Phase 4: filter by verdict only

- CONFIRMED: reported, at every severity. The verifier's severity wins, with its reason.
- REJECTED: dropped. Keep its one-line reason in the run record (the report's appendix), never as a finding.
- NEEDS-HUMAN: a "needs a decision" list with the unverified precondition stated. For native HIGH or CRITICAL, a second verifier on opus may be dispatched once before listing.

Never filter by confidence or by severity. Fix or file every confirmed finding, however small; cheap ones go to quick wins.

## Phase 5: report

Write `~/.claude/gauntlet/reports/<repo>/<YYYY-MM-DD>-debt.md` (repo = main checkout directory name; create directories; never write inside the repo). Format in [reference/report.md](reference/report.md). Contents:

1. Header: date, repo, head SHA, scope, regions and specialists run with models, config files found or missing.
2. Metrics table with the previous value and delta, where the previous report is the newest `*-debt.md` in the same directory that has a metrics table. Note when a metric command changed and is not comparable. This table is the trend; there is no numeric score.
3. Findings grouped: quick wins (effort S, confirmed), planned refactors (M), strategic (L), then needs-a-decision. Per finding: title, category, locations, evidence summary, effort, recommendation, verifier note. Tracked issues go in an acknowledged band.
4. Suggested PR bundles: group confirmed findings that touch the same files or the same fix pattern into reviewable PRs, each with a title, findings, expected size and risk. Respect the repo's one-concern-per-PR and migration rules from CLAUDE.md.
5. Full sweeps only: a qualitative grade (one of healthy, moderate debt, needs a dedicated cleanup, velocity impacted) with two sentences of justification built from the metrics and confirmed findings. No x/10 number. Say that it is not comparable with other grades.
6. Dead code catalog (confirmed only), coverage table (region, tier, candidates, confirmed, rejected, files read in full or skimmed or not read), appendix of rejected candidates with reasons, notes on unmapped files.

Print a condensed summary in the session (counts, top bundles, report path).

## Phase 6: memory proposals

Propose, do not write. List: new known-accepted patterns (from REJECTED verdicts whose reason is a documented tradeoff, and hunter clean-dimension notes), each as `path, last-verified SHA (current head), one line`; confirmed hotspots only if they are structural and slow-changing; detection-methodology lessons discovered this run. Do not propose metric snapshots, scores, sizes or counts: Phase 0 recomputes them. Remove entries proposed for deletion because their code changed or the debt was paid. Write to `<main>/.claude/agent-memory/debt-hunter/MEMORY.md` in one edit only after the user approves, keeping it under ~100 lines. Sweep outcomes go to the report, not to memory. Diff and rev-range runs propose nothing about history.

## Guardrails

- Precision over volume: a short report on a healthy codebase is a success.
- Be fair: name what the codebase does well and the tradeoffs that are still right.
- Respect by-design and known-accepted entries; if one slips through, drop the candidate and say why.
- Zero candidates is valid at every phase.
- Never use hunter confidence to decide anything. Verdicts decide.

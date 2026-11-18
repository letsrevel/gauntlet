# Gauntlet regions: <repo name>

<!-- Copy to .claude/review/regions.md. Used by /gauntlet:vuln-scan and /gauntlet:tech-debt full sweeps.
Partition by FEATURE SLICE across layers (controllers + services + models + schemas of one feature together),
not by layer: real bugs cross layers. Keep each region under ~15k non-test lines.
Every tracked non-test source file must match at least one region; the sweep fails the plan otherwise.
A region may list `context:` globs it can read but does not own. -->

## <region-name>
- globs: `<glob>`, `<glob>`
- context: `<glob>` (optional, read-only)
- risk: CRITICAL | HIGH | MEDIUM | LOW
- tier: opus | sonnet
- security focus: <surfaces to lead with, e.g. BOLA on order ids, refund caps, webhook trust>
- debt focus: <e.g. complexity in checkout, duplicated pricing logic>

## <next region>
...

## Specialists (debt sweeps, cross-cutting)
- dependencies: manifests and lockfiles
- tests: test tree, metric-driven (slowest tests, sleeps, mock density), sampled
- consistency: house rules across regions

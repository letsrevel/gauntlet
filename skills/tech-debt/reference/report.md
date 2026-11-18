# Report format

```
# Technical debt report: <repo>
Date: <YYYY-MM-DD> · Head: <short sha> · Scope: <full | path | rev-range> · Hunters: <n regions + m specialists, tiers> · Verifiers: <n, tiers>
Config: profile <found|missing> · regions <found|missing|ad hoc> · by-design <found|missing> · stack pack <name|none>

## Summary
<2-3 paragraphs: posture, what moved since the previous report, the single most actionable signal.>
Grade (full sweeps only): <healthy | moderate debt | needs a dedicated cleanup | velocity impacted>. <two sentences from metrics and findings. Not comparable across runs.>

## Metrics (trend)
| Metric | Now | Previous (<date>) | Delta | Command |
|---|---|---|---|---|

## Quick wins (effort S)
### <title> · <category> · <MAJOR|MINOR|TRIVIAL>
- Location: <path:line>, ...
- Evidence: <short>
- Fix: <specific>
- Verifier: <one line>

## Planned refactors (effort M)
## Strategic (effort L)
## Needs a decision
<candidate, the unverified precondition, who can resolve it>
## Acknowledged (already tracked)
<finding, tracker reference>

## Suggested PR bundles
1. <PR title> · findings: <ids> · size: <S|M|L> · risk: <low|med|high> · notes: <ordering, migration or file-cap constraints>

## Dead code catalog (confirmed only)
<symbol, location, test-only or zero references, searches done>

## Coverage
| Region / specialist | Tier | Candidates | Confirmed | Rejected | Read in full / skimmed / not read |
|---|---|---|---|---|---|
Unmapped files and map gaps: <list or none>

## Appendix: rejected candidates
<id, title, one-line reason>

## Positive observations and tradeoffs still right
```

Sections with no content say "none". Do not pad. The previous report is the newest earlier `*-debt.md` in the same directory with a Metrics table; if a metric's command differs, mark the delta "not comparable".

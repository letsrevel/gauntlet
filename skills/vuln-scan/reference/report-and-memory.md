# Report and memory formats

## Report (`~/.claude/gauntlet/reports/<repo>/<date>-security.md`)

```
# Security sweep: <repo> <scope> <date>

Posture: <one line>. <X> confirmed, <Y> need a decision, <Z> rejected. HEAD <sha>, base <sha or none>.
Config: profile <found|missing>, regions <found|fallback: one per top-level dir>, by-design <found|missing>, stack pack <name|none>.

## Confirmed
### [MAJOR] <title>   (native: HIGH, category: <cat>)
- Locations: <path:line>, ...
- Attack scenario: <steps and preconditions>
- Fix: <fix_sketch>
- Verifier: <decisive reasoning, path:line>
(grouped MAJOR, MINOR, TRIVIAL; none: "No confirmed findings.")

## Needs a decision
- <title> (<id>): unverified precondition: <one line>. Locations: <...>

## Rejected
| id | title | reason |

## Coverage
| region | model | read in full | skimmed | not read | candidates | confirmed |

## Notes
Catch-all regions, stale suppressions re-verified, unowned files, hunters that returned malformed output.
```

## Memory directory (`<main checkout>/.claude/agent-memory/security-hunter/`, gitignored)

`MEMORY.md`, at most 100 lines, loaded by hunters and verifiers:

```
# Security memory (index)
## Authorization model
<5 to 10 lines: roles, tenant boundary, where checks live>
## Suppressions (code-level, verified)
- <path> | <sha> | <one line: pattern and the control that makes it safe>
## Last clean
- <region> | <sha>
```

`findings.md`: ledger, one row per finding: `date | id | title | location | status (open, fixed, wont-fix) | found-at SHA | fixed-in ref`. Not auto-loaded.

`sweeps.md`: `date | scope | HEAD sha | confirmed/needs-decision/rejected counts`. Full sweeps only.

Suppression staleness: `git log --oneline <sha>..HEAD -- <path>` non-empty, or the SHA no longer resolves, means stale. Stale entries are passed to hunters and verifiers as "re-verify", never as "safe".

Policy-level intended behaviour does not belong here: it goes in the committed `.claude/review/by-design.md`.

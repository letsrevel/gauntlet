# Deterministic metrics (generic fallbacks)

Prefer the profile's `## Debt metrics` commands. These fallbacks assume a git repo; adapt the source roots and extensions (`SRC`, `EXT`) to the stack. Always run through git so untracked output is excluded.

```bash
SRC='src'            # source root(s); EXT='*.py' or '*.ts' '*.svelte' etc.
files() { git ls-files -- "$SRC" | grep -E "$EXT_RE" | grep -Ev "$EXCLUDE_RE"; }
# EXT_RE e.g. '\.(py)$'; EXCLUDE_RE e.g. '(/tests?/|test_|\.spec\.|\.test\.|/migrations/|/generated/)'
```

| Metric | Command |
|---|---|
| Source files, lines | `files \| wc -l`; `files \| xargs cat \| wc -l` |
| Test files, lines | same with the test pattern inverted |
| Longest files | `files \| xargs wc -l \| sort -rn \| sed -n 2,21p` |
| Files over the cap / within 5% | `files \| xargs wc -l \| awk -v cap=$CAP '$1>cap*0.95 && $2!="total"'` (cap from profile or lint config) |
| Suppression markers | `git grep -c -E 'noqa\|type: ignore\|eslint-disable\|@ts-(ignore\|expect-error)' -- "$SRC"` (sum) |
| TODO/FIXME/HACK | `git grep -c -E 'TODO\|FIXME\|HACK\|XXX' -- "$SRC"` (sum) |
| Function-local imports | Python: `git grep -c -E '^\s+(from\|import) ' -- "$SRC"` minus type-checking blocks; JS/TS: `git grep -c -E '^\s+(await )?import\(' -- "$SRC"` |
| Schema migrations per app | `git ls-files -- '*/migrations/*' \| grep -v __init__ \| awk -F/ '{print $(NF-2)}' \| sort \| uniq -c` (adapt the path depth); exclude data migrations if named |
| Complexity at the cap | the repo linter in report mode, e.g. `ruff check --select C901 --output-format concise`, `eslint --rule 'complexity: [error, N]' -f unix` |
| Dependencies | count and pins from the manifest; outdated: `uv pip list --outdated`, `pnpm outdated`, `npm outdated`, `cargo outdated` when available |

Record the exact command with every value in the report so the next run is comparable.

## Dead-symbol script (hits only)

Language-specific; write it to a temp location outside the repo and run it. Principle:

1. Extract top-level definitions (functions, classes, constants, exported components) from tracked production source with a parser when one is available (Python `ast`, TypeScript `ts-morph` or `tsc`, otherwise `git grep -n -E '^(def|class|export (function|const|class)) '`).
2. For each name, `git grep -w -c -- <name>` across the whole tracked tree (production, tests, templates, config, docs, sibling repos named in the profile). A hit is a name whose only references are its own definition (and optionally tests, reported as test-only).
3. Drop names that are framework entry points by convention (dunder methods, route handlers registered by decorator, signal receivers, task decorators with string names, file-based route modules such as `+page.svelte`, management commands, `__all__` members).
4. Output `name  path:line  test-only|zero-refs`. Send only these hits to verification; the verifier applies the full proof standard.

Names assembled at runtime (`getattr`, registries, dotted paths in config) defeat the script: the verifier, not the script, decides.

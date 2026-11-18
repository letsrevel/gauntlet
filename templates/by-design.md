# By design: <repo name>

<!-- Copy to .claude/review/by-design.md. Policy-level intended behaviour only: what the product deliberately does,
and the boundary that is STILL a bug. No exploit detail, no code-level "confirmed secure" notes (those belong in
gitignored agent memory with a commit SHA). Reviewers and verifiers read this before reporting.
This file can double as the out-of-scope list in SECURITY.md. -->

## <short name>
- behaviour: <what happens, and that it is intended>
- boundary: <what must still hold; violating this IS a bug>
- reference: <ADR, doc, test or issue>

## Example: shareable invitation links
- behaviour: anyone holding a valid invitation link can claim it; links are bearer tokens by design.
- boundary: a claim must still respect bans, expiry, usage limits, scope and the role ceiling of the link.
- reference: docs/<...>

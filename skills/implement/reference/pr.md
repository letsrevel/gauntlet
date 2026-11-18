# PR and external review

## Open the PR

- If the branch is behind its base, update it the way the profile says (default: rebase, never merge the base in). Rerun the gate if that pulled anything in.
- Push once. Batch fix commits; don't push piecemeal while an external reviewer is working.
- Open the PR with a conventional title and this body:

```
## Summary        what and why, linked issue
## Changes        bullets by area
## Docs           files updated
## Tests          what was added; targeted commands run
## Self-review    lanes run · confirmed/fixed · rejected · filed follow-ups
## Assumptions    deploy topology, by-design choices, anything a reviewer without project context would flag
```

Follow the harness's attribution instructions. No customer names or other real identifiers in titles, bodies or commits.

## External reviewer

Per the profile (e.g. an AI review bot). If the profile names none, skip this section.

- Skip it for the PR classes the profile exempts (e.g. internal-only tooling).
- Wait for its review; respect any rate limit the profile states, and re-request at most once after batched fixes.
- For every finding, including ones outside the diff range: verify against the code, then fix, or reply with the evidence for declining. Don't fix what you haven't verified; don't decline without a reason.
- Batch fixes into one push → gate → delta review → one re-review request.
- Record each finding in `review.md`: valid or not, and the lane that should have caught it.

## Merging

Never merge and never enable auto-merge unless the user explicitly OKs this PR in this conversation. When they do, follow the profile's merge policy and confirm the result. Resolving review threads on the user's behalf needs their OK.

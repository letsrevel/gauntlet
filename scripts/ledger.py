#!/usr/bin/env python3
"""Gauntlet escape ledger.

  fetch <PR> --author <login>   print an external reviewer's findings on a PR as JSON
  add                           append rows (a JSON object or array on stdin); safe to run concurrently
  stats                         print the escape metric

Ledger: ~/.claude/gauntlet/ledger/<repo>.jsonl, append-only, never inside a repo.
Row contract: CONTRACTS.md section 5. Standard library only; fetch needs the gh CLI.
"""

import argparse
import datetime
import fcntl
import json
import os
import pathlib
import subprocess
import sys
import typing as t
from collections import Counter

LANES = {"gate", "generalist", "sibling-path", "docs-truth", "test-strength", "security", "debt", "i18n", "none"}
ENUMS = {
    "severity": {"MAJOR", "MINOR", "TRIVIAL"},
    "class": {"bug", "docs", "tests", "i18n", "security", "debt", "ci", "style"},
    "verdict": {"CONFIRMED", "REJECTED", "NEEDS-HUMAN"},
    "outcome": {"fixed", "declined", "filed", "open"},
    "lane": LANES,
    "scope": {"full", "delta"},
}
REQUIRED = {
    "run": ["branch", "head", "round", "scope", "lanes", "candidates", "confirmed", "rejected", "needs_human"],
    "pr": ["pr", "branch", "self_reviewed", "changed_lines", "external_reviews"],
    "finding": ["pr", "finding_id", "round", "title", "severity", "class", "verdict", "outcome", "lane"],
}
INTS = {"pr", "round", "candidates", "confirmed", "rejected", "needs_human", "changed_lines", "external_reviews"}
TYPES = {"self_reviewed": bool, "lanes": list, "branch": str, "head": str, "finding_id": str, "title": str}
# A row with the same key as an existing one is skipped, except a finding last logged as "open",
# which a later row may settle. "pr" rows have no key: the latest wins.
KEYS = {"run": ["branch", "head", "round"], "finding": ["pr", "finding_id"]}
MAX_BODY = 4000  # inline thread bodies only; each carries a url to the full text

QUERY = """
query($owner: String!, $name: String!, $pr: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $pr) {
      additions deletions headRefName
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          isResolved isOutdated path line
          all: comments { totalCount }
          comments(first: 1) {
            nodes { databaseId body url author { login } pullRequestReview { databaseId } }
          }
        }
      }
    }
  }
}
"""


def sh(*cmd: str) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def repo_name() -> str:
    """Directory name of the main checkout (the same for every worktree of a repo)."""
    return pathlib.Path(sh("git", "rev-parse", "--path-format=absolute", "--git-common-dir")).parent.name


def ledger_path(repo: str) -> pathlib.Path:
    home = pathlib.Path(os.environ.get("GAUNTLET_HOME", "~/.claude/gauntlet")).expanduser()
    return home / "ledger" / f"{repo}.jsonl"


def parse(lines: t.Iterable[str]) -> list[dict]:
    # Iterate file lines, never str.splitlines(): that also splits on U+2028 inside a JSON string.
    return [json.loads(line) for line in lines if line.strip()]


def load(repo: str) -> list[dict]:
    path = ledger_path(repo)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return parse(fh)


def latest_findings(rows: list[dict]) -> dict[tuple, dict]:
    """One row per finding: a later row for the same key replaces the earlier one."""
    return {row_key(r): r for r in rows if r["kind"] == "finding"}


def row_key(row: dict) -> tuple | None:
    fields = KEYS.get(row["kind"])
    return (row["kind"], *(str(row[f]) for f in fields)) if fields else None


def clip(text: str) -> str:
    return text if len(text) <= MAX_BODY else text[:MAX_BODY] + "\n[truncated; full text at the url]"


def login(name: str | None) -> str:
    return (name or "").lower().removesuffix("[bot]")


def cmd_fetch(args: argparse.Namespace) -> None:
    repo = json.loads(sh("gh", "repo", "view", "--json", "owner,name"))
    owner, name = repo["owner"]["login"], repo["name"]
    base = ["gh", "api", "graphql", "-f", f"query={QUERY}", "-F", f"pr={args.pr}", "-f", f"owner={owner}"]
    base += ["-f", f"name={name}"]
    threads, cursor, pr = [], None, {}
    while True:
        out = json.loads(sh(*base, *(["-f", f"cursor={cursor}"] if cursor else [])))
        pr = out["data"]["repository"]["pullRequest"]
        threads += pr["reviewThreads"]["nodes"]
        page = pr["reviewThreads"]["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]
    # Reviews come from REST: it paginates in one call, and review bodies carry outside-diff findings.
    all_reviews = parse(sh("gh", "api", "--paginate", f"repos/{owner}/{name}/pulls/{args.pr}/reviews",
                           "--jq", ".[] | {id, submitted_at, body, url: .html_url, author: .user.login}").split("\n"))  # fmt: skip
    author = login(args.author)
    reviews = sorted((r for r in all_reviews if login(r["author"]) == author), key=lambda r: r["submitted_at"] or "")
    rounds = {r["id"]: i for i, r in enumerate(reviews, 1)}
    first_review_at = reviews[0]["submitted_at"] if reviews else None

    ledger = load(args.repo)
    logged = {key[2]: row["outcome"] for key, row in latest_findings(ledger).items() if row["pr"] == args.pr}
    findings = []
    for thread in threads:
        first = (thread["comments"]["nodes"] or [None])[0]
        if not first or login((first["author"] or {}).get("login")) != author:
            continue
        finding_id = str(first["databaseId"])
        findings.append({
            "finding_id": finding_id,
            "round": rounds.get((first["pullRequestReview"] or {}).get("databaseId"), 1),
            "path": thread["path"],
            "line": thread["line"],
            "resolved": thread["isResolved"],
            "outdated": thread["isOutdated"],
            "replies": thread["all"]["totalCount"] - 1,
            "url": first["url"],
            "logged": logged.get(finding_id),
            "body": clip(first["body"]),
        })  # fmt: skip
    branch = pr["headRefName"]
    json.dump({
        "repo": args.repo,
        "pr": args.pr,
        "branch": branch,
        "changed_lines": pr["additions"] + pr["deletions"],
        "external_reviews": len(reviews),
        "first_review_at": first_review_at,
        # A self-review round was logged for this branch before the reviewer first posted.
        "self_reviewed": any(r["kind"] == "run" and r["branch"] == branch
                             and (first_review_at is None or r.get("at", "") < first_review_at) for r in ledger),
        "logged_body_findings": {fid: outcome for fid, outcome in logged.items() if fid.startswith("body-")},
        "findings": findings,
        "review_bodies": [
            {"review_id": r["id"], "round": rounds[r["id"]], "url": r["url"], "body": r["body"]}
            for r in reviews if (r["body"] or "").strip()
        ],
    }, sys.stdout, indent=1)  # fmt: skip
    print()


def validate(row: dict) -> None:
    kind = row.get("kind")
    if kind not in REQUIRED:
        sys.exit(f"ledger: unknown kind {kind!r}; expected one of {sorted(REQUIRED)}")
    if missing := [f for f in REQUIRED[kind] if f not in row]:
        sys.exit(f"ledger: {kind} row is missing {missing}")
    for field, allowed in ENUMS.items():
        if field in row and row[field] not in allowed:
            sys.exit(f"ledger: {field}={row[field]!r}; expected one of {sorted(allowed)}")
    for field, value in row.items():
        expected = int if field in INTS else TYPES.get(field)
        # bool is a subclass of int; a true/false count is still wrong
        if expected and (not isinstance(value, expected) or (expected is int and isinstance(value, bool))):
            sys.exit(f"ledger: {field}={value!r}; expected {expected.__name__}")
    if unknown := set(row.get("lanes", [])) - LANES:
        sys.exit(f"ledger: unknown lanes {sorted(unknown)}; expected a subset of {sorted(LANES)}")


def cmd_add(args: argparse.Namespace) -> None:
    rows = json.load(sys.stdin)
    rows = rows if isinstance(rows, list) else [rows]
    for row in rows:
        validate(row)  # all rows are checked before any is written
    path = ledger_path(args.repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.UTC)
    added = 0
    with path.open("a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)  # held from the duplicate check to the last write
        fh.seek(0)
        existing = parse(fh)
        seen = {row_key(r) for r in existing} - {None}
        still_open = {key for key, r in latest_findings(existing).items() if r["outcome"] == "open"}
        for row in rows:
            key = row_key(row)
            settles = key in still_open and row.get("outcome") != "open"
            if key is not None and key in seen and not settles:
                continue
            if key is not None:
                seen.add(key)
                still_open.discard(key)
            stamped = {"date": now.date().isoformat(), "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "repo": args.repo}
            fh.write(json.dumps(stamped | row, ensure_ascii=False) + "\n")
            added += 1
    print(f"ledger: {added} added, {len(rows) - added} already logged -> {path}")


def ratio(num: float, den: float, digits: int = 2) -> str:
    return f"{num / den:.{digits}f}" if den else "n/a"


def cmd_stats(args: argparse.Namespace) -> None:
    rows = [r for r in load(args.repo) if r["date"] >= (args.since or "")]
    prs = {r["pr"]: r for r in rows if r["kind"] == "pr"}  # the latest row per PR wins
    reviewed = {n for n, r in prs.items() if r["self_reviewed"]}
    findings = list(latest_findings(rows).values())
    valid = [f for f in findings if f["verdict"] == "CONFIRMED"]
    escapes = [f for f in valid if f["pr"] in reviewed]
    kloc = sum(prs[n]["changed_lines"] for n in reviewed) / 1000
    runs = [r for r in rows if r["kind"] == "run"]
    confirmed, rejected = sum(r["confirmed"] for r in runs), sum(r["rejected"] for r in runs)

    print(f"Escape ledger: {args.repo}" + (f" since {args.since}" if args.since else ""))
    print(f"  PRs logged: {len(prs)} ({len(reviewed)} self-reviewed before the external review)")
    print(f"  External findings: {len(findings)}, valid {len(valid)}, "
          f"declined {sum(f['verdict'] == 'REJECTED' for f in findings)}")  # fmt: skip
    print(f"  Escapes (valid, on self-reviewed PRs): {len(escapes)}"
          f" = {ratio(len(escapes), len(reviewed))} per PR, {ratio(len(escapes), kloc)} per kLOC,"
          f" {sum(f['severity'] == 'MAJOR' for f in escapes)} MAJOR")  # fmt: skip
    print(f"  Arriving after round 1: {ratio(100 * sum(f['round'] > 1 for f in valid), len(valid), 0)}% of valid;"
          f" external reviews per PR: {ratio(sum(p['external_reviews'] for p in prs.values()), len(prs), 1)}")  # fmt: skip
    print("  Escapes by lane that should have caught them:")
    for lane, count in Counter(f["lane"] for f in escapes).most_common():
        print(f"    {lane:<14}{count}")
    print(f"  Self-review rounds: {len(runs)}; verifier kill rate:"
          f" {ratio(100 * rejected, confirmed + rejected, 0)}% ({rejected} of {confirmed + rejected} adjudicated)")  # fmt: skip


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", help="ledger name (default: the main checkout's directory name)")
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch")
    fetch.add_argument("pr", type=int)
    fetch.add_argument("--author", required=True, help="reviewer login (case-insensitive; a [bot] suffix is ignored)")
    sub.add_parser("add")
    stats = sub.add_parser("stats")
    stats.add_argument("--since", help="only rows dated YYYY-MM-DD or later")
    args = parser.parse_args()
    args.repo = args.repo or repo_name()
    {"fetch": cmd_fetch, "add": cmd_add, "stats": cmd_stats}[args.command](args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
r"""PR readiness check (Stories 2 and 3 of `2026-11-06-pr-ready-and-ledger`).

Judges a saved `gh` snapshot of one pull request and reports every reason it
is not ready to merge, typed by class, with one exit code per class. It reads
only the snapshot file, the verification ledger, and local git. It makes no
network call, writes nothing, and never sleeps or loops.

CLI:
  pr-ready.py check --snapshot FILE [--repo DIR] [--json]

  --snapshot  a pr-ready-snapshot/1 file written by the commands below
  --repo      the checkout the snapshot belongs to (default .): its
              .writ/state/verify-ledger.json and git objects feed the ledger
              gate
  --json      print one JSON object instead of the verdict lines

Snapshot (pr-ready-snapshot/1): {"schema": "pr-ready-snapshot/1",
"view": <stdout of gh pr view>, "threads": <stdout of gh api graphql>}.
Write it with these commands, run from the repository root. $N is the PR
number and $SNAP the snapshot path (suggested: .writ/state/pr-ready/pr-$N.json).

VIEW=$(gh pr view "$N" --json number,url,state,isDraft,mergeable,mergeStateStatus,reviewDecision,headRefOid,baseRefName,statusCheckRollup) &&
THREADS=$(gh api graphql -F owner='{owner}' -F name='{repo}' -F number="$N" -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){number headRefOid reviewThreads(first:100){totalCount pageInfo{hasNextPage} nodes{id isResolved isOutdated path line comments(first:1){nodes{author{login}}}}}}}}') &&
printf '{"schema":"pr-ready-snapshot/1","view":%s,"threads":%s}\n' "$VIEW" "$THREADS" > "$SNAP.tmp" && mv "$SNAP.tmp" "$SNAP"

The query requests no comment body, and the script reads none even when a
snapshot carries one. Fields read (extra keys are ignored):
  view.number int >= 1; view.state OPEN|CLOSED|MERGED; view.isDraft bool;
  view.mergeable MERGEABLE|CONFLICTING|UNKNOWN; view.mergeStateStatus
  CLEAN|HAS_HOOKS|UNSTABLE|BLOCKED|BEHIND|DIRTY|DRAFT|UNKNOWN;
  view.reviewDecision APPROVED|CHANGES_REQUESTED|REVIEW_REQUIRED|""|null;
  view.headRefOid 40 lowercase hex; view.statusCheckRollup list or null;
  threads.data.repository.pullRequest.{number (= view.number), headRefOid,
  reviewThreads.totalCount, reviewThreads.pageInfo.hasNextPage,
  reviewThreads.nodes[].{id, isResolved, isOutdated, path, line,
  comments.nodes[0].author.login}} (path, line, and the comments chain may
  be null).
  statusCheckRollup entries: CheckRun (name, status, conclusion) passes on
  COMPLETED with SUCCESS|NEUTRAL|SKIPPED, is pending on
  QUEUED|IN_PROGRESS|WAITING|PENDING|REQUESTED, and fails on COMPLETED with
  FAILURE|TIMED_OUT|CANCELLED|ACTION_REQUIRED|STARTUP_FAILURE|STALE.
  StatusContext (context, state) passes on SUCCESS, is pending on
  PENDING|EXPECTED, and fails on FAILURE|ERROR.

Blocker classes, in order, with their exit codes:
  3 conflicts           mergeable CONFLICTING or merge state DIRTY
  4 unresolved_threads  one line per thread with isResolved false
  5 failing_checks      one line per failing check, required or not
  6 merge_gates         one line per gate; each detail starts with its token:
      draft               isDraft, or merge state DRAFT
      changes_requested   reviewDecision CHANGES_REQUESTED
      review_required     reviewDecision REVIEW_REQUIRED
      not_open <STATE>    state is not OPEN
      behind              merge state BEHIND
      not_verified        the ledger does not read VERIFIED for the head:
                          `not_verified head <short>: <first ledger reason>`, or
                          `not_verified ledger_unreadable (<detail>)`
      merge_state_blocked merge state BLOCKED, no other blocker but
                          not_verified, no pending check
Unknowns, in order:
  mergeable_unknown                 mergeable or merge state UNKNOWN
  checks_pending <name>[, <name>]   a check is still running
  threads_truncated <n> of <total>  more than one page of review threads
  head_moved <view> <threads>       the two gh calls saw different heads
  merge_state_unexplained UNSTABLE  UNSTABLE with no failing or pending check

Output (check shape):
  <verdict>                          pass | fail | unverifiable
  reason: <class>: <detail>          every blocker, class order
  reason: unknown: <code> [detail]   every unknown
  pr-ready: <verdict> (<summary>)
Summaries: `pr-ready: pass (PR <n> head <short>, ledger VERIFIED)`,
`pr-ready: fail (PR <n> head <short>, blockers: <classes>; exit <code>)`,
`pr-ready: unverifiable (PR <n> head <short>, unknown: <codes>)`.
A thread prints as `<id> <path|?>:<line|?> by <login|?>`, plus ` outdated`.
A check prints as `<name> <conclusion or state>`. Control characters in
printed snapshot strings are escaped (`\n`, `\x1b`, `\u2028`), so each
`reason:` line stays one line.

Verdict: `fail` when a blocker holds; else `unverifiable` when an unknown
holds; else `pass`, which needs the ledger to read VERIFIED. Exit 0 pass or
unverifiable; 3, 4, 5, or 6 for `fail`, the first class present; 2 for a
usage error, a snapshot that cannot be judged (missing, not JSON, wrong
schema, GraphQL errors, a missing or mistyped field, an unrecognized enum
value, PR numbers that differ), or a `verify-ledger.py` that cannot be
loaded: stdout empty, cause on stderr after `pr-ready: `. The script never
exits 1 on purpose, so exit 1 means it crashed.

Ledger gate: the script loads `verify-ledger.py` from its own directory on
first use and calls `ledger_check(repo, pr=view.number, head=view.headRefOid)`
(no base: the ledger uses the PR's latest row's `base_ref`). VERIFIED means
the exact head, or a same-PR `git patch-id --verbatim` match. A missing or
broken `verify-ledger.py` exits 2 with `pr-ready: cannot load
verify-ledger.py (<cause>)`. An unreadable ledger file is not exit 2: it is
the `not_verified ledger_unreadable` gate, so the other blockers still print.

--json: all of stdout is one object, the exit code is the text run's, and
the exit-2 paths are unchanged:
  {"verdict": "fail", "exit": 6, "pr": 66, "head": "<40 hex headRefOid>",
   "blockers": [{"class": "merge_gates", "detail": "not_verified head ..."}],
   "unknowns": [{"code": "checks_pending", "detail": "ci/test"}],
   "ledger": {"verdict": "fail", "reasons": ["patch_id_mismatch ..."]}}
A detail is the text after `reason: <class>: ` (or `reason: unknown:
<code> `), so a merge_gates detail starts with its gate token. Strings are
JSON-escaped, not escaped as in the text output.

Stdlib only, Python 3.9.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

SCHEMA = "pr-ready-snapshot/1"
SHORT = 7
HEX40 = re.compile(r"^[0-9a-f]{40}\Z")  # \Z: `$` would accept a final newline
# C0, DEL, C1, and the Unicode line and paragraph separators: any of them in a
# printed value could start a new output line.
CONTROL = re.compile("[\x00-\x1f\x7f-\x9f\u2028\u2029]")

STATES = ("OPEN", "CLOSED", "MERGED")
MERGEABLE = ("MERGEABLE", "CONFLICTING", "UNKNOWN")
MERGE_STATES = ("CLEAN", "HAS_HOOKS", "UNSTABLE", "BLOCKED", "BEHIND", "DIRTY", "DRAFT",
                "UNKNOWN")
REVIEW_DECISIONS = ("APPROVED", "CHANGES_REQUESTED", "REVIEW_REQUIRED", "", None)
RUN_PASSING = ("SUCCESS", "NEUTRAL", "SKIPPED")
RUN_FAILING = ("FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE",
               "STALE")
RUN_PENDING = ("QUEUED", "IN_PROGRESS", "WAITING", "PENDING", "REQUESTED")
CONTEXT_PASSING = ("SUCCESS",)
CONTEXT_PENDING = ("PENDING", "EXPECTED")
CONTEXT_FAILING = ("FAILURE", "ERROR")

CLASSES = ("conflicts", "unresolved_threads", "failing_checks", "merge_gates")
CLASS_EXIT = {"conflicts": 3, "unresolved_threads": 4, "failing_checks": 5, "merge_gates": 6}

LEDGER_SCRIPT = "verify-ledger.py"
UNREADABLE = "ledger_unreadable"


class SnapshotError(Exception):
    """The snapshot cannot be judged (exit 2)."""


class LedgerLoadError(Exception):
    """The sibling `verify-ledger.py` cannot be loaded (exit 2)."""


class Result(NamedTuple):
    verdict: str
    exit: int
    pr: int
    head: str
    blockers: List[Tuple[str, str]]   # (class, detail), class order
    unknowns: List[Tuple[str, str]]   # (code, detail); detail may be ""
    ledger: Optional[Dict[str, Any]]  # {verdict, reasons} from the ledger gate; None without it


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def printable(text: str) -> str:
    """Escape control characters (`\\n` -> `\\\\n`, ESC -> `\\\\x1b`) so a crafted
    value cannot add an output line. Other text is unchanged."""
    return CONTROL.sub(lambda m: repr(m.group())[1:-1], text)


# ---------------------------------------------------------------------------
# Snapshot validation
# ---------------------------------------------------------------------------

def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _get(obj: Dict[str, Any], key: str, where: str) -> Any:
    if key not in obj:
        raise SnapshotError("missing field %s" % where)
    return obj[key]


def _object(value: Any, where: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise SnapshotError("%s missing or not an object" % where)
    return value


def _str(obj: Dict[str, Any], key: str, where: str, nullable: bool = False) -> Optional[str]:
    value = _get(obj, key, where)
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise SnapshotError("field %s is not a string" % where)
    return value


def _int(obj: Dict[str, Any], key: str, where: str, nullable: bool = False) -> Optional[int]:
    value = _get(obj, key, where)
    if value is None and nullable:
        return None
    if not _is_int(value):
        raise SnapshotError("field %s is not an integer" % where)
    return value


def _bool(obj: Dict[str, Any], key: str, where: str) -> bool:
    value = _get(obj, key, where)
    if not isinstance(value, bool):
        raise SnapshotError("field %s is not a boolean" % where)
    return value


def _shown(value: Any) -> str:
    """A rejected value for stderr: strings (cut to 80) and scalars as they
    are, containers only by type, so a crafted snapshot cannot echo text."""
    if isinstance(value, str):
        return value[:80]
    if value is None or isinstance(value, (bool, int, float)):
        return json.dumps(value)
    return "<%s>" % type(value).__name__


def _enum(value: Any, allowed: Sequence[Any], where: str) -> Any:
    if isinstance(value, bool) or not isinstance(value, (str, type(None))) \
            or value not in allowed:
        raise SnapshotError("unrecognized %s %s" % (where, _shown(value)))
    return value


def _head(obj: Dict[str, Any], key: str, where: str) -> str:
    value = _str(obj, key, where)
    if not HEX40.match(value or ""):
        raise SnapshotError("field %s is not 40 lowercase hex" % where)
    return value  # type: ignore[return-value]


def _check_entry(i: int, entry: Any) -> None:
    where = "view.statusCheckRollup[%d]" % i
    entry = _object(entry, where)
    kind = _enum(_get(entry, "__typename", where + ".__typename"),
                 ("CheckRun", "StatusContext"), where + ".__typename")
    if kind == "CheckRun":
        _str(entry, "name", where + ".name")
        status = _enum(_get(entry, "status", where + ".status"),
                       ("COMPLETED",) + RUN_PENDING, where + ".status")
        conclusion = _get(entry, "conclusion", where + ".conclusion")
        allowed = RUN_PASSING + RUN_FAILING
        if status != "COMPLETED":
            allowed = allowed + ("", None)
        _enum(conclusion, allowed, where + ".conclusion")
    else:
        _str(entry, "context", where + ".context")
        _enum(_get(entry, "state", where + ".state"),
              CONTEXT_PASSING + CONTEXT_PENDING + CONTEXT_FAILING, where + ".state")


def _thread_node(i: int, node: Any) -> None:
    where = "threads...reviewThreads.nodes[%d]" % i
    node = _object(node, where)
    _str(node, "id", where + ".id")
    _bool(node, "isResolved", where + ".isResolved")
    _bool(node, "isOutdated", where + ".isOutdated")
    _str(node, "path", where + ".path", nullable=True)
    _int(node, "line", where + ".line", nullable=True)
    chain = node.get("comments")
    if chain is not None:
        nodes = _object(chain, where + ".comments").get("nodes")
        if nodes is not None and not isinstance(nodes, list):
            raise SnapshotError("field %s.comments.nodes is not a list" % where)
        first = nodes[0] if nodes else None
        if first is not None:
            author = _object(first, where + ".comments.nodes[0]").get("author")
            if author is not None:
                login = _object(author, where + ".comments.nodes[0].author").get("login")
                if login is not None and not isinstance(login, str):
                    raise SnapshotError("field %s.comments.nodes[0].author.login is not a "
                                        "string" % where)


def validate(snap: Any) -> Dict[str, Any]:
    """Raise SnapshotError for any snapshot that cannot be judged."""
    snap = _object(snap, "snapshot")
    if snap.get("schema") != SCHEMA:
        raise SnapshotError("schema %s is not %s" % (_shown(snap.get("schema")), SCHEMA))
    view = _object(snap.get("view"), "view")
    threads = _object(snap.get("threads"), "threads")
    if "errors" in threads:
        raise SnapshotError("threads has GraphQL errors")

    number = _int(view, "number", "view.number")
    if number is None or number < 1:
        raise SnapshotError("field view.number is below 1")
    _enum(_get(view, "state", "view.state"), STATES, "view.state")
    _bool(view, "isDraft", "view.isDraft")
    _enum(_get(view, "mergeable", "view.mergeable"), MERGEABLE, "view.mergeable")
    _enum(_get(view, "mergeStateStatus", "view.mergeStateStatus"), MERGE_STATES,
          "view.mergeStateStatus")
    _enum(_get(view, "reviewDecision", "view.reviewDecision"), REVIEW_DECISIONS,
          "view.reviewDecision")
    _head(view, "headRefOid", "view.headRefOid")
    rollup = _get(view, "statusCheckRollup", "view.statusCheckRollup")
    if rollup is not None and not isinstance(rollup, list):
        raise SnapshotError("field view.statusCheckRollup is not a list")
    for i, entry in enumerate(rollup or []):
        _check_entry(i, entry)

    data = _object(threads.get("data"), "threads.data")
    repository = _object(data.get("repository"), "threads.data.repository")
    pr_where = "threads.data.repository.pullRequest"
    pull = _object(repository.get("pullRequest"), pr_where)
    if _int(pull, "number", pr_where + ".number") != number:
        raise SnapshotError("view.number %d differs from %s.number %d"
                            % (number, pr_where, pull["number"]))
    _head(pull, "headRefOid", pr_where + ".headRefOid")
    review = _object(pull.get("reviewThreads"), pr_where + ".reviewThreads")
    _int(review, "totalCount", pr_where + ".reviewThreads.totalCount")
    page = _object(review.get("pageInfo"), pr_where + ".reviewThreads.pageInfo")
    _bool(page, "hasNextPage", pr_where + ".reviewThreads.pageInfo.hasNextPage")
    nodes = _get(review, "nodes", pr_where + ".reviewThreads.nodes")
    if not isinstance(nodes, list):
        raise SnapshotError("field %s.reviewThreads.nodes is not a list" % pr_where)
    for i, node in enumerate(nodes):
        _thread_node(i, node)
    return snap


def load_snapshot(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise SnapshotError("cannot read (%s)" % exc)
    try:
        snap = json.loads(text)
    except (ValueError, RecursionError) as exc:
        raise SnapshotError("not JSON (%s)" % exc)
    return validate(snap)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _thread_line(node: Dict[str, Any]) -> str:
    login = None
    nodes = (node.get("comments") or {}).get("nodes") or []
    if nodes and nodes[0]:
        login = (nodes[0].get("author") or {}).get("login")
    path = node["path"] if node["path"] is not None else "?"
    line = str(node["line"]) if node["line"] is not None else "?"
    text = "%s %s:%s by %s" % (node["id"], path, line, login if login is not None else "?")
    return text + (" outdated" if node["isOutdated"] else "")


def _checks(rollup: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """(failing lines, pending names), snapshot order."""
    failing: List[str] = []
    pending: List[str] = []
    for entry in rollup:
        if entry["__typename"] == "CheckRun":
            if entry["status"] != "COMPLETED":
                pending.append(entry["name"])
            elif entry["conclusion"] in RUN_FAILING:
                failing.append("%s %s" % (entry["name"], entry["conclusion"]))
        elif entry["state"] in CONTEXT_PENDING:
            pending.append(entry["context"])
        elif entry["state"] in CONTEXT_FAILING:
            failing.append("%s %s" % (entry["context"], entry["state"]))
    return failing, pending


LedgerGate = Callable[[int, str], Tuple[str, List[str]]]


def evaluate(snap: Dict[str, Any], ledger: Optional[LedgerGate] = None) -> Result:
    """Judge a validated snapshot. `ledger(pr, head)` returns the ledger's
    ("pass" | "fail", reasons); the CLI always passes one (`ledger_gate`).
    Without it no `not_verified` gate is judged and a `pass` summary does not
    claim `ledger VERIFIED`."""
    view = snap["view"]
    pull = snap["threads"]["data"]["repository"]["pullRequest"]
    review = pull["reviewThreads"]
    pr, head = view["number"], view["headRefOid"]
    merge_state = view["mergeStateStatus"]
    failing, pending = _checks(view["statusCheckRollup"] or [])

    blockers: List[Tuple[str, str]] = []
    if view["mergeable"] == "CONFLICTING" or merge_state == "DIRTY":
        blockers.append(("conflicts", "mergeable %s (merge state %s)"
                         % (view["mergeable"], merge_state)))
    blockers += [("unresolved_threads", _thread_line(node))
                 for node in review["nodes"] if not node["isResolved"]]
    blockers += [("failing_checks", line) for line in failing]

    gates: List[str] = []
    if view["isDraft"] or merge_state == "DRAFT":
        gates.append("draft")
    if view["reviewDecision"] == "CHANGES_REQUESTED":
        gates.append("changes_requested")
    if view["reviewDecision"] == "REVIEW_REQUIRED":
        gates.append("review_required")
    if view["state"] != "OPEN":
        gates.append("not_open %s" % view["state"])
    if merge_state == "BEHIND":
        gates.append("behind")
    # `not_verified` is Writ's record, not GitHub's: it never explains BLOCKED.
    explained = bool(blockers or gates or pending)
    ledger_info: Optional[Dict[str, Any]] = None
    if ledger is not None:
        answer, reasons = ledger(pr, head)
        ledger_info = {"verdict": answer, "reasons": list(reasons)}
        if answer != "pass":
            first = reasons[0] if reasons else "no reason given"
            if first.startswith(UNREADABLE + " "):
                gates.append("not_verified %s" % first)
            else:
                gates.append("not_verified head %s: %s" % (head[:SHORT], first))
    # Computed last, from the other blockers and pending checks only.
    if merge_state == "BLOCKED" and not explained:
        gates.append("merge_state_blocked")
    blockers += [("merge_gates", gate) for gate in gates]

    unknowns: List[Tuple[str, str]] = []
    if view["mergeable"] == "UNKNOWN" or merge_state == "UNKNOWN":
        unknowns.append(("mergeable_unknown", ""))
    if pending:
        unknowns.append(("checks_pending", ", ".join(pending)))
    if review["pageInfo"]["hasNextPage"]:
        unknowns.append(("threads_truncated", "%d of %d" % (len(review["nodes"]),
                                                            review["totalCount"])))
    if pull["headRefOid"] != head:
        unknowns.append(("head_moved", "%s %s" % (head[:SHORT], pull["headRefOid"][:SHORT])))
    if merge_state == "UNSTABLE" and not failing and not pending:
        unknowns.append(("merge_state_unexplained", "UNSTABLE"))

    if blockers:
        verdict, code = "fail", CLASS_EXIT[blockers[0][0]]
    elif unknowns:
        verdict, code = "unverifiable", 0
    else:
        verdict, code = "pass", 0
    return Result(verdict, code, pr, head, blockers, unknowns, ledger_info)


def render(result: Result) -> List[str]:
    """The text output lines: verdict, reasons, summary."""
    lines = [result.verdict]
    lines += ["reason: %s: %s" % (cls, printable(detail)) for cls, detail in result.blockers]
    lines += ["reason: unknown: %s" % code + (" %s" % printable(detail) if detail else "")
              for code, detail in result.unknowns]
    where = "PR %d head %s" % (result.pr, result.head[:SHORT])
    if result.verdict == "fail":
        classes = [cls for cls in CLASSES if any(b[0] == cls for b in result.blockers)]
        lines.append("pr-ready: fail (%s, blockers: %s; exit %d)"
                     % (where, ", ".join(classes), result.exit))
    elif result.verdict == "unverifiable":
        lines.append("pr-ready: unverifiable (%s, unknown: %s)"
                     % (where, ", ".join(code for code, _ in result.unknowns)))
    elif result.ledger is not None:
        lines.append("pr-ready: pass (%s, ledger VERIFIED)" % where)
    else:
        lines.append("pr-ready: pass (%s)" % where)
    return lines


def to_json(result: Result) -> str:
    """The `--json` object: one line, keys sorted. `json.dumps` escapes control
    characters and non-ASCII itself, so details are not run through `printable`."""
    return json.dumps({
        "verdict": result.verdict,
        "exit": result.exit,
        "pr": result.pr,
        "head": result.head,
        "blockers": [{"class": cls, "detail": detail} for cls, detail in result.blockers],
        "unknowns": [{"code": code, "detail": detail} for code, detail in result.unknowns],
        "ledger": result.ledger,
    }, sort_keys=True)


# ---------------------------------------------------------------------------
# Ledger gate
# ---------------------------------------------------------------------------

_LEDGER_MODULE: List[Any] = []


def _load_sibling(name: str, module_name: str) -> Any:
    path = Path(__file__).resolve().parent / name
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError("no loader for %s" % path)
    module = importlib.util.module_from_spec(spec)
    saved = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # loading the sibling writes no __pycache__
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = saved
    return module


def _verify_ledger() -> Any:
    """`verify-ledger.py` from this script's own directory, loaded on first use."""
    if not _LEDGER_MODULE:
        try:
            module = _load_sibling(LEDGER_SCRIPT, "verify_ledger_for_pr_ready")
        except Exception as exc:  # a missing file, a syntax error, anything at import
            raise LedgerLoadError("%s: %s" % (type(exc).__name__, exc))
        for name in ("ledger_check", "LedgerError"):
            if not hasattr(module, name):
                raise LedgerLoadError("it defines no %s" % name)
        _LEDGER_MODULE.append(module)
    return _LEDGER_MODULE[0]


def ledger_gate(repo: Path) -> LedgerGate:
    """The ledger gate for `evaluate`. An unreadable or malformed ledger file
    (`LedgerError`) reads as `fail` with a `ledger_unreadable (<detail>)` reason,
    so the other blockers still print."""
    module = _verify_ledger()

    def gate(pr: int, head: str) -> Tuple[str, List[str]]:
        try:
            answer, reasons = module.ledger_check(repo, pr=pr, head=head)
        except module.LedgerError as exc:
            return "fail", ["%s (%s)" % (UNREADABLE, exc)]
        return answer, list(reasons)

    return gate


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pr-ready.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    c = sub.add_parser("check", help="judge a pr-ready-snapshot/1 file")
    c.add_argument("--snapshot", type=Path, required=True, help="the snapshot file")
    c.add_argument("--repo", type=Path, default=Path("."),
                   help="the checkout the snapshot belongs to (default .)")
    c.add_argument("--json", action="store_true",
                   help="print one JSON object instead of the verdict lines")
    return parser


def _guard_streams() -> None:
    """A non-UTF-8 console never crashes output, help included."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="backslashreplace")


def main(argv: Optional[List[str]] = None) -> int:
    _guard_streams()
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        snap = load_snapshot(args.snapshot)
    except SnapshotError as exc:
        print("pr-ready: snapshot %s: %s" % (printable(str(args.snapshot)), printable(str(exc))),
              file=sys.stderr)
        return 2
    try:
        gate = ledger_gate(args.repo)
    except LedgerLoadError as exc:
        print("pr-ready: cannot load %s (%s)" % (LEDGER_SCRIPT, printable(str(exc))),
              file=sys.stderr)
        return 2
    result = evaluate(snap, gate)
    print(to_json(result) if args.json else "\n".join(render(result)))
    return result.exit


if __name__ == "__main__":
    sys.exit(main())

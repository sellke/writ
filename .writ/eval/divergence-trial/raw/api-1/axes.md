## Draft 1
Title: Single snapshot, exit code per blocker set
Commitment: one call; blockers come back as result values — the caller gets one snapshot per run and must re-invoke to see any change, and several blockers collapse to one code that names none of them
Structure:
  Invocation: python3 scripts/pr-ready.py --pr <number> [--repo <owner/name>]
    Reads PR state once via gh, writes nothing, never sleeps or retries, returns immediately.
  Blocker (one per finding): kind, detail
    kind  = conflicts | checks | threads | gates
    detail = one line: file names for conflicts, check name + run URL for checks,
             thread path:line + author for threads, gate name (approval, branch protection, draft, pending check) for gates
  Exit codes (one per outcome; the caller branches on these alone):
    0   READY             no blockers
    10  CONFLICTS         only blocker kind is conflicts
    11  FAILING_CHECKS    only blocker kind is checks
    12  UNRESOLVED_THREADS only blocker kind is threads
    13  MERGE_GATES       only blocker kind is gates
    14  MULTIPLE          two or more blocker kinds at once
    2   USAGE             bad or missing arguments
    3   LOOKUP_FAILED     gh missing, not authenticated, PR not found, or API error
  Stdout, in order:
    line 1   verdict:  READY | BLOCKED | ERROR
    lines 2+ reason: <kind>: <detail>     one line per Blocker, conflicts first, then checks, threads, gates
    last     summary: pr #<n> <verdict> exit=<code> blockers=<kind,kind|none>
  Example (two kinds): BLOCKED / reason: conflicts: src/app.py / reason: checks: lint failed <url> /
    summary: pr #87 BLOCKED exit=14 blockers=conflicts,checks
  Errors use the same shape: ERROR, one reason: line naming the cause, summary with exit=2 or 3.
  Stderr carries nothing the caller needs; it is free for debug output.
Trade-off: a PR with several blocker kinds returns one generic code, so the caller cannot auto-fix the one fixable blocker without parsing the reason: lines or the summary's blockers= list.

## Draft 2
Title: Per-probe blocker values, one folded exit code
Commitment: several small calls; blockers come back as result values — one read-only GitHub query per blocker type means more round trips and a non-atomic snapshot of the PR
Structure:
  Invocation: python3 scripts/pr-ready.py --pr <number> [--repo <owner/name>] [--only <type>[,<type>...]]
    --only limits the run to the named probes; default runs all four
  Blocker = { type: "conflicts" | "threads" | "checks" | "gates", detail: str }
  ProbeResult = { type: str, blockers: list[Blocker], error: str | None }
  Probes, each one small read-only call that returns a ProbeResult and never raises:
    probe_conflicts(pr) -> ProbeResult    # mergeable state; one Blocker if the branch conflicts with base
    probe_threads(pr)   -> ProbeResult    # one Blocker per unresolved review thread
    probe_checks(pr)    -> ProbeResult    # one Blocker per required check that failed or errored
    probe_gates(pr)     -> ProbeResult    # one Blocker per unmet gate: approval, code-owner review, draft, branch rule
  fold(results: list[ProbeResult]) -> (verdict, exit_code)
  Exit codes (stable; callers compare against these names):
    0 READY            no blockers in any probe
    10 CONFLICTS       only conflict blockers
    11 THREADS         only unresolved-thread blockers
    12 FAILING_CHECKS  only failing-check blockers
    13 GATES           only merge-gate blockers
    20 SEVERAL         blockers of two or more types
    2 USAGE            bad flags or unknown --only type
    3 LOOKUP_FAILED    a probe returned error, or the PR does not exist; overrides all codes above
  Stdout, in order:
    line 1: READY | NOT_READY | UNKNOWN
    then one line per blocker: reason: <type>: <detail>    (probe errors print as reason: error: <probe>: <message>)
    last line: summary: pr=<number> verdict=<verdict> exit=<code> conflicts=<n> threads=<n> checks=<n> gates=<n>
  Behavior: runs each probe once, writes nothing to GitHub, and never sleeps or retries.
Trade-off: up to four API calls per run, and a check can change state between probes, so one report can mix two moments in the PR's life.

## Draft 3
Title: Exit-on-blocker readiness gate
Commitment: one call; blockers raise (fail the invocation) and unwind — any blocked PR exits nonzero, and a PR with two blockers gets the generic several-blockers code even when one of them is mechanically fixable
Structure:
  usage: pr-ready.py --pr <number> [--repo <owner/name>]   one GitHub snapshot per run, never waits or retries
  exit codes: 0 READY | 10 CONFLICTS | 11 UNRESOLVED_THREADS | 12 FAILING_CHECKS | 13 MERGE_GATES | 14 SEVERAL_BLOCKERS | 2 USAGE | 3 LOOKUP_ERROR
  class Blocker(Exception): kind: str; exit_code: int; reasons: list[str]
    class Conflicts(Blocker)          kind="conflicts", exit_code=10   mergeable state is CONFLICTING
    class UnresolvedThreads(Blocker)  kind="threads", exit_code=11     one reason per open thread: path:line author
    class FailingChecks(Blocker)      kind="checks", exit_code=12      one reason per failed or errored check; pending checks are not failures
    class MergeGates(Blocker)         kind="gates", exit_code=13       required approval, changes requested, pending required checks, draft, branch protection
  class SeveralBlockers(Blocker): blockers: list[Blocker]; exit_code=14; reasons = every child's reasons, child order kept
  class LookupError_(Exception): message: str; exit_code=3            gh missing, auth failure, PR not found, API error
  fetch_snapshot(pr: int, repo: str | None) -> Snapshot               the only network call; raises LookupError_
  Snapshot: mergeable: str; threads: list[Thread]; checks: list[Check]; reviews: list[Review]; is_draft: bool
  check_conflicts(s) / check_threads(s) / check_checks(s) / check_gates(s) -> None   each raises its Blocker or returns
  evaluate(s) -> None: run all four checks, catch each Blocker into a list; raise the one Blocker if one, SeveralBlockers if more
  main() -> int: try fetch + evaluate, print READY output, return 0; except Blocker or LookupError_ as e: print its output, return e.exit_code
  stdout, in order:
    line 1 verdict: "READY" | "BLOCKED conflicts" | "BLOCKED several: conflicts,checks" | "ERROR lookup"
    then zero or more "reason: <kind>: <detail>" lines, grouped by kind in the order conflicts, threads, checks, gates
    last line summary: "summary: pr=<n> verdict=<READY|BLOCKED|ERROR> blockers=<kinds or none> exit=<code>"
  stderr: empty unless a Python traceback escapes; any exit code outside the table means the script itself is broken
Trade-off: Callers cannot act on one blocker while others remain (conflicts plus failing checks returns 14, not 10), and a shell running with errexit treats every blocked PR as a failed command.

# Divergence trial rating sheet

Rate from this file alone. Do not open raw/, key.json, or the trial JSON.
Each brief shows two sets of three drafts. Fill the five lines under each
Rating heading and change nothing else:

- distinct_X / distinct_Y: 1, 2, or 3 (how many structurally different drafts the set holds)
- more_distinct: X, Y, or tie (which set is more distinct)
- render_only_enough: yes or no (could you choose a direction from these drafts without running code?)
- note: one line, at most 200 characters

## Brief api-1 (medium: api)

### Set X

#### Draft 1

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

#### Draft 2

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

#### Draft 3

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

### Set Y

#### Draft 1

Structure:
    Usage: pr-ready.py [PR] [--repo OWNER/NAME]
      PR: number, URL, or omitted (resolves the PR for the current branch)
    BlockerBit:
      1   conflict    merge conflict with the base branch
      2   threads     one or more review threads unresolved
      4   checks      one or more required checks failed
      8   gate        merge gate unmet (required approval, branch protection, draft state)
    Exit code:
      0        ready: no bits set
      1..15    OR of the BlockerBit values present (5 = conflict + checks)
      64       usage error (bad flag, PR not found)
      65       lookup error (gh missing, auth failed, API error)
      codes 16..63 reserved; a caller treats any code above 15 as "state unknown"
    Caller test: (code & 4) != 0 means checks are failing, regardless of other bits
    Stdout, in order:
      line 1: READY | BLOCKED | UNKNOWN
      reason: <type> <detail>      one line per blocker instance
      last line: summary: blockers=<type,type,...> mask=<code> pr=#<n>
    Behavior: one read of PR state per run; no polling, no waiting, no writes.
Trade-off: exit codes like 13 are unreadable to a human at a glance and a shell `case` on them gets long.

#### Draft 2

Structure:
    Usage: pr-ready.py [PR] [--repo OWNER/NAME] [--only TYPE[,TYPE...]]
      PR: number, URL, or omitted (resolves the PR for the current branch)
      --only: restrict the evaluation to the listed blocker types
    BlockerType:
      conflict    merge conflict with the base branch
      threads     one or more review threads unresolved
      checks      one or more required checks failed
      gate        merge gate unmet (required approval, branch protection, draft state)
    Exit codes:
      0   ready: no blockers among the evaluated types
      10  only conflict
      11  only threads
      12  only checks
      13  only gate
      19  two or more types present; reason lines say which
      2   usage error (bad flag, unknown TYPE, PR not found)
      3   lookup error (gh missing, auth failed, API error)
    Watch-loop pattern: on 19, call again with --only <type> per type it can fix
    Stdout, in order:
      line 1: READY | BLOCKED | UNKNOWN
      reason: <type> <detail>      one line per blocker instance in scope
      last line: summary: <n> blockers across <k> types on PR #<n> (scope=<types|all>)
    Behavior: one read of PR state per run; no polling, no waiting, no writes.
Trade-off: when several blockers coexist the caller needs extra runs (or must parse text) to learn which types they are.

#### Draft 3

Structure:
    Usage: pr-ready.py [PR] [--repo OWNER/NAME]
      PR: number, URL, or omitted (resolves the PR for the current branch)
    BlockerType (fixed precedence, highest first):
      conflict    merge conflict with the base branch
      checks      one or more required checks failed
      threads     one or more review threads unresolved
      gate        merge gate unmet (required approval, branch protection, draft state)
    Exit codes:
      0   ready: no blockers
      10  conflict is the highest-precedence blocker
      11  checks is the highest-precedence blocker
      12  threads is the highest-precedence blocker
      13  gate is the highest-precedence blocker
      2   usage error (bad flag, PR not found)
      3   lookup error (gh missing, auth failed, API error); verdict is UNKNOWN
    Stdout, in order:
      line 1: READY | BLOCKED | UNKNOWN
      reason: <type> <detail>      one line per blocker instance, every type present
      last line: summary: <n> blockers (<type>=<count>, ...) on PR #<n>
    Behavior: one read of PR state per run; no polling, no waiting, no writes.
Trade-off: the exit code names only one blocker; a caller that wants every type must read the reason lines.

### Rating: api-1

distinct_X:
distinct_Y:
more_distinct:
render_only_enough:
note:

## Brief api-2 (medium: api)

### Set X

#### Draft 1

Structure:
    WhyRecord (JSON, saved to .writ/why/<slug>.json)
      question: string
      sources: Source[]          in search order: ledger, then git, then mcp
      claims: Claim[]
      guidance: Guidance | null  null when no change follows
    Source
      id: "S1", "S2", ...
      layer: "ledger" | "git" | "mcp"
      locator: string            path#section, commit SHA, or server/item id
      claimIds: string[]         empty when the source held nothing
    Claim
      id: "C1", "C2", ...
      text: string
      tier: "Recorded" | "Stated" | "Corroborated" | "Inferred" | "Unknown"
      sourceIds: string[]        two or more for Corroborated; empty for Unknown
    Guidance
      preserve: GuidanceItem[]
      change: GuidanceItem[]
      avoid: GuidanceItem[]
      risk: GuidanceItem[]
    GuidanceItem
      text: string
      claimIds: string[]         the claims this item rests on
      tier: the weakest tier among the cited claims, computed, not authored
Trade-off: the developer needs a renderer to read it, since raw JSON with ID lookups is hard to follow by eye.

#### Draft 2

Structure:
    type Tier = "Recorded" | "Stated" | "Corroborated" | "Inferred" | "Unknown"
    type SourceKind = "ledger" | "git" | "mcp"
    type Citation =
      | { kind: "ledger"; path: string; section: string }
      | { kind: "git"; sha: string }
      | { kind: "mcp"; server: string; itemId: string }
    type Claim = { text: string; tier: Tier; cite: Citation | null }   // cite is null only when tier is Unknown
    type SearchStep = { order: number; kind: SourceKind; target: string; hits: number }   // hits may be 0
    type ChangeGuidance = {
      preserve: Claim[]
      change: Claim[]
      avoid: Claim[]
      risk: Claim[]
    }
    type WhyRecord = {
      question: string
      askedAt: string             // ISO date
      answer: string              // short summary for the developer
      claims: Claim[]
      searched: SearchStep[]      // all ledger steps, then git, then mcp
      guidance?: ChangeGuidance   // present only when a change follows
    }
    function buildWhyRecord(question: string, change?: string): WhyRecord
    function renderWhyRecord(record: WhyRecord): string    // markdown shown to the developer
    function loadWhyRecord(path: string): WhyRecord        // called by /create-spec before planning
Trade-off: the saved file must round-trip through render and load, so a hand edit to the markdown can break /create-spec's read.

#### Draft 3

Structure:
    why-record.md, saved to .writ/why/<date>-<slug>.md
      frontmatter:
        question: <one line>
        date: <YYYY-MM-DD>
        change: <one line, or "none">
      ## Answer
        one paragraph; every sentence ends with a tag
      ## Claims
        - <claim text> [Recorded: .writ/decision-records/adr-003.md#Decision]
        - <claim text> [Corroborated: a1b2c3d, .writ/specs/x/spec.md#Scope]
        - <claim text> [Stated: linear:ENG-142]
        - <claim text> [Unknown: no source]
      ## Sources Searched
        1. ledger: .writ/decision-records/ (2 hits)
        2. ledger: .writ/specs/ (0 hits)
        3. git: log search for "<term>" (1 hit)
        4. mcp: linear (0 hits)
      ## Change Guidance   (omitted when change is "none")
        ### Preserve, ### Change, ### Avoid, ### Risk
          - <item> [Tier: source]
    Tag grammar: [Tier: source, source...]
      Tier is one of Recorded, Stated, Corroborated, Inferred, Unknown
      source is path#section, a 7+ character hex SHA, server:item, or "no source" (Unknown only)
Trade-off: easy for a developer to read and diff, but /create-spec must parse tags by pattern, and loose formatting can slip past it.

### Set Y

#### Draft 1

Structure:
  Tier = "Recorded" | "Stated" | "Corroborated" | "Inferred" | "Unknown"
  SourceKind = "ledger" | "git" | "mcp"
  Cite = LedgerCite(path: str, section: str)
       | CommitCite(sha: str)
       | McpCite(server: str, item_id: str)
       | NothingFound(kind: SourceKind, name: str)   # backs an Unknown claim: the search that came up empty
  Claim = { tier: Tier, text: str, source: Cite }
  SourceStatus = Found(hits: int) | Empty | Unreachable(reason: str)
  SourceResult = { order: int, kind: SourceKind, name: str, status: SourceStatus }
      # name: ".writ/ ledger", "git log", or the MCP server name; order runs ledger -> git -> each MCP server
  Advice = { text: str, tier: Tier, source: Cite }
  ChangeGuidance = { preserve: list[Advice], change: list[Advice], avoid: list[Advice], risk: list[Advice] }
  WhyRecord = { question: str, asked_at: date, claims: list[Claim],
                sources_searched: list[SourceResult], change_guidance: ChangeGuidance | None }

  open_inquiry(question: str) -> InquiryId                     # resolves terms, fixes the source order
  read_claims(id: InquiryId) -> list[Claim]                     # never raises; gaps become Unknown claims
  read_sources(id: InquiryId) -> list[SourceResult]             # every source tried, Empty and Unreachable included
  read_guidance(id: InquiryId, change: str | None) -> ChangeGuidance | None   # None when no change is proposed
  why(question: str, change: str | None = None) -> WhyRecord    # opens, calls all three, packs the results unchanged
  save_record(record: WhyRecord, path: str) -> None             # writes .writ/why/<slug>.md with a typed front block
  read_saved_record(path: str) -> WhyRecord                     # same shape back; stale sources keep their saved status
Trade-off: no single atomic answer; the three reads can drift if the ledger or git changes between calls, and why() hides that only by calling them back to back.

#### Draft 2

Structure:
  Tier = enum { Recorded, Stated, Corroborated, Inferred, Unknown }
  SourceRef = one of
      FileRef   { path: str, section: str }
      CommitRef { sha: str }
      McpRef    { server: str, item_id: str }
  Claim = { tier: Tier, text: str, source: SourceRef | None }   # source is None only when tier is Unknown
  SourceKind = enum { Ledger, Git, Mcp }
  SourceOutcome = enum { Found, Empty, Unreachable }
  SourceSearched = { kind: SourceKind, name: str, outcome: SourceOutcome,
                     detail: str, claim_count: int }   # detail: what was searched, or why it failed
  GuidanceItem = { text: str, tier: Tier, source: SourceRef | None }
  ChangeGuidance = { preserve: list[GuidanceItem], change: list[GuidanceItem],
                     avoid: list[GuidanceItem], risk: list[GuidanceItem] }
  EvidenceRecord = {
      question: str,
      asked_at: datetime,
      claims: list[Claim],                     # strongest tier first
      sources_searched: list[SourceSearched],  # always ledger, then git, then one entry per MCP server
      change_guidance: ChangeGuidance | None,  # None when no change is proposed
  }
  why(question: str, proposed_change: str | None = None) -> EvidenceRecord   # never raises on a source failure
  save_record(record: EvidenceRecord, path: str) -> None      # markdown with a JSON front-matter block
  read_saved_record(path: str) -> EvidenceRecord              # raises only if the file is missing or malformed
Trade-off: A failed or empty source looks like any other entry, so a reader who skips sources_searched can mistake missing evidence for a confident answer.

#### Draft 3

Structure:
    Tier = Enum("Recorded", "Stated", "Corroborated", "Inferred", "Unknown")
    SourceKind = Enum("ledger", "git", "mcp")
    Source = { kind: SourceKind, ref: str, locator: str }
        # ledger: ref = file path, locator = section heading
        # git: ref = commit SHA, locator = "" ; mcp: ref = server name, locator = item id
    Claim = { tier: Tier, text: str, source: Source }
    SearchStep = { kind: SourceKind, name: str, queried: list[str], hits: int }
        # hits = 0 is kept; an empty source still appears in its slot
    GuidanceItem = { text: str, tier: Tier, source: Source }
    ChangeGuidance = { preserve: list[GuidanceItem], change: list[GuidanceItem],
                       avoid: list[GuidanceItem], risk: list[GuidanceItem] }
    WhyRecord = { question: str, asked_at: datetime, claims: list[Claim],
                  sources_searched: list[SearchStep],   # fixed order: ledger, git, then each MCP server
                  change_guidance: ChangeGuidance | None, saved_to: path | None }
    SourceUnreachable(Exception) = { kind: SourceKind, name: str, reason: str }
    why(question: str, intended_change: str | None = None, save: bool = True) -> WhyRecord
        # searches every source in order; the first unreachable source raises SourceUnreachable
        # and discards everything gathered so far; nothing is written to disk
        # change_guidance is filled only when intended_change is given
        # a claim with no source found is emitted as tier Unknown with the searched steps as its source list
    read_saved_record(path: path) -> WhyRecord
        # raises RecordInvalid if any claim or guidance item lacks a tier or source,
        # or if sources_searched is not in ledger, git, MCP order
    RecordInvalid(Exception) = { path: path, field: str, reason: str }
Trade-off: the developer gets no partial answer when any one source is down, so a flaky MCP server blocks the whole explanation and the /create-spec step behind it.

### Rating: api-2

distinct_X:
distinct_Y:
more_distinct:
render_only_enough:
note:

## Brief data-model-1 (medium: data-model)

### Set X

#### Draft 1

Structure:
  File: .writ/state/ledger.db (SQLite)
  TABLE verdict
    id           INTEGER PRIMARY KEY AUTOINCREMENT
    pr           INTEGER NOT NULL
    head_sha     TEXT NOT NULL CHECK (length(head_sha) = 40)
    patch_id     TEXT NOT NULL
    result       TEXT NOT NULL CHECK (result IN ('pass', 'fail'))
    verifier     TEXT NOT NULL
    created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
  INDEX verdict_head  ON verdict(pr, head_sha)
  INDEX verdict_patch ON verdict(pr, patch_id)
  QUERY head_status(:pr, :sha, :patch_id)
    SELECT *, CASE WHEN head_sha = :sha THEN 'sha' ELSE 'patch-id' END AS matched_by
    FROM verdict
    WHERE pr = :pr AND (head_sha = :sha OR (patch_id = :patch_id AND result = 'pass'))
    ORDER BY (head_sha = :sha) DESC, id DESC
    LIMIT 1
    No row: NOT VERIFIED. A row with result = 'pass': VERIFIED by that row's id.
  QUERY pr_history(:pr)
    SELECT * FROM verdict WHERE pr = :pr ORDER BY id
  Callers only INSERT; no UPDATE or DELETE statement exists in the code.
Trade-off: the binary database cannot be diffed or reviewed in git, and every caller needs sqlite3.

#### Draft 2

Structure:
  Verdict (frozen dataclass)
    pr: int
    head_sha: str              40-hex commit SHA
    patch_id: str              `git patch-id --stable` of merge-base...head
    result: Literal["pass", "fail"]
    verifier: str              command that produced it, e.g. "verify-spec"
    verified_at: str           ISO-8601 UTC
  Lookup (frozen dataclass)
    verified: bool
    verdict: Verdict | None
    matched_by: Literal["sha", "patch-id", "none"]
  File: .writ/state/verifications.jsonl, one Verdict per line, never rewritten
  append(v: Verdict) -> None             open with O_APPEND, write one line, fsync
  load() -> list[Verdict]                parse every line in file order
  lookup(pr: int, head_sha: str, patch_id: str) -> Lookup
    exact = last v in load() with v.pr == pr and v.head_sha == head_sha
    if exact: return Lookup(exact.result == "pass", exact, "sha")
    carried = last v with v.pr == pr and v.patch_id == patch_id and v.result == "pass"
    if carried: return Lookup(True, carried, "patch-id")
    return Lookup(False, None, "none")
  history(pr: int) -> list[Verdict]      every v with v.pr == pr, oldest first
Trade-off: every lookup scans the whole file, with no index and no schema enforcement beyond the dataclass.

#### Draft 3

Structure:
  Layout under .writ/verifications/
    pr-<number>/
      <verified_at>-<head_sha>.json    one file per verdict, never overwritten
    by-patch-id/
      <patch_id>                       text file, one "<pr> <head_sha> <file name>" line per passing verdict
  Verdict file fields
    pr: int
    head_sha: str
    patch_id: str
    result: "pass" | "fail"
    verifier: str
    verified_at: ISO-8601 UTC, also the file name prefix
  record(pr, head_sha, patch_id, result, verifier) -> Path
    write pr-<pr>/<verified_at>-<head_sha>.json
    if result == "pass": append a line to by-patch-id/<patch_id>
  is_verified(pr, head_sha, patch_id) -> tuple[bool, Path | None]
    newest = last match of pr-<pr>/*-<head_sha>.json, sorted by name
    if newest: return (newest.result == "pass", newest)
    for line in by-patch-id/<patch_id> where line.pr == pr: return (True, that line's file)
    return (False, None)
  history(pr) -> list[Verdict]         every file in pr-<pr>/, sorted by name
Trade-off: the patch-id index is a second write that can drift from the verdict files if a write is interrupted.

### Set Y

#### Draft 1

Structure:
  Status = Literal["VERIFIED", "NOT VERIFIED"]
  VerdictValue = Literal["pass", "fail"]
  VerdictEvent (frozen dataclass): seq: int, pr: int, head_sha: str, patch_id: str, verdict: VerdictValue, by: str, recorded_at: datetime (UTC)
  Storage: .writ/state/verification-ledger.jsonl, one VerdictEvent per line; lines are appended, never edited or removed
  PatchIdResolver = Callable[[str], Optional[str]]   # head SHA -> patch-id; default runs `git diff <merge-base>..<head> | git patch-id --stable`
  class VerificationLedger:
    __init__(self, path: Path, resolve_patch_id: PatchIdResolver)
    record_verdict(self, pr: int, head_sha: str, patch_id: str, verdict: VerdictValue, by: str) -> VerdictEvent
      appends one line under an exclusive file lock; seq = last seq in file + 1
    history(self, pr: int) -> List[VerdictEvent]
      every event for pr, ordered by seq (oldest first), failed and superseded verdicts included
    is_verified(self, pr: int, head_sha: str) -> Tuple[Status, Optional[VerdictEvent]]
      1. events = history(pr)
      2. patch_id = patch_id of any event with this head_sha, else resolve_patch_id(head_sha)
      3. matches = events whose patch_id equals it; latest = matches[-1]
      4. latest exists and latest.verdict == "pass" -> ("VERIFIED", latest); otherwise ("NOT VERIFIED", None)
  Read rules:
    no status field is stored anywhere; status exists only as the output of is_verified
    a later "fail" on the same patch-id overrides an earlier "pass"
    a head whose patch-id cannot be resolved reads NOT VERIFIED
    verdicts never carry across PRs, even when patch-ids match
  Audit: the event is_verified returns is the same record history() lists, identified by seq
Trade-off: Each status check costs a log scan plus a git call for unseen heads, and a corrupted or hand-edited line changes past answers silently because no status is snapshotted.

#### Draft 2

Structure:
  Table verdicts (one row per recorded verdict; columns can change after insert)
    id INTEGER PRIMARY KEY            -- insertion order, used for oldest-first listing
    pr INTEGER NOT NULL
    head_sha TEXT NOT NULL
    patch_id TEXT NOT NULL
    verdict TEXT NOT NULL CHECK (verdict IN ('pass','fail'))
    by TEXT NOT NULL                  -- command or script that recorded it
    recorded_at TEXT NOT NULL         -- ISO-8601 UTC
    superseded INTEGER NOT NULL DEFAULT 0   -- set to 1 when a later verdict lands on the same (pr, patch_id)
  Table patch_status (one row per (pr, patch_id); rewritten on every record)
    pr INTEGER, patch_id TEXT, PRIMARY KEY (pr, patch_id)
    status TEXT NOT NULL CHECK (status IN ('VERIFIED','NOT VERIFIED'))
    verdict_id INTEGER NOT NULL REFERENCES verdicts(id)   -- the verdict that set this status
  Verdict = record(id, pr, head_sha, patch_id, verdict, by, recorded_at, superseded)
  record_verdict(pr: int, head_sha: str, patch_id: str, verdict: str, by: str) -> Verdict
    in one transaction: mark prior verdicts for (pr, patch_id) superseded=1; insert the new row;
    upsert patch_status with status = 'VERIFIED' if verdict == 'pass' else 'NOT VERIFIED'
  is_verified(pr: int, head_sha: str) -> tuple[str, Verdict | None]
    patch_id = git patch-id of merge-base..head_sha; read patch_status(pr, patch_id);
    no row or status 'NOT VERIFIED' -> ("NOT VERIFIED", None); else ("VERIFIED", verdicts[verdict_id])
  history(pr: int) -> list[Verdict]   -- every verdicts row for pr, ORDER BY id ASC, superseded rows included
Trade-off: reads are a single keyed lookup, but status is only as current as the last write, the superseded flag is edited in place without its own audit entry, and a head whose patch-id cannot be computed from git reads as not verified.

#### Draft 3

Structure:
  Verdict = Literal["pass", "fail"]
  Status = Literal["VERIFIED", "NOT VERIFIED"]
  Event (append-only table `events`, never updated or deleted):
    seq: int (primary key, monotonic)    at: datetime (UTC)
    kind: Literal["head_seen", "verdict"]
    pr: int    head_sha: str    patch_id: str
    verdict: Verdict | None (set only when kind == "verdict")    by: str | None
  HeadStatus (derived table `head_status`, primary key (pr, head_sha)):
    patch_id: str    status: Status    verdict_seq: int | None (seq of the deciding verdict event)
  record_verdict(pr, head_sha, patch_id, verdict, by) -> Event
    appends a "verdict" event, then in the same transaction sets head_status for every
    known head of this PR whose patch_id matches, using the newest verdict for that patch_id
  observe_head(pr, head_sha, patch_id) -> HeadStatus
    appends a "head_seen" event; the new row is VERIFIED only if the newest verdict on
    any earlier head of this PR with the same patch_id is "pass"
  is_verified(pr, head_sha) -> tuple[Status, Event | None]
    one read of head_status; unknown head -> ("NOT VERIFIED", None); else the status and the event at verdict_seq
  history(pr) -> list[Event]
    every "verdict" event for the PR ordered by seq, oldest first
  rebuild_status() -> None
    drops head_status and replays events in seq order; used after a change to the matching rule
  Invariant: a "fail" verdict newer than a "pass" on the same patch_id sets matching heads to NOT VERIFIED
Trade-off: a head must be recorded with its patch-id before it can read VERIFIED, and the status table can drift from the log until rebuild_status runs if the write path has a bug.

### Rating: data-model-1

distinct_X:
distinct_Y:
more_distinct:
render_only_enough:
note:

## Brief data-model-2 (medium: data-model)

### Set X

#### Draft 1

Structure:
  EnforcerKind = "architecture" | "type" | "lint" | "test" | "docs"   # rank order, strongest first
  Proof:
    mistake_ref: str          # commit SHA, PR number, or transcript id of the past mistake
    note: str                 # one line on what went wrong; may be empty
    checked_at: date          # when the new check was run against that mistake and failed
  Enforcer:
    id: str                   # "<rule_id>/<seq>"; seq increments per rule and is never reused
    kind: EnforcerKind
    location: str             # file path plus the rule, type, or test name inside it
    proof: Proof | None       # required unless kind == "docs"
  Rule:
    id: str                   # stable slug
    text: str                 # the convention as written
    source: str               # steering file or doc path that states it
    enforcers: list[Enforcer] # edited in place
    next_seq: int
    updated_at: datetime
  Store: .writ/retro/rules.json, an object keyed by rule id, rewritten whole on every change
  unenforced_rules() -> list[Rule]                  # enforcers empty, or every enforcer is kind "docs"
  enforcers_for(rule_id) -> list[(EnforcerKind, str)]   # (kind, location), sorted by rank
  add_enforcer(rule_id, kind, location, proven_by) -> str   # appends, returns new id; rejects unknown rule, or missing proven_by when kind != "docs"
  proof_for(enforcer_id) -> Proof | None            # splits id at "/", loads that rule, scans its list
  remove_enforcer(enforcer_id) -> None              # deletes the entry and its proof
Trade-off: Past enforcers and their proofs are not kept once edited or removed, and a lookup by enforcer id depends on the id encoding its parent rule.

#### Draft 2

Structure:
  table rule
    id            text primary key        -- slug, e.g. "handlers-use-service-layer"
    statement     text not null           -- the convention as written
    source        text not null           -- steering file or doc path, with anchor
  table mistake
    id            integer primary key
    ref           text not null unique    -- commit SHA or transcript path + line
    summary       text not null           -- what went wrong
  table enforcer
    id            integer primary key
    rule_id       text not null references rule(id) on delete cascade
    kind          text not null check (kind in ('architecture','type','lint','test','docs'))
    location      text not null           -- config key, file path, or test name
    proven_by     integer references mistake(id)   -- null only when kind = 'docs'
    unique (rule_id, kind, location)
    check (kind = 'docs' or proven_by is not null)
  rank(kind) -> int: architecture=1, type=2, lint=3, test=4, docs=5
  unenforced_rules() -> [rule]: rules with no enforcer row, or whose only rows have kind = 'docs'
  enforcers_for(rule_id) -> [(kind, location)]: rows for rule_id, ordered by rank(kind)
  add_enforcer(rule_id, kind, location, proven_by) -> enforcer.id: inserts mistake by ref if absent; upserts on (rule_id, kind, location); rejects unknown rule_id
  update_enforcer(enforcer_id, location?, proven_by?) -> None: edits the row in place when a check moves
  remove_enforcer(enforcer_id) -> None: deletes the row; the rule reappears in unenforced_rules() if nothing else covers it
  proof_for(enforcer_id) -> mistake | None: join enforcer.proven_by to mistake
Trade-off: no history of removed or relocated checks, so the table cannot say when a rule lost coverage or what used to enforce it.

#### Draft 3

Structure:
  Kind = enum('architecture', 'type', 'lint', 'test', 'docs')   -- rank order /retro uses; 'docs' means not checked
  rules(rule_id TEXT PK, statement TEXT, source_file TEXT, source_line INT, recorded_at TIMESTAMP)
  mistakes(mistake_id INT PK, ref TEXT UNIQUE, description TEXT, transcript TEXT NULL)
      -- ref is a commit SHA or transcript pointer for the real past error a check must catch
  enforcers(enforcer_id INT PK, rule_id TEXT FK rules, kind Kind, location TEXT, UNIQUE(rule_id, kind, location))
  enforcement_events(event_id INT PK, enforcer_id INT FK enforcers, action TEXT CHECK(action IN ('added','retired')),
      proven_by INT FK mistakes NULL, actor TEXT, at TIMESTAMP)
      -- never updated or deleted; an 'added' event for a non-docs kind requires proven_by
  view active_enforcers AS enforcers e WHERE latest event for e.enforcer_id has action = 'added'

  unenforced_rules() -> list[Rule]
      rules r WHERE NOT EXISTS (active_enforcers a WHERE a.rule_id = r.rule_id AND a.kind <> 'docs')
      -- covers both "no enforcer" and "documentation only"
  enforcers_for(rule_id: str) -> list[tuple[Kind, str]]
      SELECT kind, location FROM active_enforcers WHERE rule_id = ? ORDER BY Kind rank
  add_enforcer(rule_id: str, kind: Kind, location: str, proven_by: str | None) -> int
      upsert mistakes(ref=proven_by); get-or-insert enforcers row; append 'added' event; return enforcer_id
      -- raises if rule_id is unknown, or if kind <> 'docs' and proven_by is None
  retire_enforcer(enforcer_id: int, actor: str) -> None   -- appends 'retired'; history stays
  proof_for(enforcer_id: int) -> Mistake | None
      mistake joined from the latest 'added' event for enforcer_id
Trade-off: Every current-state read has to find the latest event per enforcer, and fixing a wrong proof means appending a new event instead of editing the old one.

### Set Y

#### Draft 1

Structure:
    File: .writ/retro/enforcement.log.jsonl, one JSON event per line, never edited, only appended
    Common fields on every event: at (ISO time), run (retro run id), type
    Event types:
      RuleNoted        { ruleId, text, sourceFile, sourceLine }
      EnforcerAdded    { ruleId, enforcerId, kind, ref }
                       kind is one of architecture | type | lint | test | doc-only
      ProofRecorded    { enforcerId, mistakeCommit, transcriptRef, failureOutput }
      EnforcerRemoved  { enforcerId, reason }
      RuleRetired      { ruleId, reason }
    Write rule: /retro emits EnforcerAdded and ProofRecorded together; no ProofRecorded means the check is unproven
    Derived state, rebuilt by replaying the log in order:
      rules:      map ruleId -> { text, source, retired }
      enforcers:  map enforcerId -> { ruleId, kind, ref, live }
      proofs:     map enforcerId -> list of proof records
    Views (a small script, e.g. scripts/enforcement-report.py, prints each):
      --unenforced         live rules whose live enforcers are empty or all doc-only
      --rule <ruleId>      live enforcers for the rule, ordered architecture, type, lint, test, doc-only
      --proof <enforcerId> every recorded mistake commit and failure output for that check
      --unproven           live non-doc-only enforcers with no ProofRecorded event
    History questions (when was a check removed, which run added it) come from the raw log
Trade-off: every answer needs a replay script; nobody can read current state straight from the file.

#### Draft 2

Structure:
    type EnforcerKind = "architecture" | "type" | "lint" | "test" | "doc-only"
    const KIND_RANK: Record<EnforcerKind, number> = { architecture: 1, type: 2, lint: 3, test: 4, "doc-only": 5 }
    interface Location { file: string; line: number }
    interface Rule { id: string; text: string; source: Location; addedBy: string }
    interface Enforcer {
      id: string; ruleId: string; kind: EnforcerKind
      ref: string                 // lint rule id, test path::name, type name, or arch constraint path
      addedBy: string             // retro run id
      retiredAt?: string          // set when the check is removed; row kept for history
    }
    interface Proof {
      enforcerId: string
      mistakeCommit: string       // SHA of the real past mistake
      transcriptRef: string       // transcript file + turn where /retro found it
      failureOutput: string       // what the check printed when run against mistakeCommit
      checkedAt: string
    }
    interface EnforcementTable { rules: Rule[]; enforcers: Enforcer[]; proofs: Proof[] }
    Storage: .writ/retro/enforcement.json holding one EnforcementTable
    function addFix(t: EnforcementTable, rule: Rule, enf: Enforcer, proof: Proof | null): EnforcementTable
      // rejects enf.kind != "doc-only" when proof is null
    function unenforcedRules(t): Rule[]       // rules with no live enforcer, or only doc-only ones
    function enforcersFor(t, ruleId): Enforcer[]   // live ones, sorted by KIND_RANK
    function proofsFor(t, enforcerId): Proof[]
Trade-off: JSON with three linked lists is harder to read and edit by hand than a table, and dangling ids need a validator.

#### Draft 3

Structure:
    File: .writ/retro/enforcement.md, a single Markdown table, hand-readable and diffable
    Columns, in order:
      rule_id        short slug, unique, e.g. no-direct-db-in-handlers
      rule           the convention in one sentence
      source         file:line in the steering file or doc that states the rule
      enforcer_kind  one of: architecture | type | lint | test | doc-only
      enforcer_ref   path or name of the check (lint rule id, test file::test name, type name); "-" when doc-only
      proof_commit   SHA of the past commit holding the mistake the check was run against
      proof_result   one line: the failure the check produced on that commit
      added_by       retro run id (date + spec or story slug) that wrote the row
    Rules for writers:
      /retro appends a row when it turns a transcript finding into a fix
      /retro upgrades a row in place when a stronger enforcer_kind replaces a weaker one
      a row with enforcer_kind other than doc-only must have proof_commit and proof_result filled
    Queries (grep or a short script over the table):
      rules with no enforcer      -> rows where enforcer_kind = doc-only
      what enforces rule X        -> the row where rule_id = X
      which mistake proved check  -> proof_commit and proof_result on that row
    Ranking order used by /retro: architecture > type > lint > test > doc-only
Trade-off: one enforcer per rule; a rule checked by both a lint rule and a test loses one of them, and proof history is overwritten on upgrade.

### Rating: data-model-2

distinct_X:
distinct_Y:
more_distinct:
render_only_enough:
note:

## Brief ui-1 (medium: ui)

### Set X

#### Draft 1

Structure:
  type StoryStatus = "Not Started" | "In Progress" | "Completed" | "Blocked"
  type Criterion = { index: number; text: string; testPassing: boolean }
  type Story = { id: string; title: string; status: StoryStatus; criteria: Criterion[] }
  type Spec = { title: string; stories: Story[] }
  SpecGridPage(spec: Spec)
    PageTitle: spec.title
    SummaryLine: "Stories done X/Y . Criteria passing P/T . Blocked B"
    Grid
      header row: Story | Status | AC1 | AC2 | ... | AC8 | Passing
      one row per story, in spec order
        cell Story: story.id + story.title
        cell Status: StatusChip(story.status)
        cells AC1..AC8: green filled square if passing, empty outlined square if not,
          blank cell when the story has fewer criteria than the column
        cell Passing: "p/n" for that story
    CriterionTooltip(criterion): shows criterion.text on hover or focus of an AC cell
    Legend: filled = passing test, outlined = no passing test, chip colors per status
  function cellState(story: Story, column: number): "pass" | "fail" | "none"
  function totals(spec: Spec): { storiesDone: number; storyCount: number;
    passing: number; criteriaCount: number; blocked: number }
Trade-off: Criterion text is hidden behind tooltips, so the maintainer sees where gaps are but must hover to read what they are.

#### Draft 2

Structure:
  type StoryStatus = "Not Started" | "In Progress" | "Completed" | "Blocked"
  type Criterion = { id: string; text: string; hasPassingTest: boolean }
  type Story = { id: string; title: string; status: StoryStatus; criteria: Criterion[] }
  type Spec = { title: string; stories: Story[] }
  type OpenItem = { story: Story; failing: Criterion[] }
  function openItems(spec: Spec): OpenItem[]
    includes a story if status is not Completed or any criterion lacks a passing test
    orders Blocked first, then In Progress, then Not Started
  SpecTodoPage(spec: Spec)
    ProgressBar: share of criteria with a passing test across the spec
    OpenSection(openItems(spec))
      heading: "Left to do: S stories, C criteria"
      OpenStoryBlock(item) for each OpenItem
        line: StatusTag(item.story.status) + story.id + story.title
        FailingCriterionLine for each item.failing entry: criterion.text
        PassingNote: "+N criteria already passing" as one muted line
    DoneSection(collapsed by default)
      heading: "Done: D stories"
      DoneStoryLine: story.id + story.title + "all criteria passing"
Trade-off: Passing criteria on open stories collapse to a count, so the full criteria list per story is not visible at once.

#### Draft 3

Structure:
  type StoryStatus = "Not Started" | "In Progress" | "Completed" | "Blocked"
  type Criterion = { id: string; text: string; testPassing: boolean }
  type Story = { id: string; title: string; status: StoryStatus; criteria: Criterion[] }
  type Spec = { id: string; title: string; stories: Story[] }
  SpecProgressPage(spec: Spec)
    RemainingHeader(spec)
      shows: "N of M stories completed", "K of T criteria passing"
      shows: count per status, Blocked count in red when above zero
    StoryCardList(spec.stories)            sorted Blocked, In Progress, Not Started, Completed
      StoryCard(story)
        CardTitle: story.id + story.title
        StatusBadge(story.status)          color per status
        CriteriaCount: "passing / total"
        CriteriaList(story.criteria)       expanded unless story is Completed with all passing
          CriterionRow(criterion)          check mark or empty box, then criterion.text
        Mismatch flag: shown when status is Completed but a criterion is failing
  function remaining(spec: Spec): { stories: Story[]; failingCriteria: Criterion[] }
    returns stories not Completed and every criterion with testPassing false
  RemainingHeader reads its counts from remaining(spec)
Trade-off: Each story takes vertical space, so an eight-story spec needs scrolling to see every criterion.

### Set Y

#### Draft 1

Structure:
  type Status = "NotStarted" | "InProgress" | "Completed" | "Blocked"
  type Criterion = { id: string; text: string; testName: string | null; passing: boolean }
  type Story = { id: string; title: string; status: Status; blockedBy: string | null; criteria: Criterion[] }
  type Spec = { name: string; updatedAt: string; stories: Story[] }
  remaining(spec: Spec): { stories: number; criteria: number; blocked: number }
  passCount(story: Story): { passing: number; total: number }
  SpecProgressPage(spec: Spec)
    RemainingBar(remaining(spec))  // "3 stories open · 11 criteria failing · 1 blocked" plus last-updated time
    StoryStrip[]  // one row per story, all 3-8 visible without scrolling, ordered Blocked, InProgress, NotStarted, Completed
      StatusChip(status)  // color plus label text, so status reads without color
      Title(title)  // truncated to one line
      CriteriaDots(criteria)  // one filled dot per passing criterion, hollow per failing, in criterion order
      PassFraction(passCount)  // "4/6"
      BlockedNote(blockedBy)  // short reason, shown only when status is Blocked
      onClick -> toggle StoryDetail inline below the row; several rows may be open at once
    StoryDetail(story)
      CriterionRow[]  // failing rows first: pass/fail mark, criterion text, test name or "no test yet"
  Completed rows collapse to a single muted line; open/closed state of each row persists across reloads
  Page refreshes data on focus, so a return visit shows current state without a manual reload
Trade-off: Gives up seeing which specific criteria fail across the whole spec at once; the board shows counts and dots, and the criterion text needs a click per story.

#### Draft 2

Structure:
  type StoryStatus = "NotStarted" | "InProgress" | "Completed" | "Blocked"
  type TestState = "pass" | "fail" | "none"            // none = no test linked yet
  type Criterion = { id: string; label: string; test: TestState }   // label clipped to 40 chars
  type Story = { n: number; title: string; status: StoryStatus; criteria: Criterion[] }  // 3..8 criteria
  type Spec = { name: string; updatedAt: string; stories: Story[] }                       // 3..8 stories
  type Remaining = { storiesOpen: number; criteriaOpen: number; blocked: number }
  function remaining(spec: Spec): Remaining   // criteriaOpen = criteria with test != "pass"
  function glyph(t: TestState): "●" | "✕" | "○"   // pass, fail, no test
  SpecGrid(spec: Spec)
    HeaderBar: spec.name · "updated " + updatedAt · RemainingCounts(remaining(spec))
    RemainingCounts: "5 stories open · 14 criteria not passing · 1 blocked"
    StoryTable: one row per story, all rows always rendered, no collapse, no pagination
      StoryRow(story: Story)
        StatusChip(status)        // 2-letter tag + color: NS grey, IP blue, OK green, BL red
        StoryTitle(n, title)      // single line, truncated with ellipsis
        PassRatio                 // "3/6"
        CriteriaStrip: up to 8 CriterionCell, fixed width so columns align across rows
          CriterionCell(c)        // glyph(c.test) above c.label at 11px, full label in title attribute
    Legend: ● passing test  ✕ failing test  ○ no test  — fixed to the bottom edge
  Row order: Blocked, InProgress, NotStarted, Completed; story number breaks ties
  Rows with every criterion passing render at reduced contrast so open work stands out
Trade-off: Criterion wording is clipped and failing-test output, test names, and story notes never appear, so diagnosing why a criterion fails still means opening the story or test run.

#### Draft 3

Structure:
  type StoryStatus = "Not Started" | "In Progress" | "Completed" | "Blocked"
  type TestResult = "passing" | "failing" | "no test"
  type Criterion = { id: string; text: string; result: TestResult; testName?: string; lastRun?: Date }
  type Story = { number: number; title: string; status: StoryStatus; blockedBy?: string; criteria: Criterion[] }
  type Spec = { name: string; folder: string; stories: Story[]; refreshedAt: Date }
  function remaining(spec: Spec): Criterion[]  // every criterion whose result is not "passing"
  SpecProgressPage(spec: Spec)
    Header
      SpecName (spec.name, spec.folder)
      Tally: "{passing} of {total} criteria pass · {completed} of {stories} stories done · refreshed {refreshedAt}"
      RemainingLine: one sentence per non-Completed story, e.g. "Story 3: 2 criteria failing, 1 untested"
    StoryList (all stories in number order, none collapsible, no filters)
      StoryCard(story) for each story
        CardHeader: "Story {number} — {title}" + StatusBadge(status)
        BlockedNote: shown only when status is "Blocked", prints blockedBy in full
        CriteriaTable (every criterion, always rendered)
          Row: ResultMark(result) | criterion text in full | testName or "no test" | lastRun
        CardFooter: "{passing}/{criteria.length} passing"
    StatusBadge(status): text label plus color; Blocked red, In Progress amber, Completed green, Not Started gray
    ResultMark(result): "pass" green check, "fail" red cross, "none" gray dash; label text always shown beside the icon
Trade-off: No collapsing, filtering, or sorting by what is left, so finished stories take the same space as open ones and the page can run to 64 criterion rows.

### Rating: ui-1

distinct_X:
distinct_Y:
more_distinct:
render_only_enough:
note:

## Brief ui-2 (medium: ui)

### Set X

#### Draft 1

Structure:
  type Artifact = { type: "page"; screenshot: string; liveHtml: string } | { type: "code"; snippet: string }
  type Option = { key: "A" | "B" | "C"; name: string; artifact: Artifact; commitments: string[] }
  type Verdict = { winner: "A" | "B" | "C"; losses: { key: "A" | "B" | "C"; oneLine: string }[] }
  type Exploration = { id: string; summary: string; options: Option[]; verdict: Verdict }

  axes(e: Exploration): string[]   // union of all commitments, deduped, in first-seen order

  ExplorationMatrix(e: Exploration)
    SummaryRow              // e.summary + "Winner: <key> <name>"
    Table
      HeaderRow             // one column per option; winner column outlined
        OptionHeader(o: Option)       // key, name, thumbnail of artifact
      AxisRow(axis: string) for each axes(e)
        Cell(o: Option, axis: string) // filled dot if o.commitments includes axis, blank if not
      LossRow               // per column: losses[key].oneLine, or "chosen" for winner
    ArtifactDrawer(o: Option)         // opens on header click
      full screenshot or live page, or the code snippet at full size
Trade-off: The matrix only works when commitments are worded consistently across drafts, and the drafts themselves shrink to thumbnails until opened.

#### Draft 2

Structure:
  type Sketch = { format: "rendered-page"; url: string } | { format: "code"; language: string; text: string }
  type Commitment = { text: string }
  type Candidate = { name: string; sketch: Sketch; commitments: Commitment[]; rejection: string | null }
  type Record = { slug: string; question: string; candidates: Candidate[]; decidedAt: string }
  // invariant: exactly one candidate has rejection === null; that is the chosen one

  chosen(r: Record): Candidate
  losers(r: Record): Candidate[]

  RecordPage(r: Record)
    QuestionHeader          // r.question, e.g. "How should the settings form save?"
    DecisionCard
      ChosenLine            // "Went with <chosen.name>"
      RejectionList         // "<loser.name>: <loser.rejection>" one row each
    CandidateTabs           // tabs default to the chosen candidate
      TabLabel(c: Candidate)          // name + check mark or strike
      CandidatePane(c: Candidate)
        CommitmentChips     // c.commitments as short chips
        SketchFrame         // full-width render or code block
    CompareToggle           // splits CandidatePane into two panes, pick any two
Trade-off: Drafts are seen one at a time by default; true side-by-side needs a click on the compare toggle and caps at two.

#### Draft 3

Structure:
  type DraftBody = { kind: "page"; html: string } | { kind: "code"; lang: string; source: string }
  type Draft = { id: string; label: string; body: DraftBody; commitsTo: string[] }
  type Outcome = { chosenId: string; whyChosen: string; lostBecause: Record<string, string> }
  type ExplorationRecord = { title: string; date: string; drafts: Draft[]; outcome: Outcome }

  ExplorationViewer(record: ExplorationRecord)
    VerdictBanner
      shows: "Chose <chosen.label>: <outcome.whyChosen>"
      shows: one line per loser: "<label> lost: <lostBecause[id]>"
    DraftColumns            // CSS grid, one column per draft (2 or 3), equal width
      DraftColumn(draft: Draft, isChosen: boolean, lostReason?: string)
        ColumnHeader        // label + "CHOSEN" badge or muted "lost" tag
        CommitList          // draft.commitsTo as bullets, top of column
        DraftPreview        // iframe sandbox for page; highlighted <pre> for code
                            // fixed height, scrolls inside the column
        LostReason          // lostReason repeated at column foot, absent when chosen
    RecordFooter            // title, date, link to source branch

  renderPreview(body: DraftBody): Element
Trade-off: Three full previews side by side get cramped below about 1200px, so rendered pages are shown scaled down rather than at real size.

### Set Y

#### Draft 1

Structure:
  type DraftKind = "page" | "code"
  type Draft = { id: string; label: string; kind: DraftKind; body: string; commitments: string[]; lostBecause?: string }
  type ExplorationRecord = { title: string; date: string; question: string; chosenId: string; chosenWhy: string; drafts: Draft[] }
  RecordPage(record: ExplorationRecord)
    DecisionBanner            // top of page, first thing read
      Question                // the question the exploration answered
      ChosenLine              // "Chose <label>: <chosenWhy>"
      LossList                // one row per non-chosen draft: "<label> lost: <lostBecause>"
    CommitmentGrid            // one column per draft, rows aligned so the same row compares across drafts
      ColumnHeader(draft)     // label, plus a "chosen" badge on the winner and a "lost" badge on the others
      CommitmentRow[]         // draft.commitments, one per line; rows padded so columns stay level
      LossNote(draft)         // lostBecause repeated under the column; empty for the winner
    DraftBodies               // side-by-side columns, same order as CommitmentGrid
      PageRender(body)        // kind "page": scaled iframe, fixed height, no internal scroll
      CodeSketch(body)        // kind "code": full sketch, monospace, wraps instead of scrolling sideways
    RecordFooter              // date, and the branch or commit the chosen draft shipped on
  layout(width: number): "columns" | "stacked"   // below 720px columns stack in draft order, winner first
  rule: no tabs, toggles, or collapsed sections; every draft, commitment, and reason renders on load
Trade-off: Gives up focus on any one draft; full renders and long code sketches push the bodies far down the page, so detailed comparison of bodies needs scrolling past the summary.

#### Draft 2

Structure:
  type DraftKind = "page" | "code"
  type Draft = { id: string; label: string; kind: DraftKind; preview: string; body: string; commitments: string[] }
  type Outcome = { draftId: string; chosen: boolean; reason: string }   // reason: one line, required for every losing draft
  type Record = { title: string; date: string; question: string; drafts: Draft[]; outcomes: Outcome[]; choiceSummary: string }
  RecordPage(record: Record)                       // one vertical page, no tabs or routes
    Header                                         // title, date, the question the prototype set out to answer
    VerdictBanner(chosen: Draft, summary: string)  // "Chose B: <choiceSummary>", pinned at the top of the scroll
    DraftRow(drafts: Draft[], outcomes: Outcome[]) // 2 or 3 equal-width columns, side by side
      DraftCard(draft: Draft, outcome: Outcome)
        CardHead                                   // label, kind badge, "Chosen" or "Lost" tag
        Preview(draft.preview)                     // fixed-height thumbnail or first 8 lines of code
        CommitmentList(draft.commitments, max=3)   // first three commitments; "+N more" if longer
        LossReason(outcome.reason)                 // shown only when chosen=false, one line, never truncated
        ExpandButton -> opens DraftDetail inline below the row
    DraftDetail(draft: Draft)                      // collapsed by default; one open at a time
      FullBody(draft.body)                         // full rendered page in an iframe, or full code with line numbers
      AllCommitments(draft.commitments)
      CloseButton
    CommitmentMatrix(drafts: Draft[])              // collapsed section: rows = commitments, columns = drafts, marks where each applies
  Rules: verdict and loss reasons are always visible without clicking; full bodies and the matrix are always behind a click
Trade-off: a side-by-side look at full draft content needs one draft opened at a time, so close detail comparison means toggling between drafts

#### Draft 3

Structure:
  type DraftKind = "page" | "code"
  type Draft = { id: string; label: string; kind: DraftKind; artifact: string; commitments: string[]; chosen: boolean; lostBecause?: string }
  type ExplorationRecord = { title: string; date: string; question: string; drafts: Draft[]; chosenId: string; choiceReason: string }
  type ViewId = "compare" | "reasons"
  RecordViewer(record: ExplorationRecord, view: ViewId)
    VerdictRail (left, fixed, always on screen)
      RecordHeader: title, date, the question the prototype set out to answer
      ChosenLine: "Chose <label>: <choiceReason>"
      LossList: one row per non-chosen draft -> "<label> lost: <lostBecause>"
      ViewSwitch: two rail entries, "Compare" and "Reasons"; the active one is underlined
    MainPane (right)
      CompareView (view = "compare")
        DraftColumns: one column per draft, equal width, 2 or 3 across
          DraftColumn(draft: Draft)
            ColumnHeader: label, kind badge, "Chosen" badge or "Lost" badge
            ArtifactFrame: rendered page at fixed scale, or code sketch in full with line numbers
            CommitmentList: every commitment as a bullet, never truncated
            LossNote: lostBecause printed under the list when chosen = false
      ReasonsView (view = "reasons")
        ReasonTable: rows = commitments merged across drafts, columns = drafts, cells = kept / dropped / not addressed
        ChoiceParagraph: choiceReason in full, with the losing drafts' lostBecause lines beneath
  Rule: no accordions, tooltips, or hover-only text; every field in Draft renders in at least one view and the rail renders in both
Trade-off: the per-commitment table sits behind a second view, so seeing which commitment decided the choice takes one click away from the side-by-side drafts

### Rating: ui-2

distinct_X:
distinct_Y:
more_distinct:
render_only_enough:
note:

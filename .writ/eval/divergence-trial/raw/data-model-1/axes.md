## Draft 1
Title: Verdict log with a per-patch status row
Commitment: mutable rows; verified status computed on write — the status row is overwritten in place, so its past values survive only in the verdict log, and a row edit leaves no trace of its own
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

## Draft 2
Title: Verdict event log with read-time patch-id matching
Commitment: append-only events; verified status computed on read — every status check rescans the PR's events and must resolve the head's patch-id, with no stored status to read directly
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

## Draft 3
Title: Event log with a status index maintained at append time
Commitment: append-only events; verified status computed on write — every append does the patch-id matching and rewrites the derived status rows, so writes cost more and is_verified only knows heads the ledger has been told about
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

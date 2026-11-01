## Draft 1
Title: Append-only JSONL ledger with dataclasses
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

## Draft 2
Title: SQLite table with insert-only rows
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

## Draft 3
Title: One JSON file per verdict plus a patch-id index
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

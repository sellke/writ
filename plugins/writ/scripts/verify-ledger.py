#!/usr/bin/env python3
"""Verification ledger (Story 1 of `2026-11-06-pr-ready-and-ledger`).

Records which PR heads passed the project's test and eval commands, and
answers whether a given head is VERIFIED.

CLI:
  verify-ledger.py record --pr N --head SHA --base REF --evidence EXIT CMD
                          [--evidence EXIT CMD ...] [--repo .]
  verify-ledger.py check  --pr N --head SHA [--base REF] [--repo .]

  --pr        the pull request number, 1 or more
  --head      the PR head: a full object id or any revision git resolves
  --base      the branch the PR merges into (record: required; check: default
              the base_ref of the PR's most recent row)
  --evidence  an exit code, then the command that produced it; repeatable,
              required for record
  --repo      the checkout whose ledger and git objects are read (default .)

File: <repo>/.writ/state/verify-ledger.json, written only by `record`
(temp file in the same folder, then os.replace). A missing file reads as no
rows.

  {"schema": "verify-ledger/1",
   "rows": [{"pr": 66, "head": "<full id>", "patch_id": "<40 hex>" | null,
             "base_ref": "origin/main", "merge_base": "<full id>" | null,
             "recorded_at": "2026-11-06T18:04:00Z",
             "evidence": [{"command": "<cmd>", "exit": 0}, ...]}]}

Patch-id recipe (whitespace-, mode-, and binary-sensitive; user diff config
cannot change it):
  merge_base = git merge-base <base> <head>
  git -c diff.suppressBlankEmpty=false diff --no-color --no-ext-diff
      --no-textconv --binary --full-index --no-renames --src-prefix=a/
      --dst-prefix=b/ --diff-algorithm=myers -U3 --inter-hunk-context=0
      --indent-heuristic --ignore-submodules=none --submodule=short
      --no-relative <merge_base> <head>
    | git patch-id --verbatim             -> the first field
The diff runs without GIT_DIFF_OPTS or GIT_EXTERNAL_DIFF in its environment
and goes to patch-id as bytes. `git patch-id --verbatim` with empty input exiting 0 means the flag
is supported.

record writes a row only when every --evidence exit is 0, --head is the
checked-out HEAD, and `git status --porcelain --untracked-files=no
--ignore-submodules=untracked` is empty.
Otherwise it prints every refusal that holds and writes nothing:
  reason: evidence_failed <exit> <command>
  reason: head_not_checked_out <short head> (HEAD is <short>)
  reason: dirty_tree <n> path(s)
  verify-ledger: fail (record refused for PR <n> head <short>)
An accepted record replaces the row with the same (PR, head), or appends:
  pass
  reason: recorded PR <n> head <short> patch-id <short|null>
  reason: replaced                                  (when a row was replaced)
  reason: patch_id_unavailable (<why>)              (when the id is null)
  verify-ledger: pass (recorded PR <n> head <short>, <k> command(s))

check reads VERIFIED when a row of the same PR has the same head
(verified_exact; no git call for a full id), or has a non-null patch_id
equal to the head's id against --base or the most recent row's base_ref
(verified_patch_id). Ids never match across PRs. Anything else is NOT
VERIFIED, including every case where the id cannot be computed:
  no_rows PR <n>
  verified_exact <short> (recorded <recorded_at>)
  verified_patch_id <short head> matches <short row head>
  head_unavailable <head>
  base_unavailable <ref>
  patch_id_unavailable (verbatim_unsupported|empty_diff|no_merge_base|
                        git_not_found|git_failed)
  patch_id_mismatch <short head> patch-id <short id> matches no verified row for PR <n>
Summary: `verify-ledger: pass (PR <n> head <short> VERIFIED, exact|patch-id)`
or `verify-ledger: fail (PR <n> head <short> NOT VERIFIED, <first code>)`.

ledger_check(repo, pr, head, base=None) -> (verdict, reasons) is the public
function `pr-ready.py` loads by path. It never prints and raises
LedgerError for an unreadable or malformed ledger.

Output (check shape): line 1 `pass` or `fail`, `reason:` lines, then the
summary. Control characters in printed values are escaped (`\\n`, `\\x1b`).
Exit 0 pass, 1 fail, 2 usage or could not start (unreadable or malformed
ledger, --repo not a directory or not a git work tree for record, an
unresolvable --head or --base for record, git not found or not runnable for
record, a failed write): stdout empty, cause on stderr after `verify-ledger: `.

Stdlib only, Python 3.9. Runs only `git`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SCHEMA = "verify-ledger/1"
LEDGER_REL = Path(".writ") / "state" / "verify-ledger.json"
SHORT = 7
FULL_ID = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
# C0, DEL, C1, and the Unicode line and paragraph separators: any of them in a
# printed value could start a new output line.
CONTROL = re.compile("[\x00-\x1f\x7f-\x9f  ]")
DIFF_CONFIG = ("-c", "diff.suppressBlankEmpty=false")
DIFF_FLAGS = ("--no-color", "--no-ext-diff", "--no-textconv", "--binary", "--full-index",
              "--no-renames", "--src-prefix=a/", "--dst-prefix=b/", "--diff-algorithm=myers",
              "-U3", "--inter-hunk-context=0", "--indent-heuristic", "--ignore-submodules=none",
              "--submodule=short", "--no-relative")
# Environment that would change `git diff` output past the pinned flags.
DIFF_ENV_DROP = ("GIT_DIFF_OPTS", "GIT_EXTERNAL_DIFF")
ROW_FIELDS = ("pr", "head", "patch_id", "base_ref", "merge_base", "recorded_at", "evidence")


class UsageError(Exception):
    """Exit-2 conditions: the command could not start."""


class LedgerError(Exception):
    """The ledger file is unreadable or malformed."""


class GitNotFound(Exception):
    """`git` could not be run. `why` is `git_not_found` when it is not on
    PATH and `git_failed` for any other OS error."""

    def __init__(self, message: str, why: str = "git_not_found") -> None:
        super().__init__(message)
        self.why = why


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def printable(text: str) -> str:
    """Escape control characters (`\\n` -> `\\\\n`, ESC -> `\\\\x1b`) so a crafted
    value cannot add an output line. Other text is unchanged."""
    return CONTROL.sub(lambda m: repr(m.group())[1:-1], text)


def short(value: str) -> str:
    """The first 7 hex digits of a full id; any other revision as given."""
    return value[:SHORT] if FULL_ID.match(value) else value


# ---------------------------------------------------------------------------
# git
# ---------------------------------------------------------------------------

def _git(repo: Path, *args: str, data: Optional[bytes] = None, binary: bool = False,
         env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    """Run one git command in `repo`. Never raises on a non-zero exit. With
    `binary`, stdout stays bytes (diffs are not UTF-8)."""
    try:
        if binary:
            return subprocess.run(["git", "-C", str(repo), *args], input=data,
                                  capture_output=True, check=False, env=env)
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                              check=False, encoding="utf-8", errors="replace", env=env)
    except FileNotFoundError:
        raise GitNotFound("git not found")
    except OSError as exc:
        raise GitNotFound("cannot run git (%s)" % exc, "git_failed")


def _diff_env() -> Dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in DIFF_ENV_DROP}


def _rev(repo: Path, rev: str) -> Optional[str]:
    """The full commit id `rev` names, or None. A leading `-` never resolves:
    git would read it as an option."""
    if not rev or rev.startswith("-"):
        return None
    proc = _git(repo, "rev-parse", "--verify", "--quiet", "%s^{commit}" % rev)
    out = proc.stdout.strip()
    return out.lower() if proc.returncode == 0 and FULL_ID.match(out) else None


def _resolve(repo: Path, rev: str) -> str:
    sha = _rev(repo, rev)
    if sha is None:
        raise UsageError("cannot resolve %s" % rev)
    return sha


_VERBATIM: Dict[str, bool] = {}


def _verbatim_supported(repo: Path) -> bool:
    if "ok" not in _VERBATIM:
        _VERBATIM["ok"] = _git(repo, "patch-id", "--verbatim", data=b"",
                               binary=True).returncode == 0
    return _VERBATIM["ok"]


def patch_id(repo: Path, base_sha: str,
             head_sha: str) -> Tuple[Optional[str], Optional[str], str]:
    """(merge base, patch id, why). The id is None when it cannot be computed,
    and `why` names the cause; `why` is "" when the id is set."""
    try:
        mb_proc = _git(repo, "merge-base", base_sha, head_sha)
        if mb_proc.returncode == 1:
            return None, None, "no_merge_base"
        merge_base = mb_proc.stdout.strip().lower()
        if mb_proc.returncode != 0 or not FULL_ID.match(merge_base):
            return None, None, "git_failed"
        if not _verbatim_supported(repo):
            return merge_base, None, "verbatim_unsupported"
        diff = _git(repo, *DIFF_CONFIG, "diff", *DIFF_FLAGS, merge_base, head_sha, binary=True,
                    env=_diff_env())
        if diff.returncode != 0:
            return merge_base, None, "git_failed"
        if not diff.stdout.strip():
            return merge_base, None, "empty_diff"
        pid = _git(repo, "patch-id", "--verbatim", data=diff.stdout, binary=True)
        if pid.returncode != 0:
            return merge_base, None, "git_failed"
        fields = pid.stdout.decode("ascii", "replace").split()
        if not fields:
            return merge_base, None, "empty_diff"
        return merge_base, fields[0].lower(), ""
    except GitNotFound as exc:
        return None, None, exc.why


# ---------------------------------------------------------------------------
# Ledger file
# ---------------------------------------------------------------------------

def ledger_path(repo: Path) -> Path:
    return repo / LEDGER_REL


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_row(i: int, row: Any) -> None:
    where = "row %d" % i
    if not isinstance(row, dict):
        raise LedgerError("%s is not an object" % where)
    for name in ROW_FIELDS:
        if name not in row:
            raise LedgerError("%s has no %s" % (where, name))
    if not _is_int(row["pr"]) or row["pr"] < 1:
        raise LedgerError("%s pr is not an integer of 1 or more" % where)
    if not isinstance(row["head"], str) or not FULL_ID.match(row["head"]):
        raise LedgerError("%s head is not a full object id" % where)
    for name in ("patch_id", "merge_base"):
        value = row[name]
        if value is not None and (not isinstance(value, str) or not FULL_ID.match(value)):
            raise LedgerError("%s %s is not null or a full hex id" % (where, name))
    for name in ("base_ref", "recorded_at"):
        if not isinstance(row[name], str):
            raise LedgerError("%s %s is not a string" % (where, name))
    if not isinstance(row["evidence"], list):
        raise LedgerError("%s evidence is not a list" % where)
    for item in row["evidence"]:
        if not (isinstance(item, dict) and isinstance(item.get("command"), str)
                and _is_int(item.get("exit"))):
            raise LedgerError("%s evidence entry is not {command, exit}" % where)


def load_ledger(repo: Path) -> Dict[str, Any]:
    """The ledger document. A missing file reads as no rows; anything
    unreadable or malformed raises LedgerError."""
    path = ledger_path(repo)
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return {"schema": SCHEMA, "rows": []}
    except (OSError, UnicodeDecodeError) as exc:
        raise LedgerError("cannot read %s (%s)" % (LEDGER_REL.as_posix(), exc))
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise LedgerError("%s is not JSON (%s)" % (LEDGER_REL.as_posix(), exc))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise LedgerError("%s schema is not %s" % (LEDGER_REL.as_posix(), SCHEMA))
    if not isinstance(data.get("rows"), list):
        raise LedgerError("%s rows is not a list" % LEDGER_REL.as_posix())
    for i, row in enumerate(data["rows"]):
        try:
            _check_row(i, row)
        except LedgerError as exc:
            raise LedgerError("%s %s" % (LEDGER_REL.as_posix(), exc))
    return data


def write_ledger(repo: Path, data: Dict[str, Any]) -> None:
    """Write via a temp file in the same folder and os.replace, so the target
    is either the old file or the new one. The temp file never survives."""
    path = ledger_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------

def _latest(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The row with the latest recorded_at; a tie goes to the later row."""
    best = rows[0]
    for row in rows[1:]:
        if row["recorded_at"] >= best["recorded_at"]:
            best = row
    return best


def _exact(rows: List[Dict[str, Any]], head: str) -> Optional[Dict[str, Any]]:
    found = [row for row in rows if row["head"].lower() == head]
    return found[-1] if found else None


def ledger_check(repo: Path, pr: int, head: str,
                 base: Optional[str] = None) -> Tuple[str, List[str]]:
    """("pass" | "fail", reasons) for PR `pr` at `head`. Never prints. Raises
    LedgerError for an unreadable or malformed ledger. Every case where the
    patch-id cannot be computed is "fail"."""
    rows = [row for row in load_ledger(Path(repo))["rows"] if row["pr"] == pr]
    if not rows:
        return "fail", ["no_rows PR %d" % pr]
    if FULL_ID.match(head):
        row = _exact(rows, head.lower())
        if row is not None:
            return "pass", ["verified_exact %s (recorded %s)" % (head[:SHORT].lower(),
                                                                  row["recorded_at"])]
    try:
        head_sha = _rev(Path(repo), head)
        if head_sha is None:
            return "fail", ["head_unavailable %s" % head]
        row = _exact(rows, head_sha)
        if row is not None:
            return "pass", ["verified_exact %s (recorded %s)" % (head_sha[:SHORT],
                                                                  row["recorded_at"])]
        base_ref = base if base is not None else _latest(rows)["base_ref"]
        base_sha = _rev(Path(repo), base_ref)
        if base_sha is None:
            return "fail", ["base_unavailable %s" % base_ref]
    except GitNotFound as exc:
        return "fail", ["patch_id_unavailable (%s)" % exc.why]
    _, pid, why = patch_id(Path(repo), base_sha, head_sha)
    if pid is None:
        return "fail", ["patch_id_unavailable (%s)" % why]
    for row in rows:
        if row["patch_id"] is not None and row["patch_id"].lower() == pid:
            return "pass", ["verified_patch_id %s matches %s" % (head_sha[:SHORT],
                                                                  row["head"][:SHORT].lower())]
    return "fail", ["patch_id_mismatch %s patch-id %s matches no verified row for PR %d"
                    % (head_sha[:SHORT], pid[:SHORT], pr)]


# ---------------------------------------------------------------------------
# record
# ---------------------------------------------------------------------------

def _require_dir(repo: Path) -> None:
    if not repo.is_dir():
        raise UsageError("--repo %s is not a directory" % repo)


def _require_work_tree(repo: Path) -> None:
    _require_dir(repo)
    proc = _git(repo, "rev-parse", "--is-inside-work-tree")
    if proc.returncode != 0 or proc.stdout.strip() != "true":
        raise UsageError("--repo %s is not a git work tree" % repo)


def _parse_evidence(pairs: Sequence[Sequence[str]]) -> List[Dict[str, Any]]:
    evidence = []
    for exit_text, command in pairs:
        try:
            code = int(exit_text)
        except ValueError:
            raise UsageError("evidence exit %s is not an integer" % exit_text)
        if not command.strip():
            raise UsageError("evidence command is empty")
        evidence.append({"command": command, "exit": code})
    return evidence


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record(repo: Path, pr: int, head: str, base: str,
           pairs: Sequence[Sequence[str]]) -> Tuple[str, List[str], str]:
    """(verdict, reasons, summary). Raises UsageError or LedgerError for exit 2;
    writes the ledger only on "pass"."""
    if pr < 1:
        raise UsageError("--pr must be 1 or more")
    evidence = _parse_evidence(pairs)
    try:
        _require_work_tree(repo)
        head_sha = _resolve(repo, head)
        base_sha = _resolve(repo, base)
        checked_out = _resolve(repo, "HEAD")
        status = _git(repo, "status", "--porcelain", "--untracked-files=no",
                      "--ignore-submodules=untracked")
    except GitNotFound as exc:
        raise UsageError(str(exc))
    if status.returncode != 0:
        raise UsageError("git status failed (%s)" % status.stderr.strip())

    refusals = ["evidence_failed %d %s" % (e["exit"], e["command"])
                for e in evidence if e["exit"] != 0]
    if checked_out != head_sha:
        refusals.append("head_not_checked_out %s (HEAD is %s)"
                        % (head_sha[:SHORT], checked_out[:SHORT]))
    dirty = [line for line in status.stdout.splitlines() if line.strip()]
    if dirty:
        refusals.append("dirty_tree %d path(s)" % len(dirty))
    if refusals:
        return "fail", refusals, ("verify-ledger: fail (record refused for PR %d head %s)"
                                  % (pr, head_sha[:SHORT]))

    data = load_ledger(repo)
    merge_base, pid, why = patch_id(repo, base_sha, head_sha)
    if why == "git_not_found":
        raise UsageError("git not found")
    row = {"pr": pr, "head": head_sha, "patch_id": pid, "base_ref": base,
           "merge_base": merge_base, "recorded_at": _now(), "evidence": evidence}
    rows = data["rows"]
    replaced = False
    for i, old in enumerate(rows):
        if old["pr"] == pr and old["head"].lower() == head_sha:
            rows[i] = row
            replaced = True
            break
    if not replaced:
        rows.append(row)
    try:
        write_ledger(repo, {"schema": SCHEMA, "rows": rows})
    except OSError as exc:
        raise UsageError("cannot write %s (%s)" % (LEDGER_REL.as_posix(), exc))

    reasons = ["recorded PR %d head %s patch-id %s"
               % (pr, head_sha[:SHORT], pid[:SHORT] if pid else "null")]
    if replaced:
        reasons.append("replaced")
    if pid is None:
        reasons.append("patch_id_unavailable (%s)" % why)
    return "pass", reasons, ("verify-ledger: pass (recorded PR %d head %s, %d command(s))"
                             % (pr, head_sha[:SHORT], len(evidence)))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="verify-ledger.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    r = sub.add_parser("record", help="record that a PR head passed its evidence commands")
    r.add_argument("--pr", type=int, required=True, help="pull request number")
    r.add_argument("--head", required=True, help="the checked-out PR head")
    r.add_argument("--base", required=True, help="the branch the PR merges into")
    r.add_argument("--evidence", nargs=2, action="append", required=True,
                   metavar=("EXIT", "CMD"), help="exit code and command; repeatable")
    r.add_argument("--repo", type=Path, default=Path("."), help="checkout root (default .)")
    c = sub.add_parser("check", help="is this PR head VERIFIED?")
    c.add_argument("--pr", type=int, required=True, help="pull request number")
    c.add_argument("--head", required=True, help="the PR head to check")
    c.add_argument("--base", default=None,
                   help="base to diff against (default: the PR's latest row base_ref)")
    c.add_argument("--repo", type=Path, default=Path("."), help="checkout root (default .)")
    return parser


def run(args: argparse.Namespace) -> Tuple[str, List[str], str]:
    if args.action == "record":
        return record(args.repo, args.pr, args.head, args.base, args.evidence)
    if args.pr < 1:
        raise UsageError("--pr must be 1 or more")
    _require_dir(args.repo)
    verdict, reasons = ledger_check(args.repo, args.pr, args.head, args.base)
    code = reasons[0].split(" ", 1)[0]
    if verdict == "pass":
        kind = "exact" if code == "verified_exact" else "patch-id"
        last = "verify-ledger: pass (PR %d head %s VERIFIED, %s)" % (args.pr, short(args.head),
                                                                      kind)
    else:
        last = "verify-ledger: fail (PR %d head %s NOT VERIFIED, %s)" % (args.pr,
                                                                          short(args.head), code)
    return verdict, reasons, last


def main(argv: Optional[List[str]] = None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        verdict, reasons, last = run(args)
    except (UsageError, LedgerError) as exc:
        print("verify-ledger: %s" % printable(str(exc)), file=sys.stderr)
        return 2
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(errors="backslashreplace")  # a non-UTF-8 console never crashes output
    print("\n".join([verdict] + ["reason: %s" % printable(r) for r in reasons]
                    + [printable(last)]))
    return 1 if verdict == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())

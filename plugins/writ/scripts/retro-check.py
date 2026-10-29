#!/usr/bin/env python3
"""Retro file and rule table check (Story 1 of `2026-10-25-retro-fix-ladder`).

Checks the fix-ladder fields of a /retro file and the rule-to-enforcer table.

CLI:
  retro-check.py [--retro PATH] [--table PATH] [--repo DIR]

  --retro  a retro file written by /retro
  --table  the rule table; default rule-enforcers.md beside the retro file,
           read when it exists or when a finding needs a row
  --repo   where proof commit SHAs resolve, default `.`
At least one of --retro and --table is required.

Retro file: `## Transcripts` lists transcript paths (an item's first
backticked token, else its first word). `## Findings` holds blocks headed
`### F<n> [<Severity>] <Signal>: <title>`, each with `**Rung:**`,
`**Ladder:**`, `**Proof:**`, and `**Disposition:**` lines.
  Rung         architecture, types, lint, test, docs, or none
  Ladder       `<rung>: no (<reason>); ...; <rung>: yes`, from architecture,
               in order, with no gaps, ending at the Rung
  Proof        `mistake <ref>; check `<command>`; result fails|passes|pending`;
               <ref> is a 7-40 character commit SHA or a listed .jsonl path
  Disposition  applied, refreshed, issue, dismissed, or deferred
Table: the first markdown table, columns Rule | Written in | Enforcer | Rung |
Proof | Since. Enforcer `none` needs Rung docs and an em dash Proof; any other
Enforcer needs Proof `<ref>: fails`. An applied or refreshed finding with a
Rung other than none needs a row whose Since is `<retro file name> F<n>`.

Reason codes. Unverifiable: retro_missing, table_missing (explicit --table),
no_git. Fail: table_missing (default table needed), no_findings_section,
rung_missing, rung_invalid, rung_none_on_mistake, ladder_missing,
ladder_order, ladder_no_reason, ladder_rung_mismatch, proof_missing,
proof_malformed, proof_ref_unknown, proof_not_failing, applied_test_rung,
disposition_missing, disposition_invalid, table_row_missing, table_header,
table_rung_invalid, table_unenforced_rung, table_enforcer_without_proof,
table_proof_ref_unknown.

Output (check shape): line 1 `pass`, `fail`, or `unverifiable`; then
`reason: <code> <detail>` lines in file order, retro findings first, then
table rows; last line
`retro-check: <verdict> (<f> findings, <r> table rows, <n> reasons)`.
Any fail reason makes the verdict fail; otherwise any unverifiable reason
makes it unverifiable. Control characters in printed values are escaped.

Exit 0 pass or unverifiable, 1 fail, 2 usage or a file that exists but
cannot be read (stdout empty, cause on stderr).

Stdlib only, Python 3.9. Runs only `git rev-parse` and `git cat-file`, and
only when a SHA needs resolving. Writes nothing.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

LADDER = ("architecture", "types", "lint", "test", "docs")
RUNGS = LADDER + ("none",)
PROOF_RUNGS = frozenset(("architecture", "types", "lint", "test"))
LADDER_SIGNALS = frozenset(("silent patch", "stale guidance", "repeated mistake",
                            "user correction"))
DISPOSITIONS = ("applied", "refreshed", "issue", "dismissed", "deferred")
ROW_DISPOSITIONS = frozenset(("applied", "refreshed"))
HEADER = ["Rule", "Written in", "Enforcer", "Rung", "Proof", "Since"]
DEFAULT_TABLE = "rule-enforcers.md"
NO_PROOF = "—"

FENCE = re.compile(r"^ {0,3}(```|~~~)")
HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*$")
FINDING = re.compile(r"^(F\d+)\b[ \t]*(.*)$")
SIGNAL = re.compile(r"^(?:\[[^\]]*\][ \t]*)?([^:]*)")
FIELD = re.compile(r"^[ \t]*(?:[-*+][ \t]+)?\*\*(Rung|Ladder|Proof|Disposition):\*\*(.*)$")
LIST_ITEM = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+(.*)$")
BACKTICKED = re.compile(r"`([^`]+)`")
SHA = re.compile(r"[0-9a-f]{7,40}")
PROOF = re.compile(r"^mistake\s+(?:`([^`]+)`|([^\s;`]+))\s*;\s*check\s+`(.+)`\s*;"
                   r"\s*result\s+(fails|passes|pending)$")
TABLE_PROOF = re.compile(r"^(?:`([^`]+)`|(\S+)):\s*fails$")
YES_ENTRY = re.compile(r"^yes\b")
NO_ENTRY = re.compile(r"^no\s*\(\s*\S.*\)$")
DELIMITER_ROW = re.compile(r"^\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?\s*$")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
# C0, DEL, C1, and the Unicode line and paragraph separators: any of them in a
# printed value could start a new output line.
CONTROL = re.compile("[\x00-\x1f\x7f-\x9f\u2028\u2029]")


class UsageError(Exception):
    """Exit-2 conditions: the check could not start."""


class Finding(NamedTuple):
    fid: str                # `F<n>` as written
    signal: str             # lower-cased signal name from the heading
    fields: Dict[str, str]  # first Rung, Ladder, Proof, and Disposition values


class Retro(NamedTuple):
    has_findings: bool
    transcripts: Set[str]
    findings: List[Finding]


class Table(NamedTuple):
    header: Optional[List[str]]  # None when the file has no markdown table
    rows: List[List[str]]        # data rows, padded to the header width


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def _exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError as exc:  # 3.9 re-raises EACCES and the like
        raise UsageError("cannot read %s (%s)" % (path, exc.strerror or exc))


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise UsageError("cannot read %s (%s)" % (path, exc.strerror or exc))


def _lines(text: str) -> List[str]:
    """Lines outside fenced code blocks."""
    out: List[str] = []
    fence: Optional[str] = None
    for line in text.splitlines():
        match = FENCE.match(line)
        if match:
            if fence is None:
                fence = match.group(1)
            elif match.group(1) == fence:
                fence = None
            continue
        if fence is None:
            out.append(line)
    return out


def _unquote(value: str) -> str:
    """Drop one pair of backticks wrapping the whole value."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == "`" and "`" not in value[1:-1]:
        return value[1:-1].strip()
    return value


def _transcript_path(item: str) -> str:
    match = BACKTICKED.search(item)
    if match:
        return match.group(1).strip()
    words = item.split()
    return words[0] if words else ""


def parse_retro(text: str) -> Retro:
    has_findings = False
    transcripts: Set[str] = set()
    findings: List[Finding] = []
    section: Optional[str] = None
    current: Optional[Finding] = None
    for line in _lines(text):
        heading = HEADING.match(line)
        level = len(heading.group(1)) if heading else 0
        if heading and level <= 3:
            current = None
            if level <= 2:
                section = heading.group(2) if level == 2 else None
                has_findings = has_findings or section == "Findings"
            elif section == "Findings":
                match = FINDING.match(heading.group(2))
                if match:
                    signal = SIGNAL.match(match.group(2)).group(1).strip().lower()
                    current = Finding(match.group(1), signal, {})
                    findings.append(current)
            continue
        if section == "Transcripts":
            item = LIST_ITEM.match(line)
            if item:
                transcripts.add(_transcript_path(item.group(1)))
        elif current is not None:
            field = FIELD.match(line)
            if field and field.group(1) not in current.fields:
                current.fields[field.group(1)] = field.group(2).strip()
    return Retro(has_findings, transcripts, findings)


def _cells(line: str) -> List[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    return [cell.strip().replace("\\|", "|") for cell in CELL_SPLIT.split(text)]


def parse_table(text: str) -> Table:
    """The first markdown table: a `|` line followed by a delimiter row."""
    lines = _lines(text)
    for i in range(len(lines) - 1):
        if lines[i].lstrip().startswith("|") and DELIMITER_ROW.match(lines[i + 1]):
            header = _cells(lines[i])
            rows: List[List[str]] = []
            for line in lines[i + 2:]:
                if not line.lstrip().startswith("|"):
                    break
                cells = _cells(line)
                rows.append(cells + [""] * (len(HEADER) - len(cells)))
            return Table(header, rows)
    return Table(None, [])


# ---------------------------------------------------------------------------
# git
# ---------------------------------------------------------------------------

class Git:
    """Resolves commit SHAs in one repository. The work-tree check runs once,
    on the first SHA that needs resolving."""

    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.usable: Optional[bool] = None

    def _run(self, *args: str) -> Optional[subprocess.CompletedProcess]:
        try:
            return subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True,
                                  check=False, encoding="utf-8", errors="replace")
        except OSError:  # git not on PATH, or not runnable
            return None

    def has_commit(self, sha: str) -> Optional[bool]:
        """True or False in a git work tree; None when there is none or no git."""
        if self.usable is None:
            proc = self._run("rev-parse", "--is-inside-work-tree")
            self.usable = (proc is not None and proc.returncode == 0
                           and proc.stdout.strip() == "true")
        if not self.usable:
            return None
        # `sha` matches SHA, so it can never read as an option.
        proc = self._run("cat-file", "-e", "%s^{commit}" % sha)
        if proc is None:
            self.usable = False
            return None
        return proc.returncode == 0


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def _shown(value: str) -> str:
    return value if value else '""'


def _is_ref(ref: str) -> bool:
    return bool(SHA.fullmatch(ref)) or ref.endswith(".jsonl")


def _split_entries(value: str) -> List[str]:
    """Split a Ladder value on `;` outside parentheses."""
    parts: List[str] = []
    depth = start = 0
    for i, char in enumerate(value):
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char == ";" and depth == 0:
            parts.append(value[start:i])
            start = i + 1
    parts.append(value[start:])
    return [part.strip() for part in parts if part.strip()]


class Checker:
    def __init__(self, repo: Path) -> None:
        self.reasons: List[Tuple[str, str]] = []  # (class, text) in print order
        self.git = Git(repo)
        self.no_git_reported = False

    def fail(self, text: str) -> None:
        self.reasons.append(("fail", text))

    def unverifiable(self, text: str) -> None:
        self.reasons.append(("unverifiable", text))

    def commit_known(self, sha: str) -> Optional[bool]:
        """None when the SHA cannot be looked up; `no_git` prints once."""
        known = self.git.has_commit(sha)
        if known is None and not self.no_git_reported:
            self.unverifiable("no_git")
            self.no_git_reported = True
        return known

    def ladder(self, fid: str, rung: str, value: str) -> None:
        names: List[str] = []
        verdicts: List[str] = []
        no_reason: List[str] = []
        for entry in _split_entries(value):
            name, _, rest = entry.partition(":")
            name, rest = name.strip(), rest.strip()
            names.append(name)
            if YES_ENTRY.match(rest):
                verdicts.append("yes")
            else:
                verdicts.append("no")
                if not NO_ENTRY.match(rest):
                    no_reason.append(name)
        if names != list(LADDER[:len(names)]):
            self.fail("ladder_order %s" % fid)
        for name in no_reason:
            self.fail("ladder_no_reason %s %s" % (fid, _shown(name)))
        if not names or verdicts[-1] != "yes" or "yes" in verdicts[:-1] or names[-1] != rung:
            self.fail("ladder_rung_mismatch %s" % fid)

    def finding(self, finding: Finding, transcripts: Set[str]) -> bool:
        """Check one finding; True when it needs a table row."""
        fid, fields = finding.fid, finding.fields
        rung: Optional[str] = None  # set only when the value is in the vocabulary
        value = _unquote(fields.get("Rung", ""))
        if "Rung" not in fields:
            self.fail("rung_missing %s" % fid)
        elif value not in RUNGS:
            self.fail("rung_invalid %s %s" % (fid, _shown(value)))
        else:
            rung = value
            if rung == "none" and finding.signal in LADDER_SIGNALS:
                self.fail("rung_none_on_mistake %s" % fid)
        laddered = rung is not None and rung != "none"

        if laddered:
            if "Ladder" not in fields:
                self.fail("ladder_missing %s" % fid)
            else:
                self.ladder(fid, rung, fields["Ladder"])

        result: Optional[str] = None
        if "Proof" not in fields:
            if rung in PROOF_RUNGS:
                self.fail("proof_missing %s" % fid)
        else:
            match = PROOF.match(fields["Proof"])
            ref = (match.group(1) or match.group(2)).strip() if match else ""
            if not match or not _is_ref(ref):
                self.fail("proof_malformed %s" % fid)
            else:
                result = match.group(4)
                if SHA.fullmatch(ref):
                    if self.commit_known(ref) is False:
                        self.fail("proof_ref_unknown %s %s" % (fid, ref))
                elif ref not in transcripts:
                    self.fail("proof_ref_unknown %s %s" % (fid, ref))

        disposition: Optional[str] = None
        value = _unquote(fields.get("Disposition", ""))
        if "Disposition" not in fields:
            self.fail("disposition_missing %s" % fid)
        elif value not in DISPOSITIONS:
            self.fail("disposition_invalid %s %s" % (fid, _shown(value)))
        else:
            disposition = value

        if disposition == "applied" and result is not None and result != "fails":
            self.fail("proof_not_failing %s" % fid)
        if disposition == "applied" and rung == "test":
            self.fail("applied_test_rung %s" % fid)
        return laddered and disposition in ROW_DISPOSITIONS

    def table(self, table: Table) -> None:
        if table.header != HEADER:
            self.fail("table_header")
            return  # columns cannot be trusted, so rows are not read
        for n, cells in enumerate(table.rows, 1):
            enforcer, rung, proof = _unquote(cells[2]), _unquote(cells[3]), cells[4].strip()
            if rung not in LADDER:
                self.fail("table_rung_invalid row %d %s" % (n, _shown(rung)))
            if enforcer == "none":
                if rung != "docs" or proof != NO_PROOF:
                    self.fail("table_unenforced_rung row %d" % n)
                continue
            match = TABLE_PROOF.match(proof)
            ref = (match.group(1) or match.group(2)).strip() if match else ""
            if not match or not _is_ref(ref):
                self.fail("table_enforcer_without_proof row %d" % n)
            elif SHA.fullmatch(ref) and self.commit_known(ref) is False:
                self.fail("table_proof_ref_unknown row %d %s" % (n, ref))


def _since_cells(table: Table) -> Optional[Set[str]]:
    """Since values, or None when the header is wrong and rows cannot be read."""
    if table.header != HEADER:
        return None
    return {_unquote(cells[5]) for cells in table.rows}


def check(retro_arg: Optional[str], table_arg: Optional[str],
          repo: Path) -> Tuple[str, List[str], str]:
    """(verdict, reasons, summary line). Raises UsageError for exit 2."""
    checker = Checker(repo)
    table_path = Path(table_arg) if table_arg is not None else None
    table_shown = table_arg
    retro: Optional[Retro] = None
    retro_name = ""
    if retro_arg is not None:
        retro_path = Path(retro_arg)
        retro_name = retro_path.name
        if _exists(retro_path):
            retro = parse_retro(_read(retro_path))
        else:
            checker.unverifiable("retro_missing %s" % retro_arg)
        if table_path is None:
            table_path = retro_path.parent / DEFAULT_TABLE
            table_shown = str(table_path)

    table: Optional[Table] = None
    if table_path is not None and _exists(table_path):
        table = parse_table(_read(table_path))

    needs_row = False
    if retro is not None:
        if not retro.has_findings:
            checker.fail("no_findings_section")
        since = _since_cells(table) if table is not None else None
        for finding in retro.findings:
            if checker.finding(finding, retro.transcripts):
                needs_row = True
                if since is not None and "%s %s" % (retro_name, finding.fid) not in since:
                    checker.fail("table_row_missing %s" % finding.fid)

    if table is not None:
        checker.table(table)
    elif table_arg is not None:
        checker.unverifiable("table_missing %s" % table_shown)
    elif needs_row:
        checker.fail("table_missing %s" % table_shown)

    classes = {cls for cls, _ in checker.reasons}
    verdict = "fail" if "fail" in classes else (
        "unverifiable" if "unverifiable" in classes else "pass")
    reasons = [text for _, text in checker.reasons]
    summary = "retro-check: %s (%d findings, %d table rows, %d reasons)" % (
        verdict, len(retro.findings) if retro else 0, len(table.rows) if table else 0,
        len(reasons))
    return verdict, reasons, summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def printable(text: str) -> str:
    """Escape control characters (`\\n` -> `\\\\n`, ESC -> `\\\\x1b`) so a crafted
    value cannot add an output line. Other text is unchanged."""
    return CONTROL.sub(lambda m: repr(m.group())[1:-1], text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="retro-check.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--retro", metavar="PATH", help="retro file to check")
    parser.add_argument("--table", metavar="PATH",
                        help="rule table (default: rule-enforcers.md beside --retro)")
    parser.add_argument("--repo", metavar="DIR", type=Path, default=Path("."),
                        help="repository where proof SHAs resolve (default .)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if args.retro is None and args.table is None:
            parser.error("give --retro, --table, or both")
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        verdict, reasons, last = check(args.retro, args.table, args.repo)
    except UsageError as exc:
        print("retro-check: %s" % printable(str(exc)), file=sys.stderr)
        return 2
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(errors="backslashreplace")  # a non-UTF-8 console never crashes output
    print("\n".join([verdict] + ["reason: %s" % printable(r) for r in reasons] + [last]))
    return 1 if verdict == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())

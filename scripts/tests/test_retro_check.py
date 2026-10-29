#!/usr/bin/env python3
"""Fixture tests for `scripts/retro-check.py` (Story 1 of
`2026-10-25-retro-fix-ladder`).

Each test writes a retro file and a rule table under `tmp_path` and runs the
real script through an argument list. SHA cases use a `git init` repository
with one commit. Fixture git calls and the script run with the user's global
and system git config off and a fixed author and committer, so the machine's
git setup cannot change a result.

- A conforming retro file and table pass [AC-1.1].
- Each finding-level defect fails with its reason code and finding ID [AC-1.2].
- Proof refs resolve against the repository or the `## Transcripts` list, and
  a `--repo` outside a git work tree is `unverifiable` with `no_git` [AC-1.3].
- Table defects fail with their reason code; an explicit `--table` that does
  not exist is `unverifiable` with `table_missing` [AC-1.4].
- Usage errors exit 2 with stdout empty, `--help` exits 0, and a run leaves
  the fixture directory unchanged [AC-1.5].

Run: uv run --python 3.9 pytest scripts/tests/test_retro_check.py
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "retro-check.py"

RETRO_NAME = "2026-10-30-spec-x.md"
TRANSCRIPT = "transcripts/run-1.jsonl"
FAKE_SHA = "0123456789abcdef0123456789abcdef01234567"

LADDER_LINT = ("architecture: no (no boundary rule covers it); "
               "types: no (the type checker cannot see it); lint: yes")
LADDER_TEST = ("architecture: no (no boundary rule covers it); "
               "types: no (the type checker cannot see it); "
               "lint: no (no lint rule names the fix); test: yes")
LADDER_DOCS = ("architecture: no (not a layout rule); types: no (not a type error); "
               "lint: no (no rule can see intent); test: no (no failing case to pin); "
               "docs: yes")

HEADER_ROW = "| Rule | Written in | Enforcer | Rung | Proof | Since |"
DELIMITER_ROW = "|---|---|---|---|---|---|"


def _clean_env() -> Dict[str, str]:
    """The caller's env minus GIT_*, with global and system git config off and
    a fixed author and committer."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Retro Test",
        "GIT_AUTHOR_EMAIL": "retro@example.com",
        "GIT_COMMITTER_NAME": "Retro Test",
        "GIT_COMMITTER_EMAIL": "retro@example.com",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
    })
    return env


ENV = _clean_env()


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          encoding="utf-8", env=ENV)
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), proc.stderr))
    return proc.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Tuple[Path, str]:
    """A `git init` repository with one commit, and that commit's SHA."""
    path = tmp_path / "repo"
    path.mkdir()
    git(path, "-c", "init.defaultBranch=main", "init", "-q")
    (path / "app.py").write_text("def save():\n    pass\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "chore: base")
    return path, git(path, "rev-parse", "HEAD")


def proof(ref: str, result: str = "fails",
          command: str = "ruff check --select BLE src/") -> str:
    return "mistake %s; check `%s`; result %s" % (ref, command, result)


def finding(n: int = 1, signal: str = "Silent patch", rung: Optional[str] = "lint",
            ladder: Optional[str] = LADDER_LINT, proof_line: Optional[str] = proof(TRANSCRIPT),
            disposition: Optional[str] = "issue", body: str = "") -> str:
    """One `### F<n>` block. A field passed as None is left out."""
    lines = ["### F%d [High] %s: Bare except hid a failed write" % (n, signal), "",
             "**Evidence:** the agent wrapped the write in `except: pass`."]
    for field, value in (("Rung", rung), ("Ladder", ladder), ("Proof", proof_line),
                         ("Disposition", disposition)):
        if value is not None:
            lines.append("**%s:** %s" % (field, value))
    if body:
        lines.append(body)
    return "\n".join(lines)


def retro_text(*blocks: str, findings_heading: bool = True) -> str:
    parts = ["# Retro: spec x", "", "> Scope: spec 2026-10-30-spec-x", "",
             "## Transcripts", "",
             "- `%s` (story 1, coding agent)" % TRANSCRIPT,
             "- transcripts/run-2.jsonl story 2 review", ""]
    if findings_heading:
        parts += ["## Findings", ""]
        for block in blocks:
            parts += [block, ""]
    parts += ["## Summary", "", "Findings reviewed with the user.", ""]
    return "\n".join(parts)


def row(since: str = "seed", enforcer: str = "`ruff check --select BLE`",
        rung: str = "lint", proof_cell: str = TRANSCRIPT + ": fails",
        rule: str = "No bare except", written: str = "`CLAUDE.md`") -> str:
    return "| %s |" % " | ".join([rule, written, enforcer, rung, proof_cell, since])


def table_text(*rows: str, header: str = HEADER_ROW) -> str:
    return "\n".join(["# Rule-to-Enforcer Table", "", header, DELIMITER_ROW, *rows]) + "\n"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def retro_path(tmp: Path) -> Path:
    return tmp / "retros" / RETRO_NAME


def default_table(tmp: Path) -> Path:
    return tmp / "retros" / "rule-enforcers.md"


def since(n: int) -> str:
    return "%s F%d" % (RETRO_NAME, n)


def run(args: List[str], cwd: Path,
        env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(cwd),
                          capture_output=True, encoding="utf-8", env=env or ENV,
                          timeout=60)


def run_retro(tmp: Path, *blocks: str, rows: Optional[List[str]] = None,
              repo: Optional[Path] = None, extra: Optional[List[str]] = None,
              findings_heading: bool = True) -> subprocess.CompletedProcess:
    """Write the retro file (and, when `rows` is given, the default table
    beside it), then run `--retro`. `--repo` defaults to `tmp`, which is not
    a git work tree, so a run that resolves no SHA never touches git."""
    write(retro_path(tmp), retro_text(*blocks, findings_heading=findings_heading))
    if rows is not None:
        write(default_table(tmp), table_text(*rows))
    return run(["--retro", str(retro_path(tmp)), "--repo", str(repo or tmp), *(extra or [])],
               tmp)


def run_table(tmp: Path, text: str, repo: Optional[Path] = None) -> subprocess.CompletedProcess:
    table = write(tmp / "table.md", text)
    return run(["--table", str(table), "--repo", str(repo or tmp)], tmp)


SUMMARY = re.compile(r"retro-check: (\w+) \((\d+) findings, (\d+) table rows, (\d+) reasons\)")


def assert_result(result: subprocess.CompletedProcess, verdict: str, reasons: List[str],
                  findings: Optional[int] = None, rows: Optional[int] = None) -> None:
    """Line 1 is the verdict, every middle line is one of `reasons` in order,
    the summary counts match, and the exit code follows the verdict."""
    out = result.stdout.splitlines()
    assert out, "no stdout; stderr: %s" % result.stderr
    assert out[0] == verdict, result.stdout + result.stderr
    assert out[1:-1] == ["reason: %s" % r for r in reasons], result.stdout
    match = SUMMARY.fullmatch(out[-1])
    assert match, out[-1]
    assert match.group(1) == verdict
    assert int(match.group(4)) == len(reasons), out[-1]
    if findings is not None:
        assert int(match.group(2)) == findings, out[-1]
    if rows is not None:
        assert int(match.group(3)) == rows, out[-1]
    assert result.returncode == {"pass": 0, "unverifiable": 0, "fail": 1}[verdict], \
        result.stdout + result.stderr
    assert result.stderr == ""


def conforming(tmp: Path, sha: str) -> Tuple[Path, Path]:
    """Four findings (lint applied, docs refreshed, test issue, a non-ladder
    signal with Rung none) and a four-row table that covers them."""
    retro = write(retro_path(tmp), retro_text(
        finding(1, proof_line=proof(sha), disposition="applied"),
        finding(2, signal="User correction", rung="docs", ladder=LADDER_DOCS,
                proof_line=None, disposition="refreshed"),
        finding(3, signal="Repeated mistake", rung="test", ladder=LADDER_TEST,
                proof_line=proof(TRANSCRIPT, "pending", "pytest tests/test_save.py"),
                disposition="issue"),
        finding(4, signal="Dead end", rung="none", ladder=None, proof_line=None,
                disposition="dismissed")))
    table = write(default_table(tmp), table_text(
        row("seed", "`uv run --python 3.9 pytest`", "test", sha + ": fails",
            "The suite runs on Python 3.9"),
        row("seed", "none", "docs", "—", "Instruction files use plain prose",
            "`skills/plain-prose/SKILL.md`"),
        row(since(1), proof_cell=sha[:7] + ": fails"),
        row(since(2), "none", "docs", "—", "Ask before renaming a command")))
    return retro, table


# ---------------------------------------------------------------------------
# AC-1.1 conforming files pass
# ---------------------------------------------------------------------------

def test_conforming_retro_and_table_pass(tmp_path, repo):
    """A conforming retro file and table, explicit `--table`: exact pass output, exit 0. [AC-1.1]"""
    repo_dir, sha = repo
    retro, table = conforming(tmp_path, sha)
    result = run(["--retro", str(retro), "--table", str(table), "--repo", str(repo_dir)],
                 tmp_path)
    assert result.stdout.splitlines() == [
        "pass", "retro-check: pass (4 findings, 4 table rows, 0 reasons)"], result.stderr
    assert result.returncode == 0
    assert result.stderr == ""


def test_default_table_beside_retro_file(tmp_path, repo):
    """`--table` defaults to `rule-enforcers.md` beside the retro file. [AC-1.1]"""
    repo_dir, sha = repo
    retro, _ = conforming(tmp_path, sha)
    result = run(["--retro", str(retro), "--repo", str(repo_dir)], tmp_path)
    assert_result(result, "pass", [], findings=4, rows=4)


def test_default_repo_is_cwd(tmp_path, repo):
    """`--repo` defaults to `.`: run from inside the repository, SHAs resolve. [AC-1.1, AC-1.3]"""
    repo_dir, sha = repo
    retro, _ = conforming(tmp_path, sha)
    assert_result(run(["--retro", str(retro)], repo_dir), "pass", [], findings=4, rows=4)


def test_table_only_run(tmp_path, repo):
    """`--table` alone checks only the table. [AC-1.1, AC-1.4]"""
    repo_dir, sha = repo
    _, table = conforming(tmp_path, sha)
    assert_result(run(["--table", str(table), "--repo", str(repo_dir)], tmp_path),
                  "pass", [], findings=0, rows=4)


def test_empty_findings_section_passes(tmp_path):
    """A `## Findings` heading with no blocks passes; no table is needed. [AC-1.1]"""
    assert_result(run_retro(tmp_path), "pass", [], findings=0, rows=0)


def test_default_table_missing_and_not_needed_passes(tmp_path):
    """No default table and no applied or refreshed ladder finding: pass, nothing read. [AC-1.1, AC-1.4]"""
    result = run_retro(tmp_path, finding(1), finding(2, rung="none", ladder=None,
                                                     proof_line=None, signal="Token sink",
                                                     disposition="applied"))
    assert_result(result, "pass", [], findings=2, rows=0)


def test_semicolon_inside_ladder_reason(tmp_path):
    """A `;` inside a parenthesized reason does not split the Ladder entry. [AC-1.1]"""
    ladder = ("architecture: no (no rule; none exists); "
              "types: no (untyped; plain Python); lint: yes")
    assert_result(run_retro(tmp_path, finding(1, ladder=ladder)), "pass", [])


def test_fenced_code_in_a_finding_is_ignored(tmp_path):
    """Headings and field lines inside a fenced block are not read. [AC-1.1]"""
    body = "```text\n### F9 [Low] Dead end: quoted\n**Rung:** bogus\n```"
    assert_result(run_retro(tmp_path, finding(1, body=body)), "pass", [], findings=1)


def test_list_marker_before_field(tmp_path):
    """A field line may sit in a list item (`- **Rung:** lint`). [AC-1.1]"""
    block = finding(1).replace("**Rung:**", "- **Rung:**").replace(
        "**Disposition:**", "- **Disposition:**")
    assert_result(run_retro(tmp_path, block), "pass", [])


# ---------------------------------------------------------------------------
# AC-1.2 finding-level defects
# ---------------------------------------------------------------------------

FINDING_DEFECTS = [
    ("rung_missing", dict(rung=None), ["rung_missing F1"]),
    ("rung_invalid", dict(rung="lints"), ["rung_invalid F1 lints"]),
    ("rung_none_on_mistake", dict(rung="none", ladder=None, proof_line=None),
     ["rung_none_on_mistake F1"]),
    ("ladder_missing", dict(ladder=None), ["ladder_missing F1"]),
    ("ladder_order_skip", dict(ladder="architecture: no (x); lint: yes"), ["ladder_order F1"]),
    ("ladder_order_start", dict(ladder="types: no (x); architecture: no (y); lint: yes"),
     ["ladder_order F1"]),
    ("ladder_no_reason", dict(ladder="architecture: no (x); types: no; lint: yes"),
     ["ladder_no_reason F1 types"]),
    ("ladder_no_reason_empty", dict(ladder="architecture: no ( ); types: no (y); lint: yes"),
     ["ladder_no_reason F1 architecture"]),
    ("ladder_rung_mismatch_rung", dict(rung="types"), ["ladder_rung_mismatch F1"]),
    ("ladder_rung_mismatch_last_no",
     dict(ladder="architecture: no (x); types: no (y); lint: no (z)"),
     ["ladder_rung_mismatch F1"]),
    ("ladder_rung_mismatch_early_yes",
     dict(ladder="architecture: yes; types: no (y); lint: yes"),
     ["ladder_rung_mismatch F1"]),
    ("proof_missing", dict(proof_line=None), ["proof_missing F1"]),
    ("proof_malformed_shape", dict(proof_line="mistake run-1; check ruff; result fails"),
     ["proof_malformed F1"]),
    ("proof_malformed_result", dict(proof_line=proof(TRANSCRIPT, "failed")),
     ["proof_malformed F1"]),
    ("proof_malformed_ref", dict(proof_line=proof("transcripts/run-1.log")),
     ["proof_malformed F1"]),
    ("proof_ref_unknown_transcript", dict(proof_line=proof("transcripts/run-9.jsonl")),
     ["proof_ref_unknown F1 transcripts/run-9.jsonl"]),
    ("proof_not_failing", dict(proof_line=proof(TRANSCRIPT, "passes"), disposition="applied"),
     ["proof_not_failing F1"]),
    ("proof_not_failing_pending",
     dict(proof_line=proof(TRANSCRIPT, "pending"), disposition="applied"),
     ["proof_not_failing F1"]),
    ("applied_test_rung", dict(rung="test", ladder=LADDER_TEST, disposition="applied"),
     ["applied_test_rung F1"]),
    ("disposition_missing", dict(disposition=None), ["disposition_missing F1"]),
    ("disposition_invalid", dict(disposition="applyed"), ["disposition_invalid F1 applyed"]),
]


@pytest.mark.parametrize("fields,reasons", [d[1:] for d in FINDING_DEFECTS],
                         ids=[d[0] for d in FINDING_DEFECTS])
def test_finding_defect_fails(tmp_path, fields, reasons):
    """One defect per fixture: line 1 `fail`, the reason names the code and finding ID, exit 1. [AC-1.2]"""
    result = run_retro(tmp_path, finding(1, **fields), rows=[row(since(1))])
    assert_result(result, "fail", reasons, findings=1, rows=1)


def test_no_findings_section(tmp_path):
    """A retro file with no `## Findings` heading fails. [AC-1.2]"""
    assert_result(run_retro(tmp_path, findings_heading=False), "fail",
                  ["no_findings_section"], findings=0)


def test_docs_rung_needs_no_proof(tmp_path):
    """A docs-rung finding with no Proof line passes; a malformed one still fails. [AC-1.2]"""
    docs = dict(signal="Stale guidance", rung="docs", ladder=LADDER_DOCS)
    assert_result(run_retro(tmp_path, finding(1, proof_line=None, **docs)), "pass", [])
    assert_result(run_retro(tmp_path, finding(1, proof_line="mistake later", **docs)),
                  "fail", ["proof_malformed F1"])


def test_non_ladder_signal_may_climb_the_ladder(tmp_path):
    """A Dead end finding with a lint rung follows the ladder and proof rules. [AC-1.2]"""
    assert_result(run_retro(tmp_path, finding(1, signal="Dead end")), "pass", [])
    assert_result(run_retro(tmp_path, finding(1, signal="Dead end", proof_line=None)),
                  "fail", ["proof_missing F1"])


def test_reasons_in_file_order(tmp_path):
    """Reasons print in file order: findings first, then table rows. [AC-1.2, AC-1.4]"""
    result = run_retro(tmp_path, finding(1, rung=None), finding(2, disposition=None),
                       rows=[row(proof_cell="—")])
    assert_result(result, "fail", ["rung_missing F1", "disposition_missing F2",
                                   "table_enforcer_without_proof row 1"], findings=2, rows=1)


def test_every_reason_prints(tmp_path):
    """All checks run: one finding with three defects prints all three. [AC-1.2]"""
    result = run_retro(tmp_path, finding(1, ladder=None, proof_line=None, disposition="done"))
    assert_result(result, "fail", ["ladder_missing F1", "proof_missing F1",
                                   "disposition_invalid F1 done"])


def test_control_characters_escaped(tmp_path):
    """A control character in an echoed value prints escaped and adds no line. [AC-1.2]"""
    result = run_retro(tmp_path, finding(1, rung="lint\x1b[31m"))
    assert_result(result, "fail", ["rung_invalid F1 lint\\x1b[31m"])
    missing = str(tmp_path / "x\nreason: pass.md")
    result = run(["--retro", missing], tmp_path)
    assert_result(result, "unverifiable",
                  ["retro_missing %s" % missing.replace("\n", "\\n")])


# ---------------------------------------------------------------------------
# AC-1.3 proof refs, git, and transcripts
# ---------------------------------------------------------------------------

def test_unknown_sha_fails(tmp_path, repo):
    """A Proof SHA not in the `git init` repository fails `proof_ref_unknown`. [AC-1.3]"""
    repo_dir, _ = repo
    result = run_retro(tmp_path, finding(1, proof_line=proof(FAKE_SHA)), repo=repo_dir)
    assert_result(result, "fail", ["proof_ref_unknown F1 %s" % FAKE_SHA])


def test_real_sha_resolves(tmp_path, repo):
    """A full or 7-character SHA of a real commit has no `proof_ref_unknown`. [AC-1.3]"""
    repo_dir, sha = repo
    for ref in (sha, sha[:7]):
        result = run_retro(tmp_path, finding(1, proof_line=proof(ref)), repo=repo_dir)
        assert_result(result, "pass", [])


def test_listed_transcript_resolves(tmp_path):
    """A `.jsonl` ref listed under `## Transcripts` resolves without git; a plain
    list item's first word counts as its path. [AC-1.3]"""
    for ref in (TRANSCRIPT, "transcripts/run-2.jsonl"):
        assert_result(run_retro(tmp_path, finding(1, proof_line=proof(ref))), "pass", [])


def test_no_git_outside_work_tree(tmp_path, repo):
    """`--repo` outside any git work tree: `unverifiable`, one `no_git`, exit 0. [AC-1.3]"""
    _, sha = repo
    retro, table = conforming(tmp_path, sha)
    plain = tmp_path / "plain"
    plain.mkdir()
    env = dict(ENV, GIT_CEILING_DIRECTORIES=str(tmp_path.resolve()))
    result = run(["--retro", str(retro), "--table", str(table), "--repo", str(plain)],
                 tmp_path, env)
    assert_result(result, "unverifiable", ["no_git"], findings=4, rows=4)


def test_no_git_when_git_not_on_path(tmp_path, repo):
    """No `git` on PATH: `unverifiable` with `no_git`, exit 0. [AC-1.3]"""
    repo_dir, sha = repo
    retro, _ = conforming(tmp_path, sha)
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    result = run(["--retro", str(retro), "--repo", str(repo_dir)], tmp_path,
                 dict(ENV, PATH=str(empty_bin)))
    assert_result(result, "unverifiable", ["no_git"], findings=4, rows=4)


def test_no_sha_needs_no_git(tmp_path):
    """Transcript refs only: no git call, so a non-repo `--repo` still passes. [AC-1.3]"""
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    write(retro_path(tmp_path), retro_text(finding(1)))
    result = run(["--retro", str(retro_path(tmp_path)), "--repo", str(tmp_path)], tmp_path,
                 dict(ENV, PATH=str(empty_bin)))
    assert_result(result, "pass", [])


def test_fail_outranks_unverifiable(tmp_path):
    """`no_git` plus a fail reason: verdict `fail`, both reasons print, exit 1. [AC-1.3]"""
    plain = tmp_path / "plain"
    plain.mkdir()
    env = dict(ENV, GIT_CEILING_DIRECTORIES=str(tmp_path.resolve()))
    write(retro_path(tmp_path), retro_text(finding(1, proof_line=proof(FAKE_SHA)),
                                           finding(2, rung=None)))
    result = run(["--retro", str(retro_path(tmp_path)), "--repo", str(plain)], tmp_path, env)
    assert_result(result, "fail", ["no_git", "rung_missing F2"])


def test_retro_missing(tmp_path):
    """A `--retro` path that does not exist: `unverifiable`, `retro_missing`, exit 0. [AC-1.3]"""
    missing = tmp_path / "retros" / "nope.md"
    assert_result(run(["--retro", str(missing)], tmp_path), "unverifiable",
                  ["retro_missing %s" % missing], findings=0, rows=0)


# ---------------------------------------------------------------------------
# AC-1.4 table checks
# ---------------------------------------------------------------------------

TABLE_DEFECTS = [
    ("table_header_cells",
     table_text(row(), header="| Rule | Where | Enforcer | Rung | Proof | Since |"),
     ["table_header"], 1),
    ("table_header_no_table", "# Rule-to-Enforcer Table\n\nNo rows yet.\n", ["table_header"], 0),
    ("table_rung_invalid", table_text(row(rung="none")), ["table_rung_invalid row 1 none"], 1),
    ("table_unenforced_rung_lint", table_text(row(), row(enforcer="none", proof_cell="—")),
     ["table_unenforced_rung row 2"], 2),
    ("table_unenforced_rung_proof", table_text(row(enforcer="none", rung="docs")),
     ["table_unenforced_rung row 1"], 1),
    ("table_enforcer_without_proof_dash", table_text(row(proof_cell="—")),
     ["table_enforcer_without_proof row 1"], 1),
    ("table_enforcer_without_proof_passes", table_text(row(proof_cell=TRANSCRIPT + ": passes")),
     ["table_enforcer_without_proof row 1"], 1),
]


@pytest.mark.parametrize("text,reasons,rows", [d[1:] for d in TABLE_DEFECTS],
                         ids=[d[0] for d in TABLE_DEFECTS])
def test_table_defect_fails(tmp_path, text, reasons, rows):
    """One table defect per fixture: line 1 `fail` with its reason code, exit 1. [AC-1.4]"""
    assert_result(run_table(tmp_path, text), "fail", reasons, findings=0, rows=rows)


def test_table_proof_ref_unknown(tmp_path, repo):
    """A table Proof SHA not in the repository fails `table_proof_ref_unknown`. [AC-1.4]"""
    repo_dir, sha = repo
    text = table_text(row(proof_cell=sha + ": fails"), row(proof_cell=FAKE_SHA + ": fails"))
    assert_result(run_table(tmp_path, text, repo_dir), "fail",
                  ["table_proof_ref_unknown row 2 %s" % FAKE_SHA], rows=2)


def test_explicit_table_missing_is_unverifiable(tmp_path):
    """An explicit `--table` that does not exist: `unverifiable`, `table_missing`, exit 0. [AC-1.4]"""
    missing = tmp_path / "nope.md"
    assert_result(run(["--table", str(missing)], tmp_path), "unverifiable",
                  ["table_missing %s" % missing], rows=0)
    write(retro_path(tmp_path), retro_text(finding(1, disposition="applied")))
    result = run(["--retro", str(retro_path(tmp_path)), "--table", str(missing),
                  "--repo", str(tmp_path)], tmp_path)
    assert_result(result, "unverifiable", ["table_missing %s" % missing], findings=1, rows=0)


def test_default_table_missing_when_needed_fails(tmp_path):
    """No default table and an applied ladder finding needs a row: `fail`, `table_missing`. [AC-1.4]"""
    result = run_retro(tmp_path, finding(1, disposition="applied"))
    assert_result(result, "fail", ["table_missing %s" % default_table(tmp_path)],
                  findings=1, rows=0)


def test_table_row_missing(tmp_path):
    """Applied and refreshed ladder findings need a row whose Since is `<retro file> F<n>`. [AC-1.4]"""
    result = run_retro(
        tmp_path,
        finding(1, disposition="applied"),
        finding(2, disposition="applied"),
        finding(3, signal="Stale guidance", rung="docs", ladder=LADDER_DOCS, proof_line=None,
                disposition="refreshed"),
        rows=[row(since(1)), row("2026-10-01-other.md F2")])
    assert_result(result, "fail", ["table_row_missing F2", "table_row_missing F3"],
                  findings=3, rows=2)


def test_backticked_cells(tmp_path):
    """Backticks around a whole Enforcer, Rung, or Since cell, or around a Proof ref, are code formatting. [AC-1.4]"""
    text = table_text(row(enforcer="`none`", rung="`docs`", proof_cell="—"),
                      row(rung="`lint`", proof_cell="`%s`: fails" % TRANSCRIPT))
    assert_result(run_table(tmp_path, text), "pass", [], rows=2)


# ---------------------------------------------------------------------------
# AC-1.5 usage and read-only
# ---------------------------------------------------------------------------

def test_no_arguments_is_usage_error(tmp_path):
    """No arguments: exit 2, stdout empty, usage on stderr. [AC-1.5]"""
    result = run([], tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stdout == ""
    assert "usage:" in result.stderr


def test_repo_alone_is_usage_error(tmp_path):
    """`--repo` without `--retro` or `--table`: exit 2, stdout empty. [AC-1.5]"""
    result = run(["--repo", str(tmp_path)], tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stdout == ""
    assert "usage:" in result.stderr


def test_bad_flag_is_usage_error(tmp_path):
    """An unknown flag: exit 2, stdout empty, usage on stderr. [AC-1.5]"""
    result = run(["--zz-probe"], tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stdout == ""
    assert "usage:" in result.stderr


def test_help_exits_zero(tmp_path):
    """`--help` exits 0 and names the script and its flags. [AC-1.5]"""
    result = run(["--help"], tmp_path)
    assert result.returncode == 0, result.stderr
    for text in ("retro-check.py", "--retro", "--table", "--repo"):
        assert text in result.stdout


def test_unreadable_retro_is_exit_2(tmp_path):
    """A `--retro` path that exists but cannot be read (a directory): exit 2, stdout empty. [AC-1.5]"""
    folder = tmp_path / "retros"
    folder.mkdir()
    result = run(["--retro", str(folder)], tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stdout == ""
    assert result.stderr.startswith("retro-check: ")


def snapshot(root: Path) -> List[Tuple[str, str]]:
    """Every path under `root` with a SHA-256 of each file's bytes."""
    return sorted((str(p.relative_to(root)),
                   hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "dir")
                  for p in root.rglob("*"))


def test_run_writes_nothing(tmp_path, repo):
    """File names and checksums under the fixture directory, the repository
    included, are identical before and after full runs. [AC-1.5]"""
    repo_dir, sha = repo
    retro, table = conforming(tmp_path, sha)
    write(tmp_path / "bad" / RETRO_NAME, retro_text(finding(1, proof_line=proof(FAKE_SHA),
                                                            disposition="applied")))
    before = snapshot(tmp_path)
    for args in (["--retro", str(retro), "--table", str(table), "--repo", str(repo_dir)],
                 ["--retro", str(retro), "--repo", str(repo_dir)],
                 ["--retro", str(tmp_path / "bad" / RETRO_NAME), "--repo", str(repo_dir)]):
        assert run(args, tmp_path).returncode in (0, 1)
    assert snapshot(tmp_path) == before

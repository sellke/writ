#!/usr/bin/env python3
"""Unit tests for scripts/prune-ledger.py (Story 1 of
2026-09-07-phase11-stage2-prune-the-base).

Every `check` test builds a throwaway git repository holding the two base
files, commits it once (that commit is the fake `--base-commit`), then edits
the working tree and the ledger to produce exactly one finding code. The
module filename contains a hyphen, so it is imported by path.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

MODULE_PATH = Path(__file__).resolve().parent.parent / "prune-ledger.py"
_spec = importlib.util.spec_from_file_location("prune_ledger", MODULE_PATH)
pl = importlib.util.module_from_spec(_spec)
sys.modules["prune_ledger"] = pl
_spec.loader.exec_module(pl)  # type: ignore[union-attr]

_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}

SYSTEM = "system-instructions.md"
PREAMBLE = "commands/_preamble.md"

SYSTEM_TEXT = (
    "# System Instructions\n"
    "\n"
    "## Identity\n"
    "Never claim a test passed that you did not run.\n"
    "Use `git diff` before every commit.\n"
    "\n"
    "---\n"
    "\n"
    "## Hard Constraints\n"
    "Do not push without a person.\n"
    "Prefer a table | with pipes | when comparing.\n"
    "### Sub\n"
    "Shared line.\n"
)
PREAMBLE_TEXT = (
    "# Preamble\n"
    "\n"
    "## Tools\n"
    "Read the spec first.\n"
    "Shared line.\n"
)

HEADER = (
    "# Pruned Instructions Ledger\n"
    "\n"
    "> Append-only.\n"
    "\n"
    "| Date | File | Class | Reason | Text |\n"
    "|---|---|---|---|---|\n"
)


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, env=_GIT_ENV,
    )
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), proc.stderr))
    return proc.stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def row(date: str, file: str, cls: str, reason: str, text: str) -> str:
    return "| %s | %s | %s | %s | %s |\n" % (date, file, cls, reason, pl.escape_pipes(text))


class PruneLedgerFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "commit.gpgsign", "false")
        write(self.repo / SYSTEM, SYSTEM_TEXT)
        write(self.repo / PREAMBLE, PREAMBLE_TEXT)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.ledger = self.repo / pl.LEDGER
        self.base_bytes = len(SYSTEM_TEXT.encode("utf-8")) + len(PREAMBLE_TEXT.encode("utf-8"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, *extra: str, sub: str = "check"):
        argv = [sub, "--repo", str(self.repo)]
        if sub == "check":
            argv += ["--base-commit", self.base]
        argv += list(extra)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                pl.main(argv)
        code = ctx.exception.code
        return (code or 0), out.getvalue(), err.getvalue()

    def remove_line(self, rel: str, text: str) -> None:
        path = self.repo / rel
        lines = path.read_text(encoding="utf-8").split("\n")
        lines.remove(text)
        path.write_text("\n".join(lines), encoding="utf-8")

    def findings(self, out: str) -> list:
        lines = out.rstrip("\n").split("\n")
        return [ln for ln in lines if not ln.startswith("note: ") and not ln.startswith("base: ")]

    def summary(self, out: str) -> str:
        return out.rstrip("\n").split("\n")[-1]


class CheckCleanTests(PruneLedgerFixture):
    def test_empty_ledger_no_removals_exit0_with_note(self) -> None:
        write(self.ledger, HEADER)
        code, out, err = self.run_cli()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.findings(out), [])
        self.assertIn("note: ledger_missing: ", out)
        self.assertEqual(
            self.summary(out),
            "base: %d bytes (cap 10000), ledger: 0 rows, removed: 0, re-added: 0" % self.base_bytes,
        )

    def test_absent_ledger_file_is_note_not_finding(self) -> None:
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertEqual(self.findings(out), [])
        self.assertIn("note: ledger_missing: ", out)
        self.assertIn("ledger: 0 rows", self.summary(out))

    def test_summary_is_always_last_line(self) -> None:
        write(self.ledger, HEADER)
        _, out, _ = self.run_cli("--cap", "10")
        self.assertTrue(self.summary(out).startswith("base: "))
        self.assertTrue(out.endswith("\n"))

    def test_removal_with_matching_row_exit0(self) -> None:
        self.remove_line(SYSTEM, "Use `git diff` before every commit.")
        write(self.ledger, HEADER + row("2026-09-08", SYSTEM, "behavior-request", "models do this", "Use `git diff` before every commit."))
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.findings(out), [])
        self.assertNotIn("ledger_missing", out)
        self.assertIn("ledger: 1 rows, removed: 1, re-added: 0", self.summary(out))


class FindingCodeTests(PruneLedgerFixture):
    def test_removed_not_in_ledger_names_file_and_text(self) -> None:
        self.remove_line(SYSTEM, "Use `git diff` before every commit.")
        write(self.ledger, HEADER)
        code, out, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertEqual(
            self.findings(out),
            ["removed_not_in_ledger: system-instructions.md: Use `git diff` before every commit."],
        )
        self.assertIn("removed: 1", self.summary(out))

    def test_row_for_wrong_file_does_not_satisfy_removal(self) -> None:
        self.remove_line(PREAMBLE, "Read the spec first.")
        write(self.ledger, HEADER + row("2026-09-08", SYSTEM, "duplicate", "elsewhere", "Read the spec first."))
        code, out, _ = self.run_cli()
        self.assertEqual(code, 1)
        codes = [f.split(":")[0] for f in self.findings(out)]
        self.assertIn("removed_not_in_ledger", codes)

    def test_ledger_text_reappeared_names_date_and_file(self) -> None:
        # Row present, line never left (or came back): the text is a whole
        # line in the base file and is not a current removal.
        write(self.ledger, HEADER + row("2026-09-08", PREAMBLE, "behavior-request", "why", "Read the spec first."))
        code, out, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertEqual(
            self.findings(out),
            ["ledger_text_reappeared: 2026-09-08 commands/_preamble.md: Read the spec first."],
        )
        self.assertIn("re-added: 1", self.summary(out))

    def test_over_cap_is_note_without_flag(self) -> None:
        write(self.ledger, HEADER)
        code, out, _ = self.run_cli("--cap", "10")
        self.assertEqual(code, 0)
        self.assertEqual(self.findings(out), [])
        self.assertIn("note: over_cap: %d bytes > cap 10" % self.base_bytes, out)
        self.assertIn("(cap 10)", self.summary(out))

    def test_over_cap_is_finding_with_flag(self) -> None:
        write(self.ledger, HEADER)
        code, out, _ = self.run_cli("--cap", "10", "--cap-blocking")
        self.assertEqual(code, 1)
        self.assertEqual(self.findings(out), ["over_cap: %d bytes > cap 10" % self.base_bytes])

    def test_under_cap_no_note(self) -> None:
        write(self.ledger, HEADER)
        code, out, _ = self.run_cli("--cap", str(self.base_bytes), "--cap-blocking")
        self.assertEqual(code, 0)
        self.assertNotIn("over_cap", out)

    def test_malformed_row_exit1(self) -> None:
        write(self.ledger, HEADER + "| 2026-09-08 | system-instructions.md | typo-class | reason | text |\n")
        code, out, _ = self.run_cli()
        self.assertEqual(code, 1)
        findings = self.findings(out)
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0].startswith("malformed_row: "), findings)
        self.assertIn(":7: ", findings[0])  # line number in the ledger file
        self.assertIn("ledger: 0 rows", self.summary(out))

    def test_marker_line_is_not_a_row(self) -> None:
        write(self.ledger, HEADER + "\n" + pl.CAP_BLOCKING_MARKER + "\n")
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.findings(out), [])


class DiffSemanticsTests(PruneLedgerFixture):
    def test_move_within_file_is_not_a_removal(self) -> None:
        path = self.repo / SYSTEM
        text = path.read_text(encoding="utf-8")
        line = "Do not push without a person.\n"
        text = text.replace(line, "")
        text = text.replace("## Identity\n", "## Identity\n" + line)
        path.write_text(text, encoding="utf-8")
        write(self.ledger, HEADER)
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0, out)
        self.assertIn("removed: 0", self.summary(out))

    def test_move_between_files_is_a_removal(self) -> None:
        self.remove_line(SYSTEM, "Do not push without a person.")
        with (self.repo / PREAMBLE).open("a", encoding="utf-8") as fh:
            fh.write("Do not push without a person.\n")
        write(self.ledger, HEADER)
        code, out, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertEqual(
            self.findings(out),
            ["removed_not_in_ledger: system-instructions.md: Do not push without a person."],
        )

    def test_removed_horizontal_rule_is_a_removal(self) -> None:
        # A removed `---` line renders as `----` in the diff; it must not be
        # mistaken for the `--- a/file` header.
        self.remove_line(SYSTEM, "---")
        write(self.ledger, HEADER)
        code, out, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertEqual(self.findings(out), ["removed_not_in_ledger: system-instructions.md: ---"])

    def test_blank_line_removal_needs_no_row(self) -> None:
        path = self.repo / SYSTEM
        path.write_text(path.read_text(encoding="utf-8").replace("---\n\n", "---\n"), encoding="utf-8")
        write(self.ledger, HEADER)
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0, out)
        self.assertIn("removed: 0", self.summary(out))

    def test_duplicate_line_one_copy_removed_is_not_reappeared(self) -> None:
        # "Shared line." exists in both files; removing the preamble copy with a
        # row must not read as reappeared because the system copy still exists
        # in *its* file — rows are matched per file.
        self.remove_line(PREAMBLE, "Shared line.")
        write(self.ledger, HEADER + row("2026-09-08", PREAMBLE, "duplicate", "system-instructions.md", "Shared line."))
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0, out)

    def test_same_file_duplicate_one_copy_removed_is_not_reappeared(self) -> None:
        path = self.repo / SYSTEM
        path.write_text(path.read_text(encoding="utf-8") + "Shared line.\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "dup")
        self.base = git(self.repo, "rev-parse", "HEAD")
        # Remove one of the two identical lines; the other stays.
        text = path.read_text(encoding="utf-8")
        text = text[: text.rfind("Shared line.\n")]
        path.write_text(text, encoding="utf-8")
        write(self.ledger, HEADER + row("2026-09-08", SYSTEM, "duplicate", "kept copy above", "Shared line."))
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0, out)
        self.assertIn("removed: 1, re-added: 0", self.summary(out))

    def test_no_whitespace_normalization(self) -> None:
        path = self.repo / SYSTEM
        path.write_text(
            path.read_text(encoding="utf-8").replace("Read the spec first.", "Read the spec first. ")
            .replace("Do not push without a person.", "Do not push  without a person."),
            encoding="utf-8",
        )
        # The row's text differs from the removed line only by whitespace and
        # a trailing period; neither may be normalized into a match.
        write(self.ledger, HEADER + row("2026-09-08", SYSTEM, "behavior-request", "x", "Do not push  without a person"))
        code, out, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertEqual(self.findings(out), ["removed_not_in_ledger: system-instructions.md: Do not push without a person."])
        self.assertIn("removed: 1", self.summary(out))


class PipeEscapeTests(PruneLedgerFixture):
    def test_escape_unescape_round_trip(self) -> None:
        text = "Prefer a table | with pipes | when comparing."
        escaped = pl.escape_pipes(text)
        self.assertEqual(escaped, "Prefer a table \\| with pipes \\| when comparing.")
        self.assertEqual(pl.unescape_pipes(escaped), text)
        self.assertEqual(pl.unescape_pipes(pl.escape_pipes("no pipes")), "no pipes")

    def test_row_with_pipes_matches_removed_line(self) -> None:
        text = "Prefer a table | with pipes | when comparing."
        self.remove_line(SYSTEM, text)
        write(self.ledger, HEADER + row("2026-09-08", SYSTEM, "behavior-request", "style", text))
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0, out)
        self.assertIn("ledger: 1 rows, removed: 1", self.summary(out))

    def test_parse_ledger_unescapes_text_column(self) -> None:
        rows, findings = pl.parse_ledger(HEADER + row("2026-09-08", SYSTEM, "moved", "a.md", "x | y"))
        self.assertEqual(findings, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].text, "x | y")
        self.assertEqual(rows[0].file, SYSTEM)
        self.assertEqual(rows[0].cls, "moved")
        self.assertEqual(rows[0].date, "2026-09-08")


class ExitCodeTests(PruneLedgerFixture):
    def test_bad_base_commit_exit2_with_git_stderr(self) -> None:
        write(self.ledger, HEADER)
        argv = ["check", "--repo", str(self.repo), "--base-commit", "deadbeef0"]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                pl.main(argv)
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(out.getvalue(), "")  # no findings fabricated
        self.assertIn("fatal:", err.getvalue())
        self.assertIn("deadbeef0", err.getvalue())

    def test_repo_not_a_directory_exit2(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                pl.main(["check", "--repo", str(self.repo / "nope")])
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("check: error:", err.getvalue())

    def test_missing_base_file_exit2(self) -> None:
        (self.repo / PREAMBLE).unlink()
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                pl.main(["check", "--repo", str(self.repo), "--base-commit", self.base])
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn(PREAMBLE, err.getvalue())

    def test_stdlib_only(self) -> None:
        import ast
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        allowed = {"argparse", "collections", "dataclasses", "os", "re", "subprocess", "sys", "typing", "__future__", "pathlib"}
        self.assertTrue(names <= allowed, names - allowed)


class ParseDiffTests(unittest.TestCase):
    def test_parse_diff_skips_headers_and_no_newline_marker(self) -> None:
        diff = (
            "diff --git a/f.md b/f.md\n"
            "index 1..2 100644\n"
            "--- a/f.md\n"
            "+++ b/f.md\n"
            "@@ -3,2 +3,1 @@\n"
            "-gone\n"
            "----\n"
            "+added\n"
            "\\ No newline at end of file\n"
        )
        removed, added = pl.parse_diff(diff)
        self.assertEqual(dict(removed), {"gone": 1, "---": 1})
        self.assertEqual(dict(added), {"added": 1})

    def test_parse_diff_empty(self) -> None:
        removed, added = pl.parse_diff("")
        self.assertEqual(dict(removed), {})
        self.assertEqual(dict(added), {})


class MeasureTests(PruneLedgerFixture):
    def test_measure_prints_bytes_per_section(self) -> None:
        code, out, _ = self.run_cli(sub="measure")
        self.assertEqual(code, 0)
        self.assertIn("system-instructions.md", out)
        self.assertIn("commands/_preamble.md", out)
        self.assertIn("## Identity", out)
        self.assertIn("### Sub", out)
        self.assertIn("## Tools", out)
        self.assertTrue(out.rstrip("\n").endswith("total: %d bytes" % self.base_bytes), out)
        ident = len("## Identity\nNever claim a test passed that you did not run.\nUse `git diff` before every commit.\n\n---\n\n".encode("utf-8"))
        self.assertIn("%6d  ## Identity" % ident, out)

    def test_measure_sections_sum_to_file_bytes(self) -> None:
        sections = pl.measure_sections(SYSTEM_TEXT)
        self.assertEqual(sum(b for _, b in sections), len(SYSTEM_TEXT.encode("utf-8")))
        self.assertEqual(sections[0][0], "(before first heading)")

    def test_measure_missing_file_exit2(self) -> None:
        (self.repo / SYSTEM).unlink()
        code, _, err = self.run_cli(sub="measure")
        self.assertEqual(code, 2)
        self.assertIn("measure: error:", err)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for `scripts/eval-command-structure.py` and eval.sh's `command-structure` check.

Spec `2026-10-20-shipped-command-hygiene`, Story 2. Some literal pins on
command files guarded structure, not wording: a heading, a frontmatter key, or
a script call. A literal substring pin passes when the heading turns into
prose or the call turns into a bare mention. The helper checks the structure
instead, one table row per converted pin. Tests run the helper against temp
roots through `--root`; the eval-level test copies `eval.sh`, the helper, and
`commands/` into a temp tree the way `test_eval_shipped_refs.py` does.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts" / "eval-command-structure.py"
EVAL_SH = REPO_ROOT / "scripts" / "eval.sh"
KINDS = ("heading", "frontmatter", "invocation")


def load_helper_module():
    spec = importlib.util.spec_from_file_location("eval_command_structure", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_helper(root: Path) -> Tuple[int, List[List[str]]]:
    proc = subprocess.run(
        [sys.executable, str(HELPER), "--root", str(root)],
        capture_output=True, text=True, check=False)
    rows = [line.split("\t") for line in proc.stdout.splitlines() if line]
    return proc.returncode, rows


def run_with_rows(module, rows, files: Dict[str, str]) -> Tuple[int, List[List[str]]]:
    """Run the helper's main() against a temp root holding `files`, with its
    table replaced by `rows`."""
    saved = module.ROWS
    module.ROWS = tuple(rows)
    out = io.StringIO()
    try:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "commands").mkdir()
            for rel, text in files.items():
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text(text, encoding="utf-8")
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = module.main(["--root", str(root)])
    finally:
        module.ROWS = saved
    return code, [line.split("\t") for line in out.getvalue().splitlines() if line]


def row_name(row) -> str:
    return f"command-structure:{row.file}:{row.kind}:{row.value}"


def verdict(rows: List[List[str]], name: str) -> str:
    found = [r[0] for r in rows if len(r) > 1 and r[1] == name]
    if len(found) != 1:
        raise AssertionError(f"expected one line named {name!r}, got {found} in {rows}")
    return found[0]


class KindCase(unittest.TestCase):
    """Shared helpers: one synthetic row checked against one synthetic file."""

    module = None

    @classmethod
    def setUpClass(cls):
        cls.module = load_helper_module()

    def check(self, kind: str, value: str, text: str) -> str:
        row = self.module.Row("commands/x.md", kind, value, "check_synthetic", "synthetic row")
        _, rows = run_with_rows(self.module, [row], {"commands/x.md": text})
        return verdict(rows, row_name(row))


class HeadingKindTests(KindCase):
    """AC-2.3: a heading row passes on a heading and fails on prose or fenced text."""

    def test_passes_when_heading_text_begins_with_the_value(self):
        text = "# Title\n\n## User Challenge (Scope-Degradation Escalation)\n\nBody.\n"
        self.assertEqual(self.check("heading", "User Challenge", text), "PASS")

    def test_passes_at_any_heading_level(self):
        text = "#### Step 1.1b: Dirty-Tree Guard\n"
        self.assertEqual(self.check("heading", "Step 1.1b: Dirty-Tree Guard", text), "PASS")

    def test_fails_when_the_text_survives_only_as_prose(self):
        text = "# Title\n\nUser Challenge (Scope-Degradation Escalation) is defined here.\n"
        self.assertEqual(self.check("heading", "User Challenge", text), "FAIL")

    def test_fails_when_the_heading_is_inside_a_fenced_block(self):
        for fence in ("```", "~~~", "   ```markdown"):
            close = fence.strip()[:3]
            text = f"# Title\n\n{fence}\n## User Challenge\n{close}\n"
            with self.subTest(fence=fence):
                self.assertEqual(self.check("heading", "User Challenge", text), "FAIL")

    def test_a_heading_after_a_closed_fence_still_counts(self):
        text = "```bash\necho hi\n```\n\n## User Challenge\n"
        self.assertEqual(self.check("heading", "User Challenge", text), "PASS")

    def test_fails_when_the_heading_text_does_not_begin_with_the_value(self):
        for line in ("## The User Challenge", "##User Challenge", "####### User Challenge"):
            with self.subTest(line=line):
                self.assertEqual(self.check("heading", "User Challenge", line + "\n"), "FAIL")


class FrontmatterKindTests(KindCase):
    """AC-2.3: a frontmatter row fails when the key is renamed or only in the body."""

    TEXT = "---\nname: x\nloop:\n  unit: spec\n---\n\n# Body\n"

    def test_passes_on_a_top_level_key(self):
        self.assertEqual(self.check("frontmatter", "loop", self.TEXT), "PASS")
        self.assertEqual(self.check("frontmatter", "name", self.TEXT), "PASS")

    def test_fails_when_the_key_is_renamed(self):
        renamed = self.TEXT.replace("loop:", "loops:")
        self.assertEqual(self.check("frontmatter", "loop", renamed), "FAIL")

    def test_fails_when_the_key_appears_only_in_the_body(self):
        text = "---\nname: x\n---\n\nloop: 3\n"
        self.assertEqual(self.check("frontmatter", "loop", text), "FAIL")

    def test_fails_when_the_key_is_nested(self):
        self.assertEqual(self.check("frontmatter", "unit", self.TEXT), "FAIL")

    def test_fails_without_a_frontmatter_block(self):
        self.assertEqual(self.check("frontmatter", "loop", "# Title\nloop: 3\n"), "FAIL")

    def test_fails_when_the_block_never_closes(self):
        self.assertEqual(self.check("frontmatter", "loop", "---\nloop: 3\n# Body\n"), "FAIL")


class InvocationKindTests(KindCase):
    """AC-2.3: an invocation row passes on a call and fails on a bare mention."""

    def test_passes_on_a_call_with_or_without_an_interpreter(self):
        for line in ("python3 scripts/x.py check", "bash scripts/x.py check --spec a",
                     "`scripts/x.py check --spec <folder>`", "  Run scripts/x.py check"):
            with self.subTest(line=line):
                self.assertEqual(self.check("invocation", "scripts/x.py check", line + "\n"),
                                 "PASS")

    def test_a_path_only_value_needs_a_subcommand_or_flag_after_it(self):
        for line, want in (("python3 scripts/x.py check", "PASS"),
                           ("python3 scripts/x.py --dry-run", "PASS"),
                           ("`scripts/x.py`", "FAIL"),
                           ("See scripts/x.py.", "FAIL"),
                           ("scripts/x.py", "FAIL")):
            with self.subTest(line=line):
                self.assertEqual(self.check("invocation", "scripts/x.py", line + "\n"), want)

    def test_fails_on_a_bare_mention(self):
        for line in ("x.py", "the `x.py` helper", "`scripts/x.py`",
                     "scripts/x.py is the executable reference"):
            with self.subTest(line=line):
                self.assertEqual(self.check("invocation", "scripts/x.py check", line + "\n"),
                                 "FAIL")

    def test_the_value_must_stand_alone_on_both_sides(self):
        for line in ("python3 scripts/x.py checker", "python3 myscripts/x.py check",
                     "python3 scripts/x.pyc check"):
            with self.subTest(line=line):
                self.assertEqual(self.check("invocation", "scripts/x.py check", line + "\n"),
                                 "FAIL")


class OutputTests(KindCase):
    """PASS/FAIL TSV, a FAIL that names the row, exit codes."""

    def test_a_fail_line_names_file_kind_value_and_message(self):
        row = self.module.Row("commands/x.md", "heading", "User Challenge", "check_phase_challenges",
                              "x.md must keep the User Challenge heading.")
        code, rows = run_with_rows(self.module, [row], {"commands/x.md": "User Challenge\n"})
        fail = [r for r in rows if r[0] == "FAIL"]
        self.assertEqual(len(fail), 1, rows)
        self.assertEqual(fail[0][1], "command-structure:commands/x.md:heading:User Challenge")
        self.assertIn("x.md must keep the User Challenge heading.", fail[0][2])
        self.assertIn("check_phase_challenges", fail[0][2])
        self.assertEqual(code, 1)

    def test_a_missing_target_file_fails_its_row(self):
        row = self.module.Row("commands/gone.md", "heading", "X", "check_synthetic", "m")
        code, rows = run_with_rows(self.module, [row], {})
        self.assertEqual(verdict(rows, row_name(row)), "FAIL")
        self.assertEqual(code, 1)

    def test_all_rows_passing_exits_zero_after_one_self_test_per_kind(self):
        row = self.module.Row("commands/x.md", "heading", "X", "check_synthetic", "m")
        code, rows = run_with_rows(self.module, [row], {"commands/x.md": "## X\n"})
        self.assertEqual(code, 0)
        names = [r[1] for r in rows]
        self.assertEqual(names[:len(KINDS)], [f"command-structure-kind-{k}" for k in KINDS])
        self.assertEqual([r[0] for r in rows], ["PASS"] * len(rows))

    def test_missing_commands_directory_is_a_run_error_not_a_pass(self):
        with TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, str(HELPER), "--root", tmp],
                                  capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("no commands/ directory", proc.stderr)


class SelfTestTests(unittest.TestCase):
    """A matcher that passes everything or nothing must fail its own scenario."""

    def test_a_broken_matcher_fails_its_own_kind_only(self):
        module = load_helper_module()
        for kind in KINDS:
            for broken in (lambda text, value: True, lambda text, value: False):
                with self.subTest(kind=kind, broken=broken(None, None)):
                    saved = dict(module.MATCHERS)
                    try:
                        module.MATCHERS[kind] = broken
                        results = {name: ok for name, ok, _ in module.self_test()}
                    finally:
                        module.MATCHERS.clear()
                        module.MATCHERS.update(saved)
                    self.assertFalse(results[f"command-structure-kind-{kind}"])
                    others = [k for k in KINDS if k != kind]
                    self.assertTrue(all(results[f"command-structure-kind-{k}"] for k in others))


def mutate(row, text: str) -> str:
    """Break exactly the structure `row` checks, leaving its words in the file."""
    if row.kind == "heading":
        # Demote every heading whose text begins with the value to plain prose.
        pattern = re.compile(r"^#{1,6} (?=%s)" % re.escape(row.value), re.MULTILINE)
        return pattern.sub("", text)
    if row.kind == "frontmatter":
        return re.sub(r"^%s:" % re.escape(row.value), row.value + "_renamed:", text,
                      flags=re.MULTILINE)
    # invocation: every call reduced to a bare mention of the script's file name.
    script = row.value.split()[0].rsplit("/", 1)[-1]
    return text.replace(row.value, script)


class TableTests(unittest.TestCase):
    """AC-2.3: every row passes on a copy of its real target and fails, naming
    itself, when its own structure is broken."""

    @classmethod
    def setUpClass(cls):
        cls.module = load_helper_module()

    def test_the_table_holds_the_converted_pins(self):
        self.assertGreater(len(self.module.ROWS), 0)

    def test_every_row_is_well_formed_and_unique(self):
        seen = set()
        for row in self.module.ROWS:
            with self.subTest(row=row_name(row)):
                self.assertIn(row.kind, KINDS)
                self.assertTrue(row.file.startswith("commands/") and row.file.endswith(".md"))
                self.assertRegex(row.was, r"^check_[a-z_]+$")
                self.assertTrue(row.value.strip() and row.message.strip())
                if row.kind == "invocation":
                    self.assertRegex(row.value, r"^scripts/[\w.-]+\.(py|sh)\b")
                key = (row.file, row.kind, row.value)
                self.assertNotIn(key, seen)
                seen.add(key)

    def test_each_row_passes_on_its_real_target_and_fails_on_its_mutation(self):
        for row in self.module.ROWS:
            with self.subTest(row=row_name(row)):
                original = (REPO_ROOT / row.file).read_text(encoding="utf-8")
                broken = mutate(row, original)
                self.assertNotEqual(broken, original, "the mutation must change the file")
                with TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    target = root / row.file
                    target.parent.mkdir(parents=True)
                    target.write_text(original, encoding="utf-8")
                    _, rows = run_helper(root)
                    self.assertEqual(verdict(rows, row_name(row)), "PASS")
                    target.write_text(broken, encoding="utf-8")
                    _, rows = run_helper(root)
                    self.assertEqual(verdict(rows, row_name(row)), "FAIL")


class RealTreeTests(unittest.TestCase):
    """The shipped commands carry every structure the table names."""

    def test_real_tree_passes(self):
        code, rows = run_helper(REPO_ROOT)
        self.assertEqual([r for r in rows if r[0] == "FAIL"], [])
        self.assertEqual(code, 0)


def run_eval(root: Path) -> Tuple[int, str]:
    report = root / "report.md"
    proc = subprocess.run(
        ["bash", str(root / "scripts" / "eval.sh"), "--check=command-structure",
         f"--report={report}"],
        capture_output=True, text=True, check=False)
    return proc.returncode, report.read_text(encoding="utf-8") if report.exists() else ""


class EvalWiringTests(unittest.TestCase):
    """The check passes on the tree, bites on a demoted heading, and errors
    without its helper."""

    def test_check_passes_bites_and_errors_without_the_helper(self):
        module = load_helper_module()
        row = next(r for r in module.ROWS if r.kind == "heading")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            shutil.copy(EVAL_SH, root / "scripts" / "eval.sh")
            shutil.copy(HELPER, root / "scripts" / "eval-command-structure.py")
            shutil.copytree(REPO_ROOT / "commands", root / "commands")

            code, report = run_eval(root)
            self.assertEqual(code, 0, report)
            self.assertIn("Scenarios:", report)

            target = root / row.file
            target.write_text(mutate(row, target.read_text(encoding="utf-8")), encoding="utf-8")
            code, report = run_eval(root)
            self.assertEqual(code, 1, report)
            self.assertIn(row_name(row), report)
            self.assertIn(row.message, report)

            (root / "scripts" / "eval-command-structure.py").unlink()
            code, report = run_eval(root)
            self.assertEqual(code, 2, report)
            self.assertIn("scripts/eval-command-structure.py", report)

    def test_command_structure_is_registered_right_after_shipped_refs(self):
        text = EVAL_SH.read_text(encoding="utf-8")
        block = text[text.index("CHECKS=(\n"):]
        block = block[:block.index("\n)\n")]
        names = [line.strip() for line in block.splitlines()[1:]]
        self.assertEqual(names[names.index("shipped-refs") + 1], "command-structure")


if __name__ == "__main__":
    unittest.main()

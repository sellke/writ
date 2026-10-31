#!/usr/bin/env python3
"""Tests for `scripts/eval-size-pins.py` and eval.sh's `size-pins` check.

Retro `.writ/retros/2026-10-30-phase-15.md` F9: byte caps on `commands/*.md`
spread across per-spec test modules (IMPLEMENT_STORY_CAP in
test_review_route_rigor.py), and three lanes tripped one they were never
told about. The rule: a command file's size cap lives only in
KNOWN_OVER_BUDGET in `scripts/tests/test_governor_enforcement.py`. The
helper flags a size comparison on a command file in any other test module;
eval.sh turns each `reason:` line into a finding. Fixtures are written into
temp roots; the pins below are string data, so this file pins nothing.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts" / "eval-size-pins.py"
EVAL_SH = REPO_ROOT / "scripts" / "eval.sh"
REGISTRY = "test_governor_enforcement.py"

HEADER = (
    "from pathlib import Path\n"
    "import unittest\n"
    "REPO_ROOT = Path(__file__).resolve().parents[2]\n"
)

# name -> (source, line of the pin, command the pin names)
PINNED: Dict[str, Tuple[str, int, str]] = {
    "test_named_cap.py": (HEADER + (
        'IMPLEMENT_STORY = REPO_ROOT / "commands" / "implement-story.md"\n'
        "IMPLEMENT_STORY_CAP = 40682\n"
        "class T(unittest.TestCase):\n"
        "    def test_cap(self):\n"
        "        size = len(IMPLEMENT_STORY.read_bytes())\n"
        "        self.assertLessEqual(size, IMPLEMENT_STORY_CAP)\n"), 9, "commands/implement-story.md"),
    "test_inline_cap.py": (HEADER + (
        'COMMANDS = REPO_ROOT / "commands"\n'
        "class T(unittest.TestCase):\n"
        "    def test_cap(self):\n"
        '        self.assertLessEqual(len((COMMANDS / "verify-spec.md").read_bytes()), 35858)\n'),
        7, "commands/verify-spec.md"),
    "test_helper_cap.py": (HEADER + (
        'SHIP = "commands/ship.md"\n'
        "class T(unittest.TestCase):\n"
        "    def size(self, rel):\n"
        "        return len((REPO_ROOT / rel).read_bytes())\n"
        "    def test_cap(self):\n"
        "        self.assertLessEqual(self.size(SHIP), 28990)\n"), 9, "commands/ship.md"),
    "test_rel_cap.py": (HEADER + (
        'COMMAND_REL = "commands/why.md"\n'
        "COMMAND = REPO_ROOT / COMMAND_REL\n"
        "def test_budget():\n"
        "    assert len(COMMAND.read_bytes()) < 24960\n"), 7, "commands/why.md"),
    "test_stat_cap.py": (HEADER + (
        "def test_budget():\n"
        '    assert 30000 >= (REPO_ROOT / "commands" / "status.md").stat().st_size\n'),
        5, "commands/status.md"),
    "test_shell_cap.sh": (
        "#!/usr/bin/env bash\n"
        'REPO="$(cd "$(dirname "$0")/../.." && pwd)"\n'
        'CMD="$REPO/commands/create-uat-plan.md"\n'
        "size=\"$(wc -c < \"$CMD\" | tr -d ' ')\"\n"
        '[ "$size" -lt 24960 ] || exit 1\n', 5, "commands/create-uat-plan.md"),
}

CLEAN: Dict[str, str] = {
    # The registry may pin; it is the one place caps live.
    REGISTRY: PINNED["test_named_cap.py"][0],
    "test_hash.py": HEADER + (
        "import hashlib\n"
        'CMD = REPO_ROOT / "commands" / "retro.md"\n'
        "def test_hash():\n"
        "    assert hashlib.sha256(CMD.read_bytes()).hexdigest()\n"),
    "test_equal.py": HEADER + (
        "class T(unittest.TestCase):\n"
        "    def size(self, rel):\n"
        "        return len((REPO_ROOT / rel).read_bytes())\n"
        "    def test_registry_matches(self):\n"
        '        self.assertEqual(15717, self.size("commands/implement-story.md") - 24960)\n'),
    "test_floor.py": HEADER + (
        "def test_not_empty():\n"
        '    assert len((REPO_ROOT / "commands" / "ship.md").read_bytes()) > 0\n'),
    "test_other_file.py": HEADER + (
        "def test_agents_md():\n"
        '    assert len((REPO_ROOT / "codex" / "AGENTS.md").read_bytes()) < 16384\n'),
    "test_report_text.py": HEADER + (
        "def test_report():\n"
        '    size = (REPO_ROOT / "commands" / "retro.md").stat().st_size\n'
        '    assert f"{size} bytes" in "x"\n'),
    "test_shell_other.sh": (
        "#!/usr/bin/env bash\n"
        'size="$(wc -c < "$REPO/README.md")"\n'
        '[ "$size" -lt 99999 ] || exit 1\n'),
}


def make_root(tmp: str, files: Dict[str, str]) -> Path:
    root = Path(tmp)
    tests = root / "scripts" / "tests"
    (tests / "fixtures").mkdir(parents=True)
    for name, source in files.items():
        (tests / name).write_text(source, encoding="utf-8")
    return root


def run_helper(root: Path) -> Tuple[int, List[str], str]:
    proc = subprocess.run([sys.executable, str(HELPER), "--root", str(root)],
                          capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout.splitlines(), proc.stderr


def reasons(lines: List[str]) -> List[str]:
    return [line[len("reason: "):] for line in lines if line.startswith("reason: ")]


class HelperTests(unittest.TestCase):

    def test_each_pin_form_is_one_reason_at_its_line(self):
        for name, (source, line, command) in PINNED.items():
            with self.subTest(file=name), TemporaryDirectory() as tmp:
                code, lines, _ = run_helper(make_root(tmp, {name: source}))
                self.assertEqual(code, 1, lines)
                self.assertEqual(lines[0], "fail")
                got = reasons(lines)
                self.assertEqual(len(got), 1, got)
                self.assertTrue(got[0].startswith("scripts/tests/%s:%d pins a byte cap on %s; "
                                                  % (name, line, command)), got[0])
                self.assertIn("KNOWN_OVER_BUDGET", got[0])
                self.assertEqual(lines[-1], "size-pins: fail (1 pin in 1 file, 1 test file scanned)")

    def test_registry_hashes_equality_floors_and_other_files_pass(self):
        with TemporaryDirectory() as tmp:
            code, lines, _ = run_helper(make_root(tmp, CLEAN))
        self.assertEqual((code, lines),
                         (0, ["pass", "size-pins: pass (0 pins, %d test files scanned)"
                              % (len(CLEAN) - 1)]))

    def test_fixture_directory_is_not_scanned(self):
        with TemporaryDirectory() as tmp:
            root = make_root(tmp, {})
            source = PINNED["test_named_cap.py"][0]
            (root / "scripts" / "tests" / "fixtures" / "test_named_cap.py").write_text(source)
            code, lines, _ = run_helper(root)
        self.assertEqual(code, 0, lines)

    def test_counts_every_pin_across_files(self):
        files = {name: source for name, (source, _, _) in PINNED.items()}
        files.update(CLEAN)
        with TemporaryDirectory() as tmp:
            code, lines, _ = run_helper(make_root(tmp, files))
        self.assertEqual(code, 1)
        self.assertEqual(len(reasons(lines)), len(PINNED))
        self.assertEqual(lines[-1], "size-pins: fail (%d pins in %d files, %d test files scanned)"
                         % (len(PINNED), len(PINNED), len(files) - 1))
        self.assertEqual(lines[1:-1], ["reason: " + r for r in reasons(lines)])

    def test_unparsable_module_is_unverifiable_not_pass(self):
        with TemporaryDirectory() as tmp:
            code, lines, _ = run_helper(make_root(tmp, {"test_broken.py": "def x(:\n"}))
        self.assertEqual(code, 0)
        self.assertEqual(lines[0], "unverifiable")
        self.assertTrue(reasons(lines)[0].startswith("scripts/tests/test_broken.py:1 cannot be parsed"))

    def test_missing_tests_dir_is_a_usage_error(self):
        with TemporaryDirectory() as tmp:
            code, lines, err = run_helper(Path(tmp))
        self.assertEqual((code, lines), (2, []))
        self.assertIn("scripts/tests", err)

    def test_real_tree_has_no_pin_outside_the_registry(self):
        code, lines, _ = run_helper(REPO_ROOT)
        self.assertEqual(code, 0, "\n".join(lines))
        self.assertEqual(lines[0], "pass", "\n".join(lines))


def run_eval(root: Path) -> Tuple[int, str]:
    report = root / "eval-report.md"
    proc = subprocess.run(["bash", "scripts/eval.sh", "--check=size-pins",
                           "--report=%s" % report], cwd=str(root),
                          capture_output=True, text=True, check=False)
    text = report.read_text(encoding="utf-8") if report.exists() else proc.stderr
    return proc.returncode, text


def eval_root(tmp: str, files: Dict[str, str], helper: bool = True) -> Path:
    root = make_root(tmp, files)
    shutil.copy(EVAL_SH, root / "scripts" / "eval.sh")
    if helper:
        shutil.copy(HELPER, root / "scripts" / "eval-size-pins.py")
    return root


class EvalCheckTests(unittest.TestCase):

    def test_registered_in_checks(self):
        text = EVAL_SH.read_text(encoding="utf-8")
        block = text[text.index("CHECKS=(\n"):]
        block = block[:block.index("\n)\n")]
        self.assertIn("size-pins", [line.strip() for line in block.splitlines()[1:]])

    def test_a_pin_is_a_finding_at_its_path_and_line(self):
        source, line, command = PINNED["test_named_cap.py"]
        with TemporaryDirectory() as tmp:
            code, report = run_eval(eval_root(tmp, {"test_named_cap.py": source}))
        self.assertEqual(code, 1, report)
        self.assertIn("## size-pins\n\nFAIL (1 finding(s))", report)
        self.assertIn("- `scripts/tests/test_named_cap.py:%d`: pins a byte cap on %s;"
                      % (line, command), report)
        self.assertIn("_Remediation:_ Delete the pin", report)

    def test_clean_tree_passes_with_the_summary_as_a_note(self):
        with TemporaryDirectory() as tmp:
            code, report = run_eval(eval_root(tmp, CLEAN))
        self.assertEqual(code, 0, report)
        self.assertIn("## size-pins\n\nPASS", report)
        self.assertIn("NOTE [size-pins]: size-pins: pass (0 pins", report)

    def test_missing_helper_is_a_run_error(self):
        with TemporaryDirectory() as tmp:
            code, report = run_eval(eval_root(tmp, CLEAN, helper=False))
        self.assertEqual(code, 2, report)
        self.assertIn("size-pins helper is missing", report)

    def test_helper_usage_error_is_a_run_error(self):
        with TemporaryDirectory() as tmp:
            root = eval_root(tmp, {})
            shutil.rmtree(root / "scripts" / "tests")
            code, report = run_eval(root)
        self.assertEqual(code, 2, report)
        self.assertIn("size-pins helper failed to run (exit 2)", report)


if __name__ == "__main__":
    unittest.main()

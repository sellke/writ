#!/usr/bin/env python3
"""Tests for `scripts/eval-command-structure.py` and eval.sh's `command-structure` check.

Spec `2026-10-20-shipped-command-hygiene`, Story 2. Some literal pins on
command files guarded structure, not wording: a heading, a frontmatter key, or
a script call. The `precondition` kind came later, for create-spec's
show-the-contract-before-the-lock rule (bug 2026-10-22). A literal substring pin passes when the heading turns into
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
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts" / "eval-command-structure.py"
EVAL_SH = REPO_ROOT / "scripts" / "eval.sh"
KINDS = ("heading", "frontmatter", "invocation", "precondition")


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

    def test_a_value_without_a_subcommand_never_passes(self):
        """A path-only value cannot tell a call from a mention, so it never passes."""
        for line in ("python3 scripts/x.py check", "python3 scripts/x.py --dry-run",
                     "`scripts/x.py`", "See scripts/x.py for details", "scripts/x.py"):
            with self.subTest(line=line):
                self.assertEqual(self.check("invocation", "scripts/x.py", line + "\n"), "FAIL")

    def test_fails_on_a_bare_mention(self):
        for line in ("x.py", "the `x.py` helper", "`scripts/x.py`",
                     "scripts/x.py is the executable reference",
                     "See scripts/x.py for details",
                     'calibrated_against: "scripts/x.py cmd_classify (retries only once)"'):
            with self.subTest(line=line):
                self.assertEqual(self.check("invocation", "scripts/x.py check", line + "\n"),
                                 "FAIL")

    def test_the_value_must_stand_alone_on_both_sides(self):
        for line in ("python3 scripts/x.py checker", "python3 myscripts/x.py check",
                     "python3 scripts/x.pyc check"):
            with self.subTest(line=line):
                self.assertEqual(self.check("invocation", "scripts/x.py check", line + "\n"),
                                 "FAIL")


class PreconditionKindTests(KindCase):
    """A precondition row passes when each matching step opens with a
    **Precondition:** paragraph and fails when the prompt comes first."""

    STEP = "#### Step 1.4b: Contract Decision\n\n"
    RULE = "**Precondition:** the contract is shown.\n\n"
    PROMPT = "```\nAskQuestion({ title: \"Contract Decision\" })\n```\n\n"

    def test_passes_when_the_precondition_opens_the_step(self):
        text = self.STEP + self.RULE + self.PROMPT + "## Next\n"
        self.assertEqual(self.check("precondition", "Step 1.4b", text), "PASS")

    def test_fails_when_the_prompt_comes_before_the_precondition(self):
        text = self.STEP + self.PROMPT + self.RULE
        self.assertEqual(self.check("precondition", "Step 1.4b", text), "FAIL")

    def test_fails_when_the_label_is_prose_or_the_step_is_gone(self):
        for text in (self.STEP + "Precondition: the contract is shown.\n",
                     self.STEP + "The contract must be shown.\n\n" + self.RULE,
                     "Step 1.4b: Contract Decision\n\n" + self.RULE,
                     "```\n" + self.STEP + "```\n" + self.RULE,
                     self.STEP):
            with self.subTest(text=text):
                self.assertEqual(self.check("precondition", "Step 1.4b", text), "FAIL")

    def test_every_matching_step_needs_its_own_precondition(self):
        first = "### Step 3: Phase 2 with Story 1\n\n" + self.RULE
        second = "### Step 3: Phase 2 with spec_ref\n\n"
        self.assertEqual(self.check("precondition", "Step 3: Phase 2", first + second + self.RULE),
                         "PASS")
        self.assertEqual(self.check("precondition", "Step 3: Phase 2", first + second + "Run.\n"),
                         "FAIL")


class CreateSpecPreconditionTests(unittest.TestCase):
    """Bug 2026-10-22-create-spec-can-lock-an-unseen-contract: every lock point
    in create-spec.md opens with the rule that the contract was shown first,
    and the Contract Decision fits a four-option prompt."""

    def test_each_lock_point_has_a_precondition_row(self):
        module = load_helper_module()
        values = {r.value for r in module.ROWS
                  if r.file == "commands/create-spec.md" and r.kind == "precondition"}
        self.assertEqual(values, {"Step 1.4b: Contract Decision", "Step 3: Phase 2 with Story 1",
                                  "Step 3: Phase 2 with `spec_ref`"})

    def test_the_contract_decision_has_at_most_four_options(self):
        text = (REPO_ROOT / "commands" / "create-spec.md").read_text(encoding="utf-8")
        block = text[text.index('title: "Contract Decision"'):]
        block = block[:block.index("\n})")]
        self.assertLessEqual(len(re.findall(r"\{ id: \"", block)), 4)


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
    if row.kind == "precondition":
        # Push a blank-line-separated sentence ahead of each matching step's
        # precondition, so the step no longer opens with it.
        pattern = re.compile(r"^(#{1,6} %s.*\n\n)" % re.escape(row.value), re.MULTILINE)
        return pattern.sub(r"\1Do the step.\n\n", text)
    # invocation: every occurrence of the value (path plus subcommand) reduced to
    # a bare mention of the script's file name. Other mentions of the script,
    # such as a calibrated_against note, stay, so they cannot hide a weak row.
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
                    # Path plus the subcommand or flag the command must call.
                    self.assertRegex(row.value, r"^scripts/[\w.-]+\.(py|sh) \S")
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


class PhaseStateRowTests(unittest.TestCase):
    """Pin-map row 74: implement-phase.md's phase-state.py rows fail when every
    real call becomes a mention, even though the frontmatter's
    calibrated_against note still names `scripts/phase-state.py cmd_classify`."""

    def test_rows_fail_when_only_the_real_calls_become_mentions(self):
        module = load_helper_module()
        rows = [r for r in module.ROWS
                if r.file == "commands/implement-phase.md" and r.was == "check_phase_lanes"]
        self.assertTrue(rows)
        original = (REPO_ROOT / "commands" / "implement-phase.md").read_text(encoding="utf-8")
        note = "scripts/phase-state.py cmd_classify"
        self.assertIn(note, original)
        lines = original.splitlines(keepends=True)
        calls = re.compile(r"scripts/phase-state\.py (?=[a-z][\w-]*\b)(?!cmd_classify)")
        broken = "".join(calls.sub("phase-state.py ", line) if "calibrated_against" not in line
                         else line for line in lines)
        self.assertIn(note, broken, "the frontmatter note must stay")
        self.assertNotRegex(broken, r"scripts/phase-state\.py (?!cmd_classify)",
                            "every real call must be reduced")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "commands" / "implement-phase.md"
            target.parent.mkdir(parents=True)
            target.write_text(original, encoding="utf-8")
            _, before = run_helper(root)
            target.write_text(broken, encoding="utf-8")
            _, after = run_helper(root)
        for row in rows:
            with self.subTest(row=row_name(row)):
                self.assertEqual(verdict(before, row_name(row)), "PASS")
                self.assertEqual(verdict(after, row_name(row)), "FAIL")


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

    def test_a_helper_that_prints_no_verdict_is_a_run_error(self):
        for stub in ("raise SystemExit(0)\n", "print('noise')\nraise SystemExit(1)\n"):
            with self.subTest(stub=stub), TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "scripts").mkdir()
                shutil.copy(EVAL_SH, root / "scripts" / "eval.sh")
                (root / "scripts" / "eval-command-structure.py").write_text(stub, encoding="utf-8")
                shutil.copytree(REPO_ROOT / "commands", root / "commands")
                code, report = run_eval(root)
                self.assertEqual(code, 2, report)
                self.assertIn("command-structure helper failed to run", report)

    def test_command_structure_is_registered_right_after_shipped_refs(self):
        text = EVAL_SH.read_text(encoding="utf-8")
        block = text[text.index("CHECKS=(\n"):]
        block = block[:block.index("\n)\n")]
        names = [line.strip() for line in block.splitlines()[1:]]
        self.assertEqual(names[names.index("shipped-refs") + 1], "command-structure")


SPEC_NAME = "2026-10-20-shipped-command-hygiene"
SAFETY = {"prime-directive", "recommend-boundary", "gate-class", "loop-bound",
          "script-invocation", "verdict-provenance", "parsed-format"}
ALLOWED = {category: {"keep", "convert"} for category in SAFETY}
ALLOWED.update({"structure": {"keep", "convert", "remove"},
                "wording": {"keep", "remove"},
                "retired-text": {"keep", "remove"}})
HEADER = re.compile(
    r"^> Before: (\d+) instances at (\d+) call sites · After: (\d+) instances at (\d+) call sites$"
    r".*^> Dispositions: keep (\d+) · convert (\d+) · remove (\d+) · (\d+) \+ (\d+) \+ (\d+) = (\d+)$",
    re.MULTILINE | re.DOTALL)


def read_pin_map() -> Tuple[Tuple[int, ...], List[List[str]]]:
    """The header numbers and the table rows of the spec's pin-map.md, active
    or archived."""
    for parent in (".writ/specs", ".writ/specs/archive"):
        path = REPO_ROOT / parent / SPEC_NAME / "pin-map.md"
        if path.is_file():
            break
    else:
        raise AssertionError(f"no pin-map.md for {SPEC_NAME}")
    text = path.read_text(encoding="utf-8")
    header = HEADER.search(text)
    if header is None:
        raise AssertionError("pin-map.md header does not match the technical-spec format")
    rows = [[cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
            for line in text.splitlines() if re.match(r"^\| \d+ \|", line)]
    return tuple(int(n) for n in header.groups()), rows


class PinMapTests(unittest.TestCase):
    """The pin map is internally consistent, keeps every safety row, and every
    convert row has its structural row."""

    @classmethod
    def setUpClass(cls):
        cls.header, cls.rows = read_pin_map()

    def test_one_row_per_instance_with_every_column(self):
        """[AC-2.1] Rows run 1..N, N is the header's before count, and each row
        has function, line, target, kind, literal, category, disposition, reason."""
        before = self.header[0]
        self.assertEqual([int(row[0]) for row in self.rows], list(range(1, before + 1)))
        for row in self.rows:
            with self.subTest(row=row[0]):
                self.assertEqual(len(row), 9)
                number, function, line, target, kind, literal, _, _, reason = row
                self.assertRegex(function, r"^check_[a-z_]+$")
                self.assertRegex(line, r"^\d+$")
                self.assertRegex(target, r"^commands/[\w.-]+\.md$")
                self.assertIn(kind, ("require", "forbid", "forbid-ci"))
                self.assertTrue(literal and reason)

    def test_no_safety_row_is_removed(self):
        """[AC-2.2] Every disposition is one its category allows; the seven
        safety categories take only keep or convert."""
        for row in self.rows:
            category, disposition = row[6], row[7]
            with self.subTest(row=row[0]):
                self.assertIn(category, ALLOWED)
                self.assertIn(disposition, ALLOWED[category])
                if category in SAFETY:
                    self.assertNotEqual(disposition, "remove")

    def test_header_totals_match_the_rows_and_the_count_fell(self):
        """[AC-2.4] keep + convert + remove = N; the after count is the keep
        count, so the drop equals convert + remove and the count fell."""
        before, _, after, _, keep, convert, remove, k, c, r, n = self.header
        counts = Counter(row[7] for row in self.rows)
        self.assertEqual((counts["keep"], counts["convert"], counts["remove"]),
                         (keep, convert, remove))
        self.assertEqual((k, c, r, n), (keep, convert, remove, before))
        self.assertEqual(keep + convert + remove, before)
        self.assertEqual(after, keep)
        self.assertEqual(before - after, convert + remove)
        self.assertLess(after, before)

    def test_every_convert_row_has_its_structural_row(self):
        """[AC-2.3] [AC-2.4] Each convert row's target and check function is
        a row in scripts/eval-command-structure.py."""
        module = load_helper_module()
        converted = Counter((row[3], row[1]) for row in self.rows if row[7] == "convert")
        table = Counter((row.file, row.was) for row in module.ROWS)
        self.assertEqual(converted - table, Counter())


class RegistryTests(unittest.TestCase):
    """[AC-2.5] A check function deleted with its last pin leaves no CHECKS
    entry behind, and every entry still names a function."""

    def test_every_checks_entry_names_a_function_and_back(self):
        text = EVAL_SH.read_text(encoding="utf-8")
        block = text[text.index("CHECKS=(\n"):]
        block = block[:block.index("\n)\n")]
        registered = {"check_" + line.strip().replace("-", "_")
                      for line in block.splitlines()[1:]}
        defined = set(re.findall(r"(?m)^(check_[a-z_]+)\(\) \{", text)) - {"check_exists"}
        self.assertEqual(registered - defined, set(), "CHECKS entries with no function")
        self.assertEqual(defined - registered, set(), "check functions missing from CHECKS")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for scripts/goal-emit.py (Story 1 of
`2026-09-09-phase11-stage4-goal-emit`). [AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]
"""

from __future__ import annotations

import ast
import importlib.util
import io
import re
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "goal-emit.py"

ADR_SENTENCE = (
    "No `--recommend` command merges, opens PRs, or releases. "
    "Production remains a human decision."
)
ADR_PLAIN = (
    "No --recommend command merges, opens PRs, or releases. "
    "Production remains a human decision."
)
INVOKE = """\
/goal Treat this stop as acceptable when ANY of the following is true — do not
collapse these into "the checker passed":
(a) `python3 scripts/exit-criteria.py check --command implement-phase --state .writ/state/phase-execution-{timestamp}.json` exits 0 (verdict: met);
(b) the run is currently paused awaiting a retained AskQuestion — for example the
    Step 2.3 execute/edit/abort confirmation — regardless of whether the checker
    has been invoked yet; this state is met on its own;
(c) the checker exits 2 (verdict: impossible) — a tripped loop bound, an
    unresolved challenge_required, or a phase-state/git mismatch.
If none of these hold, the condition is not-met: continue the run rather than
stopping, and never treat a pause as something to route around."""
DONE_WHEN_CHECK = "count DONE WHEN lines on the card"

LOOP_YES = """# Fixture Loop Yes Card

> **loop:** yes

## OBJECTIVE

Convert a Goal Card into paste-ready goal files.

## DONE WHEN

- Emitter writes GOAL.md and VERIFY.md
- Printed invoke matches the adapter template

## STOP-CAPS

- loop.max_iterations: 8
- on_exhaustion: halt_reported

## QUALITY

Fixture quality line for verify copy.
"""

LOOP_NO = LOOP_YES.replace("> **loop:** yes", "> **loop:** no")

MALFORMED = """# Fixture Loop Yes Card

> **loop:** yes

## DONE WHEN

- Emitter writes GOAL.md and VERIFY.md

## STOP-CAPS

- loop.max_iterations: 8
"""


def _run(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _verdict(out: str) -> str:
    for line in out.splitlines():
        if line in ("pass", "fail", "unverifiable"):
            return line
    return out.strip()


def _reasons(out: str) -> list[str]:
    return [ln[8:] for ln in out.splitlines() if ln.startswith("reason: ")]


def _summary_line(out: str) -> str:
    for line in out.splitlines():
        if line.startswith("goal-emit:"):
            return line
    return ""


def _assert_no_banned(out: str) -> None:
    for word in ("accept", "reject", "modify-spec"):
        assert not re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(word), out)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _load_mod():
    spec = importlib.util.spec_from_file_location("goal_emit", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_main(mod, args: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = mod.main(args)
    return code, stdout.getvalue(), stderr.getvalue()


NO_QUALITY = """# Fixture No Quality

> **loop:** yes

## OBJECTIVE

Ship files.

## DONE WHEN

- Files exist

## STOP-CAPS

- loop.max_iterations: 8
"""

EMPTY_DONE_WHEN = """# Fixture Empty Done When

> **loop:** yes

## OBJECTIVE

Ship files.

## DONE WHEN

## STOP-CAPS

- loop.max_iterations: 8
"""

EMPTY_STOP_CAPS = """# Fixture Empty Stop Caps

> **loop:** yes

## OBJECTIVE

Ship files.

## DONE WHEN

- Files exist

## STOP-CAPS

"""

SPEC_REF_CARD = """# Fixture Spec Ref

> **loop:** yes

## OBJECTIVE

Ship files.

## DONE WHEN

- Files exist

## STOP-CAPS

- loop.max_iterations: 8

spec_ref: .writ/specs/demo/spec.md
"""


class GoalEmitTests(unittest.TestCase):
    def test_usage_unknown_subcommand_exits_2(self) -> None:
        code, _out, err = _run(["nope"])
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())

    def test_usage_no_subcommand_exits_2(self) -> None:
        code, _out, err = _run([])
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())

    def test_usage_unknown_flag_exits_2(self) -> None:
        code, _out, err = _run(["emit", "--nope"])
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())

    def test_unverifiable_missing_card_omitted(self) -> None:
        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run(["emit", "--out", str(out_dir)])
            self.assertEqual(_verdict(out), "unverifiable")
            self.assertEqual(code, 0)
            self.assertIn("missing_card", _reasons(out))
            self.assertFalse(out_dir.exists())
            _assert_no_banned(out)

    def test_unverifiable_missing_card_unreadable(self) -> None:
        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "emit-out"
            missing = Path(tmp) / "no-such-card.md"
            code, out, _err = _run(
                ["emit", "--card", str(missing), "--out", str(out_dir)]
            )
            self.assertEqual(_verdict(out), "unverifiable")
            self.assertEqual(code, 0)
            self.assertIn("missing_card", _reasons(out))
            self.assertFalse(out_dir.exists())

    def test_unverifiable_loop_no_creates_no_dir(self) -> None:
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "loop-no-card.md", LOOP_NO)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run(
                ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(_verdict(out), "unverifiable")
            self.assertEqual(code, 0)
            self.assertIn("loop_no", _reasons(out))
            self.assertFalse(out_dir.exists())
            self.assertFalse(out_dir.is_dir())

    def test_fail_malformed_card_missing_objective(self) -> None:
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "malformed.md", MALFORMED)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run(
                ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(_verdict(out), "fail")
            self.assertEqual(code, 1)
            self.assertIn("malformed_card", _reasons(out))
            self.assertTrue(_summary_line(out).startswith("goal-emit: fail"))

    def test_emit_malformed_card_creates_no_dir(self) -> None:
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "malformed.md", MALFORMED)
            out_dir = Path(tmp) / "emit-out"
            _run(["emit", "--card", str(card), "--out", str(out_dir)])
            self.assertFalse(out_dir.exists())

    def test_pass_emit_writes_files_and_prints_invoke_after_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "fixture-loop-yes.md", LOOP_YES)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run(
                ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(_verdict(out), "pass")
            self.assertEqual(code, 0)
            self.assertEqual(_reasons(out), [])
            goal = (out_dir / "GOAL.md").read_text(encoding="utf-8")
            verify = (out_dir / "VERIFY.md").read_text(encoding="utf-8")
            self.assertIn("Fixture Loop Yes Card", goal)
            self.assertIn("Convert a Goal Card into paste-ready goal files.", goal)
            self.assertIn("Emitter writes GOAL.md and VERIFY.md", goal)
            self.assertIn("loop.max_iterations: 8", goal)
            self.assertIn(ADR_PLAIN.replace("`", ""), goal.replace("`", ""))
            self.assertIn(INVOKE, goal)
            self.assertIn("Fixture quality line for verify copy.", verify)
            self.assertIn(DONE_WHEN_CHECK, verify)
            self.assertIn(ADR_PLAIN.replace("`", ""), verify.replace("`", ""))
            summary = _summary_line(out)
            self.assertTrue(summary.startswith("goal-emit: pass"))
            summary_at = out.index(summary)
            invoke_at = out.index(INVOKE)
            self.assertGreater(invoke_at, summary_at)
            _assert_no_banned(out)

    def test_default_out_stem_under_repo(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            card = _write(repo / "cards" / "fixture-loop-yes.md", LOOP_YES)
            code, out, _err = _run(
                ["emit", "--card", str(card), "--repo", str(repo)]
            )
            self.assertEqual(_verdict(out), "pass")
            self.assertEqual(code, 0)
            dest = repo / ".writ" / "goals" / "fixture-loop-yes"
            self.assertTrue((dest / "GOAL.md").is_file())
            self.assertTrue((dest / "VERIFY.md").is_file())

    def test_overwrite_does_not_append(self) -> None:
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "fixture-loop-yes.md", LOOP_YES)
            out_dir = Path(tmp) / "emit-out"
            _run(["emit", "--card", str(card), "--out", str(out_dir)])
            goal_path = out_dir / "GOAL.md"
            goal_path.write_text(
                goal_path.read_text(encoding="utf-8") + "\nAPPEND-MARKER\n",
                encoding="utf-8",
            )
            code, out, _err = _run(
                ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(_verdict(out), "pass")
            self.assertEqual(code, 0)
            rewritten = goal_path.read_text(encoding="utf-8")
            self.assertNotIn("APPEND-MARKER", rewritten)
            self.assertEqual(rewritten.count("Fixture Loop Yes Card"), 1)
            self.assertEqual(rewritten.count(INVOKE), 1)

    def test_check_pass_after_emit(self) -> None:
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "fixture-loop-yes.md", LOOP_YES)
            out_dir = Path(tmp) / "emit-out"
            _run(["emit", "--card", str(card), "--out", str(out_dir)])
            code, out, _err = _run(
                ["check", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(_verdict(out), "pass")
            self.assertEqual(code, 0)
            self.assertEqual(_reasons(out), [])
            self.assertTrue(_summary_line(out).startswith("goal-emit: pass"))
            self.assertNotIn(INVOKE, out)

    def test_check_does_not_print_invoke(self) -> None:
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "fixture-loop-yes.md", LOOP_YES)
            out_dir = Path(tmp) / "emit-out"
            _run(["emit", "--card", str(card), "--out", str(out_dir)])
            _code, out, _err = _run(
                ["check", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertNotIn("/goal Treat this stop", out)

    def test_check_does_not_rewrite_card(self) -> None:
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "fixture-loop-yes.md", LOOP_YES)
            out_dir = Path(tmp) / "emit-out"
            _run(["emit", "--card", str(card), "--out", str(out_dir)])
            before = card.read_text(encoding="utf-8")
            _run(["check", "--card", str(card), "--out", str(out_dir)])
            self.assertEqual(card.read_text(encoding="utf-8"), before)

    def test_check_missing_boundary_stripped_adr(self) -> None:
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "fixture-loop-yes.md", LOOP_YES)
            out_dir = Path(tmp) / "emit-out"
            _run(["emit", "--card", str(card), "--out", str(out_dir)])
            goal = out_dir / "GOAL.md"
            mutated = goal.read_text(encoding="utf-8").replace(
                ADR_SENTENCE, ""
            ).replace(ADR_PLAIN, "")
            goal.write_text(mutated, encoding="utf-8")
            code, out, _err = _run(
                ["check", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(_verdict(out), "fail")
            self.assertEqual(code, 1)
            self.assertIn("missing_boundary", _reasons(out))

    def test_check_missing_written_files_missing_boundary(self) -> None:
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "fixture-loop-yes.md", LOOP_YES)
            out_dir = Path(tmp) / "never-created"
            code, out, _err = _run(
                ["check", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(_verdict(out), "fail")
            self.assertEqual(code, 1)
            self.assertIn("missing_boundary", _reasons(out))
            self.assertFalse(out_dir.exists())

    def test_project_alias_of_repo(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "proj"
            card = _write(repo / "cards" / "fixture-loop-yes.md", LOOP_YES)
            code, out, _err = _run(
                ["emit", "--card", str(card), "--project", str(repo)]
            )
            self.assertEqual(_verdict(out), "pass")
            self.assertEqual(code, 0)
            dest = repo / ".writ" / "goals" / "fixture-loop-yes"
            self.assertTrue((dest / "GOAL.md").is_file())

    def test_banned_verdicts_never_appear(self) -> None:
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "fixture-loop-yes.md", LOOP_YES)
            out_dir = Path(tmp) / "emit-out"
            _code, out, _err = _run(
                ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            _assert_no_banned(out)

    def test_no_llm_import(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        joined = " ".join(imported)
        self.assertNotIn("anthropic", joined)
        self.assertNotIn("openai", joined)
        self.assertNotIn("litellm", joined)

    def test_quality_absent_uses_count_done_when(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "no-quality.md", NO_QUALITY)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run_main(
                mod, ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 0)
            self.assertEqual(_verdict(out), "pass")
            verify = (out_dir / "VERIFY.md").read_text(encoding="utf-8")
            self.assertNotIn("## QUALITY", verify)
            self.assertIn(DONE_WHEN_CHECK, verify)

    def test_empty_done_when_malformed(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "empty-done.md", EMPTY_DONE_WHEN)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run_main(
                mod, ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 1)
            self.assertEqual(_verdict(out), "fail")
            self.assertIn("malformed_card", _reasons(out))
            self.assertFalse(out_dir.exists())

    def test_empty_stop_caps_malformed(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "empty-stop.md", EMPTY_STOP_CAPS)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run_main(
                mod, ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 1)
            self.assertEqual(_verdict(out), "fail")
            self.assertIn("malformed_card", _reasons(out))

    def test_check_loop_no_creates_no_dir(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "loop-no-card.md", LOOP_NO)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run_main(
                mod, ["check", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 0)
            self.assertEqual(_verdict(out), "unverifiable")
            self.assertIn("loop_no", _reasons(out))
            self.assertFalse(out_dir.exists())

    def test_spec_ref_uses_exit_criteria_when_spec_exists(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            spec = _write(repo / ".writ" / "specs" / "demo" / "spec.md", "# Spec\n")
            card = _write(repo / "card.md", SPEC_REF_CARD)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run_main(
                mod,
                [
                    "emit",
                    "--card",
                    str(card),
                    "--out",
                    str(out_dir),
                    "--repo",
                    str(repo),
                ],
            )
            self.assertEqual(code, 0)
            self.assertEqual(_verdict(out), "pass")
            verify = (out_dir / "VERIFY.md").read_text(encoding="utf-8")
            self.assertIn("exit-criteria.py", verify)
            self.assertTrue(spec.is_file())

    def test_spec_ref_missing_file_uses_count(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            card = _write(repo / "card.md", SPEC_REF_CARD)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run_main(
                mod,
                [
                    "emit",
                    "--card",
                    str(card),
                    "--out",
                    str(out_dir),
                    "--repo",
                    str(repo),
                ],
            )
            self.assertEqual(code, 0)
            verify = (out_dir / "VERIFY.md").read_text(encoding="utf-8")
            self.assertIn(DONE_WHEN_CHECK, verify)
            self.assertNotIn("exit-criteria.py", verify)

    def test_spec_ref_trailing_period_still_resolves(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _write(repo / ".writ" / "specs" / "demo" / "spec.md", "# Spec\n")
            card_text = SPEC_REF_CARD.replace(
                "spec_ref: .writ/specs/demo/spec.md",
                "spec_ref: .writ/specs/demo/spec.md.",
            )
            card = _write(repo / "card.md", card_text)
            out_dir = Path(tmp) / "emit-out"
            code, _out, _err = _run_main(
                mod,
                [
                    "emit",
                    "--card",
                    str(card),
                    "--out",
                    str(out_dir),
                    "--repo",
                    str(repo),
                ],
            )
            self.assertEqual(code, 0)
            verify = (out_dir / "VERIFY.md").read_text(encoding="utf-8")
            self.assertIn("exit-criteria.py", verify)

    def test_spec_ref_absolute_path(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            spec = _write(Path(tmp) / "abs" / "spec.md", "# Spec\n")
            card_text = SPEC_REF_CARD.replace(
                "spec_ref: .writ/specs/demo/spec.md",
                "spec_ref: %s" % spec,
            )
            card = _write(Path(tmp) / "card.md", card_text)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run_main(
                mod, ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 0)
            verify = (out_dir / "VERIFY.md").read_text(encoding="utf-8")
            self.assertIn("exit-criteria.py", verify)

    def test_spec_ref_token_not_spec_md_ignored(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card_text = SPEC_REF_CARD.replace(
                "spec_ref: .writ/specs/demo/spec.md",
                "spec_ref: notes.txt other.markdown",
            )
            card = _write(Path(tmp) / "card.md", card_text)
            out_dir = Path(tmp) / "emit-out"
            code, _out, _err = _run_main(
                mod, ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 0)
            verify = (out_dir / "VERIFY.md").read_text(encoding="utf-8")
            self.assertIn(DONE_WHEN_CHECK, verify)

    def test_emit_loop_no_in_process(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "loop-no-card.md", LOOP_NO)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run_main(
                mod, ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 0)
            self.assertIn("loop_no", _reasons(out))
            self.assertFalse(out_dir.exists())

    def test_default_out_in_process(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            card = _write(repo / "cards" / "fixture-loop-yes.md", LOOP_YES)
            code, out, _err = _run_main(
                mod, ["emit", "--card", str(card), "--repo", str(repo)]
            )
            self.assertEqual(code, 0)
            self.assertEqual(_verdict(out), "pass")
            dest = repo / ".writ" / "goals" / "fixture-loop-yes"
            self.assertTrue((dest / "GOAL.md").is_file())

    def test_check_pass_in_process(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "card.md", LOOP_YES)
            out_dir = Path(tmp) / "emit-out"
            _run_main(mod, ["emit", "--card", str(card), "--out", str(out_dir)])
            code, out, _err = _run_main(
                mod, ["check", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 0)
            self.assertEqual(_verdict(out), "pass")

    def test_check_missing_files_in_process(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "card.md", LOOP_YES)
            out_dir = Path(tmp) / "never-created"
            code, out, _err = _run_main(
                mod, ["check", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 1)
            self.assertIn("missing_boundary", _reasons(out))

    def test_check_missing_card_in_process(self) -> None:
        mod = _load_mod()
        code, out, _err = _run_main(mod, ["check"])
        self.assertEqual(code, 0)
        self.assertEqual(_verdict(out), "unverifiable")
        self.assertIn("missing_card", _reasons(out))

    def test_check_malformed_card(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "malformed.md", MALFORMED)
            code, out, _err = _run_main(mod, ["check", "--card", str(card)])
            self.assertEqual(code, 1)
            self.assertEqual(_verdict(out), "fail")
            self.assertIn("malformed_card", _reasons(out))

    def test_check_verify_missing_adr(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card = _write(Path(tmp) / "card.md", LOOP_YES)
            out_dir = Path(tmp) / "emit-out"
            _run_main(
                mod, ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            verify = out_dir / "VERIFY.md"
            mutated = verify.read_text(encoding="utf-8").replace(
                ADR_SENTENCE, ""
            ).replace(ADR_PLAIN, "")
            verify.write_text(mutated, encoding="utf-8")
            code, out, _err = _run_main(
                mod, ["check", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 1)
            self.assertIn("missing_boundary", _reasons(out))

    def test_unreadable_card_oserror(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card = Path(tmp) / "dir-as-card"
            card.mkdir()
            code, out, _err = _run_main(mod, ["emit", "--card", str(card)])
            self.assertEqual(code, 0)
            self.assertEqual(_verdict(out), "unverifiable")
            self.assertIn("missing_card", _reasons(out))

    def test_binary_card_unreadable(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            card = Path(tmp) / "binary.md"
            card.write_bytes(b"\xff\xfe\x00\x01")
            code, out, _err = _run_main(mod, ["emit", "--card", str(card)])
            self.assertEqual(code, 0)
            self.assertEqual(_verdict(out), "unverifiable")
            self.assertIn("missing_card", _reasons(out))

    def test_missing_loop_header_malformed(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            text = LOOP_YES.replace("> **loop:** yes\n\n", "")
            card = _write(Path(tmp) / "no-loop.md", text)
            code, out, _err = _run_main(mod, ["emit", "--card", str(card)])
            self.assertEqual(code, 1)
            self.assertIn("malformed_card", _reasons(out))

    def test_untitled_card_emits_empty_title(self) -> None:
        mod = _load_mod()
        with TemporaryDirectory() as tmp:
            text = LOOP_YES.replace("# Fixture Loop Yes Card\n\n", "")
            card = _write(Path(tmp) / "untitled.md", text)
            out_dir = Path(tmp) / "emit-out"
            code, out, _err = _run_main(
                mod, ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 0)
            self.assertEqual(_verdict(out), "pass")
            goal = (out_dir / "GOAL.md").read_text(encoding="utf-8")
            self.assertTrue(goal.startswith("# \n"))

    def test_main_systemexit_non_int_becomes_2(self) -> None:
        mod = _load_mod()
        class FakeParser:
            def parse_args(self, argv):
                raise SystemExit("usage")

        original = mod.build_parser
        mod.build_parser = lambda: FakeParser()
        try:
            code, _out, _err = _run_main(mod, ["emit"])
        finally:
            mod.build_parser = original
        self.assertEqual(code, 2)

    def test_main_unknown_action_returns_2(self) -> None:
        mod = _load_mod()
        class Args:
            action = "other"
            card = None
            out = None
            repo = Path(".")

        class FakeParser:
            def parse_args(self, argv):
                return Args()

        original = mod.build_parser
        mod.build_parser = lambda: FakeParser()
        try:
            code, _out, _err = _run_main(mod, ["other"])
        finally:
            mod.build_parser = original
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

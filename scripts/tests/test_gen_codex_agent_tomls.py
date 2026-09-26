#!/usr/bin/env python3
"""Unit tests for scripts/gen-codex-agent-tomls.py (Story 3 of
`2026-09-03-model-delegation`, AC-3.5).

The generator turns `agents/*.md` into `codex/agents/*.toml`. Under ADR-024
the Codex floor is effort-only: the two `floor` stems get
`model_reasoning_effort = "low"` and no `model =` line (the parent's model is
used, so the floor never crosses vendors or exceeds the origin); the five
`anchor` stems get neither line. Any historical `model: "fast"` line inside an
embedded agent body is stripped defensively, and the retired `FAST_MODEL`
constant must not exist. The module filename contains a hyphen, so it is
imported by path — the recipe `test_ac_trace.py` uses.

Assertions run against the TOML HEADER only (everything before the
`developer_instructions = ` key), so text inside the embedded agent body can
never satisfy — or falsely violate — a header expectation.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "gen-codex-agent-tomls.py"
_spec = importlib.util.spec_from_file_location("gen_codex_agent_tomls", MODULE_PATH)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)  # type: ignore[union-attr]

FLOOR_STEMS = ("architecture-check-agent", "user-story-generator")
ANCHOR_STEMS = (
    "coding-agent",
    "documentation-agent",
    "review-agent",
    "testing-agent",
    "visual-qa-agent",
)
ALL_STEMS = FLOOR_STEMS + ANCHOR_STEMS

EFFORT_LOW = re.compile(r'^model_reasoning_effort = "low"$', re.MULTILINE)
EFFORT_KEY = re.compile(r"^model_reasoning_effort\s*=", re.MULTILINE)
MODEL_KEY = re.compile(r"^model\s*=", re.MULTILINE)
BODY_SPLIT = "\ndeveloper_instructions = "

BODY = "# Fixture Agent\n\nSome body text.\n"


def split_toml(output: str) -> tuple[str, str]:
    """Return (header, body) — the generator's header ends where the
    `developer_instructions` key begins."""
    assert BODY_SPLIT in output, "emit_toml() output lacks developer_instructions"
    header, body = output.split(BODY_SPLIT, 1)
    return header, body


class FloorStemsEmitEffortOnly(unittest.TestCase):
    """AC-3.5: floor stems carry `model_reasoning_effort = "low"` and no `model =`."""

    def test_floor_stems_emit_low_effort(self) -> None:
        for stem in FLOOR_STEMS:
            with self.subTest(stem=stem):
                header, _ = split_toml(gen.emit_toml(stem, BODY))
                self.assertRegex(header, EFFORT_LOW)

    def test_anchor_stems_emit_no_effort(self) -> None:
        # Any effort key — not just "low" — would pin the anchor below the
        # origin, so anchor stems must emit no model_reasoning_effort at all.
        for stem in ANCHOR_STEMS:
            with self.subTest(stem=stem):
                header, _ = split_toml(gen.emit_toml(stem, BODY))
                self.assertNotRegex(header, EFFORT_KEY)


class NoStemEmitsAModelKey(unittest.TestCase):
    """AC-3.5: `model =` is never emitted — the parent's model is always used."""

    def test_no_model_key_for_any_stem(self) -> None:
        for stem in ALL_STEMS:
            with self.subTest(stem=stem):
                header, _ = split_toml(gen.emit_toml(stem, BODY))
                self.assertNotRegex(header, MODEL_KEY)


class BodyFilterStripsRetiredFastLines(unittest.TestCase):
    """AC-3.5: any `model: "fast"` line — bare or the historical
    comma-terminated template form — is dropped from the embedded body, while
    unrelated `model:` lines survive."""

    FIXTURE_BODY = (
        "# Fixture Agent\n"
        "\n"
        "```\n"
        "model: \"fast\"\n"
        "model: default (inherits from parent)\n"
        "```\n"
        "\n"
        "Task({\n"
        "  subagent_type: \"generalPurpose\",\n"
        "  model: \"fast\",\n"
        "  model: inherit\n"
        "})\n"
    )

    def test_fast_lines_are_stripped_and_others_survive(self) -> None:
        _, body = split_toml(gen.emit_toml("coding-agent", self.FIXTURE_BODY))
        self.assertNotRegex(body, re.compile(r'^\s*model:\s*"fast",?\s*$', re.MULTILINE))
        self.assertIn("model: default (inherits from parent)\n", body)
        self.assertIn("model: inherit\n", body)


class FastModelConstantIsGone(unittest.TestCase):
    """AC-3.5: the generator contains no `FAST_MODEL`."""

    def test_no_fast_model_attribute(self) -> None:
        self.assertFalse(hasattr(gen, "FAST_MODEL"))


# ---------------------------------------------------------------------------
# Story 1 of `2026-09-26-arch-lint-and-follow-ups` — Codex TOML freshness.
# [AC-1.1, AC-1.2, AC-1.3, AC-1.4]
#
# Every agent is mapped, write mode validates every stem before the first
# write, and `--check` reports stale/missing/orphan/unmapped without writing.
# ---------------------------------------------------------------------------

REPO_ROOT = MODULE_PATH.parent.parent
MANIFEST = REPO_ROOT / ".writ" / "manifest.yaml"
SUMMARY_PREFIX = "gen-codex-agent-tomls: "


def manifest_agent_purposes() -> dict[str, str]:
    """`agents[].purpose` by name, read from the manifest without PyYAML."""
    purposes: dict[str, str] = {}
    in_agents = False
    name = None
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\S", line):
            in_agents = line.startswith("agents:")
            continue
        if not in_agents:
            continue
        m = re.match(r"^\s*-\s+name:\s*(\S+)\s*$", line)
        if m:
            name = m.group(1)
            continue
        m = re.match(r'^\s+purpose:\s*"(.*)"\s*$', line)
        if m and name:
            purposes[name] = m.group(1)
    return purposes


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MODULE_PATH), *args],
        capture_output=True,
        text=True,
    )


def snapshot(directory: Path) -> dict[str, bytes]:
    if not directory.exists():
        return {}
    return {p.name: p.read_bytes() for p in sorted(directory.iterdir())}


class EveryAgentIsMapped(unittest.TestCase):
    """AC-1.1: every `agents/*.md` stem has PURPOSES and SANDBOX entries, and
    each purpose is the manifest purpose verbatim."""

    def test_every_stem_has_purpose_and_sandbox(self) -> None:
        for md in sorted((REPO_ROOT / "agents").glob("*.md")):
            with self.subTest(stem=md.stem):
                self.assertIn(md.stem, gen.PURPOSES)
                self.assertIn(md.stem, gen.SANDBOX)

    def test_purposes_match_manifest(self) -> None:
        manifest = manifest_agent_purposes()
        for md in sorted((REPO_ROOT / "agents").glob("*.md")):
            with self.subTest(stem=md.stem):
                self.assertIn(md.stem, manifest)
                self.assertEqual(gen.PURPOSES.get(md.stem), manifest[md.stem])

    def test_evaluator_agent_is_read_only(self) -> None:
        self.assertEqual(gen.SANDBOX.get("evaluator-agent"), "read-only")
        self.assertEqual(
            gen.PURPOSES.get("evaluator-agent"),
            manifest_agent_purposes()["evaluator-agent"],
        )


class FixtureDirs(unittest.TestCase):
    """Temp `agents/` and `codex/agents/` dirs driven through the real CLI."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.agents = root / "agents"
        self.out = root / "codex" / "agents"
        self.agents.mkdir()
        self.out.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def add_agent(self, stem: str) -> None:
        (self.agents / f"{stem}.md").write_text(
            f"---\nname: {stem}\n---\n# {stem}\n\nBody.\n", encoding="utf-8"
        )

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return run_cli("--agents-dir", str(self.agents), "--out-dir", str(self.out), *args)

    def generate(self) -> None:
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)


class WriteModeValidatesBeforeWriting(FixtureDirs):
    """AC-1.2: an unmapped stem aborts write mode before any file is written,
    naming every unmapped stem."""

    def test_unmapped_stems_abort_with_no_writes(self) -> None:
        self.add_agent("coding-agent")
        self.add_agent("alpha-unmapped")
        self.add_agent("zeta-unmapped")
        (self.out / "sentinel.txt").write_text("keep\n", encoding="utf-8")
        before = snapshot(self.out)

        result = self.cli()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("alpha-unmapped", result.stderr)
        self.assertIn("zeta-unmapped", result.stderr)
        self.assertNotIn("coding-agent", result.stderr)
        self.assertEqual(snapshot(self.out), before)

    def test_expected_tomls_names_every_unmapped_stem(self) -> None:
        self.add_agent("coding-agent")
        self.add_agent("alpha-unmapped")
        self.add_agent("zeta-unmapped")
        with self.assertRaises(SystemExit) as ctx:
            gen.expected_tomls(self.agents)
        self.assertIn("alpha-unmapped", str(ctx.exception))
        self.assertIn("zeta-unmapped", str(ctx.exception))

    def test_expected_tomls_renders_every_mapped_stem(self) -> None:
        self.add_agent("coding-agent")
        self.add_agent("review-agent")
        expected = gen.expected_tomls(self.agents)
        self.assertEqual(sorted(expected), ["coding-agent", "review-agent"])
        self.assertIn('name = "review-agent"', expected["review-agent"])


class CheckModePass(FixtureDirs):
    """AC-1.3: identical output prints `pass` and a zeroed summary last,
    exits 0, and writes nothing; an unknown argument exits 2."""

    def test_check_passes_on_fresh_output(self) -> None:
        self.add_agent("coding-agent")
        self.add_agent("review-agent")
        self.generate()
        before = snapshot(self.out)

        result = self.cli("--check")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lines = result.stdout.strip().splitlines()
        self.assertEqual(lines[0], "pass")
        self.assertEqual(
            lines[-1],
            "gen-codex-agent-tomls: pass (0 stale, 0 missing, 0 orphan, 0 unmapped)",
        )
        self.assertEqual(snapshot(self.out), before)

    def test_unknown_argument_exits_2(self) -> None:
        self.assertEqual(run_cli("--bogus").returncode, 2)
        self.assertEqual(run_cli("--che").returncode, 2)


class CheckModeFail(FixtureDirs):
    """AC-1.4: each problem is one `reason:` line in stem order, the counted
    summary is last, exit is 1, and nothing is written."""

    def test_every_reason_in_stem_order(self) -> None:
        for stem in ("coding-agent", "review-agent", "testing-agent"):
            self.add_agent(stem)
        self.generate()
        stale = self.out / "coding-agent.toml"
        stale.write_text(stale.read_text(encoding="utf-8") + "# hand edit\n", encoding="utf-8")
        (self.out / "review-agent.toml").unlink()
        (self.out / "orphan-agent.toml").write_text('name = "orphan-agent"\n', encoding="utf-8")
        self.add_agent("mmm-unmapped")
        before = snapshot(self.out)

        result = self.cli("--check")

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(
            result.stdout.strip().splitlines(),
            [
                "fail",
                "reason: stale coding-agent",
                "reason: unmapped mmm-unmapped",
                "reason: orphan orphan-agent",
                "reason: missing review-agent",
                "gen-codex-agent-tomls: fail (1 stale, 1 missing, 1 orphan, 1 unmapped)",
            ],
        )
        self.assertEqual(snapshot(self.out), before)

    def test_missing_output_dir_reports_missing_without_creating_it(self) -> None:
        self.add_agent("coding-agent")
        self.out.rmdir()

        result = self.cli("--check")

        self.assertEqual(result.returncode, 1)
        self.assertIn("reason: missing coding-agent", result.stdout)
        self.assertTrue(result.stdout.strip().splitlines()[-1].startswith(SUMMARY_PREFIX))
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()

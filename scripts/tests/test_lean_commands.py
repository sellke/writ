#!/usr/bin/env python3
"""Story 4 (flagged harness cuts): lean command bodies.

Four lean siblings sit beside their defaults:

    commands/create-spec.lean.md       commands/implement-phase.lean.md
    commands/verify-spec.lean.md       commands/implement-story.lean.md

The contract this file pins:

- AC-4.1  the four default command files are byte-identical to before the
          story, and with WRIT_HARNESS_LEAN unset no lean byte reaches any
          invocation floor;
- AC-4.2  with WRIT_HARNESS_LEAN=1 the loader reports the lean body as the
          source for each of the four commands;
- AC-4.3  each lean body keeps its default's frontmatter contract (exit
          criteria, loop bounds, gates), its named gates and steps, and the
          production boundary, and carries no instruction to save tokens;
- AC-4.4  neither text is embedded in the live command (a pasted lean body
          is visible in the floor), and these four plus Story 2's lean
          preamble are the only lean siblings.

Every measurement pins WRIT_HARNESS_LEAN and removes ANTHROPIC_API_KEY, and
uses tokenizer="estimate", so the developer's shell cannot change a verdict.
"""

from __future__ import annotations

import glob
import hashlib
import importlib.util
import os
import re
import shutil
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
COMMANDS = os.path.join(ROOT, "commands")
TARGET = os.path.join(ROOT, "scripts", "measure-invocation.py")

LEAN_ENV = "WRIT_HARNESS_LEAN"
KEY_ENV = "ANTHROPIC_API_KEY"

STEMS = ("create-spec", "verify-spec", "implement-phase", "implement-story")

# sha256 of each default command, recorded before any lean sibling existed
# (identical to the HEAD blobs at commit 7b17152). AC-4.1: the lean work must
# not touch a single byte of these. Story 5 is the only story allowed to
# change the default load path; if it does, it updates these pins on purpose.
# Repinned 2026-09-25 (2026-09-25-jev-judgment-pilot Story 3): create-spec.md
# Step 2.6c/2.9 and verify-spec.md 3g gained the opt-in Jev conditional. The
# lean siblings deliberately keep today's full pass (lean is the no-Jev
# baseline arm).
# Repinned 2026-09-25 (Story 5): implement-story.md Gate 3 gained the opt-in
# `ac-shadow` line; implement-story.lean.md is unchanged (no-Jev baseline arm).
DEFAULT_SHA256 = {
    "create-spec": "ea07703c724b0783a6d666b8c0949fb210b74546db7ed29e080d4a25f238471f",
    "verify-spec": "5272a3f0a50a2850c327691fa2edf99973ebb4641a5d7871850afc78b50b58c9",
    "implement-phase": "f1a4d735259af57f7f763b3b50a11cf1a3f074ece68ea451d530d5ef33c23423",
    "implement-story": "29026fb12f0ce8422a5e8108ee658f7a2e2e7f48f1e1aa2407bb94f2c92d1231",
}

# Headings that name a gate, check, or procedural step. Built by hand from
# each default: every one of these carries pass/fail/escalation semantics or
# a script/AskQuestion the run depends on, so the lean body must keep it.
# Headings that are pure exposition (Overview, Example Usage, Integration
# with Writ) are deliberately absent — a lean body may drop them.
KEPT_HEADINGS = {
    "implement-story": [
        "Step 1: Story Selection",
        "Step 2: Load Context",
        "Step 3: Run Pipeline",
        "Gate 0: Architecture Check",
        "Gate 0.5: Boundary Computation",
        "Gate 1: Coding Agent",
        "Gate 2: Lint, Typecheck, Format & Build Smoke",
        "Gate 2.5: Change Surface Classification",
        "Gate 3: Review Agent",
        "Gate 3.5: Drift Response Handling",
        "A. Drift Response",
        "B. \"What Was Built\" Data Extraction",
        "Gate 4: Testing Agent",
        "Gate 4.5: Visual QA",
        "Gate 5: Documentation Agent",
        "Step 4: Story Completion",
        "BLOCKED Agent Escalation",
        "Quick Mode",
        "Completion",
    ],
    "create-spec": [
        "Recommended Mode (`--recommend`)",
        "Authoritative `--recommend` Invocation Matrix",
        "Autonomous Authoring Boundary",
        "`--from-prototype` Mode",
        "`--from-issue` Mode",
        "Step 0: Read Prototype Context",
        "Step 0: Read Issue Context",
        "Step 3: Phase 2 with Story 1 Pre-Marked Complete",
        "Step 3: Phase 2 with `spec_ref` Writeback",
        "Phase 1: Contract Establishment",
        "Step 1.0: Feature Selection",
        "Step 1.1: Initial Context Scan",
        "Step 1.3: Discovery Conversation",
        "Step 1.3b: Cross-Spec Overlap Check",
        "Step 1.4: Contract Proposal",
        "Step 1.4b: Contract Decision",
        "Step 1.5: Visual References",
        "Phase 2: Spec Package Creation",
        "Step 2.2: Determine Current Date",
        "Step 2.3: Create Directory Structure",
        "Step 2.4: Generate Core Documents",
        "Step 2.4b: Supersession Write-back",
        "Step 2.5: Plan User Stories",
        "Step 2.6: Generate User Stories in Parallel",
        "Step 2.6a: Validate Generated Stories",
        "Step 2.6b: Tag spec-lite.md Review Criteria with IDs",
        "Step 2.6c: Spec analysis",
        "Step 2.7: Create User Stories README",
        "Step 2.8: Generate Technical Sub-Specs",
        "Step 2.9: Final Package Review",
        "Completion",
    ],
    "verify-spec": [
        "Phase 1: Spec Discovery & Loading",
        "Step 1.1: Select Specification",
        "Step 1.2: Load Everything",
        "Phase 2: Verification Checks",
        "Check 1: Story File Integrity",
        "Check 2: Status Consistency",
        "Check 3: Completion Integrity",
        "Check 4: Dependency Validation",
        "Check 5: Deliverables Checklist",
        "Check 6: Spec Contract vs Implementation",
        "Check 7: Spec-Lite Integrity",
        "Check 8: Spec Owner Field Presence",
        "Phase 3: Verification Report",
        "Phase 4: Auto-Fix",
        "4.1: Sync README with Story Files",
        "4.2: Sync Deliverables Checklist",
        "4.3: Fix Status Headers",
        "4.4: Regenerate Spec-Lite",
        "Phase 5: Verification Report File",
        "Product Consistency Checks (`--product`)",
        "Check P1: Phase-Status Parity",
        "Check P2: ADR Reference Resolution",
        "Check P3: Derivative Freshness",
        "Check P4: Shipped-Claim Sanity",
        "Auto-Fix Mechanics (Check P3 only)",
        "Completion",
    ],
    "implement-phase": [
        "Recommended Mode (`--recommend`)",
        "Phase 1: Phase Resolution",
        "Step 1.1: Load the Roadmap",
        "Step 1.2: Resolve Features to Specs",
        "Step 1.2b: Decomposition Pre-Pass",
        "Step 1.3: Inventory Prior Progress",
        "Step 1.4: Emit Goal files when origin is a Goal Card",
        "Phase 2: Sequencing & The One Confirmation",
        "Step 2.1: Validate and Order the Specs",
        "Step 2.2: Verify Exit Criteria Exist",
        "Step 2.3: Present the Phase Execution Plan",
        "Phase 3: The Loop",
        "Step 3.1: Initialize Phase State",
        "Step 3.2: Per-Spec Iteration",
        "Step 3.2b: User Challenge Handling",
        "Step 3.3: Failure Handling",
        "Step 3.4: `--all` Mode",
        "Phase 4: Exit Criteria Verification & Handoff",
        "Step 4.1: Verify Machine-Checkable Criteria",
        "Step 4.1b: Evidence-Bound Knowledge Writeback",
        "Step 4.1c: Phase Progress and Production Health",
        "Step 4.2: The Honest Completion Report",
        "Step 4.3: Partial Completion Honesty",
        "Question Policy",
        "Completion",
    ],
}

# Every script that re-derives a verdict or persists state in the default
# must still be invoked from the lean body ("Verify the claim, don't trust it").
KEPT_SCRIPTS = {
    "implement-story": ["scripts/story-context.py", "scripts/arch-check.py",
                        "scripts/boundary-map.py", "scripts/build-smoke.py",
                        "scripts/change-surface.py", "scripts/review-override.py",
                        "scripts/drift-format.py", "scripts/test-integrity.py",
                        "scripts/docs-check.py"],
    "create-spec": ["scripts/spec-status.py", "scripts/supersession-writeback.py",
                    "scripts/ac-trace.py", "scripts/spec-analyze.py"],
    "verify-spec": ["scripts/ac-trace.py", "scripts/spec-analyze.py",
                    "scripts/spec-deps.py"],
    "implement-phase": ["scripts/spec-deps.py", "scripts/phase-state.py",
                        "scripts/goal-emit.py", "scripts/exit-criteria.py",
                        "validate-challenge", "record-halt", "close-spec",
                        "set-terminal-status", "record-exit-criterion"],
}

# Business rule 1: no line asks the model to conserve tokens, be brief, or
# avoid waste. Tuned against the defaults: "brevity" and "terse" are absent
# on purpose, because the defaults use them about spec-lite *artifact* size
# and about not omitting a report section "for brevity", which are not
# instructions to the model to shorten its own output.
TOKEN_SAVING = re.compile(
    r"fewer tokens|save tokens|saving tokens|conserve|be brief|be concise"
    r"|keep it short|keep (?:your )?(?:answers|responses|output) short"
    r"|avoid waste|wast(?:e|ing) tokens|minimi[sz]e tokens|token[- ]efficient",
    re.IGNORECASE)

# Production boundary (preamble Autonomy Gate Classes): no autonomous merge,
# PR, release, tag, or publish. Each lean body states it in one line.
BOUNDARY_LINE = re.compile(r"production boundary", re.IGNORECASE)
BOUNDARY_TERMS = ("merge", "PR", "release", "tag", "publish")


def _load_measure():
    spec = importlib.util.spec_from_file_location("measure_invocation_lc", TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mi = _load_measure()


def lean_env(value=None):
    env = {k: v for k, v in os.environ.items() if k not in (KEY_ENV, LEAN_ENV)}
    if value is not None:
        env[LEAN_ENV] = value
    return mock.patch.dict(os.environ, env, clear=True)


def default_path(stem):
    return os.path.join(COMMANDS, f"{stem}.md")


def lean_path(stem):
    return os.path.join(COMMANDS, f"{stem}.lean.md")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def size(path):
    return os.path.getsize(path)


def frontmatter(text):
    """The raw frontmatter block (between the first two `---` lines)."""
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return match.group(1) if match else ""


def contract_fields(text):
    """Frontmatter minus `name:` and `description:` — every other key (the
    problem/outcome, entry_level, exit_criteria, loop bounds, gates) must be
    carried verbatim by a lean body."""
    return [line for line in frontmatter(text).splitlines()
            if not line.startswith(("name:", "description:"))]


def exit_criteria(text):
    block = frontmatter(text)
    match = re.search(r"^exit_criteria:\n((?:  - .*\n?)+)", block, re.M)
    return match.group(1).strip() if match else ""


def headings(text):
    return [m.group(1).strip() for m in re.finditer(r"^#{1,6}\s+(.*)$", text, re.M)]


def has_heading(text, name):
    return any(h.startswith(name) for h in headings(text))


def expected_floor(stem):
    """base + default command + eagerly declared skills, from the files."""
    base = size(os.path.join(ROOT, "system-instructions.md")) + \
        size(os.path.join(COMMANDS, "_preamble.md"))
    fields = mi._L.read_frontmatter(default_path(stem)) or {}
    eager = 0
    for name in mi._L.parse_skill_names(fields.get("required_skills", "")):
        skill = os.path.join(ROOT, "skills", name, "SKILL.md")
        if os.path.isfile(skill):
            eager += size(skill)
    return base + size(default_path(stem)) + eager


def measure(root=ROOT):
    return mi.measure(root, tokenizer="estimate")


class DefaultsUntouched(unittest.TestCase):
    """AC-4.1: the four defaults are byte-identical to before the story."""

    def test_default_hashes_are_pinned(self):
        for stem, want in DEFAULT_SHA256.items():
            with open(default_path(stem), "rb") as handle:
                got = hashlib.sha256(handle.read()).hexdigest()
            self.assertEqual(got, want, f"commands/{stem}.md changed")

    def test_defaults_carry_no_lean_marker(self):
        for stem in STEMS:
            text = read(default_path(stem))
            self.assertNotIn("Lean variant of", text, stem)
            self.assertNotRegex(text, rf"(?m)^name:\s*{re.escape(stem)}-lean\s*$")
            self.assertNotIn("_preamble.lean.md", text, stem)


class FlagOffFloor(unittest.TestCase):
    """AC-4.1: flag unset, lean siblings on disk, no lean byte in any floor."""

    def test_no_lean_key_is_measured(self):
        with lean_env(None):
            report = measure()
        self.assertFalse([k for k in report["commands"] if ".lean" in k])
        self.assertNotIn("harness_lean", report)
        for stem in STEMS:
            self.assertNotIn("source", report["commands"][stem])

    def test_floor_is_base_plus_default_plus_eager_skills(self):
        with lean_env(None):
            report = measure()
        for stem in STEMS:
            row = report["commands"][stem]
            self.assertEqual(row["command_bytes"], size(default_path(stem)), stem)
            self.assertEqual(row["floor_bytes"], expected_floor(stem), stem)

    def test_base_is_the_default_preamble(self):
        with lean_env(None):
            report = measure()
        self.assertEqual(sorted(report["base"]["components"]),
                         ["commands/_preamble.md", "system-instructions.md"])


class FlagOnSource(unittest.TestCase):
    """AC-4.2: WRIT_HARNESS_LEAN=1 loads the lean bodies."""

    def test_source_is_the_lean_sibling(self):
        with lean_env("1"):
            report = measure()
        self.assertTrue(report.get("harness_lean"))
        for stem in STEMS:
            row = report["commands"][stem]
            self.assertEqual(row["source"], f"commands/{stem}.lean.md", stem)
            self.assertEqual(row["command_bytes"], size(lean_path(stem)), stem)

    def test_no_missing_sibling_warning_for_the_four(self):
        with lean_env("1"):
            report = measure()
        for stem in STEMS:
            self.assertFalse(
                [w for w in report["warnings"] if f"commands/{stem}.lean.md is absent" in w],
                stem)


class EmbeddingIsVisible(unittest.TestCase):
    """AC-4.4: pasting the lean body into the live command grows the floor
    by exactly the lean bytes, so embedding both texts cannot hide."""

    def _fixture(self, tmp, stem):
        shutil.copy(os.path.join(ROOT, "system-instructions.md"),
                    os.path.join(tmp, "system-instructions.md"))
        os.makedirs(os.path.join(tmp, "commands"))
        shutil.copy(os.path.join(COMMANDS, "_preamble.md"),
                    os.path.join(tmp, "commands", "_preamble.md"))
        shutil.copy(default_path(stem), os.path.join(tmp, "commands", f"{stem}.md"))

    def test_pasted_lean_body_grows_floor(self):
        for stem in STEMS:
            with tempfile.TemporaryDirectory() as tmp, lean_env(None):
                self._fixture(tmp, stem)
                before = measure(tmp)["commands"][stem]["floor_bytes"]
                with open(lean_path(stem), "rb") as handle:
                    lean_bytes = handle.read()
                with open(os.path.join(tmp, "commands", f"{stem}.md"), "ab") as handle:
                    handle.write(lean_bytes)
                after = measure(tmp)["commands"][stem]["floor_bytes"]
                self.assertEqual(after - before, len(lean_bytes), stem)


class LeanBodies(unittest.TestCase):
    """AC-4.3: contract kept, no token-saving line, shorter than default."""

    def test_frontmatter_name_and_description(self):
        for stem in STEMS:
            fm = frontmatter(read(lean_path(stem)))
            self.assertRegex(fm, rf"(?m)^name:\s*{re.escape(stem)}-lean\s*$", stem)
            self.assertRegex(
                fm, rf'(?m)^description:\s*"Lean variant of /{re.escape(stem)} '
                    rf"for WRIT_HARNESS_LEAN=1 baseline runs\.", stem)

    def test_exit_criteria_verbatim(self):
        for stem in STEMS:
            want = exit_criteria(read(default_path(stem)))
            self.assertTrue(want, stem)
            self.assertEqual(exit_criteria(read(lean_path(stem))), want, stem)

    def test_frontmatter_contract_verbatim(self):
        """loop bounds, gates, problem/outcome, entry_level: all kept."""
        for stem in STEMS:
            self.assertEqual(contract_fields(read(lean_path(stem))),
                             contract_fields(read(default_path(stem))), stem)

    def test_kept_headings_exist_in_default(self):
        """Guard the list itself: a typo would make the lean check vacuous."""
        for stem, names in KEPT_HEADINGS.items():
            text = read(default_path(stem))
            for name in names:
                self.assertTrue(has_heading(text, name), f"{stem}: {name}")

    def test_kept_headings_exist_in_lean(self):
        for stem, names in KEPT_HEADINGS.items():
            text = read(lean_path(stem))
            missing = [n for n in names if not has_heading(text, n)]
            self.assertEqual(missing, [], stem)

    def test_verdict_scripts_kept(self):
        for stem, names in KEPT_SCRIPTS.items():
            default, lean = read(default_path(stem)), read(lean_path(stem))
            for name in names:
                self.assertIn(name, default, f"{stem}: list typo {name}")
                self.assertIn(name, lean, f"{stem}: dropped {name}")

    def test_ask_question_gates_kept(self):
        for stem in STEMS:
            want = read(default_path(stem)).count("AskQuestion") > 0
            if want:
                self.assertIn("AskQuestion", read(lean_path(stem)), stem)

    def test_terminal_constraint_verbatim(self):
        """The default's Terminal constraint line (create-spec: "Do not offer
        to implement...") is carried byte-for-byte."""
        for stem in STEMS:
            want = [l for l in read(default_path(stem)).splitlines()
                    if l.startswith("**Terminal constraint:**")]
            self.assertEqual(len(want), 1, stem)
            self.assertIn(want[0], read(lean_path(stem)).splitlines(), stem)

    def test_create_spec_never_offers_to_code(self):
        self.assertIn("Do not offer to implement, build, or execute what was "
                      "specified.", read(lean_path("create-spec")))


def recommend_section(text):
    """`## Recommended Mode (`--recommend`)` up to the next `## ` heading."""
    start = text.index("## Recommended Mode (`--recommend`)")
    end = text.index("\n## ", start + 3)
    return text[start:end].rstrip("\n")


class RecommendModeKept(unittest.TestCase):
    """Story 2's lean preamble drops the Narrow Recommended-Delivery
    Exception, so under the flag the explicit recommend-mode branch, the
    invocation matrix validated before mutation, recommendation-log.md
    recording, and the retained pauses live only in these two bodies."""

    def test_create_spec_section_verbatim(self):
        self.assertEqual(recommend_section(read(lean_path("create-spec"))),
                         recommend_section(read(default_path("create-spec"))))

    def test_create_spec_section_elements(self):
        section = recommend_section(read(lean_path("create-spec")))
        for needle in ("Parse `--recommend` exactly once at command entry",
                       "Authoritative `--recommend` Invocation Matrix",
                       "stop before mutation", "recommendation-log.md",
                       "**Pause (bounded question or actionable blocker):**",
                       "**stops**"):
            self.assertIn(needle, section)

    def test_implement_phase_section_keeps_every_default_line(self):
        lean = recommend_section(read(lean_path("implement-phase"))).splitlines()
        for line in recommend_section(read(default_path("implement-phase"))).splitlines():
            self.assertIn(line, lean)

    def test_implement_phase_validates_matrix_before_mutation(self):
        section = recommend_section(read(lean_path("implement-phase")))
        self.assertRegex(section, r"invocation matrix before any mutation")
        for needle in ("recommendation-log.md", "Non-routine pauses are retained",
                       "never ships, opens PRs, or releases",
                       "incompatible with `--quick`"):
            self.assertIn(needle, section)

    def test_production_boundary_stated(self):
        for stem in STEMS:
            lines = [l for l in read(lean_path(stem)).splitlines()
                     if BOUNDARY_LINE.search(l)]
            self.assertTrue(lines, f"{stem}: no production boundary line")
            joined = " ".join(lines)
            for term in BOUNDARY_TERMS:
                self.assertRegex(joined, rf"(?i)\b{term}", f"{stem}: {term}")
            self.assertNotRegex(joined, r"(?i)only git write", stem)

    def test_no_token_saving_line(self):
        for stem in STEMS:
            for number, line in enumerate(read(lean_path(stem)).splitlines(), 1):
                self.assertIsNone(TOKEN_SAVING.search(line),
                                  f"{stem}.lean.md:{number}: {line}")

    def test_token_saving_pattern_does_not_false_match_defaults(self):
        """The defaults are the no-token-saving baseline; the pattern must
        not fire on their legitimate text, or the check is noise."""
        for stem in STEMS:
            self.assertIsNone(TOKEN_SAVING.search(read(default_path(stem))), stem)

    def test_token_saving_pattern_catches_instructions(self):
        for line in ("Be concise in every report.", "Use fewer tokens here.",
                     "Keep it short.", "Minimise tokens when you summarise.",
                     "Avoid waste: skip the table."):
            self.assertIsNotNone(TOKEN_SAVING.search(line), line)

    def test_lean_is_shorter(self):
        for stem in STEMS:
            lean = read(lean_path(stem)).count("\n")
            default = read(default_path(stem)).count("\n")
            self.assertLess(lean, default, stem)

    def test_required_command_sections(self):
        """eval.sh check_required_sections still applies to lean bodies."""
        for stem in STEMS:
            text = read(lean_path(stem))
            self.assertRegex(text, r"(?m)^## Overview\s*$", stem)
            self.assertRegex(text, r"(?m)^## (Invocation|Modes)\s*$", stem)
            self.assertRegex(text, r"(?m)^## Command Process\s*$", stem)

    def test_references_lean_preamble(self):
        for stem in STEMS:
            self.assertIn("commands/_preamble.lean.md", read(lean_path(stem)), stem)


class ImplementStorySpill(unittest.TestCase):
    """The lean implement-story reads spilled context instead of losing it."""

    def setUp(self):
        self.text = read(lean_path("implement-story"))

    def test_story_context_spill_is_read(self):
        self.assertIn("spill.path", self.text)
        self.assertIn("spill.bytes", self.text)
        self.assertRegex(self.text, r"Read the (spill )?file at `spill\.path`")

    def test_what_was_built_spills_instead_of_truncating(self):
        self.assertIn("1,000", self.text)
        self.assertIn(".writ/state/", self.text)
        self.assertRegex(self.text, r"(?i)instead of truncating")


class EvalLeannessSkipsLeanSiblings(unittest.TestCase):
    """eval-leanness.py treats `commands/<stem>.lean.md` as an alternate body
    for `<stem>`, never a command of its own: no README orphan, no second
    contract/budget row, and its per-command byte accounting stays equal to
    measure-invocation.py's (which already skips lean siblings)."""

    def _root(self, tmp):
        os.makedirs(os.path.join(tmp, "commands"))
        body = "---\nname: foo\ndescription: \"d\"\n---\n# Foo\n"
        for rel, text in (("commands/foo.md", body),
                          ("commands/foo.lean.md", body.replace("foo", "foo-lean")),
                          ("commands/_preamble.md", "P\n"),
                          ("commands/_preamble.lean.md", "p\n"),
                          ("README.md", "## Commands\n\n| Command | What |\n|---|---|\n"
                                        "| `/foo` | does foo |\n")):
            with open(os.path.join(tmp, rel), "w", encoding="utf-8") as handle:
                handle.write(text)
        return tmp

    def test_all_command_files_excludes_lean(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = mi._L.all_command_files(self._root(tmp))
            self.assertEqual(sorted(os.path.basename(p) for p in files),
                             ["_preamble.md", "foo.md"])

    def test_no_readme_orphan_for_lean_sibling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            self.assertEqual(mi._L.command_names(root), {"foo"})
            self.assertEqual(mi._L.check_parity(root), [])

    def test_command_count_ignores_lean_siblings(self):
        """The MAX_COMMANDS soft ceiling counts commands, not alternate
        bodies: adding lean siblings must not move `metrics.commands`."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            metrics, _warnings = mi._L.compute_metrics(root)
            without = metrics["commands"]
            for rel in ("commands/foo.lean.md", "commands/_preamble.lean.md"):
                os.remove(os.path.join(root, rel))
            metrics, _warnings = mi._L.compute_metrics(root)
            self.assertEqual(without, metrics["commands"])

    def test_orphan_lean_file_is_still_a_command(self):
        """A `bar.lean.md` with no `bar.md` is not a sibling of anything, so
        it is enumerated, counted, and reported as a README orphan."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            with open(os.path.join(root, "commands", "bar.lean.md"), "w") as handle:
                handle.write("---\nname: bar\ndescription: \"d\"\n---\n")
            names = [os.path.basename(p) for p in mi._L.all_command_files(root)]
            self.assertIn("bar.lean.md", names)
            self.assertNotIn("foo.lean.md", names)
            self.assertIn("bar.lean", mi._L.command_names(root))
            self.assertTrue([f for f in mi._L.check_parity(root)
                             if "bar.lean" in f["subject"]])
            metrics, _warnings = mi._L.compute_metrics(root)
            self.assertEqual(metrics["commands"], 3)  # foo, _preamble, bar.lean

    def test_real_repo_has_no_lean_command_name(self):
        self.assertFalse([n for n in mi._L.command_names(ROOT) if ".lean" in n])


class OnlyFourSiblings(unittest.TestCase):
    """AC-4.4: the only lean command siblings are these four plus Story 2's
    lean preamble."""

    def test_glob(self):
        found = sorted(os.path.basename(p)
                       for p in glob.glob(os.path.join(COMMANDS, "*.lean.md")))
        want = sorted([f"{s}.lean.md" for s in STEMS] + ["_preamble.lean.md"])
        self.assertEqual(found, want)


if __name__ == "__main__":
    unittest.main()

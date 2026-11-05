#!/usr/bin/env python3
"""Tests for scripts/review-panel.py (spec `2026-10-01-cross-family-review-panel`).

Story 7 of `2026-11-04-evidence-gated-review` removed the panel's `status`
and `tally` path, the `Review Panel` config key, its docs, and its Gate 3
wiring (ADR-032). What stays, and is tested here: the vendor table that
`trial-record` uses, the Gate 3 output parser that
`.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` loads by path, the
ADR-028 records, and the retrospective trial subcommands. The trimmed script
and the cleaned docs are checked too. [AC-7.1, AC-7.3]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "review-panel.py"

ORIGIN = "Claude Fable 5.1"


def _load_module():
    spec = importlib.util.spec_from_file_location("review_panel", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _run(*args: str) -> Tuple[int, List[str]]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout.splitlines()



class VendorTableTests(unittest.TestCase):
    """One test per table row, plus the boundaries. [AC-1.3] `trial-record`
    still resolves vendors through this table after Story 7."""

    @classmethod
    def setUpClass(cls):
        cls.rp = _load_module()

    def test_claude_prefix_is_anthropic(self):
        self.assertEqual(self.rp.slug_vendor("claude-opus-5-thinking-high"), "anthropic")

    def test_gpt_prefix_is_openai(self):
        self.assertEqual(self.rp.slug_vendor("gpt-5.6-sol-medium"), "openai")

    def test_o_digit_prefix_is_openai(self):
        for slug in ("o1", "o3-mini", "o4-mini-high", "o9"):
            self.assertEqual(self.rp.slug_vendor(slug), "openai", slug)

    def test_o_followed_by_letter_is_unknown(self):
        for slug in ("opus-5", "omni-2", "o-1", "oa3"):
            self.assertIsNone(self.rp.slug_vendor(slug), slug)

    def test_grok_prefix_is_xai(self):
        self.assertEqual(self.rp.slug_vendor("grok-4.7-high-fast"), "xai")

    def test_cursor_grok_prefix_is_xai_longest_prefix_wins(self):
        self.assertEqual(self.rp.slug_vendor("cursor-grok-4.6-medium-fast"), "xai")

    def test_gemini_prefix_is_google(self):
        self.assertEqual(self.rp.slug_vendor("gemini-3.8-flash-high"), "google")

    def test_composer_prefix_is_cursor(self):
        self.assertEqual(self.rp.slug_vendor("composer-2.5-fast"), "cursor")

    def test_muse_prefix_is_meta(self):
        self.assertEqual(self.rp.slug_vendor("muse-spark-1.3-high"), "meta")

    def test_unknown_prefix_resolves_to_none(self):
        for slug in ("inherit", "mistral-large", "cursor-small", "", "Claude-opus"):
            self.assertIsNone(self.rp.slug_vendor(slug), slug)

    def test_origin_word_match_is_case_insensitive(self):
        cases = {
            "Claude Fable 5.1": "anthropic",
            "claude-fable-5-1-thinking-high": "anthropic",
            "GPT-5.6 Sol": "openai",
            "o3": "openai",
            "Grok 4.7": "xai",
            "Gemini 3.8 Flash": "google",
            "Composer 2.5": "cursor",
            "Muse Spark": "meta",
        }
        for origin, vendor in cases.items():
            self.assertEqual(self.rp.origin_vendor(origin), vendor, origin)

    def test_origin_without_vendor_word_is_unknown(self):
        for origin in ("Some Model 1", "Claudette 2", "", "opus"):
            self.assertIsNone(self.rp.origin_vendor(origin), origin)

    def test_origin_naming_two_vendors_is_unknown(self):
        self.assertIsNone(self.rp.origin_vendor("Claude vs GPT"))


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Story 7 of `2026-11-04-evidence-gated-review`: the panel's `status` and
# `tally` path and its docs are gone (ADR-032).
# --------------------------------------------------------------------------

KEPT_SUBCOMMANDS = ("trial-init", "trial-prepare", "trial-record", "trial-label",
                    "trial-report")
GATE_UPGRADE_TRIAL = REPO_ROOT / ".writ" / "eval" / "gate-upgrade-trial" / "gate-upgrade-trial.py"
# The names gate-upgrade-trial.py reuses, plus the two helpers parse_output calls.
REUSED_NAMES = ("_prepare_run", "parse_output", "trial_key", "_key_order", "PrepareError",
                "normalize_location", "_issue_entries")
PANEL_ADAPTERS = ("adapters/openclaw.md", "adapters/codex.md", "adapters/claude-code.md",
                  "adapters/cursor.md")


def _subcommands(module) -> List[str]:
    parser = module.build_parser()
    subparsers = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
    return sorted(subparsers[0].choices)


class TrimmedScriptTests(unittest.TestCase):
    """AC-7.1 — gate-upgrade-trial.py still loads the script by path, the parser
    has no `status` or `tally`, and every `trial-*` subcommand parses."""

    @classmethod
    def setUpClass(cls):
        cls.rp = _load_module()

    def test_gate_upgrade_trial_loads_the_script_with_its_reused_names(self):
        spec = importlib.util.spec_from_file_location("gate_upgrade_trial_s7", GATE_UPGRADE_TRIAL)
        harness = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(harness)
        self.assertEqual(Path(harness.REVIEW_PANEL).resolve(), SCRIPT.resolve())
        module = harness.load_review_panel()
        for name in REUSED_NAMES:
            self.assertTrue(hasattr(module, name), name)

    def test_parser_has_no_status_or_tally(self):
        names = _subcommands(self.rp)
        self.assertNotIn("status", names)
        self.assertNotIn("tally", names)
        self.assertEqual(names, sorted(KEPT_SUBCOMMANDS))

    def test_removed_subcommands_are_usage_errors(self):
        for argv in (("status", "--repo", ".", "--origin", ORIGIN),
                     ("tally", "--origin", ORIGIN, "--primary", "primary.md")):
            rc, out = _run(*argv)
            self.assertEqual((rc, out), (2, []), argv[0])

    def test_every_trial_subcommand_parses(self):
        parser = self.rp.build_parser()
        argvs = {
            "trial-init": ["--baseline", "b.json", "--out", "t.json"],
            "trial-prepare": ["--trial", "t.json", "--yuss", "yuss", "--story", "s"],
            "trial-record": ["--trial", "t.json", "--story", "s", "--arm", "panel",
                             "--origin", ORIGIN, "--primary", "p.md",
                             "--reviewer", "gpt-5.6-sol-medium=r.md"],
            "trial-label": ["--trial", "t.json", "--story", "s", "--key", "ac:AC-1.1",
                            "--label", "valid", "--note", "n"],
            "trial-report": ["--trial", "t.json", "--json"],
        }
        self.assertEqual(sorted(argvs), sorted(KEPT_SUBCOMMANDS))
        for name, rest in argvs.items():
            with self.subTest(subcommand=name):
                self.assertTrue(callable(parser.parse_args([name] + rest).func))

    def test_docstring_names_no_removed_subcommand_or_key(self):
        doc = self.rp.__doc__
        for word in ("Review Panel", "--panel", "status", "tally"):
            self.assertNotIn(word, doc, word)
        for name in KEPT_SUBCOMMANDS:
            self.assertIn(name, doc, name)


class PanelRemovedFromDocsTests(unittest.TestCase):
    """AC-7.3 — the adapters, config-format.md, agent-cli-contract.md, eval.sh,
    and this repo's `.writ/config.md` carry no panel wiring."""

    def test_no_adapter_has_a_panel_paragraph(self):
        for rel in PANEL_ADAPTERS:
            self.assertNotIn("Review panel (ADR-028)", _read(rel), rel)

    def test_config_format_has_no_panel_key_and_one_removed_keys_line(self):
        doc = _read(".writ/docs/config-format.md")
        self.assertNotIn("| `Review Panel` |", doc)
        self.assertNotRegex(doc, r"(?m)^#+ Review Panel\b")
        self.assertNotIn("(#review-panel)", doc)
        removed = [line for line in doc.splitlines() if "Removed keys" in line]
        self.assertEqual(len(removed), 1, removed)
        self.assertIn("`Review Panel`", removed[0])
        self.assertIn("ADR-032", removed[0])

    def test_cli_contract_row_and_bullet_name_only_kept_subcommands(self):
        lines = _read(".writ/docs/agent-cli-contract.md").splitlines()
        row = [l for l in lines if l.startswith("| `review-panel.py` |")]
        bullet = [l for l in lines if l.startswith("- `review-panel.py` —")]
        self.assertEqual((len(row), len(bullet)), (1, 1), (row, bullet))
        for line in row + bullet:
            self.assertIsNone(re.search(r"\b(status|tally)\b", line), line)
            named = set(re.findall(r"\btrial-[a-z]+\b", line))
            self.assertTrue(named, line)
            self.assertLessEqual(named, set(KEPT_SUBCOMMANDS), line)
        callers = row[0].strip().strip("|").split("|")[3]
        self.assertNotIn("commands/", callers)
        self.assertNotIn("adapters/", callers)

    def test_eval_has_no_review_panel_check(self):
        text = _read("scripts/eval.sh")
        self.assertNotRegex(text, r"(?m)^  review-panel$")
        self.assertNotIn("check_review_panel", text)

    def test_repo_config_has_no_review_panel_line(self):
        self.assertNotRegex(_read(".writ/config.md"), r"(?mi)^- \*\*Review Panel:\*\*")


class ProductAmendmentTests(unittest.TestCase):
    """AC-1.5 — ADR-028 Decision 3 amendment, four adapter rows, roadmap pointer."""

    def test_adr_028_decision_3_amendment(self):
        adr = _read(".writ/decision-records/"
                    "adr-028-behavioral-verification-and-cross-family-panels.md")
        decision3 = adr.split("3. **Cross-family review is a panel", 1)[1].split("\n4. ", 1)[0]
        self.assertIn("*Amended 2026-10-01 by", decision3)
        for point in ("**Additive authority.**", "**Stakes signal.**", "`gate3_route`",
                      "`--panel`", "**Matching rule.**", "`[AC-N.M]`",
                      "**Exclusions are instructions.**", "**Removal measurement.**",
                      "retrospective trial"):
            self.assertIn(point, decision3, point)

    def test_roadmap_feature_3_points_to_spec(self):
        roadmap = _read(".writ/product/roadmap.md")
        feature = [l for l in roadmap.splitlines()
                   if re.match(r"- \[[ x]\] \*\*Cross-family review panel\*\*", l)]
        self.assertEqual(len(feature), 1)
        self.assertIn("2026-10-01-cross-family-review-panel/spec.md", feature[0])


# --------------------------------------------------------------------------
# Story 2 of `2026-10-01-cross-family-review-panel`: the Gate 3 output parser.
# Its `tally` consumer is gone (ADR-032); gate-upgrade-trial.py and the trial
# subcommands still read finding keys through it.
# --------------------------------------------------------------------------

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "review-panel"
OPENAI = "gpt-5.6-sol-medium"


class ParserTests(unittest.TestCase):
    """AC-2.2 — keys from unchecked tagged lines and qualifying Issues Found entries."""

    @classmethod
    def setUpClass(cls):
        cls.rp = _load_module()

    def _keys(self, name: str):
        parsed = self.rp.parse_output((FIXTURES / name).read_text(encoding="utf-8"))
        return parsed

    def test_verdict_line_for_both_agents(self):
        self.assertEqual(self._keys("primary-pass.md").verdict, "PASS")
        self.assertEqual(self._keys("panel-ac23.md").verdict, "FAIL")
        self.assertIsNone(self._keys("malformed.md").verdict)

    def test_unchecked_tagged_line_keys_ac(self):
        self.assertEqual(set(self._keys("primary-fail-ac23.md").findings), {"ac:AC-2.3"})
        self.assertEqual(set(self._keys("primary-pass.md").findings), set())

    def test_multi_id_tag_yields_one_key_per_id(self):
        self.assertEqual(set(self._keys("panel-multi-id.md").findings),
                         {"ac:AC-2.2", "ac:AC-2.3"})

    def test_category_key_from_critical_or_major_security_architecture(self):
        self.assertEqual(set(self._keys("panel-security-pay.md").findings),
                         {"security:app/api/pay.ts"})
        self.assertEqual(set(self._keys("panel-security-pay-b.md").findings),
                         {"security:app/api/pay.ts"})
        self.assertEqual(set(self._keys("panel-architecture-pay.md").findings),
                         {"architecture:app/api/pay.ts"})

    def test_minor_taste_untagged_and_locationless_are_never_keyed(self):
        self.assertEqual(set(self._keys("panel-minor-security-pay.md").findings), set())

    def test_criterion_category_is_not_keyed(self):
        keys = set(self._keys("panel-ac23.md").findings)
        self.assertEqual(keys, {"ac:AC-2.3"})

    def test_path_normalization(self):
        cases = {
            "`app/api/pay.ts:42`": "app/api/pay.ts",
            "`./app/api/pay.ts:42-47`": "app/api/pay.ts",
            "app/api/pay.ts:44": "app/api/pay.ts",
            "  `app/api/pay.ts` — catch block": "app/api/pay.ts",
            "./app/api/pay.ts": "app/api/pay.ts",
            "`scripts/x.py` `cmd_status` / y": "scripts/x.py",
            "": None,
            "  ": None,
        }
        for raw, expected in cases.items():
            self.assertEqual(self.rp.normalize_location(raw), expected, raw)

    def test_subheadings_inside_issues_found_keep_the_section_open(self):
        self.assertEqual(set(self._keys("panel-subheadings-na.md").findings),
                         {"security:app/api/pay.ts"})

    def test_placeholder_and_punctuated_locations(self):
        for raw in ("N/A", "n/a", "none", "-", "—", "`N/A`", "*none*"):
            self.assertIsNone(self.rp.normalize_location(raw), raw)
        self.assertEqual(self.rp.normalize_location("src/a.ts:12, src/b.ts"), "src/a.ts")
        self.assertEqual(self.rp.normalize_location("src/a.ts;"), "src/a.ts")

    def test_regex_accepts_every_evaluator_line_jev_judge_accepts(self):
        spec = importlib.util.spec_from_file_location(
            "jev_judge", REPO_ROOT / "scripts" / "jev-judge.py")
        jev = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(jev)
        lines = [
            "- [ ] Criterion — evidence [AC-1.1]",
            "  * [ ] Criterion `[AC-12.34]`",
            "- [ ] Criterion — not satisfied: x `[AC-2.3]`  ",
            "- [x] Criterion [AC-1.2]",
            "- [X] Criterion `[AC-1.3]`",
        ]
        for line in lines:
            jm = jev.EVALUATOR_LINE.match(line)
            tm = self.rp.CHECKLIST_LINE.match(line)
            self.assertIsNotNone(jm, line)
            self.assertIsNotNone(tm, line)
            self.assertEqual(jm.group(1), tm.group(1), line)
            self.assertIn(jm.group(2), tm.group(2), line)


class TaggedOutputContractTests(unittest.TestCase):
    """AC-2.1 — both Gate 3 agents (and the Claude Code mirrors) emit AC tags and Category."""

    AGENTS = ("agents/review-agent.md", "agents/evaluator-agent.md",
              "claude-code/agents/writ-reviewer.md", "claude-code/agents/writ-evaluator.md")

    def test_checklist_lines_end_with_ac_tag(self):
        for path in self.AGENTS:
            self.assertRegex(_read(path), r"`- \[ \]`[^\n]*`\[AC-N\.M\]` tag", path)

    def test_issues_found_entries_carry_category(self):
        for path in self.AGENTS:
            self.assertIn("- **Category:** [criterion/security/architecture/taste]",
                          _read(path), path)

    def test_codex_tomls_carry_the_category_line(self):
        for stem in ("review-agent", "evaluator-agent"):
            text = _read("codex/agents/%s.toml" % stem)
            self.assertIn("**Category:** [criterion/security/architecture/taste]", text, stem)

    def test_review_agent_example_lines_parse_in_jev_judge_and_tally(self):
        spec = importlib.util.spec_from_file_location(
            "jev_judge", REPO_ROOT / "scripts" / "jev-judge.py")
        jev = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(jev)
        sample = "\n".join(l for l in _read("agents/review-agent.md").splitlines()
                           if l.startswith("- [x] Given"))
        verdicts, conflicting = jev.parse_evaluator(sample)
        self.assertEqual(verdicts, {"AC-1.1": True, "AC-1.2": True})
        self.assertEqual(conflicting, [])
        unchecked = sample.replace("- [x]", "- [ ]")
        parsed = _load_module().parse_output("### REVIEW_RESULT: FAIL\n" + unchecked)
        self.assertEqual(set(parsed.findings), {"ac:AC-1.1", "ac:AC-1.2"})


class RatchetDisclosureTests(unittest.TestCase):
    """The implement-story.md re-pin is disclosed, not exempted. [AC-3.5]"""

    def test_disclosure_names_the_story_and_the_rebase(self):
        text = _read("scripts/tests/test_governor_enforcement.py")
        start = text.index("(spec 2026-10-01-cross-family-review-panel, Story 3)")
        block = text[start:text.index("KNOWN_OVER_BUDGET = {", start)]
        self.assertIn("rebased on", block)
        self.assertIn("2026-10-01-behavioral-verification Story 4's 11103", block)
        self.assertIn("Inline prose, no new step, gate, or spawn site. "
                      "Acknowledged, not exempted.", block)


# --------------------------------------------------------------------------
# Story 4 of `2026-10-01-cross-family-review-panel`: the retrospective trial
# harness (`trial-init`, `trial-prepare`, `trial-record`, `trial-label`,
# `trial-report`). A throwaway local git repo stands in for yuss; no network.
# --------------------------------------------------------------------------

TRIAL_FIXTURES = FIXTURES / "trial"
MINI_BASELINE = TRIAL_FIXTURES / "mini-baseline.json"
S1 = "2026-01-01-alpha/story-1-api"
S2 = "2026-01-02-beta/story-2-ui"
ALL_STORIES = (S1, S2, "2026-01-03-gamma/story-3-db", "2026-01-04-delta/story-4-lib")
AC23 = "ac:AC-2.3"
SEC_PAY = "security:app/api/pay.ts"
CAVEAT = "sample: 4 stories; one valid miss keeps the panel — a low bar, not a cost case"


def _run_in(cwd: Path, *args: str) -> Tuple[int, List[str], str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=str(cwd),
    )
    return proc.returncode, proc.stdout.splitlines(), proc.stderr


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@example.com",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True,
    )
    return proc.stdout.strip()


def _init_trial(cwd: Path, baseline: Path = MINI_BASELINE) -> Path:
    (cwd / ".writ").mkdir(exist_ok=True)
    out = cwd / "trial.json"
    code, out_lines, err = _run_in(cwd, "trial-init", "--baseline", str(baseline),
                                   "--out", str(out))
    assert code == 0, (out_lines, err)
    return out


def _trial(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _story(doc: dict, story_id: str) -> dict:
    return next(s for s in doc["stories"] if s["story_id"] == story_id)


def _record(cwd: Path, trial: Path, story: str, arm: str, primary: str,
            *reviewers: Tuple[str, str]) -> Tuple[int, List[str], str]:
    args = ["trial-record", "--trial", str(trial), "--story", story, "--arm", arm,
            "--origin", ORIGIN, "--primary", str(FIXTURES / primary)]
    for slug, name in reviewers:
        args += ["--reviewer", "%s=%s" % (slug, FIXTURES / name)]
    return _run_in(cwd, *args)


XAI = "grok-4.7-high-fast"


class TrialInitTests(unittest.TestCase):
    """`trial-init` copies the four-story selection into a skeleton. [AC-4.1]"""

    def test_skeleton_carries_the_identity_fields_and_no_arms(self):
        with TemporaryDirectory() as tmp:
            doc = _trial(_init_trial(Path(tmp)))
        self.assertEqual(doc["schema"], "panel-trial-v1")
        self.assertEqual([s["story_id"] for s in doc["stories"]], list(ALL_STORIES))
        first = doc["stories"][0]
        self.assertEqual(first["story_commit"], "1" * 40)
        self.assertEqual(first["parent_sha"], "1" * 39 + "0")
        self.assertEqual(first["spec_folder"], "2026-01-01-alpha")
        self.assertEqual(first["story_path"],
                         ".writ/specs/archive/2026-01-01-alpha/user-stories/story-1-api.md")
        for story in doc["stories"]:
            self.assertEqual(story["arms"], {})
            self.assertEqual(story["panel_only"], [])
            self.assertNotIn("test_files", story)

    def test_init_prints_pass_first_and_summary_last(self):
        """Agent CLI contract (check shape). [AC-4.1]"""
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "trial.json"
            code, lines, err = _run_in(Path(tmp), "trial-init", "--baseline",
                                       str(MINI_BASELINE), "--out", str(out))
        self.assertEqual(code, 0, err)
        self.assertEqual(lines[0], "pass")
        self.assertEqual(lines[1], "story: %s %s" % (S1, "1" * 12))
        self.assertEqual(lines[-1], "review-panel: trial initialized — 4 stories, no arms recorded")

    def test_real_phase11_baseline_has_four_stories(self):
        baseline = REPO_ROOT / ".writ/eval/baselines/2026-09-07-claude-fable-5-1.json"
        with TemporaryDirectory() as tmp:
            doc = _trial(_init_trial(Path(tmp), baseline))
        self.assertEqual(len(doc["stories"]), 4)

    def _refused(self, baseline_text: Optional[str], extra: Sequence[str] = ()) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.json"
            if baseline_text is not None:
                baseline.write_text(baseline_text, encoding="utf-8")
            out = root / "trial.json"
            code, _, err = _run_in(root, "trial-init", "--baseline", str(baseline),
                                   "--out", str(out), *extra)
            self.assertEqual(code, 2, err)
            self.assertFalse(out.exists())

    def test_missing_baseline_exits_2(self):
        self._refused(None)

    def test_unparseable_baseline_exits_2(self):
        self._refused("{not json")

    def test_selection_without_four_stories_exits_2(self):
        doc = _trial(MINI_BASELINE)
        doc["selection"] = doc["selection"][:3]
        self._refused(json.dumps(doc))

    def test_selection_entry_with_a_bad_sha_exits_2(self):
        doc = _trial(MINI_BASELINE)
        doc["selection"][1]["story_commit"] = "--upload-pack=evil"
        self._refused(json.dumps(doc))

    def test_selection_entry_with_an_escaping_path_exits_2(self):
        doc = _trial(MINI_BASELINE)
        doc["selection"][2]["story_path"] = "../outside.md"
        self._refused(json.dumps(doc))

    def test_existing_out_needs_force(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "trial.json"
            out.write_text("keep me", encoding="utf-8")
            args = ("trial-init", "--baseline", str(MINI_BASELINE), "--out", str(out))
            code, _, _ = _run_in(root, *args)
            self.assertEqual(code, 2)
            self.assertEqual(out.read_text(encoding="utf-8"), "keep me")
            code, _, _ = _run_in(root, *args, "--force")
            self.assertEqual(code, 0)
            self.assertEqual(_trial(out)["schema"], "panel-trial-v1")


class TrialPrepareTests(unittest.TestCase):
    """`trial-prepare` builds a fresh checkout and never writes in yuss. [AC-4.2]"""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.yuss = self.root / "yuss"
        self.yuss.mkdir()
        spec = self.yuss / ".writ/specs/2026-01-01-alpha"
        (spec / "user-stories").mkdir(parents=True)
        _git(self.yuss, "init", "-q")
        (spec / "spec.md").write_text(
            "# Alpha\n\n## Specification Contract\n\nDeliverable: an API route.\n\n"
            "## Detailed Requirements\n\nnot part of the contract\n", encoding="utf-8")
        story = spec / "user-stories/story-1-api.md"
        story.write_text("# Story 1: API\n\n> **Status:** Not Started\n", encoding="utf-8")
        _git(self.yuss, "add", "-A")
        _git(self.yuss, "commit", "-q", "-m", "parent")
        self.parent = _git(self.yuss, "rev-parse", "HEAD")
        (self.yuss / "app.py").write_text("print('route')\n", encoding="utf-8")
        story.write_text("# Story 1: API\n\n> **Status:** Completed ✅\n", encoding="utf-8")
        _git(self.yuss, "add", "-A")
        _git(self.yuss, "commit", "-q", "-m", "story 1")
        self.commit = _git(self.yuss, "rev-parse", "HEAD")
        doc = _trial(MINI_BASELINE)
        doc["selection"][0]["story_commit"] = self.commit
        doc["selection"][0]["parent_sha"] = self.parent
        baseline = self.root / "baseline.json"
        baseline.write_text(json.dumps(doc), encoding="utf-8")
        self.trial = _init_trial(self.root, baseline)
        self.tmp_root = self.root / "runs"
        self.tmp_root.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def _retarget(self, commit: str, parent: str) -> None:
        doc = _trial(self.trial)
        _story(doc, S1).update(story_commit=commit, parent_sha=parent)
        self.trial.write_text(json.dumps(doc), encoding="utf-8")

    def _third_commit(self, spec_text: str) -> str:
        (self.yuss / ".writ/specs/2026-01-01-alpha/spec.md").write_text(spec_text, encoding="utf-8")
        _git(self.yuss, "add", "-A")
        _git(self.yuss, "commit", "-q", "-m", "third")
        return _git(self.yuss, "rev-parse", "HEAD")

    def test_spec_without_a_contract_exits_2_and_cleans_up(self):
        third = self._third_commit("# Alpha\n\n## Detailed Requirements\n\nno contract\n")
        self._retarget(third, self.commit)
        before = self._snapshot()
        code, _, err = self._prepare()
        self.assertEqual(code, 2)
        self.assertIn("Specification Contract", err)
        self.assertEqual(list(self.tmp_root.iterdir()), [])
        self.assertEqual(self._snapshot(), before)

    def test_parent_beyond_depth_2_exits_2_and_cleans_up(self):
        third = self._third_commit("# Alpha\n\n## Specification Contract\n\nv3\n")
        self._retarget(third, self.parent)
        code, _, err = self._prepare()
        self.assertEqual(code, 2)
        self.assertIn("depth 2", err)
        self.assertEqual(list(self.tmp_root.iterdir()), [])

    def _snapshot(self) -> Tuple[str, str, str]:
        return (_git(self.yuss, "rev-parse", "HEAD"),
                _git(self.yuss, "for-each-ref"),
                _git(self.yuss, "status", "--porcelain"))

    def _prepare(self, story: str = S1, yuss: Optional[Path] = None):
        return _run_in(self.root, "trial-prepare", "--trial", str(self.trial),
                       "--yuss", str(yuss or self.yuss), "--story", story,
                       "--tmp-root", str(self.tmp_root))

    def test_prepare_writes_inputs_and_leaves_yuss_unchanged(self):
        before = self._snapshot()
        code, out, err = self._prepare()
        self.assertEqual(code, 0, (out, err))
        self.assertEqual(self._snapshot(), before)
        run = self.tmp_root / "writ-panel-trial-2026-01-01-alpha--story-1-api"
        checkout = run / "checkout"
        self.assertEqual(_git(checkout, "rev-parse", "HEAD"), self.commit)
        self.assertEqual(_git(checkout, "remote"), "")
        diff = (run / "diff.patch").read_text(encoding="utf-8")
        self.assertIn("+print('route')", diff)
        self.assertIn("Completed ✅", (run / "story.md").read_text(encoding="utf-8"))
        contract = (run / "contract.md").read_text(encoding="utf-8")
        self.assertIn("Deliverable: an API route.", contract)
        self.assertNotIn("not part of the contract", contract)
        self.assertEqual(out[0], "pass")  # agent CLI contract: verdict on line 1
        for name in ("checkout", "diff.patch", "story.md", "contract.md"):
            self.assertTrue(any(line.endswith(str(run / name)) for line in out), name)
        self.assertTrue(out[-1].startswith("review-panel: prepared %s" % S1))

    def test_missing_yuss_exits_2_and_writes_nothing(self):
        code, out, err = self._prepare(yuss=self.root / "no-such-yuss")
        self.assertEqual(code, 2)
        self.assertIn(S1, err)
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertEqual(list(self.tmp_root.iterdir()), [])

    def test_unreachable_commit_exits_2_and_writes_nothing(self):
        before = self._snapshot()
        code, _, err = self._prepare(story=S2)
        self.assertEqual(code, 2)
        self.assertIn(S2, err)
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertEqual(list(self.tmp_root.iterdir()), [])
        self.assertEqual(self._snapshot(), before)

    def test_unknown_story_exits_2(self):
        code, _, err = self._prepare(story="nope/story-9")
        self.assertEqual(code, 2)
        self.assertIn("nope/story-9", err)


class ExtractContractTests(unittest.TestCase):
    """Baseline specs predate the `## Specification Contract` heading. [AC-4.2]"""

    @classmethod
    def setUpClass(cls):
        cls.rp = _load_module()

    def test_current_heading_is_extracted_up_to_the_next_h2(self):
        text = "# A\n\n## Specification Contract\n\nDeliverable: x\n\n## Details\n\nno\n"
        self.assertEqual(self.rp.extract_contract(text),
                         "## Specification Contract\n\nDeliverable: x\n")

    def test_legacy_contract_summary_heading_is_the_fallback(self):
        text = "# A\n\n## Contract Summary\n\nDeliverable: y\n\n## 🎯 Experience Design\n\nno\n"
        self.assertEqual(self.rp.extract_contract(text),
                         "## Contract Summary\n\nDeliverable: y\n")

    def test_current_heading_wins_when_both_exist(self):
        text = "## Contract Summary\n\nold\n\n## Specification Contract\n\nnew\n"
        self.assertEqual(self.rp.extract_contract(text), "## Specification Contract\n\nnew\n")

    def test_no_contract_section_is_none(self):
        self.assertIsNone(self.rp.extract_contract("# A\n\n## Details\n\nno\n"))


class TrialRecordTests(unittest.TestCase):
    """`trial-record` stores keys, vendors, and severities, never text. [AC-4.3]"""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.trial = _init_trial(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def _both_arms(self, evaluator_primary: str = "primary-pass.md") -> None:
        code, out, err = _record(self.root, self.trial, S1, "evaluator", evaluator_primary)
        self.assertEqual(code, 0, (out, err))
        code, out, err = _record(self.root, self.trial, S1, "panel", "primary-pass.md",
                                 (OPENAI, "panel-ac23.md"), (XAI, "panel-security-pay.md"))
        self.assertEqual(code, 0, (out, err))

    def test_panel_only_findings_are_marked_unlabeled(self):
        self._both_arms()
        story = _story(_trial(self.trial), S1)
        panel_only = {f["key"]: f for f in story["panel_only"]}
        self.assertEqual(set(panel_only), {AC23, SEC_PAY})
        self.assertEqual(panel_only[AC23]["vendors"], ["openai"])
        self.assertEqual(panel_only[SEC_PAY]["vendors"], ["xai"])
        self.assertEqual(panel_only[SEC_PAY]["severity"], "Critical")
        self.assertIsNone(panel_only[AC23]["label"])
        self.assertIsNone(panel_only[AC23]["note"])
        panel = story["arms"]["panel"]
        self.assertEqual(panel["session_vendor"], "anthropic")
        self.assertEqual({k["key"] for k in panel["keys"]}, {AC23, SEC_PAY})
        self.assertEqual(story["arms"]["evaluator"]["keys"], [])

    def test_plural_only_turns_consonant_y_into_ies(self):
        rp = _load_module()
        self.assertEqual(rp._plural(0, "key"), "0 keys")
        self.assertEqual(rp._plural(2, "key"), "2 keys")
        self.assertEqual(rp._plural(1, "key"), "1 key")
        self.assertEqual(rp._plural(4, "story"), "4 stories")
        self.assertEqual(rp._plural(3, "panel-only finding"), "3 panel-only findings")

    def test_record_summary_reads_zero_keys(self):
        code, out, err = _record(self.root, self.trial, S1, "evaluator", "primary-pass.md")
        self.assertEqual(code, 0, (out, err))
        self.assertEqual(out[0], "pass")  # agent CLI contract: verdict on line 1
        self.assertIn("— 0 keys, 0 panel-only findings", out[-1])

    def test_a_key_the_evaluator_also_raised_is_not_panel_only(self):
        self._both_arms(evaluator_primary="primary-fail-ac23.md")
        story = _story(_trial(self.trial), S1)
        self.assertEqual([f["key"] for f in story["panel_only"]], [SEC_PAY])

    def test_recording_order_does_not_change_the_set_and_keeps_labels(self):
        _record(self.root, self.trial, S1, "panel", "primary-pass.md",
                (OPENAI, "panel-ac23.md"), (XAI, "panel-security-pay.md"))
        code, out, _ = _run_in(self.root, "trial-label", "--trial", str(self.trial),
                               "--story", S1, "--key", SEC_PAY, "--label", "valid",
                               "--note", "real missing auth check")
        self.assertEqual(code, 0)
        self.assertEqual(out[0], "pass")  # agent CLI contract: verdict on line 1
        self.assertTrue(out[-1].startswith("review-panel: labeled "), out)
        _run_in(self.root, "trial-label", "--trial", str(self.trial), "--story", S1,
                "--key", AC23, "--label", "invalid", "--note", "criterion was met")
        _record(self.root, self.trial, S1, "evaluator", "primary-fail-ac23.md")
        story = _story(_trial(self.trial), S1)
        self.assertEqual([(f["key"], f["label"]) for f in story["panel_only"]],
                         [(SEC_PAY, "valid")])

    def test_a_session_vendor_reviewer_is_not_a_panel_vendor(self):
        code, _, _ = _record(self.root, self.trial, S1, "panel", "primary-pass.md",
                             ("claude-opus-5-5-medium", "panel-ac23.md"),
                             (OPENAI, "panel-security-pay.md"))
        self.assertEqual(code, 0)
        story = _story(_trial(self.trial), S1)
        self.assertEqual([f["key"] for f in story["panel_only"]], [SEC_PAY])

    def test_dropped_reviewers_are_recorded_without_text(self):
        code, out, _ = _record(self.root, self.trial, S1, "panel", "primary-pass.md",
                               (OPENAI, "malformed.md"), ("mystery-1", "panel-ac23.md"),
                               (XAI, "panel-security-pay.md"))
        self.assertEqual(code, 0)
        panel = _story(_trial(self.trial), S1)["arms"]["panel"]
        self.assertEqual(panel["dropped"], [
            {"slug": OPENAI, "reason": "malformed_output"},
            {"slug": "mystery-1", "reason": "unknown_vendor"},
        ])
        self.assertIn("review-panel: dropped %s — malformed_output" % OPENAI, out)

    def test_raw_outputs_are_copied_under_state(self):
        self._both_arms()
        raw = self.root / ".writ/state/panel-trial/2026-01-01-alpha--story-1-api"
        self.assertEqual(sorted(p.name for p in raw.iterdir()), sorted([
            "evaluator-primary.md", "panel-primary.md",
            "panel-%s.md" % OPENAI, "panel-%s.md" % XAI,
        ]))
        self.assertEqual((raw / ("panel-%s.md" % OPENAI)).read_text(encoding="utf-8"),
                         (FIXTURES / "panel-ac23.md").read_text(encoding="utf-8"))

    def test_trial_json_holds_no_reviewer_text(self):
        self._both_arms()
        text = self.trial.read_text(encoding="utf-8")
        for marker in ("@@", "+++", "**Issue:**", "Severity:", "EVALUATION_RESULT",
                       "REVIEW_RESULT"):
            self.assertNotIn(marker, text)
        scanned = 0
        for name in ("panel-ac23.md", "panel-security-pay.md"):
            for line in (FIXTURES / name).read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if len(line) > 30:
                    scanned += 1
                    self.assertNotIn(line, text)
        self.assertGreater(scanned, 5)

    def test_a_source_shaped_location_is_stored_as_a_digest(self):
        source = "trial/panel-location-source.md"
        _record(self.root, self.trial, S1, "evaluator", "primary-pass.md")
        code, _, err = _record(self.root, self.trial, S1, "panel", "primary-pass.md",
                               (OPENAI, source))
        self.assertEqual(code, 0, err)
        story = _story(_trial(self.trial), S1)
        [finding] = story["panel_only"]
        self.assertRegex(finding["key"], r"^security:#[0-9a-f]{12}$")
        text = self.trial.read_text(encoding="utf-8")
        self.assertNotIn("isAdmin", text)
        self.assertNotIn("return token", text)

    def test_digest_keys_still_match_across_arms(self):
        source = "trial/panel-location-source.md"
        _record(self.root, self.trial, S1, "evaluator", source)
        _record(self.root, self.trial, S1, "panel", "primary-pass.md", (OPENAI, source))
        self.assertEqual(_story(_trial(self.trial), S1)["panel_only"], [])

    def test_record_outside_the_repo_root_exits_2(self):
        elsewhere = self.root / "scripts"
        elsewhere.mkdir()
        code, _, err = _record(elsewhere, self.trial, S1, "evaluator", "primary-pass.md")
        self.assertEqual(code, 2)
        self.assertIn("repo root", err)
        self.assertFalse((elsewhere / ".writ").exists())

    def test_usage_errors_exit_2_and_leave_the_file(self):
        before = self.trial.read_text(encoding="utf-8")
        cases = (
            (S1, "evaluator", "malformed.md", ()),
            (S1, "evaluator", "primary-pass.md", ((OPENAI, "panel-ac23.md"),)),
            (S1, "panel", "primary-pass.md", ()),
            ("nope/story-9", "evaluator", "primary-pass.md", ()),
        )
        for story, arm, primary, reviewers in cases:
            with self.subTest(story=story, arm=arm, primary=primary):
                code, _, _ = _record(self.root, self.trial, story, arm, primary, *reviewers)
                self.assertEqual(code, 2)
        code, _, _ = _run_in(self.root, "trial-record", "--trial", str(self.trial),
                             "--story", S1, "--arm", "evaluator", "--origin", "Mystery 9",
                             "--primary", str(FIXTURES / "primary-pass.md"))
        self.assertEqual(code, 2)
        self.assertEqual(self.trial.read_text(encoding="utf-8"), before)


class TrialLabelTests(unittest.TestCase):
    """`trial-label` validates before it writes. [AC-4.4]"""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.trial = _init_trial(self.root)
        _record(self.root, self.trial, S1, "evaluator", "primary-pass.md")
        _record(self.root, self.trial, S1, "panel", "primary-pass.md",
                (OPENAI, "panel-ac23.md"))

    def tearDown(self):
        self._tmp.cleanup()

    def _label(self, *args: str) -> int:
        code, _, _ = _run_in(self.root, "trial-label", "--trial", str(self.trial), *args)
        return code

    def test_label_and_note_are_stored(self):
        self.assertEqual(self._label("--story", S1, "--key", AC23, "--label", "valid",
                                     "--note", "the unmet criterion is real"), 0)
        finding = _story(_trial(self.trial), S1)["panel_only"][0]
        self.assertEqual((finding["label"], finding["note"]),
                         ("valid", "the unmet criterion is real"))

    def test_invalid_input_exits_2_and_leaves_the_file(self):
        before = self.trial.read_text(encoding="utf-8")
        for args in (
            ("--story", S1, "--key", AC23, "--label", "valid", "--note", "x" * 201),
            ("--story", S1, "--key", AC23, "--label", "valid", "--note", "two\nlines"),
            ("--story", S1, "--key", AC23, "--label", "valid", "--note", "see ```code```"),
            ("--story", S1, "--key", AC23, "--label", "maybe", "--note", "ok"),
            ("--story", S1, "--key", SEC_PAY, "--label", "valid", "--note", "ok"),
            ("--story", S2, "--key", AC23, "--label", "valid", "--note", "ok"),
        ):
            with self.subTest(args=args):
                self.assertEqual(self._label(*args), 2)
        self.assertEqual(self.trial.read_text(encoding="utf-8"), before)

    def test_a_200_character_note_is_accepted(self):
        self.assertEqual(self._label("--story", S1, "--key", AC23, "--label", "invalid",
                                     "--note", "y" * 200), 0)


class TrialReportTests(unittest.TestCase):
    """`trial-report` applies Business Rule 12. [AC-4.5]"""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.trial = _init_trial(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def _complete(self, panel_reviewers=((OPENAI, "panel-ac23.md"),)) -> None:
        for story in ALL_STORIES:
            _record(self.root, self.trial, story, "evaluator", "primary-pass.md")
            reviewers = panel_reviewers if story == S1 else ((OPENAI, "panel-minor-security-pay.md"),)
            _record(self.root, self.trial, story, "panel", "primary-pass.md", *reviewers)

    def _label(self, key: str, label: str) -> None:
        code, _, _ = _run_in(self.root, "trial-label", "--trial", str(self.trial),
                             "--story", S1, "--key", key, "--label", label, "--note", "n")
        self.assertEqual(code, 0)

    def _report(self, *extra: str) -> Tuple[int, List[str]]:
        code, out, _ = _run_in(self.root, "trial-report", "--trial", str(self.trial), *extra)
        return code, out

    def test_one_valid_panel_only_finding_keeps(self):
        self._complete(((OPENAI, "panel-ac23.md"), (XAI, "panel-security-pay.md")))
        self._label(AC23, "valid")
        self._label(SEC_PAY, "invalid")
        code, out = self._report()
        self.assertEqual(code, 0)
        self.assertEqual(out[:2], ["pass", "reason: keep"])
        self.assertIn(CAVEAT, out)
        self.assertIn("story: %s arms=evaluator,panel panel_only=2 valid=1 invalid=1 "
                      "unlabeled=0" % S1, out)
        self.assertEqual(out[-1], "review-panel: keep — 1 valid of 2 panel-only findings, 4 stories")

    def test_every_finding_labeled_invalid_removes(self):
        self._complete()
        self._label(AC23, "invalid")
        code, out = self._report()
        self.assertEqual((code, out[:2]), (0, ["pass", "reason: remove"]))
        self.assertEqual(out[-1], "review-panel: remove — 0 valid of 1 panel-only finding, 4 stories")

    def test_no_panel_only_findings_removes(self):
        self._complete(((OPENAI, "panel-minor-security-pay.md"),))
        code, out = self._report()
        self.assertEqual((code, out[:2]), (0, ["pass", "reason: remove"]))

    def test_unlabeled_findings_are_unverifiable(self):
        self._complete(((OPENAI, "panel-ac23.md"), (XAI, "panel-security-pay.md")))
        code, out = self._report()
        self.assertEqual((code, out[0]), (0, "unverifiable"))
        self.assertIn("reason: unlabeled %s %s" % (S1, AC23), out)
        self.assertEqual(out[-1], "review-panel: unverifiable — 2 unlabeled")

    def test_an_unlabeled_finding_beside_a_valid_one_is_still_unverifiable(self):
        self._complete(((OPENAI, "panel-ac23.md"), (XAI, "panel-security-pay.md")))
        self._label(AC23, "valid")
        code, out = self._report()
        self.assertEqual(out[0], "unverifiable")
        self.assertEqual(out[-1], "review-panel: unverifiable — 1 unlabeled")

    def test_a_missing_arm_is_unverifiable(self):
        self._complete()
        self._label(AC23, "valid")
        doc = _trial(self.trial)
        del _story(doc, S2)["arms"]["panel"]
        self.trial.write_text(json.dumps(doc), encoding="utf-8")
        code, out = self._report()
        self.assertEqual((code, out[0]), (0, "unverifiable"))
        self.assertIn("reason: missing_arm %s panel" % S2, out)
        self.assertEqual(out[-1], "review-panel: unverifiable — 1 story missing an arm")

    def test_fresh_trial_is_unverifiable_on_every_story(self):
        code, out = self._report()
        self.assertEqual((code, out[0]), (0, "unverifiable"))
        self.assertEqual(out[-1], "review-panel: unverifiable — 4 stories missing an arm")

    def test_json_is_one_object(self):
        self._complete()
        self._label(AC23, "valid")
        code, out = self._report("--json")
        self.assertEqual(code, 0)
        self.assertEqual(len(out), 1)
        doc = json.loads(out[0])
        self.assertEqual(doc["verdict"], "keep")
        self.assertEqual(doc["caveat"], CAVEAT)
        self.assertEqual(len(doc["stories"]), 4)
        self.assertEqual(doc["summary"],
                         "review-panel: keep — 1 valid of 1 panel-only finding, 4 stories")

    def test_a_trial_without_four_stories_exits_2(self):
        doc = _trial(self.trial)
        doc["stories"] = doc["stories"][:3]
        self.trial.write_text(json.dumps(doc), encoding="utf-8")
        code, _ = self._report()
        self.assertEqual(code, 2)

    def test_unreadable_trial_exits_2(self):
        self.trial.write_text("{oops", encoding="utf-8")
        code, _ = self._report()
        self.assertEqual(code, 2)
        code, _ = _run_in(self.root, "trial-report", "--trial", str(self.root / "none.json"))[:2]
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for scripts/review-panel.py (spec `2026-10-01-cross-family-review-panel`).

Story 1: the `- **Review Panel:**` config line, the fixed vendor table, and
`status` (kept / dropped reviewers, every off or skip reason, platforms,
`--json`, usage exits). [AC-1.2, AC-1.3, AC-1.4]
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple


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


def _repo(tmp: Path, config_line: Optional[str]) -> Path:
    writ = tmp / ".writ"
    writ.mkdir(parents=True, exist_ok=True)
    lines = ["# Writ Project Config", "", "## Conventions", "",
             "- **Default Branch:** main"]
    if config_line is not None:
        lines.append(config_line)
    (writ / "config.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp


class VendorTableTests(unittest.TestCase):
    """One test per table row, plus the boundaries. [AC-1.3]"""

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


class StatusPassTests(unittest.TestCase):
    """[AC-1.2]"""

    def test_pass_lists_kept_and_dropped_reviewers(self):
        line = ("- **Review Panel:** gpt-5.6-sol-medium, claude-opus-5-thinking-high, "
                "gpt-5.6-sol-medium, foo-1, cursor-grok-4.6-medium-fast, "
                "gemini-3.8-flash-high, composer-2.5-fast")
        with TemporaryDirectory() as tmp:
            repo = _repo(Path(tmp), line)
            rc, out = _run("status", "--repo", str(repo), "--origin", ORIGIN)
        self.assertEqual(rc, 0)
        self.assertEqual(out[0], "pass")
        self.assertIn("reviewer: gpt-5.6-sol-medium openai", out)
        self.assertIn("reviewer: cursor-grok-4.6-medium-fast xai", out)
        self.assertIn("reviewer: gemini-3.8-flash-high google", out)
        self.assertIn("dropped: claude-opus-5-thinking-high same_vendor", out)
        self.assertIn("dropped: gpt-5.6-sol-medium duplicate_slug", out)
        self.assertIn("dropped: foo-1 unknown_vendor", out)
        self.assertIn("dropped: composer-2.5-fast over_cap", out)
        self.assertTrue(out[-1].startswith("review-panel: pass — 3 reviewers"), out[-1])

    def test_kept_order_follows_config_order(self):
        line = "- **Review Panel:** gemini-3.8-flash-high, gpt-5.6-sol-medium"
        with TemporaryDirectory() as tmp:
            rc, out = _run("status", "--repo", str(_repo(Path(tmp), line)),
                           "--origin", ORIGIN)
        reviewers = [l for l in out if l.startswith("reviewer: ")]
        self.assertEqual(reviewers, ["reviewer: gemini-3.8-flash-high google",
                                     "reviewer: gpt-5.6-sol-medium openai"])

    def test_first_matching_line_wins(self):
        with TemporaryDirectory() as tmp:
            repo = _repo(Path(tmp), "- **Review Panel:** gpt-5.6-sol-medium\n"
                                    "- **Review Panel:** none")
            rc, out = _run("status", "--repo", str(repo), "--origin", ORIGIN)
        self.assertEqual(out[0], "pass")

    def test_json_shape(self):
        line = "- **Review Panel:** gpt-5.6-sol-medium, claude-opus-5-thinking-high"
        with TemporaryDirectory() as tmp:
            rc, out = _run("status", "--repo", str(_repo(Path(tmp), line)),
                           "--origin", ORIGIN, "--json")
        self.assertEqual(rc, 0)
        self.assertEqual(len(out), 1)
        payload = json.loads(out[0])
        self.assertEqual(payload["verdict"], "pass")
        self.assertEqual(payload["session_vendor"], "anthropic")
        self.assertEqual(payload["reviewers"],
                         [{"slug": "gpt-5.6-sol-medium", "vendor": "openai"}])
        self.assertEqual(payload["dropped"],
                         [{"slug": "claude-opus-5-thinking-high", "reason": "same_vendor"}])
        self.assertTrue(payload["summary"].startswith("review-panel: pass"))


class StatusUnverifiableTests(unittest.TestCase):
    """Every off or skip condition prints exactly one reason. [AC-1.4]"""

    def _status(self, config_line, *extra, origin=ORIGIN):
        with TemporaryDirectory() as tmp:
            repo = _repo(Path(tmp), config_line)
            return _run("status", "--repo", str(repo), "--origin", origin, *extra)

    def _assert_reason(self, out, reason):
        self.assertEqual(out[0], "unverifiable")
        reasons = [l for l in out if l.startswith("reason: ")]
        self.assertEqual(reasons, ["reason: %s" % reason])
        self.assertTrue(out[-1].startswith("review-panel: "), out[-1])

    def test_no_config_line(self):
        rc, out = self._status(None)
        self.assertEqual(rc, 0)
        self._assert_reason(out, "no_config_line")
        self.assertEqual(out[-1], "review-panel: off — no_config_line")

    def test_missing_config_file_is_no_config_line(self):
        with TemporaryDirectory() as tmp:
            rc, out = _run("status", "--repo", tmp, "--origin", ORIGIN)
        self.assertEqual(rc, 0)
        self._assert_reason(out, "no_config_line")

    def test_none_disables_case_insensitive(self):
        for value in ("none", "None", "NONE"):
            rc, out = self._status("- **Review Panel:** %s" % value)
            self.assertEqual(rc, 0)
            self._assert_reason(out, "panel_disabled")
            self.assertEqual(out[-1], "review-panel: off — panel_disabled")

    def test_empty_list_is_malformed(self):
        for value in ("", " , ,"):
            rc, out = self._status("- **Review Panel:** %s" % value)
            self.assertEqual(rc, 0)
            self._assert_reason(out, "malformed_config")
            self.assertEqual(out[-1], "review-panel: skipped — malformed_config")

    def test_unknown_session_vendor(self):
        rc, out = self._status("- **Review Panel:** gpt-5.6-sol-medium",
                               origin="Mystery Model 9")
        self.assertEqual(rc, 0)
        self._assert_reason(out, "unknown_session_vendor")
        self.assertEqual(out[-1], "review-panel: skipped — unknown_session_vendor")

    def test_no_other_vendor_lists_drops(self):
        rc, out = self._status("- **Review Panel:** claude-opus-5-thinking-high, foo-1")
        self.assertEqual(rc, 0)
        self._assert_reason(out, "no_other_vendor")
        self.assertIn("dropped: claude-opus-5-thinking-high same_vendor", out)
        self.assertIn("dropped: foo-1 unknown_vendor", out)
        self.assertEqual(out[-1], "review-panel: skipped — no_other_vendor (dropped: "
                         "claude-opus-5-thinking-high same_vendor, foo-1 unknown_vendor)")

    def test_platform_claude_code_and_codex_skip(self):
        for platform in ("claude-code", "codex"):
            rc, out = self._status("- **Review Panel:** gpt-5.6-sol-medium",
                                   "--platform", platform)
            self.assertEqual(rc, 0)
            self._assert_reason(out, "platform_cannot_spawn_other_vendors")
            self.assertEqual(out[-1], "review-panel: skipped — platform cannot "
                             "spawn other vendors")

    def test_platform_cursor_is_pass(self):
        rc, out = self._status("- **Review Panel:** gpt-5.6-sol-medium",
                               "--platform", "cursor")
        self.assertEqual((rc, out[0]), (0, "pass"))
        self.assertNotIn("reason: unverified_platform", out)

    def test_platform_openclaw_is_pass_plus_unverified(self):
        rc, out = self._status("- **Review Panel:** gpt-5.6-sol-medium",
                               "--platform", "openclaw")
        self.assertEqual((rc, out[0]), (0, "pass"))
        self.assertIn("reason: unverified_platform", out)
        self.assertIn("reviewer: gpt-5.6-sol-medium openai", out)

    def test_no_config_line_wins_over_platform(self):
        rc, out = self._status(None, "--platform", "claude-code")
        self._assert_reason(out, "no_config_line")


class StatusUsageTests(unittest.TestCase):
    """[AC-1.4]"""

    def test_missing_origin_exits_2(self):
        with TemporaryDirectory() as tmp:
            rc, _ = _run("status", "--repo", tmp)
        self.assertEqual(rc, 2)

    def test_unreadable_repo_exits_2(self):
        with TemporaryDirectory() as tmp:
            rc, _ = _run("status", "--repo", str(Path(tmp) / "missing"),
                         "--origin", ORIGIN)
        self.assertEqual(rc, 2)

    @unittest.skipIf(os.name != "posix" or os.geteuid() == 0, "needs POSIX non-root")
    def test_unreadable_repo_directory_exits_2(self):
        with TemporaryDirectory() as tmp:
            repo = _repo(Path(tmp) / "repo", "- **Review Panel:** gpt-5.6-sol-medium")
            repo.chmod(0)
            try:
                rc, _ = _run("status", "--repo", str(repo), "--origin", ORIGIN)
            finally:
                repo.chmod(0o755)
        self.assertEqual(rc, 2)

    def test_undecodable_config_exits_2(self):
        with TemporaryDirectory() as tmp:
            repo = _repo(Path(tmp), None)
            (repo / ".writ" / "config.md").write_bytes(b"- **Review Panel:** \xff\xfe\n")
            rc, _ = _run("status", "--repo", str(repo), "--origin", ORIGIN)
        self.assertEqual(rc, 2)

    def test_unknown_platform_exits_2(self):
        with TemporaryDirectory() as tmp:
            rc, _ = _run("status", "--repo", tmp, "--origin", ORIGIN,
                         "--platform", "vscode")
        self.assertEqual(rc, 2)


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


class ConfigDocTests(unittest.TestCase):
    """AC-1.1 — config-format.md documents the line, its rules, and consent."""

    def test_review_panel_section(self):
        doc = _read(".writ/docs/config-format.md")
        self.assertIn("| `Review Panel` |", doc)
        section = doc.split("## Review Panel", 1)[1].split("\n## ", 1)[0]
        for phrase in ("- **Review Panel:** <slug>[, <slug>…]", "first matching line wins",
                       "`none`", "case-insensitive", "keep their order", "`duplicate_slug`",
                       "`over_cap`", "consent to send story content",
                       "review-panel.py status"):
            self.assertIn(phrase, section, phrase)


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

    def test_each_adapter_has_one_panel_row(self):
        rows = {
            "adapters/cursor.md": "**Review panel (ADR-028): available.**",
            "adapters/claude-code.md": "**Review panel (ADR-028): unavailable.**",
            "adapters/codex.md": "**Review panel (ADR-028): unavailable by default.**",
            "adapters/openclaw.md": "**Review panel (ADR-028): *(unverified)*.**",
        }
        for path, row in rows.items():
            text = _read(path)
            self.assertEqual(text.count("**Review panel (ADR-028):"), 1, path)
            self.assertIn(row, text, path)
        self.assertIn("`slug_rejected`", _read("adapters/cursor.md"))
        self.assertIn("`sessions_spawn`", _read("adapters/openclaw.md"))

    def test_roadmap_feature_3_points_to_spec(self):
        roadmap = _read(".writ/product/roadmap.md")
        feature = [l for l in roadmap.splitlines()
                   if l.startswith("- [ ] **Cross-family review panel**")]
        self.assertEqual(len(feature), 1)
        self.assertIn("2026-10-01-cross-family-review-panel/spec.md", feature[0])


# --------------------------------------------------------------------------
# Story 2 of `2026-10-01-cross-family-review-panel`: `tally`, the output
# parser, the matching rule, and the mutation fixtures.
# --------------------------------------------------------------------------

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "review-panel"
OPENAI = "gpt-5.6-sol-medium"
OPENAI_2 = "gpt-5.6-terra-medium"
XAI = "cursor-grok-4.6-medium-fast"


def _fx(name: str) -> str:
    return str(FIXTURES / name)


def _tally(primary: str, *reviewers: Tuple[str, str], origin: str = ORIGIN,
           json_out: bool = False) -> Tuple[int, List[str]]:
    args = ["tally", "--origin", origin, "--primary", _fx(primary)]
    for slug, name in reviewers:
        args += ["--reviewer", "%s=%s" % (slug, _fx(name))]
    if json_out:
        args.append("--json")
    return _run(*args)


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


class TallyVerdictTests(unittest.TestCase):
    """AC-2.3, AC-2.4 — combination, printed lines, exit codes, drops, JSON."""

    def test_primary_and_one_panel_vendor_on_same_ac_blocks(self):
        rc, out = _tally("primary-fail-ac23.md", (OPENAI, "panel-ac23.md"))
        self.assertEqual(rc, 1)
        self.assertEqual(out[0], "block")
        self.assertIn("review-panel: block — AC-2.3 unmet (anthropic, openai)", out)
        self.assertTrue(out[-1].startswith("review-panel: block — 2 vendors, 1 consensus"),
                        out[-1])

    def test_single_panel_vendor_is_advisory_and_passes(self):
        rc, out = _tally("primary-pass.md", (OPENAI, "panel-ac23.md"))
        self.assertEqual(rc, 0)
        self.assertEqual(out[0], "pass")
        self.assertIn("review-panel: advisory — AC-2.3 unmet (openai)", out)
        self.assertEqual(out[-1], "review-panel: pass — 2 vendors, 0 consensus findings")

    def test_primary_only_key_is_not_printed(self):
        rc, out = _tally("primary-fail-ac23.md", (OPENAI, "panel-security-pay.md"))
        self.assertEqual(rc, 0)
        self.assertFalse(any("AC-2.3" in line for line in out), out)
        self.assertIn("review-panel: advisory — security app/api/pay.ts (openai)", out)

    def test_no_keys_is_pass(self):
        rc, out = _tally("primary-pass.md", (OPENAI, "panel-minor-security-pay.md"))
        self.assertEqual((rc, out[0]), (0, "pass"))
        self.assertEqual(out[-1], "review-panel: pass — 2 vendors, 0 consensus findings")

    def test_vendor_order_primary_first_then_reviewer_order(self):
        rc, out = _tally("primary-pass.md", (XAI, "panel-ac23.md"), (OPENAI, "panel-ac23.md"))
        self.assertEqual(rc, 1)
        self.assertIn("review-panel: block — AC-2.3 unmet (xai, openai)", out)

    def test_malformed_reviewer_dropped_and_rest_counted(self):
        rc, out = _tally("primary-fail-ac23.md", (XAI, "malformed.md"),
                         (OPENAI, "panel-ac23.md"))
        self.assertEqual(rc, 1)
        self.assertIn("review-panel: dropped %s — malformed_output" % XAI, out)
        self.assertIn("review-panel: block — AC-2.3 unmet (anthropic, openai)", out)

    def test_missing_or_empty_reviewer_output_dropped_no_output(self):
        with TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.md"
            empty.write_text("", encoding="utf-8")
            rc, out = _run("tally", "--origin", ORIGIN, "--primary", _fx("primary-pass.md"),
                           "--reviewer", "%s=%s" % (OPENAI, empty),
                           "--reviewer", "%s=%s" % (XAI, Path(tmp) / "missing.md"))
        self.assertEqual(rc, 0)
        self.assertIn("review-panel: dropped %s — no_output" % OPENAI, out)
        self.assertIn("review-panel: dropped %s — no_output" % XAI, out)
        self.assertEqual(out[0], "unverifiable")

    def test_zero_usable_reviewers_is_unverifiable(self):
        rc, out = _tally("primary-fail-ac23.md", (OPENAI, "malformed.md"))
        self.assertEqual(rc, 0)
        self.assertEqual(out[0], "unverifiable")
        self.assertIn("reason: no_usable_reviewer", out)
        self.assertEqual(out[-1], "review-panel: unverifiable — no_usable_reviewer")

    def test_unknown_vendor_reviewer_dropped(self):
        rc, out = _tally("primary-pass.md", ("foo-1", "panel-ac23.md"))
        self.assertIn("review-panel: dropped foo-1 — unknown_vendor", out)
        self.assertEqual(out[0], "unverifiable")

    def test_unknown_session_vendor_is_unverifiable(self):
        rc, out = _tally("primary-fail-ac23.md", (OPENAI, "panel-ac23.md"),
                         origin="Mystery Model 9")
        self.assertEqual(rc, 0)
        self.assertEqual(out[0], "unverifiable")
        self.assertIn("reason: unknown_session_vendor", out)

    def test_malformed_primary_exits_2(self):
        rc, _ = _tally("malformed.md", (OPENAI, "panel-ac23.md"))
        self.assertEqual(rc, 2)

    def test_missing_primary_exits_2(self):
        rc, _ = _run("tally", "--origin", ORIGIN, "--primary", _fx("nope.md"),
                     "--reviewer", "%s=%s" % (OPENAI, _fx("panel-ac23.md")))
        self.assertEqual(rc, 2)

    def test_reviewer_without_equals_exits_2(self):
        rc, _ = _run("tally", "--origin", ORIGIN, "--primary", _fx("primary-pass.md"),
                     "--reviewer", _fx("panel-ac23.md"))
        self.assertEqual(rc, 2)

    def test_json_has_per_key_vendors_and_original_text(self):
        rc, out = _tally("primary-fail-ac23.md", (OPENAI, "panel-ac23.md"),
                         (XAI, "panel-security-pay.md"), json_out=True)
        self.assertEqual(rc, 1)
        self.assertEqual(len(out), 1)
        payload = json.loads(out[0])
        self.assertEqual(payload["verdict"], "block")
        findings = {f["key"]: f for f in payload["findings"]}
        ac = findings["ac:AC-2.3"]
        self.assertEqual(ac["classification"], "consensus")
        self.assertEqual(ac["vendors"], ["anthropic", "openai"])
        sources = {t["source"]: t for t in ac["texts"]}
        self.assertIn("no test asserts the message", sources["primary"]["text"])
        self.assertIn("generic 500", sources[OPENAI]["text"])
        sec = findings["security:app/api/pay.ts"]
        self.assertEqual(sec["classification"], "advisory")
        self.assertEqual(sec["severity"], "Critical")
        self.assertIn("Card number is written", sec["texts"][0]["text"])
        self.assertEqual(payload["primary_verdict"], "FAIL")


class TallyMutationTests(unittest.TestCase):
    """AC-2.5 — the mutation fixtures: one vendor never blocks, two always do."""

    def test_single_vendor_finding_never_blocks(self):
        for fixture in ("panel-ac23.md", "panel-security-pay.md", "panel-architecture-pay.md",
                        "panel-multi-id.md"):
            rc, out = _tally("primary-pass.md", (OPENAI, fixture))
            self.assertEqual(rc, 0, fixture)
            self.assertEqual(out[0], "pass", fixture)
            self.assertFalse(any(l.startswith("review-panel: block") for l in out),
                             (fixture, out))

    def test_two_vendor_ac_finding_always_blocks(self):
        for primary, reviewers in (
            ("primary-fail-ac23.md", ((OPENAI, "panel-ac23.md"),)),
            ("primary-fail-ac23.md", ((XAI, "panel-multi-id.md"),)),
            ("primary-pass.md", ((OPENAI, "panel-ac23.md"), (XAI, "panel-multi-id.md"))),
        ):
            rc, out = _tally(primary, *reviewers)
            self.assertEqual(rc, 1, (primary, reviewers, out))
            self.assertTrue(any(l.startswith("review-panel: block — AC-2.3 unmet") for l in out))

    def test_two_panel_vendors_block_when_primary_passed(self):
        rc, out = _tally("primary-pass.md", (OPENAI, "panel-security-pay.md"),
                         (XAI, "panel-security-pay-b.md"))
        self.assertEqual(rc, 1)
        self.assertIn("review-panel: block — security app/api/pay.ts (openai, xai)", out)

    def test_same_file_different_category_is_no_consensus(self):
        rc, out = _tally("primary-pass.md", (OPENAI, "panel-security-pay.md"),
                         (XAI, "panel-architecture-pay.md"))
        self.assertEqual(rc, 0)
        self.assertIn("review-panel: advisory — security app/api/pay.ts (openai)", out)
        self.assertIn("review-panel: advisory — architecture app/api/pay.ts (xai)", out)

    def test_minor_security_from_two_vendors_is_no_consensus(self):
        rc, out = _tally("primary-pass.md", (OPENAI, "panel-minor-security-pay.md"),
                         (XAI, "panel-minor-security-pay.md"))
        self.assertEqual((rc, out[0]), (0, "pass"))
        self.assertFalse(any("advisory" in l or "block — security" in l for l in out))

    def test_two_reviewers_same_vendor_count_once(self):
        rc, out = _tally("primary-pass.md", (OPENAI, "panel-ac23.md"),
                         (OPENAI_2, "panel-ac23.md"))
        self.assertEqual(rc, 0)
        self.assertIn("review-panel: advisory — AC-2.3 unmet (openai)", out)
        self.assertEqual(out[-1], "review-panel: pass — 2 vendors, 0 consensus findings")

    def test_reviewer_with_session_vendor_does_not_fake_consensus(self):
        rc, out = _tally("primary-fail-ac23.md", ("claude-opus-5-thinking-high", "panel-ac23.md"))
        self.assertEqual(rc, 0)
        self.assertFalse(any(l.startswith("review-panel: block — AC") for l in out), out)
        self.assertEqual(out[0], "unverifiable")
        self.assertIn("reason: no_usable_reviewer", out)

    def test_session_vendor_reviewer_key_is_never_advisory(self):
        rc, out = _tally("primary-pass.md", ("claude-opus-5-thinking-high", "panel-ac23.md"),
                         (OPENAI, "panel-minor-security-pay.md"))
        self.assertEqual((rc, out[0]), (0, "pass"))
        self.assertFalse(any("advisory" in l for l in out), out)

    def test_placeholder_locations_from_two_vendors_never_block(self):
        rc, out = _tally("primary-pass.md", (OPENAI, "panel-subheadings-na.md"),
                         (XAI, "panel-subheadings-na.md"))
        self.assertEqual(rc, 1)
        self.assertEqual([l for l in out if l.startswith("review-panel: block — ")
                          and "consensus" not in l],
                         ["review-panel: block — security app/api/pay.ts (openai, xai)"])

    def test_malformed_reviewer_dropped_others_still_count(self):
        rc, out = _tally("primary-pass.md", (OPENAI, "malformed.md"),
                         (XAI, "panel-ac23.md"))
        self.assertEqual(rc, 0)
        self.assertIn("review-panel: dropped %s — malformed_output" % OPENAI, out)
        self.assertIn("review-panel: advisory — AC-2.3 unmet (xai)", out)


if __name__ == "__main__":
    unittest.main()

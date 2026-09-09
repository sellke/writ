#!/usr/bin/env python3
"""Tests for measure-invocation.py — per-invocation load measurement.

The tool exists because Phase 10's token success criterion reads
"measured **per-invocation load**, not just file size" and nothing measured
that. `eval-leanness.py` weighs the whole `commands/` directory; a command
invocation loads the root contract, the shared preamble, one command file,
and (only if declared) its `required_skills:`. Those are different numbers
and progressive disclosure only moves one of them.

Three families live here:

  1. **Byte accounting** — floor/ceiling/base arithmetic on fixture trees
     with known sizes, including the shared-base insight that disclosure
     cannot reduce, and the ghost-skill case where a declared skill has no
     file (counted as unresolved, never silently zero).

  2. **Labeling discipline (ADR-019)** — bytes are a measurement, tokens are
     an estimate unless a real tokenizer is present, and the output must say
     which it did. This is the half that settles roadmap caveat 1: chars/4
     was never validated against a tokenizer, and the tool must not launder
     an assumption into a number that reads like a measurement.

  3. **Validated counting (Phase 11 Story 2)** — with `ANTHROPIC_API_KEY`
     set, every measured text is counted by the Anthropic `count_tokens`
     endpoint (mocked here at `urllib.request.urlopen`), results are cached
     by content hash under `.writ/state/`, and a failed request degrades one
     item to the estimate rather than the whole run. Without the key the
     output must be byte-identical to the pre-story output except for
     `token_note`, so the no-key shape is pinned exactly.

`measure-invocation.py` has a hyphen in its filename, so it is loaded by path
via `importlib.util.spec_from_file_location` — the established recipe in
`test_archive_sweep.py`, `test_spec_status.py`, `test_story_deps.py` and
`test_eval_leanness_contract.py`.
"""

from __future__ import annotations

import contextlib
import http.client
import importlib.util
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
TARGET = os.path.join(SCRIPTS, "measure-invocation.py")

KEY_ENV = "ANTHROPIC_API_KEY"
FAKE_KEY = "sk-ant-fake-key-for-tests-only"


def _load():
    spec = importlib.util.spec_from_file_location("measure_invocation", TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mi = _load()


def env_without_key():
    """os.environ with ANTHROPIC_API_KEY removed — nothing else disturbed."""
    return {k: v for k, v in os.environ.items() if k != KEY_ENV}


def with_key(value=FAKE_KEY):
    return mock.patch.dict(os.environ, {KEY_ENV: value})


def without_key():
    return mock.patch.dict(os.environ, env_without_key(), clear=True)


class _FakeResponse:
    def __init__(self, payload: bytes, read_raises: BaseException | None = None):
        self._payload = payload
        self._read_raises = read_raises

    def read(self):
        if self._read_raises is not None:
            raise self._read_raises
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_count(text: str) -> int:
    """A count that is deterministic and never equals round(len/4), so a
    fallback to the estimate is always distinguishable from a real count."""
    return 1000 + len(text)


def fake_urlopen(decide=fake_count):
    """A stand-in for urllib.request.urlopen.

    `decide(text)` returns an int to answer with, or an exception instance to
    raise. Every call is recorded as (request, timeout) so tests can assert
    on the wire shape and the request count.
    """
    calls = []

    def _urlopen(request, timeout=None):
        calls.append((request, timeout))
        text = json.loads(request.data.decode("utf-8"))["messages"][0]["content"]
        result = decide(text)
        if isinstance(result, BaseException):
            raise result
        return _FakeResponse(json.dumps({"input_tokens": result}).encode("utf-8"))

    return _urlopen, calls


def http_error(code: int, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(mi.ANTHROPIC_COUNT_TOKENS_URL, code,
                                  f"HTTP {code}", {}, io.BytesIO(body))


def request_text(request) -> str:
    return json.loads(request.data.decode("utf-8"))["messages"][0]["content"]


def build_root(tmp, *, commands, skills=None, system_instructions="S" * 100,
               preamble="P" * 50):
    """A minimal product tree. `commands` maps stem -> file body."""
    os.makedirs(os.path.join(tmp, "commands"), exist_ok=True)
    if system_instructions is not None:
        with open(os.path.join(tmp, "system-instructions.md"), "w") as fh:
            fh.write(system_instructions)
    if preamble is not None:
        with open(os.path.join(tmp, "commands", "_preamble.md"), "w") as fh:
            fh.write(preamble)
    for stem, body in commands.items():
        with open(os.path.join(tmp, "commands", f"{stem}.md"), "w") as fh:
            fh.write(body)
    for name, body in (skills or {}).items():
        d = os.path.join(tmp, "skills", name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "SKILL.md"), "w") as fh:
            fh.write(body)
    return tmp


def fm(**fields):
    """A frontmatter block followed by body filler."""
    lines = ["---", "name: x", 'description: "d"']
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


class ByteAccounting(unittest.TestCase):

    def test_floor_is_base_plus_command(self):
        """Per-invocation floor = root contract + preamble + the command."""
        with tempfile.TemporaryDirectory() as tmp:
            body = fm() + "x" * 400
            build_root(tmp, commands={"alpha": body},
                       system_instructions="S" * 100, preamble="P" * 50)
            report = mi.measure(tmp)
            alpha = report["commands"]["alpha"]
            self.assertEqual(report["base"]["bytes"], 150)
            self.assertEqual(alpha["command_bytes"], len(body))
            self.assertEqual(alpha["floor_bytes"], 150 + len(body))

    def test_no_skills_at_all_means_ceiling_equals_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["conditional_bytes"], 0)
            self.assertEqual(alpha["eager_bytes"], 0)
            self.assertEqual(alpha["ceiling_bytes"], alpha["floor_bytes"])

    def test_required_skills_is_EAGER_and_lands_in_the_floor(self):
        """`required_skills:` pre-loads before phase 1 — it is not conditional.

        system-instructions.md: "the harness loads skills/foo/SKILL.md ... and
        makes it accessible to the agent before any phase work begins."
        adapters/claude-code.md:396 says the same. A declared skill is paid on
        every invocation, so it belongs in the floor. An earlier version of
        this module put it in `conditional_bytes`, which understated the floor
        and would have let progressive disclosure self-certify on a number
        nobody pays.
        """
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp,
                       commands={"alpha": fm(required_skills="[tdd-cycle]")},
                       skills={"tdd-cycle": "K" * 300})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["eager_bytes"], 300)
            self.assertIn(300, [alpha["floor_bytes"] - alpha["base_bytes"]
                                - alpha["command_bytes"]])
            self.assertEqual(alpha["conditional_bytes"], 0)

    def test_inline_read_is_CONDITIONAL_and_lands_above_the_floor(self):
        """`Read skills/<n>/SKILL.md` in the body loads only if reached."""
        with tempfile.TemporaryDirectory() as tmp:
            body = fm() + "\nGate 3 runs via `Read skills/tdd-cycle/SKILL.md` here.\n"
            build_root(tmp, commands={"alpha": body},
                       skills={"tdd-cycle": "K" * 300})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["conditional_bytes"], 300)
            self.assertEqual(alpha["eager_bytes"], 0)
            self.assertEqual(alpha["ceiling_bytes"], alpha["floor_bytes"] + 300)
            self.assertEqual(alpha["conditional_skills"], ["tdd-cycle"])

    def test_both_mechanisms_are_reported_separately(self):
        """A misclassified skill must be visible, never silently absorbed."""
        with tempfile.TemporaryDirectory() as tmp:
            body = fm(required_skills="[eagerly]") + "\n`Read skills/lazily/SKILL.md`\n"
            build_root(tmp, commands={"alpha": body},
                       skills={"eagerly": "E" * 200, "lazily": "L" * 500})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["eager_bytes"], 200)
            self.assertEqual(alpha["conditional_bytes"], 500)
            self.assertEqual(alpha["eager_skills"], ["eagerly"])
            self.assertEqual(alpha["conditional_skills"], ["lazily"])

    def test_skill_both_declared_and_inline_read_warns(self):
        """Declaring what you also inline-read pays for it unconditionally."""
        with tempfile.TemporaryDirectory() as tmp:
            body = fm(required_skills="[dup]") + "\n`Read skills/dup/SKILL.md`\n"
            build_root(tmp, commands={"alpha": body}, skills={"dup": "D" * 400})
            report = mi.measure(tmp)
            alpha = report["commands"]["alpha"]
            self.assertEqual(alpha["eager_bytes"], 400)
            self.assertEqual(alpha["conditional_bytes"], 0)  # not double-counted
            self.assertTrue(any("dup" in w and "both" in w.lower()
                                for w in report["warnings"]))

    def test_ghost_skill_is_unresolved_not_silently_zero(self):
        """A declared skill with no file must be visible, not absorbed."""
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp,
                       commands={"alpha": fm(required_skills="[ghost, real]")},
                       skills={"real": "R" * 120})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["unresolved_skills"], ["ghost"])
            self.assertEqual(alpha["eager_bytes"], 120)
            self.assertEqual(alpha["resolved_skills"], ["real"])

    def test_preamble_is_base_never_a_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            report = mi.measure(tmp)
            self.assertNotIn("_preamble", report["commands"])
            self.assertEqual(report["base"]["components"]["commands/_preamble.md"], 50)

    def test_missing_root_contract_degrades_without_crashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()}, system_instructions=None)
            report = mi.measure(tmp)
            self.assertEqual(report["base"]["components"]["system-instructions.md"], 0)
            self.assertIn("system-instructions.md", report["warnings"][0])

    def test_shared_base_is_the_floor_disclosure_cannot_reduce(self):
        """Reported explicitly: the irreducible cost of any invocation."""
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"a": fm() + "x" * 900, "b": fm()},
                       system_instructions="S" * 200, preamble="P" * 100)
            report = mi.measure(tmp)
            self.assertEqual(report["base"]["bytes"], 300)
            self.assertEqual(report["corpus"]["irreducible_base_bytes"], 300)
            self.assertLess(report["corpus"]["min_floor_bytes"],
                            report["corpus"]["max_floor_bytes"])


class CorpusSummary(unittest.TestCase):

    def test_distribution_reports_min_median_max(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={
                "a": fm() + "x" * 100,
                "b": fm() + "x" * 200,
                "c": fm() + "x" * 300,
            }, system_instructions="", preamble="")
            corpus = mi.measure(tmp)["corpus"]
            self.assertEqual(corpus["commands_measured"], 3)
            floors = sorted(
                mi.measure(tmp)["commands"][k]["floor_bytes"] for k in "abc")
            self.assertEqual(corpus["min_floor_bytes"], floors[0])
            self.assertEqual(corpus["median_floor_bytes"], floors[1])
            self.assertEqual(corpus["max_floor_bytes"], floors[2])

    def test_worst_offender_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"small": fm(), "huge": fm() + "x" * 5000})
            self.assertEqual(mi.measure(tmp)["corpus"]["max_floor_command"], "huge")


class LabelingDiscipline(unittest.TestCase):
    """ADR-019: never report an estimate as a measurement."""

    def test_bytes_and_tokens_are_separately_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertIn("floor_bytes", alpha)
            self.assertIn("floor_tokens_estimated", alpha)
            self.assertNotIn("floor_tokens", alpha)

    def test_method_records_estimate_and_divisor(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            report = mi.measure(tmp, chars_per_token=4.0)
            self.assertEqual(report["token_method"], "estimate:chars/4.0")
            self.assertEqual(report["chars_per_token"], 4.0)

    def test_divisor_is_overridable(self):
        """chars/4 is an assumption; the tool must let it be calibrated."""
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm() + "x" * 800})
            four = mi.measure(tmp, chars_per_token=4.0)
            three = mi.measure(tmp, chars_per_token=3.0)
            self.assertEqual(four["commands"]["alpha"]["floor_bytes"],
                             three["commands"]["alpha"]["floor_bytes"])
            self.assertGreater(three["commands"]["alpha"]["floor_tokens_estimated"],
                               four["commands"]["alpha"]["floor_tokens_estimated"])

    def test_estimate_carries_an_honest_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            note = mi.measure(tmp)["token_note"]
            self.assertIn("not", note.lower())
            self.assertIn("tokeniz", note.lower())

    def test_unvalidated_divisor_is_flagged_as_unvalidated(self):
        """The roadmap's chars/4 was never checked against a tokenizer."""
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            self.assertFalse(mi.measure(tmp)["token_method_validated"])


class LineCounts(unittest.TestCase):
    """The 400-line cap was derived from a distribution, not an impact."""

    def test_lines_reported_alongside_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = fm() + "\n".join("line" for _ in range(40)) + "\n"
            build_root(tmp, commands={"alpha": body})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["command_lines"], body.count("\n"))

    def test_bytes_per_line_enables_cap_calibration(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm() + "y" * 100 + "\n"})
            corpus = mi.measure(tmp)["corpus"]
            self.assertIn("mean_bytes_per_command_line", corpus)
            self.assertGreater(corpus["mean_bytes_per_command_line"], 0)


class CommandLineInterface(unittest.TestCase):

    def _run(self, *args):
        # The key is stripped so a maintainer who has ANTHROPIC_API_KEY set
        # does not fire real count_tokens requests from the test suite.
        return subprocess.run([sys.executable, TARGET, *args],
                              capture_output=True, text=True,
                              env=env_without_key())

    def test_emits_one_json_object_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            proc = self._run("--root", tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertIn("commands", payload)

    def test_single_command_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm(), "beta": fm()})
            payload = json.loads(self._run("--root", tmp, "--command", "alpha").stdout)
            self.assertEqual(list(payload["commands"]), ["alpha"])

    def test_absent_root_exits_zero_with_a_warning(self):
        """Read-only measurement never blocks a caller."""
        proc = self._run("--root", "/nonexistent-root-xyz")
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(json.loads(proc.stdout)["warnings"])

    def test_table_mode_is_human_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            proc = self._run("--root", tmp, "--format", "table")
            self.assertEqual(proc.returncode, 0)
            self.assertIn("alpha", proc.stdout)
            self.assertIn("floor", proc.stdout.lower())

    def test_tokenizer_model_and_cache_flags_are_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            proc = self._run("--root", tmp, "--tokenizer", "estimate",
                             "--model", "claude-fable-5-1",
                             "--cache", os.path.join(tmp, "c.json"))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["token_method"], "estimate:chars/4.0")
            self.assertNotIn("token_model", payload)
            self.assertFalse(os.path.exists(os.path.join(tmp, "c.json")))

    def test_explicit_anthropic_without_key_still_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            proc = self._run("--root", tmp, "--tokenizer", "anthropic")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertFalse(payload["token_method_validated"])
            self.assertTrue(any(KEY_ENV in w for w in payload["warnings"]))

    def _main(self, *argv):
        """main() in-process so a fake key and a mocked urlopen can be
        installed — the subprocess runner strips the key on purpose."""
        out = io.StringIO()
        with mock.patch.object(sys, "argv", [TARGET, *argv]), \
                contextlib.redirect_stdout(out):
            rc = mi.main()
        return rc, out.getvalue()

    def test_main_routes_tokenizer_model_cache_and_divisor_into_measure(self):
        """AC-2.5: --model reaches the request body AND the cache key;
        --cache relocates the file; --chars-per-token is the fallback divisor."""
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            custom = os.path.join(tmp, "elsewhere", "counts.json")
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                rc, stdout = self._main("--root", tmp, "--tokenizer", "anthropic",
                                        "--model", "claude-other-9",
                                        "--cache", custom, "--chars-per-token", "3")
            self.assertEqual(rc, 0)
            payload = json.loads(stdout)
            self.assertEqual(payload["token_model"], "claude-other-9")
            self.assertEqual(payload["chars_per_token"], 3.0)
            self.assertIs(payload["token_method_validated"], True)
            self.assertEqual(len(calls), 5)
            for request, _ in calls:
                self.assertEqual(json.loads(request.data)["model"], "claude-other-9")
            with open(custom) as fh:
                cache = json.load(fh)
            self.assertEqual(cache[mi.token_cache_key("claude-other-9", SYS)],
                             fake_count(SYS))
            self.assertNotIn(mi.token_cache_key("claude-fable-5-1", SYS), cache)
            self.assertFalse(os.path.exists(os.path.join(tmp, ".writ")))

    def test_main_table_format_with_a_key_names_the_model(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            urlopen, _ = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                rc, stdout = self._main("--root", tmp, "--format", "table")
            self.assertEqual(rc, 0)
            self.assertIn("anthropic-count-tokens [claude-fable-5-1]", stdout)
            self.assertNotIn(FAKE_KEY, stdout)


# ---------------------------------------------------------------------------
# Family 3: validated counting via the Anthropic count_tokens endpoint.
# ---------------------------------------------------------------------------

# The top-level key set the estimate path emitted before Phase 11 Story 2.
# AC-2.2 says the no-key output is byte-identical to that output except for
# `token_note`, so this set — and only this set — may appear without a key.
PRE_STORY_TOP_KEYS = [
    "schema", "root", "token_method", "token_method_validated",
    "chars_per_token", "token_note", "ceiling_note", "base", "commands",
    "corpus", "warnings",
]
PRE_STORY_COMMAND_KEYS = [
    "command_bytes", "command_lines", "base_bytes", "eager_bytes",
    "floor_bytes", "conditional_bytes", "ceiling_bytes", "eager_skills",
    "conditional_skills", "hoisted_skills", "resolved_skills",
    "unresolved_skills", "floor_tokens_estimated", "ceiling_tokens_estimated",
    "base_share_of_floor",
]
PRE_STORY_CORPUS_KEYS = [
    "commands_measured", "irreducible_base_bytes",
    "irreducible_base_tokens_estimated", "min_floor_bytes",
    "median_floor_bytes", "max_floor_bytes", "max_floor_command",
    "mean_bytes_per_command_line",
]

SYS = "S" * 100
PRE = "P" * 50
EAGER = "E" * 200
LAZY = "L" * 500


ALPHA = fm(required_skills="[eagerly]") + "\n## Step 1\n\n`Read skills/lazily/SKILL.md`\n"


def build_counting_root(tmp):
    """One command with one eager and one conditional skill: five distinct
    texts (two base, one command, two skills)."""
    build_root(tmp, commands={"alpha": ALPHA},
               skills={"eagerly": EAGER, "lazily": LAZY},
               system_instructions=SYS, preamble=PRE)
    return ALPHA


class AnthropicCounting(unittest.TestCase):
    """AC-2.1: with a key, every text is counted by the API and the report
    says so."""

    def test_every_request_is_a_post_to_count_tokens_with_the_three_headers(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                mi.measure(tmp)
            self.assertTrue(calls)
            for request, timeout in calls:
                self.assertEqual(request.full_url, mi.ANTHROPIC_COUNT_TOKENS_URL)
                self.assertEqual(request.full_url,
                                 "https://api.anthropic.com/v1/messages/count_tokens")
                self.assertEqual(request.get_method(), "POST")
                self.assertEqual(request.get_header("X-api-key"), FAKE_KEY)
                self.assertEqual(request.get_header("Anthropic-version"),
                                 mi.ANTHROPIC_VERSION)
                self.assertEqual(request.get_header("Content-type"),
                                 "application/json")
                self.assertEqual(timeout, mi.REQUEST_TIMEOUT_SECONDS)
                body = json.loads(request.data.decode("utf-8"))
                self.assertEqual(sorted(body), ["messages", "model"])
                self.assertEqual(body["model"], "claude-fable-5-1")
                self.assertEqual(len(body["messages"]), 1)
                self.assertEqual(body["messages"][0]["role"], "user")
                self.assertIsInstance(body["messages"][0]["content"], str)

    def test_token_figures_are_sums_of_the_component_counts(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            body = build_counting_root(tmp)
            urlopen, _ = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            alpha = report["commands"]["alpha"]
            base = fake_count(SYS) + fake_count(PRE)
            floor = base + fake_count(body) + fake_count(EAGER)
            self.assertEqual(report["corpus"]["irreducible_base_tokens_estimated"], base)
            self.assertEqual(alpha["floor_tokens_estimated"], floor)
            self.assertEqual(alpha["ceiling_tokens_estimated"], floor + fake_count(LAZY))
            self.assertEqual(report["token_method"], "anthropic-count-tokens")
            self.assertIs(report["token_method_validated"], True)
            self.assertEqual(report["token_model"], "claude-fable-5-1")
            self.assertEqual(report["token_failures"], 0)
            self.assertIn("claude-fable-5-1", report["token_note"])

    def test_model_override_is_sent_and_reported(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp, model="claude-other-9")
            self.assertEqual(report["token_model"], "claude-other-9")
            for request, _ in calls:
                self.assertEqual(json.loads(request.data)["model"], "claude-other-9")

    def test_each_distinct_text_is_requested_exactly_once(self):
        """Base files are counted once and reused; a skill shared by two
        commands is one request, not two. 2 base + 2 commands + 1 skill = 5."""
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_root(tmp, commands={
                "alpha": fm(required_skills="[shared]") + "a",
                "beta": fm(required_skills="[shared]") + "b",
            }, skills={"shared": "K" * 300})
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            self.assertEqual(len(calls), 5)
            self.assertEqual(len({request_text(r) for r, _ in calls}), 5)
            self.assertEqual(report["token_failures"], 0)

    def test_empty_text_is_zero_tokens_and_no_request(self):
        """Technical spec §8: empty input -> 0 tokens, no request."""
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_root(tmp, commands={"alpha": fm(required_skills="[void]")},
                       skills={"void": ""})
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            self.assertNotIn("", [request_text(r) for r, _ in calls])
            alpha = report["commands"]["alpha"]
            self.assertEqual(alpha["eager_bytes"], 0)
            self.assertEqual(alpha["floor_tokens_estimated"],
                             fake_count("S" * 100) + fake_count("P" * 50)
                             + fake_count(fm(required_skills="[void]")))
            self.assertEqual(report["token_failures"], 0)

    def test_undecodable_text_is_zero_tokens_and_no_request(self):
        """Technical spec §8 (unreadable -> 0): bytes are still measured, but
        a file that is not UTF-8 cannot be sent as message content, so it
        contributes 0 tokens, no request, and is not a failure."""
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_root(tmp, commands={"alpha": fm(required_skills="[binary]")})
            skill_dir = os.path.join(tmp, "skills", "binary")
            os.makedirs(skill_dir)
            with open(os.path.join(skill_dir, "SKILL.md"), "wb") as fh:
                fh.write(b"\xff\xfe\xfd\xfc")
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            alpha = report["commands"]["alpha"]
            self.assertEqual(alpha["eager_bytes"], 4)
            self.assertEqual(len(calls), 3)  # 2 base + the command; not the skill
            self.assertEqual(alpha["floor_tokens_estimated"],
                             fake_count("S" * 100) + fake_count("P" * 50)
                             + fake_count(fm(required_skills="[binary]")))
            self.assertEqual(report["token_failures"], 0)
            self.assertIs(report["token_method_validated"], True)

    def test_unknown_tokenizer_is_rejected_before_any_work(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                with self.assertRaises(ValueError):
                    mi.measure(tmp, tokenizer="bogus")
            self.assertEqual(calls, [])
            self.assertFalse(os.path.exists(os.path.join(tmp, ".writ")))

    def test_key_appears_nowhere_in_the_report(self):
        """Business Rule 3."""
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            urlopen, _ = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            self.assertNotIn(FAKE_KEY, json.dumps(report))

    def test_key_beats_tiktoken_under_auto(self):
        """Story Notes: with a key, the API wins over an installed tiktoken."""
        fake_enc = mock.Mock()
        fake_enc.encode.return_value = [0] * 7
        with tempfile.TemporaryDirectory() as tmp, with_key(), \
                mock.patch.object(mi, "_tokenizer",
                                  return_value=(fake_enc, "cl100k_base")):
            build_counting_root(tmp)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            self.assertEqual(report["token_method"], "anthropic-count-tokens")
            self.assertTrue(calls)

    def test_table_header_names_the_model_when_the_api_ran(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            urlopen, _ = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                table = mi.render_table(mi.measure(tmp))
            header = table.splitlines()[1]
            self.assertIn("anthropic-count-tokens", header)
            self.assertIn("claude-fable-5-1", header)


class NoKeyIsTodaysOutput(unittest.TestCase):
    """AC-2.2: without the key, nothing but `token_note` may change."""

    def test_auto_without_key_is_the_estimate_and_the_note_names_the_env_var(self):
        with tempfile.TemporaryDirectory() as tmp, without_key(), \
                mock.patch.object(mi, "_tokenizer", return_value=None):
            build_counting_root(tmp)
            auto = mi.measure(tmp)
            estimate = mi.measure(tmp, tokenizer="estimate")
            self.assertEqual(json.dumps(auto, indent=2), json.dumps(estimate, indent=2))
            self.assertIn(KEY_ENV, auto["token_note"])
            self.assertEqual(auto["token_method"], "estimate:chars/4.0")
            self.assertIs(auto["token_method_validated"], False)

    def test_no_http_call_is_attempted_without_a_key(self):
        with tempfile.TemporaryDirectory() as tmp, without_key():
            build_counting_root(tmp)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                mi.measure(tmp)
                mi.measure(tmp, tokenizer="estimate")
            self.assertEqual(calls, [])

    def test_no_key_path_has_zero_side_effects(self):
        """Shadow path (nil input): no cache file, no `.writ/state/` created."""
        with tempfile.TemporaryDirectory() as tmp, without_key():
            build_counting_root(tmp)
            mi.measure(tmp)
            mi.measure(tmp, tokenizer="anthropic")
            self.assertFalse(os.path.exists(os.path.join(tmp, ".writ")))

    def test_estimate_figures_are_still_computed_on_byte_sums(self):
        """The estimate branch rounds the aggregate, not per-file sums —
        round(a+b) != round(a)+round(b), so this is what byte-identity needs."""
        with tempfile.TemporaryDirectory() as tmp, without_key(), \
                mock.patch.object(mi, "_tokenizer", return_value=None):
            body = fm() + "x" * 401  # odd sizes so per-item rounding would differ
            build_root(tmp, commands={"alpha": body},
                       system_instructions="S" * 101, preamble="P" * 51)
            report = mi.measure(tmp, chars_per_token=4.0)
            alpha = report["commands"]["alpha"]
            self.assertEqual(alpha["floor_tokens_estimated"],
                             int(round(alpha["floor_bytes"] / 4.0)))
            self.assertEqual(report["corpus"]["irreducible_base_tokens_estimated"],
                             int(round(152 / 4.0)))

    def test_estimate_rounds_the_aggregate_not_the_sum_of_per_text_rounds(self):
        """Sizes chosen so the two strategies disagree: 100 + 50 bytes at
        chars/4 is 25 + round(12.5)=12 = 37 per text, but round(37.5) = 38 on
        the aggregate. HEAD rounds the aggregate; AC-2.2 says the no-key
        output must not move by a single byte, so neither may this."""
        with tempfile.TemporaryDirectory() as tmp, without_key(), \
                mock.patch.object(mi, "_tokenizer", return_value=None):
            body = fm() + "x" * 7  # 40 bytes -> exactly 10, so only the base splits
            self.assertEqual(len(body), 40)
            build_root(tmp, commands={"alpha": body},
                       system_instructions="S" * 100, preamble="P" * 50)
            report = mi.measure(tmp, chars_per_token=4.0)
            alpha = report["commands"]["alpha"]
            self.assertEqual(report["corpus"]["irreducible_base_tokens_estimated"], 38)
            self.assertEqual(alpha["floor_tokens_estimated"], 48)    # round(190/4)
            self.assertEqual(alpha["ceiling_tokens_estimated"], 48)  # not 25+12+10

    def test_table_header_omits_model_and_failures_without_a_key(self):
        with tempfile.TemporaryDirectory() as tmp, without_key(), \
                mock.patch.object(mi, "_tokenizer", return_value=None):
            build_root(tmp, commands={"alpha": fm()}, system_instructions=None)
            table = mi.render_table(mi.measure(tmp))
            header = table.splitlines()[1]
            self.assertEqual(header,
                             "token method: estimate:chars/4.0  (validated: False)")
            self.assertNotIn("token_failures", table)
            self.assertIn("WARNING: system-instructions.md", table)

    def test_pre_story_shape_is_pinned_exactly(self):
        with tempfile.TemporaryDirectory() as tmp, without_key(), \
                mock.patch.object(mi, "_tokenizer", return_value=None):
            build_counting_root(tmp)
            report = mi.measure(tmp)
            self.assertEqual(list(report), PRE_STORY_TOP_KEYS)
            self.assertEqual(list(report["commands"]["alpha"]), PRE_STORY_COMMAND_KEYS)
            self.assertEqual(list(report["corpus"]), PRE_STORY_CORPUS_KEYS)
            self.assertNotIn("token_model", report)
            self.assertNotIn("token_failures", report)

    def test_explicit_anthropic_without_key_warns_and_estimates(self):
        with tempfile.TemporaryDirectory() as tmp, without_key(), \
                mock.patch.object(mi, "_tokenizer", return_value=None):
            build_counting_root(tmp)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp, tokenizer="anthropic")
            self.assertEqual(calls, [])
            self.assertEqual(report["token_method"], "estimate:chars/4.0")
            self.assertTrue(any(KEY_ENV in w for w in report["warnings"]))
            self.assertNotIn("token_model", report)


class TokenizerSelection(unittest.TestCase):
    """AC-2.5 / DEV-017: `estimate` is chars/N regardless of what is
    installed; `auto` without a key is exactly the pre-story behaviour,
    tiktoken fallback included."""

    def _fake_encoder(self):
        enc = mock.Mock()
        enc.encode.return_value = [0] * 7
        return enc

    def test_estimate_bypasses_an_installed_tiktoken(self):
        enc = self._fake_encoder()
        with tempfile.TemporaryDirectory() as tmp, without_key(), \
                mock.patch.object(mi, "_tokenizer",
                                  return_value=(enc, "cl100k_base")) as tok:
            build_counting_root(tmp)
            report = mi.measure(tmp, tokenizer="estimate")
        self.assertEqual(report["token_method"], "estimate:chars/4.0")
        self.assertIs(report["token_method_validated"], False)
        self.assertIn(KEY_ENV, report["token_note"])
        tok.assert_not_called()
        enc.encode.assert_not_called()

    def test_estimate_bypasses_the_api_even_with_a_key(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp, tokenizer="estimate")
        self.assertEqual(calls, [])
        self.assertEqual(report["token_method"], "estimate:chars/4.0")
        self.assertNotIn("token_model", report)
        self.assertFalse(os.path.exists(os.path.join(tmp, ".writ")))

    def test_auto_without_key_keeps_the_tiktoken_fallback(self):
        """Story Notes: tiktoken remains the no-key fallback exactly as
        today. Labels only — the pre-existing branch's arithmetic is not
        this story's to change (see What Was Built)."""
        with tempfile.TemporaryDirectory() as tmp, without_key(), \
                mock.patch.object(mi, "_tokenizer",
                                  return_value=(self._fake_encoder(), "cl100k_base")):
            build_counting_root(tmp)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
        self.assertEqual(calls, [])
        self.assertEqual(report["token_method"], "tokenizer:cl100k_base")
        self.assertIn("cl100k_base", report["token_note"])
        self.assertEqual(list(report), PRE_STORY_TOP_KEYS)
        self.assertNotIn("token_model", report)
        self.assertNotIn("token_failures", report)


class TokenCaching(unittest.TestCase):
    """AC-2.3: content-hash cache under `.writ/state/`, hashes and ints only."""

    def _cache_path(self, tmp):
        return os.path.join(tmp, ".writ", "state", "token-cache.json")

    def test_seeded_hash_skips_the_request_and_the_rest_are_written_back(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            body = build_counting_root(tmp)
            os.makedirs(os.path.dirname(self._cache_path(tmp)))
            seeded_key = mi.token_cache_key("claude-fable-5-1", SYS)
            with open(self._cache_path(tmp), "w") as fh:
                json.dump({seeded_key: 999}, fh)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            requested = [request_text(r) for r, _ in calls]
            self.assertNotIn(SYS, requested)
            self.assertEqual(len(calls), 4)
            self.assertEqual(report["corpus"]["irreducible_base_tokens_estimated"],
                             999 + fake_count(PRE))
            with open(self._cache_path(tmp)) as fh:
                raw = fh.read()
            cache = json.loads(raw)
            self.assertEqual(cache[seeded_key], 999)
            for text in (PRE, body, EAGER, LAZY):
                self.assertEqual(cache[mi.token_cache_key("claude-fable-5-1", text)],
                                 fake_count(text))
            self.assertEqual(len(cache), 5)

    def test_cache_file_holds_only_hashes_and_integer_counts(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            body = build_counting_root(tmp)
            urlopen, _ = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                mi.measure(tmp)
            with open(self._cache_path(tmp)) as fh:
                raw = fh.read()
            cache = json.loads(raw)
            for key, value in cache.items():
                self.assertRegex(key, r"^[0-9a-f]{64}$")
                self.assertIsInstance(value, int)
                self.assertNotIsInstance(value, bool)
            self.assertNotIn(FAKE_KEY, raw)
            self.assertNotIn("claude-fable-5-1", raw)
            for text in (SYS, PRE, body, EAGER, LAZY):
                self.assertNotIn(text, raw)

    def test_cache_key_is_sha256_of_model_nul_text(self):
        """Story task 2.3 pins the separator as NUL — a model change never
        returns a stale count."""
        import hashlib
        expected = hashlib.sha256("m\0t".encode("utf-8")).hexdigest()
        self.assertEqual(mi.token_cache_key("m", "t"), expected)
        self.assertNotEqual(mi.token_cache_key("a", "b"), mi.token_cache_key("ab", ""))

    def test_a_different_model_misses_the_cache(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                mi.measure(tmp)
                first = len(calls)
                mi.measure(tmp, model="claude-other-9")
            self.assertEqual(len(calls), 2 * first)

    def test_second_run_over_an_unchanged_tree_makes_zero_requests(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                first = mi.measure(tmp)
                del calls[:]
                second = mi.measure(tmp)
            self.assertEqual(calls, [])
            self.assertEqual(first["commands"], second["commands"])

    def test_malformed_cache_starts_empty_and_is_replaced(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            os.makedirs(os.path.dirname(self._cache_path(tmp)))
            with open(self._cache_path(tmp), "w") as fh:
                fh.write("{not json")
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            self.assertEqual(len(calls), 5)
            self.assertEqual(report["token_failures"], 0)
            with open(self._cache_path(tmp)) as fh:
                self.assertEqual(len(json.load(fh)), 5)

    def test_fully_seeded_cache_makes_zero_requests_and_leaves_the_file_alone(self):
        """Cache hit for every text: 0 requests, seeded figures reported as
        real counts, validated stays true, and the file is not rewritten."""
        with tempfile.TemporaryDirectory() as tmp, with_key():
            body = build_counting_root(tmp)
            os.makedirs(os.path.dirname(self._cache_path(tmp)))
            seeded = {mi.token_cache_key("claude-fable-5-1", t): 100 + i
                      for i, t in enumerate((SYS, PRE, body, EAGER, LAZY))}
            with open(self._cache_path(tmp), "w") as fh:
                json.dump(seeded, fh)  # deliberately not the flush() format
            with open(self._cache_path(tmp), "rb") as fh:
                before = fh.read()
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            self.assertEqual(calls, [])
            self.assertEqual(report["corpus"]["irreducible_base_tokens_estimated"], 201)
            self.assertEqual(report["commands"]["alpha"]["floor_tokens_estimated"],
                             100 + 101 + 102 + 103)
            self.assertEqual(report["commands"]["alpha"]["ceiling_tokens_estimated"],
                             100 + 101 + 102 + 103 + 104)
            self.assertIs(report["token_method_validated"], True)
            self.assertEqual(report["token_failures"], 0)
            self.assertFalse(any("cache" in w.lower() for w in report["warnings"]))
            with open(self._cache_path(tmp), "rb") as fh:
                self.assertEqual(fh.read(), before)

    def test_cache_that_is_not_a_json_object_starts_empty(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            os.makedirs(os.path.dirname(self._cache_path(tmp)))
            with open(self._cache_path(tmp), "w") as fh:
                json.dump([1, 2, 3], fh)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            self.assertEqual(len(calls), 5)
            self.assertEqual(report["token_failures"], 0)
            with open(self._cache_path(tmp)) as fh:
                cache = json.load(fh)
            self.assertEqual(len(cache), 5)
            self.assertIsInstance(cache, dict)

    def test_non_integer_cache_values_are_ignored_not_trusted(self):
        """A string, a bool, or a non-string key is not a count; only the
        well-formed entry is honoured, the rest are re-requested."""
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            os.makedirs(os.path.dirname(self._cache_path(tmp)))
            k = lambda t: mi.token_cache_key("claude-fable-5-1", t)  # noqa: E731
            with open(self._cache_path(tmp), "w") as fh:
                json.dump({k(SYS): "9", k(PRE): True, k(EAGER): 7,
                           k(LAZY): 3.5}, fh)
            urlopen, calls = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            requested = {request_text(r) for r, _ in calls}
            self.assertEqual(requested, {SYS, PRE, ALPHA, LAZY})
            self.assertEqual(report["commands"]["alpha"]["floor_tokens_estimated"],
                             fake_count(SYS) + fake_count(PRE) + fake_count(ALPHA) + 7)
            with open(self._cache_path(tmp)) as fh:
                cache = json.load(fh)
            self.assertEqual(cache[k(SYS)], fake_count(SYS))
            self.assertEqual(cache[k(EAGER)], 7)
            self.assertEqual(len(cache), 5)

    def test_cache_path_is_overridable(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            custom = os.path.join(tmp, "elsewhere", "counts.json")
            urlopen, _ = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                mi.measure(tmp, cache_path=custom)
            self.assertTrue(os.path.isfile(custom))
            self.assertFalse(os.path.exists(self._cache_path(tmp)))

    def test_unwritable_cache_degrades_with_a_warning_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            blocker = os.path.join(tmp, "blocker")
            with open(blocker, "w") as fh:
                fh.write("a regular file where a directory is needed")
            urlopen, _ = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp, cache_path=os.path.join(blocker, "c.json"))
            self.assertEqual(report["token_failures"], 0)
            self.assertTrue(any("cache" in w.lower() for w in report["warnings"]))

    def test_flush_is_a_no_op_when_nothing_new_was_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "c.json")
            cache = mi.TokenCache(path)
            self.assertFalse(cache.flush())
            self.assertFalse(os.path.exists(path))
            cache.put("m", "t", 3)
            self.assertTrue(cache.flush())
            self.assertFalse(cache.flush())
            self.assertEqual(mi.TokenCache(path).get("m", "t"), 3)

    def test_failed_counts_are_not_cached(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            urlopen, _ = fake_urlopen(
                lambda text: urllib.error.URLError("down") if text == LAZY
                else fake_count(text))
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                mi.measure(tmp)
            with open(self._cache_path(tmp)) as fh:
                cache = json.load(fh)
            self.assertNotIn(mi.token_cache_key("claude-fable-5-1", LAZY), cache)
            self.assertEqual(len(cache), 4)


class Degradation(unittest.TestCase):
    """AC-2.4: a failed request degrades one item, never the run."""

    def _measure_with(self, decide):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            body = build_counting_root(tmp)
            urlopen, calls = fake_urlopen(decide)
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
        return report, calls, body

    def test_urlerror_on_some_texts_falls_back_per_item(self):
        report, _, body = self._measure_with(
            lambda text: urllib.error.URLError("connection refused")
            if text == ALPHA else fake_count(text))
        alpha = report["commands"]["alpha"]
        base = fake_count(SYS) + fake_count(PRE)
        self.assertEqual(alpha["floor_tokens_estimated"],
                         base + int(round(len(body) / 4.0)) + fake_count(EAGER))
        self.assertEqual(alpha["ceiling_tokens_estimated"],
                         alpha["floor_tokens_estimated"] + fake_count(LAZY))
        self.assertEqual(report["token_method"], "anthropic-count-tokens")
        self.assertIs(report["token_method_validated"], False)
        self.assertEqual(report["token_failures"], 1)
        self.assertIn("commands/alpha.md", report["token_note"])
        self.assertNotIn("skills/lazily/SKILL.md", report["token_note"])

    def test_timeout_is_one_failure(self):
        report, calls, _ = self._measure_with(
            lambda text: socket.timeout("timed out") if text == LAZY
            else fake_count(text))
        self.assertEqual(report["token_failures"], 1)
        self.assertEqual(len(calls), 5)  # the run continued past the failure
        self.assertIn("skills/lazily/SKILL.md", report["token_note"])

    def test_http_529_is_one_failure_and_the_run_continues(self):
        report, calls, _ = self._measure_with(
            lambda text: http_error(529, b'{"error":"overloaded"}')
            if text == SYS else fake_count(text))
        self.assertEqual(report["token_failures"], 1)
        self.assertEqual(len(calls), 5)
        self.assertIn("system-instructions.md", report["token_note"])

    def test_http_429_and_500_are_one_failure_each_and_the_run_continues(self):
        """Tech spec §7: HTTP 4xx/5xx other than auth degrade the item and
        never stop the run."""
        for code in (429, 500):
            with self.subTest(code=code):
                report, calls, body = self._measure_with(
                    lambda text, code=code: http_error(code, b'{"error":"x"}')
                    if text == ALPHA else fake_count(text))
                self.assertEqual(len(calls), 5)
                self.assertEqual(report["token_failures"], 1)
                self.assertIs(report["token_method_validated"], False)
                self.assertIn(f"HTTP {code}", report["token_note"])
                self.assertIn("commands/alpha.md", report["token_note"])
                self.assertEqual(report["commands"]["alpha"]["floor_tokens_estimated"],
                                 fake_count(SYS) + fake_count(PRE)
                                 + int(round(len(body) / 4.0)) + fake_count(EAGER))
                self.assertFalse(any("No further" in w for w in report["warnings"]))

    def test_non_json_and_non_integer_bodies_each_degrade_one_item(self):
        def _urlopen(request, timeout=None):
            text = request_text(request)
            if text == LAZY:
                return _FakeResponse(b"<html>gateway</html>")
            if text == EAGER:
                return _FakeResponse(b'{"input_tokens": "9"}')
            return _FakeResponse(json.dumps({"input_tokens": fake_count(text)}).encode())
        with tempfile.TemporaryDirectory() as tmp, with_key():
            body = build_counting_root(tmp)
            with mock.patch("urllib.request.urlopen", side_effect=_urlopen):
                report = mi.measure(tmp)
        alpha = report["commands"]["alpha"]
        self.assertEqual(report["token_failures"], 2)
        self.assertIs(report["token_method_validated"], False)
        self.assertIn("skills/eagerly/SKILL.md", report["token_note"])
        self.assertIn("skills/lazily/SKILL.md", report["token_note"])
        base = fake_count(SYS) + fake_count(PRE)
        self.assertEqual(alpha["floor_tokens_estimated"],
                         base + fake_count(body) + int(round(len(EAGER) / 4.0)))
        self.assertEqual(alpha["ceiling_tokens_estimated"],
                         alpha["floor_tokens_estimated"] + int(round(len(LAZY) / 4.0)))

    def test_per_item_fallback_uses_the_requested_divisor(self):
        """The fallback is `round(len_bytes / chars_per_token)` for the
        failed text only — with the caller's divisor, not the default."""
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            urlopen, _ = fake_urlopen(
                lambda text: urllib.error.URLError("down") if text == LAZY
                else fake_count(text))
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp, chars_per_token=3.0)
        alpha = report["commands"]["alpha"]
        self.assertEqual(report["chars_per_token"], 3.0)
        self.assertEqual(alpha["ceiling_tokens_estimated"] - alpha["floor_tokens_estimated"],
                         int(round(500 / 3.0)))  # 167, not 125

    def test_malformed_response_is_one_failure(self):
        def _urlopen(request, timeout=None):
            return _FakeResponse(b'{"unexpected": true}')
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            with mock.patch("urllib.request.urlopen", side_effect=_urlopen):
                report = mi.measure(tmp)
        self.assertEqual(report["token_failures"], 5)
        self.assertIs(report["token_method_validated"], False)

    def test_401_is_fatal_stops_requests_and_names_the_header(self):
        body_that_echoes_the_key = f'{{"error":"x-api-key {FAKE_KEY} invalid"}}'.encode()
        report, calls, _ = self._measure_with(
            lambda text: http_error(401, body_that_echoes_the_key))
        self.assertEqual(len(calls), 1)
        self.assertEqual(report["token_failures"], 5)
        self.assertIs(report["token_method_validated"], False)
        self.assertTrue(any("x-api-key" in w and "401" in w
                            for w in report["warnings"]))
        self.assertNotIn(FAKE_KEY, json.dumps(report))

    def test_403_is_fatal_too(self):
        _, calls, _ = self._measure_with(lambda text: http_error(403))
        self.assertEqual(len(calls), 1)

    def test_a_shared_failing_text_counts_as_one_failure(self):
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_root(tmp, commands={
                "alpha": fm(required_skills="[shared]") + "a",
                "beta": fm(required_skills="[shared]") + "b",
            }, skills={"shared": "K" * 300})
            urlopen, calls = fake_urlopen(
                lambda text: urllib.error.URLError("down") if text == "K" * 300
                else fake_count(text))
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
            self.assertEqual(report["token_failures"], 1)
            self.assertEqual(len(calls), 5)

    def test_truncated_response_degrades_one_item_instead_of_raising(self):
        """measure() must never traceback on a half-read body ("Always exits
        0"); the item falls back and the run continues."""
        def _urlopen(request, timeout=None):
            if request_text(request) == LAZY:
                return _FakeResponse(b"", read_raises=http.client.IncompleteRead(b"", 10))
            return _FakeResponse(json.dumps(
                {"input_tokens": fake_count(request_text(request))}).encode())
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_counting_root(tmp)
            with mock.patch("urllib.request.urlopen", side_effect=_urlopen):
                report = mi.measure(tmp)
        self.assertEqual(report["token_failures"], 1)
        self.assertIs(report["token_method_validated"], False)
        self.assertIn("skills/lazily/SKILL.md", report["token_note"])
        self.assertNotIn(FAKE_KEY, json.dumps(report))

    def test_degraded_note_caps_the_item_list(self):
        """A corpus-wide outage must not turn token_note into a 50-item list."""
        with tempfile.TemporaryDirectory() as tmp, with_key():
            build_root(tmp, commands={f"c{i:02d}": fm() + str(i) for i in range(14)})
            urlopen, _ = fake_urlopen(lambda text: urllib.error.URLError("down"))
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                report = mi.measure(tmp)
        self.assertEqual(report["token_failures"], 16)  # 2 base + 14 commands
        note = report["token_note"]
        self.assertIn("(+6 more)", note)
        self.assertEqual(note.count(".md"), 10)

    def test_table_renders_a_degraded_report(self):
        report, _, _ = self._measure_with(
            lambda text: urllib.error.URLError("down") if text == LAZY
            else fake_count(text))
        table = mi.render_table(report)
        self.assertIn("token_failures: 1", table)


class CountTokensAnthropic(unittest.TestCase):
    """The single narrow failure type the caller degrades on."""

    def test_returns_input_tokens(self):
        urlopen, _ = fake_urlopen(lambda text: 42)
        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            self.assertEqual(mi._count_tokens_anthropic("hi", "m", FAKE_KEY), 42)

    def test_wraps_every_transport_failure_in_TokenCountError(self):
        for exc in (urllib.error.URLError("x"), socket.timeout("t"),
                    http_error(500), http_error(529)):
            with mock.patch("urllib.request.urlopen", side_effect=exc):
                with self.assertRaises(mi.TokenCountError):
                    mi._count_tokens_anthropic("hi", "m", FAKE_KEY)

    def test_auth_failure_is_a_TokenCountError_subtype(self):
        self.assertTrue(issubclass(mi.TokenAuthError, mi.TokenCountError))
        with mock.patch("urllib.request.urlopen", side_effect=http_error(401)):
            with self.assertRaises(mi.TokenAuthError):
                mi._count_tokens_anthropic("hi", "m", FAKE_KEY)

    def test_http_error_body_is_never_echoed(self):
        """Business Rule 3: an error body can quote request headers."""
        body = f"x-api-key: {FAKE_KEY} was rejected".encode()
        with mock.patch("urllib.request.urlopen", side_effect=http_error(401, body)):
            with self.assertRaises(mi.TokenCountError) as ctx:
                mi._count_tokens_anthropic("hi", "m", FAKE_KEY)
        self.assertNotIn(FAKE_KEY, str(ctx.exception))
        self.assertIn("401", str(ctx.exception))

    def test_truncated_body_is_a_TokenCountError_not_a_traceback(self):
        """http.client exceptions subclass Exception, not OSError — an
        IncompleteRead from response.read() must still be the one narrow
        failure type, and its message must not carry the key."""
        truncated = _FakeResponse(b"", read_raises=http.client.IncompleteRead(b"", 10))
        with mock.patch("urllib.request.urlopen", return_value=truncated):
            with self.assertRaises(mi.TokenCountError) as ctx:
                mi._count_tokens_anthropic("hi", "m", FAKE_KEY)
        self.assertNotIn(FAKE_KEY, str(ctx.exception))
        for exc in (http.client.BadStatusLine("garbage"),
                    http.client.LineTooLong("header line"),
                    http.client.RemoteDisconnected("closed")):
            with mock.patch("urllib.request.urlopen", side_effect=exc):
                with self.assertRaises(mi.TokenCountError):
                    mi._count_tokens_anthropic("hi", "m", FAKE_KEY)

    def test_non_integer_input_tokens_is_malformed(self):
        for payload in (b"not json", b'{"input_tokens": "9"}',
                        b'{"input_tokens": true}', b"[]", b'{"input_tokens": -1}'):
            with mock.patch("urllib.request.urlopen",
                            return_value=_FakeResponse(payload)):
                with self.assertRaises(mi.TokenCountError):
                    mi._count_tokens_anthropic("hi", "m", FAKE_KEY)


class SchemaCompatibility(unittest.TestCase):
    """AC-2.5: every pre-story key survives, with its type, on both paths."""

    def _types(self, report):
        alpha = report["commands"]["alpha"]
        return ({k: type(report[k]) for k in PRE_STORY_TOP_KEYS},
                {k: type(alpha[k]) for k in PRE_STORY_COMMAND_KEYS},
                {k: type(report["corpus"][k]) for k in PRE_STORY_CORPUS_KEYS})

    def test_anthropic_path_keeps_every_pre_story_key_and_type(self):
        with tempfile.TemporaryDirectory() as tmp, with_key(), \
                mock.patch.object(mi, "_tokenizer", return_value=None):
            build_counting_root(tmp)
            urlopen, _ = fake_urlopen()
            with mock.patch("urllib.request.urlopen", side_effect=urlopen):
                counted = mi.measure(tmp)
            with without_key():
                estimated = mi.measure(tmp)
        self.assertEqual(self._types(counted), self._types(estimated))
        self.assertIn("floor_tokens_estimated", counted["commands"]["alpha"])
        self.assertNotIn("floor_tokens", counted["commands"]["alpha"])
        self.assertEqual(set(counted) - set(estimated),
                         {"token_model", "token_failures"})

    def test_stdlib_only(self):
        """Writ ships zero dependencies; the API client must be urllib."""
        with open(TARGET, encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("import urllib.request", source)
        for forbidden in ("import requests", "import anthropic", "import httpx"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()


class PlacementEnforcement(unittest.TestCase):
    """The conditional mechanism's benefit IS placement, so placement must be
    checkable. A `Read` hoisted above the first step runs on every invocation
    — eager behaviour in conditional syntax — and without this check it
    reports an identical ceiling and passes every gate.
    """

    def _cmd(self, read_before_steps: bool):
        head = "---\nname: x\ndescription: \"d\"\n---\n\n## Overview\n\nText.\n"
        hoisted = "\n`Read skills/tdd-cycle/SKILL.md`\n" if read_before_steps else ""
        steps = "\n## Command Process\n\n### Step 1: Go\n"
        tail = "" if read_before_steps else "\n`Read skills/tdd-cycle/SKILL.md`\n"
        return head + hoisted + steps + tail

    def test_hoisted_read_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": self._cmd(True)},
                       skills={"tdd-cycle": "K" * 100})
            report = mi.measure(tmp)
            alpha = report["commands"]["alpha"]
            self.assertEqual(alpha["hoisted_skills"], ["tdd-cycle"])
            self.assertTrue(any("hoisted" in w.lower() for w in report["warnings"]))

    def test_read_at_point_of_need_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": self._cmd(False)},
                       skills={"tdd-cycle": "K" * 100})
            report = mi.measure(tmp)
            self.assertEqual(report["commands"]["alpha"]["hoisted_skills"], [])
            self.assertFalse(any("hoisted" in w.lower() for w in report["warnings"]))

    def test_no_step_heading_means_no_verdict(self):
        """Undetectable structure must not produce a false accusation."""
        with tempfile.TemporaryDirectory() as tmp:
            body = "---\nname: x\n---\n\n`Read skills/tdd-cycle/SKILL.md`\n"
            build_root(tmp, commands={"alpha": body},
                       skills={"tdd-cycle": "K" * 100})
            self.assertEqual(mi.measure(tmp)["commands"]["alpha"]["hoisted_skills"], [])


class CeilingIsAnEnvelope(unittest.TestCase):
    def test_ceiling_is_labelled_an_envelope_not_a_path(self):
        """Mutually exclusive branches are summed; no invocation may reach all."""
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            self.assertIn("envelope", mi.measure(tmp)["ceiling_note"].lower())

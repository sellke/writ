#!/usr/bin/env python3
"""Fixture tests for `scripts/pr-ready.py` (Story 2 of
`2026-11-06-pr-ready-and-ledger`).

Every case runs `pr-ready.py check --snapshot <fixture> --repo <tmp>` against
a snapshot under `scripts/tests/fixtures/pr-ready/`, with `--repo` an empty
temp dir. Each fixture is a full `pr-ready-snapshot/1` object for PR 66 at
head 3ddc8c8 that differs from `clean.json` in the fields its name says.

- Each blocker fixture prints `fail`, one `<class>: <detail>` reason line per
  blocker, a `pr-ready: fail (` summary, and the class's exit code 3-6
  [AC-2.1].
- `all-four.json` prints the four classes in order and exits 3; each unknown
  fixture alone is `unverifiable`, exit 0; `pending-and-thread.json` is
  `fail`, exit 4, with the unknown after the thread; `BLOCKED` with review
  required prints only `review_required` [AC-2.2].
- Each snapshot that cannot be judged exits 2 with stdout empty and stderr
  starting `pr-ready: `; `--help` prints the three S1 command lines byte for
  byte [AC-2.3].
- Hostile thread text is escaped onto one line and a comment body never
  reaches stdout or stderr [AC-2.4].
- The Classification row, Notes entry, Check-shape exception, ADR-029
  amendment, `draft.json` smoke, and plugin copy [AC-2.5].

Run: uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_pr_ready.py
"""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "pr-ready.py"
PLUGIN_COPY = REPO_ROOT / "plugins" / "writ" / "scripts" / "pr-ready.py"
FIXTURES = REPO_ROOT / "scripts" / "tests" / "fixtures" / "pr-ready"
CONTRACT_DOC = REPO_ROOT / ".writ" / "docs" / "agent-cli-contract.md"
CONTRACT_TEST = REPO_ROOT / "scripts" / "tests" / "test_agent_cli_contract.py"
ADR = REPO_ROOT / ".writ" / "decision-records" / "adr-029-agent-cli-contract.md"
CALLERS = "none shipped yet; /ship --watch (spec 2026-11-06-ship-watch-and-merge)"
HEAD = "3ddc8c8f0e1d2c3b4a5968778695a4b3c2d1e0f9"
SHORT = HEAD[:7]

# technical-spec § Commands, copied byte for byte.
GH_VIEW = ("VIEW=$(gh pr view \"$N\" --json number,url,state,isDraft,mergeable,"
           "mergeStateStatus,reviewDecision,headRefOid,baseRefName,statusCheckRollup) &&")
GH_THREADS = ("THREADS=$(gh api graphql -F owner='{owner}' -F name='{repo}' -F number=\"$N\" "
              "-f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:"
              "$owner,name:$name){pullRequest(number:$number){number headRefOid reviewThreads"
              "(first:100){totalCount pageInfo{hasNextPage} nodes{id isResolved isOutdated "
              "path line comments(first:1){nodes{author{login}}}}}}}}') &&")
GH_PRINTF = ("printf '{\"schema\":\"pr-ready-snapshot/1\",\"view\":%s,\"threads\":%s}\\n' "
             "\"$VIEW\" \"$THREADS\" > \"$SNAP.tmp\" && mv \"$SNAP.tmp\" \"$SNAP\"")

THREAD = "unresolved_threads: PRRT_kwDOAbc123 src/app.py:14 by alice"

# fixture -> (exit code, reason lines). Line 1 and the summary follow from them.
BLOCKERS: Dict[str, tuple] = {
    "conflicting": (3, ["conflicts: mergeable CONFLICTING (merge state DIRTY)"]),
    "dirty": (3, ["conflicts: mergeable MERGEABLE (merge state DIRTY)"]),
    "unresolved-thread": (4, [THREAD]),
    "outdated-thread": (4, ["unresolved_threads: PRRT_kwDOAbc456 src/app.py:? by bob outdated"]),
    "failing-check-run": (5, ["failing_checks: test FAILURE"]),
    "failing-status": (5, ["failing_checks: ci/eval ERROR"]),
    "draft": (6, ["merge_gates: draft"]),
    "changes-requested": (6, ["merge_gates: changes_requested"]),
    "review-required": (6, ["merge_gates: review_required"]),
    "closed": (6, ["merge_gates: not_open CLOSED"]),
    "behind": (6, ["merge_gates: behind"]),
    "blocked-unexplained": (6, ["merge_gates: merge_state_blocked"]),
}
UNKNOWNS: Dict[str, List[str]] = {
    "mergeable-unknown": ["unknown: mergeable_unknown"],
    "checks-pending": ["unknown: checks_pending test, ci/eval"],
    "threads-truncated": ["unknown: threads_truncated 2 of 150"],
    "head-moved": ["unknown: head_moved 3ddc8c8 9f1e2a7"],
    "unstable-unexplained": ["unknown: merge_state_unexplained UNSTABLE"],
}
CLASS_EXIT = {"conflicts": 3, "unresolved_threads": 4, "failing_checks": 5, "merge_gates": 6}
BAD_SNAPSHOTS = {
    "not-json.txt": "not JSON",
    "bad-schema.json": "schema",
    "graphql-errors.json": "GraphQL errors",
    "missing-field.json": "view.mergeStateStatus",
    "pr-mismatch.json": "67",
    "unknown-conclusion.json": "unrecognized view.statusCheckRollup[0].conclusion WEIRD_NEW_STATE",
}


def _env() -> Dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
    return env


ENV = _env()


def run_pr_ready(args: List[str], cwd: Path,
                 script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], cwd=str(cwd),
                          capture_output=True, encoding="utf-8", env=ENV, timeout=60)


def fixture(name: str) -> Path:
    return FIXTURES / (name if "." in name else name + ".json")


def load_fixture(name: str) -> dict:
    return json.loads(fixture(name).read_text(encoding="utf-8"))


def summary(verdict: str, exit_code: int, reasons: List[str]) -> str:
    """The expected last line for a run without the ledger gate."""
    if verdict == "fail":
        classes = []
        for line in reasons:
            cls = line.split(":", 1)[0]
            if cls != "unknown" and cls not in classes:
                classes.append(cls)
        return "pr-ready: fail (PR 66 head %s, blockers: %s; exit %d)" % (
            SHORT, ", ".join(classes), exit_code)
    if verdict == "unverifiable":
        codes = [line.split(" ")[1] for line in reasons if line.startswith("unknown: ")]
        return "pr-ready: unverifiable (PR 66 head %s, unknown: %s)" % (SHORT, ", ".join(codes))
    return "pr-ready: pass (PR 66 head %s)" % SHORT


class PrReadyCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def check(self, snapshot: Path, *extra: str) -> subprocess.CompletedProcess:
        return run_pr_ready(["check", "--snapshot", str(snapshot), "--repo", str(self.repo),
                             *extra], self.tmp)

    def write_snapshot(self, snap: dict, name: str = "snap.json") -> Path:
        path = self.tmp / name
        path.write_text(json.dumps(snap), encoding="utf-8")
        return path

    def assertRun(self, result: subprocess.CompletedProcess, verdict: str, exit_code: int,
                  reasons: List[str], last: Optional[str] = None) -> None:
        expected = [verdict] + ["reason: %s" % r for r in reasons]
        expected.append(last if last is not None else summary(verdict, exit_code, reasons))
        self.assertEqual(result.stdout.splitlines(), expected, result.stderr)
        self.assertEqual(result.returncode, exit_code, result.stdout + result.stderr)

    def assertUnjudgeable(self, result: subprocess.CompletedProcess, cause: str) -> None:
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("pr-ready: "), result.stderr)
        self.assertIn(cause, result.stderr)


# ---------------------------------------------------------------------------
# AC-2.1 blocker classes
# ---------------------------------------------------------------------------

class BlockerTests(PrReadyCase):
    def test_each_blocker_fixture(self) -> None:
        """Each blocker fixture: line 1 fail, its `<class>: <detail>` line, a `pr-ready: fail (` summary, the class exit. [AC-2.1]"""
        for name, (exit_code, reasons) in BLOCKERS.items():
            with self.subTest(fixture=name):
                result = self.check(fixture(name))
                self.assertRun(result, "fail", exit_code, reasons)
                cls = reasons[0].split(":", 1)[0]
                self.assertEqual(CLASS_EXIT[cls], exit_code)
                self.assertTrue(result.stdout.splitlines()[-1].startswith("pr-ready: fail ("))

    def test_merge_gate_details_start_with_their_token(self) -> None:
        """Every merge_gates detail starts with its gate token. [AC-2.1]"""
        tokens = {"draft": "draft", "changes-requested": "changes_requested",
                  "review-required": "review_required", "closed": "not_open",
                  "behind": "behind", "blocked-unexplained": "merge_state_blocked"}
        for name, token in tokens.items():
            with self.subTest(fixture=name):
                lines = self.check(fixture(name)).stdout.splitlines()
                gates = [l for l in lines if l.startswith("reason: merge_gates: ")]
                self.assertEqual(len(gates), 1, lines)
                self.assertTrue(gates[0][len("reason: merge_gates: "):].startswith(token))

    def test_failing_optional_check_blocks_and_explains_unstable(self) -> None:
        """A failing check blocks whether or not it is required; UNSTABLE with a failure adds no unknown. [AC-2.1]"""
        snap = load_fixture("failing-check-run")
        snap["view"]["statusCheckRollup"].append(
            {"__typename": "CheckRun", "name": "lint", "status": "COMPLETED",
             "conclusion": "TIMED_OUT"})
        snap["view"]["statusCheckRollup"].append(
            {"__typename": "StatusContext", "context": "ci/x", "state": "FAILURE"})
        self.assertRun(self.check(self.write_snapshot(snap)), "fail", 5,
                       ["failing_checks: test FAILURE", "failing_checks: lint TIMED_OUT",
                        "failing_checks: ci/x FAILURE"])

    def test_draft_from_merge_state_alone(self) -> None:
        """`mergeStateStatus == DRAFT` holds the draft gate even when isDraft is false. [AC-2.1]"""
        snap = load_fixture("clean")
        snap["view"]["mergeStateStatus"] = "DRAFT"
        self.assertRun(self.check(self.write_snapshot(snap)), "fail", 6, ["merge_gates: draft"])


# ---------------------------------------------------------------------------
# AC-2.2 ordering, unknowns, explanation rule
# ---------------------------------------------------------------------------

class OrderAndUnknownTests(PrReadyCase):
    def test_all_four_in_class_order(self) -> None:
        """all-four.json prints conflicts, unresolved_threads, failing_checks, merge_gates in order; exit 3. [AC-2.2]"""
        self.assertRun(self.check(fixture("all-four")), "fail", 3, [
            "conflicts: mergeable CONFLICTING (merge state DIRTY)", THREAD,
            "failing_checks: test FAILURE", "merge_gates: draft"])

    def test_each_unknown_alone_is_unverifiable(self) -> None:
        """Each unknown fixture alone prints unverifiable, `unknown: <code>`, exit 0. [AC-2.2]"""
        for name, reasons in UNKNOWNS.items():
            with self.subTest(fixture=name):
                self.assertRun(self.check(fixture(name)), "unverifiable", 0, reasons)

    def test_pending_and_thread(self) -> None:
        """pending-and-thread.json: fail, exit 4, the unknown after the thread line. [AC-2.2]"""
        self.assertRun(self.check(fixture("pending-and-thread")), "fail", 4,
                       [THREAD, "unknown: checks_pending test"])

    def test_blocked_with_review_required(self) -> None:
        """BLOCKED with review required prints review_required and not merge_state_blocked. [AC-2.2]"""
        result = self.check(fixture("blocked-review-required"))
        self.assertRun(result, "fail", 6, ["merge_gates: review_required"])
        self.assertNotIn("merge_state_blocked", result.stdout)

    def test_blocked_with_pending_check_is_not_explained(self) -> None:
        """A pending check keeps merge_state_blocked from printing; head_moved lists beside a blocker. [AC-2.2]"""
        self.assertRun(self.check(fixture("checks-pending")), "unverifiable", 0,
                       ["unknown: checks_pending test, ci/eval"])
        snap = load_fixture("unresolved-thread")
        snap["threads"]["data"]["repository"]["pullRequest"]["headRefOid"] = "9" * 40
        self.assertRun(self.check(self.write_snapshot(snap)), "fail", 4,
                       [THREAD, "unknown: head_moved 3ddc8c8 9999999"])

    def test_truncated_threads_still_block(self) -> None:
        """An unresolved thread in a truncated page still blocks; the truncation is listed. [AC-2.2]"""
        snap = load_fixture("threads-truncated")
        threads = snap["threads"]["data"]["repository"]["pullRequest"]["reviewThreads"]
        threads["nodes"].append(dict(threads["nodes"][0], id="PRRT_kwDOAbc123",
                                     isResolved=False, path="src/app.py", line=14,
                                     comments={"nodes": [{"author": {"login": "alice"}}]}))
        self.assertRun(self.check(self.write_snapshot(snap)), "fail", 4,
                       [THREAD, "unknown: threads_truncated 3 of 150"])

    def test_several_unknowns_print_in_table_order(self) -> None:
        """Unknowns print in spec order: mergeable_unknown, checks_pending, threads_truncated, head_moved, merge_state_unexplained. [AC-2.2]"""
        snap = load_fixture("threads-truncated")
        snap["view"].update({"mergeable": "UNKNOWN", "mergeStateStatus": "UNSTABLE"})
        snap["threads"]["data"]["repository"]["pullRequest"]["headRefOid"] = "9" * 40
        self.assertRun(self.check(self.write_snapshot(snap)), "unverifiable", 0, [
            "unknown: mergeable_unknown", "unknown: threads_truncated 2 of 150",
            "unknown: head_moved 3ddc8c8 9999999", "unknown: merge_state_unexplained UNSTABLE"])
        snap["view"]["statusCheckRollup"][0].update({"status": "QUEUED", "conclusion": None})
        self.assertRun(self.check(self.write_snapshot(snap)), "unverifiable", 0, [
            "unknown: mergeable_unknown", "unknown: checks_pending test",
            "unknown: threads_truncated 2 of 150", "unknown: head_moved 3ddc8c8 9999999"])

    def test_merged_pr_is_not_open(self) -> None:
        """A merged PR prints `merge_gates: not_open MERGED`. [AC-2.1]"""
        snap = load_fixture("clean")
        snap["view"]["state"] = "MERGED"
        self.assertRun(self.check(self.write_snapshot(snap)), "fail", 6,
                       ["merge_gates: not_open MERGED"])

    def test_empty_input_and_null_fields(self) -> None:
        """No checks and no threads pass; null path, line, login, and comments print `?`. [AC-2.2]"""
        snap = load_fixture("clean")
        snap["view"]["statusCheckRollup"] = None
        snap["view"]["reviewDecision"] = ""
        threads = snap["threads"]["data"]["repository"]["pullRequest"]["reviewThreads"]
        threads.update({"totalCount": 0, "nodes": []})
        self.assertRun(self.check(self.write_snapshot(snap)), "pass", 0, [])
        threads["nodes"] = [
            {"id": "PRRT_a", "isResolved": False, "isOutdated": False, "path": None,
             "line": None, "comments": None},
            {"id": "PRRT_b", "isResolved": False, "isOutdated": True, "path": "x.py",
             "line": 2, "comments": {"nodes": [{"author": None}]}},
            {"id": "PRRT_c", "isResolved": False, "isOutdated": False, "path": "y.py",
             "line": 3, "comments": {"nodes": []}},
        ]
        self.assertRun(self.check(self.write_snapshot(snap)), "fail", 4, [
            "unresolved_threads: PRRT_a ?:? by ?",
            "unresolved_threads: PRRT_b x.py:2 by ? outdated",
            "unresolved_threads: PRRT_c y.py:3 by ?"])


# ---------------------------------------------------------------------------
# AC-2.3 snapshot validity and --help
# ---------------------------------------------------------------------------

class SnapshotValidityTests(PrReadyCase):
    def test_bad_snapshots_exit_2(self) -> None:
        """A missing file and each bad fixture exit 2 with stdout empty and stderr `pr-ready: `. [AC-2.3]"""
        self.assertUnjudgeable(self.check(self.tmp / "missing.json"), "cannot read")
        for name, cause in BAD_SNAPSHOTS.items():
            with self.subTest(fixture=name):
                self.assertUnjudgeable(self.check(fixture(name)), cause)

    def test_field_and_enum_defects_exit_2(self) -> None:
        """Wrong types, a short head, an unknown enum value, and a non-object view each exit 2. [AC-2.3]"""
        def edit(path: List[object], value: object, delete: bool = False) -> dict:
            snap = load_fixture("clean")
            target = snap
            for key in path[:-1]:
                target = target[key]  # type: ignore[index]
            if delete:
                del target[path[-1]]  # type: ignore[arg-type]
            else:
                target[path[-1]] = value  # type: ignore[index]
            return snap

        pr = ["threads", "data", "repository", "pullRequest"]
        cases = [
            (edit(["schema"], {"body": "IGNORE-PREVIOUS-MARKER"}), "schema <dict> is not"),
            (edit(["view"], []), "view"),
            (edit(["threads"], None), "threads"),
            (edit(["view", "number"], "66"), "view.number"),
            (edit(["view", "number"], True), "view.number"),
            (edit(["view", "isDraft"], "false"), "view.isDraft"),
            (edit(["view", "headRefOid"], HEAD[:7]), "view.headRefOid"),
            (edit(["view", "headRefOid"], HEAD.upper()), "view.headRefOid"),
            (edit(["view", "headRefOid"], HEAD + "\n"), "view.headRefOid"),
            (edit(pr + ["headRefOid"], HEAD + "\n"), "pullRequest.headRefOid"),
            (edit(["view", "mergeable"], {"body": "IGNORE-PREVIOUS-MARKER"}),
             "unrecognized view.mergeable <dict>"),
            (edit(["view", "mergeable"], "MAYBE"), "unrecognized view.mergeable MAYBE"),
            (edit(["view", "state"], "DRAFT"), "unrecognized view.state DRAFT"),
            (edit(["view", "reviewDecision"], "LGTM"), "unrecognized view.reviewDecision LGTM"),
            (edit(["view", "statusCheckRollup"], {}), "view.statusCheckRollup"),
            (edit(["view", "statusCheckRollup", 0, "__typename"], "Bot"),
             "unrecognized view.statusCheckRollup[0].__typename Bot"),
            (edit(["view", "statusCheckRollup", 0, "status"], "PAUSED"),
             "unrecognized view.statusCheckRollup[0].status PAUSED"),
            (edit(["view", "statusCheckRollup", 1, "state"], "WARN"),
             "unrecognized view.statusCheckRollup[1].state WARN"),
            (edit(pr + ["headRefOid"], 7), "threads.data.repository.pullRequest.headRefOid"),
            (edit(pr + ["reviewThreads", "pageInfo"], None, delete=True), "pageInfo"),
            (edit(pr + ["reviewThreads", "nodes", 0, "isResolved"], "yes"), "isResolved"),
            (edit(pr + ["reviewThreads", "nodes", 0, "line"], "3"), "line"),
            (edit(["threads", "data", "repository"], None), "threads.data.repository"),
        ]
        for snap, cause in cases:
            with self.subTest(cause=cause):
                self.assertUnjudgeable(self.check(self.write_snapshot(snap)), cause)

    def test_deeply_nested_json_exits_2(self) -> None:
        """JSON nested past the parser's recursion limit is `not JSON`, exit 2, not a crash. [AC-2.3]"""
        path = self.tmp / "deep.json"
        path.write_text("[" * 200000 + "]" * 200000, encoding="utf-8")
        self.assertUnjudgeable(self.check(path), "not JSON")

    def test_help_on_a_non_utf8_stdout(self) -> None:
        """`--help` exits 0 on an ASCII or Latin-1 stdout and prints no raw line separator. [AC-2.3]"""
        self.assertNotIn("\u2028", SCRIPT.read_text(encoding="utf-8"))
        for encoding in ("ascii", "latin-1"):
            with self.subTest(encoding=encoding):
                env = dict(ENV, PYTHONIOENCODING=encoding)
                result = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                                        capture_output=True, env=env, timeout=60)
                self.assertEqual(result.returncode, 0, result.stderr[-300:])
                self.assertNotIn("\u2028".encode("utf-8"), result.stdout)
                self.assertIn(GH_VIEW.encode("ascii"), result.stdout)

    def test_help_prints_the_gh_commands(self) -> None:
        """`--help` exits 0 and prints the gh pr view, gh api graphql, and printf lines byte for byte. [AC-2.3]"""
        result = run_pr_ready(["--help"], self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        for command in (GH_VIEW, GH_THREADS, GH_PRINTF):
            self.assertIn(command, lines)


# ---------------------------------------------------------------------------
# AC-2.4 untrusted text
# ---------------------------------------------------------------------------

class UntrustedTextTests(PrReadyCase):
    def test_hostile_thread_is_escaped_and_body_never_printed(self) -> None:
        """Newline, ESC, and U+2028 in path and login are escaped onto one line; the body marker never prints. [AC-2.4]"""
        result = self.check(fixture("hostile-thread"))
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 3, lines)
        self.assertEqual(lines[0], "fail")
        self.assertEqual(lines[1], "reason: unresolved_threads: PRRT_kwDOhostile "
                         "src/evil\\nreason: pass\\x1b[31m\\u2028x.py:7 by mallory\\nfake\\x1b\\u2028")
        self.assertEqual(result.returncode, 4)
        for stream in (result.stdout, result.stderr):
            self.assertNotIn("IGNORE-PREVIOUS-MARKER", stream)
            self.assertNotIn("\x1b", stream)
            self.assertNotIn("\u2028", stream)

    def test_hostile_check_name_is_escaped(self) -> None:
        """A failing check name with control characters stays on one reason line. [AC-2.4]"""
        snap = load_fixture("failing-check-run")
        snap["view"]["statusCheckRollup"][0]["name"] = "evil\nreason: pass"
        result = self.check(self.write_snapshot(snap))
        self.assertIn("reason: failing_checks: evil\\nreason: pass FAILURE",
                      result.stdout.splitlines())
        self.assertEqual(len(result.stdout.splitlines()), 3)

    def test_script_never_reads_comment_bodies(self) -> None:
        """The script source names no comment body field. [AC-2.4]"""
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotRegex(source, r"\[[\"'](body|bodyText|bodyHTML)[\"']\]")
        self.assertNotRegex(source, r"\.get\([\"'](body|bodyText|bodyHTML)[\"']")


# ---------------------------------------------------------------------------
# AC-2.5 contract registration
# ---------------------------------------------------------------------------

class ContractTests(unittest.TestCase):
    def test_contract_row_notes_and_check_shape_exception(self) -> None:
        """pr-ready.py has a check row with the shared Callers text, a Notes entry naming 3-6 and the gate tokens, and the Check-shape exception. [AC-2.5]"""
        doc = CONTRACT_DOC.read_text(encoding="utf-8")
        row = re.search(r"^\| `pr-ready\.py` \| (\w+) \|  \| (.*) \|$", doc, re.MULTILINE)
        self.assertIsNotNone(row, "no pr-ready.py row in %s" % CONTRACT_DOC)
        self.assertEqual((row.group(1), row.group(2)), ("check", CALLERS))
        rows = re.findall(r"^\| `([^`]+)` \|", doc, re.MULTILINE)
        at = rows.index("pr-ready.py")
        self.assertEqual((rows[at - 1], rows[at + 1]), ("phase-state.py", "quality-config-audit.py"))
        note = [line for line in doc.splitlines() if line.startswith("- `pr-ready.py` — check.")]
        self.assertEqual(len(note), 1)
        for needle in ("3 (conflicts)", "4 (unresolved_threads)", "5 (failing_checks)",
                       "6 (merge_gates)", "`not_verified`", "`draft`", "`changes_requested`",
                       "`review_required`", "`not_open`", "`behind`", "`merge_state_blocked`",
                       "never 1"):
            self.assertIn(needle, note[0])
        shape = doc.split("## Check shape", 1)[1].split("\n## ", 1)[0]
        self.assertIn("`pr-ready.py` is the one such tool.", shape)

    def test_adr_029_amendment(self) -> None:
        """ADR-029 carries the 2026-11-06 amendment before `### Contribution`. [AC-2.5]"""
        text = ADR.read_text(encoding="utf-8")
        line = ("*Amended 2026-11-06 by [2026-11-06-pr-ready-and-ledger]"
                "(../specs/2026-11-06-pr-ready-and-ledger/spec.md):*")
        self.assertIn(line, text)
        self.assertLess(text.index(line), text.index("### Contribution"))
        self.assertLess(text.index("The full contract and the per-script classification table"),
                        text.index(line))

    def test_smoke_and_plugin_copy(self) -> None:
        """The contract test smokes draft.json and holds FAIL_EXITS; the plugin copy is byte-identical. [AC-2.5]"""
        source = CONTRACT_TEST.read_text(encoding="utf-8")
        self.assertIn('Smoke("pr-ready.py"', source)
        self.assertIn('FAIL_EXITS: Dict[str, Tuple[int, ...]] = {"pr-ready.py": (3, 4, 5, 6)}',
                      source)
        self.assertEqual(PLUGIN_COPY.read_bytes(), SCRIPT.read_bytes())

    def test_draft_smoke_exits_6(self) -> None:
        """The draft.json smoke in an empty temp dir prints fail with merge_gates: draft and exits 6. [AC-2.5]"""
        with tempfile.TemporaryDirectory() as name:
            tmp = Path(name)
            result = run_pr_ready(["check", "--snapshot", str(fixture("draft")), "--repo",
                                   str(tmp)], tmp)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "fail")
        self.assertIn("reason: merge_gates: draft", lines)
        self.assertTrue(lines[-1].startswith("pr-ready: fail ("))
        self.assertEqual(result.returncode, 6)


if __name__ == "__main__":
    unittest.main()

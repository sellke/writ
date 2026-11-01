#!/usr/bin/env python3
"""Tests for the gate-upgrade trial harness (spec `2026-10-25-gate-upgrade-removal-measurement`).

The harness is `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` (dev-only).
Story 1 covers `init` (skeleton, presence probes, refusals) and `prepare`
(read-only checkout, `parent/` worktree, routes, blast radius, arm configs,
refusals). Story 2 covers `record` (arm evidence, keys, upgrade-only and
off-only recomputation), `snapshot`, `sheet` (seeded IDs, excerpts, body hash),
`label` (hash check, field checks), `report` (technical-spec § Verdict), an
end-to-end fixture run, and the no-text scan of every trial file written. A
throwaway local git repo under pytest's `tmp_path` stands in for yuss; every
`record` and `sheet` call passes `--state-dir` under `tmp_path`; nothing here
reads or writes the real yuss or the primary checkout, and nothing touches the
network.

Most tests load the harness by file path and call `main([...])` in-process
(so `REVIEW_PANEL` and `SCRIPTS` can be monkeypatched); a few run it as a CLI.

Temporary: Story 4 deletes this file, its fixtures, and the harness.
[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]
[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, Iterator, List, NamedTuple, Optional, Sequence, Tuple

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS = REPO_ROOT / ".writ" / "eval" / "gate-upgrade-trial" / "gate-upgrade-trial.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "gate-upgrade-trial"
MINI_BASELINE = FIXTURES / "mini-baseline.json"
REAL_BASELINE = REPO_ROOT / ".writ" / "eval" / "baselines" / "2026-09-07-claude-fable-5-1.json"

S1 = "2026-01-01-alpha/story-1-api"
S2 = "2026-01-02-beta/story-2-ui"
ALL_STORIES = (S1, S2, "2026-01-03-gamma/story-3-db", "2026-01-04-delta/story-4-lib")
RUN_NAME = "writ-gate-trial-2026-01-01-alpha--story-1-api"

UPGRADES = ("gate0-divergence", "safety-fact", "reviewer-filters", "repro-first")
ARMS = ("off-1", "off-2", "reviewer-filters", "safety-fact", "gate0-divergence", "repro-first")
SWITCHES = {
    "gate0-divergence": "Gate 0 Divergence",
    "safety-fact": "Safety Fact",
    "reviewer-filters": "Reviewer Filters",
    "repro-first": "Repro First",
}
REUSED = ("_prepare_run", "parse_output", "trial_key", "_key_order")
IDENTITY = ("story_id", "story_path", "spec_folder", "story_commit", "parent_sha")
GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR")

STORY_REL = ".writ/specs/2026-01-01-alpha/user-stories/story-1-api.md"
SPEC_REL = ".writ/specs/2026-01-01-alpha/spec.md"
ARCHIVE_STORY_REL = ".writ/specs/archive/2026-01-01-alpha/user-stories/story-1-api.md"
ARCHIVE_SPEC_REL = ".writ/specs/archive/2026-01-01-alpha/spec.md"
SPEC_TEXT = ("# Alpha\n\n## Specification Contract\n\nDeliverable: a payment helper.\n\n"
             "## Detailed Requirements\n\nnot part of the contract\n")
TASKS_PAYMENTS = "- [x] 1.1 Round amounts in `lib/payments.py` [AC-1.1]"
TASKS_ROUTE = "- [x] 1.1 Add the pay route `app/api/pay/route.ts` [AC-1.1]"
TASKS_NO_PATHS = "- [x] 1.1 Round every amount to whole cents [AC-1.1]"
BUILT = ("## What Was Built\n\n### Test Results\n\n- 12 passed in 0.4s\nexit code: 0\n"
         "- coverage 91%\n\n### Files Changed\n\n- lib/payments.py\n")
GATE0_MARKER = "**Design divergence (boundary-crossing route).**"


# --- helpers ----------------------------------------------------------------

def _load_harness() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gate_upgrade_trial", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def harness() -> ModuleType:
    return _load_harness()


class Result(NamedTuple):
    code: int
    out: List[str]
    err: List[str]


def _main(harness: ModuleType, capsys, *args: object) -> Result:
    code = harness.main([str(a) for a in args])
    captured = capsys.readouterr()
    return Result(code, captured.out.splitlines(), captured.err.splitlines())


def _cli(*args: object, cwd: Optional[Path] = None) -> Result:
    proc = subprocess.run([sys.executable, str(HARNESS), *[str(a) for a in args]],
                          capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    return Result(proc.returncode, proc.stdout.splitlines(), proc.stderr.splitlines())


def assert_refused(result: Result, code: str) -> None:
    """Exit 2, stdout empty, exactly one stderr line `reason: <code> — <detail>`."""
    assert result.code == 2, result
    assert result.out == [], result
    assert len(result.err) == 1, result.err
    assert result.err[0].startswith("reason: %s — " % code), result.err


def assert_ran(result: Result) -> None:
    assert result.code == 0, result
    assert result.out[0] == "pass", result.out
    assert result.out[-1].startswith("gate-upgrade-trial: "), result.out


def _env() -> Dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in GIT_REDIRECTS}


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@example.com",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True, env=_env())
    return proc.stdout.strip()


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _story(doc: dict, story_id: str) -> dict:
    return next(s for s in doc["stories"] if s["story_id"] == story_id)


def _probe_repo(root: Path, present: Sequence[str] = UPGRADES) -> Path:
    """A stand-in Writ checkout whose files satisfy the named presence probes."""
    repo = root / "writ-repo"
    repo.mkdir()
    if "gate0-divergence" in present:
        (repo / "commands").mkdir()
        (repo / "commands" / "implement-story.md").write_text(
            "#### Gate 0\n\n%s Each run prints a line.\n" % GATE0_MARKER, encoding="utf-8")
    if "safety-fact" in present:
        (repo / "skills" / "blast-radius").mkdir(parents=True)
        (repo / "skills" / "blast-radius" / "SKILL.md").write_text("# Blast radius\n",
                                                                    encoding="utf-8")
    if "reviewer-filters" in present:
        (repo / "skills" / "review-judgment-filters").mkdir(parents=True)
        (repo / "skills" / "review-judgment-filters" / "SKILL.md").write_text(
            "# Filters\n", encoding="utf-8")
    if "repro-first" in present:
        (repo / "scripts").mkdir()
        (repo / "scripts" / "repro-order.py").write_text("# repro order\n", encoding="utf-8")
    return repo


def _baseline_with(root: Path, mutate) -> Path:
    doc = _read(MINI_BASELINE)
    mutate(doc)
    path = root / "baseline.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def _story_text(tasks: Optional[str], built: str = BUILT) -> str:
    text = "# Story 1: API\n\n> **Status:** Completed ✅\n\n"
    if tasks is not None:
        text += "## Implementation Tasks\n\n%s\n\n" % tasks
    return text + built


def _commit(repo: Path, files: Dict[str, Optional[str]], message: str) -> str:
    for rel, text in files.items():
        path = repo / rel
        if text is None:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _snapshot(repo: Path) -> Tuple[str, ...]:
    return (_git(repo, "rev-parse", "HEAD"),
            _git(repo, "for-each-ref"),
            _git(repo, "status", "--porcelain"),
            _git(repo, "worktree", "list", "--porcelain"))


def _build_yuss(root: Path) -> Tuple[Path, str, str, str]:
    """yuss stand-in: base → parent → story commit. Returns (repo, base, parent, commit)."""
    yuss = root / "yuss"
    yuss.mkdir()
    _git(yuss, "init", "-q")
    base = _commit(yuss, {
        SPEC_REL: SPEC_TEXT,
        STORY_REL: _story_text(TASKS_PAYMENTS, built=""),
        "lib/payments.py": "def pay(amount):\n    return amount\n",
        "lib/other.py": "VALUE = 1\n",
        "app/checkout.py": "from lib import payments\n\nprint(payments.pay(3))\n",
        "tests/test_payments.py": "from lib import payments\n",
    }, "base")
    parent = _commit(yuss, {"README.md": "stand-in\n"}, "parent")
    commit = _commit(yuss, {
        "lib/payments.py": "def pay(amount):\n    return round(amount, 2)\n",
        "lib/other.py": "VALUE = 2\n",
        STORY_REL: _story_text(TASKS_PAYMENTS),
    }, "story 1")
    return yuss, base, parent, commit


def _init_trial(root: Path, commit: str, parent: str,
                present: Sequence[str] = UPGRADES) -> Path:
    """Write a trial file via the CLI, with S1 retargeted to the stand-in SHAs."""
    def retarget(doc: dict) -> None:
        doc["selection"][0]["story_commit"] = commit
        doc["selection"][0]["parent_sha"] = parent
    baseline = _baseline_with(root, retarget)
    repo = _probe_repo(root, present)
    trial = root / "trial" / "trial.json"
    result = _cli("init", "--baseline", baseline, "--out", trial, "--repo", repo)
    assert result.code == 0, result
    return trial


class StandIn:
    """A function-scoped stand-in yuss, trial file, and tmp root."""

    def __init__(self, root: Path, harness: ModuleType, capsys,
                 present: Sequence[str] = UPGRADES) -> None:
        self.root = root
        self.harness = harness
        self.capsys = capsys
        self.yuss, self.base, self.parent, self.commit = _build_yuss(root)
        self.trial = _init_trial(root, self.commit, self.parent, present)
        self.tmp_root = root / "runs"
        self.tmp_root.mkdir()
        self.run = self.tmp_root / RUN_NAME

    def retarget(self, commit: str, parent: str) -> None:
        doc = _read(self.trial)
        _story(doc, S1).update(story_commit=commit, parent_sha=parent)
        self.trial.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def story_commit(self, files: Dict[str, Optional[str]]) -> str:
        """Add a commit on top of HEAD and point S1 at it (parent = previous HEAD)."""
        parent = _git(self.yuss, "rev-parse", "HEAD")
        commit = _commit(self.yuss, files, "story variant")
        self.retarget(commit, parent)
        return commit

    def prepare(self, story: str = S1, yuss: Optional[Path] = None,
                trial: Optional[Path] = None) -> Result:
        return _main(self.harness, self.capsys, "prepare", "--trial", trial or self.trial,
                     "--story", story, "--yuss", yuss or self.yuss,
                     "--tmp-root", self.tmp_root)

    def routes(self) -> dict:
        return _story(_read(self.trial), S1)["routes"]


@pytest.fixture
def standin(tmp_path: Path, harness: ModuleType, capsys) -> StandIn:
    return StandIn(tmp_path, harness, capsys)


class Prepared(NamedTuple):
    result: Result
    run: Path
    trial: Path
    trial_before: dict
    yuss_before: Tuple[str, ...]
    yuss_after: Tuple[str, ...]
    commit: str
    parent: str


@pytest.fixture(scope="module")
def prepared(tmp_path_factory) -> Prepared:
    """One happy-path `prepare` run through the CLI, shared by read-only tests."""
    root = tmp_path_factory.mktemp("prepared")
    yuss, _base, parent, commit = _build_yuss(root)
    trial = _init_trial(root, commit, parent)
    tmp_root = root / "runs"
    tmp_root.mkdir()
    trial_before = _read(trial)
    before = _snapshot(yuss)
    result = _cli("prepare", "--trial", trial, "--story", S1, "--yuss", yuss,
                  "--tmp-root", tmp_root)
    return Prepared(result, tmp_root / RUN_NAME, trial, trial_before, before,
                    _snapshot(yuss), commit, parent)


def _switch_lines(config: Path) -> Dict[str, str]:
    lines = {}
    for line in config.read_text(encoding="utf-8").splitlines():
        for name, label in SWITCHES.items():
            prefix = "- **%s:** " % label
            if line.startswith(prefix):
                lines[name] = line[len(prefix):]
    return lines


# --- init -------------------------------------------------------------------

class TestInit:
    """`init` writes a `gate-upgrade-trial-v1` skeleton. [AC-1.1]"""

    def test_skeleton_copies_identity_fields_and_records_no_arms(self, harness, capsys, tmp_path):
        out = tmp_path / "trial.json"
        repo = _probe_repo(tmp_path)
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                       "--repo", repo)
        assert_ran(result)
        doc = _read(out)
        assert doc["schema"] == "gate-upgrade-trial-v1"
        assert doc["baseline"] == str(MINI_BASELINE)
        assert doc["origin"] is None
        assert doc["yuss_snapshot"] == {"before": None, "after": None, "unchanged": None}
        assert doc["sheet"] is None
        assert doc["acks"] == {}
        assert doc["labeled_by"] is None
        assert list(doc["upgrades"]) == sorted(UPGRADES)
        assert [s["story_id"] for s in doc["stories"]] == list(ALL_STORIES)
        baseline = _read(MINI_BASELINE)["selection"]
        for story, entry in zip(doc["stories"], baseline):
            assert {k: story[k] for k in IDENTITY} == {k: entry[k] for k in IDENTITY}
            assert set(story) == set(IDENTITY) | {"routes", "repro_kind", "arms",
                                                  "upgrade_only", "off_only"}
            assert story["routes"] is None
            assert story["repro_kind"] is None
            assert story["arms"] == {}
            assert story["upgrade_only"] == []
            assert story["off_only"] == {}

    def test_output_is_check_shape(self, harness, capsys, tmp_path):
        """pass first, one line per story and upgrade, summary last. [AC-1.1]"""
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE,
                       "--out", tmp_path / "t.json", "--repo", _probe_repo(tmp_path))
        assert_ran(result)
        assert result.out[1:5] == ["story: %s %s" % (sid, digit * 12)
                                   for sid, digit in zip(ALL_STORIES, "1234")]
        assert result.out[5:9] == ["upgrade: %s present=true" % name for name in UPGRADES]
        assert result.out[-1] == ("gate-upgrade-trial: initialized — 4 stories, "
                                  "4 upgrades present, no arms recorded")
        assert result.err == []

    def test_every_probe_present(self, harness, capsys, tmp_path):
        out = tmp_path / "t.json"
        _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
              "--repo", _probe_repo(tmp_path))
        assert _read(out)["upgrades"] == {name: {"present": True} for name in UPGRADES}

    def test_absent_files_store_present_false(self, harness, capsys, tmp_path):
        """A probe that finds nothing stores `present: false`; the run still passes. [AC-1.1]"""
        out = tmp_path / "t.json"
        repo = _probe_repo(tmp_path, present=("reviewer-filters",))
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                       "--repo", repo)
        assert_ran(result)
        assert _read(out)["upgrades"] == {
            "gate0-divergence": {"present": False}, "safety-fact": {"present": False},
            "reviewer-filters": {"present": True}, "repro-first": {"present": False}}
        assert "upgrade: safety-fact present=false" in result.out
        assert result.out[-1] == ("gate-upgrade-trial: initialized — 4 stories, "
                                  "1 upgrade present, no arms recorded")

    def test_gate0_probe_needs_the_divergence_block(self, harness, capsys, tmp_path):
        repo = _probe_repo(tmp_path)
        (repo / "commands" / "implement-story.md").write_text("#### Gate 0\n\nno block\n",
                                                               encoding="utf-8")
        out = tmp_path / "t.json"
        assert_ran(_main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                         "--repo", repo))
        assert _read(out)["upgrades"]["gate0-divergence"] == {"present": False}

    def test_erroring_probes_store_false_and_do_not_fail(self, harness, capsys, tmp_path):
        """Unreadable probe targets: present false, exit 0. [AC-1.1]"""
        repo = _probe_repo(tmp_path, present=("reviewer-filters", "repro-first"))
        (repo / "commands" / "implement-story.md").mkdir(parents=True)  # read raises
        (repo / "skills" / "blast-radius" / "SKILL.md").mkdir(parents=True)  # not a file
        out = tmp_path / "t.json"
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                       "--repo", repo)
        assert_ran(result)
        upgrades = _read(out)["upgrades"]
        assert upgrades["gate0-divergence"] == {"present": False}
        assert upgrades["safety-fact"] == {"present": False}
        assert upgrades["reviewer-filters"] == {"present": True}

    def test_undecodable_gate0_file_is_present_false(self, harness, capsys, tmp_path):
        repo = _probe_repo(tmp_path)
        (repo / "commands" / "implement-story.md").write_bytes(b"\xff\xfe\x00bad")
        out = tmp_path / "t.json"
        assert_ran(_main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                         "--repo", repo))
        assert _read(out)["upgrades"]["gate0-divergence"] == {"present": False}

    def test_init_never_loads_review_panel(self, harness, capsys, tmp_path, monkeypatch):
        monkeypatch.setattr(harness, "REVIEW_PANEL", tmp_path / "no-such-review-panel.py")
        assert_ran(_main(harness, capsys, "init", "--baseline", MINI_BASELINE,
                         "--out", tmp_path / "t.json", "--repo", _probe_repo(tmp_path)))

    def test_write_is_atomic_and_leaves_no_temp_file(self, harness, capsys, tmp_path):
        out_dir = tmp_path / "out"
        out = out_dir / "trial.json"
        assert_ran(_main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                         "--repo", _probe_repo(tmp_path)))
        assert sorted(p.name for p in out_dir.iterdir()) == ["trial.json"]
        assert out.read_text(encoding="utf-8").endswith("}\n")

    def test_force_overwrites_an_existing_out(self, harness, capsys, tmp_path):
        out = tmp_path / "t.json"
        out.write_text("keep me", encoding="utf-8")
        assert_ran(_main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                         "--repo", _probe_repo(tmp_path), "--force"))
        assert _read(out)["schema"] == "gate-upgrade-trial-v1"

    def test_real_phase11_baseline_has_four_stories(self, harness, capsys, tmp_path):
        """The committed Phase 11 baseline yields the four selected stories. [AC-1.1]"""
        out = tmp_path / "t.json"
        result = _main(harness, capsys, "init", "--baseline", REAL_BASELINE, "--out", out,
                       "--repo", _probe_repo(tmp_path))
        assert_ran(result)
        expected = [e["story_id"] for e in _read(REAL_BASELINE)["selection"]]
        assert [s["story_id"] for s in _read(out)["stories"]] == expected
        assert len(expected) == 4

    def test_cli_entry_point(self, tmp_path):
        result = _cli("init", "--baseline", MINI_BASELINE, "--out", tmp_path / "t.json",
                      "--repo", _probe_repo(tmp_path))
        assert_ran(result)


class TestInitYussSnapshot:
    """`init --yuss` records a read-only before-snapshot; yuss is unchanged. [AC-1.1, AC-1.3]"""

    def test_before_snapshot_is_hashes_only(self, harness, capsys, tmp_path):
        yuss, _base, _parent, commit = _build_yuss(tmp_path)
        (yuss / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        before = _snapshot(yuss)
        out = tmp_path / "t.json"
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                       "--repo", _probe_repo(tmp_path), "--yuss", yuss)
        assert_ran(result)
        assert _snapshot(yuss) == before
        snap = _read(out)["yuss_snapshot"]
        assert snap["after"] is None and snap["unchanged"] is None
        refs = subprocess.run(["git", "-C", str(yuss), "show-ref"], capture_output=True,
                              env=_env()).stdout
        status = subprocess.run(["git", "-C", str(yuss), "status", "--porcelain"],
                                capture_output=True, env=_env()).stdout
        assert snap["before"] == {
            "head": commit,
            "refs_sha256": hashlib.sha256(refs).hexdigest(),
            "status_sha256": hashlib.sha256(status).hexdigest(),
        }
        assert any(line.startswith("yuss: before ") for line in result.out)

    def test_missing_yuss_refuses(self, harness, capsys, tmp_path):
        out = tmp_path / "t.json"
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                       "--repo", _probe_repo(tmp_path), "--yuss", tmp_path / "no-yuss")
        assert_refused(result, "yuss_missing")
        assert not out.exists()

    def test_non_git_yuss_refuses(self, harness, capsys, tmp_path):
        plain = tmp_path / "plain"
        plain.mkdir()
        out = tmp_path / "t.json"
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                       "--repo", _probe_repo(tmp_path), "--yuss", plain)
        assert_refused(result, "yuss_missing")
        assert not out.exists()

    def test_subdirectory_of_a_repo_is_not_yuss(self, harness, capsys, tmp_path):
        yuss, _base, _parent, _commit = _build_yuss(tmp_path)
        out = tmp_path / "t.json"
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                       "--repo", _probe_repo(tmp_path), "--yuss", yuss / "lib")
        assert_refused(result, "yuss_missing")
        assert not out.exists()


class TestInitRefusals:
    """Every `init` refusal exits 2 with one `reason:` line and leaves `--out` unchanged. [AC-1.2]"""

    def _refused(self, harness, capsys, tmp_path, baseline: Path, code: str,
                 extra: Sequence[object] = ()) -> None:
        out = tmp_path / "t.json"
        result = _main(harness, capsys, "init", "--baseline", baseline, "--out", out,
                       "--repo", _probe_repo(tmp_path), *extra)
        assert_refused(result, code)
        assert not out.exists()

    def test_missing_baseline(self, harness, capsys, tmp_path):
        self._refused(harness, capsys, tmp_path, tmp_path / "nope.json", "baseline_unreadable")

    def test_unparseable_baseline(self, harness, capsys, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        self._refused(harness, capsys, tmp_path, bad, "baseline_unreadable")

    def test_baseline_not_an_object(self, harness, capsys, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("[1, 2]", encoding="utf-8")
        self._refused(harness, capsys, tmp_path, bad, "baseline_unreadable")

    @pytest.mark.parametrize("count", [0, 3, 5])
    def test_selection_not_four_stories(self, harness, capsys, tmp_path, count):
        def mutate(doc):
            entries = doc["selection"]
            doc["selection"] = (entries + entries)[:count]
        self._refused(harness, capsys, tmp_path, _baseline_with(tmp_path, mutate),
                      "selection_invalid")

    def test_selection_not_a_list(self, harness, capsys, tmp_path):
        def mutate(doc):
            doc["selection"] = {"a": 1}
        self._refused(harness, capsys, tmp_path, _baseline_with(tmp_path, mutate),
                      "selection_invalid")

    def test_selection_entry_not_an_object(self, harness, capsys, tmp_path):
        def mutate(doc):
            doc["selection"][3] = "story"
        self._refused(harness, capsys, tmp_path, _baseline_with(tmp_path, mutate),
                      "selection_invalid")

    @pytest.mark.parametrize("field", IDENTITY)
    def test_selection_entry_missing_an_identity_field(self, harness, capsys, tmp_path, field):
        def mutate(doc):
            del doc["selection"][1][field]
        self._refused(harness, capsys, tmp_path, _baseline_with(tmp_path, mutate),
                      "selection_invalid")

    def test_duplicate_story_id(self, harness, capsys, tmp_path):
        def mutate(doc):
            doc["selection"][1]["story_id"] = doc["selection"][0]["story_id"]
        self._refused(harness, capsys, tmp_path, _baseline_with(tmp_path, mutate),
                      "selection_invalid")

    @pytest.mark.parametrize("field,value", [
        ("story_commit", "--upload-pack=evil"),
        ("story_commit", "ABCDEF1234567"),
        ("parent_sha", "12345"),
        ("parent_sha", "g" * 40),
    ])
    def test_non_hex_sha(self, harness, capsys, tmp_path, field, value):
        def mutate(doc):
            doc["selection"][2][field] = value
        self._refused(harness, capsys, tmp_path, _baseline_with(tmp_path, mutate), "bad_sha")

    @pytest.mark.parametrize("field,value", [
        ("story_path", "../outside.md"),
        ("story_path", "/etc/passwd"),
        ("spec_folder", "a/../../b"),
        ("story_id", "-rf/story-1"),
    ])
    def test_unsafe_path(self, harness, capsys, tmp_path, field, value):
        def mutate(doc):
            doc["selection"][2][field] = value
        self._refused(harness, capsys, tmp_path, _baseline_with(tmp_path, mutate),
                      "unsafe_path")

    def test_existing_out_without_force(self, harness, capsys, tmp_path):
        out = tmp_path / "t.json"
        out.write_text("keep me", encoding="utf-8")
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                       "--repo", _probe_repo(tmp_path))
        assert_refused(result, "out_exists")
        assert out.read_text(encoding="utf-8") == "keep me"

    def test_bad_baseline_with_force_leaves_out_unchanged(self, harness, capsys, tmp_path):
        out = tmp_path / "t.json"
        out.write_text("keep me", encoding="utf-8")
        result = _main(harness, capsys, "init", "--baseline", tmp_path / "nope.json",
                       "--out", out, "--repo", _probe_repo(tmp_path), "--force")
        assert_refused(result, "baseline_unreadable")
        assert out.read_text(encoding="utf-8") == "keep me"

    def test_missing_repo(self, harness, capsys, tmp_path):
        out = tmp_path / "t.json"
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                       "--repo", tmp_path / "no-repo")
        assert_refused(result, "repo_missing")
        assert not out.exists()

    def test_usage_error_exits_2(self, harness, capsys, tmp_path):
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE)
        assert result.code == 2
        assert result.out == []

    def test_cli_refusal_shape(self, tmp_path):
        result = _cli("init", "--baseline", tmp_path / "nope.json", "--out", tmp_path / "t.json",
                      "--repo", tmp_path)
        assert_refused(result, "baseline_unreadable")


# --- prepare: happy path (one shared CLI run) -------------------------------

class TestPrepareInputs:
    """`prepare` builds read-only inputs under the tmp root; yuss is unchanged. [AC-1.3]"""

    def test_runs_and_leaves_yuss_unchanged(self, prepared):
        assert_ran(prepared.result)
        assert prepared.yuss_after == prepared.yuss_before

    def test_checkout_is_at_the_story_commit_with_no_remote(self, prepared):
        checkout = prepared.run / "checkout"
        assert _git(checkout, "rev-parse", "HEAD") == prepared.commit
        assert _git(checkout, "remote") == ""

    def test_parent_worktree_is_at_the_parent_sha(self, prepared):
        parent = prepared.run / "parent"
        assert _git(parent, "rev-parse", "HEAD") == prepared.parent
        assert (parent / "lib" / "payments.py").read_text(encoding="utf-8") == (
            "def pay(amount):\n    return amount\n")

    def test_diff_story_and_contract(self, prepared):
        diff = (prepared.run / "diff.patch").read_text(encoding="utf-8")
        assert "+    return round(amount, 2)" in diff
        assert "Completed ✅" in (prepared.run / "story.md").read_text(encoding="utf-8")
        contract = (prepared.run / "contract.md").read_text(encoding="utf-8")
        assert "Deliverable: a payment helper." in contract
        assert "not part of the contract" not in contract

    def test_output_names_every_path(self, prepared):
        """Check shape: pass first, every written path printed, summary last. [AC-1.3, AC-1.4]"""
        out = prepared.result.out
        run = prepared.run
        expected = {
            "checkout": run / "checkout", "parent": run / "parent",
            "diff": run / "diff.patch", "story": run / "story.md",
            "contract": run / "contract.md", "tests": run / "tests.txt",
            "boundary": run / "boundary.json", "routes-json": run / "routes.json",
            "blast-radius": run / "blast-radius.json",
        }
        for label, path in expected.items():
            assert "%s: %s" % (label, path) in out, (label, out)
        for arm in ARMS:
            assert "arm: %s %s" % (arm, run / "arms" / arm / ".writ" / "config.md") in out
        assert out[-1] == "gate-upgrade-trial: prepared %s at %s" % (S1, prepared.commit[:12])
        assert prepared.result.err == []


class TestPrepareRoutes:
    """Routes come from the Gate 2.5 and Gate 0 route scripts and are stored atomically. [AC-1.4]"""

    def test_routes_stored_in_the_trial_file(self, prepared):
        doc = _read(prepared.trial)
        assert _story(doc, S1)["routes"] == {
            "surface": "cross-component",
            "gate3_route": "review-agent",          # lib/other.py crosses the boundary
            "planned_surface": "cross-component",
            "gate0_route": "evaluator-agent",       # owned lib/payments.py: no crossing
        }
        assert "routes: surface=cross-component gate3_route=review-agent " \
               "planned_surface=cross-component gate0_route=evaluator-agent" in prepared.result.out

    def test_only_this_storys_routes_change(self, prepared):
        after = _read(prepared.trial)
        before = prepared.trial_before
        _story(after, S1)["routes"] = None
        assert after == before
        assert sorted(p.name for p in prepared.trial.parent.iterdir()) == ["trial.json"]

    def test_routes_json_and_boundary_json(self, prepared):
        boundary = _read(prepared.run / "boundary.json")
        assert boundary["owned"] == ["lib/payments.py"]
        routes = _read(prepared.run / "routes.json")
        assert routes["gate3"]["surface"] == "cross-component"
        assert routes["gate3"]["crossings"]["reasons"] == ["outside_boundary lib/other.py"]
        assert routes["gate0"]["planned"] == ["lib/payments.py"]
        assert routes["gate0"]["crossings"]["route"] == "evaluator-agent"

    def test_blast_radius_written_for_review_agent_with_safety_fact(self, prepared):
        blast = _read(prepared.run / "blast-radius.json")
        assert blast["verdict"] == "pass"
        assert blast["consumers"]["lib/payments.py"] == ["app/checkout.py"]
        assert blast["tests"]["lib/payments.py"] == ["tests/test_payments.py"]


class TestPrepareTestsFile:
    """`tests.txt` holds historical results only, never an `exit code:` line. [AC-1.4]"""

    def test_historical_results_without_exit_code(self, prepared):
        lines = (prepared.run / "tests.txt").read_text(encoding="utf-8").splitlines()
        assert lines[0] == "historical, not re-run"
        assert "- 12 passed in 0.4s" in lines
        assert "- coverage 91%" in lines
        assert not any(line.strip().lower().startswith("exit code:") for line in lines)
        assert "### Files Changed" not in lines
        assert "- lib/payments.py" not in lines

    def test_placeholder_when_the_story_has_no_results(self, standin):
        standin.story_commit({STORY_REL: _story_text(TASKS_PAYMENTS, built=""),
                              "lib/payments.py": "def pay(a):\n    return a\n"})
        assert_ran(standin.prepare())
        assert (standin.run / "tests.txt").read_text(encoding="utf-8").splitlines() == [
            "historical, not re-run", "(no historical test results in the story file)"]


class TestPrepareArmConfigs:
    """One config per arm with exact `on`/`off` switch lines (technical-spec § Arms). [AC-1.4]"""

    def test_all_six_arm_configs(self, prepared):
        for arm in ARMS:
            config = prepared.run / "arms" / arm / ".writ" / "config.md"
            states = _switch_lines(config)
            if arm in ("off-1", "off-2"):
                expected = {name: "off" for name in UPGRADES}
            else:
                expected = {name: ("on" if name == arm else "off") for name in UPGRADES}
            assert states == expected, arm

    def test_review_override_reads_the_arm_switches(self, prepared):
        script = REPO_ROOT / "scripts" / "review-override.py"
        for arm, name, state in (("off-1", "safety-fact", "off"),
                                 ("safety-fact", "safety-fact", "on"),
                                 ("safety-fact", "reviewer-filters", "off"),
                                 ("reviewer-filters", "reviewer-filters", "on")):
            proc = subprocess.run([sys.executable, str(script), "switch", "--name", name,
                                   "--repo", str(prepared.run / "arms" / arm)],
                                  capture_output=True, text=True)
            assert proc.stdout.splitlines()[0] == state, (arm, name, proc.stdout)


# --- prepare: route variants (function-scoped stand-ins) --------------------

class TestPrepareRouteVariants:
    """Each route branch, recomputed at run time. [AC-1.4]"""

    def test_full_stack_plan_routes_gate0_to_review_agent(self, standin):
        standin.story_commit({STORY_REL: _story_text(TASKS_ROUTE),
                              "app/api/pay/route.ts": "export const GET = 1;\n"})
        assert_ran(standin.prepare())
        assert standin.routes() == {"surface": "full-stack", "gate3_route": "review-agent",
                                    "planned_surface": "full-stack",
                                    "gate0_route": "review-agent"}
        assert _read(standin.run / "routes.json")["gate3"]["crossings"]["reasons"] == [
            "full_stack_surface"]

    def test_owned_only_change_routes_gate3_to_evaluator_and_skips_blast_radius(self, standin):
        standin.story_commit({"lib/payments.py": "def pay(a):\n    return a\n"})
        result = standin.prepare()
        assert_ran(result)
        assert standin.routes()["gate3_route"] == "evaluator-agent"
        assert not (standin.run / "blast-radius.json").exists()
        assert not any(line.startswith("blast-radius:") for line in result.out)

    def test_empty_planned_set_stores_gate0_skip(self, standin):
        """No planned files: `gate0_route: skip` with the reason. [AC-1.4]"""
        standin.story_commit({STORY_REL: _story_text(TASKS_NO_PATHS),
                              "lib/other.py": "VALUE = 3\n"})
        result = standin.prepare()
        assert_ran(result)
        assert standin.routes() == {"surface": "cross-component", "gate3_route": "review-agent",
                                    "planned_surface": None, "gate0_route": "skip",
                                    "gate0_reason": "unverifiable: no planned files"}
        assert "gate0_reason: unverifiable: no planned files" in result.out

    def test_malformed_story_makes_crossings_unverifiable(self, standin):
        """compute blocker: Gate 3 crossings read `unverifiable` → review-agent; Gate 0 skips. [AC-1.4]"""
        standin.story_commit({STORY_REL: _story_text(None),
                              "lib/payments.py": "def pay(a):\n    return a\n"})
        assert_ran(standin.prepare())
        routes = standin.routes()
        assert routes["gate3_route"] == "review-agent"
        assert routes["gate0_route"] == "skip"
        assert routes["gate0_reason"].startswith("unverifiable: ")
        assert "blocker" in _read(standin.run / "boundary.json")
        gate3 = _read(standin.run / "routes.json")["gate3"]["crossings"]
        assert gate3["verdict"] == "unverifiable"

    def test_archived_story_path_is_the_fallback(self, standin):
        standin.story_commit({
            STORY_REL: None, SPEC_REL: None,
            ARCHIVE_STORY_REL: _story_text(TASKS_PAYMENTS),
            ARCHIVE_SPEC_REL: SPEC_TEXT,
            "lib/payments.py": "def pay(a):\n    return a\n",
        })
        assert_ran(standin.prepare())
        assert _read(standin.run / "boundary.json")["owned"] == ["lib/payments.py"]
        assert standin.routes()["gate3_route"] == "evaluator-agent"

    def test_safety_fact_absent_skips_blast_radius(self, tmp_path, harness, capsys):
        standin = StandIn(tmp_path, harness, capsys,
                          present=("gate0-divergence", "reviewer-filters", "repro-first"))
        assert_ran(standin.prepare())
        assert standin.routes()["gate3_route"] == "review-agent"
        assert not (standin.run / "blast-radius.json").exists()

    def test_existing_run_dir_is_replaced(self, standin):
        standin.run.mkdir()
        (standin.run / "stale.txt").write_text("old\n", encoding="utf-8")
        assert_ran(standin.prepare())
        assert not (standin.run / "stale.txt").exists()
        assert (standin.run / "checkout").is_dir()


# --- prepare: refusals ------------------------------------------------------

class TestPrepareRefusals:
    """Every `prepare` refusal: exit 2, one line naming the story, no run dir, trial unchanged. [AC-1.5]"""

    def _assert_untouched(self, standin: StandIn, trial_bytes: bytes,
                          yuss_before: Tuple[str, ...]) -> None:
        assert list(standin.tmp_root.iterdir()) == []
        assert standin.trial.read_bytes() == trial_bytes
        assert _snapshot(standin.yuss) == yuss_before

    def _refuse(self, standin: StandIn, code: str, story: str = S1, **kwargs) -> Result:
        trial_bytes = standin.trial.read_bytes()
        before = _snapshot(standin.yuss)
        result = standin.prepare(story=story, **kwargs)
        assert_refused(result, code)
        self._assert_untouched(standin, trial_bytes, before)
        return result

    def test_missing_yuss(self, standin):
        result = self._refuse(standin, "yuss_missing", yuss=standin.root / "no-such-yuss")
        assert result.err[0].startswith("reason: yuss_missing — %s: " % S1)

    def test_non_git_yuss(self, standin):
        plain = standin.root / "plain"
        plain.mkdir()
        self._refuse(standin, "yuss_missing", yuss=plain)

    def test_unreachable_commit(self, standin):
        result = self._refuse(standin, "sha_unreachable", story=S2)
        assert result.err[0].startswith("reason: sha_unreachable — %s: " % S2)

    def test_unreachable_parent(self, standin):
        standin.retarget(standin.commit, "ab" * 20)
        result = self._refuse(standin, "sha_unreachable")
        assert "parent_sha" in result.err[0]

    def test_parent_beyond_depth_2_removes_the_run_dir(self, standin):
        """The parent exists in yuss but not within depth 2 of the commit. [AC-1.5]"""
        standin.retarget(standin.commit, standin.base)
        result = self._refuse(standin, "prepare_failed")
        assert "depth 2" in result.err[0]
        assert S1 in result.err[0]

    def test_tampered_sha_in_the_trial_file(self, standin):
        standin.retarget("--upload-pack=evil", standin.parent)
        self._refuse(standin, "bad_sha")

    def test_tampered_path_in_the_trial_file(self, standin):
        doc = _read(standin.trial)
        _story(doc, S1)["spec_folder"] = "../../etc"
        standin.trial.write_text(json.dumps(doc), encoding="utf-8")
        self._refuse(standin, "unsafe_path")

    def test_unknown_story(self, standin):
        result = self._refuse(standin, "story_unknown", story="nope/story-9")
        assert result.err[0].startswith("reason: story_unknown — nope/story-9: ")

    def test_missing_trial_file(self, standin):
        result = standin.prepare(trial=standin.root / "no-trial.json")
        assert_refused(result, "trial_invalid")
        assert list(standin.tmp_root.iterdir()) == []

    def test_wrong_schema(self, standin):
        doc = _read(standin.trial)
        doc["schema"] = "panel-trial-v1"
        standin.trial.write_text(json.dumps(doc), encoding="utf-8")
        self._refuse(standin, "trial_invalid")

    def test_review_panel_missing(self, standin, monkeypatch):
        monkeypatch.setattr(standin.harness, "REVIEW_PANEL", standin.root / "gone.py")
        result = self._refuse(standin, "review_panel_missing")
        assert not result.err[0].startswith("reason: review_panel_missing — %s" % S1)

    @pytest.mark.parametrize("missing", REUSED)
    def test_review_panel_lacks_a_reused_name(self, standin, monkeypatch, missing):
        stub = standin.root / "review-panel-stub.py"
        body = ["class PrepareError(Exception):", "    pass", ""]
        for name in REUSED:
            if name != missing:
                body += ["def %s(*args, **kwargs):" % name, "    return None", ""]
        stub.write_text("\n".join(body), encoding="utf-8")
        monkeypatch.setattr(standin.harness, "REVIEW_PANEL", stub)
        result = self._refuse(standin, "review_panel_missing")
        assert missing in result.err[0]

    def test_review_panel_that_fails_to_load(self, standin, monkeypatch):
        stub = standin.root / "review-panel-broken.py"
        stub.write_text("def broken(:\n", encoding="utf-8")
        monkeypatch.setattr(standin.harness, "REVIEW_PANEL", stub)
        self._refuse(standin, "review_panel_missing")

    @pytest.mark.parametrize("mode,fragment", [
        ("classify-exit-2", "change-surface classify (changed files) exited 2"),
        ("classify-unknown", "unknown class: 'weird'"),
        ("compute-exit-2", "boundary-map compute exited 2"),
        ("compute-not-json", "boundary-map compute printed no JSON object"),
        ("crossings-no-route", "boundary-map crossings (changed files) printed no route"),
    ])
    def test_route_script_failure_removes_the_run_dir(self, standin, monkeypatch, mode,
                                                      fragment):
        """A route script that exits 2 or prints nothing usable: `route_failed`. [AC-1.5]"""
        monkeypatch.setattr(standin.harness, "SCRIPTS", _stub_scripts(standin.root))
        monkeypatch.setenv(STUB_ENV, mode)
        result = self._refuse(standin, "route_failed")
        assert result.err[0].startswith("reason: route_failed — %s: " % S1)
        assert fragment in result.err[0]

    def test_blast_radius_absent_while_safety_fact_present(self, standin, monkeypatch):
        """The `blast-radius` subcommand is missing (argparse exit 2). [AC-1.5]"""
        monkeypatch.setattr(standin.harness, "SCRIPTS", _stub_scripts(standin.root))
        monkeypatch.setenv(STUB_ENV, "no-blast-radius")
        result = self._refuse(standin, "blast_radius_unavailable")
        assert "exited 2" in result.err[0]

    def test_blast_radius_without_json_is_unavailable(self, standin, monkeypatch):
        monkeypatch.setattr(standin.harness, "SCRIPTS", _stub_scripts(standin.root))
        monkeypatch.setenv(STUB_ENV, "blast-not-json")
        result = self._refuse(standin, "blast_radius_unavailable")
        assert "printed no JSON object" in result.err[0]

    @pytest.mark.parametrize("verb", ["worktree", "diff"])
    def test_git_failure_after_the_fetch_removes_the_run_dir(self, standin, monkeypatch, verb):
        _fail_git(monkeypatch, standin.harness, verb)
        self._refuse(standin, "prepare_failed")

    def test_review_panel_without_a_python_suffix(self, standin, monkeypatch):
        stub = standin.root / "review-panel.txt"
        stub.write_text("x = 1\n", encoding="utf-8")
        monkeypatch.setattr(standin.harness, "REVIEW_PANEL", stub)
        self._refuse(standin, "review_panel_missing")

    def test_cli_refusal_shape(self, standin):
        result = _cli("prepare", "--trial", standin.trial, "--story", S2,
                      "--yuss", standin.yuss, "--tmp-root", standin.tmp_root)
        assert_refused(result, "sha_unreachable")


class TestPrepareStubbedRoutes:
    """Gate 0 crossings that read `unverifiable` store a skip with the reason. [AC-1.4]"""

    def test_unverifiable_gate0_crossings_store_skip(self, standin, monkeypatch):
        monkeypatch.setattr(standin.harness, "SCRIPTS", _stub_scripts(standin.root))
        monkeypatch.setenv(STUB_ENV, "gate0-unverifiable")
        assert_ran(standin.prepare())
        assert standin.routes() == {"surface": "cross-component", "gate3_route": "review-agent",
                                    "planned_surface": "cross-component", "gate0_route": "skip",
                                    "gate0_reason": "unverifiable: map_unreadable"}


class TestInitYussFailures:
    """`init --yuss` refuses when git cannot read yuss. [AC-1.2]"""

    def test_yuss_without_commits(self, harness, capsys, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        _git(empty, "init", "-q")
        out = tmp_path / "t.json"
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                       "--repo", _probe_repo(tmp_path), "--yuss", empty)
        assert_refused(result, "yuss_missing")
        assert not out.exists()

    def test_unreadable_status(self, harness, capsys, tmp_path, monkeypatch):
        yuss, _base, _parent, _commit = _build_yuss(tmp_path)
        _fail_git(monkeypatch, harness, "status")
        out = tmp_path / "t.json"
        result = _main(harness, capsys, "init", "--baseline", MINI_BASELINE, "--out", out,
                       "--repo", _probe_repo(tmp_path), "--yuss", yuss)
        assert_refused(result, "yuss_missing")
        assert not out.exists()


def _fail_git(monkeypatch, harness: ModuleType, verb: str) -> None:
    """Make the harness's own `git` helper fail for one git verb."""
    real = harness.git

    def failing(cwd, *args):
        if args and args[0] == verb:
            return subprocess.CompletedProcess(["git", *args], 1, b"", b"")
        return real(cwd, *args)

    monkeypatch.setattr(harness, "git", failing)


# Stub route scripts: each delegates to the real script unless the mode in
# STUB_ENV names a rule (subcommand, an argv token whose presence disables the
# rule or None, stdout, exit code). The env var reaches the subprocesses.
STUB_ENV = "GATE_UPGRADE_TRIAL_STUB"
UNVERIFIABLE = json.dumps({"verdict": "unverifiable", "route": "review-agent",
                           "reasons": ["map_unreadable"], "summary": "stub"})
STUB_MODES = {
    "change-surface.py": {
        "classify-exit-2": ("classify", None, "", 2),
        "classify-unknown": ("classify", None, "weird\n", 0),
        "no-blast-radius": ("blast-radius", None, "", 2),
        "blast-not-json": ("blast-radius", None, "nope\n", 0),
    },
    "boundary-map.py": {
        "compute-exit-2": ("compute", None, "", 2),
        "compute-not-json": ("compute", None, "not json\n", 0),
        "crossings-no-route": ("crossings", None, "{}\n", 0),
        # Only the Gate 0 run (planned files) lacks lib/other.py.
        "gate0-unverifiable": ("crossings", "lib/other.py", UNVERIFIABLE + "\n", 0),
    },
}
STUB_TEMPLATE = """import os
import runpy
import sys
REAL = {real!r}
RULE = {modes!r}.get(os.environ.get({env!r}, ""))
ARGV = sys.argv[1:]
if RULE is not None and ARGV[:1] == [RULE[0]] and (RULE[1] is None or RULE[1] not in ARGV):
    sys.stdout.write(RULE[2])
    sys.exit(RULE[3])
sys.argv[0] = REAL
runpy.run_path(REAL, run_name="__main__")
"""


def _stub_scripts(root: Path) -> Path:
    """A scripts dir whose route scripts delegate to the real ones unless stubbed."""
    stub = root / "stub-scripts"
    stub.mkdir()
    for name, modes in STUB_MODES.items():
        (stub / name).write_text(STUB_TEMPLATE.format(
            real=str(REPO_ROOT / "scripts" / name), modes=modes, env=STUB_ENV),
            encoding="utf-8")
    return stub


# =============================================================================
# Story 2: record, snapshot, sheet, label, report
# [AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]
# =============================================================================

S3, S4 = ALL_STORIES[2], ALL_STORIES[3]
SLUG1 = "2026-01-01-alpha--story-1-api"

ROUTES_RR = {"surface": "full-stack", "gate3_route": "review-agent",
             "planned_surface": "full-stack", "gate0_route": "review-agent"}
ROUTES_RE = {"surface": "full-stack", "gate3_route": "review-agent",
             "planned_surface": "cross-component", "gate0_route": "evaluator-agent"}
ROUTES_ER = {"surface": "single-component", "gate3_route": "evaluator-agent",
             "planned_surface": "full-stack", "gate0_route": "review-agent"}
ROUTES_RS = {"surface": "cross-component", "gate3_route": "review-agent",
             "planned_surface": None, "gate0_route": "skip",
             "gate0_reason": "unverifiable: no planned files"}
DEFAULT_ROUTES = {S1: ROUTES_RR, S2: ROUTES_RE, S3: ROUTES_ER, S4: ROUTES_RS}
ALL_EVALUATOR = {sid: {"surface": "single-component", "gate3_route": "evaluator-agent",
                       "planned_surface": "single-component", "gate0_route": "evaluator-agent"}
                 for sid in ALL_STORIES}

OFF_STATES = ("safety-fact=off", "reviewer-filters=off")
STATES = {
    "off-1": OFF_STATES,
    "off-2": OFF_STATES,
    "reviewer-filters": ("reviewer-filters=on", "safety-fact=off"),
    "safety-fact": ("safety-fact=on", "reviewer-filters=off"),
    "gate0-divergence": (),
    "repro-first": (),
}
CHOSE = "gate0-divergence: chose B (sketch B keeps the ledger in one module)"
SKIP = "gate0-divergence: skip (sketch incomplete: sketch A has no Files line)"
VERIFIER_PASS = FIXTURES / "verifier-pass.txt"
BUG_FAIL_FAIL = ("--kind", "bug", "--repro-ac", "AC-1.3", "--at-parent", "fail",
                 "--at-commit", "fail")

AC12 = "ac:AC-1.2"
PAY_ROUTE = "security:app/api/pay/route.ts"
WEBHOOK = "security:app/api/pay/webhook.ts"
FEES = "architecture:lib/fees.ts"
LEDGER = "architecture:lib/ledger.ts"
FEE_SHARE = "security:app/api/events/[id]/fee-share/route.ts"
SETTLE = "architecture:#" + hashlib.sha256(b"nightly settle job").hexdigest()[:12]
REPRO_KEY = "ac:AC-1.3"

SAMPLE_LINE = ("sample: 4 stories, two current-gates runs, one run per upgrade arm; one valid "
               "catch keeps an upgrade — a low bar, not a cost case")
PROXY_LINE = ("proxy: Gate 0 and Repro First arms are retrospective proxies (sketch comparison, "
              "repro re-run), not replays")
BLINDING_LINE = ("blinding: honor system — the sheet hides which upgrade raised a finding, but the "
                 "trial file and raw outputs map IDs to arms, and Gate 0 excerpts show their "
                 "Avoided by line")
SHEET_HEADER = ("> Fill every `label:` with `valid` or `invalid` (spec.md Business Rule 6), "
                "optionally a one-line `note:` (at most 200 characters, no backticks), and every "
                "`ack:` with `remove` or `amend` (Rule 7). Do not change any other line. See "
                "rating-handoff.md.")
NO_MATCH = "(no matching block found in the raw output)"


def _call(harness: ModuleType, *args: object) -> Result:
    """`main([...])` in-process without capsys (usable from module-scoped fixtures)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = harness.main([str(a) for a in args])
    return Result(code, out.getvalue().splitlines(), err.getvalue().splitlines())


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(root: Path) -> List[Tuple[str, str]]:
    """Every file under root with its digest (empty when root is absent)."""
    if not root.exists():
        return []
    return sorted((str(p.relative_to(root)), _sha(p)) for p in root.rglob("*") if p.is_file())


class Trial:
    """A trial file from `init` with routes written directly (no prepare), a tmp
    state dir, and helpers that call the harness in-process. `history` keeps the
    trial file's text after every successful harness call (the AC-2.5 scan)."""

    def __init__(self, root: Path, harness: ModuleType, present: Sequence[str] = UPGRADES,
                 routes: Optional[Dict[str, Optional[dict]]] = None,
                 yuss: Optional[Path] = None) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.root, self.harness = root, harness
        self.trial = root / "trial.json"
        self.state = root / "state"
        self.sheet_path = root / "labeling-sheet.md"
        self.history: List[str] = []
        args: List[object] = ["init", "--baseline", MINI_BASELINE, "--out", self.trial,
                              "--repo", _probe_repo(root, present)]
        if yuss is not None:
            args += ["--yuss", yuss]
        assert_ran(self.call(*args))
        self.set_routes(DEFAULT_ROUTES if routes is None else routes)

    def call(self, *args: object) -> Result:
        result = _call(self.harness, *args)
        if result.code == 0 and self.trial.exists():
            self.history.append(self.trial.read_text(encoding="utf-8"))
        return result

    def doc(self) -> dict:
        return _read(self.trial)

    def write(self, doc: dict) -> None:
        self.trial.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def set_routes(self, routes: Dict[str, Optional[dict]]) -> None:
        doc = self.doc()
        for story in doc["stories"]:
            story["routes"] = routes.get(story["story_id"])
        self.write(doc)

    def story(self, story_id: str) -> dict:
        return _story(self.doc(), story_id)

    def raw(self) -> bytes:
        return self.trial.read_bytes()

    def record(self, story: str, arm: str, output: object, *extra: object,
               states: Optional[Sequence[str]] = None) -> Result:
        path = output if isinstance(output, Path) else FIXTURES / str(output)
        args: List[object] = ["record", "--trial", self.trial, "--story", story, "--arm", arm,
                              "--output", path, "--state-dir", self.state]
        for value in STATES[arm] if states is None else states:
            args += ["--state", value]
        return self.call(*args, *extra)

    def ok(self, story: str, arm: str, output: object, *extra: object,
           states: Optional[Sequence[str]] = None) -> Result:
        result = self.record(story, arm, output, *extra, states=states)
        assert_ran(result)
        return result

    def off(self, story: str, output: str = "off-fail.md", off2: Optional[str] = None) -> None:
        self.ok(story, "off-1", output)
        self.ok(story, "off-2", off2 or output)

    def safety(self, story: str, output: str = "safety-on.md",
               verifier: Path = VERIFIER_PASS) -> Result:
        return self.ok(story, "safety-fact", output, "--verifier", verifier)

    def gate0(self, story: str, output: str = "gate0-comparison.md", line: str = CHOSE) -> Result:
        return self.ok(story, "gate0-divergence", output, "--report-line", line)

    def repro(self, story: str, *flags: str, output: object = "repro-not-bug.md") -> Result:
        return self.ok(story, "repro-first", output, *(flags or ("--kind", "not-a-bug-fix")))

    def sheet(self, *extra: object) -> Result:
        return self.call("sheet", "--trial", self.trial, "--out", self.sheet_path,
                         "--state-dir", self.state, *extra)

    def label(self, sheet: Optional[Path] = None, name: str = "A. Maintainer") -> Result:
        return self.call("label", "--trial", self.trial, "--sheet", sheet or self.sheet_path,
                         "--labeled-by", name)

    def report(self, *extra: object) -> Result:
        return self.call("report", "--trial", self.trial, *extra)

    def sheet_text(self) -> str:
        return self.sheet_path.read_text(encoding="utf-8")

    def fill(self, **kwargs) -> Path:
        self.sheet_path.write_text(_fill(self.sheet_text(), **kwargs), encoding="utf-8")
        return self.sheet_path


def _record_e2e(t: Trial) -> None:
    """reviewer-filters absent: every applicable arm on the four default-route stories."""
    t.off(S1)
    t.safety(S1)
    t.gate0(S1)
    t.repro(S1)
    t.off(S2, "off-pass.md")
    t.safety(S2, "safety-on-pass.md")
    t.repro(S2)
    t.off(S3, "off-pass.md")
    t.gate0(S3, "gate0-no-avoided.md", SKIP)
    t.repro(S3)
    t.off(S4)
    t.safety(S4)
    t.repro(S4)


def _record_full(t: Trial) -> None:
    """All four upgrades present: every applicable arm, eight upgrade-only findings."""
    t.off(S1)
    t.ok(S1, "reviewer-filters", "filters-on.md")
    t.safety(S1)
    t.gate0(S1)
    t.repro(S1, *BUG_FAIL_FAIL, output="repro-bug.md")
    t.off(S2, "off-pass.md")
    t.ok(S2, "reviewer-filters", "off-pass.md")
    t.safety(S2, "safety-on-pass.md")
    t.repro(S2)
    t.off(S3, "off-pass.md")
    t.ok(S3, "reviewer-filters", "off-pass.md")
    t.gate0(S3, "gate0-no-avoided.md", SKIP)
    t.repro(S3)
    t.off(S4)
    t.ok(S4, "reviewer-filters", "filters-on.md")
    t.safety(S4)
    t.repro(S4)


FULL_UPGRADE_ONLY = {
    (S1, "reviewer-filters", SETTLE), (S1, "reviewer-filters", FEE_SHARE),
    (S1, "safety-fact", FEES), (S1, "gate0-divergence", WEBHOOK),
    (S1, "repro-first", REPRO_KEY),
    (S4, "reviewer-filters", SETTLE), (S4, "reviewer-filters", FEE_SHARE),
    (S4, "safety-fact", FEES),
}


def _fill(text: str, label: str = "invalid",
          labels: Optional[Dict[Tuple[str, str], str]] = None,
          notes: Optional[Dict[Tuple[str, str], str]] = None,
          acks: Optional[Dict[str, str]] = None, ack: str = "remove") -> str:
    """Fill a sheet's blank fields by (story, key) and upgrade."""
    labels, notes, acks = labels or {}, notes or {}, acks or {}
    out: List[str] = []
    story = key = upgrade = None
    for line in text.split("\n"):
        if line.startswith("story: "):
            story = line[len("story: "):]
        elif line.startswith("key: "):
            key = line[len("key: "):]
        elif line.startswith("### not exercised: "):
            upgrade = line[len("### not exercised: "):]
        if line == "label:":
            line = "label: %s" % labels.get((story, key), label)
        elif line == "note:" and (story, key) in notes:
            line = "note: %s" % notes[(story, key)]
        elif line == "ack:":
            line = "ack: %s" % acks.get(upgrade, ack)
        out.append(line)
    return "\n".join(out)


def _sheet_entries(text: str) -> Dict[str, Dict[str, str]]:
    """`### Fnn` blocks of a sheet → {field: value}."""
    entries: Dict[str, Dict[str, str]] = {}
    current: Optional[Dict[str, str]] = None
    for line in text.splitlines():
        match = re.match(r"^### (F\d+)$", line)
        if match:
            current = entries.setdefault(match.group(1), {})
            continue
        if line.startswith("#"):
            current = None
            continue
        if current is not None and ":" in line:
            field, _, value = line.partition(":")
            current[field] = value.strip()
    return entries


def _all_findings(doc: dict) -> List[Tuple[str, dict]]:
    return [(s["story_id"], e) for s in doc["stories"] for e in s["upgrade_only"]]


def _load_review_panel() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gate_trial_test_review_panel",
                                                  REPO_ROOT / "scripts" / "review-panel.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _norm_hash(text: str) -> str:
    return hashlib.sha256(re.sub(r"(?m)^(label|note|ack):.*$", r"\1:", text)
                          .encode("utf-8")).hexdigest()


@pytest.fixture
def trial(tmp_path: Path, harness: ModuleType) -> Trial:
    return Trial(tmp_path / "t", harness)


@pytest.fixture
def full(tmp_path: Path, harness: ModuleType) -> Trial:
    t = Trial(tmp_path / "full", harness)
    _record_full(t)
    return t


# --- record: evidence refusals ------------------------------------------------

class TestRecordEvidenceRefusals:
    """`record` refuses arm evidence that does not match the arm; the trial file
    and the state dir are unchanged. [AC-2.1]"""

    @pytest.fixture
    def offs(self, trial: Trial) -> Trial:
        trial.off(S1)
        return trial

    @staticmethod
    def refused(t: Trial, code: str, story: str, arm: str, output: object, *extra: object,
                states: Optional[Sequence[str]] = None) -> Result:
        before, state_before = t.raw(), _tree(t.state)
        result = t.record(story, arm, output, *extra, states=states)
        assert_refused(result, code)
        assert t.raw() == before
        assert _tree(t.state) == state_before
        return result

    def test_safety_fact_output_without_a_safety_fact_heading(self, offs):
        result = self.refused(offs, "evidence_mismatch", S1, "safety-fact", "off-fail.md",
                              "--verifier", VERIFIER_PASS)
        assert "Safety Fact" in result.err[0]

    def test_off_arm_output_with_a_safety_fact_heading(self, offs):
        self.refused(offs, "evidence_mismatch", S1, "off-1", "safety-on.md")

    def test_off_2_output_with_a_safety_fact_heading(self, trial):
        trial.ok(S1, "off-1", "off-fail.md")
        self.refused(trial, "evidence_mismatch", S1, "off-2", "safety-on-pass.md")

    def test_reviewer_filters_output_with_a_safety_fact_heading(self, offs):
        self.refused(offs, "evidence_mismatch", S1, "reviewer-filters", "safety-on.md")

    @pytest.mark.parametrize("arm,states", [
        ("off-1", ("safety-fact=on", "reviewer-filters=off")),
        ("off-1", ("safety-fact=off", "reviewer-filters=on")),
        ("off-1", ("safety-fact=off",)),
        ("off-2", ("reviewer-filters=off",)),
        ("off-2", ("safety-fact=off", "reviewer-filters=off", "repro-first=on")),
        ("off-1", ()),
        ("reviewer-filters", ("reviewer-filters=off", "safety-fact=off")),
        ("reviewer-filters", ("reviewer-filters=on", "safety-fact=on")),
        ("reviewer-filters", ("reviewer-filters=on",)),
        ("reviewer-filters", ("reviewer-filters=on", "safety-fact=off", "gate0-divergence=on")),
        ("safety-fact", ("safety-fact=on", "reviewer-filters=on")),
        ("safety-fact", ("safety-fact=off", "reviewer-filters=off")),
        ("safety-fact", ("safety-fact=on",)),
    ])
    def test_states_that_do_not_match_the_arm(self, offs, arm, states):
        output = "safety-on.md" if arm == "safety-fact" else "filters-on.md"
        self.refused(offs, "evidence_mismatch", S1, arm, output, "--verifier", VERIFIER_PASS,
                     states=states)

    @pytest.mark.parametrize("value", ["safety-fact", "safety-fact=yes", "nonsense=on",
                                       "Safety-Fact=off", "safety-fact=ON", "=on"])
    def test_malformed_state(self, offs, value):
        self.refused(offs, "bad_state", S1, "reviewer-filters", "filters-on.md",
                     states=("reviewer-filters=on", value))

    def test_repeated_state(self, offs):
        self.refused(offs, "bad_state", S1, "reviewer-filters", "filters-on.md",
                     states=("reviewer-filters=on", "safety-fact=off", "safety-fact=off"))

    def test_safety_fact_without_a_verifier(self, offs):
        self.refused(offs, "verifier_missing", S1, "safety-fact", "safety-on.md")

    def test_safety_fact_with_a_missing_verifier_file(self, offs, tmp_path):
        self.refused(offs, "verifier_missing", S1, "safety-fact", "safety-on.md",
                     "--verifier", tmp_path / "nope.txt")

    @pytest.mark.parametrize("text", ["maybe\n", "", "\npass\n", "PASS\n"])
    def test_verifier_line_1_is_not_a_result(self, offs, tmp_path, text):
        verifier = tmp_path / "verifier.txt"
        verifier.write_text(text, encoding="utf-8")
        self.refused(offs, "evidence_mismatch", S1, "safety-fact", "safety-on.md",
                     "--verifier", verifier)

    def test_gate3_output_without_a_verdict_line(self, offs):
        self.refused(offs, "no_verdict", S1, "reviewer-filters", "gate0-comparison.md")

    @pytest.mark.parametrize("line", [None, "gate0-divergence: off", "gate0-divergence:",
                                      "gate0: chose B", "chose B", "skip"])
    def test_gate0_report_line_must_read_chose_or_skip(self, offs, line):
        extra = () if line is None else ("--report-line", line)
        self.refused(offs, "evidence_mismatch", S1, "gate0-divergence", "gate0-comparison.md",
                     *extra)

    @pytest.mark.parametrize("states", [("gate0-divergence=off",),
                                        ("gate0-divergence=on", "safety-fact=on")])
    def test_gate0_states_turn_on_only_gate0(self, offs, states):
        self.refused(offs, "evidence_mismatch", S1, "gate0-divergence", "gate0-comparison.md",
                     "--report-line", CHOSE, states=states)

    def test_repro_without_kind(self, offs):
        self.refused(offs, "evidence_mismatch", S1, "repro-first", "repro-bug.md")

    @pytest.mark.parametrize("drop", ["--repro-ac", "--at-parent", "--at-commit"])
    def test_repro_bug_without_all_three_fields(self, offs, drop):
        flags = list(BUG_FAIL_FAIL)
        at = flags.index(drop)
        del flags[at:at + 2]
        self.refused(offs, "evidence_mismatch", S1, "repro-first", "repro-bug.md", *flags)

    @pytest.mark.parametrize("ac", ["1.3", "AC-1", "ac-1.3", "AC-1.3a", "AC-1.3 "])
    def test_repro_ac_must_be_an_ac_id(self, offs, ac):
        self.refused(offs, "evidence_mismatch", S1, "repro-first", "repro-bug.md",
                     "--kind", "bug", "--repro-ac", ac, "--at-parent", "fail",
                     "--at-commit", "fail")

    @pytest.mark.parametrize("field", [("--repro-ac", "AC-1.3"), ("--at-parent", "fail"),
                                       ("--at-commit", "pass")])
    def test_not_a_bug_fix_takes_no_repro_field(self, offs, field):
        self.refused(offs, "evidence_mismatch", S1, "repro-first", "repro-not-bug.md",
                     "--kind", "not-a-bug-fix", *field)

    def test_repro_states_turn_on_only_repro(self, offs):
        self.refused(offs, "evidence_mismatch", S1, "repro-first", "repro-not-bug.md",
                     "--kind", "not-a-bug-fix", states=("repro-first=off",))


# --- record: other refusals ---------------------------------------------------

class TestRecordRefusals:
    """`record` refuses an inapplicable arm, a mixed origin, an unreadable
    output, and missing prerequisites; nothing is written. [AC-2.1]"""

    refused = staticmethod(TestRecordEvidenceRefusals.refused)

    def test_story_without_routes(self, trial):
        trial.set_routes({})
        self.refused(trial, "not_prepared", S1, "off-1", "off-fail.md")

    @pytest.mark.parametrize("story,arm", [
        (S3, "safety-fact"),        # gate3_route evaluator-agent
        (S2, "gate0-divergence"),   # gate0_route evaluator-agent
        (S4, "gate0-divergence"),   # gate0_route skip
    ])
    def test_arm_not_applicable_to_the_route(self, trial, story, arm):
        extra = ("--verifier", VERIFIER_PASS) if arm == "safety-fact" else (
            "--report-line", CHOSE)
        output = "safety-on.md" if arm == "safety-fact" else "gate0-comparison.md"
        self.refused(trial, "arm_not_applicable", story, arm, output, *extra)

    @pytest.mark.parametrize("arm,output,extra", [
        ("reviewer-filters", "filters-on.md", ()),
        ("repro-first", "repro-not-bug.md", ("--kind", "not-a-bug-fix")),
        ("safety-fact", "safety-on.md", ("--verifier", str(VERIFIER_PASS))),
        ("gate0-divergence", "gate0-comparison.md", ("--report-line", CHOSE)),
    ])
    def test_absent_upgrade_arm_never_applies(self, tmp_path, harness, arm, output, extra):
        present = tuple(name for name in UPGRADES if name != arm)
        t = Trial(tmp_path / "absent", harness, present=present)
        self.refused(t, "arm_not_applicable", S1, arm, output, *extra)

    def test_origin_mismatch(self, trial):
        trial.ok(S1, "off-1", "off-fail.md", "--origin", "claude-opus-5-5")
        self.refused(trial, "origin_mismatch", S1, "off-2", "off-fail.md",
                     "--origin", "gpt-5")

    def test_missing_output(self, trial, tmp_path):
        self.refused(trial, "output_unreadable", S1, "off-1", tmp_path / "missing.md")

    @pytest.mark.parametrize("data", [b"", b"  \n\n", b"\xff\xfe REVIEW_RESULT"])
    def test_empty_or_non_utf8_output(self, trial, tmp_path, data):
        output = tmp_path / "out.md"
        output.write_bytes(data)
        self.refused(trial, "output_unreadable", S1, "off-1", output)

    def test_review_panel_missing(self, trial, monkeypatch, tmp_path):
        monkeypatch.setattr(trial.harness, "REVIEW_PANEL", tmp_path / "no-review-panel.py")
        self.refused(trial, "review_panel_missing", S1, "off-1", "off-fail.md")

    def test_review_panel_lacking_a_reused_name(self, trial, monkeypatch, tmp_path):
        stub = tmp_path / "review-panel.py"
        stub.write_text("def parse_output(text):\n    return None\n", encoding="utf-8")
        monkeypatch.setattr(trial.harness, "REVIEW_PANEL", stub)
        self.refused(trial, "review_panel_missing", S1, "off-1", "off-fail.md")

    def test_unknown_story(self, trial):
        self.refused(trial, "story_unknown", "2026-09-09-nope/story-9", "off-1", "off-fail.md")

    def test_missing_trial(self, harness, tmp_path):
        result = _call(harness, "record", "--trial", tmp_path / "none.json", "--story", S1,
                       "--arm", "off-1", "--output", FIXTURES / "off-fail.md",
                       "--state-dir", tmp_path / "state")
        assert_refused(result, "trial_invalid")
        assert not (tmp_path / "state").exists()

    def test_unsafe_story_id_in_the_trial_file(self, trial):
        doc = trial.doc()
        doc["stories"][0]["story_id"] = "../../escape"
        trial.write(doc)
        self.refused(trial, "unsafe_path", "../../escape", "off-1", "off-fail.md")

    def test_state_dir_unresolved_outside_git(self, trial, tmp_path, monkeypatch):
        outside = tmp_path / "not-a-repo"
        outside.mkdir()
        monkeypatch.chdir(outside)
        monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
        before = trial.raw()
        result = _call(trial.harness, "record", "--trial", trial.trial, "--story", S1,
                       "--arm", "off-1", "--output", FIXTURES / "off-fail.md",
                       "--state", "safety-fact=off", "--state", "reviewer-filters=off")
        assert_refused(result, "state_dir_unresolved")
        assert trial.raw() == before

    def test_state_dir_that_is_a_file(self, trial, tmp_path):
        blocker = tmp_path / "state-file"
        blocker.write_text("x", encoding="utf-8")
        before = trial.raw()
        result = _call(trial.harness, "record", "--trial", trial.trial, "--story", S1,
                       "--arm", "off-1", "--output", FIXTURES / "off-fail.md",
                       "--state", "safety-fact=off", "--state", "reviewer-filters=off",
                       "--state-dir", blocker)
        assert_refused(result, "state_dir_unwritable")
        assert trial.raw() == before

    def test_unknown_arm_is_a_usage_error(self, trial):
        before = trial.raw()
        result = trial.call("record", "--trial", trial.trial, "--story", S1, "--arm", "panel",
                            "--output", FIXTURES / "off-fail.md", "--state-dir", trial.state)
        assert result.code == 2 and result.out == []
        assert trial.raw() == before


# --- record: keys -------------------------------------------------------------

class TestRecordKeys:
    """`record` parses keys through review-panel.py, filters Gate 0 to
    `**Avoided by:**` issues, maps repro results, copies the raw output, and
    recomputes upgrade-only and off-only. [AC-2.2]"""

    def test_off_arm_entry(self, trial):
        result = trial.ok(S1, "off-1", "off-fail.md")
        entry = trial.story(S1)["arms"]["off-1"]
        assert entry == {
            "verdict": "FAIL",
            "keys": [{"key": AC12, "severity": "Critical"},
                     {"key": PAY_ROUTE, "severity": "Critical"}],
            "states": {"safety-fact": "off", "reviewer-filters": "off"},
            "raw": "%s/off-1.md" % SLUG1,
            "raw_sha256": _sha(FIXTURES / "off-fail.md"),
            "exercised": True,
        }
        raw = trial.state / SLUG1 / "off-1.md"
        assert raw.read_bytes() == (FIXTURES / "off-fail.md").read_bytes()
        assert result.out == [
            "pass",
            "arm: off-1 verdict=FAIL keys=2 exercised=true",
            "upgrade_only: 0",
            "gate-upgrade-trial: recorded %s off-1 — 2 keys, 0 upgrade-only findings" % S1,
        ]

    def test_one_key_reads_singular(self, trial):
        trial.off(S1, "off-pass.md")
        result = trial.safety(S1)
        assert result.out[-1] == ("gate-upgrade-trial: recorded %s safety-fact — 2 keys, "
                                  "2 upgrade-only findings" % S1)
        result = trial.gate0(S1)
        assert result.out[1] == "arm: gate0-divergence verdict=none keys=1 exercised=true"
        assert result.out[-1].endswith("— 1 key, 3 upgrade-only findings")

    def test_gate0_keys_only_from_avoided_by_issues(self, trial):
        trial.gate0(S1)
        entry = trial.story(S1)["arms"]["gate0-divergence"]
        assert entry["keys"] == [{"key": WEBHOOK, "severity": "Critical"}]
        assert entry["report"] == "chose"
        assert entry["exercised"] is True
        assert entry["verdict"] is None
        assert entry["states"] == {}
        assert "sketch B" not in trial.trial.read_text(encoding="utf-8")

    def test_gate0_without_avoided_by_lines_has_no_keys(self, trial):
        trial.gate0(S1, "gate0-no-avoided.md")
        entry = trial.story(S1)["arms"]["gate0-divergence"]
        assert entry["keys"] == [] and entry["exercised"] is True

    def test_gate0_skip_is_stored_unexercised_with_no_keys(self, trial):
        result = trial.gate0(S1, "gate0-comparison.md", SKIP)
        entry = trial.story(S1)["arms"]["gate0-divergence"]
        assert entry["keys"] == [] and entry["exercised"] is False
        assert entry["report"] == "skip"
        assert result.out[1] == "arm: gate0-divergence verdict=none keys=0 exercised=false"

    def test_gate0_with_explicit_states(self, trial):
        trial.ok(S1, "gate0-divergence", "gate0-comparison.md", "--report-line", CHOSE,
                 states=("gate0-divergence=on", "safety-fact=off"))
        assert trial.story(S1)["arms"]["gate0-divergence"]["states"] == {
            "gate0-divergence": "on", "safety-fact": "off"}

    def test_repro_fail_fail_stores_the_ac_key_at_critical(self, trial):
        trial.repro(S1, *BUG_FAIL_FAIL, output="repro-bug.md")
        story = trial.story(S1)
        entry = story["arms"]["repro-first"]
        assert entry["keys"] == [{"key": REPRO_KEY, "severity": "Critical"}]
        assert (entry["kind"], entry["repro_ac"], entry["at_parent"], entry["at_commit"],
                entry["repro_result"], entry["exercised"]) == (
            "bug", "AC-1.3", "fail", "fail", "still_fails", True)
        assert story["repro_kind"] == "bug"
        assert story["upgrade_only"] == [{"id": None, "upgrade": "repro-first", "key": REPRO_KEY,
                                          "severity": "Critical", "label": None, "note": None}]

    @pytest.mark.parametrize("parent,commit,result", [("pass", "pass", "no_repro"),
                                                      ("pass", "fail", "no_repro"),
                                                      ("fail", "pass", "fixed")])
    def test_other_repro_pairs_store_no_key(self, trial, parent, commit, result):
        trial.repro(S1, "--kind", "bug", "--repro-ac", "AC-1.3", "--at-parent", parent,
                    "--at-commit", commit, output="repro-bug.md")
        entry = trial.story(S1)["arms"]["repro-first"]
        assert entry["keys"] == [] and entry["exercised"] is True
        assert entry["repro_result"] == result

    def test_not_a_bug_fix_is_unexercised(self, trial):
        trial.repro(S1)
        story = trial.story(S1)
        entry = story["arms"]["repro-first"]
        assert entry["keys"] == [] and entry["exercised"] is False
        assert entry["kind"] == "not-a-bug-fix"
        assert entry["repro_ac"] is None and entry["repro_result"] is None
        assert story["repro_kind"] == "not-a-bug-fix"

    def test_prose_location_is_stored_as_a_digest_key(self, trial):
        trial.ok(S1, "reviewer-filters", "filters-on.md")
        keys = trial.story(S1)["arms"]["reviewer-filters"]["keys"]
        assert {"key": SETTLE, "severity": "Major"} in keys
        assert "nightly" not in trial.trial.read_text(encoding="utf-8")

    def test_upgrade_only_is_arm_keys_minus_both_off_runs(self, trial):
        trial.off(S1, "off-fail.md", off2="off-pass.md")
        trial.ok(S1, "reviewer-filters", "filters-on.md")
        assert trial.story(S1)["upgrade_only"] == [
            {"id": None, "upgrade": "reviewer-filters", "key": SETTLE, "severity": "Major",
             "label": None, "note": None},
            {"id": None, "upgrade": "reviewer-filters", "key": FEE_SHARE, "severity": "Major",
             "label": None, "note": None},
        ]

    def test_upgrade_only_lists_upgrades_in_order(self, trial):
        trial.off(S1, "off-pass.md")
        trial.repro(S1, *BUG_FAIL_FAIL, output="repro-bug.md")
        trial.gate0(S1)
        trial.safety(S1)
        trial.ok(S1, "reviewer-filters", "filters-on.md")
        pairs = [(e["upgrade"], e["key"]) for e in trial.story(S1)["upgrade_only"]]
        assert pairs == [("gate0-divergence", WEBHOOK), ("safety-fact", AC12),
                         ("safety-fact", FEES), ("reviewer-filters", AC12),
                         ("reviewer-filters", SETTLE), ("reviewer-filters", FEE_SHARE),
                         ("repro-first", REPRO_KEY)]

    def test_labels_stay_on_keys_that_stay_upgrade_only(self, trial, tmp_path):
        trial.off(S1, "off-pass.md")
        trial.ok(S1, "reviewer-filters", "filters-on.md")
        doc = trial.doc()
        for entry in _story(doc, S1)["upgrade_only"]:
            entry.update(id="F0%d" % len(entry["key"]), label="valid", note="seen")
        settle_id = next(e["id"] for e in _story(doc, S1)["upgrade_only"] if e["key"] == SETTLE)
        trial.write(doc)
        only_fee_share = tmp_path / "off-fee-share.md"
        only_fee_share.write_text(
            "### REVIEW_RESULT: FAIL\n\n### Issues Found\n\n"
            "- **Issue:** Owner check missing\n"
            "- **Location:** `app/api/events/[id]/fee-share/route.ts`\n"
            "- **Severity:** Critical\n- **Category:** security\n", encoding="utf-8")
        trial.ok(S1, "off-2", only_fee_share)
        found = {e["key"]: e for e in trial.story(S1)["upgrade_only"]}
        assert set(found) == {AC12, SETTLE}
        assert (found[SETTLE]["id"], found[SETTLE]["label"], found[SETTLE]["note"]) == (
            settle_id, "valid", "seen")

    def test_new_keys_after_a_rerecord_start_unlabeled(self, trial):
        trial.off(S1, "off-pass.md")
        trial.safety(S1, "safety-on-pass.md")
        assert trial.story(S1)["upgrade_only"] == []
        trial.safety(S1)
        assert all(e["label"] is None and e["id"] is None
                   for e in trial.story(S1)["upgrade_only"])

    def test_rerecording_replaces_the_arm(self, trial):
        trial.off(S1, "off-pass.md")
        trial.safety(S1)
        assert len(trial.story(S1)["upgrade_only"]) == 2
        trial.safety(S1, "safety-on-pass.md", verifier=FIXTURES / "verifier-fail.txt")
        story = trial.story(S1)
        assert story["arms"]["safety-fact"]["keys"] == []
        assert story["arms"]["safety-fact"]["verifier"] == "fail"
        assert story["upgrade_only"] == []
        assert ((trial.state / SLUG1 / "safety-fact.md").read_bytes()
                == (FIXTURES / "safety-on-pass.md").read_bytes())

    def test_off_only_counts_keys_both_off_runs_raised_and_the_arm_missed(self, trial):
        trial.off(S1)
        trial.safety(S1)
        trial.gate0(S1)
        trial.ok(S1, "reviewer-filters", "filters-on.md")
        assert trial.story(S1)["off_only"] == {
            "safety-fact": 1, "gate0-divergence": 2, "reviewer-filters": 1}

    def test_off_only_is_zero_until_both_off_runs_are_recorded(self, trial):
        trial.ok(S1, "off-1", "off-fail.md")
        trial.safety(S1)
        assert trial.story(S1)["off_only"] == {
            "safety-fact": 0, "gate0-divergence": 0, "reviewer-filters": 0}

    def test_off_only_ignores_an_unexercised_gate0_arm(self, trial):
        trial.off(S1)
        trial.gate0(S1, "gate0-comparison.md", SKIP)
        assert trial.story(S1)["off_only"]["gate0-divergence"] == 0

    def test_origin_is_stored_once(self, trial):
        trial.ok(S1, "off-1", "off-fail.md", "--origin", "claude-opus-5-5")
        assert trial.doc()["origin"] == "claude-opus-5-5"
        trial.ok(S1, "off-2", "off-fail.md")
        trial.ok(S2, "off-1", "off-pass.md", "--origin", "claude-opus-5-5")
        assert trial.doc()["origin"] == "claude-opus-5-5"

    @pytest.mark.parametrize("name,first", [("verifier-pass.txt", "pass"),
                                            ("verifier-fail.txt", "fail"),
                                            ("verifier-unverifiable.txt", "unverifiable")])
    def test_safety_fact_stores_the_verifier_line_and_a_copy(self, trial, name, first):
        trial.safety(S1, verifier=FIXTURES / name)
        entry = trial.story(S1)["arms"]["safety-fact"]
        assert entry["verifier"] == first
        assert entry["states"] == {"safety-fact": "on", "reviewer-filters": "off"}
        copy = trial.state / SLUG1 / "safety-fact-verifier.txt"
        assert copy.read_bytes() == (FIXTURES / name).read_bytes()

    def test_cli_run(self, trial):
        """The harness runs as a script too."""
        result = _cli("record", "--trial", trial.trial, "--story", S1, "--arm", "off-1",
                      "--output", FIXTURES / "off-pass.md", "--state", "safety-fact=off",
                      "--state", "reviewer-filters=off", "--state-dir", trial.state)
        assert_ran(result)


class TestResolveStateDir:
    """The default state dir is the primary checkout's `.writ/state/gate-upgrade-trial/`,
    found from a linked worktree too. [AC-2.2]"""

    def test_default_from_a_linked_worktree(self, harness, tmp_path, monkeypatch):
        primary = tmp_path / "primary"
        primary.mkdir()
        _git(primary, "init", "-q")
        _commit(primary, {"README.md": "x\n"}, "base")
        _git(primary, "worktree", "add", "-q", "--detach", str(tmp_path / "lane"))
        monkeypatch.chdir(tmp_path / "lane")
        state = harness.resolve_state_dir(None)
        assert state.resolve() == (primary / ".writ" / "state" / "gate-upgrade-trial").resolve()
        assert not state.exists()

    def test_explicit_value_wins(self, harness, tmp_path):
        assert harness.resolve_state_dir(str(tmp_path / "s")) == tmp_path / "s"


# --- snapshot -----------------------------------------------------------------

def _mini_yuss(root: Path) -> Path:
    yuss = root / "yuss"
    yuss.mkdir()
    _git(yuss, "init", "-q")
    _commit(yuss, {"app.ts": "export {}\n"}, "base")
    return yuss


class TestSnapshot:
    """`snapshot` records yuss `after` and `unchanged` (Business Rule 2). [AC-2.4]"""

    def test_unchanged(self, harness, tmp_path):
        yuss = _mini_yuss(tmp_path)
        t = Trial(tmp_path / "t", harness, yuss=yuss)
        result = t.call("snapshot", "--trial", t.trial, "--yuss", yuss)
        assert result.out == ["pass", "yuss: unchanged",
                              "gate-upgrade-trial: yuss snapshot after — unchanged"]
        snap = t.doc()["yuss_snapshot"]
        assert snap["after"] == snap["before"] and snap["unchanged"] is True

    def test_changed(self, harness, tmp_path):
        yuss = _mini_yuss(tmp_path)
        t = Trial(tmp_path / "t", harness, yuss=yuss)
        (yuss / "stray.txt").write_text("x\n", encoding="utf-8")
        result = t.call("snapshot", "--trial", t.trial, "--yuss", yuss)
        assert result.code == 0
        assert result.out == ["unverifiable", "reason: yuss_changed", "yuss: changed",
                              "gate-upgrade-trial: yuss snapshot after — changed"]
        assert t.doc()["yuss_snapshot"]["unchanged"] is False

    def test_no_before_snapshot(self, trial, tmp_path):
        yuss = _mini_yuss(tmp_path)
        before = trial.raw()
        assert_refused(trial.call("snapshot", "--trial", trial.trial, "--yuss", yuss),
                       "no_before_snapshot")
        assert trial.raw() == before

    def test_missing_yuss(self, harness, tmp_path):
        yuss = _mini_yuss(tmp_path)
        t = Trial(tmp_path / "t", harness, yuss=yuss)
        before = t.raw()
        assert_refused(t.call("snapshot", "--trial", t.trial, "--yuss", tmp_path / "gone"),
                       "yuss_missing")
        assert t.raw() == before


# --- sheet ----------------------------------------------------------------------

class TestSheet:
    """`sheet` assigns shuffled IDs, writes one excerpt per finding, blank
    fields, one ack per never-exercised upgrade, and records the body hash. [AC-2.3]"""

    def test_ids_are_a_seeded_shuffle_of_the_deterministic_order(self, full):
        assert_ran(full.sheet("--seed", "7"))
        doc = full.doc()
        rp = _load_review_panel()
        ordered = []
        for index, story in enumerate(doc["stories"]):
            for entry in story["upgrade_only"]:
                ordered.append((index, UPGRADES.index(entry["upgrade"]),
                                rp._key_order(entry["key"]), story["story_id"], entry["upgrade"],
                                entry["key"]))
        ordered.sort(key=lambda row: row[:3])
        expected = [row[3:] for row in ordered]
        random.Random(7).shuffle(expected)
        got = {e["id"]: (sid, e["upgrade"], e["key"]) for sid, e in _all_findings(doc)}
        assert sorted(got) == ["F0%d" % n for n in range(1, 9)]
        assert [got["F0%d" % n] for n in range(1, 9)] == expected
        assert {(sid, u, k) for sid, u, k in got.values()} == FULL_UPGRADE_ONLY

    def test_same_seed_same_ids_other_seed_other_ids(self, tmp_path, harness):
        maps = []
        for name, seed in (("a", "7"), ("b", "7"), ("c", "8")):
            t = Trial(tmp_path / name, harness)
            _record_full(t)
            assert_ran(t.sheet("--seed", seed))
            maps.append({e["id"]: (sid, e["key"], e["upgrade"])
                         for sid, e in _all_findings(t.doc())})
        assert maps[0] == maps[1]
        assert maps[0] != maps[2]

    def test_default_seed_is_drawn_and_stored(self, full):
        assert_ran(full.sheet())
        seed = full.doc()["sheet"]["seed"]
        assert isinstance(seed, int) and 1 <= seed < 2 ** 31

    def test_sheet_record_and_body_hash(self, full):
        result = full.sheet("--seed", "7")
        text = full.sheet_text()
        assert full.doc()["sheet"] == {"path": str(full.sheet_path),
                                       "body_sha256": _norm_hash(text), "seed": 7,
                                       "findings": 8}
        assert result.out == [
            "pass",
            "sheet: %s" % full.sheet_path,
            "findings: 8",
            "not_exercised: none",
            "excerpts: %s" % (full.state / "findings"),
            "gate-upgrade-trial: sheet written — 8 findings, 0 acknowledgments",
        ]

    def test_sheet_text(self, full):
        full.sheet("--seed", "7")
        lines = full.sheet_text().splitlines()
        assert lines[:6] == ["# Gate Upgrade Trial — Labeling Sheet", "", SHEET_HEADER, "",
                             "## Findings", ""]
        doc = full.doc()
        by_id = {e["id"]: (sid, e) for sid, e in _all_findings(doc)}
        expected: List[str] = []
        for fid in sorted(by_id):
            sid, entry = by_id[fid]
            expected += ["### %s" % fid, "story: %s" % sid, "key: %s" % entry["key"],
                         "severity: %s" % entry["severity"],
                         "excerpt: %s" % (full.state / "findings" / ("%s.md" % fid)),
                         "label:", "note:", ""]
        assert lines[6:6 + len(expected)] == expected
        assert lines[6 + len(expected):] == ["## Not exercised", "", "(none)"]
        assert full.sheet_text().endswith("(none)\n")

    def test_sheet_names_no_upgrade(self, full):
        full.sheet("--seed", "7")
        text = full.sheet_text()
        for name in UPGRADES + ("off-1", "off-2"):
            assert name not in text

    def test_one_excerpt_per_finding(self, full):
        full.sheet("--seed", "7")
        findings = full.state / "findings"
        ids = sorted(e["id"] for _, e in _all_findings(full.doc()))
        assert sorted(p.name for p in findings.iterdir()) == ["%s.md" % i for i in ids]
        for sid, entry in _all_findings(full.doc()):
            lines = (findings / ("%s.md" % entry["id"])).read_text(encoding="utf-8").splitlines()
            assert lines[:5] == ["# %s" % entry["id"], "story: %s" % sid,
                                 "key: %s" % entry["key"], "severity: %s" % entry["severity"],
                                 ""]
            body = "\n".join(lines[5:])
            for name in UPGRADES + ("off-1", "off-2"):
                assert name not in body, (entry["key"], name)

    def _excerpt(self, t: Trial, story: str, upgrade: str, key: str) -> str:
        entry = next(e for sid, e in _all_findings(t.doc())
                     if sid == story and e["upgrade"] == upgrade and e["key"] == key)
        return (t.state / "findings" / ("%s.md" % entry["id"])).read_text(encoding="utf-8")

    def test_gate0_excerpt_is_the_avoided_by_issue_only(self, full):
        full.sheet("--seed", "7")
        text = self._excerpt(full, S1, "gate0-divergence", WEBHOOK)
        assert "- **Avoided by:** sketch B line 14 — upsert keyed on payment_intent_id" in text
        assert "inserts a fee row before it checks the payment intent" in text
        assert "lib/ledger.ts" not in text
        assert "[AC-1.2]" not in text

    def test_category_excerpt_is_the_matching_issue_block(self, full):
        full.sheet("--seed", "7")
        text = self._excerpt(full, S1, "reviewer-filters", FEE_SHARE)
        assert "- **Issue:** The fee-share route never checks that the caller owns the event" in text
        assert "- **Suggested Fix:** Compare `session.user.id`" in text
        assert "nightly settle job" not in text

    def test_digest_key_excerpt(self, full):
        full.sheet("--seed", "7")
        text = self._excerpt(full, S4, "reviewer-filters", SETTLE)
        assert "- **Location:** `nightly settle job`" in text
        assert "fee-share" not in text

    def test_minor_issue_at_the_same_path_is_not_in_the_excerpt(self, full):
        full.sheet("--seed", "7")
        text = self._excerpt(full, S1, "safety-fact", FEES)
        assert "Fee math is duplicated" in text
        assert "@@ -1,4 +1,6 @@" in text
        assert "Variable naming" not in text

    def test_repro_excerpt(self, full):
        full.sheet("--seed", "7")
        text = self._excerpt(full, S1, "repro-first", REPRO_KEY)
        body = text.split("\n\n", 1)[1]
        assert body.startswith("### Repro\n")
        assert "#### Why it fails" in body and "inserts a new fee row" in body
        assert "### Notes" not in body and "Stopped after" not in body
        assert body.rstrip("\n").endswith("targets: AC-1.3\nat parent: fail\nat commit: fail")

    def test_ac_excerpt_from_a_gate3_arm(self, trial):
        trial.off(S1, "off-pass.md")
        trial.safety(S1)
        for sid in (S2, S3, S4):
            trial.off(sid, "off-pass.md")
            trial.ok(sid, "reviewer-filters", "off-pass.md")
            trial.repro(sid)
        trial.ok(S1, "reviewer-filters", "off-pass.md")
        trial.gate0(S1, "gate0-no-avoided.md")
        trial.repro(S1)
        trial.safety(S2, "safety-on-pass.md")
        trial.gate0(S3, "gate0-no-avoided.md", SKIP)
        trial.safety(S4, "safety-on-pass.md")
        assert_ran(trial.sheet("--seed", "3"))
        text = self._excerpt(trial, S1, "safety-fact", AC12)
        assert "- [ ] Given a retried payment, when the webhook fires twice" in text
        assert "AC-1.2 depends on both agreeing" in text   # the issue that mentions it
        assert "[AC-1.1]" not in text
        assert "Variable naming" not in text

    def test_no_matching_block_falls_back_to_one_line(self, full):
        doc = full.doc()
        _story(doc, S1)["upgrade_only"].append(
            {"id": None, "upgrade": "safety-fact", "key": "ac:AC-9.9", "severity": "Critical",
             "label": None, "note": None})
        full.write(doc)
        assert_ran(full.sheet("--seed", "7"))
        text = self._excerpt(full, S1, "safety-fact", "ac:AC-9.9")
        assert text.split("\n\n", 1)[1] == NO_MATCH + "\n"

    def test_repro_output_without_a_repro_section(self, full, tmp_path):
        output = tmp_path / "repro-no-section.md"
        output.write_text("### Summary\nStopped after the repro commit.\n", encoding="utf-8")
        full.repro(S1, *BUG_FAIL_FAIL, output=output)
        assert_ran(full.sheet("--seed", "7"))
        body = self._excerpt(full, S1, "repro-first", REPRO_KEY).split("\n\n", 1)[1]
        assert body == NO_MATCH + "\n\ntargets: AC-1.3\nat parent: fail\nat commit: fail\n"

    def test_findings_dir_unwritable(self, full):
        full.state.mkdir(parents=True, exist_ok=True)
        (full.state / "findings").write_text("not a dir\n", encoding="utf-8")
        before = full.raw()
        assert_refused(full.sheet("--seed", "7"), "state_dir_unwritable")
        assert full.raw() == before and not full.sheet_path.exists()

    def test_stale_excerpts_are_removed(self, full):
        findings = full.state / "findings"
        findings.mkdir(parents=True)
        (findings / "F99.md").write_text("stale\n", encoding="utf-8")
        (findings / "keep.txt").write_text("other\n", encoding="utf-8")
        (findings / "Fnotes.md").write_text("other\n", encoding="utf-8")
        full.sheet("--seed", "7")
        assert not (findings / "F99.md").exists()
        assert (findings / "keep.txt").exists() and (findings / "Fnotes.md").exists()

    def test_sheet_recorded_needs_force(self, full):
        assert_ran(full.sheet("--seed", "7"))
        before, sheet_before = full.raw(), full.sheet_text()
        excerpts = _tree(full.state / "findings")
        assert_refused(full.sheet("--seed", "8"), "sheet_recorded")
        assert full.raw() == before and full.sheet_text() == sheet_before
        assert _tree(full.state / "findings") == excerpts
        assert_ran(full.sheet("--seed", "8", "--force"))
        assert full.doc()["sheet"]["seed"] == 8

    def test_missing_arm(self, tmp_path, harness):
        t = Trial(tmp_path / "t", harness)
        _record_full(t)
        doc = t.doc()
        del _story(doc, S2)["arms"]["safety-fact"]
        t.write(doc)
        before = t.raw()
        result = t.sheet("--seed", "7")
        assert_refused(result, "missing_arm")
        assert result.err[0] == "reason: missing_arm — %s safety-fact" % S2
        assert t.raw() == before and not t.sheet_path.exists()
        assert not (t.state / "findings").exists()

    def test_missing_routes(self, full):
        doc = full.doc()
        _story(doc, S3)["routes"] = None
        full.write(doc)
        result = full.sheet("--seed", "7")
        assert_refused(result, "missing_arm")
        assert result.err[0] == "reason: missing_arm — %s routes" % S3

    def test_raw_output_missing(self, full):
        (full.state / SLUG1 / "safety-fact.md").unlink()
        before = full.raw()
        assert_refused(full.sheet("--seed", "7"), "raw_missing")
        assert full.raw() == before and not full.sheet_path.exists()

    def test_raw_output_altered(self, full):
        (full.state / SLUG1 / "gate0-divergence.md").write_text("changed\n", encoding="utf-8")
        assert_refused(full.sheet("--seed", "7"), "raw_missing")

    def test_review_panel_missing(self, full, monkeypatch, tmp_path):
        monkeypatch.setattr(full.harness, "REVIEW_PANEL", tmp_path / "none.py")
        assert_refused(full.sheet("--seed", "7"), "review_panel_missing")

    def test_no_findings_and_three_acks(self, tmp_path, harness):
        t = Trial(tmp_path / "t", harness, routes=ALL_EVALUATOR)
        for sid in ALL_STORIES:
            t.off(sid, "off-pass.md")
            t.ok(sid, "reviewer-filters", "off-pass.md")
            t.repro(sid)
        result = t.sheet("--seed", "1")
        lines = t.sheet_text().splitlines()
        tail = ["## Findings", "", "(none)", "", "## Not exercised", ""]
        for name, reason in (("gate0-divergence", "route evaluator-agent"),
                             ("safety-fact", "route evaluator-agent"),
                             ("repro-first", "not-a-bug-fix")):
            tail += ["### not exercised: %s" % name, "exercised: 0/4"]
            tail += ["- %s: %s" % (sid, reason) for sid in ALL_STORIES]
            tail += ["ack:", ""]
        assert lines[4:] == tail[:-1]
        assert result.out[2:4] == ["findings: 0",
                                   "not_exercised: gate0-divergence, safety-fact, repro-first"]
        assert result.out[-1] == ("gate-upgrade-trial: sheet written — 0 findings, "
                                  "3 acknowledgments")
        assert t.doc()["sheet"]["findings"] == 0

    def test_gate0_not_exercised_reasons(self, tmp_path, harness):
        t = Trial(tmp_path / "t", harness)
        _record_full(t)
        t.gate0(S1, "gate0-comparison.md", SKIP)
        t.sheet("--seed", "7")
        text = t.sheet_text()
        block = text[text.index("### not exercised: gate0-divergence"):].splitlines()[:7]
        assert block == ["### not exercised: gate0-divergence", "exercised: 0/4",
                         "- %s: skip (gate0-divergence run)" % S1,
                         "- %s: route evaluator-agent" % S2,
                         "- %s: skip (gate0-divergence run)" % S3,
                         "- %s: route skip (unverifiable: no planned files)" % S4,
                         "ack:"]

    def test_excerpt_paths_relative_to_the_primary_checkout(self, tmp_path, harness,
                                                            monkeypatch):
        project = tmp_path / "project"
        project.mkdir()
        _git(project, "init", "-q")
        t = Trial(tmp_path / "t", harness)
        _record_full(t)
        state = project / ".writ" / "state" / "gate-upgrade-trial"
        shutil_copytree(t.state, state)
        monkeypatch.chdir(project)
        result = t.call("sheet", "--trial", t.trial, "--out", t.sheet_path, "--seed", "7",
                        "--state-dir", state)
        assert_ran(result)
        excerpts = [v["excerpt"] for v in _sheet_entries(t.sheet_text()).values()]
        assert excerpts and all(
            re.match(r"^\.writ/state/gate-upgrade-trial/findings/F0\d\.md$", e) for e in excerpts)

    def test_three_digit_ids_past_99(self, harness):
        assert harness.finding_ids(2) == ["F01", "F02"]
        assert harness.finding_ids(99)[-1] == "F99"
        ids = harness.finding_ids(100)
        assert ids[0] == "F001" and ids[-1] == "F100"


def shutil_copytree(src: Path, dst: Path) -> None:
    shutil.copytree(str(src), str(dst))


# --- label ----------------------------------------------------------------------

@pytest.fixture
def sheeted(full: Trial) -> Trial:
    assert_ran(full.sheet("--seed", "7"))
    return full


class TestLabel:
    """`label` imports a filled sheet only when the body hash matches and every
    field is well formed, and refuses agent-like labelers. [AC-2.3]"""

    @staticmethod
    def refused(t: Trial, code: str, sheet: Optional[Path] = None,
                name: str = "A. Maintainer") -> Result:
        before = t.raw()
        result = t.label(sheet, name)
        assert_refused(result, code)
        assert t.raw() == before
        return result

    def test_labels_notes_and_labeler_are_stored(self, sheeted):
        sheeted.fill(labels={(S1, WEBHOOK): "valid"},
                     notes={(S1, WEBHOOK): "retry double-charges; the sketch upsert avoids it"})
        result = sheeted.label(name="  A. Maintainer  ")
        assert result.out == ["pass", "labeled: 8 (valid 1, invalid 7)", "acks: none",
                              "labeled_by: A. Maintainer",
                              "gate-upgrade-trial: labels stored — 8 findings, 0 acknowledgments"]
        doc = sheeted.doc()
        assert doc["labeled_by"] == "A. Maintainer"
        assert doc["acks"] == {}
        found = {(sid, e["key"], e["upgrade"]): e for sid, e in _all_findings(doc)}
        webhook = found[(S1, WEBHOOK, "gate0-divergence")]
        assert (webhook["label"], webhook["note"]) == (
            "valid", "retry double-charges; the sketch upsert avoids it")
        others = [e for k, e in found.items() if k[1] != WEBHOOK]
        assert all(e["label"] == "invalid" and e["note"] == "" for e in others)

    def test_acks_are_stored(self, tmp_path, harness):
        t = Trial(tmp_path / "t", harness, routes=ALL_EVALUATOR)
        for sid in ALL_STORIES:
            t.off(sid, "off-pass.md")
            t.ok(sid, "reviewer-filters", "off-pass.md")
            t.repro(sid)
        t.sheet("--seed", "1")
        t.fill(acks={"repro-first": "amend"})
        result = t.label()
        assert result.out[1:3] == ["labeled: 0 (valid 0, invalid 0)",
                                   "acks: gate0-divergence=remove safety-fact=remove "
                                   "repro-first=amend"]
        assert t.doc()["acks"] == {"gate0-divergence": "remove", "safety-fact": "remove",
                                   "repro-first": "amend"}

    def test_note_of_exactly_200_characters(self, sheeted):
        sheeted.fill(notes={(S1, WEBHOOK): "x" * 200})
        assert_ran(sheeted.label())

    def test_relabeling_replaces_labels(self, sheeted):
        sheeted.fill()
        assert_ran(sheeted.label())
        sheeted.sheet_path.write_text(_fill(sheeted.sheet_text().replace(
            "label: invalid", "label:"), label="valid"), encoding="utf-8")
        assert_ran(sheeted.label(name="B. Maintainer"))
        doc = sheeted.doc()
        assert doc["labeled_by"] == "B. Maintainer"
        assert all(e["label"] == "valid" for _, e in _all_findings(doc))

    @pytest.mark.parametrize("name", ["", "   ", "Claude", "claude-opus-5-5", "lane agent",
                                      "GPT-5", "Codex", "cursor", "Gemini", "grok",
                                      "Model Reviewer", "review-bot", "A.\nMaintainer"])
    def test_agent_like_or_empty_labeler(self, sheeted, name):
        sheeted.fill()
        self.refused(sheeted, "labeled_by_invalid", name=name)

    def test_no_sheet_recorded(self, full, tmp_path):
        sheet = tmp_path / "sheet.md"
        sheet.write_text("# sheet\n", encoding="utf-8")
        self.refused(full, "no_sheet", sheet)

    def test_sheet_unreadable(self, sheeted, tmp_path):
        self.refused(sheeted, "sheet_unreadable", tmp_path / "missing.md")
        bad = tmp_path / "bad.md"
        bad.write_bytes(b"\xff\xfe")
        self.refused(sheeted, "sheet_unreadable", bad)

    @pytest.mark.parametrize("edit", [
        lambda text: text.replace("severity: Major", "severity: Critical", 1),
        lambda text: text.replace("key: ", "key:  ", 1),
        lambda text: text + "extra line\n",
        lambda text: text.replace("note:\n", "note:\nnote: second\n", 1),
        lambda text: text.replace("label: invalid\n", "", 1),
        lambda text: text.replace("\n", "\r\n"),
    ])
    def test_sheet_body_changed(self, sheeted, edit):
        sheeted.sheet_path.write_bytes(edit(_fill(sheeted.sheet_text())).encode("utf-8"))
        self.refused(sheeted, "sheet_changed")

    def test_sheet_stale_after_a_new_finding(self, sheeted):
        sheeted.fill()
        sheeted.ok(S2, "reviewer-filters", "filters-on.md")
        result = self.refused(sheeted, "sheet_stale")
        assert "sheet" in result.err[0]

    def test_sheet_stale_after_a_finding_disappears(self, sheeted):
        sheeted.fill()
        sheeted.ok(S4, "reviewer-filters", "off-pass.md")
        self.refused(sheeted, "sheet_stale")

    def test_sheet_stale_after_the_not_exercised_set_changes(self, tmp_path, harness):
        t = Trial(tmp_path / "t", harness, routes=ALL_EVALUATOR)
        for sid in ALL_STORIES:
            t.off(sid, "off-pass.md")
            t.ok(sid, "reviewer-filters", "off-pass.md")
            t.repro(sid)
        t.sheet("--seed", "1")
        t.fill()
        t.repro(S1, "--kind", "bug", "--repro-ac", "AC-1.1", "--at-parent", "fail",
                "--at-commit", "pass", output="repro-bug.md")
        self.refused(t, "sheet_stale")

    @pytest.mark.parametrize("label", ["", "maybe", "Valid", "valid invalid"])
    def test_bad_label(self, sheeted, label):
        text = _fill(sheeted.sheet_text())
        sheeted.sheet_path.write_text(text.replace("label: invalid", ("label: " + label).rstrip(),
                                                   1), encoding="utf-8")
        result = self.refused(sheeted, "bad_field")
        assert re.search(r"F\d\d", result.err[0])

    @pytest.mark.parametrize("note", ["x" * 201, "see `route.ts`", "split\rline"])
    def test_bad_note(self, sheeted, note):
        sheeted.sheet_path.write_bytes(
            _fill(sheeted.sheet_text(), notes={(S1, WEBHOOK): note}).encode("utf-8"))
        self.refused(sheeted, "bad_field")

    @pytest.mark.parametrize("ack", ["", "keep", "Remove"])
    def test_bad_ack(self, tmp_path, harness, ack):
        t = Trial(tmp_path / "t", harness, routes=ALL_EVALUATOR)
        for sid in ALL_STORIES:
            t.off(sid, "off-pass.md")
            t.ok(sid, "reviewer-filters", "off-pass.md")
            t.repro(sid)
        t.sheet("--seed", "1")
        text = _fill(t.sheet_text(), acks={"safety-fact": ack})
        t.sheet_path.write_text(text.replace("ack: \n", "ack:\n"), encoding="utf-8")
        result = self.refused(t, "bad_field")
        assert "safety-fact" in result.err[0]


# --- report ---------------------------------------------------------------------

def _decided_doc() -> dict:
    """Every applicable arm recorded on the default routes; nothing labeled."""
    stories = []
    for sid in ALL_STORIES:
        routes = dict(DEFAULT_ROUTES[sid])
        arms: Dict[str, dict] = {
            "off-1": {"keys": [], "exercised": True},
            "off-2": {"keys": [], "exercised": True},
            "reviewer-filters": {"keys": [], "exercised": True},
            "repro-first": {"keys": [], "kind": "not-a-bug-fix", "exercised": False},
        }
        if routes["gate3_route"] == "review-agent":
            arms["safety-fact"] = {"keys": [], "exercised": True}
        if routes["gate0_route"] == "review-agent":
            arms["gate0-divergence"] = {"keys": [], "report": "chose", "exercised": True}
        stories.append({"story_id": sid, "routes": routes, "repro_kind": "not-a-bug-fix",
                        "arms": arms, "upgrade_only": [],
                        "off_only": {"gate0-divergence": 0, "safety-fact": 0,
                                     "reviewer-filters": 0}})
    return {"schema": "gate-upgrade-trial-v1", "baseline": "baseline.json", "origin": None,
            "yuss_snapshot": {"before": None, "after": None, "unchanged": None},
            "upgrades": {name: {"present": True} for name in UPGRADES},
            "stories": stories, "sheet": None, "acks": {}, "labeled_by": None}


def _finding(upgrade: str, key: str, label: Optional[str] = None) -> dict:
    return {"id": "F01", "upgrade": upgrade, "key": key, "severity": "Major", "label": label,
            "note": "" if label else None}


def _rows(harness: ModuleType, doc: dict) -> Dict[str, dict]:
    return {row["name"]: row for row in harness.trial_report(doc)["upgrades"]}


class TestReportVerdict:
    """`report` applies technical-spec § Verdict per upgrade, in order. [AC-2.4]"""

    def test_absent_comes_first(self, harness):
        doc = _decided_doc()
        doc["upgrades"]["safety-fact"]["present"] = False
        del doc["stories"][0]["arms"]["safety-fact"]
        row = _rows(harness, doc)["safety-fact"]
        assert row["verdict"] == "absent" and row["reason"] is None
        assert row["exercised"] is None

    @pytest.mark.parametrize("drop,upgrade,reason", [
        ("safety-fact", "safety-fact", "missing_arm %s safety-fact" % S1),
        ("gate0-divergence", "gate0-divergence", "missing_arm %s gate0-divergence" % S1),
        ("repro-first", "repro-first", "missing_arm %s repro-first" % S1),
        ("off-1", "reviewer-filters", "missing_arm %s off-1" % S1),
        ("off-2", "safety-fact", "missing_arm %s off-2" % S1),
    ])
    def test_missing_arm(self, harness, drop, upgrade, reason):
        doc = _decided_doc()
        del doc["stories"][0]["arms"][drop]
        doc["acks"] = {"repro-first": "remove"}
        row = _rows(harness, doc)[upgrade]
        assert (row["verdict"], row["reason"], row["exercised"]) == ("unverifiable", reason, None)

    def test_missing_off_arm_affects_every_upgrade_that_applies(self, harness):
        doc = _decided_doc()
        del doc["stories"][2]["arms"]["off-2"]     # S3: safety-fact does not apply
        rows = _rows(harness, doc)
        for name in ("gate0-divergence", "reviewer-filters", "repro-first"):
            assert rows[name]["reason"] == "missing_arm %s off-2" % S3
        assert rows["safety-fact"]["reason"] != "missing_arm %s off-2" % S3

    def test_missing_routes(self, harness):
        doc = _decided_doc()
        doc["stories"][1]["routes"] = None
        rows = _rows(harness, doc)
        assert {row["reason"] for row in rows.values()} == {"missing_arm %s routes" % S2}

    def test_inapplicable_arm_is_not_missing(self, harness):
        doc = _decided_doc()
        assert "safety-fact" not in doc["stories"][2]["arms"]   # S3 evaluator-agent
        doc["labeled_by"] = "A. Maintainer"
        assert _rows(harness, doc)["safety-fact"]["verdict"] == "remove"

    @pytest.mark.parametrize("ack,verdict,reason", [
        ("remove", "remove", "not_exercised"),
        ("amend", "unverifiable", "amendment_requested"),
        (None, "unverifiable", "not_exercised_unacknowledged"),
    ])
    def test_not_exercised(self, harness, ack, verdict, reason):
        doc = _decided_doc()
        if ack:
            doc["acks"]["repro-first"] = ack
        row = _rows(harness, doc)["repro-first"]
        assert (row["verdict"], row["exercised"], row["reason"]) == (verdict, 0, reason)
        assert row["upgrade_only"] is None

    def test_gate0_recorded_as_skip_everywhere_is_not_exercised(self, harness):
        doc = _decided_doc()
        for story in doc["stories"]:
            if "gate0-divergence" in story["arms"]:
                story["arms"]["gate0-divergence"].update(report="skip", exercised=False)
        doc["acks"]["gate0-divergence"] = "remove"
        row = _rows(harness, doc)["gate0-divergence"]
        assert (row["verdict"], row["reason"]) == ("remove", "not_exercised")

    def test_not_exercised_decides_before_labels(self, harness):
        doc = _decided_doc()
        doc["acks"]["repro-first"] = "remove"
        assert doc["labeled_by"] is None
        assert _rows(harness, doc)["repro-first"]["verdict"] == "remove"

    def test_labeled_by_null_is_unlabeled_even_with_no_findings(self, harness):
        row = _rows(harness, _decided_doc())["reviewer-filters"]
        assert (row["verdict"], row["reason"], row["upgrade_only"]) == (
            "unverifiable", "unlabeled 0", 0)

    def test_unlabeled_counts_every_finding_while_labeled_by_is_null(self, harness):
        doc = _decided_doc()
        doc["stories"][0]["upgrade_only"] = [_finding("safety-fact", FEES, "valid"),
                                             _finding("safety-fact", AC12)]
        assert _rows(harness, doc)["safety-fact"]["reason"] == "unlabeled 2"

    def test_one_unlabeled_finding(self, harness):
        doc = _decided_doc()
        doc["labeled_by"] = "A. Maintainer"
        doc["stories"][0]["upgrade_only"] = [_finding("safety-fact", FEES, "valid"),
                                             _finding("safety-fact", AC12)]
        row = _rows(harness, doc)["safety-fact"]
        assert (row["verdict"], row["reason"]) == ("unverifiable", "unlabeled 1")

    def test_keep_on_one_valid(self, harness):
        doc = _decided_doc()
        doc["labeled_by"] = "A. Maintainer"
        doc["stories"][0]["upgrade_only"] = [_finding("gate0-divergence", WEBHOOK, "valid"),
                                             _finding("gate0-divergence", LEDGER, "invalid")]
        doc["stories"][0]["off_only"]["gate0-divergence"] = 2
        doc["stories"][2]["off_only"]["gate0-divergence"] = 1
        row = _rows(harness, doc)["gate0-divergence"]
        assert row == {"name": "gate0-divergence", "verdict": "keep", "exercised": 2,
                       "upgrade_only": 2, "valid": 1, "invalid": 1, "off_only": 3,
                       "reason": None}

    def test_remove_when_none_valid(self, harness):
        doc = _decided_doc()
        doc["labeled_by"] = "A. Maintainer"
        doc["stories"][3]["upgrade_only"] = [_finding("safety-fact", FEES, "invalid")]
        row = _rows(harness, doc)["safety-fact"]
        assert (row["verdict"], row["exercised"], row["valid"], row["invalid"]) == (
            "remove", 3, 0, 1)

    def test_remove_when_exercised_with_no_findings(self, harness):
        doc = _decided_doc()
        doc["labeled_by"] = "A. Maintainer"
        row = _rows(harness, doc)["reviewer-filters"]
        assert (row["verdict"], row["exercised"], row["upgrade_only"]) == ("remove", 4, 0)

    def test_repro_exercised_on_a_bug(self, harness):
        doc = _decided_doc()
        doc["labeled_by"] = "A. Maintainer"
        doc["stories"][1]["repro_kind"] = "bug"
        row = _rows(harness, doc)["repro-first"]
        assert (row["verdict"], row["exercised"], row["off_only"]) == ("remove", 1, 0)


class TestReportOutput:
    """`report` prints the check shape: `pass`/`unverifiable`, `reason:` lines,
    one `upgrade:` line each, the caveat lines, and the summary last; `--json`
    carries the same fields. [AC-2.4]"""

    def _write(self, tmp_path: Path, doc: dict) -> Path:
        path = tmp_path / "trial.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        return path

    def _doc(self) -> dict:
        doc = _decided_doc()
        doc["upgrades"]["reviewer-filters"]["present"] = False
        for story in doc["stories"]:
            del story["arms"]["reviewer-filters"]
        doc["stories"][0]["upgrade_only"] = [_finding("safety-fact", FEES, "valid")]
        doc["stories"][0]["off_only"]["safety-fact"] = 1
        doc["stories"][1]["arms"]["repro-first"] = {"keys": [], "kind": "bug",
                                                    "exercised": True}
        doc["stories"][1]["repro_kind"] = "bug"
        doc["labeled_by"] = "A. Maintainer"
        doc["yuss_snapshot"]["unchanged"] = True
        return doc

    def test_text_report(self, harness, tmp_path):
        result = _call(harness, "report", "--trial", self._write(tmp_path, self._doc()))
        assert result.code == 0 and result.err == []
        assert result.out == [
            "pass",
            "story: %s gate3_route=review-agent gate0_route=review-agent repro=not-a-bug-fix "
            "arms=off-1,off-2,safety-fact,gate0-divergence,repro-first" % S1,
            "story: %s gate3_route=review-agent gate0_route=evaluator-agent repro=bug "
            "arms=off-1,off-2,safety-fact,repro-first" % S2,
            "story: %s gate3_route=evaluator-agent gate0_route=review-agent "
            "repro=not-a-bug-fix arms=off-1,off-2,gate0-divergence,repro-first" % S3,
            "story: %s gate3_route=review-agent gate0_route=skip repro=not-a-bug-fix "
            "arms=off-1,off-2,safety-fact,repro-first" % S4,
            "upgrade: gate0-divergence verdict=remove exercised=2/4 upgrade_only=0 valid=0 "
            "invalid=0 off_only=0",
            "upgrade: safety-fact verdict=keep exercised=3/4 upgrade_only=1 valid=1 invalid=0 "
            "off_only=1",
            "upgrade: reviewer-filters verdict=absent",
            "upgrade: repro-first verdict=remove exercised=1/4 upgrade_only=0 valid=0 "
            "invalid=0 off_only=0",
            SAMPLE_LINE,
            PROXY_LINE,
            BLINDING_LINE,
            "yuss: unchanged",
            "gate-upgrade-trial: keep 1, remove 2, unverifiable 0, absent 1 — 4 stories",
        ]

    def test_unverifiable_report_has_reason_lines_in_upgrade_order(self, harness, tmp_path):
        doc = _decided_doc()
        del doc["stories"][3]["arms"]["safety-fact"]
        doc["acks"]["repro-first"] = "amend"
        doc["stories"][0]["routes"] = dict(ROUTES_RR)
        result = _call(harness, "report", "--trial", self._write(tmp_path, doc))
        assert result.out[0] == "unverifiable"
        assert result.out[1:5] == [
            "reason: gate0-divergence unlabeled 0",
            "reason: safety-fact missing_arm %s safety-fact" % S4,
            "reason: reviewer-filters unlabeled 0",
            "reason: repro-first amendment_requested",
        ]
        upgrade_lines = [line for line in result.out if line.startswith("upgrade: ")]
        assert upgrade_lines == [
            "upgrade: gate0-divergence verdict=unverifiable exercised=2/4 upgrade_only=0 "
            "valid=0 invalid=0 off_only=0 reason=unlabeled 0",
            "upgrade: safety-fact verdict=unverifiable reason=missing_arm %s safety-fact" % S4,
            "upgrade: reviewer-filters verdict=unverifiable exercised=4/4 upgrade_only=0 "
            "valid=0 invalid=0 off_only=0 reason=unlabeled 0",
            "upgrade: repro-first verdict=unverifiable exercised=0/4 reason=amendment_requested",
        ]
        assert result.out[-2] == "yuss: not checked"
        assert result.out[-1] == ("gate-upgrade-trial: keep 0, remove 0, unverifiable 4, "
                                  "absent 0 — 4 stories")

    def test_story_line_without_routes_or_arms(self, harness, tmp_path):
        doc = _decided_doc()
        doc["stories"][0].update(routes=None, arms={}, repro_kind=None)
        result = _call(harness, "report", "--trial", self._write(tmp_path, doc))
        assert ("story: %s gate3_route=none gate0_route=none repro=none arms=none" % S1
                in result.out)

    def test_yuss_changed(self, harness, tmp_path):
        doc = self._doc()
        doc["yuss_snapshot"]["unchanged"] = False
        result = _call(harness, "report", "--trial", self._write(tmp_path, doc))
        assert result.out[0] == "pass" and result.out[-2] == "yuss: changed"

    def test_json_carries_the_same_fields(self, harness, tmp_path):
        path = self._write(tmp_path, self._doc())
        text = _call(harness, "report", "--trial", path).out
        result = _call(harness, "report", "--trial", path, "--json")
        assert result.code == 0 and len(result.out) == 1
        report = json.loads(result.out[0])
        assert set(report) == {"verdict", "reasons", "stories", "upgrades", "sample", "proxy",
                               "blinding", "yuss", "summary"}
        assert report["verdict"] == text[0] == "pass"
        assert report["reasons"] == []
        assert report["summary"] == text[-1]
        assert "sample: " + report["sample"] == SAMPLE_LINE
        assert "proxy: " + report["proxy"] == PROXY_LINE
        assert "blinding: " + report["blinding"] == BLINDING_LINE
        assert report["yuss"] == "unchanged"
        assert [row["name"] for row in report["upgrades"]] == list(UPGRADES)
        assert report["upgrades"][2] == {"name": "reviewer-filters", "verdict": "absent",
                                         "exercised": None, "upgrade_only": None, "valid": None,
                                         "invalid": None, "off_only": None, "reason": None}
        assert report["stories"][1] == {"story_id": S2, "gate3_route": "review-agent",
                                        "gate0_route": "evaluator-agent", "repro": "bug",
                                        "arms": ["off-1", "off-2", "safety-fact",
                                                 "repro-first"]}

    def test_json_reasons_match_text(self, harness, tmp_path):
        path = self._write(tmp_path, _decided_doc())
        text = _call(harness, "report", "--trial", path).out
        report = json.loads(_call(harness, "report", "--trial", path, "--json").out[0])
        assert ["reason: " + r for r in report["reasons"]] == [
            line for line in text if line.startswith("reason: ")]

    def test_missing_trial(self, harness, tmp_path):
        assert_refused(_call(harness, "report", "--trial", tmp_path / "none.json"),
                       "trial_invalid")
        assert_refused(_call(harness, "report", "--trial", tmp_path / "none.json", "--json"),
                       "trial_invalid")

    @pytest.mark.parametrize("mutate", [
        lambda doc: doc.update(schema="panel-trial-v1"),
        lambda doc: doc.update(stories="nope"),
        lambda doc: doc["stories"].append("not a story"),
        lambda doc: doc["stories"][0].pop("story_id"),
    ])
    def test_malformed_trial(self, harness, tmp_path, mutate):
        doc = _decided_doc()
        mutate(doc)
        assert_refused(_call(harness, "report", "--trial", self._write(tmp_path, doc)),
                       "trial_invalid")

    def test_unparseable_trial(self, harness, tmp_path):
        path = tmp_path / "trial.json"
        path.write_text("{not json", encoding="utf-8")
        assert_refused(_call(harness, "report", "--trial", path), "trial_invalid")


# --- end to end -----------------------------------------------------------------

class E2E(NamedTuple):
    trial: Trial
    yuss: Path
    report_empty: Result
    report_unlabeled: Result
    snapshot: Result
    sheet: Result
    label: Result
    report: Result
    report_json: Result
    sheet_filled: str


E2E_NOTE = "retry double-charges; the sketch upsert avoids it"


@pytest.fixture(scope="module")
def e2e(tmp_path_factory) -> E2E:
    """init → routes → record every applicable arm on four stories → snapshot →
    sheet → fill → label → report. reviewer-filters is absent."""
    root = tmp_path_factory.mktemp("e2e")
    harness = _load_harness()
    yuss = _mini_yuss(root)
    t = Trial(root / "trial", harness,
              present=("gate0-divergence", "safety-fact", "repro-first"), yuss=yuss)
    report_empty = t.report()
    _record_e2e(t)
    snapshot = t.call("snapshot", "--trial", t.trial, "--yuss", yuss)
    report_unlabeled = t.report()
    sheet = t.sheet("--seed", "11")
    t.fill(labels={(S1, WEBHOOK): "valid"}, notes={(S1, WEBHOOK): E2E_NOTE},
           acks={"repro-first": "remove"})
    label = t.label()
    return E2E(t, yuss, report_empty, report_unlabeled, snapshot, sheet, label, t.report(),
               t.report("--json"), t.sheet_text())


class TestEndToEnd:
    """The fixture pipeline: missing arms, unlabeled findings, then a keep, a
    remove, a not-exercised remove, and an absent upgrade.
    [AC-2.1, AC-2.2, AC-2.3, AC-2.4]"""

    def test_missing_arm_before_any_record(self, e2e):
        lines = e2e.report_empty.out
        assert lines[0] == "unverifiable"
        assert [line for line in lines if line.startswith("upgrade: ")] == [
            "upgrade: gate0-divergence verdict=unverifiable reason=missing_arm %s "
            "gate0-divergence" % S1,
            "upgrade: safety-fact verdict=unverifiable reason=missing_arm %s safety-fact" % S1,
            "upgrade: reviewer-filters verdict=absent",
            "upgrade: repro-first verdict=unverifiable reason=missing_arm %s repro-first" % S1,
        ]

    def test_unlabeled_before_label(self, e2e):
        lines = e2e.report_unlabeled.out
        assert lines[:4] == ["unverifiable",
                             "reason: gate0-divergence unlabeled 1",
                             "reason: safety-fact unlabeled 2",
                             "reason: repro-first not_exercised_unacknowledged"]
        assert [line for line in lines if line.startswith("upgrade: ")] == [
            "upgrade: gate0-divergence verdict=unverifiable exercised=1/4 upgrade_only=1 "
            "valid=0 invalid=0 off_only=2 reason=unlabeled 1",
            "upgrade: safety-fact verdict=unverifiable exercised=3/4 upgrade_only=2 valid=0 "
            "invalid=0 off_only=2 reason=unlabeled 2",
            "upgrade: reviewer-filters verdict=absent",
            "upgrade: repro-first verdict=unverifiable exercised=0/4 "
            "reason=not_exercised_unacknowledged",
        ]

    def test_snapshot_unchanged(self, e2e):
        assert e2e.snapshot.out[0] == "pass"
        assert e2e.trial.doc()["yuss_snapshot"]["unchanged"] is True

    def test_sheet_has_three_findings_and_one_ack(self, e2e):
        assert_ran(e2e.sheet)
        assert e2e.sheet.out[2:4] == ["findings: 3", "not_exercised: repro-first"]
        entries = _sheet_entries(e2e.sheet_filled)
        assert sorted(entries) == ["F01", "F02", "F03"]
        assert sorted((v["story"], v["key"]) for v in entries.values()) == [
            (S1, FEES), (S1, WEBHOOK), (S4, FEES)]
        text = e2e.sheet_filled
        block = text[text.index("### not exercised: repro-first"):].splitlines()
        assert block == (["### not exercised: repro-first", "exercised: 0/4"]
                         + ["- %s: not-a-bug-fix" % sid for sid in ALL_STORIES]
                         + ["ack: remove"])

    def test_gate0_excerpt_shows_the_avoided_by_line(self, e2e):
        fid = next(k for k, v in _sheet_entries(e2e.sheet_filled).items() if v["key"] == WEBHOOK)
        text = (e2e.trial.state / "findings" / ("%s.md" % fid)).read_text(encoding="utf-8")
        assert "**Avoided by:**" in text

    def test_label(self, e2e):
        assert e2e.label.out[1:4] == ["labeled: 3 (valid 1, invalid 2)",
                                      "acks: repro-first=remove", "labeled_by: A. Maintainer"]

    def test_final_report(self, e2e):
        assert e2e.report.code == 0
        assert e2e.report.out[0] == "pass"
        assert [line for line in e2e.report.out if line.startswith("upgrade: ")] == [
            "upgrade: gate0-divergence verdict=keep exercised=1/4 upgrade_only=1 valid=1 "
            "invalid=0 off_only=2",
            "upgrade: safety-fact verdict=remove exercised=3/4 upgrade_only=2 valid=0 "
            "invalid=2 off_only=2",
            "upgrade: reviewer-filters verdict=absent",
            "upgrade: repro-first verdict=remove exercised=0/4 reason=not_exercised",
        ]
        assert e2e.report.out[-5:] == [
            SAMPLE_LINE, PROXY_LINE, BLINDING_LINE, "yuss: unchanged",
            "gate-upgrade-trial: keep 1, remove 2, unverifiable 0, absent 1 — 4 stories"]
        report = json.loads(e2e.report_json.out[0])
        assert [r["verdict"] for r in report["upgrades"]] == ["keep", "remove", "absent",
                                                              "remove"]

    def test_story_lines(self, e2e):
        assert [line for line in e2e.report.out if line.startswith("story: ")] == [
            "story: %s gate3_route=review-agent gate0_route=review-agent repro=not-a-bug-fix "
            "arms=off-1,off-2,safety-fact,gate0-divergence,repro-first" % S1,
            "story: %s gate3_route=review-agent gate0_route=evaluator-agent "
            "repro=not-a-bug-fix arms=off-1,off-2,safety-fact,repro-first" % S2,
            "story: %s gate3_route=evaluator-agent gate0_route=review-agent "
            "repro=not-a-bug-fix arms=off-1,off-2,gate0-divergence,repro-first" % S3,
            "story: %s gate3_route=review-agent gate0_route=skip repro=not-a-bug-fix "
            "arms=off-1,off-2,safety-fact,repro-first" % S4,
        ]


# --- AC-2.5: no reviewer, diff, or story text in trial files ---------------------

FIXTURE_LINES = sorted({line.strip() for path in FIXTURES.glob("*.md")
                        for line in path.read_text(encoding="utf-8").splitlines()
                        if len(line.strip()) >= 6}
                       | {line.strip() for path in FIXTURES.glob("verifier-*.txt")
                          for line in path.read_text(encoding="utf-8").splitlines()[1:]})
TOKEN = re.compile(r"^[A-Za-z0-9._:/#@+()\[\]=-]*$")
FORBIDDEN = ("@@", "+++", "---", "\n", "\r", "`")
SHEET_LINE = re.compile(
    r"^(?:|# Gate Upgrade Trial — Labeling Sheet|## Findings|## Not exercised|\(none\)"
    r"|### F\d{2,3}|### not exercised: [a-z0-9-]+"
    r"|(?:story|key|severity|excerpt): [A-Za-z0-9._:/#@+()\[\]-]+"
    r"|label:(?: valid| invalid)?|ack:(?: remove| amend)?|note:|exercised: \d+/\d+"
    r"|- [A-Za-z0-9._/-]+: (?:route [a-z-]+(?: \(unverifiable: [a-z_ ]+\))?"
    r"|skip \(gate0-divergence run\)|not-a-bug-fix))$")


def _strings(node: object) -> Iterator[str]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings(value)
    elif isinstance(node, str):
        yield node


def assert_text_free_trial(text: str, phrases: Sequence[str]) -> None:
    """Only IDs, paths, SHAs, keys, severities, labels, notes, and acks."""
    for value in _strings(json.loads(text)):
        assert not any(marker in value for marker in FORBIDDEN), value
        assert not any(line in value for line in FIXTURE_LINES), value
        assert TOKEN.match(value) or value in phrases, value


def assert_text_free_sheet(text: str, notes: Sequence[str]) -> None:
    lines = text.splitlines()
    assert lines[2] == SHEET_HEADER
    for line in lines[:2] + lines[3:]:
        assert not any(marker in line for marker in ("@@", "+++", "---", "`")), line
        assert not any(fixture in line for fixture in FIXTURE_LINES), line
        assert SHEET_LINE.match(line) or line in ["note: %s" % n for n in notes], line


class TestNoText:
    """Fixture trial files written by `init`, `record`, `sheet`, and `label`
    hold no reviewer output line, diff marker, or story text. [AC-2.5]"""

    PHRASES = ("unverifiable: no planned files", "A. Maintainer", E2E_NOTE, "")

    def test_scan_catches_text(self):
        """The scan itself fails on the text it guards against."""
        for bad in ("@@ -10,3 +10,3 @@", "+++ b/app/api/pay/route.ts",
                    "- **Severity:** Critical", "two words"):
            with pytest.raises(AssertionError):
                assert_text_free_trial(json.dumps({"k": bad}), ())
        story_line = next(line for line in FIXTURE_LINES if "As a host" in line)
        with pytest.raises(AssertionError):
            assert_text_free_trial(json.dumps({"k": story_line}), ())

    def test_every_e2e_trial_file_state(self, e2e):
        history = e2e.trial.history
        assert len(history) >= 20   # init, 17 records, snapshot, sheet, label
        for text in history:
            assert_text_free_trial(text, self.PHRASES)

    def test_e2e_labeled_trial_file(self, e2e):
        text = e2e.trial.trial.read_text(encoding="utf-8")
        assert_text_free_trial(text, self.PHRASES)
        assert E2E_NOTE in text and "A. Maintainer" in text

    def test_e2e_sheet(self, e2e):
        assert_text_free_sheet(e2e.sheet_filled, (E2E_NOTE,))

    def test_full_pipeline(self, full):
        assert_ran(full.sheet("--seed", "7"))
        assert_text_free_sheet(full.sheet_text(), ())
        note = "owner check missing at that commit"
        full.fill(label="valid", notes={(S1, FEE_SHARE): note})
        assert_ran(full.label())
        assert_text_free_sheet(full.sheet_text(), (note,))
        for text in full.history:
            assert_text_free_trial(text, self.PHRASES + (note,))

    def test_raw_outputs_stay_in_the_state_dir(self, e2e):
        """The reviewer text the scan rejects is in the gitignored state dir."""
        raw = (e2e.trial.state / SLUG1 / "off-1.md").read_text(encoding="utf-8")
        assert "@@ -10,3 +10,3 @@" in raw

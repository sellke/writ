#!/usr/bin/env python3
"""Tests for the gate-upgrade trial harness (spec `2026-10-25-gate-upgrade-removal-measurement`).

The harness is `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` (dev-only).
Story 1 covers `init` (skeleton, presence probes, refusals) and `prepare`
(read-only checkout, `parent/` worktree, routes, blast radius, arm configs,
refusals). A throwaway local git repo under pytest's `tmp_path` stands in for
yuss; nothing here reads or writes the real yuss or the primary checkout, and
nothing touches the network.

Most tests load the harness by file path and call `main([...])` in-process
(so `REVIEW_PANEL` and `SCRIPTS` can be monkeypatched); a few run it as a CLI.

Temporary: Story 4 deletes this file, its fixtures, and the harness.
[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

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

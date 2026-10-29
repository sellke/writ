#!/usr/bin/env python3
"""Tests for scripts/divergence-trial.py (spec `2026-10-25-design-divergence`, Story 4).

The harness prepares, records, blinds, rates, and scores a trial of declared-axes
drafts against naive drafts. Every subcommand runs through the CLI with
`sys.executable`; every file lives under `tmp_path`. A filled sheet is produced
in-test from the blinded sheet, so its body matches what `blind` wrote.

Temporary: Story 6 deletes this file, its fixtures, and the harness.
[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "divergence-trial.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "divergence-trial"
BRIEFS = FIXTURES / "briefs"
AXES = FIXTURES / "drafts" / "axes.md"
NAIVE = FIXTURES / "drafts" / "naive.md"
INVALID = FIXTURES / "invalid"

BRIEF_IDS = ["api-1", "api-2", "data-model-1", "data-model-2", "ui-1", "ui-2"]
FIELDS = ("distinct_X", "distinct_Y", "more_distinct", "render_only_enough", "note")
CAVEAT = ("sample: 6 briefs, one rater; declared axes must win 4 of 6 — "
          "a small sample, not a general result")
BLINDING = "blinding: honor-system; the rater opened only the sheet"
BRIEF_LINE = re.compile(
    r"^brief: (\S+) medium=(ui|api|data-model) winner=(axes|naive|tie|-) "
    r"distinct axes=(\d|-) naive=(\d|-) render_only=(yes|no|-)$")


class Run:
    def __init__(self, proc: subprocess.CompletedProcess) -> None:
        self.code = proc.returncode
        self.out = proc.stdout.splitlines()
        self.err = proc.stderr.splitlines()


def run(*args: str, cwd: Optional[Path] = None) -> Run:
    proc = subprocess.run([sys.executable, str(SCRIPT), *[str(a) for a in args]],
                          capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    return Run(proc)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_refused(result: Run) -> None:
    """Exit 2, nothing on stdout, `reason:` lines then the summary last on stderr."""
    assert result.code == 2, (result.out, result.err)
    assert result.out == []
    assert result.err, "a refusal says why"
    assert result.err[-1].startswith("divergence-trial: refused"), result.err
    assert any(line.startswith("reason: ") for line in result.err), result.err


def assert_ran(result: Run) -> None:
    assert result.code == 0, (result.out, result.err)
    assert result.out[0] == "pass", result.out
    assert result.out[-1].startswith("divergence-trial: "), result.out


def copy_briefs(tmp: Path) -> Path:
    dest = tmp / "briefs"
    shutil.copytree(str(BRIEFS), str(dest))
    return dest


def init_trial(tmp: Path) -> Path:
    trial = tmp / "eval" / "trial.json"
    assert_ran(run("init", "--briefs", BRIEFS, "--out", trial))
    return trial


def recorded_trial(tmp: Path, skip: Tuple[str, str] = ("", "")) -> Path:
    trial = init_trial(tmp)
    for brief in BRIEF_IDS:
        for arm, drafts in (("axes", AXES), ("naive", NAIVE)):
            if (brief, arm) == skip:
                continue
            assert_ran(run("record", "--trial", trial, "--brief", brief, "--arm", arm,
                           "--drafts", drafts))
    return trial


def blinded_trial(tmp: Path, seed: str = "7") -> Tuple[Path, Path]:
    trial = recorded_trial(tmp)
    sheet = tmp / "eval" / "rating-sheet.md"
    assert_ran(run("blind", "--trial", trial, "--sheet", sheet, "--seed", seed))
    return trial, sheet


def fill(sheet_text: str, values: Dict[str, Dict[str, str]]) -> str:
    """Write rating values into the blank field lines under each `### Rating: <id>`."""
    out: List[str] = []
    current = None
    for line in sheet_text.split("\n"):
        heading = re.match(r"^### Rating: (\S+)$", line)
        if heading:
            current = heading.group(1)
        field = re.match(r"^(%s):$" % "|".join(FIELDS), line)
        if field and current in values and field.group(1) in values[current]:
            line = "%s: %s" % (field.group(1), values[current][field.group(1)])
        out.append(line)
    return "\n".join(out)


def key_sets(sheet: Path) -> Dict[str, Dict[str, str]]:
    """brief -> {arm: set label}, read from key.json beside the sheet."""
    key = json.loads((sheet.parent / "key.json").read_text(encoding="utf-8"))
    sets = {}
    for brief, entry in key["briefs"].items():
        sets[brief] = {entry[label]["arm"]: label for label in ("X", "Y")}
    return sets


def by_arm(sheet: Path, plan: Dict[str, Tuple[str, int, int, str]]) -> Dict[str, Dict[str, str]]:
    """plan: brief -> (winner arm or 'tie', axes distinct, naive distinct, render_only)."""
    sets = key_sets(sheet)
    values = {}
    for brief, (winner, axes_n, naive_n, render) in plan.items():
        s = sets[brief]
        values[brief] = {
            "distinct_" + s["axes"]: str(axes_n),
            "distinct_" + s["naive"]: str(naive_n),
            "more_distinct": "tie" if winner == "tie" else s[winner],
            "render_only_enough": render,
            "note": "rated %s" % brief,
        }
    return values


def rate_plan(tmp: Path, plan: Dict[str, Tuple[str, int, int, str]]) -> Path:
    trial, sheet = blinded_trial(tmp)
    sheet.write_text(fill(sheet.read_text(encoding="utf-8"), by_arm(sheet, plan)),
                     encoding="utf-8")
    assert_ran(run("rate", "--trial", trial, "--sheet", sheet, "--rated-by", "Rater"))
    return trial


def uniform(winner: str, axes_n: int, naive_n: int, render: str = "yes"):
    return {b: (winner, axes_n, naive_n, render) for b in BRIEF_IDS}


# --- init [AC-4.1] -----------------------------------------------------------


def test_init_writes_skeleton(tmp_path):
    trial = tmp_path / "trial.json"
    result = run("init", "--briefs", BRIEFS, "--out", trial)
    assert_ran(result)
    doc = json.loads(trial.read_text(encoding="utf-8"))
    assert doc["schema"] == "divergence-trial-v1"
    assert [b["id"] for b in doc["briefs"]] == BRIEF_IDS
    for brief in doc["briefs"]:
        assert brief["medium"] == brief["id"].rsplit("-", 1)[0]
        assert brief["brief_sha256"] == sha(BRIEFS / ("%s.md" % brief["id"]))
        assert brief["arms"] == {}
    assert doc["blind"] is None and doc["rated_by"] is None and doc["ratings"] is None
    assert sum(1 for line in result.out if line.startswith("brief: ")) == 6


@pytest.mark.parametrize("change", ["five", "seven", "split", "no-id", "no-medium",
                                    "bad-medium", "duplicate-id", "bad-id"])
def test_init_refuses_bad_briefs(tmp_path, change):
    briefs = copy_briefs(tmp_path)
    ui1 = briefs / "ui-1.md"
    if change == "five":
        ui1.unlink()
    elif change == "seven":
        (briefs / "ui-3.md").write_text("id: ui-3\nmedium: ui\n\nThird.\n", encoding="utf-8")
    elif change == "split":
        (briefs / "api-1.md").write_text("id: ui-3\nmedium: ui\n\nMoved.\n", encoding="utf-8")
    elif change == "no-id":
        ui1.write_text("medium: ui\n\nNo id.\n", encoding="utf-8")
    elif change == "no-medium":
        ui1.write_text("id: ui-1\n\nNo medium.\n", encoding="utf-8")
    elif change == "bad-medium":
        ui1.write_text("id: ui-1\nmedium: cli\n\nWrong.\n", encoding="utf-8")
    elif change == "duplicate-id":
        (briefs / "ui-2.md").write_text("id: ui-1\nmedium: ui\n\nSame id.\n", encoding="utf-8")
    elif change == "bad-id":
        ui1.write_text("id: ../ui-1\nmedium: ui\n\nPath id.\n", encoding="utf-8")
    out = tmp_path / "trial.json"
    assert_refused(run("init", "--briefs", briefs, "--out", out))
    assert not out.exists()


def test_init_refuses_missing_briefs_dir(tmp_path):
    out = tmp_path / "trial.json"
    assert_refused(run("init", "--briefs", tmp_path / "nope", "--out", out))
    assert not out.exists()


def test_init_refuses_existing_out_without_force(tmp_path):
    out = tmp_path / "trial.json"
    out.write_text("keep me\n", encoding="utf-8")
    assert_refused(run("init", "--briefs", BRIEFS, "--out", out))
    assert out.read_text(encoding="utf-8") == "keep me\n"
    assert_ran(run("init", "--briefs", BRIEFS, "--out", out, "--force"))
    assert json.loads(out.read_text(encoding="utf-8"))["schema"] == "divergence-trial-v1"


# --- record [AC-4.2] ---------------------------------------------------------


def test_record_stores_hash_count_and_raw_copy(tmp_path):
    trial = init_trial(tmp_path)
    result = run("record", "--trial", trial, "--brief", "ui-1", "--arm", "axes",
                 "--drafts", AXES)
    assert_ran(result)
    assert "1 of 12 arms recorded" in result.out[-1]
    doc = json.loads(trial.read_text(encoding="utf-8"))
    brief = next(b for b in doc["briefs"] if b["id"] == "ui-1")
    assert brief["arms"] == {"axes": {"sha256": sha(AXES), "drafts": 3}}
    raw = trial.parent / "raw" / "ui-1" / "axes.md"
    assert raw.read_bytes() == AXES.read_bytes()


def test_record_naive_and_rerecord_replaces(tmp_path):
    trial = init_trial(tmp_path)
    assert_ran(run("record", "--trial", trial, "--brief", "api-1", "--arm", "naive",
                   "--drafts", NAIVE))
    other = tmp_path / "naive-2.md"
    other.write_text(NAIVE.read_text(encoding="utf-8").replace("Simple list", "Plain list"),
                     encoding="utf-8")
    assert_ran(run("record", "--trial", trial, "--brief", "api-1", "--arm", "naive",
                   "--drafts", other))
    doc = json.loads(trial.read_text(encoding="utf-8"))
    brief = next(b for b in doc["briefs"] if b["id"] == "api-1")
    assert brief["arms"]["naive"]["sha256"] == sha(other)
    assert (trial.parent / "raw" / "api-1" / "naive.md").read_bytes() == other.read_bytes()


@pytest.mark.parametrize("arm,name", [
    ("axes", "two-drafts.md"),
    ("axes", "four-drafts.md"),
    ("axes", "axes-missing-commitment.md"),
    ("naive", "naive-with-commitment.md"),
    ("axes", "missing-trade-off.md"),
    ("naive", "missing-title.md"),
    ("naive", "empty-structure.md"),
])
def test_record_refuses_invalid_drafts(tmp_path, arm, name):
    trial = init_trial(tmp_path)
    before = trial.read_bytes()
    assert_refused(run("record", "--trial", trial, "--brief", "ui-1", "--arm", arm,
                       "--drafts", INVALID / name))
    assert trial.read_bytes() == before
    assert not (trial.parent / "raw").exists()


def test_record_refuses_wrong_arm_template(tmp_path):
    """The valid naive file has no Commitment lines, so it cannot be an axes arm."""
    trial = init_trial(tmp_path)
    before = trial.read_bytes()
    assert_refused(run("record", "--trial", trial, "--brief", "ui-1", "--arm", "axes",
                       "--drafts", NAIVE))
    assert_refused(run("record", "--trial", trial, "--brief", "ui-1", "--arm", "naive",
                       "--drafts", AXES))
    assert trial.read_bytes() == before


def test_record_refuses_unknown_brief_missing_file_and_bad_trial(tmp_path):
    trial = init_trial(tmp_path)
    before = trial.read_bytes()
    assert_refused(run("record", "--trial", trial, "--brief", "ui-9", "--arm", "axes",
                       "--drafts", AXES))
    assert_refused(run("record", "--trial", trial, "--brief", "ui-1", "--arm", "axes",
                       "--drafts", tmp_path / "missing.md"))
    assert trial.read_bytes() == before
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema": "other"}\n', encoding="utf-8")
    assert_refused(run("record", "--trial", bad, "--brief", "ui-1", "--arm", "axes",
                       "--drafts", AXES))
    assert_refused(run("record", "--trial", tmp_path / "absent.json", "--brief", "ui-1",
                       "--arm", "axes", "--drafts", AXES))


def test_record_refuses_after_blinding(tmp_path):
    trial, _sheet = blinded_trial(tmp_path)
    before = trial.read_bytes()
    assert_refused(run("record", "--trial", trial, "--brief", "ui-1", "--arm", "axes",
                       "--drafts", AXES))
    assert trial.read_bytes() == before


def test_bad_arm_is_usage_error(tmp_path):
    trial = init_trial(tmp_path)
    result = run("record", "--trial", trial, "--brief", "ui-1", "--arm", "both",
                 "--drafts", AXES)
    assert result.code == 2 and result.out == []
    assert result.err[-1].startswith("divergence-trial: refused")


# --- blind [AC-4.3] ----------------------------------------------------------


def test_blind_refuses_missing_arm(tmp_path):
    trial = recorded_trial(tmp_path, skip=("data-model-2", "naive"))
    before = trial.read_bytes()
    sheet = tmp_path / "eval" / "rating-sheet.md"
    result = run("blind", "--trial", trial, "--sheet", sheet, "--seed", "1")
    assert_refused(result)
    assert any("missing_arm data-model-2 naive" in line for line in result.err)
    assert not sheet.exists()
    assert not (sheet.parent / "key.json").exists()
    assert trial.read_bytes() == before


def test_blind_refuses_raw_edited_after_record(tmp_path):
    trial = recorded_trial(tmp_path)
    raw = trial.parent / "raw" / "ui-2" / "axes.md"
    raw.write_text(raw.read_text(encoding="utf-8") + "edited\n", encoding="utf-8")
    before = trial.read_bytes()
    sheet = tmp_path / "eval" / "rating-sheet.md"
    assert_refused(run("blind", "--trial", trial, "--sheet", sheet, "--seed", "1"))
    assert not sheet.exists() and trial.read_bytes() == before


def test_blind_writes_sheet_key_and_hashes(tmp_path):
    trial, sheet = blinded_trial(tmp_path)
    text = sheet.read_text(encoding="utf-8")
    key = sheet.parent / "key.json"
    assert key.exists()
    doc = json.loads(trial.read_text(encoding="utf-8"))
    blind = doc["blind"]
    assert blind["sheet"] == "rating-sheet.md" and blind["key"] == "key.json"
    assert blind["key_sha256"] == sha(key)
    # Fields are blank as written, so the body hash is the file's own hash.
    assert blind["sheet_body_sha256"] == sha(sheet)
    # No arm names, no Commitment lines, no original titles.
    for leak in ("axes", "naive", "Commitment:", "Title:", "Wide table", "Simple list"):
        assert leak not in text, leak
    # The commitment's content is gone, not only its label.
    for line in AXES.read_text(encoding="utf-8").splitlines():
        if line.startswith("Commitment:"):
            value = line[len("Commitment:"):].strip()
            assert value and value not in text, value
    assert "layout=" not in text and "grouping=" not in text
    assert "\n\n\n" not in text
    for brief in BRIEF_IDS:
        medium = brief.rsplit("-", 1)[0]
        assert "## Brief %s (medium: %s)" % (brief, medium) in text
        assert "### Rating: %s" % brief in text
    assert text.count("#### Draft 1") == 12 and text.count("#### Draft 3") == 12
    assert text.count("### Set X") == 6 and text.count("### Set Y") == 6
    for field in FIELDS:
        assert len(re.findall(r"^%s:$" % field, text, re.M)) == 6
    # Draft bodies survive blinding.
    assert "cards grouped under state headings" in text
    assert "bulleted lists under group headings" in text
    # Key: every brief maps X and Y to the two arms, drafts are a permutation.
    keydoc = json.loads(key.read_text(encoding="utf-8"))
    assert sorted(keydoc["briefs"]) == BRIEF_IDS
    for entry in keydoc["briefs"].values():
        assert sorted([entry["X"]["arm"], entry["Y"]["arm"]]) == ["axes", "naive"]
        assert sorted(entry["X"]["drafts"]) == [1, 2, 3]
        assert sorted(entry["Y"]["drafts"]) == [1, 2, 3]


def test_blind_seed_is_deterministic(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    c = tmp_path / "c"
    _ta, sheet_a = blinded_trial(a, seed="42")
    _tb, sheet_b = blinded_trial(b, seed="42")
    _tc, sheet_c = blinded_trial(c, seed="43")
    assert sheet_a.read_bytes() == sheet_b.read_bytes()
    assert (a / "eval" / "key.json").read_bytes() == (b / "eval" / "key.json").read_bytes()
    assert ((a / "eval" / "key.json").read_bytes() != (c / "eval" / "key.json").read_bytes()
            or sheet_a.read_bytes() != sheet_c.read_bytes())


def test_blind_shuffles_and_assigns_both_ways(tmp_path):
    """Across six briefs a seeded run puts axes in X at least once and in Y at least once,
    and reorders at least one set."""
    _trial, sheet = blinded_trial(tmp_path, seed="42")
    keydoc = json.loads((sheet.parent / "key.json").read_text(encoding="utf-8"))
    x_arms = {entry["X"]["arm"] for entry in keydoc["briefs"].values()}
    assert x_arms == {"axes", "naive"}
    orders = [entry[s]["drafts"] for entry in keydoc["briefs"].values() for s in ("X", "Y")]
    assert any(order != [1, 2, 3] for order in orders)


def test_blind_refuses_after_rating(tmp_path):
    trial = rate_plan(tmp_path, uniform("axes", 3, 1))
    before = trial.read_bytes()
    assert_refused(run("blind", "--trial", trial, "--sheet", tmp_path / "s2.md"))
    assert trial.read_bytes() == before
    assert not (tmp_path / "s2.md").exists()


def test_blind_without_seed_runs(tmp_path):
    trial = recorded_trial(tmp_path)
    sheet = tmp_path / "out" / "sheet.md"
    assert_ran(run("blind", "--trial", trial, "--sheet", sheet))
    doc = json.loads(trial.read_text(encoding="utf-8"))
    assert doc["blind"]["sheet"] == "../out/sheet.md"
    assert doc["blind"]["key"] == "../out/key.json"


# --- rate [AC-4.4] -----------------------------------------------------------


def test_rate_stores_ratings_by_set_label(tmp_path):
    trial, sheet = blinded_trial(tmp_path)
    values = {b: {"distinct_X": "3", "distinct_Y": "1", "more_distinct": "X",
                  "render_only_enough": "no", "note": "note for %s" % b} for b in BRIEF_IDS}
    sheet.write_text(fill(sheet.read_text(encoding="utf-8"), values), encoding="utf-8")
    result = run("rate", "--trial", trial, "--sheet", sheet, "--rated-by", "Adam")
    assert_ran(result)
    doc = json.loads(trial.read_text(encoding="utf-8"))
    assert doc["rated_by"] == "Adam"
    assert set(doc["ratings"]) == set(BRIEF_IDS)
    assert doc["ratings"]["ui-1"] == {"distinct_X": 3, "distinct_Y": 1, "more_distinct": "X",
                                      "render_only_enough": "no", "note": "note for ui-1"}
    assert "axes" not in json.dumps(doc["ratings"]) and "naive" not in json.dumps(doc["ratings"])


def test_rate_tolerates_crlf_and_trailing_spaces(tmp_path):
    trial, sheet = blinded_trial(tmp_path)
    values = {b: {"distinct_X": "2  ", "distinct_Y": "2", "more_distinct": "tie",
                  "render_only_enough": "yes", "note": "same"} for b in BRIEF_IDS}
    text = fill(sheet.read_text(encoding="utf-8"), values)
    sheet.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    assert_ran(run("rate", "--trial", trial, "--sheet", sheet, "--rated-by", "Adam"))


def _full(**override: str) -> Dict[str, Dict[str, str]]:
    base = {"distinct_X": "3", "distinct_Y": "1", "more_distinct": "X",
            "render_only_enough": "yes", "note": "fine"}
    values = {b: dict(base) for b in BRIEF_IDS}
    values["api-2"].update(override)
    return values


@pytest.mark.parametrize("override", [
    {"distinct_X": ""},
    {"note": ""},
    {"distinct_Y": "4"},
    {"distinct_X": "0"},
    {"distinct_X": "two"},
    {"more_distinct": "Z"},
    {"render_only_enough": "maybe"},
    {"note": "x" * 201},
])
def test_rate_refuses_bad_field(tmp_path, override):
    trial, sheet = blinded_trial(tmp_path)
    sheet.write_text(fill(sheet.read_text(encoding="utf-8"), _full(**override)),
                     encoding="utf-8")
    before = trial.read_bytes()
    assert_refused(run("rate", "--trial", trial, "--sheet", sheet, "--rated-by", "Adam"))
    assert trial.read_bytes() == before


def test_rate_accepts_200_char_note(tmp_path):
    trial, sheet = blinded_trial(tmp_path)
    sheet.write_text(fill(sheet.read_text(encoding="utf-8"), _full(note="x" * 200)),
                     encoding="utf-8")
    assert_ran(run("rate", "--trial", trial, "--sheet", sheet, "--rated-by", "Adam"))


def test_rate_refuses_partial_ratings(tmp_path):
    trial, sheet = blinded_trial(tmp_path)
    values = _full()
    del values["ui-2"]
    sheet.write_text(fill(sheet.read_text(encoding="utf-8"), values), encoding="utf-8")
    before = trial.read_bytes()
    result = run("rate", "--trial", trial, "--sheet", sheet, "--rated-by", "Adam")
    assert_refused(result)
    assert any("ui-2" in line for line in result.err)
    assert trial.read_bytes() == before


def test_rate_refuses_multiline_note(tmp_path):
    trial, sheet = blinded_trial(tmp_path)
    text = fill(sheet.read_text(encoding="utf-8"), _full(note="first line\nsecond line"))
    sheet.write_text(text, encoding="utf-8")
    before = trial.read_bytes()
    result = run("rate", "--trial", trial, "--sheet", sheet, "--rated-by", "Adam")
    assert_refused(result)
    assert any("note" in line for line in result.err if line.startswith("reason: "))
    assert trial.read_bytes() == before


def test_rate_refuses_draft_edited_after_blinding(tmp_path):
    trial, sheet = blinded_trial(tmp_path)
    text = fill(sheet.read_text(encoding="utf-8"), _full())
    text = text.replace("cards grouped under state headings", "cards grouped by owner", 1)
    sheet.write_text(text, encoding="utf-8")
    before = trial.read_bytes()
    result = run("rate", "--trial", trial, "--sheet", sheet, "--rated-by", "Adam")
    assert_refused(result)
    assert any("body_changed" in line for line in result.err)
    assert trial.read_bytes() == before


def test_rate_refuses_deleted_field_line(tmp_path):
    trial, sheet = blinded_trial(tmp_path)
    text = fill(sheet.read_text(encoding="utf-8"), _full())
    text = text.replace("render_only_enough: yes\n", "", 1)
    sheet.write_text(text, encoding="utf-8")
    before = trial.read_bytes()
    assert_refused(run("rate", "--trial", trial, "--sheet", sheet, "--rated-by", "Adam"))
    assert trial.read_bytes() == before


@pytest.mark.parametrize("name", ["", "   "])
def test_rate_refuses_empty_rater(tmp_path, name):
    trial, sheet = blinded_trial(tmp_path)
    sheet.write_text(fill(sheet.read_text(encoding="utf-8"), _full()), encoding="utf-8")
    before = trial.read_bytes()
    assert_refused(run("rate", "--trial", trial, "--sheet", sheet, "--rated-by", name))
    assert trial.read_bytes() == before


def test_rate_refuses_unblinded_trial_and_missing_sheet(tmp_path):
    trial = recorded_trial(tmp_path)
    before = trial.read_bytes()
    sheet = tmp_path / "sheet.md"
    sheet.write_text("nothing\n", encoding="utf-8")
    assert_refused(run("rate", "--trial", trial, "--sheet", sheet, "--rated-by", "Adam"))
    trial2, _sheet2 = blinded_trial(tmp_path / "b")
    before2 = trial2.read_bytes()
    assert_refused(run("rate", "--trial", trial2, "--sheet", tmp_path / "gone.md",
                       "--rated-by", "Adam"))
    assert trial.read_bytes() == before and trial2.read_bytes() == before2


# --- report [AC-4.5] ---------------------------------------------------------


def report_lines(trial: Path) -> List[str]:
    result = run("report", "--trial", trial)
    assert result.code == 0, (result.out, result.err)
    return result.out


def assert_report_shape(lines: List[str], verdict: str) -> None:
    assert lines[0] == verdict
    reasons = [line for line in lines if line.startswith("reason: ")]
    if verdict == "unverifiable":
        assert reasons and lines[1].startswith("reason: ")
    else:
        assert reasons == []
    briefs = [line for line in lines if line.startswith("brief: ")]
    assert len(briefs) == 6
    for line in briefs:
        assert BRIEF_LINE.match(line), line
    render = [line for line in lines if line.startswith("render-only: ")]
    assert len(render) == 1
    assert lines[-3] == CAVEAT
    assert lines[-2] == BLINDING
    assert lines[-1].startswith("divergence-trial: %s" % verdict)
    # Order: verdict, reasons, briefs, render-only, caveat, blinding, summary.
    assert lines.index(render[0]) == len(lines) - 4
    assert lines.index(briefs[0]) == 1 + len(reasons)


def test_report_keep(tmp_path):
    plan = uniform("axes", 3, 1)
    plan["ui-1"] = ("naive", 2, 3, "no")
    trial = rate_plan(tmp_path, plan)
    lines = report_lines(trial)
    assert_report_shape(lines, "keep")
    assert "brief: ui-1 medium=ui winner=naive distinct axes=2 naive=3 render_only=no" in lines
    assert ("brief: api-1 medium=api winner=axes distinct axes=3 naive=1 render_only=yes"
            in lines)
    assert "render-only: yes on 5 of 6 briefs (ui 1 of 2)" in lines
    assert lines[-1] == "divergence-trial: keep — axes won 5 of 6, distinct 17 vs 8"


def test_report_keep_at_exactly_four_wins(tmp_path):
    plan = uniform("axes", 3, 2)
    plan["ui-1"] = ("naive", 1, 3, "yes")
    plan["ui-2"] = ("tie", 2, 2, "yes")
    trial = rate_plan(tmp_path, plan)
    lines = report_lines(trial)
    assert_report_shape(lines, "keep")
    assert lines[-1] == "divergence-trial: keep — axes won 4 of 6, distinct 15 vs 13"


def test_report_remove_three_wins(tmp_path):
    plan = uniform("axes", 3, 1)
    for brief in ("ui-1", "ui-2", "api-1"):
        plan[brief] = ("naive", 1, 3, "no")
    trial = rate_plan(tmp_path, plan)
    lines = report_lines(trial)
    assert_report_shape(lines, "remove")
    assert "render-only: yes on 3 of 6 briefs (ui 0 of 2)" in lines
    assert lines[-1] == "divergence-trial: remove — axes won 3 of 6, distinct 12 vs 12"


def test_report_tie_is_not_a_win(tmp_path):
    """Three wins and three ties with a higher axes total: ties do not count, so remove."""
    plan = uniform("axes", 3, 1)
    for brief in ("ui-1", "api-1", "data-model-1"):
        plan[brief] = ("tie", 3, 3, "yes")
    trial = rate_plan(tmp_path, plan)
    lines = report_lines(trial)
    assert_report_shape(lines, "remove")
    assert "brief: ui-1 medium=ui winner=tie distinct axes=3 naive=3 render_only=yes" in lines
    assert lines[-1] == "divergence-trial: remove — axes won 3 of 6, distinct 18 vs 12"


def test_report_four_wins_but_total_not_higher(tmp_path):
    plan = uniform("axes", 2, 1)
    plan["ui-1"] = ("naive", 1, 3, "yes")
    plan["ui-2"] = ("naive", 1, 3, "yes")
    trial = rate_plan(tmp_path, plan)
    lines = report_lines(trial)
    assert_report_shape(lines, "remove")
    assert lines[-1] == "divergence-trial: remove — axes won 4 of 6, distinct 10 vs 10"
    plan["api-1"] = ("axes", 2, 2, "yes")
    trial2 = rate_plan(tmp_path / "lower", plan)
    lines2 = report_lines(trial2)
    assert_report_shape(lines2, "remove")
    assert lines2[-1] == "divergence-trial: remove — axes won 4 of 6, distinct 10 vs 11"


def test_report_unrated_after_blind(tmp_path):
    trial, _sheet = blinded_trial(tmp_path)
    lines = report_lines(trial)
    assert_report_shape(lines, "unverifiable")
    assert "reason: unrated" in lines
    assert "brief: ui-1 medium=ui winner=- distinct axes=- naive=- render_only=-" in lines
    assert lines[-1] == "divergence-trial: unverifiable — unrated"


def test_report_missing_rated_by_is_unrated(tmp_path):
    trial = rate_plan(tmp_path, uniform("axes", 3, 1))
    doc = json.loads(trial.read_text(encoding="utf-8"))
    doc["rated_by"] = None
    trial.write_text(json.dumps(doc), encoding="utf-8")
    lines = report_lines(trial)
    assert_report_shape(lines, "unverifiable")
    assert "reason: unrated" in lines


def test_report_partial_ratings_in_file_is_unrated(tmp_path):
    trial = rate_plan(tmp_path, uniform("axes", 3, 1))
    doc = json.loads(trial.read_text(encoding="utf-8"))
    del doc["ratings"]["api-2"]
    doc["ratings"]["ui-1"]["distinct_X"] = 9
    trial.write_text(json.dumps(doc), encoding="utf-8")
    lines = report_lines(trial)
    assert_report_shape(lines, "unverifiable")
    assert "reason: unrated api-2" in lines
    assert "reason: unrated ui-1" in lines


def test_report_missing_arm(tmp_path):
    trial = recorded_trial(tmp_path, skip=("ui-2", "axes"))
    lines = report_lines(trial)
    assert_report_shape(lines, "unverifiable")
    assert "reason: missing_arm ui-2 axes" in lines
    assert "reason: key_missing" in lines
    assert "reason: unrated" in lines
    assert lines[-1] == "divergence-trial: unverifiable — missing_arm, key_missing, unrated"


def test_report_key_missing(tmp_path):
    trial = rate_plan(tmp_path, uniform("axes", 3, 1))
    (trial.parent / "key.json").unlink()
    lines = report_lines(trial)
    assert_report_shape(lines, "unverifiable")
    assert "reason: key_missing" in lines
    assert "brief: ui-1 medium=ui winner=- distinct axes=- naive=- render_only=yes" in lines
    assert lines[-1] == "divergence-trial: unverifiable — key_missing"


def test_report_key_changed(tmp_path):
    trial = rate_plan(tmp_path, uniform("axes", 3, 1))
    key = trial.parent / "key.json"
    doc = json.loads(key.read_text(encoding="utf-8"))
    for entry in doc["briefs"].values():
        entry["X"], entry["Y"] = entry["Y"], entry["X"]
    key.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = report_lines(trial)
    assert_report_shape(lines, "unverifiable")
    assert "reason: key_changed" in lines
    assert lines[-1] == "divergence-trial: unverifiable — key_changed"


def test_report_json(tmp_path):
    trial = rate_plan(tmp_path, uniform("axes", 3, 1))
    result = run("report", "--trial", trial, "--json")
    assert result.code == 0
    assert len(result.out) == 1
    doc = json.loads(result.out[0])
    assert doc["verdict"] == "keep"
    assert doc["reasons"] == []
    assert doc["axes_wins"] == 6
    assert doc["distinct"] == {"axes": 18, "naive": 6}
    assert len(doc["briefs"]) == 6
    assert doc["briefs"][0] == {"id": "api-1", "medium": "api", "winner": "axes",
                                "distinct_axes": 3, "distinct_naive": 1, "render_only": "yes"}
    assert doc["caveat"] == CAVEAT
    assert doc["blinding"] == BLINDING
    assert doc["summary"] == "divergence-trial: keep — axes won 6 of 6, distinct 18 vs 6"


def test_report_json_unverifiable(tmp_path):
    trial = init_trial(tmp_path)
    result = run("report", "--trial", trial, "--json")
    assert result.code == 0
    doc = json.loads(result.out[0])
    assert doc["verdict"] == "unverifiable"
    assert "unrated" in doc["reasons"] and "key_missing" in doc["reasons"]


def test_report_brief_count_unverifiable(tmp_path):
    """The report trusts no hand-edited brief list: not six briefs split two per medium."""
    trial = rate_plan(tmp_path, uniform("axes", 3, 1))
    doc = json.loads(trial.read_text(encoding="utf-8"))
    doc["briefs"] = [b for b in doc["briefs"] if b["id"] != "ui-2"]
    trial.write_text(json.dumps(doc), encoding="utf-8")
    result = run("report", "--trial", trial)
    assert result.code == 0
    assert result.out[0] == "unverifiable"
    assert any(line.startswith("reason: brief_count") for line in result.out)
    assert result.out[-1] == "divergence-trial: unverifiable — brief_count"
    # Six briefs with the wrong split are also refused a verdict.
    doc = json.loads(trial.read_text(encoding="utf-8"))
    extra = dict(doc["briefs"][0], id="api-3")
    doc["briefs"].append(extra)
    trial.write_text(json.dumps(doc), encoding="utf-8")
    result = run("report", "--trial", trial, "--json")
    assert result.code == 0
    report = json.loads(result.out[0])
    assert report["verdict"] == "unverifiable"
    assert any(r.startswith("brief_count") for r in report["reasons"])


# --- recode after Gate 3 cycle 1 ---------------------------------------------


def axes_variant(tmp: Path, old: str, new: str) -> Path:
    text = AXES.read_text(encoding="utf-8")
    assert old in text
    path = tmp / "axes-variant.md"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return path


@pytest.mark.parametrize("old,new,reason", [
    # Empty label, commitment carried on the following bullet lines.
    ("Commitment: layout=cards, grouping=state\n",
     "Commitment:\n- layout=cards\n- grouping=state\n", "empty_field draft 2 Commitment"),
    # Value on the label line, then continuation lines.
    ("Commitment: layout=cards, grouping=state\n",
     "Commitment: layout=cards\n  grouping=state\n", "commitment_multiline draft 2"),
    # Two commitment lines.
    ("Commitment: layout=cards, grouping=state\n",
     "Commitment: layout=cards\nCommitment: grouping=state\n", "duplicate_field draft 2 Commitment"),
])
def test_record_refuses_commitment_that_would_leak(tmp_path, old, new, reason):
    trial = init_trial(tmp_path)
    before = trial.read_bytes()
    result = run("record", "--trial", trial, "--brief", "ui-1", "--arm", "axes",
                 "--drafts", axes_variant(tmp_path, old, new))
    assert_refused(result)
    assert any(reason in line for line in result.err), result.err
    assert trial.read_bytes() == before
    assert not (trial.parent / "raw").exists()


def test_commitment_before_a_field_line_is_accepted(tmp_path):
    trial = init_trial(tmp_path)
    variant = axes_variant(tmp_path, "Title: Cards grouped by state\nStructure:\n",
                           "Commitment: layout=cards, grouping=state\nTitle: Cards grouped by state\n"
                           "Structure:\n")
    text = variant.read_text(encoding="utf-8").replace(
        "Trade-off: scans well; hides cross-item comparison\n"
        "Commitment: layout=cards, grouping=state\n",
        "Trade-off: scans well; hides cross-item comparison\n")
    variant.write_text(text, encoding="utf-8")
    assert_ran(run("record", "--trial", trial, "--brief", "ui-1", "--arm", "axes",
                   "--drafts", variant))


def test_blind_leaves_no_double_blank_where_a_commitment_was(tmp_path):
    """A commitment between blank lines is dropped without leaving a blank-line tell."""
    trial = init_trial(tmp_path)
    variant = axes_variant(
        tmp_path,
        "- a single table\n- one row per item, one column per attribute\n"
        "Trade-off: dense; hard to read on a narrow screen\n"
        "Commitment: layout=table, grouping=none\n",
        "- a single table\n\nCommitment: layout=table, grouping=none\n\n"
        "- one row per item, one column per attribute\n"
        "Trade-off: dense; hard to read on a narrow screen\n")
    for brief in BRIEF_IDS:
        assert_ran(run("record", "--trial", trial, "--brief", brief, "--arm", "axes",
                       "--drafts", variant))
        assert_ran(run("record", "--trial", trial, "--brief", brief, "--arm", "naive",
                       "--drafts", NAIVE))
    sheet = tmp_path / "eval" / "sheet.md"
    assert_ran(run("blind", "--trial", trial, "--sheet", sheet, "--seed", "5"))
    out = sheet.read_text(encoding="utf-8")
    assert "layout=table" not in out
    assert "\n\n\n" not in out
    assert "- a single table\n\n- one row per item" in out


def test_blind_keeps_title_lines_inside_structure(tmp_path):
    """Only each draft's first `Title:` line is the draft title; later ones are content."""
    trial = init_trial(tmp_path)
    naive = tmp_path / "naive-title.md"
    naive.write_text(NAIVE.read_text(encoding="utf-8").replace(
        "- each bullet expands to show attributes\n",
        "- each bullet expands to show attributes\nTitle: a page heading shown on every view\n", 1),
        encoding="utf-8")
    for brief in BRIEF_IDS:
        assert_ran(run("record", "--trial", trial, "--brief", brief, "--arm", "axes",
                       "--drafts", AXES))
        assert_ran(run("record", "--trial", trial, "--brief", brief, "--arm", "naive",
                       "--drafts", naive))
    sheet = tmp_path / "eval" / "sheet.md"
    assert_ran(run("blind", "--trial", trial, "--sheet", sheet, "--seed", "5"))
    out = sheet.read_text(encoding="utf-8")
    assert out.count("Title: a page heading shown on every view") == 6
    assert "Detailed list" not in out


def test_record_refuses_second_title_outside_structure(tmp_path):
    """A second `Title:` before `Structure:` is not content; it would leak a title."""
    trial = init_trial(tmp_path)
    before = trial.read_bytes()
    naive = tmp_path / "naive-two-titles.md"
    naive.write_text(NAIVE.read_text(encoding="utf-8").replace(
        "Title: Detailed list\n", "Title: Detailed list\nTitle: Expanding rows\n", 1),
        encoding="utf-8")
    result = run("record", "--trial", trial, "--brief", "ui-1", "--arm", "naive",
                 "--drafts", naive)
    assert_refused(result)
    assert any("duplicate_field draft 2 Title" in line for line in result.err), result.err
    assert trial.read_bytes() == before


def test_structure_starting_with_title_line_records_and_survives_blinding(tmp_path):
    """`Title: input` as the Structure's only continuation line is content, not empty."""
    trial = init_trial(tmp_path)
    naive = tmp_path / "naive-title-input.md"
    naive.write_text(NAIVE.read_text(encoding="utf-8").replace(
        "Structure:\n- a bulleted list of items\nTrade-off: easy to build",
        "Structure:\nTitle: input\nTrade-off: easy to build", 1), encoding="utf-8")
    for brief in BRIEF_IDS:
        assert_ran(run("record", "--trial", trial, "--brief", brief, "--arm", "axes",
                       "--drafts", AXES))
        assert_ran(run("record", "--trial", trial, "--brief", brief, "--arm", "naive",
                       "--drafts", naive))
    sheet = tmp_path / "eval" / "sheet.md"
    assert_ran(run("blind", "--trial", trial, "--sheet", sheet, "--seed", "5"))
    out = sheet.read_text(encoding="utf-8")
    assert out.count("Structure:\nTitle: input\nTrade-off: easy to build") == 6
    assert "Simple list" not in out


def test_io_error_is_a_refusal(tmp_path):
    """An --out that is a directory fails the write: exit 2, io_error, no temp file left."""
    out = tmp_path / "trial.json"
    out.mkdir()
    result = run("init", "--briefs", BRIEFS, "--out", out, "--force")
    assert_refused(result)
    assert any(line.startswith("reason: io_error") for line in result.err), result.err
    assert out.is_dir()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["trial.json"]


def test_unreadable_brief_is_a_refusal(tmp_path):
    briefs = copy_briefs(tmp_path)
    locked = briefs / "ui-1.md"
    locked.chmod(0)
    try:
        if os.access(str(locked), os.R_OK):
            pytest.skip("running with read access to mode-000 files (root)")
        out = tmp_path / "trial.json"
        result = run("init", "--briefs", briefs, "--out", out)
        assert_refused(result)
        assert any(line.startswith("reason: io_error") for line in result.err), result.err
        assert not out.exists()
    finally:
        locked.chmod(0o644)


def test_report_refuses_missing_trial(tmp_path):
    assert_refused(run("report", "--trial", tmp_path / "none.json"))


def test_help_exits_zero():
    result = run("--help")
    assert result.code == 0
    assert "init" in "\n".join(result.out) and "report" in "\n".join(result.out)

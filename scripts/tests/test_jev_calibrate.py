#!/usr/bin/env python3
"""Tests for `jev-judge.py calibrate` and the labeled fixture set (Story 4 of
`2026-09-25-jev-judgment-pilot`). [AC-4.1, AC-4.2, AC-4.3]

No test reaches the network. Scoring reads recorded responses only; `--live`
tests inject a fake transport under the `no_network` guard.
"""

from __future__ import annotations

import http.client
import importlib.util
import json
import re
import shutil
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "jev-judge.py"
FIXTURES = REPO_ROOT / "scripts" / "tests" / "fixtures" / "spec-analyze"
REPLAY_DIR = REPO_ROOT / "scripts" / "tests" / "fixtures" / "jev-replay"
THRESHOLDS = REPO_ROOT / "scripts" / "jev-thresholds.json"

CLASSES = ("contradiction", "gap", "ambiguity", "clean")
CODES = ("contradiction", "gap", "ambiguity")
LEGACY = ("story-2-event-creation-payment-flow", "story-3-fee-sharing-pro-exemption",
          "story-3-settlement-view-share-link", "story-4-messaging-migration-quick-split-guard")
GOLD_KEYS = {"label", "expected_verdict", "expected_reasons", "findings"}
FAKE_KEY = "sk-jev-FAKE-7d1b0c93e2a54f18-DO-NOT-PRINT"
KEY_VARS = ("TYPESAFE_API_KEY", "AI_GATEWAY_API_KEY", "VERCEL_OIDC_TOKEN")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def jev():
    return _load(SCRIPT, "jev_judge_cal")


@pytest.fixture
def no_network(monkeypatch):
    calls: List[str] = []

    def _boom(name):
        def _raise(*_a, **_k):
            calls.append(name)
            raise AssertionError("network or request attempted: %s" % name)
        return _raise

    monkeypatch.setattr(urllib.request, "urlopen", _boom("urlopen"))
    monkeypatch.setattr(urllib.request, "Request", _boom("Request"))
    monkeypatch.setattr(http.client.HTTPConnection, "request", _boom("HTTPConnection.request"))
    monkeypatch.setattr(http.client.HTTPSConnection, "request", _boom("HTTPSConnection.request"))
    monkeypatch.setattr(socket, "create_connection", _boom("create_connection"))
    monkeypatch.setattr(socket.socket, "connect", _boom("socket.connect"))
    return calls


def _gold_dirs() -> List[Path]:
    return sorted(p.parent for p in FIXTURES.glob("*/gold.json"))


def _gold(path: Path) -> Dict[str, Any]:
    return json.loads((path / "gold.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# The committed fixture set [AC-4.1]
# --------------------------------------------------------------------------


def test_at_least_twenty_fixtures_with_four_per_class():
    labels = [_gold(d)["label"] for d in _gold_dirs()]
    assert len(labels) >= 20
    for cls in CLASSES:
        assert labels.count(cls) >= 4, cls


def test_legacy_slugs_kept_and_new_fixtures_are_synthetic():
    slugs = [d.name for d in _gold_dirs()]
    for slug in LEGACY:
        assert slug in slugs
    new = [s for s in slugs if s not in LEGACY]
    assert len(new) >= 16
    for slug in new:
        assert re.fullmatch(r"synthetic-(contradiction|gap|ambiguity|clean)-[a-z0-9-]+", slug), slug
        assert slug.split("-")[1] == _gold(FIXTURES / slug)["label"], slug


@pytest.mark.parametrize("fixture", [d.name for d in _gold_dirs()])
def test_gold_json_keeps_the_existing_shape(fixture):
    gold = _gold(FIXTURES / fixture)
    assert set(gold) == GOLD_KEYS
    assert gold["label"] in CLASSES
    assert gold["expected_verdict"] == "pass" and gold["expected_reasons"] == []
    stories = sorted((FIXTURES / fixture / "user-stories").glob("story-*.md"))
    assert len(stories) == 1
    if gold["label"] == "clean":
        assert gold["findings"] == []
        return
    assert gold["findings"], fixture
    for finding in gold["findings"]:
        assert set(finding) <= {"code", "story", "summary", "ac_ids"}
        assert finding["code"] == gold["label"]
        assert finding["story"] == stories[0].name
        assert finding["summary"].strip()


@pytest.mark.parametrize("fixture", [d.name for d in _gold_dirs()])
def test_every_fixture_parses_with_three_criteria(jev, fixture):
    stories = jev.load_stories(FIXTURES / fixture)
    assert len(stories) == 1
    story = stories[0]
    assert len(story.criteria) >= 3
    if fixture.startswith("synthetic-"):
        assert story.user_story.startswith("**As a")
        assert all(ids for ids in story.ac_ids), "every synthetic criterion is AC-tagged"
    for finding in _gold(FIXTURES / fixture)["findings"]:
        for ac in finding.get("ac_ids", []):
            assert any(ac in ids for ids in story.ac_ids), (fixture, ac)


def test_split_file_assigns_every_fixture_once_with_every_class_in_each_split():
    splits = json.loads((FIXTURES / "splits.json").read_text(encoding="utf-8"))
    assert set(splits) == {"dev", "test"}
    slugs = {d.name for d in _gold_dirs()}
    assigned = splits["dev"] + splits["test"]
    assert sorted(assigned) == sorted(slugs)
    assert len(set(assigned)) == len(assigned)
    for name, members in splits.items():
        labels = {_gold(FIXTURES / s)["label"] for s in members}
        assert labels == set(CLASSES), name
    for slug in LEGACY:
        assert slug in splits["dev"]


# --------------------------------------------------------------------------
# Threshold selection [AC-4.2]
# --------------------------------------------------------------------------


def _rec(jev, label: str, split: str = "dev", **scores: float):
    full = {code: 0.05 for code in CODES}
    full.update(scores)
    return jev.Scored(slug="f-%s-%d" % (label, id(scores)), label=label, split=split,
                      scores=full)


def test_band_separated_emits_at_lowest_positive_and_escalates_above_clean(jev):
    recs = [_rec(jev, "gap", gap=0.75), _rec(jev, "gap", gap=0.95), _rec(jev, "gap", gap=0.85),
            _rec(jev, "clean", gap=0.45), _rec(jev, "clean", gap=0.20),
            _rec(jev, "contradiction", gap=0.60)]
    band = jev.choose_band(recs, "gap")
    assert band == {"emit": 0.75, "escalate": 0.46}


def test_band_skips_positive_within_margin_of_clean(jev):
    recs = [_rec(jev, "gap", gap=0.48), _rec(jev, "gap", gap=0.80), _rec(jev, "clean", gap=0.45)]
    band = jev.choose_band(recs, "gap")
    # 0.48 sits within the 0.05 margin above the highest clean score.
    assert band["emit"] == 0.80
    # The positive under emit must escalate, not be silently cleared.
    assert band["escalate"] == 0.46


def test_band_positive_below_clean_lowers_escalate(jev):
    recs = [_rec(jev, "ambiguity", ambiguity=0.30), _rec(jev, "ambiguity", ambiguity=0.90),
            _rec(jev, "clean", ambiguity=0.40)]
    band = jev.choose_band(recs, "ambiguity")
    assert band == {"emit": 0.90, "escalate": 0.30}


def test_band_unseparated_never_emits_and_escalates_everything(jev):
    recs = [_rec(jev, "gap", gap=0.40), _rec(jev, "gap", gap=0.47), _rec(jev, "clean", gap=0.61)]
    band = jev.choose_band(recs, "gap")
    assert band == {"emit": jev.NEVER_EMIT, "escalate": 0.0}
    assert jev.NEVER_EMIT > 1.0


def test_band_uses_only_its_own_class_scores(jev):
    recs = [_rec(jev, "contradiction", contradiction=0.48, gap=0.99),
            _rec(jev, "clean", contradiction=0.10, gap=0.99)]
    assert jev.choose_band(recs, "contradiction") == {"emit": 0.48, "escalate": 0.11}


def test_score_split_counts_tp_fp_fn_and_clean(jev):
    bands = {"contradiction": {"emit": 0.40, "escalate": 0.20},
             "gap": {"emit": 0.70, "escalate": 0.50},
             "ambiguity": {"emit": 0.60, "escalate": 0.30}}
    recs = [
        _rec(jev, "contradiction", contradiction=0.45),       # TP contradiction
        _rec(jev, "contradiction", contradiction=0.25),       # FN, escalated
        _rec(jev, "gap", gap=0.80, contradiction=0.50),       # TP gap, FP contradiction
        _rec(jev, "gap", gap=0.10),                           # FN gap, silent (predicted clean)
        _rec(jev, "ambiguity", ambiguity=0.65),               # TP ambiguity
        _rec(jev, "clean"),                                   # TP clean
        _rec(jev, "clean", gap=0.72),                         # FP gap on clean
    ]
    result = jev.score_split(recs, bands)
    assert result["contradiction"] == {"tp": 1, "fp": 1, "fp_clean": 0, "fn": 1}
    assert result["gap"] == {"tp": 1, "fp": 1, "fp_clean": 1, "fn": 1}
    assert result["ambiguity"] == {"tp": 1, "fp": 0, "fp_clean": 0, "fn": 0}
    # clean: predicted clean = no class at or above its escalate threshold.
    assert result["clean"] == {"tp": 1, "fp": 1, "fp_clean": 0, "fn": 1}
    assert result["stories"] == 7
    assert result["escalated"] == 1  # only the 0.25 contradiction story sits in a band alone
    assert result["silent_miss"] == 1


# --------------------------------------------------------------------------
# CLI: scoring recorded responses [AC-4.2, AC-4.3]
# --------------------------------------------------------------------------

STORY = """# Story 1: {title}

## User Story

**As a** tester
**I want** {title}
**So that** calibration has data

## Acceptance Criteria

- [ ] Given input A, when it runs, then output A is stored `[AC-1.1]`
- [ ] Given input B, when it runs, then output B is stored `[AC-1.2]`
- [ ] Given input C, when it runs, then output C is stored `[AC-1.3]`
"""

# slug -> (label, split, {code: p})
MINI = {
    "mini-contradiction-a": ("contradiction", "dev", {"contradiction": 0.50}),
    "mini-contradiction-b": ("contradiction", "test", {"contradiction": 0.45}),
    "mini-gap-a": ("gap", "dev", {"gap": 0.80}),
    "mini-gap-b": ("gap", "test", {"gap": 0.30}),
    "mini-ambiguity-a": ("ambiguity", "dev", {"ambiguity": 0.40}),
    "mini-ambiguity-b": ("ambiguity", "test", {"ambiguity": 0.42}),
    "mini-clean-a": ("clean", "dev", {"gap": 0.60}),
    "mini-clean-b": ("clean", "test", {}),
}


def _mini_fixtures(tmp_path: Path, splits: bool = True) -> Path:
    root = tmp_path / "fixtures"
    for slug, (label, _split, _p) in MINI.items():
        folder = root / slug / "user-stories"
        folder.mkdir(parents=True)
        filename = "story-1-%s.md" % slug
        (folder / filename).write_text(STORY.format(title=slug), encoding="utf-8")
        findings = [] if label == "clean" else [
            {"code": label, "story": filename, "summary": "labeled %s" % label}]
        (root / slug / "gold.json").write_text(json.dumps(
            {"label": label, "expected_verdict": "pass", "expected_reasons": [],
             "findings": findings}), encoding="utf-8")
    if splits:
        (root / "splits.json").write_text(json.dumps({
            "dev": sorted(s for s, v in MINI.items() if v[1] == "dev"),
            "test": sorted(s for s, v in MINI.items() if v[1] == "test")}), encoding="utf-8")
    return root


def _body(jev, questions: Dict[str, Any], index, scores: Dict[str, float],
          backend: str, live: bool = True, slug: str = "x") -> Dict[str, Any]:
    answers = {}
    for qid in questions:
        answers[qid] = {"type": "noul", "noul": scores.get(index[qid].code, 0.05)}
    body: Dict[str, Any] = {"model": jev.BACKENDS[backend].model, "answers": answers,
                            "usage": {"input_tokens": 900, "output_tokens": 60}}
    if live:
        body["writ_recording"] = {"source": "live", "backend": backend,
                                  "recorded_on": "2026-09-25", "fixture": slug}
    return body


def _record(jev, fixtures: Path, recordings: Path, backend: str = "vercel-gateway",
            only: Optional[List[str]] = None, live: bool = True) -> None:
    recordings.mkdir(parents=True, exist_ok=True)
    for slug, (_label, _split, scores) in MINI.items():
        if only is not None and slug not in only:
            continue
        state, questions, index = jev.spec_request(jev.load_stories(fixtures / slug))
        digest = jev.request_hash(jev.canonical_body(
            jev.build_body(state, questions, jev.BACKENDS[backend])))
        (recordings / ("%s.json" % digest)).write_text(
            json.dumps(_body(jev, questions, index, scores, backend, live, slug)),
            encoding="utf-8")


def _run(jev, capsys, argv: List[str], environ: Optional[Dict[str, str]] = None,
         transport=None) -> Tuple[int, str, str]:
    code = jev.main(argv, environ=environ or {}, transport=transport, sleep=lambda _s: None)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _cal_argv(fixtures: Path, recordings: Path, repo: Path, *extra: str) -> List[str]:
    return ["calibrate", "--fixtures", str(fixtures), "--recordings", str(recordings),
            "--repo", str(repo)] + list(extra)


def _verdict(out: str) -> str:
    return out.splitlines()[0]


def _reasons(out: str) -> List[str]:
    return [ln[len("reason: "):] for ln in out.splitlines() if ln.startswith("reason: ")]


def _summary(out: str) -> str:
    return out.splitlines()[-1]


def _assert_shape(out: str) -> None:
    lines = out.splitlines()
    assert lines[0] in ("pass", "fail", "unverifiable"), out
    assert lines[-1].startswith("jev-judge:"), out
    for line in lines[1:-1]:
        assert line.startswith("reason: "), out


def _repo(tmp_path: Path, provider: Optional[str]) -> Path:
    repo = tmp_path / "repo"
    (repo / ".writ").mkdir(parents=True)
    line = "" if provider is None else "- **Judgment Provider:** %s\n" % provider
    (repo / ".writ" / "config.md").write_text("# Config\n\n%s" % line, encoding="utf-8")
    return repo


def _thresholds_copy(jev, tmp_path: Path) -> Path:
    path = tmp_path / "jev-thresholds.json"
    path.write_text(json.dumps(jev._default_thresholds(), indent=2) + "\n", encoding="utf-8")
    jev.THRESHOLDS_PATH = path
    return path


def test_scores_recordings_and_prints_counts_and_thresholds(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    _record(jev, fixtures, recordings)
    code, out, err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path))
    _assert_shape(out)
    assert code == 0 and _verdict(out) == "pass", out + err
    assert _reasons(out)[0] == "scored"
    assert "model_unpinned" in _reasons(out)
    summary = _summary(out)
    assert "fixtures=8" in summary and "fit=dev" in summary
    assert "backend=vercel-gateway" in summary and "model=typesafe-ai/jev" in summary
    # dev: contradiction 0.50 vs clean 0.05 -> 0.50/0.06; gap 0.80 vs clean 0.60 -> 0.80/0.61;
    # ambiguity 0.40 vs clean 0.05 -> 0.40/0.06.
    assert "contradiction=0.50/0.06" in summary
    assert "gap=0.80/0.61" in summary
    assert "ambiguity=0.40/0.06" in summary
    assert "thresholds_written=0" in summary
    for split in ("dev", "test"):
        for cls in CLASSES:
            assert re.search(r"split=%s class=%s tp=\d+ fp=\d+ fp_clean=\d+ fn=\d+" % (split, cls),
                             err), (split, cls, err)
    # test: contradiction 0.45 < 0.50 -> FN; gap 0.30 below escalate -> FN and silent miss.
    assert "split=test class=contradiction tp=0 fp=0 fp_clean=0 fn=1" in err
    assert "split=test class=gap tp=0 fp=0 fp_clean=0 fn=1" in err
    assert "split=test class=ambiguity tp=1 fp=0 fp_clean=0 fn=0" in err
    assert re.search(r"split=test stories=4 escalated=1 silent_miss=1", err), err
    assert no_network == []


def test_without_split_file_fits_and_reports_all(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path, splits=False)
    recordings = tmp_path / "rec"
    _record(jev, fixtures, recordings)
    code, out, err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path))
    assert code == 0 and _verdict(out) == "pass", out + err
    assert "fit=all" in _summary(out)
    assert "split=all class=gap" in err


def test_unseparated_class_is_reported(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    saved = dict(MINI)
    try:
        MINI["mini-gap-a"] = ("gap", "dev", {"gap": 0.40})  # below the dev clean 0.60
        _record(jev, fixtures, recordings)
    finally:
        MINI.clear()
        MINI.update(saved)
    code, out, err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path))
    assert code == 0 and _verdict(out) == "pass"
    assert "unseparated" in _reasons(out)
    assert "gap=1.01/0.00" in _summary(out) and "unseparated=gap" in _summary(out)


def test_no_recordings_is_no_live_run_and_leaves_thresholds(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    path = _thresholds_copy(jev, tmp_path)
    before = path.read_bytes()
    code, out, _err = _run(jev, capsys, _cal_argv(fixtures, tmp_path / "empty", tmp_path,
                                                 "--write-thresholds"))
    _assert_shape(out)
    assert code == 0
    assert _verdict(out) == "unverifiable" and _reasons(out)[0] == "no_live_run", out
    assert path.read_bytes() == before
    assert no_network == []


def test_synthetic_recordings_are_not_scored(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    _record(jev, fixtures, recordings, live=False)  # no writ_recording live marker
    path = _thresholds_copy(jev, tmp_path)
    before = path.read_bytes()
    code, out, _err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path,
                                                 "--write-thresholds"))
    assert code == 0 and _reasons(out)[0] == "no_live_run", out
    assert path.read_bytes() == before


def test_partial_recordings_are_incomplete_and_leave_thresholds(jev, tmp_path, capsys,
                                                                no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    _record(jev, fixtures, recordings, only=["mini-gap-a", "mini-clean-a"])
    path = _thresholds_copy(jev, tmp_path)
    before = path.read_bytes()
    code, out, _err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path,
                                                 "--write-thresholds"))
    assert code == 0 and _verdict(out) == "unverifiable"
    assert _reasons(out)[0] == "recordings_incomplete", out
    assert "recorded=2 missing=6" in _summary(out)
    assert path.read_bytes() == before


def test_write_thresholds_after_scored_run(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    _record(jev, fixtures, recordings)
    path = _thresholds_copy(jev, tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["ac_shadow"] = {"satisfied": 0.93}  # Story 5's value is preserved
    path.write_text(json.dumps(data), encoding="utf-8")
    code, out, _err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path,
                                                 "--write-thresholds"))
    assert code == 0 and _verdict(out) == "pass", out
    assert "thresholds_written=1" in _summary(out)
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["calibrated"] is True
    assert written["backend"] == "vercel-gateway"
    assert written["model"] == "typesafe-ai/jev"
    assert written["calibrated_on"] == "2026-09-25"
    assert written["ac_shadow"] == {"satisfied": 0.93}
    assert written["spec_findings"] == {
        "contradiction": {"emit": 0.5, "escalate": 0.06},
        "gap": {"emit": 0.8, "escalate": 0.61},
        "ambiguity": {"emit": 0.4, "escalate": 0.06}}
    assert written["calibration"]["fixtures"] == 8
    assert written["calibration"]["fit_split"] == "dev"
    # The written file is valid for spec-findings, with no uncalibrated reason on its backend.
    loaded, reasons = jev._spec_thresholds(jev.BACKENDS["vercel-gateway"])
    assert reasons == [] and loaded["calibrated"] is True


def test_written_never_emit_band_is_accepted_by_spec_findings(jev, tmp_path):
    path = _thresholds_copy(jev, tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["spec_findings"]["gap"] = {"emit": jev.NEVER_EMIT, "escalate": 0.0}
    path.write_text(json.dumps(data), encoding="utf-8")
    loaded, _reasons = jev._spec_thresholds(None)
    assert jev.band(1.0, loaded["spec_findings"]["gap"]) == "escalate"
    data["spec_findings"]["gap"] = {"emit": 1.5, "escalate": 0.0}
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(jev.UsageError):
        jev._spec_thresholds(None)


def test_explicit_backend_selects_its_recordings(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    _record(jev, fixtures, recordings, backend="typesafe")
    code, out, _err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path,
                                                 "--backend", "typesafe"))
    assert code == 0 and _verdict(out) == "pass", out
    assert "backend=typesafe" in _summary(out) and "model_unpinned" not in _reasons(out)
    code, out, _err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path,
                                                 "--backend", "vercel-gateway"))
    assert _reasons(out)[0] == "no_live_run"


def test_malformed_live_recording_is_fail(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    _record(jev, fixtures, recordings)
    victim = sorted(recordings.glob("*.json"))[0]
    body = json.loads(victim.read_text(encoding="utf-8"))
    body["answers"] = {}
    victim.write_text(json.dumps(body), encoding="utf-8")
    code, out, _err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path))
    assert code == 1 and _verdict(out) == "fail" and _reasons(out)[0] == "malformed_response"


# --------------------------------------------------------------------------
# CLI: --live [AC-4.3]
# --------------------------------------------------------------------------


class FakeHTTP:
    def __init__(self, jev, fail_slugs: Tuple[str, ...] = ()):
        self.jev = jev
        self.calls: List[bytes] = []
        self.fail_slugs = fail_slugs

    def __call__(self, url, headers, payload):
        self.calls.append(payload)
        body = json.loads(payload.decode("utf-8"))
        story = next(iter(body["state"]["stories"]))
        slug = story[len("story-1-"):-len(".md")]
        if slug in self.fail_slugs:
            raise self.jev.TransportFailure("URLError")
        _label, _split, scores = MINI[slug]
        stories = self.jev.load_stories(self._fixtures / slug)
        _state, questions, index = self.jev.spec_request(stories)
        answers = {qid: {"type": "noul", "noul": scores.get(index[qid].code, 0.05)}
                   for qid in questions}
        out = {"model": "typesafe-ai/jev", "answers": answers,
               "usage": {"input_tokens": 700, "output_tokens": 50},
               "provider_metadata": {"gateway": {"cost": "0.00003", "routing": {}}}}
        return self.jev.HttpResponse(200, {}, json.dumps(out).encode("utf-8"))


def _live_env() -> Dict[str, str]:
    return {"AI_GATEWAY_API_KEY": FAKE_KEY}


def test_live_records_every_fixture_then_reuses(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    repo = _repo(tmp_path, "vercel-gateway")
    fake = FakeHTTP(jev)
    fake._fixtures = fixtures
    code, out, err = _run(jev, capsys, _cal_argv(fixtures, recordings, repo, "--live"),
                          _live_env(), transport=fake)
    assert code == 0 and _verdict(out) == "pass", out + err
    assert len(fake.calls) == len(MINI)
    assert "requested=8 reused=0" in _summary(out)
    files = sorted(recordings.glob("*.json"))
    # Each file is named by the replay hash of the request that produced it.
    assert {p.stem for p in files} == {jev.request_hash(c) for c in fake.calls}
    for path in files:
        body = json.loads(path.read_text(encoding="utf-8"))
        assert body["writ_recording"]["source"] == "live"
        assert body["writ_recording"]["backend"] == "vercel-gateway"
        assert body["writ_recording"]["fixture"] in MINI
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", body["writ_recording"]["recorded_on"])
        assert body["provider_metadata"]["gateway"]["cost"] == "0.00003"  # full body kept
    for blob in [out, err] + [p.read_text(encoding="utf-8") for p in tmp_path.rglob("*")
                              if p.is_file()]:
        assert FAKE_KEY not in blob
    code, out, _err = _run(jev, capsys, _cal_argv(fixtures, recordings, repo, "--live"),
                           _live_env(), transport=fake)
    assert code == 0 and "requested=0 reused=8" in _summary(out)
    assert len(fake.calls) == len(MINI)
    assert no_network == []


def test_live_recordings_replay_through_spec_findings(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    repo = _repo(tmp_path, "vercel-gateway")
    fake = FakeHTTP(jev)
    fake._fixtures = fixtures
    _run(jev, capsys, _cal_argv(fixtures, recordings, repo, "--live"), _live_env(),
         transport=fake)
    out_file = tmp_path / "f.json"
    code, out, _err = _run(jev, capsys, ["spec-findings", "--spec",
                                         str(fixtures / "mini-contradiction-a"), "--out",
                                         str(out_file), "--repo", str(repo)],
                           {"WRIT_JEV_REPLAY": str(recordings)})
    assert code == 0 and _verdict(out) == "pass", out


def test_live_failure_is_incomplete_and_writes_no_thresholds(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    repo = _repo(tmp_path, "vercel-gateway")
    fake = FakeHTTP(jev, fail_slugs=("mini-gap-b",))
    fake._fixtures = fixtures
    path = _thresholds_copy(jev, tmp_path)
    before = path.read_bytes()
    code, out, _err = _run(jev, capsys, _cal_argv(fixtures, recordings, repo, "--live",
                                                 "--write-thresholds"),
                           _live_env(), transport=fake)
    assert code == 0 and _verdict(out) == "unverifiable"
    assert _reasons(out)[:2] == ["recordings_incomplete", "transport_error"], out
    assert len(list(recordings.glob("*.json"))) == len(MINI) - 1
    assert path.read_bytes() == before


def test_live_needs_the_double_opt_in(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    fake = FakeHTTP(jev)
    for provider, env, reason in ((None, _live_env(), "no_config_line"),
                                  ("none", _live_env(), "provider_disabled"),
                                  ("vercel-gateway", {}, "no_api_key")):
        repo = _repo(tmp_path / (provider or "absent"), provider)
        code, out, _err = _run(jev, capsys, _cal_argv(fixtures, tmp_path / "rec", repo, "--live"),
                               env, transport=fake)
        assert code == 0 and _verdict(out) == "unverifiable", out
        assert _reasons(out)[0] == reason
    assert fake.calls == []
    assert not (tmp_path / "rec").exists()


def test_live_refuses_replay_env_and_backend_flag(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    repo = _repo(tmp_path, "vercel-gateway")
    env = dict(_live_env(), WRIT_JEV_REPLAY=str(REPLAY_DIR))
    code, _out, err = _run(jev, capsys, _cal_argv(fixtures, tmp_path / "rec", repo, "--live"), env)
    assert code == 2 and "WRIT_JEV_REPLAY" in err
    code, _out, err = _run(jev, capsys, _cal_argv(fixtures, tmp_path / "rec", repo, "--live",
                                                 "--backend", "typesafe"), _live_env())
    assert code == 2 and "--backend" in err


# --------------------------------------------------------------------------
# CLI: usage errors
# --------------------------------------------------------------------------


def test_fixtures_dir_missing_exits_2(jev, tmp_path, capsys):
    code, _out, err = _run(jev, capsys, _cal_argv(tmp_path / "nope", tmp_path, tmp_path))
    assert code == 2 and "--fixtures" in err


def test_split_file_naming_unknown_fixture_exits_2(jev, tmp_path, capsys):
    fixtures = _mini_fixtures(tmp_path)
    splits = json.loads((fixtures / "splits.json").read_text(encoding="utf-8"))
    splits["test"].append("mini-ghost")
    (fixtures / "splits.json").write_text(json.dumps(splits), encoding="utf-8")
    code, _out, err = _run(jev, capsys, _cal_argv(fixtures, tmp_path / "rec", tmp_path))
    assert code == 2 and "splits" in err


def test_bad_gold_label_exits_2(jev, tmp_path, capsys):
    fixtures = _mini_fixtures(tmp_path)
    gold = fixtures / "mini-gap-a" / "gold.json"
    gold.write_text(json.dumps({"label": "typo", "expected_verdict": "pass",
                                "expected_reasons": [], "findings": []}), encoding="utf-8")
    code, _out, err = _run(jev, capsys, _cal_argv(fixtures, tmp_path / "rec", tmp_path))
    assert code == 2 and "label" in err


# --------------------------------------------------------------------------
# The committed calibration [AC-4.2, AC-4.3]
# --------------------------------------------------------------------------


def test_every_fixture_has_a_committed_live_recording(jev):
    backend = jev.BACKENDS["vercel-gateway"]
    for fixture in _gold_dirs():
        state, questions, _index = jev.spec_request(jev.load_stories(fixture))
        digest = jev.request_hash(jev.canonical_body(jev.build_body(state, questions, backend)))
        path = REPLAY_DIR / ("%s.json" % digest)
        assert path.is_file(), "no live recording for %s; run calibrate --live" % fixture.name
        body = json.loads(path.read_text(encoding="utf-8"))
        assert body["writ_recording"]["source"] == "live", fixture.name
        assert body["writ_recording"]["fixture"] == fixture.name
        assert body["model"] == "typesafe-ai/jev"
        assert set(body["answers"]) == set(questions)


def test_committed_thresholds_match_a_fresh_score_of_the_recordings(jev, tmp_path, capsys,
                                                                    no_network):
    committed = json.loads(THRESHOLDS.read_text(encoding="utf-8"))
    assert committed["calibrated"] is True
    assert committed["backend"] == "vercel-gateway"
    assert committed["model"] == "typesafe-ai/jev"
    assert committed["calibrated_on"] == "2026-09-25"
    path = tmp_path / "th.json"
    shutil.copy(THRESHOLDS, path)
    jev.THRESHOLDS_PATH = path
    code, out, err = _run(jev, capsys, ["calibrate", "--fixtures", str(FIXTURES),
                                        "--recordings", str(REPLAY_DIR), "--repo", str(tmp_path),
                                        "--backend", "vercel-gateway", "--write-thresholds"])
    assert code == 0 and _verdict(out) == "pass", out + err
    rescored = json.loads(path.read_text(encoding="utf-8"))
    assert rescored["spec_findings"] == committed["spec_findings"]
    assert rescored["calibration"] == committed["calibration"]
    assert rescored["ac_shadow"] == committed["ac_shadow"]
    # Zero false positives on clean dev fixtures, by construction of the rule.
    for cls in CODES:
        assert re.search(r"split=dev class=%s tp=\d+ fp=\d+ fp_clean=0 fn=\d+" % cls, err), err


def test_subprocess_offline_calibrate_never_touches_network(tmp_path):
    env = {"PATH": "/usr/bin:/bin", "HTTPS_PROXY": "http://127.0.0.1:9",
           "https_proxy": "http://127.0.0.1:9", "AI_GATEWAY_API_KEY": FAKE_KEY}
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "calibrate", "--fixtures", str(FIXTURES),
         "--recordings", str(REPLAY_DIR), "--repo", str(tmp_path), "--backend",
         "vercel-gateway"], capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    _assert_shape(proc.stdout)
    assert proc.stdout.splitlines()[0] == "pass"
    assert FAKE_KEY not in proc.stdout + proc.stderr


def _rewrite_models(recordings: Path, model_for) -> None:
    for i, path in enumerate(sorted(recordings.glob("*.json"))):
        body = json.loads(path.read_text(encoding="utf-8"))
        body["model"] = model_for(i)
        path.write_text(json.dumps(body), encoding="utf-8")


def test_mixed_models_are_not_scored(jev, tmp_path, capsys, no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    _record(jev, fixtures, recordings)
    _rewrite_models(recordings, lambda i: "typesafe-ai/jev" if i else "typesafe-ai/jev-next")
    path = _thresholds_copy(jev, tmp_path)
    before = path.read_bytes()
    code, out, _err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path,
                                                 "--write-thresholds"))
    assert code == 0 and _reasons(out)[0] == "mixed_models", out
    assert path.read_bytes() == before


def test_pinned_backend_recordings_from_another_model_are_not_scored(jev, tmp_path, capsys,
                                                                     no_network):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    _record(jev, fixtures, recordings, backend="typesafe")
    _rewrite_models(recordings, lambda _i: "jev-1.14.0")
    code, out, _err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path,
                                                 "--backend", "typesafe"))
    assert code == 0 and _reasons(out)[0] == "model_mismatch", out
    assert "expected=jev-1.13.0" in _summary(out)


def test_recordings_for_both_backends_need_an_explicit_backend(jev, tmp_path, capsys):
    fixtures = _mini_fixtures(tmp_path)
    recordings = tmp_path / "rec"
    _record(jev, fixtures, recordings, backend="typesafe")
    _record(jev, fixtures, recordings, backend="vercel-gateway")
    code, _out, err = _run(jev, capsys, _cal_argv(fixtures, recordings, tmp_path))
    assert code == 2 and "--backend" in err

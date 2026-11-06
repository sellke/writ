#!/usr/bin/env python3
"""Tests for `jev-judge.py doubt`, `doubt-label`, and `doubt-calibrate` (ADR-033).

No test reaches the network: every judged call goes through an injected fake
transport, and the rule and fallback paths never build a request.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "jev-judge.py"
FAKE_KEY = "sk-jev-FAKE-doubt-DO-NOT-PRINT"
MODEL = "typesafe-ai/jev"


def _load():
    spec = importlib.util.spec_from_file_location("jev_judge_doubt", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


jev = _load()


def _repo(tmp_path: Path, provider: Optional[str] = None) -> Path:
    repo = tmp_path / "repo"
    (repo / ".writ").mkdir(parents=True)
    line = "" if provider is None else "- **Judgment Provider:** %s\n" % provider
    (repo / ".writ" / "config.md").write_text(
        "# Writ Configuration\n\n## Conventions\n\n%s- **Test Runner:** pytest\n" % line,
        encoding="utf-8")
    return repo


def _record(tmp_path: Path, **overrides: Any) -> Path:
    data: Dict[str, Any] = {
        "site": "choice",
        "question": "Which test runner should the new suite use?",
        "options": ["pytest (Recommended)", "unittest"],
        "recommended": "pytest",
        "evidence": ["pyproject.toml configures pytest", "every existing test uses pytest"],
        "reversible": True,
    }
    data.update(overrides)
    for key in [k for k, v in overrides.items() if v is _DROP]:
        data.pop(key)
    path = tmp_path / ("record-%d.json" % len(list(tmp_path.glob("record-*.json"))))
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


_DROP = object()


class Fake:
    """A transport that answers every request with one Noul value, or fails."""

    def __init__(self, p: Optional[float] = None, status: int = 200) -> None:
        self.p = p
        self.status = status
        self.calls = 0

    def __call__(self, url: str, headers: Dict[str, str], payload: bytes):
        self.calls += 1
        body = json.loads(payload.decode("utf-8"))
        assert set(body["questions"]) == {jev.DOUBT_QUESTION}
        assert body["state"]["decision"]["question"]
        if self.status != 200:
            return jev.HttpResponse(self.status, {}, b"{}")
        answer = {"model": MODEL, "answers": {jev.DOUBT_QUESTION: {"noul": self.p}}}
        return jev.HttpResponse(200, {}, json.dumps(answer).encode("utf-8"))


def _run(capsys, repo: Path, argv: List[str], env: Optional[Dict[str, str]] = None,
         transport: Optional[Fake] = None):
    code = jev.main(["--help"] if not argv else argv[:1] + ["--repo", str(repo)] + argv[1:],
                    environ=env or {}, transport=transport, sleep=lambda s: None)
    out = capsys.readouterr().out
    return code, out.splitlines()


def _log_rows(repo: Path) -> List[Dict[str, Any]]:
    path = repo / ".writ" / "state" / "doubt-log.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


ENABLED = {"AI_GATEWAY_API_KEY": FAKE_KEY}


# --------------------------------------------------------------------------
# The rules: no network, no judgment
# --------------------------------------------------------------------------


@pytest.mark.parametrize("overrides,reason", [
    ({"site": "merge"}, "no_verification_ledger"),
    ({"site": "release"}, "outward"),
    ({"reversible": False}, "not_revertable"),
    ({"recommended": ""}, "no_recommendation"),
    ({"conflict": True}, "conflicting_evidence"),
    ({"evidence": []}, "no_evidence"),
])
def test_rules_ask_without_calling_jev(tmp_path, capsys, overrides, reason):
    repo = _repo(tmp_path, "vercel-gateway")
    fake = Fake(p=0.0)
    code, lines = _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path, **overrides))],
                       env=ENABLED, transport=fake)
    assert code == 1
    assert lines[0] == "fail"
    assert "reason: %s" % reason in lines
    assert "(ask) %s" % reason in lines[-1]
    assert fake.calls == 0
    row = _log_rows(repo)[-1]
    assert row["verdict"] == "ask" and row["source"] == "rules" and row["p"] is None


# --------------------------------------------------------------------------
# The fallback: no provider, or an uncalibrated threshold
# --------------------------------------------------------------------------


@pytest.mark.parametrize("site,code,verdict,reason", [
    ("choice", 0, "pass", "fallback_act"),
    ("route", 0, "pass", "fallback_act"),
    ("plan", 0, "pass", "fallback_act"),
    ("destructive", 0, "pass", "fallback_act"),
    ("direction", 1, "fail", "fallback_direction"),
    ("design", 1, "fail", "fallback_design"),
])
def test_fallback_without_provider(tmp_path, capsys, site, code, verdict, reason):
    repo = _repo(tmp_path)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path, site=site))])
    assert rc == code
    assert lines[0] == verdict
    assert "reason: %s" % reason in lines
    assert "reason: jev_no_config_line" in lines
    row = _log_rows(repo)[-1]
    assert row["source"] == "fallback" and row["site"] == site


def test_uncalibrated_provider_shadows_and_logs_p(tmp_path, capsys):
    """Jev runs first and its p is logged, but without a calibrated threshold
    the site's fallback decides."""
    repo = _repo(tmp_path, "vercel-gateway")
    fake = Fake(p=0.91)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path))],
                     env=ENABLED, transport=fake)
    assert rc == 0 and lines[0] == "pass"
    assert "reason: fallback_act" in lines and "reason: doubt_uncalibrated" in lines
    assert fake.calls == 1
    row = _log_rows(repo)[-1]
    assert row["p"] == pytest.approx(0.91) and row["model"] == MODEL
    assert row["judgment"] == jev.DOUBT_QUESTION
    assert row["act"] is None and row["source"] == "fallback"


def test_transport_failure_falls_back(tmp_path, capsys):
    repo = _repo(tmp_path, "vercel-gateway")
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path, site="direction"))],
                     env=ENABLED, transport=Fake(status=500))
    assert rc == 1 and lines[0] == "fail"
    assert "reason: fallback_direction" in lines
    assert any(line.startswith("reason: jev_") for line in lines)


# --------------------------------------------------------------------------
# A calibrated threshold decides both ways
# --------------------------------------------------------------------------


def _calibrated(repo: Path, act: float = 0.6, model: str = MODEL,
                backend: str = "vercel-gateway", judgment: Optional[str] = None) -> None:
    (repo / ".writ" / "doubt-thresholds.json").write_text(json.dumps({
        "calibrated": True, "backend": backend, "model": model, "act": act,
        "judgment": judgment or jev.DOUBT_QUESTION}), encoding="utf-8")


def test_calibrated_high_confidence_acts_on_a_direction_decision(tmp_path, capsys):
    repo = _repo(tmp_path, "vercel-gateway")
    _calibrated(repo)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path, site="direction"))],
                     env=ENABLED, transport=Fake(p=0.8))
    assert rc == 0 and lines[0] == "pass"
    assert "reason: jev_clear" in lines
    assert "p=0.80 act=0.60" in lines[-1]


@pytest.mark.parametrize("p", [0.4, 0.6])
def test_calibrated_confidence_at_or_below_the_threshold_asks(tmp_path, capsys, p):
    repo = _repo(tmp_path, "vercel-gateway")
    _calibrated(repo)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path))],
                     env=ENABLED, transport=Fake(p=p))
    assert rc == 1 and lines[0] == "fail"
    assert "reason: jev_doubt" in lines
    assert _log_rows(repo)[-1]["source"] == "jev"


@pytest.mark.parametrize("kwargs", [{"model": "some-other-model"},
                                    {"judgment": "needs_person"}])
def test_threshold_for_another_model_or_question_is_not_applied(tmp_path, capsys, kwargs):
    repo = _repo(tmp_path, "vercel-gateway")
    _calibrated(repo, **kwargs)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path, site="direction"))],
                     env=ENABLED, transport=Fake(p=0.99))
    assert rc == 1
    assert "reason: fallback_direction" in lines
    assert "reason: uncalibrated_thresholds" in lines


# --------------------------------------------------------------------------
# Malformed records are the caller's bug: exit 2, nothing logged
# --------------------------------------------------------------------------


@pytest.mark.parametrize("overrides", [
    {"site": "everything"},
    {"options": ["only one"]},
    {"recommended": "neither"},
    {"reversible": _DROP},
    {"evidence": "not a list"},
    {"question": "  "},
])
def test_malformed_record_is_a_usage_error(tmp_path, capsys, overrides):
    repo = _repo(tmp_path)
    rc, _lines = _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path, **overrides))])
    assert rc == 2
    assert not (repo / ".writ" / "state" / "doubt-log.jsonl").exists()


# --------------------------------------------------------------------------
# doubt-label
# --------------------------------------------------------------------------


def test_label_appends_and_is_read_back(tmp_path, capsys):
    repo = _repo(tmp_path)
    _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path, site="direction"))])
    rid = _log_rows(repo)[-1]["id"]
    rc, lines = _run(capsys, repo, ["doubt-label", "--id", rid, "--outcome", "as_recommended"])
    assert rc == 0 and lines[0] == "pass"
    decisions, labels = jev.read_doubt_log(repo / ".writ" / "state" / "doubt-log.jsonl")
    assert rid in decisions and labels[rid] == "as_recommended"


def test_label_rejects_an_unknown_id(tmp_path, capsys):
    repo = _repo(tmp_path)
    rc, _lines = _run(capsys, repo, ["doubt-label", "--id", "nope", "--outcome", "overridden"])
    assert rc == 2


# --------------------------------------------------------------------------
# doubt-calibrate
# --------------------------------------------------------------------------


def _example(rid: str, outcome: str, draws: List[float], model: Optional[str] = MODEL,
             judgment: Optional[str] = None) -> Dict[str, Any]:
    return {"id": rid, "question": "Q %s?" % rid, "options": ["A", "B"], "recommended": "A",
            "evidence": [], "outcome": outcome, "draws": list(draws), "model": model,
            "judgment": judgment or jev.DOUBT_QUESTION}


def _draws(p: float) -> List[float]:
    return [p] * jev.DOUBT_DRAWS


def _extra(tmp_path: Path, rows: List[Dict[str, Any]]) -> Path:
    path = tmp_path / "extra.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def _separable(override_draws: Optional[List[List[float]]] = None,
               accepted: int = 30) -> List[Dict[str, Any]]:
    """Accepted decisions score 0.90 down to 0.61; four overrides score 0.4."""
    rows = [_example("acc-%d" % i, "as_recommended", _draws(0.9 - 0.01 * i))
            for i in range(accepted)]
    for i, draws in enumerate(override_draws or [_draws(0.4)] * 4):
        rows.append(_example("ovr-%d" % i, "overridden", draws))
    return rows


def _calibrate(capsys, tmp_path: Path, rows: List[Dict[str, Any]], *flags: str,
               provider: Optional[str] = None):
    repo = _repo(tmp_path, provider)
    rc, lines = _run(capsys, repo, ["doubt-calibrate", "--extra", str(_extra(tmp_path, rows))]
                     + list(flags))
    return repo, rc, lines


def test_calibrate_writes_a_threshold_above_every_override_draw(tmp_path, capsys):
    """A live decision is scored once, with fresh noise: the threshold clears the
    highest score any override got on any draw, not its first or its mean."""
    overrides = [[0.3, 0.5, 0.4], [0.5, 0.45, 0.5], [0.42] * 3, [0.38] * 3]
    repo, rc, lines = _calibrate(capsys, tmp_path, _separable(overrides), "--write",
                                 provider="vercel-gateway")
    assert rc == 0 and lines[0] == "pass", lines
    written = json.loads((repo / ".writ" / "doubt-thresholds.json").read_text(encoding="utf-8"))
    assert written["calibrated"] is True and written["act"] == pytest.approx(0.5)
    assert written["judgment"] == jev.DOUBT_QUESTION and written["draws"] == jev.DOUBT_DRAWS
    assert written["backend"] == "vercel-gateway" and written["model"] == MODEL
    assert written["overrides"] == 4 and written["slipped"] == 0
    assert written["false_act_bound"] <= jev.DOUBT_MAX_FALSE_ACT


@pytest.mark.parametrize("overrides,verdict", [
    ([_draws(0.4)] * 4, "pass"),
    # One override scores above the others: a threshold fitted without it acts on
    # it, and one slip in four lifts the bound past the cap.
    ([_draws(0.45)] + [_draws(0.4)] * 3, "unverifiable"),
], ids=["no override slips", "one override slips"])
def test_calibrate_bounds_overrides_left_out_of_the_fit(tmp_path, capsys, overrides, verdict):
    repo, rc, lines = _calibrate(capsys, tmp_path, _separable(overrides, accepted=26),
                                 "--write")
    assert rc == 0 and lines[0] == verdict, lines
    assert ("slipped=%d" % (verdict == "unverifiable")) in lines[-1]
    assert (repo / ".writ" / "doubt-thresholds.json").exists() == (verdict == "pass")
    if verdict != "pass":
        assert "reason: false_act_bound" in lines


def test_calibrate_refuses_when_too_few_acts_bound_the_share(tmp_path, capsys):
    """No override slips, but Jev acts on so few accepted decisions that four
    overrides cannot bound the false-act share under the cap."""
    repo, rc, lines = _calibrate(capsys, tmp_path, _separable([_draws(0.85)] * 4), "--write")
    assert lines[0] == "unverifiable" and "reason: false_act_bound" in lines
    assert "slipped=0" in lines[-1]
    assert not (repo / ".writ" / "doubt-thresholds.json").exists()


def test_calibrate_counts_each_draw_of_an_accepted_decision(tmp_path, capsys):
    """An accepted decision above the threshold on one draw in three acts a third
    of the time live, so it counts as a third of an act."""
    rows = [_example("acc-%d" % i, "as_recommended", [0.9, 0.3, 0.3]) for i in range(30)]
    rows += [_example("ovr-%d" % i, "overridden", _draws(0.4)) for i in range(4)]
    _repo_, _rc, lines = _calibrate(capsys, tmp_path, rows)
    assert "acted=10.0/30" in lines[-1], lines


def test_calibrate_needs_every_draw(tmp_path, capsys):
    """Examples scored fewer than DOUBT_DRAWS times are not calibration examples."""
    rows = [dict(r, draws=r["draws"][:1]) for r in _separable()]
    _repo_, _rc, lines = _calibrate(capsys, tmp_path, rows)
    assert lines[0] == "unverifiable" and "reason: too_few_labels" in lines
    assert "scored=0" in lines[-1]


def test_calibrate_needs_enough_labels(tmp_path, capsys):
    _repo_, _rc, lines = _calibrate(capsys, tmp_path, _separable()[-10:])
    assert lines[0] == "unverifiable" and "reason: too_few_labels" in lines


def test_calibrate_needs_an_override(tmp_path, capsys):
    rows = [r for r in _separable() if r["outcome"] == "as_recommended"]
    _repo_, _rc, lines = _calibrate(capsys, tmp_path, rows)
    assert lines[0] == "unverifiable" and "reason: no_override" in lines


def test_calibrate_refuses_when_no_accepted_decision_clears_the_threshold(tmp_path, capsys):
    rows = _separable([_draws(0.95)] * 4)
    _repo_, _rc, lines = _calibrate(capsys, tmp_path, rows)
    assert lines[0] == "unverifiable" and "reason: unseparated" in lines


def test_calibrate_rejects_mixed_models(tmp_path, capsys):
    rows = _separable()
    rows[0]["model"] = "other"
    _repo_, _rc, lines = _calibrate(capsys, tmp_path, rows)
    assert lines[0] == "unverifiable" and "reason: mixed_models" in lines


def test_calibrate_ignores_scores_from_another_question(tmp_path, capsys):
    """A score the current question did not produce counts as unscored, so a
    reworded question never calibrates on its predecessor's scale."""
    rows = [dict(r, judgment="needs_person") for r in _separable()]
    _repo_, _rc, lines = _calibrate(capsys, tmp_path, rows)
    assert lines[0] == "unverifiable" and "reason: too_few_labels" in lines
    assert "scored=0" in lines[-1]


def test_calibrate_reads_labels_from_the_log(tmp_path, capsys):
    """A logged decision with a p and a label is a calibration example with one draw."""
    repo = _repo(tmp_path, "vercel-gateway")
    _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path))], env=ENABLED,
         transport=Fake(p=0.3))
    rid = _log_rows(repo)[-1]["id"]
    _run(capsys, repo, ["doubt-label", "--id", rid, "--outcome", "overridden"])
    examples = jev._doubt_examples(repo / ".writ" / "state" / "doubt-log.jsonl", [])
    assert [(e.id, e.outcome, e.draws) for e in examples] == [
        (rid, "overridden", [pytest.approx(0.3)])]


def test_calibrate_live_scores_each_example_until_it_has_every_draw(tmp_path, capsys):
    rows = [_example("new", "overridden", [], model=None),
            _example("partial", "as_recommended", [0.7, 0.8])]
    repo = _repo(tmp_path, "vercel-gateway")
    saved = tmp_path / "scored.jsonl"
    fake = Fake(p=0.6)
    _run(capsys, repo, ["doubt-calibrate", "--extra", str(_extra(tmp_path, rows)), "--live",
                        "--save", str(saved)], env=ENABLED, transport=fake)
    assert fake.calls == jev.DOUBT_DRAWS + (jev.DOUBT_DRAWS - 2)
    out = {r["id"]: r for r in map(json.loads, saved.read_text(encoding="utf-8").splitlines())}
    assert out["new"]["draws"] == _draws(0.6)
    assert out["partial"]["draws"] == [0.7, 0.8] + [0.6] * (jev.DOUBT_DRAWS - 2)
    assert {r["judgment"] for r in out.values()} == {jev.DOUBT_QUESTION}


def test_calibrate_live_refuses_replay(tmp_path, capsys):
    repo = _repo(tmp_path, "vercel-gateway")
    rc, _lines = _run(capsys, repo, ["doubt-calibrate", "--live"],
                      env=dict(ENABLED, WRIT_JEV_REPLAY=str(tmp_path)))
    assert rc == 2


def test_calibrate_live_without_provider_sends_nothing(tmp_path, capsys):
    repo = _repo(tmp_path)
    fake = Fake(p=0.1)
    rc, lines = _run(capsys, repo, ["doubt-calibrate", "--live"], transport=fake)
    assert lines[0] == "unverifiable" and fake.calls == 0


@pytest.mark.parametrize("successes,trials,expected", [
    (0, 10, 1 - 0.05 ** 0.1),  # closed form when nothing slipped
    (1, 10, 0.3942),
    (3, 3, 1.0),
])
def test_binomial_upper_bound(successes, trials, expected):
    assert jev._binomial_upper(successes, trials, 0.95) == pytest.approx(expected, abs=1e-3)


def test_request_names_the_state_paths_it_reads():
    state, questions = jev.doubt_request("Q?", [{"label": "A"}, {"label": "B"}], "A", ["e"])
    question = questions[jev.DOUBT_QUESTION]
    assert question["type"] == "noul"
    for path in ("`decision.question`", "`decision.recommended`", "`decision.options`",
                 "`decision.evidence`"):
        assert path in question["instructions"]
    assert state == {"decision": {"question": "Q?", "recommended": "A", "evidence": ["e"],
                                  "options": [{"label": "A", "description": ""},
                                              {"label": "B", "description": ""}]}}


# --------------------------------------------------------------------------
# 2026-11-06-ship-watch-and-merge Story 1: the merge rule re-derives readiness.
# A `site: merge` record names its PR, head, and snapshot; `doubt` re-runs
# `pr-ready.py check --json` on that snapshot, locally, before Jev is asked.
# --------------------------------------------------------------------------

HEAD = "3ddc8c8f0e1d2c3b4a5968778695a4b3c2d1e0f9"
OTHER_HEAD = "0123456789abcdef0123456789abcdef01234567"
SNAPSHOT = ".writ/state/pr-ready/pr-7.json"

PR_READY_STUB = """import os, sys, time
sleep = os.environ.get("PR_READY_STUB_SLEEP")
if sleep:
    time.sleep(float(sleep))
out = os.environ.get("PR_READY_STUB_OUT")
if out:
    with open(out, encoding="utf-8") as fh:
        sys.stdout.write(fh.read())
sys.exit(int(os.environ.get("PR_READY_STUB_EXIT", "0")))
"""


def _pr_ready_json(verdict: str = "pass", pr: Any = 7, head: str = HEAD,
                   blockers: Any = (), unknowns: Any = (), exit: int = 0) -> Dict[str, Any]:
    return {"verdict": verdict, "exit": exit, "pr": pr, "head": head,
            "blockers": [{"class": c, "detail": d} for c, d in blockers],
            "unknowns": [{"code": c, "detail": d} for c, d in unknowns],
            "ledger": {"verdict": "pass", "reasons": []}}


def _stub_pr_ready(tmp_path: Path, monkeypatch, payload: Any, exit: int = 0,
                   sleep: Optional[float] = None) -> Path:
    """Point jev.SCRIPTS_DIR at a stub pr-ready.py that prints `payload` and exits."""
    stub_dir = tmp_path / "stub-scripts"
    stub_dir.mkdir(exist_ok=True)
    (stub_dir / "pr-ready.py").write_text(PR_READY_STUB, encoding="utf-8")
    out = stub_dir / "stdout.txt"
    out.write_text(payload if isinstance(payload, str) else json.dumps(payload),
                   encoding="utf-8")
    monkeypatch.setenv("PR_READY_STUB_OUT", str(out))
    monkeypatch.setenv("PR_READY_STUB_EXIT", str(exit))
    if sleep is None:
        monkeypatch.delenv("PR_READY_STUB_SLEEP", raising=False)
    else:
        monkeypatch.setenv("PR_READY_STUB_SLEEP", str(sleep))
    monkeypatch.setattr(jev, "SCRIPTS_DIR", stub_dir)
    return stub_dir


def _merge_record(tmp_path: Path, **overrides: Any) -> Path:
    data: Dict[str, Any] = {
        "site": "merge",
        "question": "Merge PR #7 into main now?",
        "options": ["Merge now (Recommended)", "Leave it at merge-ready"],
        "recommended": "Merge now",
        "evidence": ["the person ran /ship --watch",
                     "pr-ready: pass (PR 7 head 3ddc8c8, ledger VERIFIED)"],
        "reversible": True,
        "pr": 7, "head_sha": HEAD, "snapshot": SNAPSHOT,
    }
    data.update(overrides)
    return _record(tmp_path, **data)


def test_merge_acts_when_pr_ready_passes_and_calibrated_jev_clears(tmp_path, capsys,
                                                                   monkeypatch):
    """AC-1.1 — pr-ready pass for the record's PR and head, calibrated act 0.6, p 0.8."""
    repo = _repo(tmp_path, "vercel-gateway")
    _calibrated(repo)
    _stub_pr_ready(tmp_path, monkeypatch, _pr_ready_json())
    fake = Fake(p=0.8)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_merge_record(tmp_path))],
                     env=ENABLED, transport=fake)
    assert rc == 0 and lines[0] == "pass"
    assert "reason: jev_clear" in lines
    assert fake.calls == 1
    row = _log_rows(repo)[-1]
    assert row["site"] == "merge" and row["verdict"] == "act"
    assert row["pr"] == 7 and row["head_sha"] == HEAD


@pytest.mark.parametrize("provider", [True, False])
def test_merge_without_a_calibrated_threshold_asks(tmp_path, capsys, monkeypatch, provider):
    """AC-1.2 — no calibrated threshold, or no provider: fallback_merge asks."""
    repo = _repo(tmp_path, "vercel-gateway" if provider else None)
    _stub_pr_ready(tmp_path, monkeypatch, _pr_ready_json())
    fake = Fake(p=0.91)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_merge_record(tmp_path))],
                     env=ENABLED if provider else {}, transport=fake)
    assert rc == 1 and lines[0] == "fail"
    assert "reason: fallback_merge" in lines
    row = _log_rows(repo)[-1]
    assert row["source"] == "fallback" and row["pr"] == 7 and row["head_sha"] == HEAD
    if provider:
        assert fake.calls == 1 and row["p"] == pytest.approx(0.91)
        assert "reason: doubt_uncalibrated" in lines
    else:
        assert fake.calls == 0 and row["p"] is None
        assert "reason: jev_no_config_line" in lines


@pytest.mark.parametrize("drop", ["pr", "head_sha", "snapshot"])
def test_merge_record_without_its_fields_asks(tmp_path, capsys, monkeypatch, drop):
    """AC-1.4 — a merge record missing pr, head_sha, or snapshot: no_verification_ledger."""
    repo = _repo(tmp_path, "vercel-gateway")
    _calibrated(repo)
    _stub_pr_ready(tmp_path, monkeypatch, _pr_ready_json())
    fake = Fake(p=0.99)
    rc, lines = _run(capsys, repo,
                     ["doubt", "--record", str(_merge_record(tmp_path, **{drop: _DROP}))],
                     env=ENABLED, transport=fake)
    assert rc == 1 and lines[0] == "fail"
    assert "reason: no_verification_ledger" in lines
    assert fake.calls == 0
    assert _log_rows(repo)[-1]["source"] == "rules"


@pytest.mark.parametrize("payload,exit,sleep,reason,info", [
    (_pr_ready_json(), 1, None, "merge_unverifiable", "pr_ready_exit_1"),
    ("", 2, None, "merge_unverifiable", "pr_ready_exit_2"),
    (_pr_ready_json(), 0, 3, "merge_unverifiable", "pr_ready_timeout"),
    ("pass\npr-ready: pass (PR 7 head 3ddc8c8, ledger VERIFIED)\n", 0, None,
     "merge_unverifiable", "pr_ready_unparseable"),
    ({"verdict": "pass", "pr": 7}, 0, None, "merge_unverifiable", "pr_ready_unparseable"),
    (_pr_ready_json(head=OTHER_HEAD), 0, None, "merge_head_mismatch", None),
    (_pr_ready_json(pr=8), 0, None, "merge_head_mismatch", None),
    (_pr_ready_json("fail", exit=6, blockers=[
        ("merge_gates", "not_verified head 3ddc8c8: patch_id_mismatch 3ddc8c8")]),
     6, None, "merge_not_verified", None),
    (_pr_ready_json("fail", exit=4, blockers=[
        ("unresolved_threads", "PRRT_1 a.py:3 by carol"),
        ("merge_gates", "not_verified head 3ddc8c8: no_rows PR 7")]),
     4, None, "merge_not_verified", None),
    (_pr_ready_json("fail", exit=4, blockers=[
        ("unresolved_threads", "PRRT_1 a.py:3 by carol")]),
     4, None, "merge_not_ready", "pr_ready_unresolved_threads"),
    (_pr_ready_json("unverifiable", unknowns=[("checks_pending", "ci/test")]),
     0, None, "merge_not_ready", "pr_ready_checks_pending"),
    (_pr_ready_json("fail", exit=6, head=OTHER_HEAD, blockers=[
        ("merge_gates", "not_verified head 0123456: no_rows PR 7")]),
     6, None, "merge_head_mismatch", None),
    (_pr_ready_json("fail", exit=6), 6, None, "merge_not_ready", "pr_ready_fail"),
])
def test_merge_rule_asks_without_calling_jev(tmp_path, capsys, monkeypatch, payload, exit,
                                              sleep, reason, info):
    """AC-1.4 — pr-ready exits 1 or 2, times out, prints non-JSON, names another PR or
    head, reports not_verified, another blocker, or only an unknown: the merge asks and
    Jev is never called."""
    repo = _repo(tmp_path, "vercel-gateway")
    _calibrated(repo)
    _stub_pr_ready(tmp_path, monkeypatch, payload, exit=exit, sleep=sleep)
    monkeypatch.setattr(jev, "MERGE_CHECK_TIMEOUT", 1)
    fake = Fake(p=0.99)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_merge_record(tmp_path))],
                     env=ENABLED, transport=fake)
    assert rc == 1 and lines[0] == "fail"
    assert lines[1] == "reason: %s" % reason
    if info is not None:
        assert "reason: %s" % info in lines
    assert fake.calls == 0
    row = _log_rows(repo)[-1]
    assert row["source"] == "rules" and row["reason"] == reason
    assert row["pr"] == 7 and row["head_sha"] == HEAD


def test_merge_rule_asks_when_pr_ready_is_missing(tmp_path, capsys, monkeypatch):
    """AC-1.4 — no pr-ready.py beside jev-judge.py: merge_unverifiable."""
    repo = _repo(tmp_path, "vercel-gateway")
    empty = tmp_path / "no-scripts"
    empty.mkdir()
    monkeypatch.setattr(jev, "SCRIPTS_DIR", empty)
    fake = Fake(p=0.99)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_merge_record(tmp_path))],
                     env=ENABLED, transport=fake)
    assert rc == 1
    assert "reason: merge_unverifiable" in lines and "reason: pr_ready_missing" in lines
    assert fake.calls == 0


def test_merge_rule_runs_before_the_generic_rules(tmp_path, capsys, monkeypatch):
    """AC-1.4 — a merge record without pr asks no_verification_ledger, even when the
    generic rules would also ask."""
    repo = _repo(tmp_path)
    _stub_pr_ready(tmp_path, monkeypatch, _pr_ready_json())
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(
        _merge_record(tmp_path, pr=_DROP, reversible=False))])
    assert rc == 1 and lines[1] == "reason: no_verification_ledger"


def test_merge_rule_compares_heads_without_case(tmp_path, capsys, monkeypatch):
    """AC-1.1 — an uppercase head_sha names the same head pr-ready printed."""
    repo = _repo(tmp_path, "vercel-gateway")
    _calibrated(repo)
    _stub_pr_ready(tmp_path, monkeypatch, _pr_ready_json())
    fake = Fake(p=0.8)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(
        _merge_record(tmp_path, head_sha=HEAD.upper()))], env=ENABLED, transport=fake)
    assert rc == 0 and "reason: jev_clear" in lines and fake.calls == 1


def test_merge_rule_asks_when_pr_ready_cannot_start(tmp_path, capsys, monkeypatch):
    """AC-1.4 — an OS error starting pr-ready: merge_unverifiable (pr_ready_not_run)."""
    repo = _repo(tmp_path)
    _stub_pr_ready(tmp_path, monkeypatch, _pr_ready_json())

    def refuse(*_args, **_kwargs):
        raise OSError("exec format error")

    monkeypatch.setattr(jev.subprocess, "run", refuse)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_merge_record(tmp_path))])
    assert rc == 1 and lines[1] == "reason: merge_unverifiable"
    assert "reason: pr_ready_not_run" in lines


def test_merge_rule_runs_pr_ready_on_the_record_snapshot(tmp_path, capsys, monkeypatch):
    """AC-1.4 — the stub sees `check --snapshot <repo>/<snapshot> --repo <repo> --json`."""
    repo = _repo(tmp_path)
    stub_dir = _stub_pr_ready(tmp_path, monkeypatch, _pr_ready_json())
    argv_file = stub_dir / "argv.json"
    (stub_dir / "pr-ready.py").write_text(
        "import json, os, sys\n"
        "open(%r, 'w').write(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd()}))\n"
        % str(argv_file) + PR_READY_STUB, encoding="utf-8")
    _run(capsys, repo, ["doubt", "--record", str(_merge_record(tmp_path))])
    seen = json.loads(argv_file.read_text(encoding="utf-8"))
    root = repo.resolve()
    assert seen["argv"] == ["check", "--snapshot", str(root / SNAPSHOT), "--repo", str(root),
                            "--json"]
    assert Path(seen["cwd"]).resolve() == root
    absolute = str(tmp_path / "elsewhere" / "pr-7.json")
    _run(capsys, repo, ["doubt", "--record", str(_merge_record(tmp_path, snapshot=absolute))])
    assert json.loads(argv_file.read_text(encoding="utf-8"))["argv"][2] == absolute


def test_merge_rule_resolves_a_relative_repo(tmp_path, capsys, monkeypatch):
    """AC-1.4 — `--repo sub` from another cwd: the child gets absolute paths."""
    repo = _repo(tmp_path)
    stub_dir = _stub_pr_ready(tmp_path, monkeypatch, _pr_ready_json())
    argv_file = stub_dir / "argv.json"
    (stub_dir / "pr-ready.py").write_text(
        "import json, sys\n"
        "open(%r, 'w').write(json.dumps(sys.argv[1:]))\n" % str(argv_file) + PR_READY_STUB,
        encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    code = jev.main(["doubt", "--repo", "repo", "--record", str(_merge_record(tmp_path))],
                    environ={}, transport=None, sleep=lambda s: None)
    capsys.readouterr()
    assert code == 1
    argv = json.loads(argv_file.read_text(encoding="utf-8"))
    assert argv[2] == str(repo.resolve() / SNAPSHOT) and argv[4] == str(repo.resolve())


@pytest.mark.parametrize("overrides", [
    {"pr": "7"}, {"pr": 0}, {"pr": True}, {"pr": 7.0},
    {"head_sha": "3ddc8c8"}, {"head_sha": HEAD + "0"}, {"head_sha": "z" * 40},
    {"snapshot": ""}, {"snapshot": 7},
])
def test_malformed_merge_fields_are_a_usage_error(tmp_path, capsys, monkeypatch, overrides):
    """AC-1.4 — a pr of the wrong type, or a head_sha that is not 40 hex: exit 2."""
    repo = _repo(tmp_path)
    _stub_pr_ready(tmp_path, monkeypatch, _pr_ready_json())
    rc, _lines = _run(capsys, repo,
                      ["doubt", "--record", str(_merge_record(tmp_path, **overrides))])
    assert rc == 2
    assert not (repo / ".writ" / "state" / "doubt-log.jsonl").exists()


def test_release_still_always_asks(tmp_path, capsys, monkeypatch):
    """AC-1.4 — release asks `outward` even with merge fields and a passing pr-ready."""
    repo = _repo(tmp_path, "vercel-gateway")
    _calibrated(repo)
    _stub_pr_ready(tmp_path, monkeypatch, _pr_ready_json())
    fake = Fake(p=0.99)
    rc, lines = _run(capsys, repo,
                     ["doubt", "--record", str(_merge_record(tmp_path, site="release"))],
                     env=ENABLED, transport=fake)
    assert rc == 1 and lines[0] == "fail" and lines[1] == "reason: outward"
    assert fake.calls == 0
    assert "pr" not in _log_rows(repo)[-1]


def test_non_merge_rows_do_not_carry_merge_fields(tmp_path, capsys):
    """AC-1.1 — only a merge row adds pr and head_sha to the log."""
    repo = _repo(tmp_path)
    _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path, pr=7, head_sha=HEAD))])
    row = _log_rows(repo)[-1]
    assert "pr" not in row and "head_sha" not in row


# Real scripts: verify-ledger.py records head A of PR 7 in a temp repo, and the
# real pr-ready.py judges a clean snapshot of a later head.

def _git(repo: Path, *args: str) -> str:
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                           "-c", "commit.gpgsign=false", *args],
                          cwd=str(repo), env=env, check=True, capture_output=True, text=True)
    return done.stdout.strip()


def _ledger_repo(tmp_path: Path, monkeypatch) -> Path:
    """main with one file; feat with a one-line change (head A) recorded for PR 7."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    repo = _repo(tmp_path, "vercel-gateway")
    _git(repo, "init", "-q")
    _git(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    (repo / "app.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
    _git(repo, "add", "app.txt")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "checkout", "-q", "-b", "feat")
    (repo / "app.txt").write_text("one\nTWO\nthree\n", encoding="utf-8")
    _git(repo, "commit", "-q", "-am", "change two")
    head_a = _git(repo, "rev-parse", "HEAD")
    done = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "verify-ledger.py"),
                           "record", "--pr", "7", "--head", head_a, "--base", "main",
                           "--evidence", "0", "true", "--repo", str(repo)],
                          capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stdout + done.stderr
    return repo


def _clean_snapshot(repo: Path, head: str) -> None:
    view = {"number": 7, "url": "https://github.com/o/r/pull/7", "state": "OPEN",
            "isDraft": False, "mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN",
            "reviewDecision": "APPROVED", "headRefOid": head, "baseRefName": "main",
            "statusCheckRollup": [{"__typename": "CheckRun", "name": "ci",
                                   "status": "COMPLETED", "conclusion": "SUCCESS"}]}
    threads = {"data": {"repository": {"pullRequest": {
        "number": 7, "headRefOid": head,
        "reviewThreads": {"totalCount": 0, "pageInfo": {"hasNextPage": False},
                          "nodes": []}}}}}
    path = repo / SNAPSHOT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": "pr-ready-snapshot/1", "view": view,
                                "threads": threads}), encoding="utf-8")


def test_real_scripts_new_head_is_not_verified(tmp_path, capsys, monkeypatch):
    """AC-1.3 — head B changes the diff: pr-ready reports not_verified, Jev is not called."""
    repo = _ledger_repo(tmp_path, monkeypatch)
    (repo / "app.txt").write_text("one\nTWO!\nthree\n", encoding="utf-8")
    _git(repo, "commit", "-q", "-am", "change two again")
    head_b = _git(repo, "rev-parse", "HEAD")
    _clean_snapshot(repo, head_b)
    fake = Fake(p=0.99)
    rc, lines = _run(capsys, repo,
                     ["doubt", "--record", str(_merge_record(tmp_path, head_sha=head_b))],
                     env=ENABLED, transport=fake)
    assert rc == 1 and lines[0] == "fail"
    assert lines[1] == "reason: merge_not_verified"
    assert fake.calls == 0


def test_real_scripts_rebased_head_reaches_jev(tmp_path, capsys, monkeypatch):
    """AC-1.3 — head A rebased onto a moved main keeps its patch-id: the merge rules
    pass and Jev is called once (uncalibrated, so the fallback still asks)."""
    repo = _ledger_repo(tmp_path, monkeypatch)
    _git(repo, "checkout", "-q", "main")
    (repo / "other.txt").write_text("unrelated\n", encoding="utf-8")
    _git(repo, "add", "other.txt")
    _git(repo, "commit", "-q", "-m", "move main")
    _git(repo, "checkout", "-q", "feat")
    _git(repo, "rebase", "-q", "main")
    head_a2 = _git(repo, "rev-parse", "HEAD")
    _clean_snapshot(repo, head_a2)
    fake = Fake(p=0.91)
    rc, lines = _run(capsys, repo,
                     ["doubt", "--record", str(_merge_record(tmp_path, head_sha=head_a2))],
                     env=ENABLED, transport=fake)
    assert fake.calls == 1
    assert not any(line.startswith("reason: merge_") for line in lines)
    assert rc == 1 and "reason: fallback_merge" in lines


# Text that stated "merge always asks" (AC-1.5).

def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _flat(rel: str) -> str:
    return " ".join(_read(rel).split())


def test_preamble_splits_the_release_and_merge_rows():
    """AC-1.5 — the Doubt Rule table has separate release and merge rows."""
    text = _read("commands/_preamble.md")
    assert "| `release` (tag, publish, deploy) | Always |" in text
    assert ("| `merge` | `pr-ready.py` does not pass for the record's PR and head; Jev is "
            "uncalibrated, or its confidence is not above the threshold |") in text
    assert "| `merge`, `release`" not in text


def test_recommendation_semantics_states_the_merge_rule():
    """AC-1.5 — the record table names pr, head_sha, snapshot; steps 1 and 4 changed."""
    text = _read(".writ/docs/recommendation-semantics.md")
    for field in ("pr", "head_sha", "snapshot"):
        assert "| `%s` |" % field in text
    flat = " ".join(text.split())
    assert ("**Rules, no network.** `release` always asks. `merge` asks unless the record "
            "names `pr`, `head_sha`, and `snapshot`, and `pr-ready.py check --json` on that "
            "snapshot, run locally, passes for that PR and head; its pass needs the "
            "verification ledger to read VERIFIED.") in flat
    assert ("`direction`, `design`, and `merge` ask; `choice`, `route`, `plan`, and "
            "`destructive` act.") in flat
    assert "`merge` and `release` always ask" not in flat


def test_system_instructions_and_readme_no_longer_say_merge_always_waits():
    """AC-1.5 — the base and README say when a merge may proceed."""
    system = _flat("system-instructions.md")
    assert ("Releasing, tagging, and publishing wait for a person's answer. A merge waits "
            "too unless `pr-ready.py` passes for the PR's exact head, which needs the "
            "verification ledger to read VERIFIED, and the doubt check passes.") in system
    assert "Merging, releasing" not in system
    readme = _flat("README.md")
    assert ("Release, tag, and publish always wait for you. A merge waits too unless "
            "`pr-ready.py` passes for the PR's exact head with the ledger VERIFIED and the "
            "doubt check passes.") in readme
    assert "Merge, release, tag, and publish always wait for you." not in readme


def test_eval_pins_the_merge_sentence_and_adr_records_the_amendment():
    """AC-1.5 — eval.sh pins `A merge waits too unless`; ADR-033 has the amendment."""
    assert 'require_literal "$system" "A merge waits too unless"' in _read("scripts/eval.sh")
    adr = _read(".writ/decision-records/adr-033-doubt-gated-autonomy.md")
    assert "### 2026-11-06 — Merge acts under the ledger (Phase 16)" in adr


def test_jev_judge_help_states_the_merge_rule():
    """AC-1.5 — --help says release always asks and merge re-runs pr-ready locally."""
    flat = " ".join((jev.__doc__ or "").split())
    assert ("Rules first, no network: release always asks; merge asks unless "
            "`pr-ready.py check --json`, run locally on the record's snapshot, passes for "
            "the record's pr and head_sha (its pass needs the ledger to read VERIFIED);"
            ) in flat
    assert "merge and release always ask" not in flat


def test_pr_ready_callers_cell_names_jev_judge():
    """AC-1.5 — the pr-ready.py row of agent-cli-contract.md lists its callers."""
    rows = [line for line in _read(".writ/docs/agent-cli-contract.md").splitlines()
            if line.startswith("| `pr-ready.py` |")]
    assert len(rows) == 1
    callers = rows[0].strip().strip("|").split("|")[3].strip()
    assert "scripts/jev-judge.py" in callers.split(", ")

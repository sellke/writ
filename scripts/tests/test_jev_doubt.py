#!/usr/bin/env python3
"""Tests for `jev-judge.py doubt`, `doubt-label`, and `doubt-calibrate` (ADR-033).

No test reaches the network: every judged call goes through an injected fake
transport, and the rule and fallback paths never build a request.
"""

from __future__ import annotations

import importlib.util
import json
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

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
        assert set(body["questions"]) == {"needs_person"}
        assert body["state"]["decision"]["question"]
        if self.status != 200:
            return jev.HttpResponse(self.status, {}, b"{}")
        answer = {"model": MODEL, "answers": {"needs_person": {"noul": self.p}}}
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
    assert row["ask"] is None and row["source"] == "fallback"


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


def _calibrated(repo: Path, ask: float = 0.4, model: str = MODEL,
                backend: str = "vercel-gateway") -> None:
    (repo / ".writ" / "doubt-thresholds.json").write_text(json.dumps({
        "calibrated": True, "backend": backend, "model": model, "ask": ask}),
        encoding="utf-8")


def test_calibrated_low_p_acts_on_a_direction_decision(tmp_path, capsys):
    repo = _repo(tmp_path, "vercel-gateway")
    _calibrated(repo)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path, site="direction"))],
                     env=ENABLED, transport=Fake(p=0.2))
    assert rc == 0 and lines[0] == "pass"
    assert "reason: jev_clear" in lines
    assert "p=0.20 ask=0.40" in lines[-1]


def test_calibrated_high_p_asks_on_a_choice(tmp_path, capsys):
    repo = _repo(tmp_path, "vercel-gateway")
    _calibrated(repo)
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path))],
                     env=ENABLED, transport=Fake(p=0.6))
    assert rc == 1 and lines[0] == "fail"
    assert "reason: jev_doubt" in lines
    assert _log_rows(repo)[-1]["source"] == "jev"


def test_threshold_for_another_model_is_not_applied(tmp_path, capsys):
    repo = _repo(tmp_path, "vercel-gateway")
    _calibrated(repo, model="some-other-model")
    rc, lines = _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path, site="direction"))],
                     env=ENABLED, transport=Fake(p=0.01))
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


def _ids_for(split: str, count: int, prefix: str) -> List[str]:
    out: List[str] = []
    n = 0
    while len(out) < count:
        candidate = "%s-%d" % (prefix, n)
        if jev._doubt_split(candidate) == split:
            out.append(candidate)
        n += 1
    return out


def _example(rid: str, outcome: str, p: Optional[float], model: str = MODEL) -> Dict[str, Any]:
    return {"id": rid, "question": "Q %s?" % rid, "options": ["A", "B"], "recommended": "A",
            "evidence": [], "outcome": outcome, "p": p, "model": model}


def _extra(tmp_path: Path, rows: List[Dict[str, Any]]) -> Path:
    path = tmp_path / "extra.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def _separable(dev_override_p: float = 0.6, test_override_p: float = 0.7) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for i, rid in enumerate(_ids_for("dev", 16, "acc-dev")):
        rows.append(_example(rid, "as_recommended", 0.1 + 0.01 * i))
    for i, rid in enumerate(_ids_for("test", 16, "acc-test")):
        rows.append(_example(rid, "as_recommended", 0.1 + 0.01 * i))
    rows += [_example(r, "overridden", dev_override_p) for r in _ids_for("dev", 2, "ovr-dev")]
    rows += [_example(r, "overridden", test_override_p) for r in _ids_for("test", 2, "ovr-test")]
    return rows


def test_calibrate_writes_a_threshold_that_holds_out(tmp_path, capsys):
    repo = _repo(tmp_path, "vercel-gateway")
    extra = _extra(tmp_path, _separable())
    rc, lines = _run(capsys, repo, ["doubt-calibrate", "--extra", str(extra), "--write"])
    assert rc == 0 and lines[0] == "pass", lines
    written = json.loads((repo / ".writ" / "doubt-thresholds.json").read_text(encoding="utf-8"))
    assert written["calibrated"] is True and written["ask"] == pytest.approx(0.6)
    assert written["backend"] == "vercel-gateway" and written["model"] == MODEL
    assert written["splits"]["test"]["false_acts"] == 0


def test_calibrate_refuses_a_held_out_false_act(tmp_path, capsys):
    repo = _repo(tmp_path)
    extra = _extra(tmp_path, _separable(dev_override_p=0.6, test_override_p=0.15))
    rc, lines = _run(capsys, repo, ["doubt-calibrate", "--extra", str(extra), "--write"])
    assert rc == 0 and lines[0] == "unverifiable"
    assert "reason: holdout_false_act" in lines
    assert not (repo / ".writ" / "doubt-thresholds.json").exists()


def test_calibrate_needs_enough_labels(tmp_path, capsys):
    repo = _repo(tmp_path)
    extra = _extra(tmp_path, _separable()[:10])
    rc, lines = _run(capsys, repo, ["doubt-calibrate", "--extra", str(extra)])
    assert lines[0] == "unverifiable" and "reason: too_few_labels" in lines


def test_calibrate_needs_overrides_in_both_splits(tmp_path, capsys):
    repo = _repo(tmp_path)
    rows = [r for r in _separable() if not r["id"].startswith("ovr-test")]
    rc, lines = _run(capsys, repo, ["doubt-calibrate", "--extra", str(_extra(tmp_path, rows))])
    assert lines[0] == "unverifiable" and "reason: no_holdout" in lines


def test_calibrate_rejects_mixed_models(tmp_path, capsys):
    repo = _repo(tmp_path)
    rows = _separable()
    rows[0]["model"] = "other"
    rc, lines = _run(capsys, repo, ["doubt-calibrate", "--extra", str(_extra(tmp_path, rows))])
    assert lines[0] == "unverifiable" and "reason: mixed_models" in lines


def test_calibrate_reads_labels_from_the_log(tmp_path, capsys):
    """A logged decision with a p and a label is a calibration example."""
    repo = _repo(tmp_path, "vercel-gateway")
    _run(capsys, repo, ["doubt", "--record", str(_record(tmp_path))], env=ENABLED,
         transport=Fake(p=0.3))
    rid = _log_rows(repo)[-1]["id"]
    _run(capsys, repo, ["doubt-label", "--id", rid, "--outcome", "overridden"])
    examples = jev._doubt_examples(repo / ".writ" / "state" / "doubt-log.jsonl", [])
    assert [(e.id, e.outcome, e.p) for e in examples] == [(rid, "overridden", pytest.approx(0.3))]


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


def test_request_names_the_state_paths_it_reads():
    state, questions = jev.doubt_request("Q?", [{"label": "A"}, {"label": "B"}], "A", ["e"])
    question = questions["needs_person"]
    assert question["type"] == "noul"
    for path in ("`decision.question`", "`decision.recommended`", "`decision.options`"):
        assert path in question["instructions"]
    assert state == {"decision": {"question": "Q?", "recommended": "A", "evidence": ["e"],
                                  "options": [{"label": "A", "description": ""},
                                              {"label": "B", "description": ""}]}}

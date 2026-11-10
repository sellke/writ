#!/usr/bin/env python3
"""Tests for plugins/writ/skills/writ-jev/jev.py, the optional second reader.

No test reaches the network. In-process tests replace every socket entry point
with one that raises, and pass a fake transport or WRIT_JEV_REPLAY. Subprocess
tests either set WRIT_JEV_REPLAY (which always wins over a live call) or run
commands that never send (status, setup, usage errors).

The replay tests read scripts/tests/fixtures/jev: labelled synthetic specs and
the live responses recorded for them. Changing a question's wording in jev.py
changes the request hashes and turns those tests into `off (replay_miss)`:
re-record and refit with fixtures/jev/calibrate.py.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "plugins" / "writ" / "skills" / "writ-jev"
SCRIPT = SKILL / "jev.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "jev"
REPLAY = FIXTURES / "replay"

KEY_VARS = ("TYPESAFE_API_KEY", "AI_GATEWAY_API_KEY", "VERCEL_OIDC_TOKEN", "WRIT_JEV_REPLAY")
FAKE_KEY = "sk-jev-FAKE-3b9f1c7e0d4a2265-DO-NOT-PRINT"
FLAG_LINE = re.compile(r"^(check )?(A\d+(?:\+A\d+)?|contract) (\w+) (\d\.\d\d|n/a) — (.+)$")
SUMMARY = re.compile(r"^jev: (\d+) flags?, (\d+) checks?, (\d+) (criteri(?:on|a)|rows?), "
                     r"backend=([\w-]+)")

SPEC = """# Export invoices

> **Status:** Draft

## Problem

Finance leads retype invoice rows
every month-end.

## Outcome

A finance lead downloads one file for the month.

**Measure:** Export tickets fall from 14 a month
to under 3 within two months.

## Scope

**In:**

- An export button on the invoices list.

**Out:**

- PDF export.
- Scheduled exports,
  including emailed ones.

## Acceptance criteria

- **A1.** When a finance lead clicks "Export CSV", the browser downloads
  `invoices-YYYY-MM.csv`
  for the selected month.
- **A2.** When the month has no invoices, the page shows "No invoices in this month".
- Not a criterion: a plain bullet.
- **A3.** A user without the Finance role gets "403 Forbidden".

## Notes for the builder

```
## Proof
- **A9.** This heading and bullet sit inside a code fence.
```

## Proof

> Verified at `4c1e9ab` on 2026-11-03 by a verifier that did not write the change.

- **A1. Proved.** Clicked "Export CSV" for March. The browser downloaded
  `invoices-2026-03.csv`. Output in `proof/a1-run.txt`.
- **A2. Not proved.** Selected an empty month. The page showed a blank table.
- **A3. Needs a person.** Someone should try it
  with a Sales login.

### Try it yourself

1. Sign in and click "Export CSV".

### Not covered

- Import into the accounting tool.
"""


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("writ_jev", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["writ_jev"] = module
    spec.loader.exec_module(module)
    return module


jev = _load()


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("a test tried to open a network connection")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


def _repo(tmp_path: Path, provider: Optional[str] = "vercel-gateway",
          config: bool = True) -> Path:
    """A temp project. provider=None writes a config with no Judgment Provider line."""
    repo = tmp_path / "repo"
    (repo / ".writ").mkdir(parents=True)
    if config:
        line = "" if provider is None else "- **Judgment Provider:** %s\n" % provider
        (repo / ".writ" / "config.md").write_text(
            "# Writ Project Config\n\n## Conventions\n\n- **Default Branch:** main\n%s"
            "\n## Paths\n\n- **Writ Specs:** .writ/specs/\n" % line, encoding="utf-8")
    return repo


def _spec_file(repo: Path, text: str = SPEC, name: str = "export") -> Path:
    folder = repo / ".writ" / "specs" / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "spec.md").write_text(text, encoding="utf-8")
    return folder / "spec.md"


def _main(capsys: pytest.CaptureFixture, argv: List[str], environ: Dict[str, str],
          transport: Any = None, sleeps: Optional[List[float]] = None
          ) -> Tuple[int, str, str]:
    code = jev.main(argv, environ, transport,
                    (sleeps.append if sleeps is not None else lambda _s: None))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _subprocess(args: List[str], extra: Optional[Dict[str, str]] = None,
                cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    env = {k: v for k, v in os.environ.items() if k not in KEY_VARS}
    env.update(extra or {})
    proc = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, env=env, cwd=str(cwd) if cwd else None)
    return proc.returncode, proc.stdout, proc.stderr


def _lines(out: str) -> List[str]:
    return out.strip().splitlines()


def _marks(out: str, soft: bool = False) -> List[Tuple[str, str]]:
    """(id, code) for each flag line, or for each `check` line when soft."""
    found = []
    for line in _lines(out)[1:-1]:
        match = FLAG_LINE.match(line)
        assert match, "unexpected line: %r" % line
        if bool(match.group(1)) == soft:
            found.append((match.group(2), match.group(3)))
    return found


def _assert_off(code: int, out: str, reason: str) -> None:
    lines = _lines(out)
    assert code == 0
    assert lines[0] == "off"
    assert lines[1] == "reason: %s" % reason
    assert lines[-1].startswith("jev: off (%s) backend=" % reason)
    assert len(lines) == 3


def _respond(req: Any, probabilities: Dict[str, float], default: float = 0.02,
             model: str = "typesafe-ai/jev") -> bytes:
    answers = {qid: {"type": "noul", "noul": probabilities.get(qid, default)}
               for qid in req.questions}
    return json.dumps({"model": model, "answers": answers,
                       "usage": {"input_tokens": 1234, "output_tokens": 12}}).encode()


def _record(directory: Path, req: Any, backend: str, body: bytes) -> None:
    """Write `body` where the replay transport looks for this request."""
    payload = jev.canonical_body(jev.build_body(req.state, req.questions,
                                                jev.BACKENDS[backend]))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / (jev.request_hash(payload) + ".json")).write_bytes(body)


def _fake_transport(status: int = 200, body: bytes = b"{}", headers: Optional[Dict] = None,
                    calls: Optional[List] = None) -> Any:
    def send(url: str, sent_headers: Dict[str, str], payload: bytes) -> Any:
        if calls is not None:
            calls.append((url, dict(sent_headers), payload))
        return jev.HttpResponse(status, headers or {}, body)
    return send


# --------------------------------------------------------------------------
# Parsing the spec format
# --------------------------------------------------------------------------


def test_parse_reads_every_contract_section() -> None:
    spec = jev.parse_spec(SPEC)
    assert spec.problem == "Finance leads retype invoice rows every month-end."
    assert spec.outcome == "A finance lead downloads one file for the month."
    assert spec.measure == ("Export tickets fall from 14 a month to under 3 within two "
                            "months.")
    assert spec.scope_in == ["An export button on the invoices list."]
    assert spec.scope_out == ["PDF export.", "Scheduled exports, including emailed ones."]


def test_parse_joins_criterion_continuation_lines_and_skips_other_bullets() -> None:
    spec = jev.parse_spec(SPEC)
    assert list(spec.criteria) == ["A1", "A2", "A3"]
    assert spec.criteria["A1"] == ('When a finance lead clicks "Export CSV", the browser '
                                   "downloads `invoices-YYYY-MM.csv` for the selected month.")
    assert spec.criteria["A2"].endswith('"No invoices in this month".')
    assert "plain bullet" not in " ".join(spec.criteria.values())


def test_parse_proof_rows_stop_at_the_next_bullet_or_heading() -> None:
    rows = jev.parse_spec(SPEC).rows
    assert {rid: verdict for rid, (verdict, _) in rows.items()} == {
        "A1": "proved", "A2": "not proved", "A3": "needs a person"}
    assert rows["A1"][1].endswith("Output in `proof/a1-run.txt`.")
    assert rows["A3"][1] == "Someone should try it with a Sales login."
    assert "Sign in" not in rows["A3"][1] and "Verified at" not in rows["A1"][1]


def test_parse_ignores_headings_and_bullets_inside_a_code_fence() -> None:
    spec = jev.parse_spec(SPEC)
    assert "A9" not in spec.criteria and "A9" not in spec.rows


def test_parse_tolerates_missing_sections() -> None:
    spec = jev.parse_spec("# Title\n\n## Acceptance criteria\n\n- **A1.** One thing.\n")
    assert spec.criteria == {"A1": "One thing."}
    assert (spec.problem, spec.outcome, spec.measure) == ("", "", "")
    assert spec.scope_in == [] and spec.scope_out == [] and spec.rows == {}
    empty = jev.parse_spec("")
    assert empty.criteria == {} and empty.rows == {}


def test_parse_outcome_without_a_measure_line_has_an_empty_measure() -> None:
    spec = jev.parse_spec("## Outcome\n\nPeople are faster.\n\n## Acceptance criteria\n")
    assert spec.outcome == "People are faster." and spec.measure == ""


def test_parse_reads_the_shipped_spec_template() -> None:
    template = REPO_ROOT / "plugins" / "writ" / "skills" / "writ-spec" / "spec-template.md"
    spec = jev.parse_spec(template.read_text(encoding="utf-8"))
    assert list(spec.criteria) == ["A1", "A2"]
    assert {rid: v for rid, (v, _) in spec.rows.items()} == {
        "A1": "proved", "A2": "not proved", "A3": "needs a person"}
    assert spec.measure and spec.problem and len(spec.scope_in) == len(spec.scope_out) == 1


# --------------------------------------------------------------------------
# Double opt-in, status, setup
# --------------------------------------------------------------------------


@pytest.mark.parametrize("provider, config, env, ok, reason", [
    (None, False, {"AI_GATEWAY_API_KEY": FAKE_KEY}, False, "no_config_line"),
    (None, True, {"AI_GATEWAY_API_KEY": FAKE_KEY}, False, "no_config_line"),
    ("none", True, {"AI_GATEWAY_API_KEY": FAKE_KEY}, False, "provider_disabled"),
    ("someone-else", True, {"AI_GATEWAY_API_KEY": FAKE_KEY}, False, "provider_disabled"),
    ("vercel-gateway", True, {}, False, "no_api_key"),
    ("vercel-gateway", True, {"AI_GATEWAY_API_KEY": "   "}, False, "no_api_key"),
    ("vercel-gateway", True, {"TYPESAFE_API_KEY": FAKE_KEY}, False, "no_api_key"),
    ("typesafe", True, {"AI_GATEWAY_API_KEY": FAKE_KEY}, False, "no_api_key"),
    ("vercel-gateway", True, {"AI_GATEWAY_API_KEY": FAKE_KEY}, True, "enabled"),
    ("vercel-gateway", True, {"VERCEL_OIDC_TOKEN": FAKE_KEY}, True, "enabled"),
    ("typesafe", True, {"TYPESAFE_API_KEY": FAKE_KEY}, True, "enabled"),
    ("VERCEL-GATEWAY", True, {"AI_GATEWAY_API_KEY": FAKE_KEY}, True, "enabled"),
])
def test_double_opt_in(tmp_path: Path, capsys: pytest.CaptureFixture, provider: Optional[str],
                       config: bool, env: Dict[str, str], ok: bool, reason: str) -> None:
    repo = _repo(tmp_path, provider, config)
    res = jev.resolve(repo, env)
    assert (res.ok, res.reason) == (ok, reason)
    code, out, err = _main(capsys, ["status", "--repo", str(repo)], env)
    lines = _lines(out)
    assert code == 0 and lines[0] == ("ready" if ok else "off")
    assert lines[1] == "reason: %s" % reason and lines[-1].startswith("jev: ")
    assert FAKE_KEY not in out + err and "someone-else" not in out + err


def test_status_names_the_backend_and_the_key_variable_never_the_value(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)
    _, out, _ = _main(capsys, ["status", "--repo", str(repo)], {"AI_GATEWAY_API_KEY": FAKE_KEY})
    assert _lines(out)[-1] == ("jev: ready backend=vercel-gateway model=typesafe-ai/jev "
                               "key_env=AI_GATEWAY_API_KEY")
    _, out, _ = _main(capsys, ["status", "--repo", str(repo)], {})
    assert _lines(out)[-1] == "jev: off (no_api_key) backend=vercel-gateway export=AI_GATEWAY_API_KEY"


def test_replay_needs_the_config_line_but_no_key(tmp_path: Path) -> None:
    res = jev.resolve(_repo(tmp_path), {"WRIT_JEV_REPLAY": "/nowhere"})
    assert (res.ok, res.reason, res.key_var) == (True, "replay", None)
    assert not jev.resolve(_repo(tmp_path / "b", None), {"WRIT_JEV_REPLAY": "/nowhere"}).ok


def test_setup_creates_the_config_with_a_conventions_heading(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = tmp_path / "fresh"
    repo.mkdir()
    code, out, _ = _main(capsys, ["setup", "typesafe", "--repo", str(repo)],
                         {"TYPESAFE_API_KEY": FAKE_KEY})
    text = (repo / ".writ" / "config.md").read_text(encoding="utf-8")
    assert code == 0 and _lines(out)[0] == "configured"
    assert text == "## Conventions\n\n- **Judgment Provider:** typesafe\n"
    assert "export=TYPESAFE_API_KEY" in out and FAKE_KEY not in out + text


def test_setup_replaces_the_line_in_place_and_keeps_every_other_line(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path, "typesafe")
    config = repo / ".writ" / "config.md"
    before = config.read_text(encoding="utf-8")
    assert _main(capsys, ["setup", "none", "--repo", str(repo)], {})[0] == 0
    after = config.read_text(encoding="utf-8")
    assert after == before.replace("typesafe", "none")
    assert jev.resolve(repo, {"TYPESAFE_API_KEY": FAKE_KEY}).reason == "provider_disabled"


def test_setup_adds_the_line_after_the_last_conventions_bullet(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path, None)
    _main(capsys, ["setup", "vercel-gateway", "--repo", str(repo)], {})
    lines = (repo / ".writ" / "config.md").read_text(encoding="utf-8").splitlines()
    at = lines.index("- **Judgment Provider:** vercel-gateway")
    assert lines[at - 1] == "- **Default Branch:** main" and lines[at + 2] == "## Paths"
    assert jev.resolve(repo, {"AI_GATEWAY_API_KEY": FAKE_KEY}).ok


def test_set_provider_line_edge_shapes() -> None:
    assert jev.set_provider_line("# Config", "none") == (
        "# Config\n\n## Conventions\n\n- **Judgment Provider:** none\n")
    twice = "- **Judgment Provider:** a\nx\n- **Judgment Provider:** b\n"
    assert jev.set_provider_line(twice, "typesafe") == "- **Judgment Provider:** typesafe\nx\n"
    assert jev.set_provider_line("## Conventions\n\n## Paths\n", "none") == (
        "## Conventions\n\n- **Judgment Provider:** none\n\n## Paths\n")


# --------------------------------------------------------------------------
# `off` paths: always exit 0, one reason, never the key
# --------------------------------------------------------------------------


@pytest.mark.parametrize("kind", ["contract", "proof"])
@pytest.mark.parametrize("provider, env, reason", [
    (None, {"AI_GATEWAY_API_KEY": FAKE_KEY}, "no_config_line"),
    ("none", {"AI_GATEWAY_API_KEY": FAKE_KEY}, "provider_disabled"),
    ("vercel-gateway", {}, "no_api_key"),
])
def test_off_when_not_configured(tmp_path: Path, capsys: pytest.CaptureFixture, kind: str,
                                 provider: Optional[str], env: Dict[str, str],
                                 reason: str) -> None:
    repo = _repo(tmp_path, provider)
    calls: List = []
    code, out, err = _main(capsys, [kind, str(_spec_file(repo))], env,
                           _fake_transport(calls=calls))
    _assert_off(code, out, reason)
    assert calls == [] and FAKE_KEY not in out + err


@pytest.mark.parametrize("kind", ["contract", "proof"])
def test_another_projects_opt_in_never_sends_this_projects_spec(
        tmp_path: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch,
        kind: str) -> None:
    """Found on the first real run: a spec in a project with no config was sent
    because the current directory was a project that had opted in."""
    opted_in = _repo(tmp_path / "a")
    not_opted_in = _repo(tmp_path / "b", config=False)
    monkeypatch.chdir(opted_in)
    calls: List = []
    code, out, _ = _main(capsys, [kind, str(_spec_file(not_opted_in))],
                         {"AI_GATEWAY_API_KEY": FAKE_KEY}, _fake_transport(calls=calls))
    _assert_off(code, out, "no_config_line")
    assert calls == []


def test_a_spec_outside_any_project_is_off(tmp_path: Path, capsys: pytest.CaptureFixture,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_repo(tmp_path / "a"))
    loose = tmp_path / "loose"
    loose.mkdir()
    (loose / "spec.md").write_text(SPEC, encoding="utf-8")
    calls: List = []
    code, out, _ = _main(capsys, ["contract", str(loose / "spec.md")],
                         {"AI_GATEWAY_API_KEY": FAKE_KEY}, _fake_transport(calls=calls))
    _assert_off(code, out, "no_config_line")
    assert calls == []


@pytest.mark.parametrize("text, kind, reason", [
    (None, "contract", "spec_unreadable"),
    ("# Title\n\n## Problem\n\nNo criteria here.\n", "contract", "no_criteria"),
    ("# Title\n\n## Acceptance criteria\n\n- **A1.** One.\n", "proof", "no_proof_rows"),
    ("## Acceptance criteria\n\n- **A1.** One.\n\n## Proof\n\n<Written by writ-verify.>\n",
     "proof", "no_proof_rows"),
])
def test_off_when_the_file_cannot_be_parsed(tmp_path: Path, capsys: pytest.CaptureFixture,
                                            text: Optional[str], kind: str, reason: str) -> None:
    repo = _repo(tmp_path)
    path = _spec_file(repo, text) if text is not None else repo / "missing" / "spec.md"
    calls: List = []
    code, out, _ = _main(capsys, [kind, str(path), "--repo", str(repo)],
                         {"AI_GATEWAY_API_KEY": FAKE_KEY}, _fake_transport(calls=calls))
    _assert_off(code, out, reason)
    assert calls == []


@pytest.mark.parametrize("status, body, reason", [
    (500, b"upstream exploded", "transport_error"),
    (401, b'{"error": {"message": "bad key"}}', "auth_error"),
    (403, b"forbidden", "auth_error"),
    (422, b'{"message": "malformed question"}', "request_invalid"),
    (200, b"not json", "malformed_response"),
    (200, b"[1, 2]", "malformed_response"),
    (200, b'{"model": "typesafe-ai/jev", "answers": {}}', "malformed_response"),
])
def test_off_when_the_request_fails(tmp_path: Path, capsys: pytest.CaptureFixture,
                                    status: int, body: bytes, reason: str) -> None:
    repo = _repo(tmp_path)
    code, out, err = _main(capsys, ["contract", str(_spec_file(repo))],
                           {"AI_GATEWAY_API_KEY": FAKE_KEY}, _fake_transport(status, body))
    _assert_off(code, out, reason)
    assert FAKE_KEY not in out + err


def test_off_when_an_answer_is_missing_or_out_of_range(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)
    path = _spec_file(repo)
    req = jev.contract_request(jev.parse_spec(SPEC))
    for bad in (1.5, "0.9", True, None):
        body = json.loads(_respond(req, {}))
        body["answers"]["A1_unclear"]["noul"] = bad
        code, out, _ = _main(capsys, ["contract", str(path)], {"AI_GATEWAY_API_KEY": FAKE_KEY},
                             _fake_transport(200, json.dumps(body).encode()))
        _assert_off(code, out, "malformed_response")


def test_off_after_three_rate_limited_attempts_and_it_backs_off(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)
    calls: List = []
    sleeps: List[float] = []
    code, out, _ = _main(capsys, ["contract", str(_spec_file(repo))],
                         {"AI_GATEWAY_API_KEY": FAKE_KEY},
                         _fake_transport(429, b"slow down", {"retry-after": "7"}, calls), sleeps)
    _assert_off(code, out, "rate_limited")
    assert len(calls) == 3 and sleeps == [7.0, 7.0]


def test_a_retry_after_overload_can_succeed_and_a_huge_retry_after_is_capped(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)
    req = jev.contract_request(jev.parse_spec(SPEC))
    replies = [jev.HttpResponse(529, {"retry-after": "99999"}, b""),
               jev.HttpResponse(200, {}, _respond(req, {}))]
    sleeps: List[float] = []
    code, out, _ = _main(capsys, ["contract", str(_spec_file(repo))],
                         {"AI_GATEWAY_API_KEY": FAKE_KEY},
                         lambda *_a: replies.pop(0), sleeps)
    assert code == 0 and _lines(out)[0] == "pass"
    assert sleeps == [jev.RETRY_AFTER_CAP_SECONDS]


def test_off_when_the_connection_fails(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)

    def broken(*_args: Any) -> Any:
        raise jev.TransportFailure("URLError")

    code, out, err = _main(capsys, ["contract", str(_spec_file(repo))],
                           {"AI_GATEWAY_API_KEY": FAKE_KEY}, broken)
    _assert_off(code, out, "transport_error")
    assert FAKE_KEY not in out + err


def test_off_when_the_spec_is_too_large_and_nothing_is_sent(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)
    huge = SPEC.replace("gets \"403 Forbidden\".", "gets this. " + "word " * 40000)
    calls: List = []
    code, out, _ = _main(capsys, ["contract", str(_spec_file(repo, huge))],
                         {"AI_GATEWAY_API_KEY": FAKE_KEY}, _fake_transport(calls=calls))
    _assert_off(code, out, "state_too_large")
    assert calls == []


def test_off_on_a_replay_miss_and_the_live_transport_is_never_used(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)
    calls: List = []
    env = {"AI_GATEWAY_API_KEY": FAKE_KEY, "WRIT_JEV_REPLAY": str(tmp_path / "empty")}
    code, out, _ = _main(capsys, ["contract", str(_spec_file(repo))], env,
                         _fake_transport(calls=calls))
    _assert_off(code, out, "replay_miss")
    assert calls == []


def test_off_when_a_pinned_backend_is_answered_by_another_model(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path, "typesafe")
    req = jev.contract_request(jev.parse_spec(SPEC))
    env = {"TYPESAFE_API_KEY": FAKE_KEY}
    code, out, _ = _main(capsys, ["contract", str(_spec_file(repo))], env,
                         _fake_transport(200, _respond(req, {}, model="jev-9.9.9")))
    _assert_off(code, out, "model_mismatch")
    code, out, _ = _main(capsys, ["contract", str(_spec_file(repo))], env,
                         _fake_transport(200, _respond(req, {}, model="jev-1.14.0")))
    assert _lines(out)[0] == "pass"
    assert _lines(out)[-1].endswith("backend=typesafe thresholds=fitted_on_other_model")


def test_off_as_json(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)
    code, out, _ = _main(capsys, ["proof", str(_spec_file(repo)), "--json"], {})
    doc = json.loads(out)
    assert code == 0
    assert doc == {"verdict": "off", "kind": "proof", "backend": "vercel-gateway",
                   "reasons": ["no_api_key"],
                   "summary": "jev: off (no_api_key) backend=vercel-gateway "
                              "export=AI_GATEWAY_API_KEY"}


# --------------------------------------------------------------------------
# The key never appears
# --------------------------------------------------------------------------


@pytest.mark.parametrize("status, body", [
    (400, ("echo: Bearer %s" % FAKE_KEY).encode()),
    (500, ("trace %s\nflag\nA1 unclear 0.99" % FAKE_KEY).encode()),
    (200, json.dumps({"model": FAKE_KEY, "answers": {}}).encode()),
])
def test_key_is_redacted_when_the_server_echoes_it(
        tmp_path: Path, capsys: pytest.CaptureFixture, status: int, body: bytes) -> None:
    repo = _repo(tmp_path)
    for extra in ([], ["--json"]):
        code, out, err = _main(capsys, ["contract", str(_spec_file(repo))] + extra,
                               {"AI_GATEWAY_API_KEY": FAKE_KEY}, _fake_transport(status, body))
        assert code == 0 and FAKE_KEY not in out + err
        # A newline in a server body must not become a verdict or a second log line.
        assert _lines(out)[0] == "off" or json.loads(out)["verdict"] == "off"
        assert "\nflag" not in out and len(err.splitlines()) <= 1


def test_a_model_name_carrying_the_key_is_dropped_from_a_good_response(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)
    req = jev.contract_request(jev.parse_spec(SPEC))
    code, out, err = _main(capsys, ["contract", str(_spec_file(repo)), "--json"],
                           {"AI_GATEWAY_API_KEY": FAKE_KEY},
                           _fake_transport(200, _respond(req, {}, model="m-" + FAKE_KEY)))
    assert code == 0 and FAKE_KEY not in out + err
    assert json.loads(out)["model"] is None


def test_the_key_travels_only_in_the_authorization_header(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)
    req = jev.contract_request(jev.parse_spec(SPEC))
    calls: List = []
    _main(capsys, ["contract", str(_spec_file(repo))], {"AI_GATEWAY_API_KEY": " %s \n" % FAKE_KEY},
          _fake_transport(200, _respond(req, {}), calls=calls))
    (url, headers, payload), = calls
    assert url == "https://ai-gateway.vercel.sh/typesafe/v1/systemone"
    assert headers["Authorization"] == "Bearer " + FAKE_KEY
    assert FAKE_KEY.encode() not in payload
    body = json.loads(payload)
    assert body["model"] == "typesafe-ai/jev"
    assert body["providerOptions"] == {"gateway": {"only": ["typesafe-ai"]}}


def test_the_direct_backend_pins_a_model_and_sends_no_gateway_options() -> None:
    body = jev.build_body({}, {}, jev.BACKENDS["typesafe"])
    assert body == {"model": "jev-1.14.0", "state": {}, "questions": {}}


def test_a_key_typed_as_an_argument_is_not_echoed(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    for args in (["setup", FAKE_KEY], ["setup", "typesafe", "--key", FAKE_KEY],
                 ["status", FAKE_KEY], [FAKE_KEY]):
        code, out, err = _subprocess(args + ["--repo", str(repo)])
        assert code == 2 and FAKE_KEY not in out + err
    assert FAKE_KEY not in (repo / ".writ" / "config.md").read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Usage errors exit 2
# --------------------------------------------------------------------------


@pytest.mark.parametrize("args", [
    [], ["frobnicate"], ["contract"], ["proof"], ["setup"], ["setup", "openai"],
    ["contract", "a.md", "b.md"], ["status", "--repo"],
])
def test_usage_errors_exit_2(args: List[str]) -> None:
    code, out, err = _subprocess(args)
    assert code == 2 and out == "" and "usage:" in err


def test_a_repo_that_is_not_a_directory_exits_2(tmp_path: Path) -> None:
    code, _, err = _subprocess(["status", "--repo", str(tmp_path / "nope")])
    assert code == 2 and "not a directory" in err


def test_the_repo_is_found_from_the_spec_path(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    path = _spec_file(repo)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    code, out, _ = _subprocess(["contract", str(path)], cwd=elsewhere)
    assert code == 0 and _lines(out)[1] == "reason: no_api_key"
    code, out, _ = _subprocess(["contract", str(path), "--repo", str(elsewhere)], cwd=elsewhere)
    assert code == 0 and _lines(out)[1] == "reason: no_config_line"


# --------------------------------------------------------------------------
# Evidence files and the secret-pattern skip
# --------------------------------------------------------------------------


@pytest.mark.parametrize("path, secret", [
    ("proof/.env", True), ("proof/.env.staging", True), ("proof/tls.pem", True),
    ("proof/deploy.KEY", True), ("proof/my-secrets.txt", True),
    ("proof/api-Credentials.json", True), ("proof/secret/run.txt", True),
    ("proof/a1-run.txt", False), ("proof/environment.txt", False),
    ("proof/keys-pressed.txt", False), ("proof/a3-pytest.txt", False),
])
def test_secret_patterns(path: str, secret: bool) -> None:
    assert jev.is_secret_path(path) is secret


def test_evidence_skips_secret_binary_missing_and_outside_files(tmp_path: Path) -> None:
    proof = tmp_path / "proof"
    proof.mkdir()
    marker = "MARKER-NOT-A-REAL-SECRET-91f3"
    (proof / "run.txt").write_text("3 passed in 0.2s\n", encoding="utf-8")
    (proof / ".env.staging").write_text("TOKEN=%s\n" % marker, encoding="utf-8")
    (proof / "tls.key").write_text(marker, encoding="utf-8")
    (proof / "api-credentials.txt").write_text(marker, encoding="utf-8")
    (proof / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
    (proof / "latin.txt").write_bytes(b"caf\xe9 \xff\xfe")
    (proof / "empty.txt").write_text("", encoding="utf-8")
    (tmp_path / "outside.txt").write_text(marker, encoding="utf-8")
    os.symlink(str(tmp_path / "outside.txt"), str(proof / "link.txt"))
    evidence = ("Ran it: `proof/run.txt`, settings in `proof/.env.staging`, cert "
                "proof/tls.key, proof/api-credentials.txt, screenshot (proof/shot.png), "
                "proof/latin.txt, proof/empty.txt, proof/gone.txt, proof/../outside.txt, "
                "proof/link.txt. Again proof/run.txt.")
    kept, skipped = jev.read_evidence(tmp_path, evidence)
    assert kept == {"proof/run.txt": "3 passed in 0.2s\n"}
    assert {s["file"]: s["why"] for s in skipped} == {
        "proof/.env.staging": "secret_pattern", "proof/tls.key": "secret_pattern",
        "proof/api-credentials.txt": "secret_pattern", "proof/shot.png": "binary_or_empty",
        "proof/latin.txt": "binary_or_empty", "proof/empty.txt": "binary_or_empty",
        "proof/gone.txt": "not_found", "proof/../outside.txt": "outside_proof",
        "proof/link.txt": "outside_proof"}


def test_a_long_evidence_file_keeps_its_head_and_tail(tmp_path: Path) -> None:
    (tmp_path / "proof").mkdir()
    text = "START " + "x" * 9000 + " 412 passed END"
    (tmp_path / "proof" / "long.txt").write_text(text, encoding="utf-8")
    kept, skipped = jev.read_evidence(tmp_path, "See proof/long.txt.")
    cut = kept["proof/long.txt"]
    assert skipped == [] and cut.startswith("START ") and cut.endswith("412 passed END")
    assert "characters cut" in cut and len(cut) < jev.FILE_HEAD + jev.FILE_TAIL + 60


def test_a_proof_request_never_carries_a_secret_looking_file(tmp_path: Path) -> None:
    marker = "MARKER-NOT-A-REAL-SECRET-91f3"
    (tmp_path / "proof").mkdir()
    (tmp_path / "proof" / "a1-run.txt").write_text("downloaded invoices-2026-03.csv\n",
                                                   encoding="utf-8")
    (tmp_path / "proof" / ".env.local").write_text("KEY=%s\n" % marker, encoding="utf-8")
    text = SPEC.replace("Output in `proof/a1-run.txt`.",
                        "Output in `proof/a1-run.txt`, settings in `proof/.env.local`.")
    req, skipped = jev.proof_request(jev.parse_spec(text), tmp_path)
    sent = jev.canonical_body(jev.build_body(req.state, req.questions,
                                             jev.BACKENDS["vercel-gateway"])).decode()
    assert marker not in sent and "downloaded invoices-2026-03.csv" in sent
    assert skipped == [{"file": "proof/.env.local", "why": "secret_pattern"}]


# --------------------------------------------------------------------------
# What is asked
# --------------------------------------------------------------------------


def test_contract_request_asks_narrow_questions_about_named_paths() -> None:
    req = jev.contract_request(jev.parse_spec(SPEC))
    assert set(req.state) == {"measure", "scope_out", "criteria"}
    assert list(req.state["criteria"]) == ["A1", "A2", "A3"]
    assert sorted(req.questions) == sorted(
        ["A1_unclear", "A2_unclear", "A3_unclear",
         "A1_out_of_scope", "A2_out_of_scope", "A3_out_of_scope",
         "A1+A2_contradiction", "A1+A3_contradiction", "A2+A3_contradiction",
         "contract_contradiction", "contract_gap", "contract_no_measure"])
    for qid, question in req.questions.items():
        assert question["type"] == "noul" and set(question["criteria"]) == {"true", "false"}
        texts = [question["instructions"]] + list(question["criteria"].values())
        assert all(t and "{" not in t for t in texts), "an unfilled placeholder in %s" % qid
    assert "`criteria.A2`" in req.questions["A2_unclear"]["instructions"]
    assert "`scope_out`" in req.questions["A3_out_of_scope"]["instructions"]
    pair = req.questions["A1+A3_contradiction"]["instructions"]
    assert "`criteria.A1`" in pair and "`criteria.A3`" in pair
    assert "`measure`" in req.questions["contract_no_measure"]["instructions"]


def test_contract_request_skips_scope_questions_without_an_out_list_and_caps_pairs() -> None:
    bare = jev.parse_spec("## Acceptance criteria\n\n- **A1.** One.\n- **A2.** Two.\n")
    assert not [q for q in jev.contract_request(bare).questions if q.endswith("out_of_scope")]
    many = "## Acceptance criteria\n\n" + "".join(
        "- **A%d.** Thing %d happens.\n" % (n, n) for n in range(1, jev.MAX_PAIR_CRITERIA + 2))
    questions = jev.contract_request(jev.parse_spec(many)).questions
    assert not [q for q in questions if "+" in q] and "contract_contradiction" in questions


def test_proof_request_puts_each_row_beside_its_criterion_and_files(tmp_path: Path) -> None:
    (tmp_path / "proof").mkdir()
    (tmp_path / "proof" / "a1-run.txt").write_text("ok\n", encoding="utf-8")
    req, skipped = jev.proof_request(jev.parse_spec(SPEC), tmp_path)
    assert skipped == [] and list(req.state["rows"]) == ["A1", "A3"]  # A2 is Not proved
    assert req.state["rows"]["A1"]["files"] == {"proof/a1-run.txt": "ok\n"}
    assert req.state["rows"]["A1"]["criterion"].startswith("When a finance lead clicks")
    assert sorted(req.questions) == ["A1_asserted", "A1_unproven", "A3_could_be_checked"]
    assert "`rows.A1.evidence`" in req.questions["A1_unproven"]["instructions"]
    assert "`rows.A3.criterion`" in req.questions["A3_could_be_checked"]["instructions"]


# --------------------------------------------------------------------------
# Thresholds, bands, and composing the lines
# --------------------------------------------------------------------------


def test_shipped_thresholds_cover_every_code_and_record_how_they_were_fitted() -> None:
    data = json.loads((SKILL / "thresholds.json").read_text(encoding="utf-8"))
    bands, model = jev.load_thresholds()
    assert model == data["model"] and data["backend"] in jev.BACKENDS
    for code in ("unclear", "out_of_scope", "contradiction", "gap", "no_measure",
                 "unproven", "asserted", "could_be_checked"):
        entry = data["codes"][code]
        assert bands[code] == entry and 0 < entry["check"] <= 1
        assert entry["flag"] is None or entry["check"] <= entry["flag"] <= 1
    cal = data["calibration"]
    assert cal["fit_split"] == "dev" and cal["rule"] and set(cal["splits"]) == {"dev", "test"}
    assert cal["fixtures"]["dev"]["contracts"] >= 4 and cal["fixtures"]["test"]["proofs"] >= 4
    assert cal["run_to_run"]["largest_difference"] >= 0


def test_missing_or_broken_thresholds_fall_back_to_the_documented_defaults(
        tmp_path: Path) -> None:
    for content in (None, "not json", "[]", '{"codes": {"unclear": {"flag": 2, "check": 0.1}}}'):
        path = tmp_path / "t.json"
        if content is not None:
            path.write_text(content, encoding="utf-8")
        bands, model = jev.load_thresholds(path)
        assert bands["unclear"] == {"flag": 0.7, "check": 0.3} and model == ""


def test_band_and_the_check_only_threshold() -> None:
    assert [jev.band(p, {"flag": 0.7, "check": 0.3}) for p in (0.7, 0.69, 0.3, 0.29)] == [
        "flag", "check", "check", "quiet"]
    assert [jev.band(p, {"flag": None, "check": 0.4}) for p in (1.0, 0.4, 0.39)] == [
        "check", "check", "quiet"]


def _contract_run(tmp_path: Path, capsys: pytest.CaptureFixture, probabilities: Dict[str, float],
                  extra: Optional[List[str]] = None) -> Tuple[int, str]:
    repo = _repo(tmp_path)
    req = jev.contract_request(jev.parse_spec(SPEC))
    _record(tmp_path / "replay", req, "vercel-gateway", _respond(req, probabilities))
    code, out, _ = _main(capsys, ["contract", str(_spec_file(repo))] + (extra or []),
                         {"WRIT_JEV_REPLAY": str(tmp_path / "replay")})
    return code, out


def test_a_borderline_answer_is_a_check_line_and_does_not_count_as_a_flag(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    code, out = _contract_run(tmp_path, capsys, {"A2_unclear": 0.45})
    lines = _lines(out)
    assert code == 0 and lines[0] == "pass"
    assert lines[1] == ("check A2 unclear 0.45 — less certain: two readers could build "
                        "opposite behaviours and both meet this")
    assert lines[2] == "jev: 0 flags, 1 check, 3 criteria, backend=vercel-gateway"


def test_flag_lines_are_ordered_and_the_summary_counts_them(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    code, out = _contract_run(tmp_path, capsys, {
        "contract_no_measure": 0.97, "A3_out_of_scope": 0.91, "A1_unclear": 0.88,
        "A2_unclear": 0.4})
    assert code == 0 and _lines(out) == [
        "flag",
        "A1 unclear 0.88 — two readers could build opposite behaviours and both meet this",
        "A3 out_of_scope 0.91 — this asks for something the Out list says is left out",
        "contract no_measure 0.97 — the Outcome names nothing that would show the change "
        "worked",
        "check A2 unclear 0.40 — less certain: two readers could build opposite behaviours "
        "and both meet this",
        "jev: 3 flags, 1 check, 3 criteria, backend=vercel-gateway"]


def test_a_flagged_pair_replaces_the_whole_contract_contradiction_line(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    _, out = _contract_run(tmp_path, capsys, {"A1+A3_contradiction": 0.9,
                                              "contract_contradiction": 0.8})
    assert _marks(out) == [("A1+A3", "contradiction")]
    assert "these two criteria cannot both hold" in out
    _, out = _contract_run(tmp_path / "b", capsys, {"contract_contradiction": 0.8,
                                                    "A1+A2_contradiction": 0.35})
    assert _marks(out) == [("contract", "contradiction")]
    assert _marks(out, soft=True) == [("A1+A2", "contradiction")]


def test_json_output_has_every_probability(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    code, out = _contract_run(tmp_path, capsys, {"A1+A3_contradiction": 0.9,
                                                 "contract_contradiction": 0.8,
                                                 "A2_unclear": 0.45}, ["--json"])
    doc = json.loads(out)
    assert code == 0
    assert set(doc) == {"verdict", "kind", "backend", "model", "input_tokens", "request_bytes",
                        "flags", "checks", "answers", "summary"}
    assert (doc["verdict"], doc["kind"], doc["backend"]) == ("flag", "contract", "vercel-gateway")
    assert (doc["model"], doc["input_tokens"]) == ("typesafe-ai/jev", 1234)
    assert len(doc["answers"]) == 12  # one per question asked
    for answer in doc["answers"]:
        assert set(answer) - {"covered_by"} == {"id", "code", "p", "band", "reason"}
        assert 0 <= answer["p"] <= 1 and answer["band"] in ("flag", "check", "quiet")
    assert [(a["id"], a["code"], a["p"]) for a in doc["flags"]] == [("A1+A3", "contradiction", 0.9)]
    assert [(a["id"], a["code"], a["p"]) for a in doc["checks"]] == [("A2", "unclear", 0.45)]
    whole = [a for a in doc["answers"] if (a["id"], a["code"]) == ("contract", "contradiction")]
    assert whole[0]["band"] == "flag" and whole[0]["covered_by"] == "pair"
    assert doc["summary"] == "jev: 1 flag, 1 check, 3 criteria, backend=vercel-gateway"


def test_proof_run_hides_unproven_under_asserted_and_reports_files(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)
    path = _spec_file(repo)
    (path.parent / "proof").mkdir()
    (path.parent / "proof" / "a1-run.txt").write_text("ok\n", encoding="utf-8")
    req, _ = jev.proof_request(jev.parse_spec(SPEC), path.parent)
    _record(tmp_path / "replay", req, "vercel-gateway", _respond(req, {
        "A1_asserted": 0.95, "A1_unproven": 0.9, "A3_could_be_checked": 0.97}))
    env = {"WRIT_JEV_REPLAY": str(tmp_path / "replay")}
    code, out, _ = _main(capsys, ["proof", str(path)], env)
    assert code == 0 and _lines(out)[0] == "flag"
    assert _marks(out) == [("A1", "asserted"), ("A3", "could_be_checked")]
    assert _lines(out)[-1] == ("jev: 2 flags, 0 checks, 3 rows, backend=vercel-gateway "
                               "files=1 skipped=0")
    doc = json.loads(_main(capsys, ["proof", str(path), "--json"], env)[1])
    assert doc["skipped_files"] == [] and len(doc["answers"]) == 3
    assert [a["covered_by"] for a in doc["answers"] if a["code"] == "unproven"] == ["asserted"]


def test_a_criterion_with_no_proof_row_is_flagged_without_a_model_call(
        tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    repo = _repo(tmp_path)
    text = ("## Acceptance criteria\n\n- **A1.** One.\n- **A2.** Two.\n- **A3.** Three.\n\n"
            "## Proof\n\n- **A1. Not proved.** Ran it; it failed.\n"
            "- **A7. Proved.** A row for a criterion that does not exist.\n")
    calls: List = []
    code, out, _ = _main(capsys, ["proof", str(_spec_file(repo, text))],
                         {"AI_GATEWAY_API_KEY": FAKE_KEY}, _fake_transport(calls=calls))
    assert code == 0 and calls == [] and _lines(out) == [
        "flag",
        "A2 missing n/a — the proof has no row for this criterion",
        "A3 missing n/a — the proof has no row for this criterion",
        "jev: 2 flags, 0 checks, 2 rows, backend=vercel-gateway files=0 skipped=0"]


def test_missing_thresholds_are_named_in_the_summary(
        tmp_path: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jev, "THRESHOLDS_PATH", tmp_path / "absent.json")
    _, out = _contract_run(tmp_path, capsys, {"A1_unclear": 0.69, "A2_unclear": 0.7})
    assert _marks(out) == [("A2", "unclear")] and _marks(out, soft=True) == [("A1", "unclear")]
    assert _lines(out)[-1].endswith("backend=vercel-gateway thresholds=default")


# --------------------------------------------------------------------------
# Replay of the recorded live responses for the labelled fixtures
# --------------------------------------------------------------------------


def _labels() -> Dict[str, Dict[str, Any]]:
    data = json.loads((FIXTURES / "labels.json").read_text(encoding="utf-8"))
    return {name: label for name, label in data.items() if not name.startswith("_")}


def _fixture_run(capsys: pytest.CaptureFixture, tmp_path: Path, name: str,
                 extra: Optional[List[str]] = None) -> str:
    kind = "contract" if name.startswith("contracts/") else "proof"
    repo = _repo(tmp_path)
    code, out, err = _main(capsys, [kind, str(FIXTURES / name / "spec.md"), "--repo", str(repo)]
                           + (extra or []), {"WRIT_JEV_REPLAY": str(REPLAY)})
    assert code == 0 and err == ""
    return out


def test_the_fixture_set_is_large_enough_and_split() -> None:
    labels = _labels()
    for kind in ("contracts/", "proofs/"):
        for split in ("dev", "test"):
            names = [n for n, v in labels.items() if n.startswith(kind) and v["split"] == split]
            assert len(names) >= 4, (kind, split)
            assert any(not labels[n]["gold"] for n in names), "no clean %s in %s" % (kind, split)
    assert len(labels) >= 16 and all((FIXTURES / n / "spec.md").is_file() for n in labels)
    codes = {g.split()[1] for v in labels.values() for g in v["gold"]}
    assert codes == {"unclear", "out_of_scope", "contradiction", "gap", "no_measure",
                     "unproven", "asserted", "could_be_checked", "missing"}


@pytest.mark.parametrize("name", sorted(_labels()))
def test_recorded_fixture_raises_its_gold_flags_and_no_others(
        capsys: pytest.CaptureFixture, tmp_path: Path, name: str) -> None:
    gold = [tuple(g.split()) for g in _labels()[name]["gold"]]
    out = _fixture_run(capsys, tmp_path, name)
    flags = _marks(out)
    assert _lines(out)[0] == ("flag" if gold else "pass"), out
    summary = SUMMARY.match(_lines(out)[-1])
    assert summary and int(summary.group(1)) == len(flags)
    assert summary.group(5) == "vercel-gateway" and "thresholds=" not in _lines(out)[-1]
    for target, code in gold:
        # A contradiction may be reported on the contract or on the pair itself.
        hit = [f for f in flags if f[1] == code and (f[0] == target or (
            code == "contradiction" and "+" in f[0]))]
        assert hit, "gold %s %s not flagged:\n%s" % (target, code, out)
    gold_lines = {target for target, _ in gold}
    for target, code in flags:
        # The only flags beyond gold sit on a line that is already a gold defect.
        on_gold_line = target in gold_lines or (
            "+" in target and ("contract", "contradiction") in gold)
        assert on_gold_line, "unexpected flag %s %s:\n%s" % (target, code, out)


def test_recorded_contract_output_line_for_line(capsys: pytest.CaptureFixture,
                                                tmp_path: Path) -> None:
    out = _fixture_run(capsys, tmp_path, "contracts/team-invite-links")
    lines = _lines(out)
    assert lines[0] == "flag" and len(lines) == 4
    assert re.fullmatch(r"A5 out_of_scope 0\.\d\d — this asks for something the Out list says "
                        r"is left out", lines[1])
    assert re.fullmatch(r"contract gap 0\.\d\d — something the user supplies has no criterion "
                        r"for when it is missing or invalid", lines[2])
    assert lines[3] == "jev: 2 flags, 0 checks, 5 criteria, backend=vercel-gateway"


def test_recorded_proof_output_line_for_line(capsys: pytest.CaptureFixture,
                                             tmp_path: Path) -> None:
    out = _fixture_run(capsys, tmp_path, "proofs/coupon-codes")
    lines = _lines(out)
    assert lines[0] == "flag" and len(lines) == 6
    assert re.fullmatch(r"A3 unproven 0\.\d\d — the evidence does not show this criterion "
                        r"holding", lines[1])
    assert re.fullmatch(r"A4 asserted 0\.\d\d — the evidence says it works without reporting "
                        r"what was run or seen", lines[2])
    assert lines[4] == "A6 missing n/a — the proof has no row for this criterion"
    assert lines[5] == "jev: 4 flags, 0 checks, 5 rows, backend=vercel-gateway files=1 skipped=0"


def test_recorded_clean_proof_is_silent_and_skips_the_screenshot(
        capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
    out = _fixture_run(capsys, tmp_path, "proofs/csv-export")
    assert _lines(out) == ["pass", "jev: 0 flags, 0 checks, 6 rows, backend=vercel-gateway "
                                   "files=3 skipped=1"]
    doc = json.loads(_fixture_run(capsys, tmp_path / "j", "proofs/csv-export", ["--json"]))
    assert doc["skipped_files"] == [{"file": "proof/a1-download.png", "why": "binary_or_empty"}]
    assert doc["flags"] == [] and doc["checks"] == [] and len(doc["answers"]) == 11


def test_recordings_are_live_and_hold_no_key_material() -> None:
    files = sorted(REPLAY.glob("*.json"))
    assert len(files) == len(_labels())
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) == {"model", "answers", "usage", "writ_recording"}
        assert data["writ_recording"]["source"] == "live"
        assert data["writ_recording"]["fixture"] in _labels()
        assert "authorization" not in path.read_text(encoding="utf-8").lower()


def test_the_cli_runs_a_recorded_fixture_as_a_subprocess(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    spec = FIXTURES / "contracts" / "saved-search-alerts" / "spec.md"
    code, out, err = _subprocess(["contract", str(spec), "--repo", str(repo)],
                                 {"WRIT_JEV_REPLAY": str(REPLAY)})
    assert (code, err) == (0, "") and _lines(out)[0] == "flag"
    assert _marks(out) == [("A2", "unclear"), ("A4", "unclear"), ("contract", "no_measure")]

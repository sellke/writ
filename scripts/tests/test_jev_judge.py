#!/usr/bin/env python3
"""Tests for scripts/jev-judge.py `status` (Story 1 of
`2026-09-25-jev-judgment-pilot`). [AC-1.3, AC-1.4, AC-1.5]

No test reaches the network: the in-process tests patch every request and
socket entry point to raise, and the subprocess tests never set a replay or
live transport (Story 1 has none).
"""

from __future__ import annotations

import http.client
import importlib.util
import os
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "jev-judge.py"

KEY_VARS = ("TYPESAFE_API_KEY", "AI_GATEWAY_API_KEY", "VERCEL_OIDC_TOKEN")
FAKE_KEY = "sk-jev-FAKE-3b9f1c7e0d4a2265-DO-NOT-PRINT"

CONFIG_TEMPLATE = """# Writ Configuration

- **Default Branch:** main
{line}- **Test Runner:** uv run pytest
"""


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _load_module():
    spec = importlib.util.spec_from_file_location("jev_judge", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _repo(tmp_path: Path, provider: Optional[str], config: bool = True) -> Path:
    """Temp repo. provider=None writes config.md with no Judgment Provider line."""
    repo = tmp_path / "repo"
    (repo / ".writ").mkdir(parents=True)
    if config:
        line = "" if provider is None else "- **Judgment Provider:** %s\n" % provider
        (repo / ".writ" / "config.md").write_text(
            CONFIG_TEMPLATE.format(line=line), encoding="utf-8"
        )
    return repo


def _clean_env(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in KEY_VARS}
    env.update(extra or {})
    return env


def _run(args: List[str], env: Dict[str, str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd) if cwd else None,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _verdict(out: str) -> str:
    lines = out.strip().splitlines()
    return lines[0] if lines else ""


def _reasons(out: str) -> List[str]:
    return [ln[len("reason: "):] for ln in out.splitlines() if ln.startswith("reason: ")]


def _summary(out: str) -> str:
    lines = out.strip().splitlines()
    return lines[-1] if lines else ""


def _assert_shape(out: str) -> None:
    """One verdict line first, only `reason:` lines between, summary last."""
    lines = out.strip().splitlines()
    assert len(lines) >= 2, out
    assert lines[0] in ("pass", "fail", "unverifiable"), out
    assert all(ln.startswith("reason: ") for ln in lines[1:-1]), out
    assert lines[-1].startswith("jev-judge:"), out
    verdicts = [ln for ln in lines if ln in ("pass", "fail", "unverifiable")]
    assert len(verdicts) == 1, out


def _assert_key_absent(repo_root: Path, *streams: str) -> None:
    for stream in streams:
        assert FAKE_KEY not in stream
    for path in repo_root.rglob("*"):
        if path.is_file():
            assert FAKE_KEY.encode() not in path.read_bytes(), path


@pytest.fixture
def no_network(monkeypatch):
    """Every request or connection attempt raises and is recorded."""
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


@pytest.fixture
def jev():
    return _load_module()


def _status_inproc(jev, capsys, repo: Path, env: Dict[str, str]) -> Tuple[int, str, str]:
    code = jev.main(["status", "--repo", str(repo)], environ=env)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# --------------------------------------------------------------------------
# Enabled: each backend with its key [AC-1.3]
# --------------------------------------------------------------------------


def test_typesafe_with_key_is_enabled(tmp_path, jev, capsys, no_network):
    repo = _repo(tmp_path, "typesafe")
    code, out, err = _status_inproc(jev, capsys, repo, {"TYPESAFE_API_KEY": FAKE_KEY})
    assert code == 0
    _assert_shape(out)
    assert _verdict(out) == "pass"
    assert _reasons(out) == ["enabled"]
    assert "backend=typesafe" in _summary(out)
    assert "model=jev-1.13.0" in _summary(out)
    assert no_network == []
    _assert_key_absent(repo, out, err)


def test_vercel_gateway_with_gateway_key_is_enabled(tmp_path, jev, capsys, no_network):
    repo = _repo(tmp_path, "vercel-gateway")
    code, out, err = _status_inproc(jev, capsys, repo, {"AI_GATEWAY_API_KEY": FAKE_KEY})
    assert code == 0
    _assert_shape(out)
    assert _verdict(out) == "pass"
    assert _reasons(out)[0] == "enabled"
    # Informational: the gateway accepts only the alias; drift is undetectable.
    assert "model_unpinned" in _reasons(out)
    assert "backend=vercel-gateway" in _summary(out)
    assert "model=typesafe-ai/jev" in _summary(out)
    assert no_network == []
    _assert_key_absent(repo, out, err)


def test_vercel_gateway_with_only_oidc_token_is_enabled(tmp_path, jev, capsys, no_network):
    repo = _repo(tmp_path, "vercel-gateway")
    code, out, err = _status_inproc(jev, capsys, repo, {"VERCEL_OIDC_TOKEN": FAKE_KEY})
    assert code == 0
    assert _verdict(out) == "pass"
    assert _reasons(out)[0] == "enabled"
    assert "backend=vercel-gateway" in _summary(out)
    assert no_network == []
    _assert_key_absent(repo, out, err)


def test_config_value_is_case_insensitive(tmp_path, jev, capsys, no_network):
    repo = _repo(tmp_path, "TypeSafe")
    code, out, _err = _status_inproc(jev, capsys, repo, {"TYPESAFE_API_KEY": FAKE_KEY})
    assert code == 0
    assert _verdict(out) == "pass"
    assert "backend=typesafe" in _summary(out)


# --------------------------------------------------------------------------
# Both keys set: the config line decides [AC-1.3]
# --------------------------------------------------------------------------


@pytest.mark.parametrize("provider", ["typesafe", "vercel-gateway"])
def test_both_keys_set_config_line_decides(tmp_path, jev, capsys, no_network, provider):
    repo = _repo(tmp_path, provider)
    env = {"TYPESAFE_API_KEY": FAKE_KEY, "AI_GATEWAY_API_KEY": FAKE_KEY}
    code, out, err = _status_inproc(jev, capsys, repo, env)
    assert code == 0
    assert _verdict(out) == "pass"
    assert "backend=%s" % provider in _summary(out)
    other = "vercel-gateway" if provider == "typesafe" else "typesafe"
    assert "backend=%s" % other not in _summary(out)
    _assert_key_absent(repo, out, err)


def test_other_backends_key_does_not_enable(tmp_path, jev, capsys, no_network):
    """typesafe named, only the gateway key set: that key is not typesafe's."""
    repo = _repo(tmp_path, "typesafe")
    code, out, err = _status_inproc(jev, capsys, repo, {"AI_GATEWAY_API_KEY": FAKE_KEY})
    assert code == 0
    assert _verdict(out) == "unverifiable"
    assert _reasons(out) == ["no_api_key"]
    assert "TYPESAFE_API_KEY" in _summary(out)
    _assert_key_absent(repo, out, err)


# --------------------------------------------------------------------------
# Disabled: no_config_line [AC-1.3]
# --------------------------------------------------------------------------


def test_config_file_missing_is_no_config_line(tmp_path, jev, capsys, no_network):
    repo = _repo(tmp_path, None, config=False)
    code, out, _err = _status_inproc(jev, capsys, repo, {})
    assert code == 0
    _assert_shape(out)
    assert _verdict(out) == "unverifiable"
    assert _reasons(out) == ["no_config_line"]


def test_config_without_line_is_no_config_line(tmp_path, jev, capsys, no_network):
    repo = _repo(tmp_path, None)
    code, out, _err = _status_inproc(jev, capsys, repo, {})
    assert code == 0
    _assert_shape(out)
    assert _verdict(out) == "unverifiable"
    assert _reasons(out) == ["no_config_line"]


def test_indented_or_unbulleted_line_does_not_count(tmp_path, jev, capsys, no_network):
    repo = tmp_path / "repo"
    (repo / ".writ").mkdir(parents=True)
    (repo / ".writ" / "config.md").write_text(
        "  - **Judgment Provider:** typesafe\n**Judgment Provider:** typesafe\n",
        encoding="utf-8",
    )
    code, out, _err = _status_inproc(jev, capsys, repo, {"TYPESAFE_API_KEY": FAKE_KEY})
    assert code == 0
    assert _reasons(out) == ["no_config_line"]


# --------------------------------------------------------------------------
# Disabled: provider_disabled [AC-1.3]
# --------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["none", "None", "openai", "typesafe-direct"])
def test_none_or_unknown_value_is_provider_disabled(tmp_path, jev, capsys, no_network, value):
    repo = _repo(tmp_path, value)
    env = {"TYPESAFE_API_KEY": FAKE_KEY, "AI_GATEWAY_API_KEY": FAKE_KEY}
    code, out, err = _status_inproc(jev, capsys, repo, env)
    assert code == 0
    _assert_shape(out)
    assert _verdict(out) == "unverifiable"
    assert _reasons(out) == ["provider_disabled"]
    assert no_network == []
    _assert_key_absent(repo, out, err)


def test_unknown_value_is_not_echoed(tmp_path, jev, capsys, no_network):
    """A key pasted into the config line by mistake must not reach stdout."""
    repo = _repo(tmp_path, FAKE_KEY)
    code, out, err = _status_inproc(jev, capsys, repo, {})
    assert code == 0
    assert _reasons(out) == ["provider_disabled"]
    assert FAKE_KEY not in out
    assert FAKE_KEY not in err


# --------------------------------------------------------------------------
# Disabled: no_api_key [AC-1.3]
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "provider,env,export_var",
    [
        ("typesafe", {}, "TYPESAFE_API_KEY"),
        ("typesafe", {"TYPESAFE_API_KEY": ""}, "TYPESAFE_API_KEY"),
        ("typesafe", {"TYPESAFE_API_KEY": "   \t"}, "TYPESAFE_API_KEY"),
        ("vercel-gateway", {}, "AI_GATEWAY_API_KEY"),
        ("vercel-gateway", {"AI_GATEWAY_API_KEY": ""}, "AI_GATEWAY_API_KEY"),
        ("vercel-gateway", {"AI_GATEWAY_API_KEY": "  ", "VERCEL_OIDC_TOKEN": " "}, "AI_GATEWAY_API_KEY"),
    ],
)
def test_named_backend_without_key_is_no_api_key(
    tmp_path, jev, capsys, no_network, provider, env, export_var
):
    repo = _repo(tmp_path, provider)
    code, out, _err = _status_inproc(jev, capsys, repo, env)
    assert code == 0
    _assert_shape(out)
    assert _verdict(out) == "unverifiable"
    assert _reasons(out)[0] == "no_api_key"
    assert export_var in _summary(out)
    assert "backend=%s" % provider in _summary(out)
    assert no_network == []


# --------------------------------------------------------------------------
# Key set, no config line: disabled, no request, no leak [AC-1.4]
# --------------------------------------------------------------------------


@pytest.mark.parametrize("config", [True, False])
def test_key_alone_never_enables(tmp_path, jev, capsys, no_network, config):
    repo = _repo(tmp_path, None, config=config)
    env = {k: FAKE_KEY for k in KEY_VARS}
    code, out, err = _status_inproc(jev, capsys, repo, env)
    assert code == 0
    assert _verdict(out) == "unverifiable"
    assert _reasons(out) == ["no_config_line"]
    assert "pass" not in out.splitlines()
    assert no_network == []
    _assert_key_absent(repo, out, err)


def test_status_writes_no_files(tmp_path, jev, capsys, no_network):
    repo = _repo(tmp_path, "typesafe")
    before = sorted(p.relative_to(repo) for p in repo.rglob("*"))
    _status_inproc(jev, capsys, repo, {"TYPESAFE_API_KEY": FAKE_KEY})
    after = sorted(p.relative_to(repo) for p in repo.rglob("*"))
    assert before == after


# --------------------------------------------------------------------------
# Subprocess: real stdout/stderr, real environment [AC-1.3, AC-1.4]
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "provider,config,env_keys,verdict,reason",
    [
        ("typesafe", True, ("TYPESAFE_API_KEY",), "pass", "enabled"),
        ("vercel-gateway", True, ("AI_GATEWAY_API_KEY",), "pass", "enabled"),
        ("vercel-gateway", True, ("VERCEL_OIDC_TOKEN",), "pass", "enabled"),
        (None, True, KEY_VARS, "unverifiable", "no_config_line"),
        (None, False, KEY_VARS, "unverifiable", "no_config_line"),
        ("none", True, KEY_VARS, "unverifiable", "provider_disabled"),
        ("bogus", True, KEY_VARS, "unverifiable", "provider_disabled"),
        ("typesafe", True, ("AI_GATEWAY_API_KEY", "VERCEL_OIDC_TOKEN"), "unverifiable", "no_api_key"),
    ],
)
def test_subprocess_status_cases_never_leak_key(
    tmp_path, provider, config, env_keys, verdict, reason
):
    repo = _repo(tmp_path, provider, config=config)
    env = _clean_env({k: FAKE_KEY for k in env_keys})
    code, out, err = _run(["status", "--repo", str(repo)], env)
    assert code == 0, err
    _assert_shape(out)
    assert _verdict(out) == verdict
    assert _reasons(out)[0] == reason
    _assert_key_absent(repo, out, err)


def test_project_alias_matches_repo(tmp_path):
    repo = _repo(tmp_path, "typesafe")
    env = _clean_env({"TYPESAFE_API_KEY": FAKE_KEY})
    code, out, err = _run(["status", "--project", str(repo)], env)
    assert code == 0, err
    assert _verdict(out) == "pass"
    _assert_key_absent(repo, out, err)


def test_repo_defaults_to_cwd(tmp_path):
    repo = _repo(tmp_path, "vercel-gateway")
    env = _clean_env({"AI_GATEWAY_API_KEY": FAKE_KEY})
    code, out, err = _run(["status"], env, cwd=repo)
    assert code == 0, err
    assert _verdict(out) == "pass"
    assert "backend=vercel-gateway" in _summary(out)
    _assert_key_absent(repo, out, err)


# --------------------------------------------------------------------------
# Usage errors exit 2 [AC-1.3]
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["bogus"],
        ["status", "--nope"],
        ["status", "extra-positional"],
        ["status", "--repo"],
    ],
)
def test_bad_argv_exits_2(tmp_path, argv):
    env = _clean_env({k: FAKE_KEY for k in KEY_VARS})
    code, out, err = _run(argv, env, cwd=tmp_path)
    assert code == 2
    assert FAKE_KEY not in out
    assert FAKE_KEY not in err


def test_repo_not_a_directory_exits_2(tmp_path):
    env = _clean_env({"TYPESAFE_API_KEY": FAKE_KEY})
    code, out, err = _run(["status", "--repo", str(tmp_path / "missing")], env)
    assert code == 2
    assert FAKE_KEY not in out
    assert FAKE_KEY not in err


def test_main_returns_2_in_process_on_bad_argv(jev, capsys):
    assert jev.main(["status", "--nope"], environ={}) == 2
    capsys.readouterr()



# ==========================================================================
# Story 2: client transport, replay, thresholds, probe
# [AC-2.1, AC-2.2, AC-2.3, AC-2.5]
#
# No test reaches the network. In-process tests run under `no_network`
# (every urllib/http.client/socket entry point raises); tests that drive the
# live transport swap in a scripted `urlopen` on top of that guard, so the
# socket-level guards stay active. Subprocess tests set WRIT_JEV_REPLAY and
# point HTTPS_PROXY at a dead port so a leak would fail, not connect.
# ==========================================================================

import email.message
import hashlib
import io
import json
import socket as _socket
import urllib.error

REAL_REQUEST = urllib.request.Request
REPLAY_DIR = REPO_ROOT / "scripts" / "tests" / "fixtures" / "jev-replay"
INPUTS_DIR = REPLAY_DIR / "inputs"
THRESHOLDS = REPO_ROOT / "scripts" / "jev-thresholds.json"

STATE = {"story": {"title": "Demo story", "criteria": ["Given a, when b, then c"]}}
QUESTIONS = {
    "q1": {
        "type": "noul",
        "instructions": "Do two criteria in `story.criteria` require outcomes that cannot both hold?",
        "criteria": {
            "true": "Two criteria require outcomes that cannot both hold.",
            "false": "All criteria can hold together.",
        },
    }
}


def _canonical(body) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _typesafe_body(state=STATE, questions=QUESTIONS):
    return {"model": "jev-1.13.0", "state": state, "questions": questions}


def _gateway_body(state=STATE, questions=QUESTIONS):
    return {
        "model": "typesafe-ai/jev",
        "state": state,
        "questions": questions,
        "providerOptions": {"gateway": {"only": ["typesafe-ai"]}},
    }


def _ok_body(model="jev-1.13.0", **extra):
    body = {
        "model": model,
        "answers": {"q1": {"type": "noul", "noul": 0.01}},
        "usage": {"input_tokens": 280, "output_tokens": 20},
    }
    body.update(extra)
    return body


class FakeHTTP:
    """Scripted transport: each call pops the next (status, headers, body)."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls: List[Tuple[str, Dict[str, str], bytes]] = []

    def __call__(self, url, headers, payload):
        self.calls.append((url, dict(headers), payload))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        status, hdrs, body = outcome
        raw = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        return self.jev.HttpResponse(status, {k.lower(): v for k, v in hdrs.items()}, raw)


@pytest.fixture
def fake_http(jev):
    def make(*outcomes):
        fake = FakeHTTP(*outcomes)
        fake.jev = jev
        return fake
    return make


class Sleeper:
    def __init__(self):
        self.calls: List[float] = []

    def __call__(self, seconds):
        self.calls.append(seconds)


@pytest.fixture
def sleeper():
    return Sleeper()


def _judge(jev, fake, sleeper, backend="typesafe", env=None, state=STATE, questions=QUESTIONS):
    environ = {"TYPESAFE_API_KEY": FAKE_KEY, "AI_GATEWAY_API_KEY": FAKE_KEY} if env is None else env
    return jev.judge(state, questions, jev.BACKENDS[backend], environ,
                     transport=fake, sleep=sleeper)


# --------------------------------------------------------------------------
# HTTP outcome map, via an injected transport [AC-2.1]
# --------------------------------------------------------------------------


def test_success_typesafe_records_model_and_tokens(jev, fake_http, sleeper, no_network):
    fake = fake_http((200, {}, _ok_body()))
    res = _judge(jev, fake, sleeper)
    assert res.verdict == "pass"
    assert res.reasons == []
    assert res.answers == {"q1": {"type": "noul", "noul": 0.01}}
    assert res.model == "jev-1.13.0"
    assert res.input_tokens == 280
    assert res.cost is None
    assert res.attempts == 1
    assert sleeper.calls == []
    assert no_network == []


@pytest.mark.parametrize(
    "status,body,reason",
    [
        (401, {"message": "bad key", "error_type": "unauthorized"}, "auth_error"),
        (422, {"message": "questions invalid", "error_type": "validation_error"}, "request_invalid"),
        (404, {"error": {"message": "Model typesafe-ai/jev-9 not found", "type": "model_not_found"}},
         "request_invalid"),
        (500, {"message": "boom"}, "transport_error"),
        (502, b"<html>bad gateway</html>", "transport_error"),
        (503, b"", "transport_error"),
    ],
)
def test_http_status_maps_to_named_unverifiable(jev, fake_http, sleeper, no_network, status, body, reason):
    fake = fake_http((status, {}, body))
    res = _judge(jev, fake, sleeper)
    assert res.verdict == "unverifiable"
    assert res.reasons[0] == reason
    assert res.answers is None
    assert res.attempts == 1  # no retry outside 429/529
    assert sleeper.calls == []


def test_request_invalid_logs_typesafe_error_body_to_stderr(jev, fake_http, sleeper, capsys, no_network):
    fake = fake_http((422, {}, {"message": "questions.q1.criteria missing", "error_type": "validation_error"}))
    _judge(jev, fake, sleeper)
    err = capsys.readouterr().err
    assert "validation_error" in err
    assert "questions.q1.criteria missing" in err


def test_request_invalid_logs_gateway_error_body_to_stderr(jev, fake_http, sleeper, capsys, no_network):
    body = {"error": {"message": "Model typesafe-ai/jev-1.13.0 not found", "type": "model_not_found"}}
    fake = fake_http((404, {}, body))
    res = _judge(jev, fake, sleeper, backend="vercel-gateway")
    assert res.reasons == ["request_invalid", "model_unpinned"]
    err = capsys.readouterr().err
    assert "model_not_found" in err
    assert "typesafe-ai/jev-1.13.0 not found" in err


def test_request_invalid_body_truncated_to_500_chars(jev, fake_http, sleeper, capsys, no_network):
    raw = json.dumps({"message": "x" * 2000, "error_type": "validation_error"})
    fake = fake_http((422, {}, raw.encode("utf-8")))
    _judge(jev, fake, sleeper)
    err = capsys.readouterr().err
    (body_line,) = [ln for ln in err.splitlines() if ln.startswith("jev-judge: body=")]
    logged = body_line[len("jev-judge: body="):]
    assert logged == raw[:500]
    assert all(len(ln) <= 500 + len("jev-judge: body=") for ln in err.splitlines())


def test_429_then_success_retries_once(jev, fake_http, sleeper, no_network):
    fake = fake_http((429, {}, {"message": "slow down"}), (200, {}, _ok_body()))
    res = _judge(jev, fake, sleeper)
    assert res.verdict == "pass"
    assert res.attempts == 2
    assert sleeper.calls == [1]


@pytest.mark.parametrize("status", [429, 529])
def test_rate_limited_after_three_attempts(jev, fake_http, sleeper, no_network, status):
    fake = fake_http(*[(status, {}, {"message": "busy"})] * 3)
    res = _judge(jev, fake, sleeper)
    assert res.verdict == "unverifiable"
    assert res.reasons == ["rate_limited"]
    assert res.attempts == 3
    assert len(fake.calls) == 3
    assert sleeper.calls == [1, 2]  # exponential backoff between attempts


def test_retry_after_header_is_honored(jev, fake_http, sleeper, no_network):
    fake = fake_http(
        (429, {"Retry-After": "7"}, {"message": "busy"}),
        (529, {"retry-after": "0.5"}, {"message": "overloaded"}),
        (200, {}, _ok_body()),
    )
    res = _judge(jev, fake, sleeper)
    assert res.verdict == "pass"
    assert res.attempts == 3
    assert sleeper.calls == [7.0, 0.5]


@pytest.mark.parametrize("value", ["soon", "-3", "Wed, 21 Oct 2026 07:28:00 GMT", ""])
def test_unparseable_retry_after_falls_back_to_backoff(jev, fake_http, sleeper, no_network, value):
    fake = fake_http((429, {"retry-after": value}, {}), (200, {}, _ok_body()))
    res = _judge(jev, fake, sleeper)
    assert res.attempts == 2
    assert sleeper.calls == [1]


def test_retry_after_is_capped(jev, fake_http, sleeper, no_network):
    fake = fake_http((429, {"retry-after": "3600"}, {}), (200, {}, _ok_body()))
    _judge(jev, fake, sleeper)
    assert sleeper.calls == [jev.RETRY_AFTER_CAP_SECONDS]


def test_transport_failure_exception_is_transport_error(jev, fake_http, sleeper, no_network):
    fake = fake_http(jev.TransportFailure("URLError"))
    res = _judge(jev, fake, sleeper)
    assert res.verdict == "unverifiable"
    assert res.reasons == ["transport_error"]
    assert res.attempts == 1


# --------------------------------------------------------------------------
# Live transport: urlopen scripted over the network guard [AC-2.1]
# --------------------------------------------------------------------------


class _FakeResp:
    def __init__(self, status, headers, body):
        self.status = status
        msg = email.message.Message()
        for k, v in headers.items():
            msg[k] = v
        self.headers = msg
        self._body = body

    def getcode(self):
        return self.status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(url, code, headers=None, body=b"{}"):
    msg = email.message.Message()
    for k, v in (headers or {}).items():
        msg[k] = v
    return urllib.error.HTTPError(url, code, "status %d" % code, msg, io.BytesIO(body))


@pytest.fixture
def scripted_urlopen(monkeypatch, no_network):
    """Replace urlopen (and restore Request) on top of the network guard.

    Socket- and http.client-level guards from `no_network` stay in place.
    """
    calls: List[Dict[str, object]] = []
    outcomes: List[object] = []

    def _urlopen(req, timeout=None, **_kw):
        calls.append({
            "url": req.full_url,
            "method": req.get_method(),
            "headers": {k.lower(): v for k, v in req.header_items()},
            "data": req.data,
            "timeout": timeout,
        })
        outcome = outcomes.pop(0)
        if callable(outcome):
            outcome = outcome(req.full_url)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    monkeypatch.setattr(urllib.request, "Request", REAL_REQUEST)
    monkeypatch.setattr(urllib.request, "urlopen", _urlopen)

    def load(*items):
        outcomes.extend(items)
        return calls
    return load


def _judge_live(jev, sleeper, backend="typesafe", env=None):
    environ = {"TYPESAFE_API_KEY": FAKE_KEY, "AI_GATEWAY_API_KEY": FAKE_KEY} if env is None else env
    return jev.judge(STATE, QUESTIONS, jev.BACKENDS[backend], environ, sleep=sleeper)


def test_live_typesafe_request_shape(jev, sleeper, scripted_urlopen):
    calls = scripted_urlopen(_FakeResp(200, {}, json.dumps(_ok_body()).encode()))
    res = _judge_live(jev, sleeper)
    assert res.verdict == "pass"
    (call,) = calls
    assert call["url"] == "https://api.typesafe.ai/v1/systemone"
    assert call["method"] == "POST"
    assert call["timeout"] == 10
    assert call["headers"]["authorization"] == "Bearer %s" % FAKE_KEY
    assert call["headers"]["content-type"] == "application/json"
    assert json.loads(call["data"]) == _typesafe_body()
    assert call["data"] == _canonical(_typesafe_body())


def test_live_gateway_request_shape_restricts_routing(jev, sleeper, scripted_urlopen):
    body = _ok_body(model="typesafe-ai/jev",
                    provider_metadata={"gateway": {"cost": "0.00001155", "routing": {}}})
    calls = scripted_urlopen(_FakeResp(200, {}, json.dumps(body).encode()))
    res = _judge_live(jev, sleeper, backend="vercel-gateway", env={"AI_GATEWAY_API_KEY": FAKE_KEY})
    assert res.verdict == "pass"
    assert res.reasons == ["model_unpinned"]
    assert res.cost == "0.00001155"
    (call,) = calls
    assert call["url"] == "https://ai-gateway.vercel.sh/typesafe/v1/systemone"
    sent = json.loads(call["data"])
    assert sent["model"] == "typesafe-ai/jev"
    assert sent["providerOptions"] == {"gateway": {"only": ["typesafe-ai"]}}


def test_live_gateway_uses_oidc_token_when_gateway_key_absent(jev, sleeper, scripted_urlopen):
    body = _ok_body(model="typesafe-ai/jev")
    calls = scripted_urlopen(_FakeResp(200, {}, json.dumps(body).encode()))
    _judge_live(jev, sleeper, backend="vercel-gateway", env={"VERCEL_OIDC_TOKEN": FAKE_KEY})
    assert calls[0]["headers"]["authorization"] == "Bearer %s" % FAKE_KEY


@pytest.mark.parametrize(
    "exc",
    [
        _socket.timeout("timed out"),
        urllib.error.URLError(_socket.timeout("timed out")),
        urllib.error.URLError(_socket.gaierror(8, "nodename nor servname provided")),
        ConnectionResetError(54, "Connection reset by peer"),
    ],
    ids=["timeout", "urlerror-timeout", "dns", "reset"],
)
def test_live_network_failures_are_transport_error(jev, sleeper, scripted_urlopen, exc):
    scripted_urlopen(exc)
    res = _judge_live(jev, sleeper)
    assert res.verdict == "unverifiable"
    assert res.reasons == ["transport_error"]
    assert res.attempts == 1


@pytest.mark.parametrize(
    "code,reason",
    [(401, "auth_error"), (422, "request_invalid"), (500, "transport_error"), (503, "transport_error")],
)
def test_live_http_errors_map(jev, sleeper, scripted_urlopen, code, reason):
    scripted_urlopen(lambda url: _http_error(url, code, body=b'{"message":"m","error_type":"t"}'))
    res = _judge_live(jev, sleeper)
    assert res.verdict == "unverifiable"
    assert res.reasons == [reason]


def test_live_429_then_200_honors_retry_after(jev, sleeper, scripted_urlopen):
    calls = scripted_urlopen(
        lambda url: _http_error(url, 429, headers={"Retry-After": "3"}),
        _FakeResp(200, {}, json.dumps(_ok_body()).encode()),
    )
    res = _judge_live(jev, sleeper)
    assert res.verdict == "pass"
    assert res.attempts == 2
    assert sleeper.calls == [3.0]
    assert len(calls) == 2


def test_live_529_three_times_is_rate_limited(jev, sleeper, scripted_urlopen):
    scripted_urlopen(*[lambda url: _http_error(url, 529)] * 3)
    res = _judge_live(jev, sleeper)
    assert res.reasons == ["rate_limited"]
    assert res.attempts == 3
    assert sleeper.calls == [1, 2]


def test_live_without_key_is_no_api_key_and_sends_nothing(jev, sleeper, scripted_urlopen):
    calls = scripted_urlopen()
    res = _judge_live(jev, sleeper, env={})
    assert res.verdict == "unverifiable"
    assert res.reasons == ["no_api_key"]
    assert res.attempts == 0
    assert calls == []


# --------------------------------------------------------------------------
# Replay transport [AC-2.2]
# --------------------------------------------------------------------------


def test_replay_key_is_sha256_of_canonical_body(jev, tmp_path, sleeper, no_network):
    digest = hashlib.sha256(_canonical(_typesafe_body())).hexdigest()
    (tmp_path / ("%s.json" % digest)).write_text(json.dumps(_ok_body()), encoding="utf-8")
    env = {"WRIT_JEV_REPLAY": str(tmp_path)}
    res = jev.judge(STATE, QUESTIONS, jev.BACKENDS["typesafe"], env, sleep=sleeper)
    assert res.verdict == "pass"
    assert res.input_tokens == 280
    assert no_network == []


def test_replay_miss(jev, tmp_path, sleeper, no_network):
    env = {"WRIT_JEV_REPLAY": str(tmp_path)}
    res = jev.judge(STATE, QUESTIONS, jev.BACKENDS["typesafe"], env, sleep=sleeper)
    assert res.verdict == "unverifiable"
    assert res.reasons == ["replay_miss"]
    assert no_network == []


def test_replay_dir_missing_is_replay_miss(jev, tmp_path, sleeper, no_network):
    env = {"WRIT_JEV_REPLAY": str(tmp_path / "nope")}
    res = jev.judge(STATE, QUESTIONS, jev.BACKENDS["typesafe"], env, sleep=sleeper)
    assert res.reasons == ["replay_miss"]


def test_replay_wins_over_injected_transport(jev, tmp_path, fake_http, sleeper, no_network):
    fake = fake_http()  # would IndexError if called
    env = {"WRIT_JEV_REPLAY": str(tmp_path), "TYPESAFE_API_KEY": FAKE_KEY}
    res = jev.judge(STATE, QUESTIONS, jev.BACKENDS["typesafe"], env, transport=fake, sleep=sleeper)
    assert res.reasons == ["replay_miss"]
    assert fake.calls == []
    assert no_network == []


def test_replay_needs_no_key(jev, sleeper, no_network):
    env = {"WRIT_JEV_REPLAY": str(REPLAY_DIR)}
    res = jev.judge(STATE, QUESTIONS, jev.BACKENDS["typesafe"], env, sleep=sleeper)
    assert res.verdict == "pass"
    assert no_network == []


def test_committed_fixture_typesafe(jev, sleeper, no_network):
    digest = hashlib.sha256(_canonical(_typesafe_body())).hexdigest()
    assert (REPLAY_DIR / ("%s.json" % digest)).is_file()
    env = {"WRIT_JEV_REPLAY": str(REPLAY_DIR)}
    res = jev.judge(STATE, QUESTIONS, jev.BACKENDS["typesafe"], env, sleep=sleeper)
    assert res.verdict == "pass"
    assert res.model == "jev-1.13.0"
    assert res.answers == {"q1": {"type": "noul", "noul": 0.01}}


def test_committed_fixture_gateway_records_cost(jev, sleeper, no_network):
    digest = hashlib.sha256(_canonical(_gateway_body())).hexdigest()
    assert (REPLAY_DIR / ("%s.json" % digest)).is_file()
    env = {"WRIT_JEV_REPLAY": str(REPLAY_DIR)}
    res = jev.judge(STATE, QUESTIONS, jev.BACKENDS["vercel-gateway"], env, sleep=sleeper)
    assert res.verdict == "pass"
    assert res.reasons == ["model_unpinned"]
    assert res.model == "typesafe-ai/jev"
    assert res.cost == "0.00001155"


def test_committed_probe_inputs_match_test_constants():
    assert json.loads((INPUTS_DIR / "state.json").read_text(encoding="utf-8")) == STATE
    assert json.loads((INPUTS_DIR / "questions.json").read_text(encoding="utf-8")) == QUESTIONS


# --------------------------------------------------------------------------
# Model pinning and response parsing [AC-2.3]
# --------------------------------------------------------------------------


@pytest.mark.parametrize("model", ["jev-1.14.0", "typesafe-ai/jev", None])
def test_typesafe_model_mismatch_discards_answers(jev, fake_http, sleeper, no_network, model):
    body = _ok_body(model=model or "x")
    if model is None:
        del body["model"]
    fake = fake_http((200, {}, body))
    res = _judge(jev, fake, sleeper)
    assert res.verdict == "unverifiable"
    assert res.reasons == ["model_mismatch"]
    assert res.answers is None


def test_gateway_does_not_check_model_but_marks_unpinned(jev, fake_http, sleeper, no_network):
    fake = fake_http((200, {}, _ok_body(model="typesafe-ai/jev")))
    res = _judge(jev, fake, sleeper, backend="vercel-gateway")
    assert res.verdict == "pass"
    assert res.reasons == ["model_unpinned"]
    assert res.answers is not None


@pytest.mark.parametrize(
    "body",
    [
        {"model": "jev-1.13.0"},
        {"model": "jev-1.13.0", "answers": []},
        {"model": "jev-1.13.0", "answers": {}},
        {"model": "jev-1.13.0", "answers": {"q1": {"type": "noul"}}},
        {"model": "jev-1.13.0", "answers": {"q1": {"type": "noul", "noul": "high"}}},
        {"model": "jev-1.13.0", "answers": {"q1": {"type": "noul", "noul": True}}},
        {"model": "jev-1.13.0", "answers": {"q1": "yes"}},
        {"model": "jev-1.13.0", "answers": {"other": {"type": "noul", "noul": 0.2}}},
        b"not json",
        b"\xff\xfe",
        [1, 2],
    ],
    ids=["no-answers", "answers-list", "answers-empty", "no-typed-field", "noul-string",
         "noul-bool", "answer-not-object", "missing-question-id", "not-json", "not-utf8",
         "not-object"],
)
def test_malformed_response_is_fail(jev, fake_http, sleeper, no_network, body):
    fake = fake_http((200, {}, body))
    res = _judge(jev, fake, sleeper)
    assert res.verdict == "fail"
    assert res.reasons == ["malformed_response"]
    assert res.answers is None


@pytest.mark.parametrize(
    "qtype,answer",
    [
        ("choice", {"type": "choice", "choice": "b", "probabilities": {"a": 0.1, "b": 0.9}, "confidence": 0.9}),
        ("score", {"type": "score", "score": 4, "probabilities": {}, "confidence": 0.7}),
    ],
)
def test_choice_and_score_answers_parse(jev, fake_http, sleeper, no_network, qtype, answer):
    questions = {"q1": {"type": qtype, "instructions": "Pick one."}}
    body = {"model": "jev-1.13.0", "answers": {"q1": answer}, "usage": {"input_tokens": 10}}
    fake = fake_http((200, {}, body))
    res = _judge(jev, fake, sleeper, questions=questions)
    assert res.verdict == "pass"
    assert res.answers == {"q1": answer}


@pytest.mark.parametrize("qtype", ["choice", "score"])
def test_choice_and_score_missing_typed_field_is_malformed(jev, fake_http, sleeper, no_network, qtype):
    questions = {"q1": {"type": qtype, "instructions": "Pick one."}}
    body = {"model": "jev-1.13.0", "answers": {"q1": {"type": qtype, "confidence": 0.5}}}
    fake = fake_http((200, {}, body))
    res = _judge(jev, fake, sleeper, questions=questions)
    assert res.verdict == "fail"
    assert res.reasons == ["malformed_response"]


def test_missing_usage_leaves_input_tokens_none(jev, fake_http, sleeper, no_network):
    body = _ok_body()
    del body["usage"]
    res = _judge(jev, fake_http((200, {}, body)), sleeper)
    assert res.verdict == "pass"
    assert res.input_tokens is None


# --------------------------------------------------------------------------
# State-size guard [AC-2.3]
# --------------------------------------------------------------------------


def _padded_state(chars: int) -> Dict[str, str]:
    # json.dumps({"p": "x"*n}) is n + 9 characters.
    return {"p": "x" * (chars - 9)}


def test_state_too_large_sends_nothing(jev, fake_http, sleeper, no_network):
    fake = fake_http()
    longest = max(len(json.dumps(q)) for q in QUESTIONS.values())
    state = _padded_state(30000 * 4 - longest + 1)  # estimate just over 30,000
    res = _judge(jev, fake, sleeper, state=state)
    assert res.verdict == "unverifiable"
    assert res.reasons == ["state_too_large"]
    assert res.attempts == 0
    assert fake.calls == []


def test_state_at_budget_is_sent(jev, fake_http, sleeper, no_network):
    fake = fake_http((200, {}, _ok_body()))
    longest = max(len(json.dumps(q)) for q in QUESTIONS.values())
    state = _padded_state(30000 * 4 - longest)  # estimate exactly 30,000
    res = _judge(jev, fake, sleeper, state=state)
    assert res.verdict == "pass"
    assert len(fake.calls) == 1


def test_estimate_uses_longest_question_not_sum(jev):
    q_short = {"type": "noul", "instructions": "a"}
    q_long = {"type": "noul", "instructions": "b" * 100}
    est = jev.estimate_tokens({"s": 1}, {"a": q_short, "b": q_long})
    assert est == (len(json.dumps({"s": 1})) + len(json.dumps(q_long))) / 4


def test_state_too_large_under_replay_also_skips(jev, tmp_path, sleeper, no_network):
    env = {"WRIT_JEV_REPLAY": str(tmp_path)}
    res = jev.judge(_padded_state(200000), QUESTIONS, jev.BACKENDS["typesafe"], env, sleep=sleeper)
    assert res.reasons == ["state_too_large"]


# --------------------------------------------------------------------------
# probe subcommand: verdict shape, summary fields, exit codes [AC-2.1, AC-2.3]
# --------------------------------------------------------------------------


def _probe_files(tmp_path, state=STATE, questions=QUESTIONS):
    s = tmp_path / "state.json"
    q = tmp_path / "questions.json"
    s.write_text(json.dumps(state), encoding="utf-8")
    q.write_text(json.dumps(questions), encoding="utf-8")
    return s, q


def _probe_inproc(jev, capsys, argv, env, transport=None, sleep=None):
    code = jev.main(argv, environ=env, transport=transport, sleep=sleep or (lambda _s: None))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _summary_fields(out: str) -> Dict[str, str]:
    return dict(tok.split("=", 1) for tok in _summary(out).split() if "=" in tok)


def test_probe_replay_typesafe_summary(jev, capsys, tmp_path, no_network):
    s, q = _probe_files(tmp_path)
    argv = ["probe", "--backend", "typesafe", "--state-file", str(s), "--questions-file", str(q)]
    code, out, _err = _probe_inproc(jev, capsys, argv, {"WRIT_JEV_REPLAY": str(REPLAY_DIR)})
    assert code == 0
    _assert_shape(out)
    assert _verdict(out) == "pass"
    fields = _summary_fields(out)
    assert fields["backend"] == "typesafe"
    assert fields["model"] == "jev-1.13.0"
    assert fields["input_tokens"] == "280"
    assert fields["attempts"] == "1"
    assert fields["answers"] == "1"
    assert "cost" not in fields
    assert no_network == []


def test_probe_replay_gateway_summary_has_cost(jev, capsys, tmp_path, no_network):
    s, q = _probe_files(tmp_path)
    argv = ["probe", "--backend", "vercel-gateway", "--state-file", str(s), "--questions-file", str(q)]
    code, out, _err = _probe_inproc(jev, capsys, argv, {"WRIT_JEV_REPLAY": str(REPLAY_DIR)})
    assert code == 0
    _assert_shape(out)
    assert _verdict(out) == "pass"
    assert _reasons(out) == ["model_unpinned"]
    fields = _summary_fields(out)
    assert fields["backend"] == "vercel-gateway"
    assert fields["model"] == "typesafe-ai/jev"
    assert fields["cost"] == "0.00001155"


def test_probe_429_then_success_shows_attempts_2(jev, capsys, tmp_path, fake_http, no_network):
    repo = _repo(tmp_path, "typesafe")
    s, q = _probe_files(tmp_path)
    fake = fake_http((429, {}, {}), (200, {}, _ok_body()))
    argv = ["probe", "--repo", str(repo), "--state-file", str(s), "--questions-file", str(q)]
    code, out, _err = _probe_inproc(jev, capsys, argv, {"TYPESAFE_API_KEY": FAKE_KEY}, transport=fake)
    assert code == 0
    assert _verdict(out) == "pass"
    assert _summary_fields(out)["attempts"] == "2"


@pytest.mark.parametrize(
    "outcomes,reason",
    [
        ([(401, {}, {"message": "no"})], "auth_error"),
        ([(422, {}, {"message": "bad"})], "request_invalid"),
        ([(429, {}, {})] * 3, "rate_limited"),
        ([(500, {}, {})], "transport_error"),
    ],
)
def test_probe_unverifiable_outcomes_exit_0(jev, capsys, tmp_path, fake_http, no_network, outcomes, reason):
    repo = _repo(tmp_path, "typesafe")
    s, q = _probe_files(tmp_path)
    fake = fake_http(*outcomes)
    argv = ["probe", "--repo", str(repo), "--state-file", str(s), "--questions-file", str(q)]
    code, out, _err = _probe_inproc(jev, capsys, argv, {"TYPESAFE_API_KEY": FAKE_KEY}, transport=fake)
    assert code == 0
    _assert_shape(out)
    assert _verdict(out) == "unverifiable"
    assert _reasons(out)[0] == reason
    assert "(%s)" % reason in _summary(out)


def test_probe_auth_error_names_key_var(jev, capsys, tmp_path, fake_http, no_network):
    repo = _repo(tmp_path, "vercel-gateway")
    s, q = _probe_files(tmp_path)
    fake = fake_http((401, {}, {"error": {"message": "bad", "type": "unauthorized"}}))
    argv = ["probe", "--repo", str(repo), "--state-file", str(s), "--questions-file", str(q)]
    code, out, err = _probe_inproc(jev, capsys, argv, {"VERCEL_OIDC_TOKEN": FAKE_KEY}, transport=fake)
    assert code == 0
    assert _reasons(out) == ["auth_error", "model_unpinned"]
    assert _summary_fields(out)["key_env"] == "VERCEL_OIDC_TOKEN"
    assert FAKE_KEY not in out + err


def test_probe_malformed_response_exits_1(jev, capsys, tmp_path, fake_http, no_network):
    repo = _repo(tmp_path, "typesafe")
    s, q = _probe_files(tmp_path)
    fake = fake_http((200, {}, {"model": "jev-1.13.0"}))
    argv = ["probe", "--repo", str(repo), "--state-file", str(s), "--questions-file", str(q)]
    code, out, _err = _probe_inproc(jev, capsys, argv, {"TYPESAFE_API_KEY": FAKE_KEY}, transport=fake)
    assert code == 1
    _assert_shape(out)
    assert _verdict(out) == "fail"
    assert _reasons(out) == ["malformed_response"]


def test_probe_model_mismatch_names_both_ids(jev, capsys, tmp_path, fake_http, no_network):
    repo = _repo(tmp_path, "typesafe")
    s, q = _probe_files(tmp_path)
    fake = fake_http((200, {}, _ok_body(model="jev-1.14.0")))
    argv = ["probe", "--repo", str(repo), "--state-file", str(s), "--questions-file", str(q)]
    code, out, _err = _probe_inproc(jev, capsys, argv, {"TYPESAFE_API_KEY": FAKE_KEY}, transport=fake)
    assert code == 0
    assert _reasons(out) == ["model_mismatch"]
    fields = _summary_fields(out)
    assert fields["model"] == "jev-1.14.0"
    assert fields["expected"] == "jev-1.13.0"


def test_probe_state_too_large_sends_nothing(jev, capsys, tmp_path, fake_http, no_network):
    repo = _repo(tmp_path, "typesafe")
    s, q = _probe_files(tmp_path, state=_padded_state(200000))
    fake = fake_http()
    argv = ["probe", "--repo", str(repo), "--state-file", str(s), "--questions-file", str(q)]
    code, out, _err = _probe_inproc(jev, capsys, argv, {"TYPESAFE_API_KEY": FAKE_KEY}, transport=fake)
    assert code == 0
    assert _reasons(out) == ["state_too_large"]
    assert _summary_fields(out)["attempts"] == "0"
    assert "input_tokens" not in _summary_fields(out)
    assert fake.calls == []


def test_probe_replay_miss(jev, capsys, tmp_path, no_network):
    s, q = _probe_files(tmp_path, state={"different": True})
    argv = ["probe", "--backend", "typesafe", "--state-file", str(s), "--questions-file", str(q)]
    code, out, _err = _probe_inproc(jev, capsys, argv, {"WRIT_JEV_REPLAY": str(REPLAY_DIR)})
    assert code == 0
    assert _verdict(out) == "unverifiable"
    assert _reasons(out) == ["replay_miss"]
    assert no_network == []


# Double opt-in holds for probe: live sends only when status would pass. [BR 1]


@pytest.mark.parametrize(
    "provider,config,env,reason",
    [
        (None, False, {k: FAKE_KEY for k in KEY_VARS}, "no_config_line"),
        ("none", True, {k: FAKE_KEY for k in KEY_VARS}, "provider_disabled"),
        ("typesafe", True, {}, "no_api_key"),
    ],
)
def test_probe_live_requires_double_opt_in(jev, capsys, tmp_path, fake_http, no_network,
                                            provider, config, env, reason):
    repo = _repo(tmp_path, provider, config=config)
    s, q = _probe_files(tmp_path)
    fake = fake_http()
    argv = ["probe", "--repo", str(repo), "--state-file", str(s), "--questions-file", str(q)]
    code, out, err = _probe_inproc(jev, capsys, argv, env, transport=fake)
    assert code == 0
    _assert_shape(out)
    assert _verdict(out) == "unverifiable"
    assert _reasons(out)[0] == reason
    assert fake.calls == []
    assert FAKE_KEY not in out + err


def test_probe_backend_flag_without_replay_is_usage(jev, capsys, tmp_path, no_network):
    s, q = _probe_files(tmp_path)
    argv = ["probe", "--backend", "typesafe", "--state-file", str(s), "--questions-file", str(q)]
    code, _out, err = _probe_inproc(jev, capsys, argv, {"TYPESAFE_API_KEY": FAKE_KEY})
    assert code == 2
    assert "--backend" in err


def test_probe_replay_without_backend_uses_config(jev, capsys, tmp_path, no_network):
    repo = _repo(tmp_path, "vercel-gateway")
    s, q = _probe_files(tmp_path)
    argv = ["probe", "--repo", str(repo), "--state-file", str(s), "--questions-file", str(q)]
    code, out, _err = _probe_inproc(jev, capsys, argv, {"WRIT_JEV_REPLAY": str(REPLAY_DIR)})
    assert code == 0
    assert _summary_fields(out)["backend"] == "vercel-gateway"


def test_probe_replay_without_backend_or_config_is_no_config_line(jev, capsys, tmp_path, no_network):
    repo = _repo(tmp_path, None)
    s, q = _probe_files(tmp_path)
    argv = ["probe", "--repo", str(repo), "--state-file", str(s), "--questions-file", str(q)]
    code, out, _err = _probe_inproc(jev, capsys, argv, {"WRIT_JEV_REPLAY": str(REPLAY_DIR)})
    assert code == 0
    assert _reasons(out) == ["no_config_line"]


@pytest.mark.parametrize(
    "state_text,questions_text",
    [
        ("not json", json.dumps(QUESTIONS)),
        ("[1]", json.dumps(QUESTIONS)),
        (json.dumps(STATE), "{}"),
        (json.dumps(STATE), "[]"),
        (json.dumps(STATE), json.dumps({"q1": "text"})),
        (json.dumps(STATE), json.dumps({"q1": {"instructions": "no type"}})),
    ],
)
def test_probe_bad_input_files_exit_2(jev, capsys, tmp_path, no_network, state_text, questions_text):
    s = tmp_path / "s.json"
    q = tmp_path / "q.json"
    s.write_text(state_text, encoding="utf-8")
    q.write_text(questions_text, encoding="utf-8")
    argv = ["probe", "--backend", "typesafe", "--state-file", str(s), "--questions-file", str(q)]
    code, _out, _err = _probe_inproc(jev, capsys, argv, {"WRIT_JEV_REPLAY": str(REPLAY_DIR)})
    assert code == 2


def test_probe_missing_input_file_exits_2(jev, capsys, tmp_path, no_network):
    argv = ["probe", "--backend", "typesafe", "--state-file", str(tmp_path / "no.json"),
            "--questions-file", str(tmp_path / "no.json")]
    code, _out, _err = _probe_inproc(jev, capsys, argv, {"WRIT_JEV_REPLAY": str(REPLAY_DIR)})
    assert code == 2


# --------------------------------------------------------------------------
# Key never printed: echo transport reflects request headers [BR 1, AC-1.4]
# --------------------------------------------------------------------------


FORGE = "\nfail\nreason: forged\njev-judge: pass (forged)"


def _echo_transport(jev, status, model=None, cost=None):
    """Fake server that reflects the request headers back.

    `model` / `cost` are templates: `{auth}` becomes the echoed Authorization
    header, `{key}` the bare key (charset-valid, so only the key check stops
    it). None keeps a benign value.
    """
    def _transport(url, headers, payload):
        echoed = dict(headers)
        auth = echoed.get("Authorization", "")
        key = auth[len("Bearer "):]

        def fill(t):
            return t.replace("{auth}", auth).replace("{key}", key)

        body = {
            "model": fill(model or "jev-1.13.0"),
            "message": "echo %r" % echoed,
            "error_type": "echo %r" % echoed,
            "echo": echoed,
        }
        if cost is not None:
            body["provider_metadata"] = {"gateway": {"cost": fill(cost)
                                                     if isinstance(cost, str) else cost}}
        if status == 200:
            body["answers"] = {"q1": {"type": "noul", "noul": 0.5, "echo": echoed}}
            body["usage"] = {"input_tokens": 1}
        return jev.HttpResponse(status, {"x-echo-auth": auth},
                                json.dumps(body).encode("utf-8"))
    return _transport


def _probe_echo(jev, capsys, tmp_path, backend, transport):
    repo = _repo(tmp_path, backend)
    s, q = _probe_files(tmp_path)
    env = {"TYPESAFE_API_KEY": FAKE_KEY, "AI_GATEWAY_API_KEY": FAKE_KEY}
    argv = ["probe", "--repo", str(repo), "--state-file", str(s), "--questions-file", str(q)]
    return _probe_inproc(jev, capsys, argv, env, transport=transport)


def _assert_contract_intact(out: str, err: str) -> None:
    """No key anywhere; exactly one verdict line, first; summary last; no forged lines."""
    assert FAKE_KEY not in out
    assert FAKE_KEY not in err
    _assert_shape(out)
    lines = out.strip().splitlines()
    assert sum(ln in ("pass", "fail", "unverifiable") for ln in lines) == 1
    assert "forged" not in out
    # stderr is merged into eval notes (2>&1): it must not forge lines either.
    for ln in err.splitlines():
        assert ln.startswith("jev-judge:") or ln.startswith("error:"), err


@pytest.mark.parametrize("status", [200, 401, 404, 422, 429, 500])
def test_probe_never_prints_key_even_when_server_echoes_it(jev, capsys, tmp_path, no_network, status):
    code, out, err = _probe_echo(jev, capsys, tmp_path, "typesafe", _echo_transport(jev, status))
    assert code in (0, 1)
    _assert_contract_intact(out, err)
    _assert_key_absent(tmp_path, out, err)


@pytest.mark.parametrize(
    "backend,model,cost,expect",
    [
        # typesafe: a hostile model takes the model_mismatch path (expected= printed).
        ("typesafe", "x-{auth}", None, "model=invalid"),
        ("typesafe", "x-{key}", None, "model=invalid"),
        ("typesafe", "jev-1.14.0" + FORGE, None, "model=invalid"),
        ("typesafe", "{auth}" + FORGE, None, "model=invalid"),
        ("typesafe", "m" * 65, None, "model=invalid"),
        # gateway: model is not checked, so it reaches the pass summary.
        ("vercel-gateway", "x-{auth}", None, "model=invalid"),
        ("vercel-gateway", "x-{key}", None, "model=invalid"),
        ("vercel-gateway", "{key}", None, "model=invalid"),
        ("vercel-gateway", "typesafe-ai/jev", "{key}", "cost=invalid"),
        ("vercel-gateway", "typesafe-ai/jev" + FORGE, None, "model=invalid"),
        ("vercel-gateway", "typesafe-ai/jev", "{auth}", "cost=invalid"),
        ("vercel-gateway", "typesafe-ai/jev", "0.01" + FORGE, "cost=invalid"),
        ("vercel-gateway", "typesafe-ai/jev", "0.01 {auth}", "cost=invalid"),
        ("vercel-gateway", "typesafe-ai/jev", {"nested": "{auth}"}, "cost=invalid"),
    ],
)
def test_hostile_model_or_cost_cannot_leak_key_or_forge_lines(
    jev, capsys, tmp_path, no_network, backend, model, cost, expect
):
    code, out, err = _probe_echo(jev, capsys, tmp_path, backend,
                                 _echo_transport(jev, 200, model=model, cost=cost))
    assert code == 0
    _assert_contract_intact(out, err)
    assert expect in _summary(out).split()
    _assert_key_absent(tmp_path, out, err)


def test_typesafe_hostile_model_is_still_a_mismatch(jev, capsys, tmp_path, no_network):
    code, out, _err = _probe_echo(jev, capsys, tmp_path, "typesafe",
                                  _echo_transport(jev, 200, model="x-{auth}"))
    assert code == 0
    assert _reasons(out) == ["model_mismatch"]
    fields = _summary_fields(out)
    assert fields["model"] == "invalid"
    assert fields["expected"] == "jev-1.13.0"


def test_judgment_carries_sanitized_model_and_cost(jev, fake_http, sleeper, no_network):
    body = _ok_body(model="typesafe-ai/jev\nfail",
                    provider_metadata={"gateway": {"cost": "1\n2"}})
    res = _judge(jev, fake_http((200, {}, body)), sleeper, backend="vercel-gateway")
    assert res.model == "invalid"
    assert res.cost == "invalid"


@pytest.mark.parametrize("value,expected", [
    ("jev-1.13.0", "jev-1.13.0"),
    ("typesafe-ai/jev", "typesafe-ai/jev"),
    ("0.00001155", "0.00001155"),
    ("a:b_c.d-e/f", "a:b_c.d-e/f"),
    ("x" * 64, "x" * 64),
    ("x" * 65, "invalid"),
    ("", "invalid"),
    ("has space", "invalid"),
    ("tab\there", "invalid"),
    ("unié", "invalid"),
    ("new\nline", "invalid"),
    (0.5, "0.5"),
    ({"a": 1}, "invalid"),
    (True, "invalid"),
])
def test_safe_token_charset(jev, value, expected):
    assert jev._safe_token(value, None) == expected


def test_safe_token_rejects_embedded_key(jev):
    assert jev._safe_token("x-%s" % FAKE_KEY, FAKE_KEY) == "invalid"
    assert jev._safe_token(FAKE_KEY, FAKE_KEY) == "invalid"


@pytest.mark.parametrize("status", [404, 422])
def test_error_body_with_newlines_cannot_forge_stderr_lines(jev, fake_http, sleeper, capsys,
                                                             no_network, status):
    body = {"error": {"message": "bad" + FORGE, "type": "model_not_found" + FORGE}}
    _judge(jev, fake_http((status, {}, body)), sleeper)
    err = capsys.readouterr().err
    lines = err.splitlines()
    assert len(lines) == 2
    assert all(ln.startswith("jev-judge: ") for ln in lines), err
    assert "fail" not in lines


def test_echo_malformed_body_does_not_leak_key(jev, capsys, tmp_path, no_network):
    """A 200 with no answers whose raw text carries the key."""
    repo = _repo(tmp_path, "typesafe")
    s, q = _probe_files(tmp_path)

    def _transport(url, headers, payload):
        return jev.HttpResponse(200, {}, ("garbage %s" % headers).encode("utf-8"))

    argv = ["probe", "--repo", str(repo), "--state-file", str(s), "--questions-file", str(q)]
    code, out, err = _probe_inproc(jev, capsys, argv, {"TYPESAFE_API_KEY": FAKE_KEY}, transport=_transport)
    assert code == 1
    assert FAKE_KEY not in out + err


# --------------------------------------------------------------------------
# Subprocess probe: replay only, no key, network poisoned [AC-2.2]
# --------------------------------------------------------------------------


def _poisoned_env(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    env = _clean_env(extra)
    # Any live attempt would go to a dead proxy and fail, never connect.
    for var in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        env[var] = "http://127.0.0.1:9"
    env.pop("NO_PROXY", None)
    env.pop("no_proxy", None)
    return env


@pytest.mark.parametrize("backend", ["typesafe", "vercel-gateway"])
def test_subprocess_probe_replay_without_key(tmp_path, backend):
    env = _poisoned_env({"WRIT_JEV_REPLAY": str(REPLAY_DIR)})
    code, out, err = _run(
        ["probe", "--backend", backend, "--state-file", str(INPUTS_DIR / "state.json"),
         "--questions-file", str(INPUTS_DIR / "questions.json")],
        env, cwd=tmp_path,
    )
    assert code == 0, err
    _assert_shape(out)
    assert _verdict(out) == "pass"
    assert "backend=%s" % backend in _summary(out)
    assert "attempts=1" in _summary(out)


def test_subprocess_probe_replay_wins_over_configured_live(tmp_path):
    repo = _repo(tmp_path, "typesafe")
    env = _poisoned_env({"WRIT_JEV_REPLAY": str(REPLAY_DIR), "TYPESAFE_API_KEY": FAKE_KEY})
    code, out, err = _run(
        ["probe", "--repo", str(repo), "--state-file", str(INPUTS_DIR / "state.json"),
         "--questions-file", str(INPUTS_DIR / "questions.json")],
        env,
    )
    assert code == 0, err
    assert _verdict(out) == "pass"  # served from replay, not the dead proxy
    _assert_key_absent(repo, out, err)


# --------------------------------------------------------------------------
# Thresholds file and loader [AC-2.5]
# --------------------------------------------------------------------------

SHIPPED_THRESHOLDS = {
    "backend": None,
    "model": None,
    "calibrated": False,
    "calibrated_on": None,
    "spec_findings": {
        "contradiction": {"emit": 0.85, "escalate": 0.35},
        "gap": {"emit": 0.85, "escalate": 0.35},
        "ambiguity": {"emit": 0.85, "escalate": 0.35},
    },
    "ac_shadow": {"satisfied": 0.9},
}


def test_shipped_thresholds_match_technical_spec():
    assert json.loads(THRESHOLDS.read_text(encoding="utf-8")) == SHIPPED_THRESHOLDS


def test_loader_reads_shipped_file_with_no_reasons(jev):
    values, reasons = jev.load_thresholds(backend="typesafe", model="jev-1.13.0")
    assert values == SHIPPED_THRESHOLDS
    assert reasons == []


def test_loader_uncalibrated_file_never_reports_mismatch(jev, tmp_path):
    path = tmp_path / "t.json"
    path.write_text(json.dumps(SHIPPED_THRESHOLDS), encoding="utf-8")
    _values, reasons = jev.load_thresholds(path, backend="vercel-gateway", model="typesafe-ai/jev")
    assert reasons == []


def _calibrated(tmp_path, backend="typesafe", model="jev-1.13.0"):
    data = dict(SHIPPED_THRESHOLDS, calibrated=True, backend=backend, model=model,
                calibrated_on="2026-10-01")
    data["spec_findings"] = {"contradiction": {"emit": 0.9, "escalate": 0.2},
                             "gap": {"emit": 0.8, "escalate": 0.3},
                             "ambiguity": {"emit": 0.7, "escalate": 0.4}}
    path = tmp_path / "t.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path, data


def test_loader_calibrated_match_has_no_reasons(jev, tmp_path):
    path, data = _calibrated(tmp_path)
    values, reasons = jev.load_thresholds(path, backend="typesafe", model="jev-1.13.0")
    assert values == data
    assert reasons == []


@pytest.mark.parametrize(
    "backend,model",
    [("vercel-gateway", "jev-1.13.0"), ("typesafe", "jev-1.14.0"), ("vercel-gateway", "typesafe-ai/jev")],
)
def test_loader_calibrated_mismatch_reports_and_keeps_values(jev, tmp_path, backend, model):
    path, data = _calibrated(tmp_path)
    values, reasons = jev.load_thresholds(path, backend=backend, model=model)
    assert reasons == ["uncalibrated_thresholds"]
    assert values == data  # kept, not reset to defaults


def test_loader_missing_file_uses_shipped_defaults_and_says_so(jev, tmp_path):
    values, reasons = jev.load_thresholds(tmp_path / "absent.json", backend="typesafe", model="jev-1.13.0")
    assert values == SHIPPED_THRESHOLDS
    assert reasons == ["thresholds_missing"]  # informational: a lost calibrated file shows up


@pytest.mark.parametrize("text", ["not json", "[]", '{"calibrated": false}'])
def test_loader_invalid_file_raises(jev, tmp_path, text):
    path = tmp_path / "t.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(jev.ThresholdsError):
        jev.load_thresholds(path, backend="typesafe", model="jev-1.13.0")


def test_transport_code_imports_only_stdlib():
    """BR 9: no requests, no SDK."""
    import ast
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    assert not names & {"requests", "httpx", "typesafe_sdk", "typesafe", "aiohttp", "urllib3"}

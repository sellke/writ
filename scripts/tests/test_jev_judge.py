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


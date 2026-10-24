"""scripts/eval-platform-facts.py: exit status and skip rules, with no CLI or
model call. The facts themselves are checked by running the script."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "eval-platform-facts.py"


@pytest.fixture
def facts(monkeypatch):
    spec = importlib.util.spec_from_file_location("eval_platform_facts", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod.shutil, "which", lambda cli: "/bin/" + cli if cli != "missing" else None)
    monkeypatch.setattr(mod, "run", lambda args, cwd=None, timeout=300: "x 1.0")
    return mod


def table(mod, rows, monkeypatch):
    monkeypatch.setattr(mod, "FACTS", rows)


def test_holds_exits_0(facts, monkeypatch, capsys):
    table(facts, [("A", "claude", "row", "fact", False, lambda: ("seen", True))], monkeypatch)
    assert facts.main([]) == 0
    assert "| A | fact | holds | seen |" in capsys.readouterr().out


def test_changed_exits_1(facts, monkeypatch, capsys):
    table(facts, [("A", "claude", "row", "fact", False, lambda: ("other", False))], monkeypatch)
    assert facts.main([]) == 1
    assert "| A | fact | changed | other |" in capsys.readouterr().out


def test_missing_cli_and_offline_live_fact_are_unverifiable(facts, monkeypatch, capsys):
    def boom():
        raise AssertionError("must not run")
    table(facts, [("A", "missing", "row", "fact a", False, boom),
                  ("B", "claude", "row", "fact b", True, boom)], monkeypatch)
    assert facts.main([]) == 0
    out = capsys.readouterr().out
    assert "| A | fact a | unverifiable | missing not installed |" in out
    assert "| B | fact b | unverifiable | needs --live |" in out


def test_every_fact_names_its_adapter_row(facts):
    for fid, cli, row, statement, live, check in facts.FACTS:
        assert row and statement and callable(check), fid

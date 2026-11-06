"""Regression for Story 2 of `2026-11-06-pr-ready-and-ledger`: a headRefOid
that is not exactly 40 lowercase hex is a snapshot that cannot be judged [AC-2.3]."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "pr-ready.py"
CLEAN = Path(__file__).resolve().parent / "fixtures" / "pr-ready" / "clean.json"


def test_head_with_trailing_newline_exits_2(tmp_path):
    snap = json.loads(CLEAN.read_text(encoding="utf-8"))
    snap["view"]["headRefOid"] += "\n"
    snap["threads"]["data"]["repository"]["pullRequest"]["headRefOid"] += "\n"
    path = tmp_path / "snap.json"
    path.write_text(json.dumps(snap), encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), "check", "--snapshot", str(path),
                             "--repo", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 2, result.stdout
    assert result.stdout == ""

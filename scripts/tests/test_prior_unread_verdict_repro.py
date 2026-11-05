import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "review-override.py"
REPRO = "def test_kept():\n    assert True\n"


def test_prior_does_not_pass_a_verdict_it_cannot_read():
    """AC-4.2: only a PASS or PAUSE verdict runs the prior checks alone. A
    verdict line the script cannot read stays `verdict_not_fail`, with or
    without `--prior`, so Gate 3 row 9 cannot turn the agent's FAIL into PASS."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = root / "repo"
        (repo / "tests").mkdir(parents=True)
        (repo / "tests" / "test_kept_repro.py").write_text(REPRO, encoding="utf-8")
        (root / "review.md").write_text(
            "**REVIEW_RESULT:** FAIL\n\n### Summary\nOne issue.\n", encoding="utf-8")
        (root / "evidence.json").write_text(json.dumps({
            "schema": "evidence-manifest-v1", "story": "story-1-x",
            "repros": [{"finding": "F1", "path": "tests/test_kept_repro.py",
                        "sha256": hashlib.sha256(REPRO.encode("utf-8")).hexdigest(),
                        "kind": "test", "location": "src/a.py:1"}],
        }), encoding="utf-8")
        (root / "tests.txt").write_text(
            "command: pytest tests/test_kept_repro.py\nexit code: 0\n", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "evidence", "--review-output", str(root / "review.md"),
             "--repo", str(repo), "--changed", "tests/test_kept_repro.py",
             "--tests-output", str(root / "tests.txt"), "--prior", str(root / "evidence.json")],
            capture_output=True, text=True, env=env, cwd=str(root))
        lines = proc.stdout.splitlines()
        assert lines[:2] == ["unverifiable", "reason: verdict_not_fail none"], proc.stdout

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "review-override.py"
TICKS = "`" * 3
REVIEW = "\n".join([
    "### REVIEW_RESULT: FAIL",
    "",
    "### Issues Found",
    "",
    "- **Issue:** `parse_limit()` accepts a negative limit",
    "- **Location:** `src/limits.py:1`",
    "- **Severity:** Major",
    "- **Category:** criterion [AC-1.1]",
    "- **Evidence:** test `tests/test_new_repro.py`",
    "  " + TICKS + "python",
    "  def test_new():",
    "      assert False",
    "  " + TICKS,
    "",
])
MANIFEST = {
    "schema": "evidence-manifest-v1",
    "story": "story-1-x",
    "repros": [{"finding": "F1", "path": "tests/test_gone_repro.py", "sha256": "0" * 64,
                "kind": "test", "location": "src/limits.py:1"}],
}


def test_prior_repro_removed_survives_a_missing_runner_binary():
    """AC-4.2: on a FAIL verdict, a removed manifest repro gives line 1 `fail`
    with `reason: repro_removed`, even when a new `test` finding's runner
    binary is missing."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = root / "repo"
        (repo / ".writ").mkdir(parents=True)
        (repo / ".writ" / "config.md").write_text(
            "- **Test Runner:** /nonexistent/bin/pytest\n", encoding="utf-8")
        (repo / "src").mkdir()
        (repo / "src" / "limits.py").write_text("LIMIT = 1\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True, env=env)
        (root / "review.md").write_text(REVIEW, encoding="utf-8")
        (root / "evidence.json").write_text(json.dumps(MANIFEST), encoding="utf-8")
        (root / "tests.txt").write_text("command: pytest\nexit code: 0\n", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "evidence", "--review-output", str(root / "review.md"),
             "--repo", str(repo), "--changed", "src/limits.py",
             "--tests-output", str(root / "tests.txt"), "--prior", str(root / "evidence.json")],
            capture_output=True, text=True, env=env, cwd=str(root))
        lines = proc.stdout.splitlines()
        assert lines[:1] == ["fail"], proc.stdout
        assert "reason: repro_removed tests/test_gone_repro.py" in lines, proc.stdout
        assert proc.returncode == 1, proc.stdout

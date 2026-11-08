from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_in_pass_step_6_is_given_the_landed_sha():
    """After `gh pr merge`, the pass has not fetched since 7.5, so Step 6.1's
    `git rev-parse origin/<base>` reads pre_merge_base. The merge step must hand
    Step 6 the read-back mergeCommit, or fetch first."""
    text = (ROOT / "commands" / "ship.md").read_text(encoding="utf-8")
    start = text.index("**Merge step.**")
    step = text[start:text.index("\n**7.7", start)]
    line = next(l for l in step.splitlines() if l.startswith("7. "))
    assert "landed SHA" in line or "git fetch origin" in line, line

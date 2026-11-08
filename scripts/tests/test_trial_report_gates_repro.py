from pathlib import Path

_SPECS = Path(__file__).resolve().parents[2] / ".writ" / "specs"
# An archived spec moves under specs/archive/; follow it.
REPORT = next((d / "2026-11-06-lean-story-pipeline" / "trial-report.md" for d in (_SPECS, _SPECS / "archive")
               if (d / "2026-11-06-lean-story-pipeline").is_dir()),
              _SPECS / "2026-11-06-lean-story-pipeline" / "trial-report.md")


def test_arm_after_gates_row_names_post_review_failures():
    # arm-after story 1 stream: story-gate post-review returned
    # "fail (phase post-review, 9 checks, 1 fail, ...)" twice before it passed.
    for line in REPORT.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].lower().startswith("gates failed or stopped"):
            assert "post-review" in cells[2].lower(), cells[2]
            return
    raise AssertionError("no 'Gates failed or stopped' row")

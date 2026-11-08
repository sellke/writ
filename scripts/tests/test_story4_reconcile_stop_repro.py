from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]


class ReconcileStopSurvivesCompression(unittest.TestCase):
    def test_resume_continues_only_when_state_and_git_agree(self):
        text = (REPO_ROOT / "commands" / "implement-phase.md").read_text(encoding="utf-8")
        begin = text.index("#### Step 3.3:")
        step = text[begin:text.index("#### Step 3.4:", begin)]
        row = next(line for line in step.splitlines() if "`reconcile`" in line)
        self.assertRegex(row.lower(), r"continu\w* only (if|when)|\bstop|\bhalt")

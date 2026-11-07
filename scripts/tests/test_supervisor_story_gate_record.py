#!/usr/bin/env python3
"""The supervisor reads the story-gate record (2026-11-06-lean-story-pipeline
Story 5, Business Rule 5).

The supervisor takes an optional `story_gate_record` input, returns `RERUN`
when the post-review record is missing, unreadable, stale against the story's
final code commit, or written on a dirty tree, marks a report's check-verdict
claim false when the record disagrees, and reads the three checkers' verdicts
from the record instead of re-running them. `implement-spec.md` drops Step 2.3
and its per-story `.writ/context.md` regeneration, and passes the record path.

Pins key phrases, not whole paragraphs, so later prose edits break only the
rule they change. Reads source files and generated copies as text, runs
`gen-platform-trees.py --check` (writes nothing), and builds a throwaway git
repo under a temp dir to check the final-code-commit command.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR = REPO_ROOT / "agents" / "supervisor-agent.md"
IMPLEMENT_SPEC = REPO_ROOT / "commands" / "implement-spec.md"
GOVERNOR_TEST = REPO_ROOT / "scripts" / "tests" / "test_governor_enforcement.py"
GEN_TREES = REPO_ROOT / "scripts" / "gen-platform-trees.py"
LEANNESS = REPO_ROOT / "scripts" / "eval-leanness.py"

# AC-5.1: the input and the missing-record rule.
INPUT_ROW = "| `story_gate_record` | **Optional.**"
RECORD_PATH = ".writ/state/story-gate-<story-stem>-post-review.json"
CLAIM_MISSING = "`story-gate record missing`"
CLAIM_UNREADABLE = "`story-gate record unreadable`"
# AC-5.2: head mismatch and dirty tree.
CLAIM_HEAD = "`story-gate record head <sha> ≠ final code commit <sha>`"
CLAIM_DIRTY = "`story-gate record written on a dirty tree`"
FINAL_CODE_COMMIT = (
    "the last commit in `{base_commit}..{head_ref}` that touches a file "
    "outside `.writ/`"
)
FINAL_CODE_COMMIT_CMD = (
    "git log -1 --format=%H {base_commit}..{head_ref} -- . ':(exclude).writ'"
)
# AC-5.3: the record decides check-verdict claims; no checker re-runs.
DISAGREE_RULE = "A report claim about a check's verdict that disagrees with the record is false."
NO_RERUN_RULE = (
    "Do not re-run `review-override.py`, `test-integrity.py`, or "
    "`drift-format.py`: read their verdicts from the record."
)
SKIP_RULE = "`skip` means the check did not apply"
RETIRED_RERUN = "python3 scripts/drift-format.py check --story"

# AC-5.4: implement-spec.md cuts.
STEP_23 = "#### Step 2.3: Estimate Scope"
STEP_23B = "#### Step 2.3b: Pre-Flight Assessment"
STEP_33 = "#### Step 3.3: Update State After Each Story"
REGEN_BULLET = "**Regenerate `.writ/context.md`**"
SPAWN_RECORD = "`story_gate_record`: `" + RECORD_PATH + "`"
POSTRUN_FIELDS = "`postRun: {typecheck, testSuite, contextRewritten, at}`"
CONTEXT_SOURCE = "`contextRewritten` is a boolean: `true` when `implement-story` Step 4"
# Carry-forwards from Story 2 and 4 reviews.
STALE_PHASES = "arch-check → code → lint → review → test → docs"
STALE_GATE4_RUN = "Per-story tests already ran in each `/implement-story` Gate 4"

GENERATED = {
    SUPERVISOR: (
        "claude-code/agents/writ-supervisor.md",
        "cursor/plugin/agents/supervisor-agent.md",
        "codex/agents/supervisor-agent.toml",
        "plugins/writ/agents/supervisor-agent.md",
        "plugins/writ/agents/writ-supervisor.md",
    ),
    IMPLEMENT_SPEC: (
        "cursor/plugin/commands/implement-spec.md",
        "plugins/writ/commands/implement-spec.md",
    ),
}
PINS = {
    SUPERVISOR: (INPUT_ROW, CLAIM_MISSING, CLAIM_HEAD, CLAIM_DIRTY,
                 FINAL_CODE_COMMIT, DISAGREE_RULE, NO_RERUN_RULE),
    IMPLEMENT_SPEC: (SPAWN_RECORD, POSTRUN_FIELDS, CONTEXT_SOURCE),
}

# implement-spec.md before this story; the cuts must not grow it.
IMPLEMENT_SPEC_BYTES_BEFORE = 22192


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    return text[i : text.index(end, i + len(start))]


def prompt(text: str) -> str:
    return section(text, "## Prompt Template", "## Output Examples")


def story_gate_rules(text: str) -> str:
    return section(prompt(text), "## Story-gate record", "\n## ")


class SupervisorInput(unittest.TestCase):
    """AC-5.1"""

    def test_ac51_declares_optional_story_gate_record_input(self) -> None:
        """AC-5.1: the input table declares optional `story_gate_record`."""
        text = read(SUPERVISOR)
        inputs = section(text, "## Input Requirements", "## Prompt Template")
        self.assertIn(INPUT_ROW, inputs)
        self.assertIn(RECORD_PATH, inputs)
        self.assertIn("{story_gate_record}", prompt(text))

    def test_ac51_missing_record_in_any_mode_is_a_false_claim_and_rerun(self) -> None:
        """AC-5.1: a missing record, `--quick` included, is false → RERUN."""
        rules = story_gate_rules(read(SUPERVISOR))
        self.assertIn(CLAIM_MISSING, rules)
        self.assertIn("any mode, `--quick` included", rules)
        line = next(x for x in rules.splitlines() if CLAIM_MISSING in x)
        self.assertIn("`false`", line)
        self.assertIn("RERUN", line)

    def test_ac51_unknown_schema_is_unreadable_and_rerun(self) -> None:
        """AC-5.1 (Error map, Supervisor read): an unknown schema → RERUN."""
        rules = story_gate_rules(read(SUPERVISOR))
        line = next(x for x in rules.splitlines() if CLAIM_UNREADABLE in x)
        self.assertIn("`story-gate-v1`", line)
        self.assertIn("RERUN", line)


class SupervisorHeadAndDirty(unittest.TestCase):
    """AC-5.2"""

    def test_ac52_head_mismatch_names_both_shas_and_reruns(self) -> None:
        """AC-5.2: `head_sha` ≠ final code commit → named false claim, RERUN."""
        rules = story_gate_rules(read(SUPERVISOR))
        line = next(x for x in rules.splitlines() if CLAIM_HEAD in x)
        self.assertIn("`head_sha`", line)
        self.assertIn("RERUN", line)

    def test_ac52_dirty_flag_reruns(self) -> None:
        """AC-5.2: `dirty: true` → named false claim, RERUN."""
        rules = story_gate_rules(read(SUPERVISOR))
        line = next(x for x in rules.splitlines() if CLAIM_DIRTY in x)
        self.assertIn("`dirty`", line)
        self.assertIn("RERUN", line)

    def test_ac52_final_code_commit_is_defined_with_a_command(self) -> None:
        """AC-5.2: the final code commit skips `.writ/`-only commits."""
        rules = story_gate_rules(read(SUPERVISOR))
        self.assertIn(FINAL_CODE_COMMIT, rules)
        self.assertIn(FINAL_CODE_COMMIT_CMD, rules)

    def test_ac52_final_code_commit_command_skips_writ_only_commits(self) -> None:
        """AC-5.2: the pinned command returns the code commit, not the
        story-completion or SHA-record commits after it, and moves when the
        coder commits code again (Interaction Edge Case)."""
        env = dict(os.environ, GIT_AUTHOR_NAME="T", GIT_AUTHOR_EMAIL="t@example.com",
                   GIT_COMMITTER_NAME="T", GIT_COMMITTER_EMAIL="t@example.com")

        def git(repo: Path, *args: str) -> str:
            return subprocess.run(
                ["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args],
                env=env, capture_output=True, text=True, check=True,
            ).stdout.strip()

        def commit(repo: Path, rel: str, msg: str) -> str:
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(msg + "\n", encoding="utf-8")
            git(repo, "add", rel)
            git(repo, "commit", "-q", "-m", msg)
            return git(repo, "rev-parse", "HEAD")

        def final_code_commit(repo: Path, base: str) -> str:
            argv = ["log", "-1", "--format=%H", base + "..HEAD", "--", ".", ":(exclude).writ"]
            return git(repo, *argv)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-q")
            base = commit(repo, "README.md", "base")
            code = commit(repo, "src/a.py", "feat: code")
            commit(repo, ".writ/specs/s/user-stories/story-1.md", "docs: complete story")
            commit(repo, ".writ/specs/s/user-stories/story-1.md", "chore: record sha")
            self.assertEqual(final_code_commit(repo, base), code)
            later = commit(repo, "src/a.py", "fix: after post-review")
            self.assertEqual(final_code_commit(repo, base), later)


class SupervisorReadsVerdicts(unittest.TestCase):
    """AC-5.3"""

    def test_ac53_disagreeing_check_claim_is_false(self) -> None:
        """AC-5.3: a report's check-verdict claim that the record contradicts is false."""
        self.assertIn(DISAGREE_RULE, story_gate_rules(read(SUPERVISOR)))

    def test_ac53_verdicts_come_from_the_record_not_a_rerun(self) -> None:
        """AC-5.3: the three checkers are read from the record, not re-run."""
        text = read(SUPERVISOR)
        rules = story_gate_rules(text)
        self.assertIn(NO_RERUN_RULE, rules)
        self.assertIn(SKIP_RULE, rules)
        self.assertNotIn(RETIRED_RERUN, prompt(text))

    def test_ac53_record_check_ids_are_named(self) -> None:
        """AC-5.3: the rule names the record's check ids for each checker."""
        rules = story_gate_rules(read(SUPERVISOR))
        for check_id in ("gate3_override", "gate3_5_drift_format",
                         "gate4_coverage", "gate4_authenticity"):
            self.assertIn("`%s`" % check_id, rules)


class ImplementSpecCuts(unittest.TestCase):
    """AC-5.4"""

    def test_ac54_step_23_is_gone_and_23b_remains(self) -> None:
        """AC-5.4: Step 2.3 is absent, Step 2.3b remains and counts."""
        text = read(IMPLEMENT_SPEC)
        self.assertNotIn(STEP_23, text)
        self.assertNotIn("#### Step 2.3:", text)
        step = section(text, STEP_23B, "\n#### ")
        self.assertIn("tasks and acceptance criteria", step)

    def test_ac54_step_33_drops_regeneration_and_passes_record(self) -> None:
        """AC-5.4: Step 3.3 has no regeneration bullet and passes the record path."""
        step = section(read(IMPLEMENT_SPEC), STEP_33, "\n### ")
        self.assertNotIn(REGEN_BULLET, step)
        self.assertIn(SPAWN_RECORD, step)

    def test_ac54_postrun_context_rewritten_is_still_recorded(self) -> None:
        """AC-5.4: `postRun` keeps its four fields; Step 4 of implement-story sets contextRewritten."""
        step = section(read(IMPLEMENT_SPEC), "#### Step 4.1:", "\n#### ")
        self.assertIn(POSTRUN_FIELDS, step)
        self.assertIn(CONTEXT_SOURCE, step)
        # eval-artifact-integrity.py: implement-spec still names the Artifact Map.
        self.assertIn("Artifact Map", step)

    def test_ac54_stale_gate_text_is_corrected(self) -> None:
        """AC-5.4 (carry-forward): no stale phase list or Gate 4 test-run claim."""
        text = read(IMPLEMENT_SPEC)
        self.assertNotIn(STALE_PHASES, text)
        self.assertNotIn(STALE_GATE4_RUN, text)
        step = section(text, "#### Step 4.1:", "\n#### ")
        self.assertIn("Gate 3's targeted recorded run", step)


class GeneratedCopiesAndBudget(unittest.TestCase):
    """AC-5.5"""

    def test_ac55_generated_copies_carry_the_same_wording(self) -> None:
        """AC-5.5: every generated copy carries each pinned phrase of its source."""
        for source, copies in GENERATED.items():
            for rel in copies:
                text = read(REPO_ROOT / rel)
                for pin in PINS[source]:
                    self.assertIn(pin, text, rel)

    def test_ac55_gen_platform_trees_check_is_clean(self) -> None:
        """AC-5.5: `gen-platform-trees.py --check` reports no stale copy."""
        proc = subprocess.run(
            [sys.executable, str(GEN_TREES), "--check"],
            cwd=str(REPO_ROOT), capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(proc.stdout.splitlines()[0], "pass", proc.stdout)

    def test_ac55_implement_spec_shrinks_and_needs_no_budget_entry(self) -> None:
        """AC-5.5: implement-spec.md shrinks and stays under the command budget,
        so KNOWN_OVER_BUDGET needs no entry for it; the governor test measures
        commands only, so supervisor-agent.md needs none either."""
        spec = importlib.util.spec_from_file_location("eval_leanness", str(LEANNESS))
        lean = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(lean)
        size = len(IMPLEMENT_SPEC.read_bytes())
        self.assertLess(size, IMPLEMENT_SPEC_BYTES_BEFORE)
        self.assertLessEqual(size, lean.COMMAND_BYTE_BUDGET)
        self.assertNotIn('"commands/implement-spec.md":', read(GOVERNOR_TEST))
        self.assertNotIn('"agents/supervisor-agent.md":', read(GOVERNOR_TEST))


if __name__ == "__main__":
    unittest.main()

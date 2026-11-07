#!/usr/bin/env python3
"""The supervisor reads the story-gate record (2026-11-06-lean-story-pipeline
Story 5, Business Rule 5).

The supervisor takes an optional `story_gate_record` input (for a lane,
resolved in the lane's worktree), returns `RERUN` when the post-review record
is missing, unreadable, followed by a code commit, written on a dirty tree, or
failing, marks a report's check-verdict claim false when the record disagrees,
and reads the three checkers' verdicts from the record instead of re-running
them. `implement-spec.md` drops Step 2.3 and its per-story `.writ/context.md`
regeneration, passes the record path, and runs a parallel batch's stories one
after another in its shared working tree.

Pins key phrases, not whole paragraphs, so later prose edits break only the
rule they change. Reads source files and generated copies as text, runs
`gen-platform-trees.py --check` (writes nothing), and builds throwaway git
repos under a temp dir to run the pinned record-currency commands.
"""

from __future__ import annotations

import importlib.util
import os
import shlex
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
STALE_RULE = "A code commit after the record needs a new record."
END_RULE = (
    "`<end>` is the SHA on the story file's `> **Commit:** <sha>` line, or "
    "`{head_ref}` when the story file has none."
)
# The record is current when ANCESTOR_CMD succeeds and AFTER_CMD prints nothing;
# a lane also needs LANE_TAIL_CMD to print nothing.
ANCESTOR_CMD = "git merge-base --is-ancestor <head_sha> <end>"
AFTER_CMD = "git log --format=%H <head_sha>..<end> -- . ':(exclude).writ'"
LANE_TAIL_CMD = "git log --format=%H <last-commit>..{head_ref} -- . ':(exclude).writ'"
SECOND_SHA = "The first `<sha>` is `head_sha`; the second is the first SHA"
RETIRED_HEAD_CMD = "git log -1 --format=%H {base_commit}..{head_ref}"
# Lane record path (F2).
LANE_WORKTREE = (
    "`git worktree list --porcelain` names the worktree whose `branch` is "
    "`refs/heads/{head_ref}`"
)
LANE_STORY_FILES = "`git show {head_ref}:<path>`"
# Recommendations accepted at Gate 3: failing record, precedence, ACCEPT row.
CLAIM_VERDICT = "`story-gate record verdict fail`"
PRECEDENCE = "When an ESCALATE condition and a story-gate RERUN rule both apply, ESCALATE wins."
ACCEPT_ROW = "| story-gate post-review pass | verified |"
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
# Maintainer decision: a parallel batch in one working tree runs serially.
# Starts after the command name: the plugin copy namespaces it (`/writ:...`).
SERIAL_BATCH = (
    "for each story one after another: the "
    "stories share this working tree, and each story's `story-gate` record must "
    "name its own final code commit on a clean tree."
)
RETIRED_CONCURRENT = (
    "Spawn `/implement-story {story-id}` for each story in the batch concurrently",
    "one parallel tool-call per story",
    "**Platform note:**",
)
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
                 STALE_RULE, ANCESTOR_CMD, AFTER_CMD, LANE_TAIL_CMD,
                 LANE_WORKTREE, CLAIM_VERDICT, PRECEDENCE,
                 DISAGREE_RULE, NO_RERUN_RULE),
    IMPLEMENT_SPEC: (SPAWN_RECORD, POSTRUN_FIELDS, CONTEXT_SOURCE, SERIAL_BATCH),
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

    def test_ac52_head_rule_is_bounded_by_the_story_commit(self) -> None:
        """AC-5.2: a code commit after the record makes it stale; each story's
        range ends at its own `> **Commit:**` SHA; the second SHA is defined."""
        rules = story_gate_rules(read(SUPERVISOR))
        for pin in (STALE_RULE, END_RULE, ANCESTOR_CMD, AFTER_CMD, LANE_TAIL_CMD, SECOND_SHA):
            self.assertIn(pin, rules)
        self.assertNotIn(RETIRED_HEAD_CMD, rules)


ENV = dict(os.environ, GIT_AUTHOR_NAME="T", GIT_AUTHOR_EMAIL="t@example.com",
           GIT_COMMITTER_NAME="T", GIT_COMMITTER_EMAIL="t@example.com")


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args],
        env=ENV, capture_output=True, text=True, check=check,
    )


def commit(repo: Path, rel: str, msg: str) -> str:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")
    git(repo, "add", rel)
    git(repo, "commit", "-q", "-m", msg)
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def run_pinned(repo: Path, template: str, **subs: str) -> subprocess.CompletedProcess:
    """Run a command exactly as the supervisor prompt pins it, placeholders filled."""
    cmd = template
    for key, value in subs.items():
        cmd = cmd.replace(key, value)
    argv = shlex.split(cmd)
    assert argv[0] == "git"
    return git(repo, *argv[1:], check=False)


def stale_sha(repo: Path, head_sha: str, end: str) -> str:
    """'' when the record is current; otherwise the second SHA the head claim names."""
    if run_pinned(repo, ANCESTOR_CMD, **{"<head_sha>": head_sha, "<end>": end}).returncode != 0:
        return end
    out = run_pinned(repo, AFTER_CMD, **{"<head_sha>": head_sha, "<end>": end}).stdout.split()
    return out[0] if out else ""


def lane_tail(repo: Path, last_commit: str) -> str:
    out = run_pinned(repo, LANE_TAIL_CMD, **{"<last-commit>": last_commit,
                                            "{head_ref}": "HEAD"}).stdout.split()
    return out[0] if out else ""


STORY = ".writ/specs/s/user-stories/story-%d.md"


class SupervisorHeadRuleGit(unittest.TestCase):
    """AC-5.2: the pinned commands, run against throwaway git histories."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git(self.repo, "init", "-q")
        commit(self.repo, "README.md", "base")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_ac52_two_story_lane_both_records_current(self) -> None:
        """AC-5.2: in a two-story lane, each story's record is current against
        its own Commit SHA, and no code follows the last story."""
        repo = self.repo
        head1 = commit(repo, "src/a.py", "feat: story 1 code")
        end1 = commit(repo, STORY % 1, "docs: complete story 1")
        commit(repo, STORY % 1, "chore: record story 1 sha")
        head2 = commit(repo, "src/b.py", "feat: story 2 code")
        end2 = commit(repo, STORY % 2, "docs: complete story 2")
        commit(repo, STORY % 2, "chore: record story 2 sha")
        self.assertEqual(stale_sha(repo, head1, end1), "")
        self.assertEqual(stale_sha(repo, head2, end2), "")
        self.assertEqual(lane_tail(repo, end2), "")

    def test_ac52_writ_only_story_record_is_current(self) -> None:
        """AC-5.2 (review Minor): a story that changed only `.writ/` passes."""
        repo = self.repo
        head = commit(repo, ".writ/docs/x.md", "docs: writ-only change")
        end = commit(repo, STORY % 1, "docs: complete story 1")
        self.assertEqual(stale_sha(repo, head, end), "")
        # No Commit line yet: <end> falls back to {head_ref}.
        self.assertEqual(stale_sha(repo, head, "HEAD"), "")

    def test_ac52_writ_only_commits_around_the_record_keep_it_current(self) -> None:
        """AC-5.2 (review Minor): a `.writ/`-only commit before post-review (so
        it is `head_sha`) or after the record never makes the record stale."""
        repo = self.repo
        commit(repo, "src/a.py", "feat: code")
        head = commit(repo, ".writ/docs/x.md", "docs: writ-only before post-review")
        commit(repo, ".writ/specs/s/drift-log.md", "docs: writ-only after the record")
        end = commit(repo, STORY % 1, "docs: complete story 1")
        self.assertEqual(stale_sha(repo, head, end), "")

    def test_ac52_code_commit_after_the_record_is_stale(self) -> None:
        """AC-5.2 (Interaction Edge Case): a code commit after the record fails,
        and the claim's second SHA is that commit."""
        repo = self.repo
        head = commit(repo, "src/a.py", "feat: code")
        later = commit(repo, "src/a.py", "fix: after post-review")
        end = commit(repo, STORY % 1, "docs: complete story 1")
        self.assertEqual(stale_sha(repo, head, end), later)

    def test_ac52_record_off_the_story_history_is_stale(self) -> None:
        """AC-5.2: a `head_sha` that is not an ancestor of <end> fails, naming <end>."""
        repo = self.repo
        git(repo, "checkout", "-q", "-b", "side")
        head = commit(repo, "src/a.py", "feat: abandoned code")
        git(repo, "checkout", "-q", "-")
        commit(repo, "src/a.py", "feat: code")
        end = commit(repo, STORY % 1, "docs: complete story 1")
        self.assertEqual(stale_sha(repo, head, end), end)

    def test_ac52_lane_code_commit_after_the_last_story_fails(self) -> None:
        """AC-5.2: a lane code commit after the last story's Commit SHA has no record."""
        repo = self.repo
        head = commit(repo, "src/a.py", "feat: story 1 code")
        end = commit(repo, STORY % 1, "docs: complete story 1")
        stray = commit(repo, "src/b.py", "feat: unreviewed code")
        self.assertEqual(stale_sha(repo, head, end), "")
        self.assertEqual(lane_tail(repo, end), stray)


class SupervisorLaneRecordPath(unittest.TestCase):
    """AC-5.1 (lane): the record and story files resolve in the lane worktree."""

    def test_ac51_lane_record_resolves_in_the_lane_worktree(self) -> None:
        """AC-5.1: an empty record path for a lane resolves via `git worktree list`."""
        text = read(SUPERVISOR)
        inputs = section(text, "## Input Requirements", "## Prompt Template")
        rules = story_gate_rules(text)
        for block in (inputs, rules):
            self.assertIn(LANE_WORKTREE, block)
            self.assertIn("<that worktree>/" + RECORD_PATH, block)
            self.assertIn(LANE_STORY_FILES, block)


class SupervisorVerdictAndPrecedence(unittest.TestCase):
    """AC-5.3 (accepted Gate 3 recommendations)"""

    def test_ac53_failing_record_reruns_unless_drift_log_accepts(self) -> None:
        """AC-5.3: a `fail` record, or a non-PASS `gate3.verdict`, → RERUN,
        unless drift-log.md names the check and file as accepted."""
        rules = story_gate_rules(read(SUPERVISOR))
        line = next(x for x in rules.splitlines() if CLAIM_VERDICT in x)
        for word in ("`verdict` is `fail`", "`gate3.verdict` is not `PASS`",
                     "RERUN", "`drift-log.md`", "maintainer-accepted false positive"):
            self.assertIn(word, line)

    def test_ac53_escalate_wins_and_accept_example_has_a_record_row(self) -> None:
        """AC-5.3: ESCALATE beats a story-gate RERUN; the ACCEPT example cites the record."""
        text = read(SUPERVISOR)
        self.assertIn(PRECEDENCE, section(prompt(text), "## Decide", "## Output Format"))
        self.assertIn(ACCEPT_ROW, section(text, "### ACCEPT", "### ESCALATE"))


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

    def test_parallel_batch_runs_serially_in_one_working_tree(self) -> None:
        """Maintainer decision (Gate 3 F3): a parallel batch's stories run one
        after another in the shared tree; nothing spawns them concurrently."""
        step = section(read(IMPLEMENT_SPEC), "#### Step 3.2: Execute Batches", "\n#### ")
        self.assertIn(SERIAL_BATCH, step)
        self.assertIn("separate worktrees (`/implement-phase` lanes)", step)
        for retired in RETIRED_CONCURRENT:
            self.assertNotIn(retired, step)

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

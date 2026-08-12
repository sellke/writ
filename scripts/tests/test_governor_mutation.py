#!/usr/bin/env python3
"""The mutation proof — 2026-08-12-governor-enforcement Story 6.

**A green suite is not evidence of a working gate.** It is equally consistent
with a gate that quietly stopped asserting anything — which is exactly what
Story 5 found in two tests that kept passing after the flip by matching a
comment instead of a statement. The only proof that a gate bites is watching it
bite, once per gated property, on real files, through the real `eval.sh`.

So each mutation here breaks ONE property on a REAL command or agent file,
runs `bash scripts/eval.sh --check=leanness` for real, asserts the exact
verdict and the exact finding text, and reverts before the next one. A batch
mutation that produces a red run tells you *something* failed, not that each
check independently does; the one-to-one correspondence between the property
broken and the finding named is the whole value.

**The committed tree is never mutated.** Every mutation lands on a scratch copy
of the product surface built in `setUpModule`, per the discipline
`EvalShBoundaryTests` established in `2026-08-11-governor-instrumentation`
Story 7. `test_zz_the_committed_tree_is_clean` is the exit condition.

Two mutations — F (a planted bound justification) and G (a planted
`eval-exempt:` marker) — test the ABSENCE of a silencing path, which is the
property Business Rules 1 and 3 exist for and the thing unit tests over
fixtures assert least convincingly. They are the ones that would be easiest to
skip and hardest to recover.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_TMP: tempfile.TemporaryDirectory | None = None
SCRATCH: Path


def setUpModule() -> None:
    """One scratch copy of the product surface, reused by every mutation.

    Cheap (~0.05s) because it copies the product surface and not `.git`, and
    reused because the value is in the mutations, not in the copying.
    """
    global _TMP, SCRATCH
    _TMP = tempfile.TemporaryDirectory()
    SCRATCH = Path(_TMP.name) / "tree"
    SCRATCH.mkdir()
    for directory in ("commands", "agents", "skills", "adapters", "scripts"):
        shutil.copytree(REPO_ROOT / directory, SCRATCH / directory)
    for name in ("system-instructions.md", "README.md"):
        shutil.copy2(REPO_ROOT / name, SCRATCH / name)
    (SCRATCH / ".writ").mkdir()
    # Seed the scratch baseline from the scratch tree itself rather than
    # copying the committed one. The copy includes THIS file, so the `scripts`
    # surface is larger here than in the repo and every run would carry two
    # standing growth warnings that have nothing to do with any mutation. A
    # freshly seeded baseline makes the clean tree genuinely silent, so a
    # warning appearing after a mutation can only have come from that mutation.
    subprocess.run([sys.executable, str(SCRATCH / "scripts" / "eval-leanness.py"),
                    "--root", str(SCRATCH), "--baseline",
                    str(SCRATCH / ".writ" / "leanness-baseline.json"),
                    "--update-baseline"], capture_output=True, check=True)


def tearDownModule() -> None:
    if _TMP is not None:
        _TMP.cleanup()


class MutationCase(unittest.TestCase):
    """Mutate one real file, run the real gate, assert, revert."""

    def run_gate(self) -> tuple[int, str]:
        report = Path(_TMP.name) / "report.md"
        result = subprocess.run(
            ["bash", str(SCRATCH / "scripts" / "eval.sh"), "--check=leanness",
             f"--report={report}"],
            capture_output=True, text=True, cwd=SCRATCH)
        return result.returncode, report.read_text(encoding="utf-8")

    def mutate(self, rel: str, transform) -> None:
        """Apply `transform` to a real file and restore it when the test ends.

        addCleanup rather than tearDown: an assertion failure mid-test must
        still leave the scratch tree in the state the next mutation expects.
        """
        path = SCRATCH / rel
        original = path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        text = original.decode("utf-8")
        new = transform(text)
        self.assertNotEqual(new, text, f"the mutation was a no-op on {rel}")
        path.write_text(new, encoding="utf-8")

    def assertBlocking(self, rc: int, report: str, *fragments: str) -> None:
        self.assertEqual(rc, 1, report)
        self.assertIn("FAIL", report)
        for fragment in fragments:
            self.assertIn(fragment, report)

    def assertNonBlocking(self, rc: int, report: str, *fragments: str) -> None:
        self.assertEqual(rc, 0, report)
        self.assertIn("- Findings: 0", report)
        for fragment in fragments:
            self.assertIn(fragment, report)


class BaselineTests(MutationCase):

    def test_aa_the_clean_scratch_tree_is_green(self):
        """The baseline every mutation is measured against, recorded first.

        Without it, a red run after a mutation proves nothing — the tree might
        have been red already.
        """
        rc, report = self.run_gate()
        self.assertEqual(rc, 0, report)
        self.assertIn("PASS", report)
        self.assertIn("- Findings: 0", report)


class ContractMutationTests(MutationCase):
    """The four checks Story 5 made blocking, one property at a time."""

    def test_b_removing_a_problem_field_fails_naming_file_and_field(self):
        self.mutate("commands/status.md",
                    lambda text: "\n".join(
                        line for line in text.split("\n")
                        if not line.startswith("problem:")))
        rc, report = self.run_gate()
        self.assertBlocking(rc, report, "commands/status.md", "problem")

    def test_c_removing_a_completion_section_fails_naming_the_heading(self):
        self.mutate("commands/status.md",
                    lambda text: text.replace("\n## Completion\n",
                                              "\n## Wrapping Up\n", 1))
        rc, report = self.run_gate()
        self.assertBlocking(rc, report, "commands/status.md", "## Completion")

    def test_d_removing_a_loop_max_iterations_fails_naming_the_field(self):
        self.mutate("commands/implement-phase.md",
                    lambda text: "\n".join(
                        line for line in text.split("\n")
                        if "max_iterations" not in line))
        rc, report = self.run_gate()
        self.assertBlocking(rc, report, "commands/implement-phase.md",
                            "max_iterations")

    def test_e1_agent_configuration_carrier_missing_a_field_fails(self):
        """The plain-fence carrier — six of the seven agents use it."""
        self.mutate("agents/coding-agent.md",
                    lambda text: "\n".join(
                        line for line in text.split("\n")
                        if not line.startswith("outcome:")))
        rc, report = self.run_gate()
        self.assertBlocking(rc, report, "agents/coding-agent.md", "outcome")

    def test_e2_agent_specification_yaml_carrier_missing_a_field_fails(self):
        """The ```yaml carrier — visual-qa-agent.md is the only user, and
        recognising only one carrier would produce false findings against a
        compliant file, which is the fastest way to teach a maintainer to
        ignore the whole channel."""
        self.mutate("agents/visual-qa-agent.md",
                    lambda text: "\n".join(
                        line for line in text.split("\n")
                        if not line.startswith("problem:")))
        rc, report = self.run_gate()
        self.assertBlocking(rc, report, "agents/visual-qa-agent.md", "problem")


class ByteBudgetMutationTests(MutationCase):
    """The cap, and the two mutations that test the absence of a silencer."""

    PADDED = "commands/retro.md"   # 16,807 bytes clean — comfortably compliant

    def pad_past_budget(self) -> None:
        self.mutate(self.PADDED, lambda text: text + "\n" + "x" * 12000 + "\n")

    def test_f1_padding_a_compliant_command_past_budget_is_reported_by_name(self):
        """Mutation A, under the 2026-08-12 (d) rescope.

        The cap ships MEASURED and NON-BLOCKING because five commands are over
        budget with no owner converting them, and a permanently-red gate is an
        invisible one. So the assertion is not "the run goes red" — it is that
        the run **names the file, its measured bytes, the budget and the
        overage**, which is what makes the number actionable. A cap that is
        non-blocking must never become a cap that is silent.
        """
        clean_rc, clean_report = self.run_gate()
        self.assertEqual(clean_rc, 0)
        self.assertNotIn(self.PADDED, clean_report)

        self.pad_past_budget()
        size = (SCRATCH / self.PADDED).stat().st_size
        rc, report = self.run_gate()
        self.assertNonBlocking(rc, report,
                               f"WARNING [{self.PADDED}]",
                               f"{size} bytes",
                               "24960-byte per-invocation budget",
                               f"by {size - 24960}")

    def test_f2_a_bound_justification_cannot_quiet_the_budget(self):
        """Mutation F. A justification explains growth against a BASELINE; it
        has no meaning against an ABSOLUTE budget (Business Rule 3)."""
        self.pad_past_budget()
        _, before = self.run_gate()

        def plant(text: str) -> str:
            data = json.loads(text)
            surface = data["surfaces"]["commands"].setdefault("justifications", {})
            surface["chars"] = {"value": 10 ** 9, "date": "2026-08-12",
                                "text": "planted by the mutation proof to try to "
                                        "silence the absolute budget"}
            return json.dumps(data, indent=2) + "\n"

        self.mutate(".writ/leanness-baseline.json", plant)
        rc, report = self.run_gate()
        self.assertNonBlocking(rc, report, f"WARNING [{self.PADDED}]",
                               "24960-byte per-invocation budget")
        self.assertIn(f"WARNING [{self.PADDED}]", before)

    def test_f3_an_eval_exempt_marker_cannot_quiet_the_budget(self):
        """Mutation G. `file_has_exemption()` lives in eval.sh and governs
        check_length and its peers; eval-leanness.py has no exemption reader at
        all, so the marker cannot reach the budget. Non-silenceability proven
        as a property of the running system, not claimed in a comment."""
        self.pad_past_budget()
        # Appended, not prepended: a marker above the leading `---` would break
        # the frontmatter and the run would go red for a reason that has
        # nothing to do with exemptions.
        self.mutate(self.PADDED,
                    lambda text: text + "\n<!-- eval-exempt: length all -->\n")
        rc, report = self.run_gate()
        self.assertNonBlocking(rc, report, f"WARNING [{self.PADDED}]",
                               "24960-byte per-invocation budget")

        # ...and the same marker DOES silence the check it legitimately governs,
        # which is what makes the assertion above meaningful rather than lucky.
        length_report = Path(_TMP.name) / "length.md"
        subprocess.run(["bash", str(SCRATCH / "scripts" / "eval.sh"),
                        "--check=length", f"--report={length_report}"],
                       capture_output=True, text=True, cwd=SCRATCH)
        self.assertNotIn(self.PADDED, length_report.read_text(encoding="utf-8"))


class GracefulDegradationMutationTests(MutationCase):
    """Mutation H — the pin survives into the live, blocking gate."""

    def test_g_an_unresolvable_required_skill_warns_and_never_fails(self):
        """system-instructions.md: "Unknown skill names produce a warning at
        consumer load time, not a hard failure." The fixture tests assert it;
        this asserts it in a FAIL-capable, post-flip eval.sh run on a real file.
        """
        self.mutate("commands/status.md",
                    lambda text: text.replace(
                        "\nname: status\n",
                        "\nname: status\nrequired_skills: [no-such-skill]\n", 1))
        rc, report = self.run_gate()
        self.assertNonBlocking(
            rc, report,
            "WARNING [commands/status.md → required_skills: no-such-skill]")
        self.assertIn("- Metrics: required_skills_declarations=1", report)


class BoundaryTests(MutationCase):
    """Assertions about things this spec did NOT change — asserted, because
    "we did not touch it" is not evidence."""

    def test_h_governor_boundary_intact_still_passes(self):
        """scripts/eval-loop-bounds.py:539 greps eval-leanness.py for the
        literal `check_loop_bounds` and degrades to a reported SKIP if it is
        absent. The failure mode is a silent skip, not a failure, so a refactor
        during Stories 2 or 5 could have disarmed it invisibly."""
        result = subprocess.run([sys.executable,
                                 str(REPO_ROOT / "scripts" / "eval-loop-bounds.py")],
                                capture_output=True, text=True)
        rows = [line.split("\t") for line in result.stdout.split("\n") if line]
        matching = [row for row in rows if len(row) > 1
                    and row[1] == "governor-boundary-intact"]
        self.assertEqual(len(matching), 1, result.stdout)
        self.assertEqual(matching[0][0], "PASS", matching[0])

    def test_zz_the_committed_tree_is_clean(self):
        """The story's exit condition. Now that the gate blocks, an
        un-reverted mutation does not merely leave a stale warning — it fails
        every subsequent run until somebody finds it."""
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", "commands", "agents",
             "skills", "adapters", "system-instructions.md"],
            capture_output=True, text=True, cwd=REPO_ROOT)
        self.assertEqual(result.stdout.strip(), "",
                         "a mutation escaped onto the committed tree")


if __name__ == "__main__":
    unittest.main(verbosity=2)

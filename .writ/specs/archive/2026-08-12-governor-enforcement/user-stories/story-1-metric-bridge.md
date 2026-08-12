# Story 1: Compliance Counts Reach the Eval Report

> **Status:** Complete
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who reads the eval report and never the raw JSON
**I want to** see `contract_compliance` and `required_skills_declarations` in the report
**So that** when the contract checks become blocking I can see how much surface the gate actually covers, and Business Rule 8's vacuous-pass guard stops being invisible in the only channel I read

## Acceptance Criteria

- [x] Given the current `scripts/eval.sh` before this story, when `bash scripts/eval.sh --check=leanness` runs and the report is grepped for `contract_compliance` or `required_skills_declarations`, then the count is **0** — the defect is reproduced and recorded before it is fixed.
- [x] Given this story's change, when the same command runs, then the report carries a `Metrics: contract_compliance: ...` line rendering `commands_checked`, `commands_with_contract`, `commands_with_completion`, `loop_commands_checked`, `loop_commands_bounded`, `agents_checked`, and `agents_with_contract` as counts.
- [x] Given the same run, when the report is read, then it carries a `Metrics: required_skills_declarations=<n>` line — so `0 findings` and `0 things checked` are distinguishable in the report, which is the whole point of instrumentation Business Rule 8.
- [x] Given the legacy first `METRIC` line (`commands= agents= skills= command_lines= command_chars=`), when this story's diff is inspected, then that line is **byte-identical** to its pre-story form. Its own comment names the Tier B consumers that read only the first METRIC line.
- [x] Given an `eval-leanness.py` whose JSON lacks either key (a mismatched install, or an older copy in a fixture root), when the bridge runs, then it prints **nothing** for the absent key — never `contract_compliance: None`.
- [x] Given the bash reader `while IFS=$'\t' read -r kind a b c`, when the new lines are rendered, then neither contains a literal tab or newline, so no field shifts. Counts and key names cannot introduce one, and the rendering must not.
- [x] Given `scripts/eval.sh` after this story, when `bash scripts/eval.sh` runs end to end, then it exits 0 and no other check's output changes.

## Implementation Tasks

- [x] 1.1 Reproduce and record the defect: run `bash scripts/eval.sh --check=leanness --report=<tmp>`, grep the report for both keys, record the zero result in the story's Notes as the pre-state
- [x] 1.2 Add a guarded `contract_compliance` branch to the TSV bridge at `scripts/eval.sh:~2828-2847`, in the same `if "<key>" in m:` shape the `per_surface` and `story_context_bytes` branches already use
- [x] 1.3 Add a guarded `required_skills_declarations` branch in the same shape
- [x] 1.4 Verify the legacy first `METRIC` line is untouched — assert byte-identity against `git show HEAD:scripts/eval.sh`, not by eye
- [x] 1.5 Add a test asserting both keys reach a generated report, and that a metrics dict missing them produces no line at all
- [x] 1.6 Raise `surfaces.scripts.justifications.{lines,chars}` in `.writ/leanness-baseline.json` to this story's post-change measurement, dated, with `text` naming this story (instrumentation Business Rule 9)
- [x] 1.7 Verify acceptance criteria and that `bash scripts/eval.sh` is green end to end

## Notes

**Technical considerations:**

- **The defect is verified, not suspected.** `scripts/eval.sh`'s `check_leanness()` TSV bridge prints a fixed METRIC set: one legacy aggregate line, a `per_surface` line and product rollup behind `if "per_surface" in m`, and a `story_context_bytes` line behind its own guard. There is no branch for either contract key. A real run on 2026-08-12 produced four `Metrics:` lines and `grep -c` returned 0 for both.
- **This lands first because the flip makes the number load-bearing.** Today `contract_compliance` is a progress trend for the migration specs. After Story 5 it is the *denominator of the gate* — how much of the surface the red or green actually covers. Flipping while that number is unreadable ships a gate nobody can reason about.
- **`required_skills_declarations` has been decorative since it shipped.** Instrumentation Business Rule 8 says *"a check with nothing to assert reports nothing — and says so in the metrics."* The saying-so has never reached the report. `required_skills_declarations: 0` is exactly the case that rule exists for, and it is invisible.
- **That 0 is now permanent, and it strengthens this story rather than weakening it.** `system-instructions.md:252` — the line Story 7 corrects — predicted that *"progressive disclosure's extraction work lands the first real declarations."* The 2026-08-12 mechanism ruling retired `required_skills:` for the phase, so no disclosure spec declares the field and the count stays 0 **by design and indefinitely**, not transiently pre-migration. `check_required_skills()` will therefore assert nothing for the foreseeable future. A guard that distinguishes *"0 findings"* from *"0 things checked"* matters **more** when the second number is permanent, not less — a reader who sees only `0 findings` would reasonably conclude the check is passing. Do not read the permanent 0 as a defect in this story, and do not "fix" it by removing the metric.
- **The legacy line is protected by an explicit comment**, not by accident. Read it before editing anything near it.

**Risks / challenges:**

- **Field shifting in the bash reader.** `while IFS=$'\t' read -r kind a b c` splits on tabs into four fields. The existing `clean()` strips tabs and newlines from finding text but the METRIC lines are built separately. A rendered value containing a tab silently shifts `b` and `c`. Integer counts and snake_case keys cannot produce one — but do not reach for a formatting helper that might.
- **Rendering `None` on a mismatched install.** `m.get("contract_compliance")` on an older helper returns `None` and would print `contract_compliance: None` into a maintainer's report, which reads as a broken check rather than an absent one. Guard on key presence, as the existing branches do.
- **Scope creep into the report's rendering.** The bash reader maps every `METRIC` line to `add_note "Metrics: $a"`. Do not restructure that mapping. Two new lines in the existing shape is the whole change.

**Integration points:**

- `scripts/eval.sh` `check_leanness()` only. `scripts/eval-leanness.py` is not touched by this story — it already emits both keys correctly.
- Story 2's `per_command_invocation` metric will use the same bridge shape this story establishes.
- Story 4's pre-flip gate reads `contract_compliance` from the JSON directly, not from the report, so it does not depend on this story — but a maintainer reading Story 4's failure needs this story's output to interpret it.

## Implementation Notes (2026-08-12)

**Pre-state, reproduced before the fix (task 1.1).**

```
$ bash scripts/eval.sh --check=leanness --report=/tmp/lean-prestate.md   # exit 0
$ grep -c "contract_compliance\|required_skills_declarations" /tmp/lean-prestate.md
0
$ grep -c "^- Metrics:" /tmp/lean-prestate.md
4
```

Four `Metrics:` lines, zero hits for either key. The defect is exactly as the
spec recorded it: `check_leanness()`'s TSV bridge prints one legacy aggregate
line, a `per_surface` pair behind `if "per_surface" in m`, and a
`story_context_bytes` line behind its own guard — and no branch for either
contract key.

**Post-state.**

```
- Metrics: contract_compliance: commands_checked=31 commands_with_contract=31 commands_with_completion=31 loop_commands_checked=5 loop_commands_bounded=5 agents_checked=7 agents_with_contract=7
- Metrics: required_skills_declarations=0 (frontmatter declarations; the phase's mechanism is the inline read counted beside it)
```

**Legacy line (task 1.4).** Asserted by diff against `git show HEAD:scripts/eval.sh`,
not by eye — the four-line legacy block is byte-identical, and
`test_the_legacy_first_metric_line_is_byte_identical_to_its_shipped_form`
keeps asserting both its source form and its rendered output.

**Branches added.** Beyond the two the story names, the same guarded shape
carries the keys Stories 2 and 7 introduce (`inline_skill_reads`,
`command_budget`, `per_command_invocation`), so the bridge is edited once
rather than in three separate diffs to the same heredoc.

**Absent-key behavior.** Every new branch is guarded on key PRESENCE
(`if "<key>" in m`), never truthiness — `required_skills_declarations=0` is
precisely the value that must still render, and a mismatched helper must print
nothing rather than `contract_compliance: None`. Asserted by
`test_absent_keys_print_nothing_never_none`. The legacy first line's
pre-existing `None` rendering for absent aggregate keys is untouched and out of
this story's scope.

**Tests.** `scripts/tests/test_governor_enforcement.py` → `MetricBridgeTests`,
7 cases. The renderer under test is **extracted from the committed
`scripts/eval.sh` heredoc** rather than re-typed, so a passing copy cannot hide
a broken original — the defect class this spec exists to close.

**Baseline (task 1.6).** `surfaces.scripts.justifications.{lines,chars}` raised
to 31,501 / 1,353,170, dated 2026-08-12, text naming this story.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 4 (every finding and every metric must be legible in the channel maintainers read)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The METRIC bridge defect — the fixed METRIC set, the two missing branches, and why it matters more after the flip] — from spec.md → ## Detailed Requirements → ### The METRIC bridge defect
- **Error map rows:** [An older `eval-leanness.py` without the contract metrics → the bridge prints nothing for them, never `None`] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Contract:** [Hard constraint 1: this spec owns `scripts/eval.sh`. The bridge defect is in reach and is taken rather than scoped out.] — from spec.md → ## Contract (Locked)

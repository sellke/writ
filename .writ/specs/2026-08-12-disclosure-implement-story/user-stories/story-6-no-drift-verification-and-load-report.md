# Story 6: No-Drift Verification and the Load Report

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 5

## User Story

**As a** maintainer who has to decide whether five more extractions should follow this one
**I want to** the pre-edit inventory walked row by row against the new surface, inline-read placement audited, unresolved-skill degradation probed under real load, and the floor, full-path ceiling and `--quick` ceiling reported as measurements
**So that** "nothing was lost" is proven rather than asserted, and the phase's go/no-go decision rests on numbers from the pilot rather than on the plan-time projection ADR-021 itself flagged as possibly wrong

## Acceptance Criteria

- [ ] Given `no-drift-inventory.md` was captured from the pre-edit file in Story 1, when this story lands, then every row's `Where it lives now` column names either `commands/implement-story.md` or exactly one of the eight `SKILL.md` files, and the count of unaccounted rows is **zero**. Any row that cannot be located is recorded as a defect and repaired before this story closes — not annotated as acceptable.
- [ ] Given a rule may be reworded but not removed, when this story lands, then the walk records for each row whether the wording changed, and every changed row carries a one-line note confirming the rule is the same. A row marked "reworded" with no note is treated as unverified.
- [ ] Given an unreadable skill path must degrade rather than break, when this story lands, then the probe has been run **on the mechanism actually used**: an inline `Read skills/deliberately-missing-skill/SKILL.md` inserted at a real step, `python3 scripts/measure-invocation.py` listing it in `unresolved_skills`, emitting a WARNING that its figures are a lower bound, and exiting 0 — and the probe reverted with `git diff` confirming the file returned to its post-Story-5 state. `scripts/eval-leanness.py`'s `check_required_skills` is **recorded as not exercisable** by this spec (it reads frontmatter only, and the command declares nothing); no declaration is added to manufacture a pass.
- [ ] Given the mechanism ruling removed the convention's only announced consumer, when this story lands, then the load report names the two files carrying the now-false claim — `system-instructions.md`'s `required_skills:` **Status: adopted** paragraph and `adapters/claude-code.md:396` — states that `metrics.required_skills_declarations` remains **0** after this spec and after all six, records that neither file is in this spec's file set and that **no owner is assigned**, and surfaces it for a maintainer decision rather than resolving it.
- [ ] Given tooling agreement is not the same as harness agreement, when this story lands, then the observed behavior of the actual harness during at least one real `/implement-story` invocation is recorded — which of the nine inline reads fired, whether any skill was loaded that the run's path did not reach, and whether an unreadable path degraded gracefully. **A `--quick` run is the one to observe**, because it is the run whose two skipped skills are the spec's whole claim. **If the rule breaks in practice, that is recorded as a finding for ADR-021's 2026-11-11 review trigger, not worked around.**
- [ ] Given Business Rule 1 binds a floor and a full-path ceiling and reports a `--quick` ceiling, when this story lands, then the load report records before and after for `command_bytes`, `command_lines`, `eager_bytes`, `floor_bytes`, `conditional_bytes` and `ceiling_bytes`, plus the derived `--quick` ceiling with its arithmetic shown, with deltas as both bytes and percentages, against the **corrected** baseline of 83,770 — and states plainly whether the full-path ceiling regressed. If it did, the written justification from Story 5 is carried into ADR-021's amendment entry 2 alongside the measured figures, and the `--quick` saving is reported separately and never as an offset.
- [ ] Given "five gates skipped" is not "five skills saved", when this story lands, then the `--quick` section of the report names the two skipped gates that actually carry a skill (0.5 → `boundary-map-computation`, 3.5 → `drift-triage`) and states that Gates 0, 3 and 5 are agent spawns whose procedure lives in `agents/*.md`, outside this instrument.
- [ ] Given ADR-021's amendment entry 2 was written with placeholders, when this story lands, then those placeholders are replaced with the measured floor, full-path ceiling and `--quick` ceiling from this pilot, and any accepted ceiling regression is recorded there as a tracked exemption with its justification.
- [ ] Given the `skills` surface has no justification in `.writ/leanness-baseline.json` and roughly doubles, when this story lands, then a **bound justification** — `(surface, metric)`-scoped `{date, value, text}` — is recorded for `skills.lines` and `skills.chars`, naming this spec, the bytes relocated, and the corresponding `commands` reduction so a reader sees a transfer rather than growth. `--update-baseline` is **not** run.
- [ ] Given `MAX_SKILLS` is 12 and the count reaches 14, when this story lands, then the overage is reported as a measured number with the per-skill scaffolding cost this pilot observed, handed to `governor-enforcement` as the input for setting a new cap — and `scripts/eval-leanness.py` is not edited.
- [ ] Given the whole spec must leave the tree clean, when this story lands, then `bash scripts/eval.sh`, `bash scripts/gen-skill.sh --check`, `bash scripts/check-agent-parity.sh` and `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` all pass with no new findings, and `git diff --name-only` for the whole spec lists no path under `scripts/` beyond the permitted comment-only exception in `eval-story-context.py`.

## Implementation Tasks

- [ ] 6.1 Walk `no-drift-inventory.md` row by row against `commands/implement-story.md` and the eight `SKILL.md` files, filling the `Where it lives now` column. Work from the inventory, not from the diff — a diff shows what moved, the inventory shows what should still exist. Record every unaccounted row as a defect and repair it before proceeding
- [ ] 6.2 Audit placement independently of Story 5's own claim: `grep -n 'Read skills/' commands/implement-story.md` (nine lines, no skill twice, none above `### Step 1`), `grep -RF 'Read skills/' skills/` (empty), and confirm each read sits at the gate/step in spec.md → *The eight extracted skills*. A misplaced read is a defect in this story's output too — it invalidates the `--quick` figure this story reports
- [ ] 6.3 Run the degradation probe on the inline mechanism: insert `Read skills/deliberately-missing-skill/SKILL.md` at a real step, run `measure-invocation.py`, capture the exit code, the `unresolved_skills` entry and the warning text, then revert and confirm with `git diff` that nothing else changed. Separately record that `eval-leanness.py`'s `check_required_skills` had nothing to resolve and why
- [ ] 6.4 Record the harness observation from a real `/implement-story` run — preferably a `--quick` one — noting which of the nine inline reads fired and whether any skill was loaded that the path did not reach. This is the roadmap's own manual Phase 10 success criterion (*"One real `/implement-story` run completes with progressive disclosure active and every gate firing"*) and it is not automatable; record what was observed, including "could not determine" where that is the honest answer
- [ ] 6.5 Produce the load report: before/after `command_bytes`, `command_lines`, `eager_bytes`, `floor_bytes`, `conditional_bytes`, `ceiling_bytes`; the derived `--quick` and `--quick`-with-no-dependencies ceilings with arithmetic; deltas in bytes and percent against the corrected 83,770 baseline; per-skill byte sizes; and the measured per-skill scaffolding overhead. State whether the full-path ceiling regressed in one sentence, at the top, and put the `--quick` contrast in the second
- [ ] 6.6 Record the ownerless correction: the two files carrying the now-false `required_skills:` first-consumer claim, that `required_skills_declarations` stays 0, that neither file is in this spec's file set, and that assigning an owner is a maintainer action. Do **not** edit either file
- [ ] 6.7 Close the records: fill ADR-021 amendment entry 2's placeholders with the measured figures and any accepted exemption; add the bound justification for `skills.lines` and `skills.chars` to `.writ/leanness-baseline.json`; then run `eval.sh`, `gen-skill.sh --check`, `check-agent-parity.sh` and `spec-deps.py validate` and confirm all clean

## Notes

**Technical considerations:**

- The inventory walk is the substantive verification in this spec. Every script in the repository together checks eleven literals and two numbers in this file; nothing checks whether the seven WWB truncation tiers, the four spec-lite degradation rows, or "classify UP one level when ambiguous" still exist. Those are the rules the walk exists to protect.
- Separating this story from Story 5 is deliberate: the author of a rewrite is the worst person to certify that nothing was lost. If one agent runs both, it should at least re-derive the walk from the inventory rather than from its own memory of what it moved.
- `check_required_skills` is **pinned** to the `warnings` bucket at `scripts/eval-leanness.py:1239` — `emit_contract_findings(..., severity="warnings")` — explicitly so that the severity flip in `governor-enforcement` cannot make an unknown skill name blocking. That pin is now untestable from this spec, because the check reads frontmatter and this command declares nothing. Report the pin as **unexercised**; do not add a declaration to test it, and do not claim it as verified.
- **The `--quick` number is the one the phase's go/no-go turns on**, and it is the only number in the report that the eager mechanism could not have produced. Put its derivation in the report, not just its value: `measure-invocation.py` does not model paths, so a reader has to be able to check the subtraction.
- The harness observation is the one part of the roadmap's Phase 10 success criteria that no script can produce. Record it honestly; "the transcript does not show whether loading was lazy" is a finding, not a failure.
- The bound justification is the mechanism `2026-08-11-governor-instrumentation` Story 1 built precisely so that accepted growth is silenced **per increment, per metric** and warns again on any growth past it. `--update-baseline` moves every surface's floor and records no reason (`eval-leanness.py:590–595`); using it here would erase the `commands` justifications a sibling spec recorded last week.

**Risks / challenges:**

- **Walking the diff instead of the inventory.** A diff review confirms what moved and is blind to what was dropped, which is the entire failure mode Business Rule 2 exists to catch. The inventory is the artifact; the diff is a convenience.
- **Marking a row "reworded — fine" without checking.** Every such row is an unverified deletion wearing a label. The one-line note requirement exists to make the check visible.
- **Reporting only the floor.** The floor is the flattering number and is projected to improve by ~41%. The full-path ceiling is the number ADR-021 warned about and the one that decides whether five more extractions follow. A report showing one of them, in the words of `scripts/measure-invocation.py`'s own docstring, *"cannot tell you whether disclosure worked."*
- **Quoting 77,669 as the baseline.** It is the pre-`e8f2a09` figure from an instrument that could not see inline reads, and it is still written in older Phase 10 material. The baseline is **83,770**. A report comparing the new ceiling to 77,669 overstates the regression by 6,101 bytes and would send a correct result to the maintainer as a failure.
- **Presenting the `--quick` saving as if it offset the full-path regression.** They are different runs. Report both, adjacent, with neither subtracted from the other.
- **Treating an accepted ceiling regression as a per-file matter.** ADR-021 sequenced `implement-story` first *"since a failure there should stop the phase rather than surface after five easier wins."* If the ceiling regresses, the escalation is to ADR-021's review trigger and the phase's go/no-go — not a tracked exemption to be applied five more times.
- **Fixing a discovered behavioral drift by amending the inventory.** The inventory is the pre-edit record. If it disagrees with the new surface, the new surface is wrong.

**Integration points:**

- Consumes `no-drift-inventory.md` (Story 1) and the rewritten command plus eight skills (Stories 2–5).
- Writes back to `.writ/decision-records/adr-021-progressive-disclosure-token-budget.md` — placeholders only, in the `## Amendments` section Story 1 created. The Decision remains untouched.
- Writes `.writ/leanness-baseline.json`, a data file, through the bound-justification mechanism. Not a `scripts/` edit.
- Hands `governor-enforcement` three measured inputs: the byte budget's first real datapoint, the `MAX_SKILLS` overage with observed per-skill overhead, and the stale 400-line roadmap success criterion.
- The five sibling disclosure specs read this story's load report as the evidence for whether to proceed, and its per-skill overhead figure as the input to how finely they split their own extractions.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Inventory walk complete with zero unaccounted rows
- [ ] Placement audit clean: nine inline reads, none duplicated, none above `### Step 1`, none inside a skill
- [ ] Degradation probe run on the inline mechanism, recorded, and reverted; `check_required_skills` reported as unexercised
- [ ] Harness observation recorded, including any inability to determine load behavior
- [ ] Load report states floor, full-path ceiling and `--quick` ceiling, before and after against the 83,770 baseline, with an explicit regressed / did-not-regress verdict
- [ ] The ownerless `required_skills:` first-consumer correction recorded, with both files named and neither edited
- [ ] ADR-021 amendment placeholders filled; Decision points 1–5 and the 2026-11-11 review trigger still unchanged
- [ ] Bound justification recorded for `skills.lines` and `skills.chars`; `--update-baseline` not run
- [ ] `bash scripts/eval.sh`, `bash scripts/gen-skill.sh --check`, `bash scripts/check-agent-parity.sh` and `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` all clean
- [ ] Reviewed against Business Rules 1, 2, 4, 7, 9

## Context for Agents

- **Business rules:** [BR1 report floor, full-path ceiling and `--quick` ceiling, the full-path ceiling may not regress past 83,770 without written justification; BR2 relocate-and-contract with the no-drift inventory as its verification method; BR4 reachable exactly once; BR7 no `scripts/` edits; BR8 placement audit; BR9 bound justification for the `skills` surface] — from spec.md → 📋 Business Rules
- **Contract:** ["The spec must report **floor and ceiling separately** and is not done if the ceiling regresses without justification"] — from spec.md → ## Contract (Locked), read with spec.md → ## Approved Scope Change (2026-08-12), which makes the ceiling path-dependent
- **Detailed requirements:** [The ADR-021 amendment — entry 2's four parts and its placeholders] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [The full-path ceiling is projected to regress; what the mechanism change actually buys is the `--quick` path; `required_skills:` loses its first consumer and the correction has no owner; a second guard goes vacuous; per-skill scaffolding is a real, new, permanent cost; `MAX_SKILLS` is 12 and this spec takes the count to 14; the pilot's failure is supposed to stop the phase] — from spec.md → ## Technical Concerns
- **Technical spec:** [Testing Strategy — the eight inventory categories; Path-dependent ceilings; Verification steps 1, 1b, 2–10; Leanness Disposition; Error & Rescue Map] — from sub-specs/technical-spec.md
- **Success criteria:** [2, 6, 7, 8, 9, 10, 12] — from spec.md → ## Success Criteria

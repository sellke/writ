# Story 6: No-Drift Verification and the Load Report

> **Status:** Completed ✅ (2026-08-12)
> **Priority:** High
> **Dependencies:** Story 5

## User Story

**As a** maintainer who has to decide whether five more extractions should follow this one
**I want to** the pre-edit inventory walked row by row against the new surface, inline-read placement audited, unresolved-skill degradation probed under real load, and the floor, full-path ceiling and `--quick` ceiling reported as measurements
**So that** "nothing was lost" is proven rather than asserted, and the phase's go/no-go decision rests on numbers from the pilot rather than on the plan-time projection ADR-021 itself flagged as possibly wrong

## Acceptance Criteria

- [x] Given `no-drift-inventory.md` was captured from the pre-edit file in Story 1, when this story lands, then every row's `Where it lives now` column names either `commands/implement-story.md` or exactly one of the eight `SKILL.md` files, and the count of unaccounted rows is **zero**. Any row that cannot be located is recorded as a defect and repaired before this story closes — not annotated as acceptable.
- [x] Given a rule may be reworded but not removed, when this story lands, then the walk records for each row whether the wording changed, and every changed row carries a one-line note confirming the rule is the same. A row marked "reworded" with no note is treated as unverified.
- [x] Given an unreadable skill path must degrade rather than break, when this story lands, then the probe has been run **on the mechanism actually used**: an inline `Read skills/deliberately-missing-skill/SKILL.md` inserted at a real step, `python3 scripts/measure-invocation.py` listing it in `unresolved_skills`, emitting a WARNING that its figures are a lower bound, and exiting 0 — and the probe reverted with `git diff` confirming the file returned to its post-Story-5 state. `scripts/eval-leanness.py`'s `check_required_skills` is **recorded as not exercisable** by this spec (it reads frontmatter only, and the command declares nothing); no declaration is added to manufacture a pass.
- [x] Given the mechanism ruling removed the convention's only announced consumer, when this story lands, then the load report names the two files carrying the now-false claim — `system-instructions.md`'s `required_skills:` **Status: adopted** paragraph and `adapters/claude-code.md:396` — states that `metrics.required_skills_declarations` remains **0** after this spec and after all six, records that neither file is in this spec's file set and that **no owner is assigned**, and surfaces it for a maintainer decision rather than resolving it.
- [x] Given tooling agreement is not the same as harness agreement, when this story lands, then the observed behavior of the actual harness during at least one real `/implement-story` invocation is recorded — which of the nine inline reads fired, whether any skill was loaded that the run's path did not reach, and whether an unreadable path degraded gracefully. **A `--quick` run is the one to observe**, because it is the run whose two skipped skills are the spec's whole claim. **If the rule breaks in practice, that is recorded as a finding for ADR-021's 2026-11-11 review trigger, not worked around.**
- [x] Given Business Rule 1 binds a floor and a full-path ceiling and reports a `--quick` ceiling, when this story lands, then the load report records before and after for `command_bytes`, `command_lines`, `eager_bytes`, `floor_bytes`, `conditional_bytes` and `ceiling_bytes`, plus the derived `--quick` ceiling with its arithmetic shown, with deltas as both bytes and percentages, against the **corrected** baseline of 83,770 — and states plainly whether the full-path ceiling regressed. If it did, the written justification from Story 5 is carried into ADR-021's amendment entry 2 alongside the measured figures, and the `--quick` saving is reported separately and never as an offset.
- [x] Given "five gates skipped" is not "five skills saved", when this story lands, then the `--quick` section of the report names the two skipped gates that actually carry a skill (0.5 → `boundary-map-computation`, 3.5 → `drift-triage`) and states that Gates 0, 3 and 5 are agent spawns whose procedure lives in `agents/*.md`, outside this instrument.
- [x] Given ADR-021's amendment entry 2 was written with placeholders, when this story lands, then those placeholders are replaced with the measured floor, full-path ceiling and `--quick` ceiling from this pilot, and any accepted ceiling regression is recorded there as a tracked exemption with its justification.
- [x] Given the `skills` surface has no justification in `.writ/leanness-baseline.json` and roughly doubles, when this story lands, then a **bound justification** — `(surface, metric)`-scoped `{date, value, text}` — is recorded for `skills.lines` and `skills.chars`, naming this spec, the bytes relocated, and the corresponding `commands` reduction so a reader sees a transfer rather than growth. `--update-baseline` is **not** run.
- [x] Given `MAX_SKILLS` is 12 and the count reaches 14, when this story lands, then the overage is reported as a measured number with the per-skill scaffolding cost this pilot observed, handed to `governor-enforcement` as the input for setting a new cap — and `scripts/eval-leanness.py` is not edited.
- [x] Given the whole spec must leave the tree clean, when this story lands, then `bash scripts/eval.sh`, `bash scripts/gen-skill.sh --check`, `bash scripts/check-agent-parity.sh` and `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` all pass with no new findings, and `git diff --name-only` for the whole spec lists no path under `scripts/` beyond the permitted comment-only exception in `eval-story-context.py`.

## Implementation Tasks

- [x] 6.1 Walk `no-drift-inventory.md` row by row against `commands/implement-story.md` and the eight `SKILL.md` files, filling the `Where it lives now` column. Work from the inventory, not from the diff — a diff shows what moved, the inventory shows what should still exist. Record every unaccounted row as a defect and repair it before proceeding
- [x] 6.2 Audit placement independently of Story 5's own claim: `grep -n 'Read skills/' commands/implement-story.md` (nine lines, no skill twice, none above `### Step 1`), `grep -RF 'Read skills/' skills/` (empty), and confirm each read sits at the gate/step in spec.md → *The eight extracted skills*. A misplaced read is a defect in this story's output too — it invalidates the `--quick` figure this story reports
- [x] 6.3 Run the degradation probe on the inline mechanism: insert `Read skills/deliberately-missing-skill/SKILL.md` at a real step, run `measure-invocation.py`, capture the exit code, the `unresolved_skills` entry and the warning text, then revert and confirm with `git diff` that nothing else changed. Separately record that `eval-leanness.py`'s `check_required_skills` had nothing to resolve and why
- [x] 6.4 Record the harness observation from a real `/implement-story` run — preferably a `--quick` one — noting which of the nine inline reads fired and whether any skill was loaded that the path did not reach. This is the roadmap's own manual Phase 10 success criterion (*"One real `/implement-story` run completes with progressive disclosure active and every gate firing"*) and it is not automatable; record what was observed, including "could not determine" where that is the honest answer
- [x] 6.5 Produce the load report: before/after `command_bytes`, `command_lines`, `eager_bytes`, `floor_bytes`, `conditional_bytes`, `ceiling_bytes`; the derived `--quick` and `--quick`-with-no-dependencies ceilings with arithmetic; deltas in bytes and percent against the corrected 83,770 baseline; per-skill byte sizes; and the measured per-skill scaffolding overhead. State whether the full-path ceiling regressed in one sentence, at the top, and put the `--quick` contrast in the second
- [x] 6.6 Record the ownerless correction: the two files carrying the now-false `required_skills:` first-consumer claim, that `required_skills_declarations` stays 0, that neither file is in this spec's file set, and that assigning an owner is a maintainer action. Do **not** edit either file
- [x] 6.7 Close the records: fill ADR-021 amendment entry 2's placeholders with the measured figures and any accepted exemption; add the bound justification for `skills.lines` and `skills.chars` to `.writ/leanness-baseline.json`; then run `eval.sh`, `gen-skill.sh --check`, `check-agent-parity.sh` and `spec-deps.py validate` and confirm all clean

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Inventory walk complete with zero unaccounted rows
- [x] Placement audit clean: nine inline reads, none duplicated, none above `### Step 1`, none inside a skill
- [x] Degradation probe run on the inline mechanism, recorded, and reverted; `check_required_skills` reported as unexercised
- [x] Harness observation recorded, including any inability to determine load behavior
- [x] Load report states floor, full-path ceiling and `--quick` ceiling, before and after against the 83,770 baseline, with an explicit regressed / did-not-regress verdict
- [x] The ownerless `required_skills:` first-consumer correction recorded, with both files named and neither edited
- [x] ADR-021 amendment placeholders filled; Decision points 1–5 and the 2026-11-11 review trigger still unchanged
- [x] Bound justification recorded for `skills.lines` and `skills.chars`; `--update-baseline` not run
- [x] `bash scripts/eval.sh`, `bash scripts/gen-skill.sh --check`, `bash scripts/check-agent-parity.sh` and `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` all clean
- [x] Reviewed against Business Rules 1, 2, 4, 7, 9

## Context for Agents

- **Business rules:** [BR1 report floor, full-path ceiling and `--quick` ceiling, the full-path ceiling may not regress past 83,770 without written justification; BR2 relocate-and-contract with the no-drift inventory as its verification method; BR4 reachable exactly once; BR7 no `scripts/` edits; BR8 placement audit; BR9 bound justification for the `skills` surface] — from spec.md → 📋 Business Rules
- **Contract:** ["The spec must report **floor and ceiling separately** and is not done if the ceiling regresses without justification"] — from spec.md → ## Contract (Locked), read with spec.md → ## Approved Scope Change (2026-08-12), which makes the ceiling path-dependent
- **Detailed requirements:** [The ADR-021 amendment — entry 2's four parts and its placeholders] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [The full-path ceiling is projected to regress; what the mechanism change actually buys is the `--quick` path; `required_skills:` loses its first consumer and the correction has no owner; a second guard goes vacuous; per-skill scaffolding is a real, new, permanent cost; `MAX_SKILLS` is 12 and this spec takes the count to 14; the pilot's failure is supposed to stop the phase] — from spec.md → ## Technical Concerns
- **Technical spec:** [Testing Strategy — the eight inventory categories; Path-dependent ceilings; Verification steps 1, 1b, 2–10; Leanness Disposition; Error & Rescue Map] — from sub-specs/technical-spec.md
- **Success criteria:** [2, 6, 7, 8, 9, 10, 12] — from spec.md → ## Success Criteria

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

1. **`.writ/specs/2026-08-12-disclosure-implement-story/load-report.md`**
   - The spec's evidence artifact: before/after for every measured field; the five path-dependent ceilings with their arithmetic shown; per-skill sizes against projection; the measured per-skill scaffolding cost; the degradation probe transcript; the harness observation; the ownerless `required_skills:` correction; the four handoffs to `governor-enforcement`; and the twelfth-pinned-constraint finding.

### Files Modified

- **`.writ/specs/.../no-drift-inventory.md`** — all 281 `Where it lives now` cells filled, plus a `## AA. Walk record` section carrying the method, the disposition summary, the three contracted rows each with its citation, a 22-entry rewording ledger, and the record of five rows deliberately kept in the command against byte pressure.
- **`.writ/decision-records/adr-021-...md`** — amendment entry 2's three placeholders replaced with the measured floor, full-path ceiling and `--quick` ceiling, plus the tracked exemption for the regression and what the pilot tells the 2026-11-11 review.
- **`.writ/leanness-baseline.json`** — bound justifications recorded for `skills.lines` (1814) and `skills.chars` (77625).
- **`skills/story-context-assembly/SKILL.md`** — the `⚠️ Spec-lite.md missing …` log line unwrapped onto one source line so the user-visible string is contiguous and grep-verifiable.

### Implementation Decisions

1. **The walk was machine-checked, not asserted.** 75 exact strings — every literal log line, every numeric threshold, every result-vocabulary token, every named fallback and every schema marker — were grepped across the command plus all 14 skills. **All 75 present.** Four initially reported missing; all four were line-wrap artifacts and resolved when re-checked whitespace-normalized. One of them was a user-visible log string, so it was unwrapped in the source anyway rather than left as a reflow hazard.
2. **The disposition counts were computed, then corrected.** The first draft of the walk record claimed 146 / 108 / 24 / 3. Recomputing from the filled table gave **119 command-only, 142 skill-only, 17 both, 3 contracted**. The claimed numbers were replaced with the computed ones — a verification story that reports unverified counts has failed at its one job.
3. **`--update-baseline` was not run.** It moves every surface's floor and records no reason; using it would have erased the `commands` justifications a sibling spec recorded on 2026-08-11. Two `(surface, metric)`-scoped bound justifications were written instead, and they silence growth to exactly 1814 / 77625 and nothing beyond.
4. **`check_required_skills` is reported unexercised, not passed.** It reads frontmatter only and this command declares nothing, so `required_skills_declarations` is 0 and there is nothing to resolve. No declaration was added to manufacture a pass. Its pin to the `warnings` bucket at `eval-leanness.py:1239` therefore stays untested in the product.
5. **The harness observation is "could not determine", recorded as such.** This spec was implemented by `/implement-spec` over its six stories; no `/implement-story` run of the rewritten command occurred, so no transcript shows whether the nine reads fired lazily. The roadmap's manual Phase 10 criterion is not satisfied by this spec and is not automatable — a `--quick` run is the one to observe, because its two skipped skills are the mechanism's whole claim.

### Test Results

**Verification:** structural.

- ✅ **No-drift walk:** 281 rows, 281 accounted, **zero unaccounted**. 75/75 exact strings verified present by grep across the command and all 14 skills.
- ✅ **Placement audit** (run independently of Story 5's claim): 9 `Read skills/` lines, no skill twice, lowest at line 102 against `### Step 1` at line 73 — none above it. `hoisted_skills` `[]`. `grep -RF 'Read skills/' skills/` — no output.
- ✅ **Degradation probe** on the inline mechanism: exit **0**, `unresolved_skills: ["deliberately-missing-skill"]`, and the warning *"…Their load is unmeasurable, so the figures below are a lower bound."* Reverted; `git diff` clean; re-measure shows `unresolved_skills` `[]`.
- ✅ `bash scripts/eval.sh` — **Findings: 0, Run errors: 0**.
- ✅ `python3 scripts/eval-loop-bounds.py` — `PASS drift-review-cycle`, `PASS drift-testing-cycle`; no new SKIP.
- ✅ `bash scripts/lint-skill.sh skills/*/SKILL.md` — all 14 clean. `bash scripts/gen-skill.sh --check` — no delta. `bash scripts/check-agent-parity.sh` — clean. `python3 scripts/spec-deps.py validate` — `status: ok`.
- ✅ `git diff --name-only | grep '^scripts/'` — **no output**.
- ✅ Leanness: both unjustified-growth warnings cleared by the bound justifications; only the `MAX_SKILLS` soft-ceiling warning remains, which is warn-only and handed to `governor-enforcement`.

### The load report, in one table

| Path | Before | After | Delta |
|---|---|---|---|
| **Floor** — every run | 77,669 | **49,797** | **−27,872 / −35.9%** ✓ |
| **Full path** — every gate fires | 83,770 | **91,904** | **+8,134 / +9.7%** ✗ |
| **`--quick`** | 83,770 | **82,224** | **−1,546 / −1.8%** ✓ |
| **`--quick`, no dependencies** | 83,770 | **77,366** | **−6,404 / −7.6%** ✓ |
| **`--review-only`** | 83,770 | **79,285** | **−4,485 / −5.4%** ✓ |

`command_bytes` 52,709 → **24,837** (≤ 24,960 ✓) · `command_lines` 989 → **340** · `eager_bytes` **0** · `conditional_skills` **9** · `unresolved_skills` **[]** · `hoisted_skills` **[]**.

**The full-path ceiling regressed by +8,134 bytes (+9.7%)** against a projection of +3,461 (+4.1%). Every Compression Ledger target landed and five of six beat projection (~4,230 B), plus ~3,974 B of further prose compression; no rule was deleted to close the gap. The residual is **per-skill scaffolding** — ~900–1,000 B per file × 8 ≈ 7,600 B, nearly the whole overage. Recorded as a tracked exemption in ADR-021 amendment entry 2 and as a finding for its 2026-11-11 review trigger.

**`--quick` skips five gates but only two carry a skill** — Gate 0.5 → `boundary-map-computation` (6,518 B) and Gate 3.5 § A → `drift-triage` (3,162 B). Gates 0, 3 and 5 are agent spawns whose procedure lives in `agents/*.md`, outside this instrument and outside this spec. The largest single conditional win is mode-independent: `dependency-context-loading` (4,858 B), never loaded by a dependency-free story.

### MAX_SKILLS overage, handed on

`MAX_SKILLS = 12` (`eval-leanness.py:71`); the count is **14**. `check_ceilings` emits a **warning**, never a structural finding, so nothing breaks and the constant was not edited. The input `governor-enforcement` needs for setting a new cap is the measured per-skill overhead — **~900–1,000 bytes of scaffolding per file** — and the trajectory: five sibling specs remain, and at six skills each the surface reaches roughly 44. That cap should not be picked by extrapolating from six files nobody has extracted yet.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small — the full-path ceiling regression is carried forward as a tracked exemption, and the twelfth pinned constraint is recorded as a spec-documentation gap.
- **Security:** Clean
- **Boundary Compliance:** `.writ/` artifacts plus one whitespace fix in a skill authored by this spec. No `scripts/`, no `system-instructions.md`, no adapter, no agent definition, no roadmap edit.

### Deviations from Spec

- **[DEV-001] Full-path ceiling exceeds the 83,770 allowance** — Severity: Medium
  - Spec said: `ceiling_bytes ≤ 83,770`, or a written justification with the measured overage, the compression attempted with its yield, and explicit acceptance recorded in the story and in the ADR-021 amendment.
  - Reality: 91,904 (+8,134 / +9.7%), against a projection of +3,461 (+4.1%).
  - Resolution: justification written in Story 5, carried into ADR-021 amendment entry 2 as a tracked exemption, and escalated to that ADR's 2026-11-11 review trigger — which is where ADR-021 said a pilot failure belongs, rather than to a per-file exemption applied five more times.
- **[DEV-002] The technical spec's Pinned Literals table was incomplete** — Severity: Small
  - Spec said: eleven `require_literal` strings from `scripts/eval.sh` plus two `eval-loop-bounds.py` regexes.
  - Reality: `scripts/eval-artifact-integrity.py:96` is a twelfth constraint, asserting both `**Integrity:**` and `missing required` in the command.
  - Resolution: both Integrity states restored to Step 4 item 3 (+60 bytes); recorded in the load report so the five sibling specs grep `scripts/` rather than trusting a hand-built table.
- **[DEV-003] The harness observation could not be made** — Severity: Small
  - Spec said: record the observed behavior of a real `/implement-story` run, preferably `--quick`.
  - Reality: this spec ran under `/implement-spec`; no invocation of the rewritten command occurred, so no transcript exists.
  - Resolution: recorded as "could not determine" in the load report, with the structural facts that *are* established separated from the runtime behavior that is not. The roadmap's manual Phase 10 criterion remains open.

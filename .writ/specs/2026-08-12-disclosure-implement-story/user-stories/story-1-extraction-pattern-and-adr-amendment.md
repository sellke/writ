# Story 1: Extraction Pattern, Naming Convention, and the ADR-021 Amendment

> **Status:** Completed ✅ (2026-08-12)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer running the first of six progressive-disclosure extractions
**I want to** fix the skill naming convention, record the instrument change in ADR-021, and capture a complete inventory of `implement-story.md`'s rules before a single byte moves
**So that** three parallel stories author into a shared namespace against one convention instead of three, the governing decision says what was actually measured rather than what was assumed at plan time, and there exists a pre-edit record against which "nothing was lost" can be proven rather than asserted

## Acceptance Criteria

- [x] Given `skills/` is a namespace shared by six sibling Phase 10 specs and holds 6 skills today with no naming convention recorded anywhere, when this story lands, then `.writ/docs/skills.md` → `## Extraction Patterns` documents all six rules from spec.md → Business Rule 3 — kebab-case noun phrase (2–3 words, ≤30 chars, unique across all three primitive namespaces); `<object>-<operation>` shape; never named after a command, gate, or step; bare-imperative verb-phrase `description:`; no consumer vocabulary in a shared skill; and the collision protocol — at that file's existing density, as a table and a paragraph rather than a second specification.
- [x] Given the collision protocol is what stops five later specs re-authoring the same skill, when this story lands, then it states explicitly that the check is run **before** `/new-skill` against both the intended name and its head noun in `.writ/manifest.yaml`'s `skills:` block, that the first writer owns the name, and that a later consumer inline-reads the existing skill at its own point of need and records an ADR-014 `evidence:` entry with `type: promotion` rather than forking a near-duplicate.
- [x] Given placement is now the mechanism (Business Rule 8), when this story lands, then `.writ/docs/skills.md` → `## Extraction Patterns` also states the load rule extraction implies: a skill is loaded by an inline `Read skills/<name>/SKILL.md` at the **narrowest** step that needs it, never hoisted to a command's preamble, never declared in `required_skills:` alongside it, and never read from inside another skill (`lint-skill.sh:52`). This ships to installed projects and is the sentence that stops a Writ user reproducing the mistake ADR-021 made.
- [x] Given ADR-021 Decision point 5 makes `check_length`'s 400-line command limit the binding instrument, when this story lands, then `.writ/decision-records/adr-021-progressive-disclosure-token-budget.md` carries a `## Amendments` section immediately before `## References`, following ADR-009's convention as ADR-020's does (`### <date> — <title>` with **Correction:** / **Rationale:** / **Measured:** / **Originating work:**), whose first entry records that the binding instrument is now an absolute byte budget of 24,960 with the 400-line cap demoted to a secondary non-binding tripwire.
- [x] Given a claim about an instrument must itself be measured, when this story lands, then that entry's **Measured:** line carries the reproducing command (`python3 scripts/measure-invocation.py --root .`) and the three figures that justify the change: the 2.63× bytes-per-line spread (34.5 for `migrate`, 90.8 for `implement-phase`), that a 400-line cap exempts `implement-phase` at 321 lines and 29,136 bytes — the 4th-heaviest command file — and that it fires on `create-uat-plan` at 417 lines and 16,239 bytes.
- [x] Given ADR-021:12 promises *"skills loaded on demand"* while ADR-021:18 selects a mechanism that is eager, when this story lands, then a second amendment entry records the **mechanism correction** — not merely an instrument change and not merely a measurement — carrying all four of: (a) the internal contradiction, with `system-instructions.md` → *Harness contract* (*"before any phase work begins"*) and `adapters/claude-code.md:396` cited as the evidence that selection is per **command**, never per **run**; (b) the correction, that the six disclosure specs use an inline `Read skills/<name>/SKILL.md` at the point of need and `required_skills:` is not used; (c) that ADR-021:54–58 chose the field partly because *"the convention has 0 real adoptions"* and deprecating it *"would mean designing the same thing again under a new name"* — a reason to examine a convention, not evidence that it meets the requirement; and (d) that under the eager mechanism extraction is byte-neutral at best, with named placeholders for the measured floor, full-path ceiling and `--quick` ceiling Story 6 supplies.
- [x] Given a correction is not a deprecation, when this story lands, then entry 2 explicitly states what it does **not** do: it does not deprecate `required_skills:` (still correct for a skill needed on every invocation, and `system-instructions.md`'s status to change), does not reopen Decision points 1–5, and does not move the 2026-11-11 review trigger — it attaches evidence to it.
- [x] Given an amendment corrects a premise and does not reopen a decision, when this story lands, then `git diff` shows ADR-021's Decision points 1–5, its Context, its Considered Alternatives, its Consequences, and its 2026-11-11 review trigger unchanged apart from the Date line gaining `(amended 2026-08-12 — see Amendments)`, and no sentence anywhere in the ADR is deleted.
- [x] Given "nothing was lost" is unprovable without a pre-edit record, when this story lands, then `.writ/specs/2026-08-12-disclosure-implement-story/no-drift-inventory.md` exists, is built from `git show <base>:commands/implement-story.md`, and enumerates one row per item with its pre-edit line number across all eight categories in `sub-specs/technical-spec.md` → Testing Strategy — gates, agent bindings, skip rules, numeric thresholds, result vocabularies, degradation rows, literal log strings, and named output variables.
- [x] Given the inventory is the spec's only defense against a budget met by deleting behavior, when this story lands, then it includes every numeric threshold named in the technical spec — 3 review iterations, 2 testing iterations, `MAX_SELF_FIX_ITERATIONS = 3`, 100% pass rate, ≥80% new-file coverage, 85%/70% visual match, 1000-line WWB truncation, ~2KB `knowledge_context`, 21000-byte context budget, depth-1 import graph, the <10s Gate 0.5 target, and the `+3/+2/+1/+1` knowledge scoring weights — with a `Where it lives now` column left blank for Story 6 to fill.
- [x] Given this story is documentation and record-keeping only, when this story lands, then `git diff --name-only` lists exactly three paths: `.writ/docs/skills.md`, `.writ/decision-records/adr-021-progressive-disclosure-token-budget.md`, and `.writ/specs/2026-08-12-disclosure-implement-story/no-drift-inventory.md` — no path under `commands/`, `skills/`, or `scripts/`.

## Implementation Tasks

- [x] 1.1 Re-measure before writing anything that asserts a number: run `python3 scripts/measure-invocation.py --root . --format table` and record `base.bytes`, `command_bytes`, `eager_bytes`, `floor_bytes`, `conditional_bytes` and `ceiling_bytes` for `implement-story`, plus the bytes-per-line extremes. Confirm the tool is post-`e8f2a09` (it reports an `eager_bytes` key and `conditional_skills: ["tdd-cycle"]` for this command); **a run that reports `ceiling_bytes: 77669` is the old, wrong instrument — stop.** If `base.bytes` is not 24,960, **stop and escalate** — the budget in the locked contract is derived from that number, and authoring an amendment around a stale one repeats the defect the amendment exists to correct
- [x] 1.2 Read `.writ/docs/skills.md` end to end (especially `## Extraction Patterns` and `## Authoring a Skill`) and `scripts/lint-skill.sh`'s `DESC_PATTERNS` / `BODY_PATTERNS` arrays, so the convention is written against what the lint actually rejects rather than against an idea of it
- [x] 1.3 Write the six naming rules and the collision protocol into `.writ/docs/skills.md` → `## Extraction Patterns`, after the existing transform diagram. Match that file's density — the incumbent six skill names are the worked examples; do not invent new ones
- [x] 1.4 Read `.writ/decision-records/adr-020-component-contract.md`'s `## Amendments` section as the format exemplar (it is the ADR-009 convention applied in this repo, with the `**Measured:**` line this spec also needs)
- [x] 1.5 Add `## Amendments` to ADR-021 immediately before `## References`, with entry 1 (instrument: lines → bytes) carrying **Correction:** / **Rationale:** / **Measured:** / **Originating work:**, and update the Date line to `> **Date:** 2026-08-11 (amended 2026-08-12 — see Amendments)`
- [x] 1.6 Add entry 2 (the mechanism correction) to the same `## Amendments` section: the :12-versus-:18 contradiction, the switch to inline `Read` at the point of need, the :54–58 adoption reasoning that a convention needing a consumer is not evidence it fits, and the byte-neutrality consequence — citing `system-instructions.md` → *Harness contract*, `adapters/claude-code.md:396`, and `scripts/measure-invocation.py`'s post-`e8f2a09` `eager_bytes` / `conditional_bytes` split; attaching to the existing 2026-11-11 review trigger; stating explicitly that it does not deprecate the convention; and leaving named placeholders for the measured floor, full-path ceiling and `--quick` ceiling Story 6 fills in
- [x] 1.7 Build `no-drift-inventory.md` from `git show <base>:commands/implement-story.md` — one row per rule, with pre-edit line number, category, the rule stated in its own words, and an empty `Where it lives now` column. Work section by section from the pre-edit file, not from the technical spec's summary tables, which are lossy by design
- [x] 1.8 Verify with `git diff` that ADR-021's Decision, Context, Considered Alternatives, Consequences and review trigger are unchanged; confirm `git diff --name-only` lists exactly the three expected paths; run `bash scripts/eval.sh` and `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` and confirm no new findings and `status: ok`

## Notes

**Technical considerations:**

- `.writ/docs/*.md` ships to installed projects through `install.sh`'s doc fan-out (`append_manifest_writ_docs`, `overlay_scan_flat_dir`). The naming convention is read by Writ *users* authoring their own skills, not only by this repo's maintainer — write it for that audience.
- The convention has to survive contact with `lint-skill.sh`, which is the real enforcer of rule 4. Its `DESC_PATTERNS` reject descriptions starting with `Acts as`, `Is responsible for`, `The .* agent`, `Run the full`, and `Execute the entire`. The bare-imperative verb phrase is not a style preference — it is the shape that clears that grammar.
- ADR-021's Consequences already say the 400-line figure is *"derived from the current distribution … not from a measured quality threshold. Expect to tune it after 2-3 real extractions."* The amendment is the tuning that sentence invited, arriving after extraction 1 of 6 rather than 3. Say so in the **Rationale:** — an amendment that reads as a reversal invites re-litigation; one that reads as the ADR's own prediction coming true does not.
- The two amendment entries do different work and must not be blurred. Entry 1 changes the **instrument** (lines → bytes). Entry 2 corrects the **mechanism** — it records that Decision point 3's `required_skills:` cannot deliver Decision line 12's "on demand", and that the six specs use the inline form instead. Entry 2 is the more consequential of the two and is the one a reader of ADR-021 needs first.
- **Entry 2 must not slide into deprecating `required_skills:`.** The convention still fits a skill a consumer needs on every invocation. What entry 2 corrects is ADR-021's claim that it fits *this* requirement. Deprecation is `system-instructions.md`'s call and is out of this spec's file set entirely.
- **The honest sentence about why ADR-021 chose wrong belongs in the amendment, not in a story note.** ADR-021:54–58 argued adoption partly on the grounds that the convention had no consumer and deprecating it would mean redesigning the same thing. That reasoning is reusable and so is the mistake in it: needing a consumer is a reason to evaluate a mechanism, not evidence that it satisfies the requirement. Writing that down is most of entry 2's value to the 2026-11-11 review.
- **`scripts/measure-invocation.py` was itself wrong for one day and was fixed on 2026-08-12 (`e8f2a09`).** Its docstring is now the clearest short statement of the two mechanisms in the repository and is worth reading before drafting entry 2. Do not cite its pre-fix figures; a `77,669` ceiling is the artifact of the defect.
- `<base>` is the commit this spec's branch forked from. Resolve it once (`git merge-base HEAD main`) and use the same value in Stories 5 and 6 — three stories comparing against three different baselines would make the no-drift walk meaningless.

**Risks / challenges:**

- **Scope creep from an amendment into a re-decision.** The instrument changes; the decision does not. Reopening the top-6 ordering, the one-spec-per-file decomposition, or the review trigger under "while we're in here" turns a correction into an unreviewed architecture change.
- **Writing the inventory from the technical spec instead of the file.** The section ledger in `sub-specs/technical-spec.md` is a byte accounting, not a rule accounting — it names 36 sections where the file contains well over a hundred discrete rules. An inventory derived from it would be complete-looking and empty, which is worse than no inventory because Story 6 would pass against it.
- **Under-populating the inventory to keep it manageable.** Every row skipped is a rule that can be silently deleted in Story 5 and never noticed. If the inventory feels long, that is the file's size being made legible, which is the point.
- **The temptation to fix `.writ/product/roadmap.md`'s now-stale 400-line success criterion.** Out of Scope — `governor-enforcement` has to edit that criterion when it changes the code, and two specs editing the same line with the same intent is how the phase acquires a merge conflict for nothing.

**Integration points:**

- Stories 2, 3 and 4 all author skill names against the convention this story fixes. A late convention change costs eight renames plus manifest and `SKILL.md` regeneration.
- Story 6 walks the inventory this story builds and fills its `Where it lives now` column. An inventory that is not machine-readable enough to walk row by row is a defect in this story, not in Story 6.
- The five sibling disclosure specs inherit the convention and the collision protocol. `project-context-snapshot` (Story 4) is the first name they will collide with, since `implement-spec` and `status` both regenerate `.writ/context.md`.
- ADR-021's 2026-11-11 review trigger is the destination for entry 2's finding. Do not move the trigger date.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `bash scripts/eval.sh` shows no new findings
- [x] `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok`
- [x] Reviewed against Business Rules 2, 3, 7
- [x] ADR-021 diff reviewed: `## Amendments` present with two entries, Decision points 1–5 and the review trigger otherwise unchanged
- [x] `.writ/docs/skills.md` reviewed for density against its own `## Extraction Patterns` section
- [x] `no-drift-inventory.md` spot-checked: pick three arbitrary sections of the pre-edit file and confirm every rule in them has a row

## Context for Agents

- **Business rules:** [BR2 relocate-and-contract with the no-drift inventory as its verification method, BR3 the six naming rules and the collision protocol, BR7 no edits under `scripts/`, BR8 placement — the rule this story documents in `.writ/docs/skills.md`] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The ADR-021 amendment — two entries, one dated section; Skill-naming documentation] — from spec.md → ## Detailed Requirements
- **Approved scope change:** [the 2026-08-12 mechanism ruling — inline `Read` at the point of need, `required_skills:` not used, and the two Contract sentences it supersedes] — from spec.md → ## Approved Scope Change
- **Technical concerns:** [`required_skills:` loses its first consumer and the correction has no owner; a second guard goes vacuous; `.writ/product/roadmap.md` Phase 10's Success Criteria will be stale on landing] — from spec.md → ## Technical Concerns
- **Contract:** ["The spec must report **floor and ceiling separately** and is not done if the ceiling regresses without justification"] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Measured Baseline; Why lines are the wrong instrument; Testing Strategy — the eight inventory categories] — from sub-specs/technical-spec.md

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

1. **`.writ/specs/2026-08-12-disclosure-implement-story/no-drift-inventory.md`** (281 rules + 5 cross-cutting indexes)
   - Built from `git show 9e76d1e:commands/implement-story.md` — the pre-edit file — section by section, one row per rule with its pre-edit line number, category and an empty `Where it lives now` column for Story 6. Indexes Z1–Z5 group thresholds, result vocabularies, output variables, literal log strings and the skip-mode matrix so a whole category can be spot-checked at once.

### Files Modified

- **`.writ/docs/skills.md`** (`## Extraction Patterns`)
  - Added `### Naming the extracted skill` — the six naming rules as a table plus the collision protocol paragraph — and `### Where the load goes`, which states the placement rule extraction implies: narrowest step, never hoisted into a preamble, never both mechanisms, never read from inside another skill (`lint-skill.sh:52`). Written at the file's existing density; the six incumbent skill names are the worked examples.
- **`.writ/decision-records/adr-021-progressive-disclosure-token-budget.md`**
  - Date line → `2026-08-11 (amended 2026-08-12 — see Amendments)`. Added `## Amendments` immediately before `## References` with two dated entries in the ADR-009 convention (**Correction:** / **Rationale:** / **Measured:** / **Originating work:**): entry 1, the instrument changes from lines to bytes; entry 2, the mechanism correction, carrying the :12-vs-:18 contradiction, the switch to the inline `Read`, the "a convention needing a consumer is not evidence it fits" finding, and three named placeholders for Story 6's measured figures.

### Implementation Decisions

1. **`<base>` resolved once** — `git merge-base HEAD phase/10-progressive-disclosure` = `9e76d1ecf50a6e2ecfe86b673175e5fb12ecce1f`. Stories 5 and 6 use the same value; three stories comparing against three baselines would make the walk meaningless.
2. **The inventory was built from the file, not from the technical spec's section ledger.** That ledger accounts for 36 sections of bytes; the file contains 281 discrete rules. An inventory derived from the ledger would be complete-looking and empty.
3. **Entry 2 stops short of deprecating `required_skills:`** and says so explicitly. The convention still fits a skill needed on *every* invocation; its status is `system-instructions.md`'s to change and that file is out of this spec's set.
4. **The amendment's `Measured:` line uses `create-uat-plan`** (417 lines / 16,239 bytes) as the fires-when-it-should-not example, not `migrate` — `migrate` is under the 400-line cap and is cited only as the low end of the bytes-per-line spread.

### Test Results

**Verification:** structural — there is no application code in this repository.

- ✅ `python3 scripts/measure-invocation.py --root . --command implement-story --format table` — post-`e8f2a09` instrument confirmed: `base.bytes` 24,960; `command_bytes` 52,709 / 989 lines; `floor_bytes` 77,669; `conditional_bytes` 6,101 (`tdd-cycle`); `ceiling_bytes` **83,770**; `base_share_of_floor` 32.1%. Not the 77,669 ceiling of the old instrument.
- ✅ `bash scripts/eval.sh` — **Findings: 0, Run errors: 0** (identical to the pre-spec baseline captured before any edit).
- ✅ `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` — `status: ok`.
- ✅ `git diff` on ADR-021 removes exactly one line (the Date line, replaced in place); Decision points 1–5, Context, Considered Alternatives, Consequences and the 2026-11-11 review trigger are untouched, and no sentence is deleted.
- ✅ Story deliverable diff lists exactly the three expected paths — no path under `commands/`, `skills/` or `scripts/`.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Documentation and record-keeping only; no product-source file touched.

### Deviations from Spec

None

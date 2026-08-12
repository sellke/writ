# Story 3: The `--product` Check Set and the Shared Regeneration Discipline

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer who runs `/verify-spec --product` before deciding whether the roadmap still tells the truth
**I want to** P1–P4 to stay a distinct check set with its own dispositions, and the regeneration procedure it shares with spec Check 7 to exist exactly once
**So that** the hybrid boundary — regenerate derivatives, never rewrite what is authoritative — is stated in one place instead of drifting between two copies

## Scope

Two skills, paired in one story because the split between them *is* the boundary being protected.

**A. `product-doc-audit`** — the `--product` set, ~4,600 source bytes, **allocation ≤ 4,400**:
- The section's opening paragraph: a separate, self-contained check set, **not** spec checks pointed at product docs, and the explicit warning against mirroring all eight
- The `--product` (before, lint) vs `/plan-product --reconcile` (after, revise) boundary
- The Inputs table: `mission.md` and `roadmap.md` **authoritative**; `mission-lite.md` and `.writ/context.md` **derivative**; ADRs as P2 targets; `.writ/specs/*/` as P4 evidence
- The graceful-skip rule, with its exact message, and the rule that a missing `.writ/context.md` is not an error
- Checks P1, P2, P4 in full with their dispositions; Check P3's *detection* half

**B. `derivative-regeneration`** — ~3,500 source bytes stating one procedure twice, **allocation ≤ 2,600**:
- The regeneration discipline: read the authoritative source in full; produce a condensed whole file; prepend `> Regenerated from <source> on YYYY-MM-DD`; **write the full file, never patch sections**; one pass
- Instantiation 1 — step 4.4: `spec-lite.md` ← `spec.md`, ~100 lines, covering What We're Building / Key Constraints / Success Criteria / Files in Scope / phase-dependency context. **`spec.md` is never modified — always the source, never the target.**
- Instantiation 2 — Check P3 mechanics: `mission-lite.md` ← `mission.md` (~5-sentence core plus phase context: core value, target users, key differentiators, success definition, current phase) and `.writ/context.md` ← the `/status` Step 8 schema, created if absent
- Trigger conditions: default mode after a Check 7 finding, or `--fix`; default `--product` after a P3 finding; **never** under `--check` or `--product --check`
- The locked boundary paragraph: *never touch authoritative prose* — `mission.md` and `roadmap.md` are always source, never target, exactly as `spec.md` is; P1 and P2 surface authoritative divergence for a human, never a silent rewrite

## Acceptance Criteria

- [ ] Given both skills are authored through `/new-skill`, when they are created, then each carries `status: candidate`, `disable-model-invocation: true`, a verb-phrase `description:`, `## Purpose`, and `## When to Use`, and `bash scripts/lint-skill.sh` exits 0 on both.
- [ ] Given Business Rule 4, when the product skill is compared against Story 1's ledger, then P1–P4 keep their `P` prefix, their numbers, and their heading strings **verbatim** — including the disposition suffixes (`— report-only`, `— auto-fix (regenerate)`, `— report-only (heuristic)`).
- [ ] Given the source states twice that `--product` is not spec checks 1–8 pointed at product docs, when the product skill is read, then that boundary is stated and P1–P4 are nowhere renumbered into the 1–8 sequence.
- [ ] Given Business Rule 6, when the regeneration skill is read, then it states in one place that `spec.md`, `mission.md`, and `roadmap.md` are sources and never targets, and that P1/P2 divergence is reported for a human rather than rewritten.
- [ ] Given the procedure appears twice in the source, when the regeneration skill is read, then it appears **once**, with both instantiations named and their differing outputs (~100-line spec-lite; ~5-sentence mission-lite; `/status` Step 8 schema for context.md) preserved.
- [ ] Given Business Rule 6, when trigger conditions are read, then regeneration runs in default and `--fix` and default `--product`, and never under `--check` or `--product --check`.
- [ ] Given `spec-lite.md` may be absent, when Check 7's skip rule is honored, then the regeneration skill never regenerates a file the diagnosis skill skipped.
- [ ] Given Business Rule 7, when both skills' headings and numbered steps are scanned for `re-?(check|verify|run)`, then there is no match — the single-pass property is preserved and the phrase "re-running Phase 2" from the source's iteration-bound paragraph stays in the command, not here.
- [ ] Given the allocations, when both files are measured, then `product-doc-audit` ≤ 4,400 and `derivative-regeneration` ≤ 2,600, or the overage is reported against another skill's underage so Σ ≤ 24,200 holds.

## Implementation Tasks

- [ ] 3.1 Read Story 1's ledger, confirmed names, and any sibling skill flagged for reuse instead of authoring `derivative-regeneration`
- [ ] 3.2 Scaffold both skills with `/new-skill`; confirm both descriptions pass the lint before writing bodies
- [ ] 3.3 Port the `--product` section intro, the `--reconcile` before/after boundary, and the Inputs table with the authoritative/derivative column intact
- [ ] 3.4 Port the graceful-skip rule with its exact message and the not-an-error rule for a missing `.writ/context.md`
- [ ] 3.5 Port P1, P2, P4 in full with dispositions verbatim; port P3's detection half, leaving its mechanics to the regeneration skill
- [ ] 3.6 Author the regeneration skill: one procedure, two instantiations, trigger conditions, and the never-touch-authoritative-prose boundary
- [ ] 3.7 Verify the deduplication lost nothing — diff both source copies (step 4.4 and the `--product` mechanics) against the single skill statement, field by field
- [ ] 3.8 Run `bash scripts/lint-skill.sh` on both and the re-check grep; re-shape rejected lines without dropping content
- [ ] 3.9 Diff both skills against Story 1's ledger rows for P1–P4 and Check 7's disposition; measure bytes against allocations

## Notes

**Technical considerations:**

- The two skills are authored together because the seam between them is where the hybrid boundary would break. Detection lives with the product checks; regeneration lives in the shared skill; the rule that authoritative files are never targets is stated in the shared skill because that is the only place that could violate it.
- The source's `--product` section already flags its own failure mode: *"Resist the urge to mirror all eight spec checks onto product docs; the value is a tight, high-signal lint, not a second full diagnostic."* That sentence is worth its bytes — a future reader with a skill file in front of them is exactly the reader who would add P5.
- Deduplicating the regeneration procedure is the single largest legitimate compression in this spec, and the riskiest. The two copies are not identical: 4.4 names five spec-lite sections and a ~100-line target; the P3 mechanics name a ~5-sentence core and a different marker source. Both parameter sets survive; only the shared discipline is stated once.
- `.writ/context.md`'s regeneration defers to `/status` Step 8's schema. The skill references that schema by name; it does not restate it, and it does not tell the reader to open `commands/status.md` (`lint-skill.sh` rejects `Read commands/`).

**Risks / challenges:**

- If `2026-08-12-disclosure-implement-story` already created an equivalent regeneration skill — plausible, since `/implement-story` amends `spec-lite.md` on Small drift — **reuse it** and extend it with the product instantiation rather than authoring a second. Story 1 records this decision; do not re-take it here.
- P3's disposition is the only auto-fix in the entire `--product` set. Losing it turns `--product` into a pure report and silently removes a behavior. Losing the `--product --check` exclusion does the opposite and makes a read-only invocation write files.

**Integration points:**

- Story 2's Check 7 raises the finding this story's regeneration skill acts on.
- Story 4's report skill renders the P1–P4 table and the `.writ/product/verification-YYYY-MM-DD.md` file.
- Story 5 places both skills' inline `Read skills/<name>/SKILL.md` calls — `product-doc-audit` in the `## Product Consistency Checks (\`--product\`)` section, `derivative-regeneration` **twice**, at step 4.4 and at Check P3's mechanics (maintainer ruling 2026-08-12 — no `required_skills:`). The two-read placement is deliberate: `derivative-regeneration` serves two mutually exclusive paths, and one read hoisted to their common ancestor would put it in the floor. `product-doc-audit` must be unreachable on a default run — that exclusion is 4,400 bytes a default run never pays, and under the superseded eager design it paid them.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh` exits 0 on both skills
- [ ] The field-by-field diff proving the deduplication lost nothing is recorded in this story's evidence
- [ ] P1–P4 heading strings verified verbatim against Story 1's ledger
- [ ] Byte counts recorded against both allocations

## Context for Agents

- **Business rules:** [BR3 no redesign, BR4 frozen numbering, BR6 hybrid boundary locked, BR7 no re-check step, BR11 shared namespace and reuse, BR12 lint-clean] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Skills — names and allocations] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [`lint-skill.sh` body grammar; the dependency may already own an equivalent skill] — from spec.md → ## Technical Concerns
- **Contract:** [Hardest constraint: the hybrid disposition is a locked boundary, not an implementation detail] — from spec.md → ## Contract (Locked)
- **Technical spec:** [The three-way splits → `--product`; The Disposition Ledger rows P1–P4; Where the Compression Comes From, item 1] — from sub-specs/technical-spec.md

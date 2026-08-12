# Story 3: Resolve `required_skills:` by Adoption

> **Status:** Complete
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer answering a review trigger that fired on 2026-08-03
**I want to** the `required_skills:` convention's "reserve-only" status and its overdue trigger replaced by a recorded adoption decision naming ADR-021 progressive disclosure as its first consumer
**So that** the trigger's own terms ("deprecate or revisit") are satisfied on the record, rather than a fired signal being silently deleted

## Acceptance Criteria

- [x] Given `system-instructions.md` § Skills → `required_skills:` frontmatter convention, when the status is read, then it states the convention is **adopted**, and carries all four facts: the trigger fired 2026-08-03; the outcome is revisit → adopt, not deprecate; the first consumer is ADR-021 progressive disclosure (Phase 10); and the schema is adopted unchanged.
- [x] Given the schema block above the status (optional array of strings, values match `name:` entries in `.writ/manifest.yaml`, order preserved, duplicates deduplicated, unknown names warn rather than hard-fail) and the harness contract beneath it, when compared before and after, then both are byte-unchanged — the convention is adopted as specified, not redesigned.
- [x] Given the literals `reserve-only` and `2026-08-03` in the `required_skills:` context, when the active surface is grepped (`system-instructions.md`, `cursor/writ.mdc`, `.writ/docs/skills.md`, `adapters/`), then zero hits remain.
- [x] Given `adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/openclaw.md`, when each file's Skills → Invocation paragraph is read, then the sentence "`required_skills:` is reserve-only in the foundation spec; pilot skills will adopt it as they ship" is replaced consistently across all three, and the per-platform pre-load mechanism described in each is otherwise unchanged.
- [x] Given `system-instructions.md` and `cursor/writ.mdc` after the edit, when the § Skills section of each is compared line for line, then the two are identical.
- [x] Given the full validation suite, when `bash scripts/eval.sh` runs, then it reports `Findings: 0` with no new `eval-exempt:` marker introduced by this story, and `scripts/eval-skill-lifecycle.py`'s `skill-lifecycle` check still passes.

## Implementation Tasks

- [x] 3.1 Read ADR-021 § "Why `required_skills:` gets adopted instead of deprecated" (`.writ/decision-records/adr-021-progressive-disclosure-token-budget.md:54`) and extract the reasoning verbatim enough to state it accurately: the convention specifies exactly the declarative, harness-resolved, per-invocation load contract progressive disclosure needs, including graceful degradation; deprecating it would mean designing the same mechanism again under a new name inside the same phase.
- [x] 3.2 Replace `system-instructions.md`'s "**Status: reserve-only.**" paragraph (line 252) and the "> **Review trigger: 2026-08-03**" blockquote (line 254) with a single adoption statement carrying all four required facts. Leave the schema block and harness contract untouched. Locate by literal — Stories 1 and 2 will have shifted these lines.
- [x] 3.3 Mirror the identical change into `cursor/writ.mdc`, then diff the § Skills section of both files. This section is outside `prime-directive-sync`'s comparison window; the diff is the only check.
- [x] 3.4 Apply the same replacement in `.writ/docs/skills.md`: the "**Status: reserve-only.**" paragraph (line 136) and the 2026-08-03 trigger blockquote (line 138). Keep the surrounding schema summary and the `promoted` lifecycle row (line 157), which references `required_skills:` as the promotion criterion and remains accurate.
- [x] 3.5 Replace the identical reserve-only sentence in `adapters/cursor.md:218`, `adapters/claude-code.md:396`, and `adapters/openclaw.md:278`. The three sentences are byte-identical to each other — apply one replacement three times so the adapters do not drift.
- [x] 3.6 Verify: run the active-surface and historical-surface greps (`.writ/specs/archive/2026-05-03-skills-foundation/` and ADRs must retain their original hits), `bash scripts/eval.sh` to `Findings: 0`, and `bash scripts/gen-skill.sh --check` to exit 0.

## Notes

**Technical considerations:**

- The trigger's terms are binary — "deprecate or revisit." Recording *which* was chosen, and why, is the deliverable. Deleting the blockquote and leaving a bare "adopted" claim converts a visible overdue signal into an invisible one, which is precisely the failure mode ADR-020 names for the four ignored leanness warnings.
- The convention has **zero real declarations** today: `grep -rn "required_skills" commands/ agents/ skills/` finds only documentation references (`commands/new-skill.md:228`, `:242`, `:267`; `skills/gbrain-interop/SKILL.md:155`), never a declared array in a consumer's frontmatter. Adoption here is a **status decision**, not a code change — the first actual declaration lands with ADR-021's extraction work, which is out of scope for this spec (spec.md → Out of Scope).
- Write the status honestly: the convention is adopted with a named, committed first consumer that has not yet shipped. Claiming it already has a live consumer would replace one false claim with another (Business Rule 1).
- `commands/new-skill.md:242` and `skills/gbrain-interop/SKILL.md:155` describe `required_skills:` as ADR-014's `promoted` bar ("a consumer structurally depends on it"). Adoption does not change that bar; leave both untouched.
- `.writ/product/mission.md:133` and `.writ/product/roadmap.md:341` already describe the adoption in forward-looking terms. They are consistent with this story's outcome and need no edit; confirm rather than assume.

**Risks / challenges:**

- **The mirror has no gate.** § Skills sits outside `check_prime_directive_sync()`'s comparison window, so editing `system-instructions.md` alone leaves the suite green and `cursor/writ.mdc` stale. Task 3.3 exists for this.
- Three adapter files carry the identical sentence. Editing two of three produces exactly the kind of silent cross-platform drift `adapters/` exists to prevent, and nothing in the eval suite compares adapter prose.
- `.writ/specs/archive/2026-05-03-skills-foundation/` (spec, technical spec, Story 5, and the story index) is where "reserve-only" originated. It records what was true at ship time and must not be edited (Business Rule 3).

**Integration points:**

- Depends on Story 2 for file-overlap ordering only. Nothing in this story's content depends on the ordinal deprecation; the serialization exists because all three chain stories edit `system-instructions.md` and `cursor/writ.mdc` and each owes a manual mirror diff.
- ADR-021 supplies the rationale this story records. The ADR itself is not edited.
- The roadmap's Phase 10 success criterion "Every `required_skills:` entry resolves to a real `skills/<name>/SKILL.md`" (`.writ/product/roadmap.md:332`) belongs to the "Make the governor bite" item, not this story — no check is added here.

## What Was Built

**Implementation Date:** 2026-08-11

### Files Modified

- **`system-instructions.md`** (§ Skills → `required_skills:` frontmatter convention) — the "**Status: reserve-only.**" paragraph and the `> **Review trigger: 2026-08-03**` blockquote were replaced *together* (Business Rule 7) by a single **Status: adopted.** statement carrying all four required facts.
- **`cursor/writ.mdc`** — identical replacement mirrored.
- **`.writ/docs/skills.md`** (lines 136/138) — the same resolution in the user-facing explainer, with an ADR-021 link relative to `.writ/docs/`.
- **`adapters/cursor.md:217`, `adapters/claude-code.md:396`, `adapters/openclaw.md:277`** — the byte-identical sentence "`required_skills:` is reserve-only in the foundation spec; pilot skills will adopt it as they ship." replaced by one byte-identical adoption sentence applied three times, so the three adapters cannot drift. Each file's per-platform pre-load mechanism sentence is otherwise unchanged.

### The four facts (Acceptance Criterion 1)

The replacement states: (1) the trigger fired **2026-08-03**, 90 days post-ship; (2) the outcome is **revisit → adopt**, not deprecate; (3) the first consumer is **Phase 10 progressive disclosure (ADR-021)**, whose need for a declarative, harness-resolved, per-invocation load mechanism with graceful degradation is exactly what this convention already specifies — deprecating would have meant redesigning the same mechanism under a new name inside the same phase; (4) the schema is adopted **unchanged**.

### Honesty about the consumer (Business Rule 1)

Both the root contract and the explainer state plainly that the first real declarations land with progressive disclosure's extraction work and that **no consumer declares the field yet**. `grep -rn "required_skills" commands/ agents/ skills/` confirms it: only documentation references (`commands/new-skill.md:228`, `:242`, `:267`; `skills/gbrain-interop/SKILL.md:155`), never a declared array. Claiming a live consumer would have replaced one false claim with another.

### Verification

- Schema and harness contract byte-unchanged: the five schema bullets (optional array, manifest-matching names, order preserved, duplicates deduplicated, unknown names warn) and the Harness contract paragraph below them were not touched — the convention is adopted as specified, not redesigned.
- `grep -F "reserve-only"` across `system-instructions.md`, `cursor/writ.mdc`, `.writ/docs/skills.md`, `adapters/`, `commands/`, `agents/`, `scripts/`, `skills/` → **0 hits in the `required_skills:` context**. (The only surviving repo-wide hits are `.writ/product/roadmap.md:299` and `:368`, which describe ADR-018's third-party skill trust model — a different reservation, not this convention.)
- `2026-08-03` now appears in the `required_skills:` context only inside the resolution statement, which AC 1 requires it to carry. All other repo hits name the unrelated spec `2026-08-03-deterministic-story-substrate`.
- Historical surface unchanged: `reserve-only` = 42 hits and `2026-08-03` = 45 hits across `.writ/decision-records/`, `.writ/specs/archive/` (including `2026-05-03-skills-foundation/`), `.writ/research/`, `CHANGELOG.md` — identical to pre-story counts.
- Promotion-bar references left intact and still accurate: `commands/new-skill.md:242`, `skills/gbrain-interop/SKILL.md:155`, `.writ/docs/skills.md:155`. Adoption does not change ADR-014's `promoted` bar.
- `.writ/product/mission.md:133` and `.writ/product/roadmap.md:341` were confirmed consistent with this outcome (mission already describes the adoption as "finally giving that reserved convention a real consumer instead of deprecating it") and needed no edit.
- Mirror parity: `diff system-instructions.md cursor/writ.mdc` → only `289a290,299` (the Self-Dogfooding appendix), proving lines 1–289 are byte-identical.
- `bash scripts/eval.sh` → `Findings: 0`, `Run errors: 0`, `skill-lifecycle` PASS (report `.writ/state/eval-20260811-211923.md`). `bash scripts/gen-skill.sh --check` → exit 0.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `bash scripts/eval.sh` reports `Findings: 0`
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (measured, not asserted — do not claim a live consumer), Rule 2 (full mirror, no gate over § Skills), Rule 3 (active surface only — the foundation spec and ADRs untouched), Rule 4 (`Findings: 0` per story), Rule 5 (no real `required_skills:` declarations in this spec), Rule 7 (status and trigger replaced together by an adoption statement)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [(b) `required_skills:` — resolved by adoption, including the parallel-locations table] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [The four facts the replacement must carry; parallel locations; the byte-identical adapter sentences] — from sub-specs/technical-spec.md → "(b) `required_skills:` adoption — Story 3"
- **Contract:** [Must include (b): the trigger fired 2026-08-03, 8 days before this spec; its terms say "deprecate or revisit"; resolved by adoption, naming Phase 10 progressive disclosure as its first consumer] — from spec.md → ## Contract (Locked)

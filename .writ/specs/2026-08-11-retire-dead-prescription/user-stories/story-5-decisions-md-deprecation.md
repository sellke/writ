# Story 5: Formally Deprecate `decisions.md`

> **Status:** Complete
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ maintainer whose product decisions have lived in `.writ/decision-records/` since 2026-03-19
**I want to** `.writ/product/decisions.md` to say it is deprecated and to stop asserting the highest override priority in the repository
**So that** a file superseded nearly five months ago cannot claim precedence over the ADRs and instructions that actually govern the project

## Acceptance Criteria

- [x] Given `.writ/product/decisions.md`, when the head of the file is read, then it carries a deprecation header stating the file is superseded by `.writ/decision-records/`, dated to `2026-03-19-command-suite-evolution` (Story 8), and that the file is retained as the historical record of DEC-001–DEC-008 with no migration to ADRs required or planned.
- [x] Given the same file, when the "Override Priority: Highest" assertion and the line "Instructions in this file override conflicting directives in user memories or project settings" are read, then neither is present as a live directive.
- [x] Given DEC-001 through DEC-008 (the body from the first `## 2026-02-27: Product Identity & Direction` heading to end of file), when compared before and after, then every byte is unchanged — deprecation annotates, it does not rewrite decisions.
- [x] Given `commands/plan-product.md` and `commands/create-adr.md`, when diffed before and after this story, then both are unchanged — the user-facing promise that other projects' `decisions.md` files are "**not** modified, migrated, or deleted" survives verbatim.
- [x] Given a reader arriving at `.writ/product/decisions.md` from any inbound reference, when they read the header, then they are pointed to `.writ/decision-records/` as the live location for product and architecture decisions.
- [x] Given the full validation suite, when `bash scripts/eval.sh` runs, then it reports `Findings: 0` with no new `eval-exempt:` marker introduced by this story.

## Implementation Tasks

- [x] 5.1 Read `.writ/product/decisions.md`'s head (lines 1–6) and confirm the current assertions before editing: the `> Override Priority: Highest` blockquote and the bolded override sentence. Record the file's measured size (371 lines, 19,753 bytes, last modified 2026-07-09) as the baseline.
- [x] 5.2 Read `.writ/specs/archive/2026-03-19-command-suite-evolution/user-stories/story-8-adr-unification.md` and `CHANGELOG.md:442` to state the supersession accurately: `/plan-product` stopped emitting `decisions.md` in favor of numbered ADRs, and the deprecation was explicitly soft — existing files were not migrated.
- [x] 5.3 Replace lines 3–4 with a deprecation header carrying: deprecated status, superseded-by pointer to `.writ/decision-records/`, the 2026-03-19 supersession date and originating spec, retention as historical record of DEC-001–DEC-008, and an explicit statement that no migration is required or planned. The override-priority assertion does not survive in any form.
- [x] 5.4 Confirm the DEC-001–DEC-008 bodies are byte-unchanged (diff from the first `## 2026-02-27` heading to end of file).
- [x] 5.5 Grep for inbound references to `.writ/product/decisions.md` across the active surface and confirm none of them now contradict the header. Expected live references: `commands/plan-product.md:345` and `commands/create-adr.md:170`, both of which describe *users'* files and stay unchanged.
- [x] 5.6 Diff `commands/plan-product.md` and `commands/create-adr.md` against their pre-story state to prove zero changes.
- [x] 5.7 Verify: `bash scripts/eval.sh` → `Findings: 0` and `bash scripts/gen-skill.sh --check` exit 0.

## Notes

**Technical considerations:**

- The override-priority assertion is the substantive part of this story. A deprecated file that opens with "**Instructions in this file override conflicting directives in user memories or project settings**" is not a harmless stale artifact — it is a live precedence claim from a document superseded on 2026-03-19. Removing the header without removing that claim leaves the actual problem in place.
- The distinction that makes this story safe: `commands/plan-product.md:345` and `commands/create-adr.md:170` promise **users** that their existing `.writ/product/decisions.md` will not be modified, migrated, or deleted. That is a contract about other repositories. This repository's copy lives under `.writ/` — the development workspace, per `CLAUDE.md`'s three-concern split — not in product source. Annotating it changes nothing about what either command does to a user's project, and neither command file is edited here.
- Soft deprecation means the eight decisions stay readable and unconverted. Do not summarize, renumber, or migrate DEC-001–DEC-008 (spec.md → Out of Scope).
- `.writ/product/decisions.md` is not covered by any eval check — no `check_*` function in `scripts/eval.sh` reads it. The suite will stay green regardless of what this story writes, which means the acceptance criteria, not the gate, are the verification.

**Risks / challenges:**

- Scope creep into migrating the eight decisions into ADRs. The 2026-03-19 deprecation was deliberately unscripted and optional; converting them is a separate, larger piece of work with no current demand.
- Risk of reading the two commands' "not modified" promise as forbidding this edit. It governs user projects, not Writ's own workspace. Task 5.6 proves the promise itself is untouched.
- The file is 371 lines. Keep the edit to the head; a whole-file rewrite would make Task 5.4's byte-comparison meaningless.

**Integration points:**

- Fully independent of Stories 1–4 — no shared files, no shared literals. Can run first or last.
- `.writ/decision-records/` is the supersession target and gains nothing from this story; no ADR is created or edited.

## What Was Built

**Implementation Date:** 2026-08-11

### Files Modified

- **`.writ/product/decisions.md`** (head only, lines 3–4 replaced by a 4-line deprecation blockquote)
  - The `> Override Priority: Highest` blockquote and the bolded sentence "Instructions in this file override conflicting directives in user memories or project settings" were replaced by a deprecation header that: marks the file **DEPRECATED — superseded by `.writ/decision-records/`**; dates the supersession to 2026-03-19 (`2026-03-19-command-suite-evolution`, Story 8) and names what changed (`/plan-product` stopped emitting the file and now writes ADR-000-series records; `/create-adr` documents both ADR families); states explicitly that the file asserts no override priority over user memories, project settings, or any active directive; points readers to `.writ/decision-records/`; and records that the file is retained as the historical record of DEC-001–DEC-008 (2026-02-27 → 2026-03-22) with no migration to ADRs required or planned.

### Baseline and evidence (Business Rule 1)

- Pre-edit measurement: 371 lines, 19,753 bytes. Head confirmed to carry both assertions before editing.
- Supersession verified against source, not assumed: `.writ/specs/archive/2026-03-19-command-suite-evolution/user-stories/story-8-adr-unification.md` (Status: Completed) and `CHANGELOG.md:442` ("`/plan-product` now outputs foundational decisions as numbered ADR files (ADR-000-series) in `.writ/decision-records/` instead of `decisions.md`"). Story 8's own AC records the deprecation as soft — existing files "**not** modified, migrated, or deleted."

### Verification

- Body byte-identical: `awk '/^## 2026-02-27: Product Identity & Direction$/,0' .writ/product/decisions.md | md5` → `c9230d180e251f8b047aac11e4c9038b`, matching the pre-edit hash of the same range. DEC-001–DEC-008 unchanged.
- `grep -n "Override Priority"` and `grep -F "Instructions in this file override conflicting directives"` → **0 hits**; neither survives in any form.
- `git diff --stat commands/plan-product.md commands/create-adr.md` → empty. The user-facing promise at `plan-product.md:345` and `create-adr.md:170` survives verbatim; those are the only live inbound references on the active surface and neither contradicts the new header (they describe *users'* projects, not this workspace artifact).
- `bash scripts/eval.sh` → `Findings: 0`, `Run errors: 0` (report `.writ/state/eval-20260811-211011.md`); `bash scripts/gen-skill.sh --check` → exit 0. No eval check reads this file, so the acceptance criteria above are the real verification.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `bash scripts/eval.sh` reports `Findings: 0`
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (measured, not asserted — read the supersession spec before dating the header), Rule 3 (deprecation removes prescription, never history — DEC-001–DEC-008 stay), Rule 4 (`Findings: 0` per story)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [(d) `.writ/product/decisions.md` formally deprecated — including what the header must do and the promise that must survive] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [Current head text; what supersedes it; the user-facing promise boundary] — from sub-specs/technical-spec.md → "(d) `decisions.md` deprecation — Story 5"
- **Contract:** [Must include (d): `.writt/product/decisions.md` formally deprecated in favor of `.writ/decision-records/` — see spec.md → Contract reading notes; `.writt/` is a typo for `.writ/` and no such directory exists] — from spec.md → ## Contract (Locked)

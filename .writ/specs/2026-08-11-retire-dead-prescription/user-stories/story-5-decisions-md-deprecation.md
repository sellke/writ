# Story 5: Formally Deprecate `decisions.md`

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ maintainer whose product decisions have lived in `.writ/decision-records/` since 2026-03-19
**I want to** `.writ/product/decisions.md` to say it is deprecated and to stop asserting the highest override priority in the repository
**So that** a file superseded nearly five months ago cannot claim precedence over the ADRs and instructions that actually govern the project

## Acceptance Criteria

- [ ] Given `.writ/product/decisions.md`, when the head of the file is read, then it carries a deprecation header stating the file is superseded by `.writ/decision-records/`, dated to `2026-03-19-command-suite-evolution` (Story 8), and that the file is retained as the historical record of DEC-001–DEC-008 with no migration to ADRs required or planned.
- [ ] Given the same file, when the "Override Priority: Highest" assertion and the line "Instructions in this file override conflicting directives in user memories or project settings" are read, then neither is present as a live directive.
- [ ] Given DEC-001 through DEC-008 (the body from the first `## 2026-02-27: Product Identity & Direction` heading to end of file), when compared before and after, then every byte is unchanged — deprecation annotates, it does not rewrite decisions.
- [ ] Given `commands/plan-product.md` and `commands/create-adr.md`, when diffed before and after this story, then both are unchanged — the user-facing promise that other projects' `decisions.md` files are "**not** modified, migrated, or deleted" survives verbatim.
- [ ] Given a reader arriving at `.writ/product/decisions.md` from any inbound reference, when they read the header, then they are pointed to `.writ/decision-records/` as the live location for product and architecture decisions.
- [ ] Given the full validation suite, when `bash scripts/eval.sh` runs, then it reports `Findings: 0` with no new `eval-exempt:` marker introduced by this story.

## Implementation Tasks

- [ ] 5.1 Read `.writ/product/decisions.md`'s head (lines 1–6) and confirm the current assertions before editing: the `> Override Priority: Highest` blockquote and the bolded override sentence. Record the file's measured size (371 lines, 19,753 bytes, last modified 2026-07-09) as the baseline.
- [ ] 5.2 Read `.writ/specs/archive/2026-03-19-command-suite-evolution/user-stories/story-8-adr-unification.md` and `CHANGELOG.md:442` to state the supersession accurately: `/plan-product` stopped emitting `decisions.md` in favor of numbered ADRs, and the deprecation was explicitly soft — existing files were not migrated.
- [ ] 5.3 Replace lines 3–4 with a deprecation header carrying: deprecated status, superseded-by pointer to `.writ/decision-records/`, the 2026-03-19 supersession date and originating spec, retention as historical record of DEC-001–DEC-008, and an explicit statement that no migration is required or planned. The override-priority assertion does not survive in any form.
- [ ] 5.4 Confirm the DEC-001–DEC-008 bodies are byte-unchanged (diff from the first `## 2026-02-27` heading to end of file).
- [ ] 5.5 Grep for inbound references to `.writ/product/decisions.md` across the active surface and confirm none of them now contradict the header. Expected live references: `commands/plan-product.md:345` and `commands/create-adr.md:170`, both of which describe *users'* files and stay unchanged.
- [ ] 5.6 Diff `commands/plan-product.md` and `commands/create-adr.md` against their pre-story state to prove zero changes.
- [ ] 5.7 Verify: `bash scripts/eval.sh` → `Findings: 0` and `bash scripts/gen-skill.sh --check` exit 0.

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

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/eval.sh` reports `Findings: 0`
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (measured, not asserted — read the supersession spec before dating the header), Rule 3 (deprecation removes prescription, never history — DEC-001–DEC-008 stay), Rule 4 (`Findings: 0` per story)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [(d) `.writ/product/decisions.md` formally deprecated — including what the header must do and the promise that must survive] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [Current head text; what supersedes it; the user-facing promise boundary] — from sub-specs/technical-spec.md → "(d) `decisions.md` deprecation — Story 5"
- **Contract:** [Must include (d): `.writt/product/decisions.md` formally deprecated in favor of `.writ/decision-records/` — see spec.md → Contract reading notes; `.writt/` is a typo for `.writ/` and no such directory exists] — from spec.md → ## Contract (Locked)

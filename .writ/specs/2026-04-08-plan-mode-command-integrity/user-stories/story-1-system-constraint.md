# Story 1: System-Level Hard Constraint

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ developer (AI system)  
**I want to** have an explicit hard constraint preventing Plan Mode from absorbing command workflows  
**So that** every planning command produces its documented artifacts instead of treating the conversation as the deliverable

## Acceptance Criteria

- [ ] **AC1:** Given `system-instructions.md` in the repository root, when the Prime Directive section is read, then a fourth bullet exists under `### Hard Constraints` whose substance matches the contract: Plan Mode is a discovery phase within commands, not a substitute for documented phases or artifacts; after discovery the command resumes and produces its documented deliverables.

- [ ] **AC2:** Given the same file, when locating behavioral rules, then the new constraint appears only in `## Prime Directive` → `### Hard Constraints` (alongside anti-reversal, anti-confirmation, anti-filler), not under Judgment Principles or elsewhere — same imperative tone and “non-negotiable” framing as the existing three bullets.

- [ ] **AC3:** Given `cursor/writ.mdc`, when its body (below YAML frontmatter) is compared to `system-instructions.md`, then the Hard Constraints subsection is textually aligned: the new fourth bullet is present and matches the canonical wording in `system-instructions.md` for the shared Prime Directive content.

- [ ] **AC4:** Given the new hard-constraint bullet text, when it is read end-to-end, then it explicitly states that planning commands create files and stop (no offers to implement, build, or code) and directs users who want fast implementation without the full artifact pipeline to `/prototype`.

## Implementation Tasks

- [ ] **1.1** Read `system-instructions.md` and `cursor/writ.mdc` in full; confirm current three Hard Constraints, frontmatter-only differences in `cursor/writ.mdc`, and that `.cursor/rules/writ.mdc` resolves to `cursor/writ.mdc` via symlink (no duplicate body to edit under `.cursor/rules/`).

- [ ] **1.2** Add the fourth Hard Constraint to `system-instructions.md` immediately after the anti-filler bullet and before `### Judgment Principles`, using the concise contract text from `.writ/specs/2026-04-08-plan-mode-command-integrity/sub-specs/technical-spec.md` (Layer 1 — “Never let Plan Mode absorb…” through “…point them to `/prototype`.”).

- [ ] **1.3** Apply the same body edit to `cursor/writ.mdc` in the corresponding `### Hard Constraints` block, preserving existing YAML frontmatter (`always_applied` / `alwaysApply` as applicable); do not alter unrelated sections.

- [ ] **1.4** Verify `.cursor/rules/writ.mdc` shows the new constraint when read through the symlink (e.g. `readlink` + file read, or single open of the resolved path).

- [ ] **1.5** Diff-check: shared Prime Directive body between `system-instructions.md` and `cursor/writ.mdc` (excluding frontmatter) is identical for the edited region; fix any drift introduced by the edit.

- [ ] **1.6** Spot-check `AGENTS.md` or other docs that claim “three Hard Constraints” — update count or phrasing only if they explicitly enumerate a fixed number (avoid stale documentation).

- [ ] **1.7** Final verification: all ACs satisfied; record completion in the story checklist and note any doc touch-ups in the implementation summary.

## Notes

- This is the foundation story — Stories 2 and 3 reference this hard constraint.
- The constraint must sit alongside existing Hard Constraints (anti-reversal, anti-confirmation, anti-filler) — same section, same tone.
- `cursor/writ.mdc` has slightly different frontmatter (`alwaysApply` YAML) but the mirrored body content must match `system-instructions.md` for the Prime Directive sections both files share.
- Platform Plan Mode behavior is not directly controllable; strength comes from instruction language — keep the bullet absolute and operational, not advisory.

## Definition of Done

- [ ] All acceptance criteria checked off in this story file after verification
- [ ] All implementation tasks completed
- [ ] `system-instructions.md` and `cursor/writ.mdc` updated in parallel; symlinked rule file reflects the change without a second manual edit
- [ ] No unintended edits outside Hard Constraints / related doc fixes from task 1.6
- [ ] Brief implementation summary available for dependent stories (2–3) if needed

## Context for Agents

- **Contract:** [`.writ/specs/2026-04-08-plan-mode-command-integrity/spec.md` — Contract Summary, Business Rules → Hard Constraint (system-instructions), Implementation Approach → Layer 1]
- **Canonical wording:** [`.writ/specs/2026-04-08-plan-mode-command-integrity/sub-specs/technical-spec.md` — Layer 1: proposed constraint text and sync targets (`system-instructions.md` ↔ `cursor/writ.mdc` manual; `.cursor/rules/writ.mdc` via symlink)]
- **Business rules:** [Commands own the workflow; Plan Mode is a phase; conversation is not the deliverable; planning commands produce markdown artifacts and terminate; `/prototype` is the legitimate escape valve for fast implementation without full artifact creation]
- **Experience:** [Discovery in Plan Mode → explicit return to command phases → artifact creation → completion; failure mode to prevent: Plan Mode absorption — chat treated as done, files never written]
- **Error map rows:** []
- **Shadow paths:** []

**Format reference:** `.writ/docs/context-hint-format.md`

**Files in scope (this story):** `system-instructions.md`, `cursor/writ.mdc` (and, by symlink, `.cursor/rules/writ.mdc`); optional doc fixes if task 1.6 finds stale “three constraints” references

---

## Proposed constraint text (implementer copy-paste)

Use this block verbatim unless the spec is formally revised:

```markdown
- **Never let Plan Mode absorb a command's workflow.** When a command uses
  Plan Mode for discovery, the conversation is a phase — not the deliverable.
  After discovery, resume the command's documented phases and produce its
  documented artifacts. Planning commands create files and stop. They never
  offer to implement, build, or code. If the user wants fast implementation,
  point them to `/prototype`.
```

# Story 2: Per-Command Completion Sections

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ developer (AI system consuming the command files)  
**I want to** have explicit `## Completion` sections in all planning commands that name required artifacts and prohibit implementation offers  
**So that** every planning command produces its documented deliverables and terminates cleanly

## Acceptance Criteria

- [ ] **AC1:** Given the nine planning command files under `commands/` (`create-spec.md`, `plan-product.md`, `new-command.md`, `create-issue.md`, `create-adr.md`, `create-uat-plan.md`, `research.md`, `design.md`, `edit-spec.md`), when each file is read end-to-end, then a `## Completion` section exists.

- [ ] **AC2:** Given any of those nine commands, when the `## Completion` section is read, then it includes numbered success criteria that name specific deliverable artifacts using concrete paths or path patterns (for example `.writ/specs/.../spec.md`, `.writ/issues/{bugs,features,improvements}/`, `commands/*.md`), not only vague outcomes.

- [ ] **AC3:** Given any of those nine commands, when the `## Completion` section is read, then it includes a **Terminal constraint** (or equivalent wording) that prohibits offering to implement, build, or execute what was planned or produced, references the appropriate downstream command(s) for implementation, and points quick-build users to `/prototype`, consistent with the hard constraint language established in Story 1.

- [ ] **AC4:** Given any of those nine commands, when the `## Completion` section is read, then it includes a **Suggested next step** (or **Next step**) line naming the natural downstream action from the spec’s Affected Commands table (e.g. `/implement-spec`, `/create-spec --from-issue`, manual UAT execution where applicable).

- [ ] **AC5:** Given `commands/create-spec.md`, which already defines five completion success criteria, when it is updated for this story, then those five criteria remain present and unchanged in substance, and the **Suggested next step** plus **Terminal constraint** lines are added (appended or integrated) without replacing or removing the existing checklist items.

## Implementation Tasks

- [ ] **2.1** Read all nine command files in `commands/` and record a short matrix: presence or absence of `## Completion`, and for `create-spec.md` capture the exact existing success criteria text to preserve (AC5).

- [ ] **2.2** Update `commands/create-spec.md`: keep the existing five completion criteria; add **Suggested next step** and **Terminal constraint** per `sub-specs/technical-spec.md` → `/create-spec` (and align wording with Story 1’s system-instructions constraint).

- [ ] **2.3** Add new `## Completion` sections to commands that lack them, using the template in `spec.md` → ## Implementation Approach → ### Layer 2: Per-Command Completion Sections: `plan-product.md`, `new-command.md`, `create-issue.md`, `create-adr.md`, `create-uat-plan.md`, `research.md` — artifacts and next steps must match `spec.md` → ## 📋 Business Rules → ### Affected Commands and `sub-specs/technical-spec.md` → Per-Command Specifications.

- [ ] **2.4** Audit `commands/design.md` and `commands/edit-spec.md`: if `## Completion` is missing, add it; if present, update so artifacts, **Suggested next step**, and **Terminal constraint** match actual command outputs and the technical-spec rows for `/design` and `/edit-spec`.

- [ ] **2.5** Verify all nine files: each has `## Completion`; each lists concrete artifacts; each includes terminal constraint and next-step pointer; `create-spec.md` still contains its original five success conditions (AC5).

- [ ] **2.6** Final pass: ensure Completion criteria in each command align with phases elsewhere in the same file that create files (no promised artifacts omitted from Completion).

## Notes

- `/create-spec` already has five completion criteria — do not remove them; append **Suggested next step** and **Terminal constraint** (or integrate without deleting the five items).
- For `design.md` and `edit-spec.md`, confirm current state before editing; add vs update accordingly.
- This is the highest-effort story in the spec (nine files); edits are small and should follow the shared template for consistency.
- Terminal constraint wording should stay consistent with Story 1 without necessarily pasting the full system-instructions block into every command.

## Definition of Done

- [ ] All acceptance criteria in this story are satisfied and checked off after verification
- [ ] All implementation tasks are completed
- [ ] All nine planning commands ship updated `## Completion` sections as specified
- [ ] No regression: `create-spec` completion criteria preserved per AC5
- [ ] Brief summary of touched files is available for reviewers or release notes

## Context for Agents

- **Business rules:** [spec.md → ## 📋 Business Rules → ### Per-Command Rules (four requirements every `## Completion` must satisfy); spec.md → ## 📋 Business Rules → ### Affected Commands (artifacts and natural next step per command)]
- **Experience:** [spec.md → ## 🎯 Experience Design → ### The Fix (Journey After) and ### State Catalog → **Completion** row (summary + next-step pointer, no implementation offers)]
- **Shadow paths:** [Happy path: discovery (where used) → artifact phases → files on disk → Completion summary; failure to avoid: conversation treated as deliverable — mitigated by explicit artifact list + terminal constraint]
- **Error map rows:** []

**Format reference:** `.writ/docs/context-hint-format.md`

**Files in scope (this story):** `commands/create-spec.md`, `commands/plan-product.md`, `commands/new-command.md`, `commands/create-issue.md`, `commands/create-adr.md`, `commands/create-uat-plan.md`, `commands/research.md`, `commands/design.md`, `commands/edit-spec.md`

**Template reference:** `spec.md` → ## Implementation Approach → ### Layer 2: Per-Command Completion Sections (markdown template); per-command artifact/next-step detail: `sub-specs/technical-spec.md` → ## Layer 2: Per-Command Completion Sections → ### Per-Command Specifications

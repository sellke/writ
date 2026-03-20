# Story 1 — Inline Prime Directive into Product Source Files

> **Status:** Complete
> **Priority:** High
> **Dependencies:** None

## User Story

As a **Writ user**, I want the system instructions to include specific anti-sycophancy principles so that every AI session starts with behavioral guidelines that promote honest assessment over comfortable agreement.

## Acceptance Criteria

- [ ] **Given** `system-instructions.md` line 32 references `.writ/docs/best-practices.md`, **when** this story is complete, **then** line 32 is replaced with the full Prime Directive section and the phantom reference is gone.
- [ ] **Given** `cursor/writ.mdc` contains the same phantom reference, **when** this story is complete, **then** it has the identical Prime Directive section as `system-instructions.md`.
- [ ] **Given** the Prime Directive is added, **when** measuring the addition, **then** it is under 35 lines of new content.
- [ ] **Given** a fresh Writ installation via `install.sh`, **when** the installer copies `system-instructions.md`, **then** the Prime Directive content is included without any installer changes.

## Implementation Tasks

- [ ] Write tests: verify both files contain the Prime Directive section header, verify no reference to `best-practices.md` remains, verify both files are identical in the relevant section
- [ ] Replace line 32 in `system-instructions.md` with the Prime Directive section from the spec
- [ ] Apply the identical replacement in `cursor/writ.mdc`
- [ ] Verify both files are valid markdown with clean heading hierarchy
- [ ] Run `install.sh --dry-run` to confirm no installer changes are needed
- [ ] Verify line count: confirm the addition is under 35 lines

## Notes

- **Self-dogfooding:** In this repo, `.cursor/rules/writ.mdc` symlinks to `cursor/writ.mdc` and `.cursor/system-instructions.md` symlinks to `system-instructions.md`. Editing the product source files automatically updates the active installation. Do not edit the symlinked copies.
- **Sync rule:** The Prime Directive section must be byte-for-byte identical in both files. The files diverge in other sections (writ.mdc has the Self-Dogfooding section), so only the Prime Directive block needs to match.

## Definition of Done

- [ ] Phantom reference removed from both files
- [ ] Prime Directive section present and identical in both files
- [ ] Under 35 lines added
- [ ] No changes to `install.sh` or any other files
- [ ] Both files render as valid, well-structured markdown

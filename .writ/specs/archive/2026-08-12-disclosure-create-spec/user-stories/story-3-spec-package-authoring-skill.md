# Story 3: Author the `spec-package-authoring` Skill

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer whose contract has just been locked
**I want to** the visual-reference intake, the date and owner resolution, the directory tree, the `spec.md` body requirements, and the whole 121-line `spec-lite.md` template authored as one skill
**So that** 6,905 bytes of file-authoring detail leave the command, while the six sentences `eval.sh` pins stay behind untouched for Story 6 to keep

## Acceptance Criteria

- [ ] Given rule-inventory rows 71–74 and 77–97 span visual references, the tree, the `spec.md` body, the writeback disposition, and the `spec-lite.md` template, when this story lands, then `skills/spec-package-authoring/SKILL.md` carries rows 72–74, 77–79, 86, 89, the disposition half of 90, and 91–97 — including the five-option visual-reference `AskQuestion` with its ids verbatim, the owner-resolution `bash` block with its `@unknown` fallback and warning text, the three-audience `spec-lite.md` template, the **100-line hard limit**, the 35/35/30 section budgets, the four over-budget tactics in order, and the backward-compatibility note.
- [ ] Given `eval.sh:1778–1779`, `:1825`, and `:1972–1973` pin six literals into the command, when this story lands, then rows 80–85, 87–88 and the never-blocks half of row 90 are **absent from the skill** and left in place in the command for Story 6 — the `> **Dependencies:**` header block, the "emit for every new spec, `[]` when none" rule, `exact spec-folder IDs`, the spec-level-versus-story-level warning, `Canonical complete-family spelling`, the `Amends:`/`Extends:` banner rule, the `python3 scripts/supersession-writeback.py apply` invocation, and "this step never blocks or fails spec package creation".
- [ ] Given the `spec-lite.md` budget is itself enforced by `scripts/eval.sh check_length` at 100 lines, when this story lands, then the skill states the limit as a hard constraint and names the check, and no figure in the template — 100, 35, 35, 30, ~5, ~10, ~90 — is changed.
- [ ] Given Compression Ledger entry 4 targets ~500 bytes, when this story lands, then *Line Budget Enforcement* (697–706), which restates the 35/35/30 figures already present three times inside the template plus the total already stated at 598, is contracted to a pointer at the one authority, the **measured** yield is recorded, and every one of the four over-budget tactics survives as a rule.
- [ ] Given this story is additive, when this story lands, then `git diff --name-only` shows no change to `commands/create-spec.md`, `bash scripts/lint-skill.sh skills/spec-package-authoring/SKILL.md` exits 0, `bash scripts/gen-skill.sh --check` reports no delta, and `bash scripts/eval.sh` reports no new findings.

## Implementation Tasks

- [ ] 3.1 Read Story 1's namespace reconciliation and confirm `spec-package-authoring` survived. Re-measure the pinned/movable split: Step 2.4 (562–583) is 2,554 bytes of which 564–577 (2,017) is pinned; Step 2.4b (584–597) is 1,629 bytes of which 588–596 (1,291) is pinned. The boundary sits **inside a bullet list**, so confirm by line range before cutting
- [ ] 3.2 Run `/new-skill spec-package-authoring` — bare-imperative description covering the package's file set and each file's required content; manifest entry; `gen-skill.sh --check`
- [ ] 3.3 Author rows 72–74 (visual references), 77–79 (date, owner block, tree), 86 (`spec.md` body sections), 89 and the disposition half of 90 (writeback behavior, `skipped_other` / `broken`)
- [ ] 3.4 Author rows 91–97 — the full `spec-lite.md` template, the budget arithmetic, the content-selection guidelines, the four over-budget tactics, and the backward-compatibility note
- [ ] 3.5 Apply Compression Ledger entry 4; measure and record the yield; confirm all four tactics and the backward-compatibility note survive
- [ ] 3.6 Verify no pinned literal was copied into the skill: `grep -n 'supersession-writeback.py\|exact spec-folder IDs\|Canonical complete-family spelling\|> \*\*Dependencies:\*\*' skills/spec-package-authoring/SKILL.md` returns nothing
- [ ] 3.7 Verify: `bash scripts/lint-skill.sh`, `bash scripts/gen-skill.sh --check`, `bash scripts/eval.sh`, `git diff --name-only`; check off rule-inventory rows 71–97 with destinations and record the skill's measured byte size

## Notes

**Technical considerations:**

- **This story has the highest pin density in the spec.** Steps 2.4 and 2.4b are each split down the middle: the rules `eval.sh` names stay in the command, the prose around them moves. Cutting by section heading rather than by line range takes a pinned literal along.
- Row 90 splits deliberately. *"This step never blocks or fails spec package creation — proceed to Step 2.5 regardless"* is a control-flow gate that stays in the command. The `skipped_other` / `broken` disposition detail is reference material and moves.
- The `spec-lite.md` template is 121 lines and 3,750 bytes — the largest movable block in Phase 2, and it is read once per run, at the very end.
- The owner-resolution block (row 78) is a literal `bash` snippet including the `@unknown` fallback and its warning text. Move it whole; it is executable content, not prose.
- Step 1.5's visual-reference gate sits in Phase 1 by position and in the package by subject — its handlers write `mockups/`, `mockups/current/`, and `mockups/component-inventory.md`. The gate line stays in the command for the phase list; the five options and their handlers move.
- `edit-spec` and `verify-spec` are prospective consumers named in spec.md's extraction map, not evidence. `status_evidence` records only the actual consumer.

**Risks / challenges:**

- **Re-numbering the `spec-lite.md` budget.** The 35/35/30 split does not add to 100 and never did — the difference is structural lines, explained in row 95. Making the arithmetic "correct" changes the budget.
- **Compression Ledger entry 4 is a pointer, not a deletion.** The four over-budget tactics are rules and are not eligible; only the restated figures are.
- **Dropping the backward-compatibility note** as obsolete. It tells an agent not to rewrite old specs it encounters; deleting it licenses exactly that.
- The `/design` command's wireframe conventions are referenced, not restated, by row 73. Keep it a prose reference — `Read commands/design.md` would fail the lint.

**Integration points:**

- Story 4 authors Steps 2.5–2.8, which run between the tree creation and the final review. The two skills must not both claim Step 2.6's story-file content.
- Story 6 keeps rows 80–85, 87–88 and the never-blocks rule in the command and places them relative to the phase list.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/spec-package-authoring/SKILL.md` exits 0
- [ ] `bash scripts/gen-skill.sh --check` reports no delta
- [ ] `bash scripts/eval.sh` shows no new findings
- [ ] No pinned literal present in the skill (grep verified)
- [ ] `git diff --name-only` shows no path under `commands/`
- [ ] Compression Ledger entry 4's measured yield recorded
- [ ] Rule-inventory rows 71–74, 77–79, 86, 89, 90 (disposition), 91–97 checked off; rows 80–85, 87–88, 90 (gate) marked as retained in the command
- [ ] Skill's measured byte size recorded for Story 6's ceiling arithmetic

## Context for Agents

- **Business rules:** BR2, BR3, BR6 (pinned strings), BR7, BR10 — from spec.md → 📋 Business Rules
- **Rule inventory rows:** 71–97, with 80–85, 87–88 and half of 90 retained in the command — from sub-specs/technical-spec.md → Rule Inventory
- **Pin table:** `> **Dependencies:**`, `exact spec-folder IDs`, `Canonical complete-family spelling`, `Amends`, `supersession-writeback.py` — from spec.md → The finding that reframes the work
- **Compression Ledger entry 4** — from sub-specs/technical-spec.md → Compression Ledger
- **Verification commands** — from sub-specs/technical-spec.md → Verification

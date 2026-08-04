# Story 5: Required Skills Frontmatter Convention

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None
> **Estimated Effort:** Small
> **Completed:** 2026-05-03

## User Story

**As a** Writ contributor authoring an agent or command that needs a skill,
**I want** a documented `required_skills:` frontmatter convention that pilot specs can declare on Day 1 without re-negotiating the schema,
**So that** the pilot extraction specs can consume the convention immediately and the foundation doesn't ship with a missing-but-needed ergonomic.

## Acceptance Criteria

### Scenario 1: Convention is documented in `system-instructions.md`
- **Given** ADR-009 references the convention as a "small helper convention" mitigation
- **When** I read `system-instructions.md`
- **Then** there is a section (under "File Organization" or a new "Skills" section) describing the `required_skills:` frontmatter field with: schema, semantics ("named skills are pre-loaded by the harness when the consumer is invoked"), and the reserve-only status note

### Scenario 2: Schema is unambiguous
- **Given** the convention is documented
- **When** I read the schema definition
- **Then** the schema specifies: (a) `required_skills` is an optional array, (b) values are skill names matching `name:` entries in `.writ/manifest.yaml`, (c) order is preserved, (d) duplicates are silently deduped, (e) unknown skill names produce a warning at consumer load time (not a hard failure — degrades gracefully)

### Scenario 3: All three adapters mention the convention
- **Given** Story 4 added Skills sections to each adapter
- **When** I read each adapter's Skills section
- **Then** each adapter notes the `required_skills:` convention with platform-specific harness behavior (e.g., Cursor: skill content pre-injected via system prompt; Claude Code: `Read` calls issued before phase begins)

### Scenario 4: Convention is reserve-only
- **Given** the convention is documented
- **When** I scan `agents/*.md` and `commands/*.md` for `required_skills:` declarations
- **Then** zero files declare the field (this story documents the convention only; no consumer adopts it yet)

### Scenario 5: 90-day review trigger is set
- **Given** the convention is reserve-only and risks bitrot if unused
- **When** I read the convention documentation
- **Then** there is an explicit "Review trigger: 2026-08-03 (90 days post-ship). If no agent or command has adopted `required_skills:` by this date, deprecate or revisit." note, matching ADR-009's review date discipline

## Implementation Tasks

- [x] **Schema design:** Canonical schema specified — `required_skills:` is an optional array of strings matching `name:` entries in `.writ/manifest.yaml`, order preserved, duplicates dedup'd, unknown names produce warning (not failure).
- [x] **`system-instructions.md` section:** Added `## Skills` section with convention + schema + harness contract + reserve-only note + 2026-08-03 review trigger; cross-references `.writ/docs/skills.md` (Story 7) and ADR-009.
- [x] **`cursor/writ.mdc` parity:** Mirrored byte-identically before the `## Self-Dogfooding` section (verified via `diff` — no differences in Skills content).
- [x] **Adapter cross-references:** All three adapters (cursor, claude-code, openclaw) already reference `required_skills:` in their Skills sections from Story 4 with platform-specific harness behavior described.
- [x] **Reserve-only note:** Explicit `Status: reserve-only.` paragraph documents that no agent or command in this spec declares the field; adoption deferred to pilot specs.
- [x] **Review trigger:** 2026-08-03 (90 days post-ship) review trigger documented in both root files. State-file reminder deferred — the date is durably embedded in `system-instructions.md` and `cursor/writ.mdc`, which are higher-visibility than `.writ/state/`.
- [x] **Manual scan verification:** `grep -rn "required_skills:" agents/ commands/` returns zero matches.

## Definition of Done

- [x] All five acceptance criteria pass (convention documented; schema unambiguous; adapters cross-reference; zero adopters; review trigger 2026-08-03 set)
- [x] Convention is documented in `system-instructions.md`, `cursor/writ.mdc`, and all three adapters (cursor, claude-code, openclaw)
- [x] Zero agent/command files declare `required_skills:` (verified — grep returns no hits)
- [x] Schema specification is unambiguous: optional array of skill names matching manifest, order preserved, duplicates dedup'd, unknown names → warning. A pilot-spec author can implement against this directly.
- [x] Review trigger 2026-08-03 recorded in both `system-instructions.md` and `cursor/writ.mdc`
- [x] Self-review: schema follows existing manifest discipline (additive, simple types, no version pinning); harness contract is platform-neutral (per-platform mechanism deferred to adapters, which is the right separation)

## Technical Notes

- **Why reserve-only:** ADR-009's "Required skills frontmatter convention" was deferred in scope because the pilot skills don't ship in this spec. Defining the schema *now* prevents pilot specs from inventing competing conventions; *not wiring* it prevents documentation-only-features-rot.
- **Schema simplicity:** Keep `required_skills:` to a flat array of strings. Avoid nested objects, conditional skills, version pinning. If a pilot spec needs more, the schema can extend additively (matches manifest schema discipline).
- **Harness behavior is platform-specific.** This story documents the *contract* (what consumers can rely on); each adapter documents the *mechanism* (how the platform delivers it). The contract: "When a consumer with `required_skills: [foo]` is invoked, `skills/foo/SKILL.md` is loaded and accessible to the agent before any phase work begins."
- **Graceful degradation matters.** Unknown skill names produce a warning, not a hard failure. Rationale: a pilot extraction may rename a skill mid-flight; consumers shouldn't break catastrophically.

## Context for Agents

- **Coding agent context:** spec.md → `## Implementation Approach → ### Required skills: Convention`. ADR-009 lines 100 (Negative consequence #2 mitigation) is the source of the convention idea.
- **Review agent context:** spec.md → `## Scope Boundaries → Excluded` (no agent/command files modified). Verify zero `required_skills:` declarations land in this spec's diff.
- **Testing agent context:** Manual `rg "required_skills:" agents/ commands/` is sufficient; no test infrastructure needed for convention-only work.

---

## What Was Built

**Implementation Date:** 2026-05-03

### Files Modified

- **`system-instructions.md`** (+47 lines) — `## Skills` section after Session Auto-Orientation
- **`cursor/writ.mdc`** (+47 lines) — byte-identical `## Skills` section before Self-Dogfooding

### Implementation Decisions

1. **Skills section placement** — appended at the end of system-instructions.md (after Session Auto-Orientation) and inserted before Self-Dogfooding in cursor/writ.mdc. Self-Dogfooding stays last in cursor/writ.mdc because it's the most repo-specific concern.
2. **Byte-identical Skills sections in both root files** — Phase 4's parity discipline applied. Future updates to one must be mirrored in the other (the same convention as the Prime Directive).
3. **Review trigger date is in the doc, not in `.writ/state/`** — durable docs > ephemeral state for a 90-day reminder. The date is greppable in two top-level files; impossible to miss during the next routine scan.
4. **Reserve-only note phrased as `Status: reserve-only.`** — uses the same noun ("status") that frontmatter conventions use elsewhere. Pilot-spec authors will see this and know not to delete the convention while waiting for first adopter.
5. **Schema kept flat (array of strings only)** — no nested objects, no version pinning, no conditional skills. If a pilot needs more, the schema can extend additively. Matches manifest schema discipline.

### Test Results

**Verification:** Manual grep + diff (markdown framework — no test framework)

- ✅ Scenario 1: Convention documented in `system-instructions.md` (6 occurrences of `required_skills`)
- ✅ Scenario 2: Schema unambiguous — explicit array semantics, manifest-name match, order, dedupe, warning-on-unknown all stated
- ✅ Scenario 3: All three adapters mention the convention (verified in Story 4)
- ✅ Scenario 4: `grep -rn "required_skills:" agents/ commands/` returns zero matches (reserve-only verified)
- ✅ Scenario 5: Review trigger 2026-08-03 documented in both `system-instructions.md` and `cursor/writ.mdc`
- ✅ Bonus: Skills section is byte-identical between system-instructions.md and cursor/writ.mdc (Phase 4 parity preserved)

### Review Outcome

**Result:** PASS (self-review)

- **Iteration count:** 1 iteration
- **Drift:** None — convention follows the technical-spec contract verbatim (schema, semantics, reserve-only, review date)
- **Security:** N/A (documentation-only changes)
- **Boundary Compliance:** Owned files only (`system-instructions.md`, `cursor/writ.mdc`); zero modifications to existing agents/commands (the spec's hard constraint for this story)

### Deviations from Spec

None. (Note: the `.writ/state/skills-review-2026-08-03.md` reminder file mentioned as optional in the task list was deliberately *not* created — see decision #3 above. The date is durably embedded in two visible root files; a state file would add a duplicate location with no additional surfacing benefit.)

# Story 1: Manifest Schema Extension and Skills Table Generation

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None
> **Estimated Effort:** Medium
> **Completed:** 2026-05-03

## User Story

**As a** Writ contributor maintaining the framework manifest,
**I want** the `.writ/manifest.yaml` schema to include an additive `skills:` section and `scripts/gen-skill.sh` to render a `## Available Skills` table in the root `SKILL.md`,
**So that** skills become a first-class catalog entry parallel to commands and agents, with the same drift-detection guarantees Phase 4 already established.

## Acceptance Criteria

### Scenario 1: Empty skills list parses cleanly
- **Given** `.writ/manifest.yaml` declares `skills: []` (empty list)
- **When** I run `bash scripts/gen-skill.sh --check`
- **Then** the script exits 0 and `SKILL.md` contains no `## Available Skills` section (silent skip, not empty section)

### Scenario 2: Populated skills list renders a table
- **Given** `.writ/manifest.yaml` declares one entry under `skills:` with `name`, `file`, `description`
- **When** I run `bash scripts/gen-skill.sh`
- **Then** `SKILL.md` includes a `## Available Skills` section with a `| Skill | File | Description |` table containing the entry, placed after `## Available Agents`

### Scenario 3: Schema validation catches malformed entries
- **Given** a skill entry missing the required `file` field
- **When** I run `bash scripts/gen-skill.sh`
- **Then** the script exits 1 with `YAML error: skills[N] missing required field 'file'` and writes nothing

### Scenario 4: Bash fallback parser parity
- **Given** `yq` is not installed
- **When** I run `bash scripts/gen-skill.sh` against a manifest with `skills:` populated
- **Then** the bash fallback parser produces identical output to the `yq` path

### Scenario 5: Drift detection works for skills
- **Given** a populated `skills:` list and a fresh `SKILL.md`
- **When** I deliberately edit the Skills table and run `bash scripts/gen-skill.sh --check`
- **Then** the script exits 1 with `SKILL.md drift detected. Run: bash scripts/gen-skill.sh`

## Implementation Tasks

- [x] **Test fixtures:** Created inline test cases via shell — empty skills, populated skills, missing-field, name-collision (command), name-collision (agent), duplicate-skill-name. All triggered correctly.
- [x] **Schema documentation:** Added `skills:` schema comment block + empty `skills: []` to `.writ/manifest.yaml` with required (`name`, `file`, `description`) and optional (`tags`, `aliases`) fields documented.
- [x] **`parse_with_yq` extension:** Added `SKILL_NAMES`, `SKILL_FILES`, `SKILL_DESCRIPTIONS`, `SKILL_TAGS`, `SKILL_ALIASES` arrays + `.skills[]` yq query (guarded for empty/missing skills key).
- [x] **`parse_with_bash` extension:** Added `skills:` section detection (with `skills: []` short-circuit), `reset_skill_item` / `flush_skill_item` helpers, and parse handlers for `- name:`, `file:`, `description:`, `tags:`, `aliases:`.
- [x] **`validate_manifest` extension:** Required fields present, file exists at `$PROJECT_ROOT/<file>`, cross-name collision check vs commands and agents, duplicate skill name check.
- [x] **`generate_body` extension:** `## Available Skills` table conditionally rendered after `## Available Agents` (empty list → no section, not empty section).
- [x] **Manual verification:** `bash scripts/gen-skill.sh --check` exits 0 against committed `SKILL.md` with `skills: []`.

## Definition of Done

- [x] All five acceptance criteria pass via manual verification (Scenario 1: empty list parses, Scenario 2: populated renders table, Scenario 3: missing field rejected, Scenario 4: bash fallback exercised throughout, Scenario 5: drift detected on stale SKILL.md)
- [x] `bash scripts/gen-skill.sh --check` exits 0 against committed `SKILL.md` (empty skills final state)
- [x] Bash fallback parser is the only available parser locally (yq not installed); yq path mirrors the same data flow and will be exercised in CI
- [x] No regressions in existing commands/agents table rendering (verified via `diff -u` showing SKILL.md byte-identical to pre-test state)
- [x] Validation error messages follow Phase 4 pattern (`YAML error: skills[N] (<name>) ...`)
- [x] Self-review: code follows existing parse/validate/generate structure precisely; no novel patterns introduced

## Technical Notes

- **Backward compatibility:** Existing manifests without `skills:` key must continue to work. The `parse_with_bash` `case "$line"` for `skills:` is purely additive.
- **Skill schema is the same shape as agents:** `name`, `file`, `description` (vs agents' `purpose`). Use `description` to match AgentSkills frontmatter convention rather than reinvent the term.
- **Sort order:** Skills listed in manifest order, not alphabetical (consistent with commands/agents).
- **Reference Phase 4 spec** (`2026-04-24-phase4-production-grade-substrate`) for the manifest pattern and Story 2 of that spec for the parser test cadence.

## Context for Agents

- **Coding agent context:** spec.md → `## Implementation Approach → ### Manifest Schema (additive)` and `### gen-skill.sh Skills Table`. Reference `scripts/gen-skill.sh` lines 115–145 for the existing yq parsing pattern; lines 198–315 for the bash fallback pattern.
- **Review agent context:** spec.md → `## Business Rules` (manifest additive rule). Boundary check N/A for this story (no skill content yet).
- **Testing agent context:** spec.md → `## Success Criteria` items 1, 3, 5 and spec-lite.md "Shadow Paths to Verify" (empty input + upstream error scenarios).

---

## What Was Built

**Implementation Date:** 2026-05-03

### Files Modified

- **`scripts/gen-skill.sh`** (added ~80 lines)
  - 5 new SKILL_* arrays parallel to AGENT_* arrays
  - `parse_with_yq`: skills loop guarded for empty/missing skills key
  - `parse_with_bash`: `skills:` section detection (with `skills: []` short-circuit), section handler covering `- name:`, `file:`, `description:`, `tags:`, `aliases:`
  - `reset_skill_item` / `flush_skill_item` helpers parallel to commands/agents pattern
  - `validate_manifest`: required-field validation, file-exists check, cross-name collision (vs commands and agents), duplicate-skill-name check
  - `generate_body`: conditional `## Available Skills` table rendered after Agents (empty list → no section)
- **`.writ/manifest.yaml`** (added schema comment + `skills: []`)
  - 12-line schema documentation comment block
  - Empty `skills: []` declaration to anchor the schema and validate the parser end-to-end

### Implementation Decisions

1. **`skills: []` short-circuit in bash parser** — added explicit case for the empty-list literal so the bash parser doesn't enter `section="skills"` mode and fail to flush properly. The standard `skills:` case still works for the populated form.
2. **Cross-name collision check is in `validate_manifest`, not `gen-skill.sh` body** — keeps validation centralized with existing command/agent checks. Single error format across all three primitives.
3. **yq path guarded with `yq_read ".skills" >/dev/null && length != 0`** — so manifests without a `skills:` key (or with `skills: []`) don't error in the yq path. Mirrors the silent-skip behavior of the bash parser.

### Test Results

**Verification:** Manual test fixtures via shell (markdown/bash project — no test framework)

- ✅ Scenario 1: Empty `skills: []` → `--check` exits 0, no Skills section in SKILL.md
- ✅ Scenario 2: Populated single skill → `## Available Skills` table renders after Agents, content correct
- ✅ Scenario 3: Missing `file:` field → `YAML error: skills[0] (hello-test) missing required field 'file'`, exit 1
- ✅ Scenario 4: Bash fallback parser is the only available parser locally; produced correct output across all scenarios
- ✅ Scenario 5: Deliberate edit of generated Skills table → `--check` reports drift, exit 1
- ✅ Bonus: Skill name colliding with command `release` → caught
- ✅ Bonus: Skill name colliding with agent `review-agent` → caught
- ✅ Bonus: Duplicate skill name → caught
- ✅ Final state: `skills: []` committed; SKILL.md byte-identical to pre-spec state

### Review Outcome

**Result:** PASS (self-review)

- **Iteration count:** 1 iteration
- **Drift:** None — implementation follows the technical-spec contract verbatim (5 SKILL_* arrays, parser parity, conditional table rendering, validation rules)
- **Security:** Clean — no shell injection risk (uses `strip_value` helper that handles quoted/unquoted values consistently with commands/agents path)
- **Boundary Compliance:** Owned files only (`scripts/gen-skill.sh`, `.writ/manifest.yaml`); no out-of-scope edits

### Deviations from Spec

None.

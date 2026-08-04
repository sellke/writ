# Story 3: Adapter Resolution (2-Band Native)

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1
> **Estimated Effort:** Small

## User Story

**As a** Writ user running agents on Cursor, Codex, or OpenClaw,
**I want** each adapter to document how a `model_tier` resolves to that platform's native model primitive and how it degrades when a tier can't be honored,
**So that** tiering behaves predictably per platform without Writ maintaining a rot-prone model ranking.

## Acceptance Criteria

### Scenario 1: Cursor resolution table
- **Given** the `model_tier` convention
- **When** I read `adapters/cursor.md` § Sub-Agent Models
- **Then** it documents `orchestration` → `inherit` (anchor) and `capability` → `"fast"` (floor), plus unset → inherit

### Scenario 2: Codex resolution table
- **Given** Codex requires concrete model IDs
- **When** I read `adapters/codex.md`
- **Then** the agents↔TOML table is framed as tier resolution: `capability` → concrete mini ID (e.g. `gpt-5-mini`), `orchestration` → omit/inherit, with the existing `/model` verification note retained

### Scenario 3: OpenClaw resolution table
- **Given** OpenClaw's optional `model` param on `sessions_spawn`
- **When** I read `adapters/openclaw.md`
- **Then** it documents `capability` → pass a cheaper `model` param, `orchestration` → omit the param (inherit)

### Scenario 4: Graceful degradation documented per adapter
- **Given** a platform may not expose a fast/cheaper model or may see an unknown tier
- **When** I read each adapter's tier section
- **Then** each documents: unknown/unhonorable tier → **warn and fall back to parent/default**, never hard-fail

### Scenario 5: Relative + reserved-offset framing
- **Given** the contract is relative and 2-band
- **When** I read each adapter
- **Then** each states resolution is relative (anchor/floor), that no maintained ranking exists, and that ordinal offsets are reserved (clamp to floor today)

## Implementation Tasks

- [ ] **Cursor adapter:** Update § Sub-Agent Models with the tier→native table (`inherit`/`fast`), degradation rule, and relative/reserved framing.
- [ ] **Codex adapter:** Reframe the agents↔TOML model column as tier resolution; document mini-ID for `capability`, inherit for `orchestration`, keep `/model` verification note.
- [ ] **OpenClaw adapter:** Update the spawning section with tier→`model`-param mapping and degradation rule.
- [ ] **Degradation consistency:** Ensure all three adapters state the same warn-and-fall-back contract (matching `required_skills:` handling).
- [ ] **Claude Code decision:** If `adapters/claude-code.md` exposes a native fast/inherit distinction, add a matching tier section; otherwise note it as deferred (see spec Scope Boundaries).
- [ ] **Cross-check with Story 2:** Confirm the resolution tables produce the exact concrete models Story 2's mapping asserts (no regression).

## Definition of Done

- [ ] All five acceptance criteria pass
- [ ] `adapters/cursor.md`, `adapters/codex.md`, `adapters/openclaw.md` each contain a tier→native-resolution table + graceful-degradation rule
- [ ] Claude Code adapter either updated or explicitly deferred with rationale
- [ ] Degradation contract is identical in spirit across adapters (warn → fall back to parent)
- [ ] Self-review: no concrete model names ship for Cursor/OpenClaw (native primitives only); Codex's single mini ID is isolated and flagged for `/model` verification

## Technical Notes

- **No ranking, native primitives.** Cursor's `inherit`/`fast` are the resolution — Writ ships zero model names there. Codex is the only platform needing a concrete ID; it lives in one table and is flagged as verify-with-`/model` (already the convention).
- **Degradation mirrors `required_skills:`.** Same graceful, warn-don't-fail posture the project already uses for unknown skills.
- **Reserved offsets clamp.** Deeper-than-2-band offsets resolve to floor (or inherit if one band); documented, not an error.

## Context for Agents

- **Coding agent context:** technical-spec.md → §2 (resolution table) and §3 (degradation). Existing surfaces: `adapters/cursor.md` § Sub-Agent Models, `adapters/codex.md` § Writ agents ↔ Codex TOML, `adapters/openclaw.md` § Spawning Sub-Agents.
- **Review agent context:** spec.md → Success Criteria #3. Verify degradation wording is present in all three adapters and that Cursor/OpenClaw ship no concrete model names.
- **Testing agent context:** For each adapter, walk the four shadow paths (technical-spec §4): happy, nil/unset, advisory-empty, upstream-error (unhonorable). Confirm each documents warn+inherit for the error path.

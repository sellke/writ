# Story 3: Adapter Resolution (2-Band Native)

> **Status:** Completed ✅ (2026-07-18)
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

### Scenario 6: Claude Code resolution table
- **Given** `adapters/claude-code.md` § Model Selection already runs a concrete `inherit`/`sonnet`/`haiku` mapping (no clean binary fast/inherit primitive)
- **When** I read `adapters/claude-code.md`
- **Then** it documents `capability` → a named cheaper model (e.g. `haiku`), `orchestration` → `inherit`, with the same graceful-degradation rule and a verification flag on the concrete names (mirrors Codex's mini-ID caveat)

## Implementation Tasks

- [x] **Cursor adapter:** Update § Sub-Agent Models with the tier→native table (`inherit`/`fast`), degradation rule, and relative/reserved framing.
- [x] **Codex adapter:** Reframe the agents↔TOML model column as tier resolution; document mini-ID for `capability`, inherit for `orchestration`, keep `/model` verification note.
- [x] **OpenClaw adapter:** Update the spawning section with tier→`model`-param mapping and degradation rule.
- [x] **Degradation consistency:** Ensure all three adapters state the same warn-and-fall-back contract (matching `required_skills:` handling).
- [x] **Claude Code mapping:** `adapters/claude-code.md` § Model Selection already runs a 3-way concrete mapping (`inherit` / `sonnet` / `haiku`), not a clean binary fast/inherit primitive — verified, not deferred. Fold in a tier section mirroring the Codex mini-ID pattern: `capability` → a named cheaper model (`haiku`, or `sonnet` where the agent needs more nuance), `orchestration` → `inherit`. Flag the concrete names for `/model`-style verification, same caveat as Codex's mini ID.
- [x] **Cross-check with Story 2:** Confirm the resolution tables produce the exact concrete models Story 2's mapping asserts (no regression).

## Definition of Done

- [x] All five acceptance criteria pass
- [x] `adapters/cursor.md`, `adapters/codex.md`, `adapters/openclaw.md` each contain a tier→native-resolution table + graceful-degradation rule
- [x] Claude Code adapter updated with a tier section using concrete model names (mirrors Codex's mini-ID pattern; verified no clean binary fast/inherit primitive exists there)
- [x] Degradation contract is identical in spirit across adapters (warn → fall back to parent)
- [x] Self-review: no concrete model names ship for Cursor/OpenClaw (native primitives only); Codex's mini ID and Claude Code's `haiku`/`sonnet` names are each isolated to their own table and flagged for verification

## Technical Notes

- **No ranking, native primitives.** Cursor's `inherit`/`fast` are the resolution — Writ ships zero model names there. Codex and Claude Code both need concrete names (mini ID / `haiku`+`sonnet` respectively); each lives in its own table and is flagged for verification, same as Codex's existing convention.
- **Degradation mirrors `required_skills:`.** Same graceful, warn-don't-fail posture the project already uses for unknown skills.
- **Reserved offsets clamp.** Deeper-than-2-band offsets resolve to floor (or inherit if one band); documented, not an error.

## Context for Agents

- **Coding agent context:** technical-spec.md → §2 (resolution table) and §3 (degradation). Existing surfaces: `adapters/cursor.md` § Sub-Agent Models, `adapters/codex.md` § Writ agents ↔ Codex TOML, `adapters/openclaw.md` § Spawning Sub-Agents.
- **Review agent context:** spec.md → Success Criteria #3. Verify degradation wording is present in all three adapters and that Cursor/OpenClaw ship no concrete model names.
- **Testing agent context:** For each adapter, walk the four shadow paths (technical-spec §4): happy, nil/unset, advisory-empty, upstream-error (unhonorable). Confirm each documents warn+inherit for the error path.

---

## What Was Built

**Implementation Date:** 2026-07-18

### Files Modified

- **`adapters/cursor.md`** — Replaced § Sub-Agent Models prose with a tier→resolution table (`orchestration`→`inherit`, `capability`→`"fast"`, unset→`inherit`, reserved `-N`→clamp); updated the stale `user-story-generator.md` override advice to target `model_tier` (not just `model:`) now that Story 2 landed a `model_tier: capability` there too.
- **`adapters/codex.md`** — Reframed the agents↔TOML table's model column into `model_tier` + "Resolved model" columns; kept the existing `/model` verification note.
- **`adapters/openclaw.md`** — Added a tier table in § 1 Spawning Sub-Agents (`orchestration`→omit `model` param, `capability`→cheaper `model` param); folded the old Gotcha #6 into a cross-reference to the new table.
- **`adapters/claude-code.md`** — Added a `model_tier` column to the existing legacy-agent Model Selection table; documented `writ-documenter`'s `sonnet` as an intentional "capability tier, higher-cost variant" (capability ≠ always-cheapest) without editing the underlying agent file; noted the legacy set is 6-of-7 (no `visual-qa` equivalent).

### Implementation Decisions

1. **Claude Code's `sonnet` classified as `capability`, not a third tier** — per technical-spec §2's explicit allowance ("`haiku`, or `sonnet` where more nuance is needed"), avoiding a false binary that would have mis-labeled `writ-documenter`.
2. **OpenClaw's tier table lives in § 1 (Spawning) rather than a new section** — that's where the existing `model` param mention already lived; avoided fragmenting the model-selection story across two sections.
3. **Cursor's stale override advice updated in the same pass** — since it sits in the exact section this story edits and would read as incomplete the moment Story 2's `model_tier` landed on `user-story-generator.md`.

### Test Results

**Verification:** Manual `rg`/`git diff` walkthrough (markdown-only repo, no test framework).
- ✅ All 4 adapters contain non-zero `orchestration`/`capability` matches
- ✅ Zero concrete model names in `cursor.md`/`openclaw.md`
- ✅ `gpt-5-mini` isolated to `codex.md`; `haiku`/`sonnet` isolated to `claude-code.md`
- ✅ Warn+fall-back degradation language present in all 4
- ✅ Relative/no-ranking/reserved-offset framing present in all 4
- ✅ Cross-checked against Story 2's actual landed mapping — tables agree exactly
- ✅ Zero overlap with parallel Story 2's files (`agents/`, `.writ/manifest.yaml`)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** None (docs only)
- **Boundary Compliance:** 4/4 owned files touched, 0 unowned files touched

### Deviations from Spec

None

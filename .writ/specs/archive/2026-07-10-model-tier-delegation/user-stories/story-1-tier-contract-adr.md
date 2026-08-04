# Story 1: Tier Contract + ADR-016

> **Status:** Completed ✅ (2026-07-18)
> **Priority:** High
> **Dependencies:** None
> **Estimated Effort:** Small

## User Story

**As a** Writ contributor authoring agents, commands, or skills,
**I want** a documented, portable `model_tier` frontmatter convention with a recorded architectural decision behind it,
**So that** I can express model-weight intent once, in one obvious place, and downstream adapters resolve it consistently without me hardcoding platform model names.

## Acceptance Criteria

### Scenario 1: `model_tier` convention documented in `system-instructions.md`
- **Given** ADR-009 defines the verb/noun/tool boundary but says nothing about model tiers
- **When** I read `system-instructions.md`
- **Then** there is a section documenting `model_tier` with: the two named tiers (`orchestration`, `capability`), the enforcement boundary (agents enforced; commands/skills advisory only), the reserved ordinal-offset form, and graceful-degradation semantics

### Scenario 2: Schema is unambiguous
- **Given** the convention is documented
- **When** I read the schema definition
- **Then** it specifies: (a) allowed values `orchestration` / `capability` / reserved negative ordinal, (b) unset = inherit parent/default, (c) explicit `model:` overrides `model_tier:`, (d) unknown/unhonorable tier warns and falls back (never hard-fails), (e) command/skill tier is advisory-only and cannot select a model, (f) the carrier per file type is explicit: skills use real `---` frontmatter, agents use the existing fenced Agent Configuration block (not a new `---` header), and commands — which have no frontmatter mechanism today — carry advisory tier as a prose note

### Scenario 3: `cursor/writ.mdc` parity
- **Given** Phase 4 parity discipline requires the two root behavioral files to agree
- **When** I `diff` the tiering content between `system-instructions.md` and `cursor/writ.mdc`
- **Then** the tiering sections are byte-identical

### Scenario 4: ADR-016 records the decision
- **Given** the design corrects the originating issue's skill-carrier framing
- **When** I read `.writ/decision-records/adr-016-model-tier-delegation.md`
- **Then** it records the decision (agent-as-carrier, relative-not-absolute, staged 2-band-now/N-step-reserved resolver) and lists considered alternatives (skill-carrier, absolute tiers, full maintained ranking) with rejection rationale

### Scenario 5: Reserved ordinal offsets marked reserve-only
- **Given** the ordinal-offset form is documented but not resolved beyond 2 bands
- **When** I read the convention
- **Then** it is explicitly marked reserve-only with a review trigger, and states resolution is 2-band today (deeper steps clamp to floor)

## Implementation Tasks

- [x] **Schema design:** Finalize the `model_tier` grammar (`orchestration` | `capability` | `-N`), precedence vs `model:`, unset behavior, and graceful-degradation contract.
- [x] **Carrier-per-file-type note:** Document explicitly that "frontmatter" is the umbrella term — skills carry real `---` frontmatter, agents carry it in their existing Agent Configuration block, and commands (no frontmatter mechanism, verified 0/31 files) carry advisory tier as a prose note. Prevents Story 2/4 from inventing new file structure.
- [x] **`system-instructions.md` section:** Add a `## Model Tiers` section near the `required_skills:` convention documenting tiers, enforcement boundary, advisory-for-commands/skills, reserved ordinal offsets, and degradation.
- [x] **`cursor/writ.mdc` mirror:** Insert byte-identical tiering content; verify via `diff`.
- [x] **Write ADR-016:** `.writ/decision-records/adr-016-model-tier-delegation.md` with Decision, the three considered alternatives + rejection rationale, and Consequences.
- [x] **Reserve-only note + review trigger:** Document ordinal offsets as reserve-only with a dated review trigger (mirror the `required_skills:` 90-day pattern).
- [x] **Cross-reference ADR-009:** Cite the skills-don't-spawn-agents rule as the grounding for agent-as-carrier.

## Definition of Done

- [x] All five acceptance criteria pass
- [x] `model_tier` convention documented in `system-instructions.md` and `cursor/writ.mdc` (byte-identical tiering content, verified via `diff`)
- [x] ADR-016 exists with decision + alternatives + consequences
- [x] Zero agents/commands/skills modified in this story (contract + docs only; adoption is Story 2)
- [x] Self-review: schema follows existing frontmatter discipline (additive, simple values, graceful degradation) and matches the `required_skills:` reserve-only precedent

## Technical Notes

- **Why agent-as-carrier:** the `model` parameter only exists at the agent spawn boundary (`Task({ model })`, `sessions_spawn`, Codex TOML). A skill is loaded text; a command runs at the user's session model. Enforced tier on either is inert. See spec.md → Technical Decisions.
- **Carrier ≠ literal frontmatter everywhere:** verified against the actual repo — agents (`agents/*.md`) have no `---` YAML block, only a fenced Agent Configuration block; commands (`commands/*.md`) have no config-block mechanism at all (0/31 files). Don't let "frontmatter convention" imply every file type gets a new `---` header.
- **Why reserve the ordinal form now:** the real 4-level orchestration nest (`/implement-phase` → spec-runner → `/implement-story` → agents) may eventually want per-level step-down, but platforms expose ~3 bands so deeper steps clamp. Declaring the vocabulary now (inert until the ranking story) mirrors `required_skills:`.
- **Keep it additive.** No breaking changes; unset `model_tier` = today's behavior.

## Context for Agents

- **Coding agent context:** spec.md → `## Implementation Approach → ### Frontmatter contract`; technical-spec.md → §1 (schema) and §3 (degradation). Model the reserve-only note on `2026-05-03-skills-foundation` Story 5.
- **Review agent context:** spec.md → Business Rules (enforcement boundary; advisory-only). Verify zero agent/command/skill files change in this story's diff. Confirm `diff` parity of the two root files.
- **Testing agent context:** `diff <(sed -n '/## Model Tiers/,/^## /p' system-instructions.md) <(sed -n '/## Model Tiers/,/^## /p' cursor/writ.mdc)` for parity; `rg "model_tier" agents/ commands/ skills/` must return zero this story.

---

## What Was Built

**Implementation Date:** 2026-07-18

### Files Created

1. **`.writ/decision-records/adr-016-model-tier-delegation.md`** (195 lines)
   - Records the agent-as-carrier / relative-not-absolute / staged 2-band-now-N-step-reserved decision, following ADR-014's structure (Decision → Context → Mechanism → Considered Alternatives → Consequences → Reserve-Only Review Trigger → References). Three considered alternatives with rejection rationale: skill-carrier, absolute tiers, full maintained ranking. Cites ADR-009's "skills do not spawn agents" line as grounding.

### Files Modified

- **`system-instructions.md`** (+40 lines) — New `## Model Tiers` section inserted immediately after `### Skill authoring`: two named tiers, enforcement boundary (agents enforced; commands/skills advisory), carrier-per-file-type table (6/7 agents use plain-fence `## Agent Configuration`; `visual-qa-agent.md` uses yaml-fence `## Agent Specification`; commands use a prose note), schema/precedence rules, graceful-degradation table, reserve-only ordinal-offset note with a 2026-10-16 review trigger.
- **`cursor/writ.mdc`** (+40 lines) — Byte-identical mirror of the same section, inserted at the same logical position (before the pre-existing, unrelated `## Self-Dogfooding` section that `system-instructions.md` lacks).

### Implementation Decisions

1. **Insertion point over append-to-EOF** — Both files got the new section immediately after `### Skill authoring` rather than a blind append, because `cursor/writ.mdc` has a pre-existing trailing `## Self-Dogfooding` section that `system-instructions.md` doesn't have; appending to EOF in both would have broken byte-parity of the inserted span.
2. **"6 of 7" agents, not "all 7"** — The carrier-per-file-type note explicitly flags that `visual-qa-agent.md` uses a differently-named/-fenced config block (`## Agent Specification` / yaml fence) so Story 2 doesn't assume header uniformity.
3. **Reserve-only review trigger dated 2026-10-16** — Mirrors the existing `required_skills:` 90-day-post-ship pattern.

### Test Results

**Verification:** Manual `rg`/`diff` walkthrough (markdown-only repo, no test framework).
- ✅ `rg "model_tier" agents/ commands/ skills/` → 0 matches
- ✅ `## Model Tiers` section diffed byte-identical between `system-instructions.md` and `cursor/writ.mdc`
- ✅ ADR-016 confirmed substantive (195 lines) with Decision, 3 lettered alternatives, Consequences
- ✅ Reserve-only + dated review trigger confirmed present in both root files and the ADR
- ✅ All 3 shadow-path semantics (nil/unset, unknown-tier warn+fallback, `model:` precedence) confirmed explicitly stated in doc text

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Zero out-of-scope files touched; only the 3 owned files changed

### Deviations from Spec

None

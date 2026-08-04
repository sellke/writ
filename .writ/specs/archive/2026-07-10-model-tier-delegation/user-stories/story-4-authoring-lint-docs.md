# Story 4: Authoring & Lint Integration + Docs

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Stories 1, 2, 3
> **Estimated Effort:** Small

## User Story

**As a** Writ contributor scaffolding a new command, agent, or skill,
**I want** the authoring commands to scaffold an (appropriately advisory) `model_tier` field and the lint to validate tier values,
**So that** the convention is discoverable at authoring time and malformed tiers are caught before they ship — with a canonical explainer to point to.

## Acceptance Criteria

### Scenario 1: `/new-skill` scaffolds frontmatter; `/new-command` scaffolds a prose note
- **Given** the `model_tier` convention exists, and commands have no frontmatter mechanism today (verified: 0/31 command files carry a `---` block)
- **When** I scaffold a new skill
- **Then** the generated frontmatter includes a `model_tier:` field with an inline `# advisory only` comment
- **When** I scaffold a new command
- **Then** the generated file includes a prose note (e.g. near Overview/Invocation) documenting an advisory `model_tier:` with an adjacent "advisory only" label — no new `---` frontmatter is introduced for commands

### Scenario 2: Lint validates tier values
- **Given** `scripts/lint-skill.sh` (and the shared frontmatter validation)
- **When** a file declares `model_tier: banana`
- **Then** lint rejects it with: "model_tier 'banana' is invalid. Use 'orchestration', 'capability', or a reserved negative offset (e.g. -1)." — and accepts `orchestration`, `capability`, and `-1`

### Scenario 3: Canonical explainer exists
- **Given** the convention needs a user-facing home
- **When** I read `.writ/docs/model-tiers.md`
- **Then** it explains the two tiers, the agent-enforced / command-skill-advisory boundary, native relative resolution, graceful degradation, and reserved ordinal offsets — using the verb/noun/tool framing

### Scenario 4: Root docs reference the convention
- **Given** `README.md` and `AGENTS.md` describe agents and model behavior
- **When** I read them
- **Then** each references the `model_tier` convention / `.writ/docs/model-tiers.md` where model or agent behavior is discussed

### Scenario 5: Advisory framing is unmistakable
- **Given** command/skill tier is advisory
- **When** I read any scaffold output, the explainer, and the lint help
- **Then** "advisory only (commands/skills run at the session/caller model)" appears wherever command/skill tier is mentioned

## Implementation Tasks

- [x] **`/new-skill` scaffold:** Add `model_tier:` (advisory) with inline comment to the generated skill frontmatter.
- [x] **`/new-command` scaffold:** Add an advisory `model_tier` **prose note** (not YAML frontmatter — none exists for commands, verified 0/31 files) near the generated command's Overview/Invocation section, with an adjacent "advisory only" label.
- [x] **Lint value check:** Extend `scripts/lint-skill.sh` (and shared frontmatter validation used by `/new-skill` / `/refresh-command` / `/new-command`) to validate `model_tier` against `^(orchestration|capability|-[0-9]+)$` with a clear remediation message, wherever it's declared (skill frontmatter, agent config block, or command prose note).
- [x] **Write `.writ/docs/model-tiers.md`:** Canonical explainer with verb/noun/tool framing, resolution/degradation summary, and reserved-offset note.
- [x] **Root doc references:** Link the convention from `README.md` and `AGENTS.md` where agent/model behavior is described.
- [x] **Advisory wording sweep:** Ensure the advisory framing is consistent across scaffolds, docs, and lint output.

## Definition of Done

- [x] All five acceptance criteria pass
- [x] `/new-skill` scaffolds an advisory `model_tier:` frontmatter field; `/new-command` scaffolds an advisory `model_tier` prose note (no frontmatter introduced for commands)
- [x] Lint rejects invalid `model_tier` values and accepts valid ones (verified with a bad + good input)
- [x] `.writ/docs/model-tiers.md` exists; `README.md` and `AGENTS.md` reference it
- [x] Advisory framing consistent everywhere command/skill tier appears
- [x] Self-review: lint change is minimal bash, no new dependency; explainer opens with the same verb/noun/tool words ADR-009 uses

## Technical Notes

- **Reuse, don't fork, the lint.** Add tier validation to the existing shared lint path so `/new-skill`, `/new-command`, and `/refresh-command` all get it. Mirror the skills-foundation approach (`scripts/lint-skill.sh` shared by `/new-skill` and `/refresh-command`).
- **Advisory comment/label is written, not lint-enforced.** `/new-skill` always emits the `# advisory only` comment; `/new-command` always emits the prose-note label. Lint doesn't fail if a hand-authored file omits either (it's documentation, not a hard rule).
- **Commands get prose, not frontmatter.** Verified against the repo: 0/31 command files carry a `---` block today. Introducing real command frontmatter is out of scope for this spec (see spec.md Scope Boundaries) — the advisory tier is a documented convention note, not a parseable field.
- **Explainer mirrors `.writ/docs/skills.md`.** Same shape and tone as the skills explainer for consistency.

## Context for Agents

- **Coding agent context:** technical-spec.md → §5 (lint) and §6 (documentation surfaces). Existing patterns: `scripts/lint-skill.sh`, `commands/new-skill.md`, `commands/new-command.md`, `.writ/docs/skills.md`.
- **Review agent context:** spec.md → Success Criteria #5, #7. Verify advisory framing is unmistakable and lint covers the invalid-value path.
- **Testing agent context:** feed lint `model_tier: banana` (reject) and `model_tier: capability` / `-1` (accept); confirm `.writ/docs/model-tiers.md` exists and root docs link it (`rg "model-tiers" README.md AGENTS.md`).

## What Was Built

### Files Created
- **`.writ/docs/model-tiers.md`** — Canonical user-facing explainer for `model_tier`. Opens with the verb/noun/tool framing shared with `.writ/docs/skills.md` and ADR-009, then covers: the agent-enforced vs. command/skill-advisory boundary, the two named tiers (`orchestration`/`capability`) and their relative (not absolute) semantics, per-platform resolution pointers into the four adapters, a graceful-degradation table, the reserved negative-ordinal offset convention (with a 2026-10-16 review trigger), authoring integration, and a references section back to ADR-016, ADR-009, and `system-instructions.md`.

### Files Modified
- **`commands/new-skill.md`** — Added `model_tier: orchestration   # advisory only — skills run in the caller's context, not selectable` to both the Phase 2 lint-candidate template and the Phase 3 generated `SKILL.md` template; updated the Completion Checklist to mention the field.
- **`commands/new-command.md`** — Added a "Model tier note" process instruction requiring every generated command to carry the locked prose note `> **Model tier (advisory only):** <tier> — commands run at the user's session model, not Writ-selectable.` near Overview/Invocation, with contextual `<tier>` guidance (default `orchestration`); added a matching "Quality bars" bullet.
- **`scripts/lint-skill.sh`** — Added a new, standalone `lint_model_tier()` function (does not modify `extract_frontmatter()`/`lint_lifecycle()`) that scans the full raw file for both the key-value shape (`model_tier: <value>`, used by skill frontmatter and agent Agent Configuration blocks) and the locked prose shape (`Model tier (advisory only): <value>`, used by commands), validates against `^(orchestration|capability|-[0-9]+)$`, and emits the exact required remediation message on violation. Wired into `lint_file`'s existing flow (2 lines). Updated `usage()` help text, including (after review) an explicit advisory-only/session-model clause so all three AC5 locations (scaffold, explainer, lint help) carry the framing.
- **`README.md`** — Added one sentence to the `## Agents` section noting `model_tier` and linking `.writ/docs/model-tiers.md`.
- **`AGENTS.md`** — Added one sentence to `### Agents (agents/)` noting `model_tier` and linking `.writ/docs/model-tiers.md`.
- **`.writ/manifest.yaml`** — Added one optional line to the `skills:` schema comment block noting `model_tier:` is available as an advisory field (no agent entries touched — those were Story 2's scope and remain locked).

### Implementation Decisions
- **Dual-shape lint, one function.** Rather than forcing the already-committed (Story 1) command prose format to contain a literal `model_tier:` substring, the lint recognizes both the key-value shape and the locked prose shape in a single new function — avoiding any edit to `system-instructions.md`/`cursor/writ.mdc` while still satisfying AC2's illustrative `model_tier: banana` example.
- **Advisory-only framing added to lint help after review.** The first review pass correctly flagged that AC5 requires the advisory framing in three places (scaffold output, explainer, lint help) — the lint help was initially missing it. Fixed with a 2-line, additive `usage()` insertion; re-verified with fresh fixtures and a full regression sweep of all real `skills/*/SKILL.md` files.

### Test Results
No test framework (markdown-only repo). Verification performed via direct execution of `scripts/lint-skill.sh` against independently authored fixtures (not the coding agent's own): `model_tier: banana` (skill-shape) → rejected with exact message; `model_tier: capability` and `model_tier: -1` → accepted; locked prose shape with `orchestration` → accepted; locked prose shape with `banana` → rejected with the same exact message. Regression-swept all 6 real `skills/*/SKILL.md` files — all clean, no false positives. Confirmed via `git diff --stat` that `system-instructions.md`, `cursor/writ.mdc`, `adr-016-model-tier-delegation.md`, `agents/*.md`, and `adapters/*.md` were untouched, and that `extract_frontmatter()`/`lint_lifecycle()` in `lint-skill.sh` remain byte-identical to `HEAD`.

### Review Outcome
Two review rounds. Round 1: FAIL on AC5 only (lint help text missing the advisory-only/session-model phrase) — all other AC and boundary checks passed cleanly. Fix applied directly (2-line additive `usage()` change). Round 2: **PASS** — all 5 acceptance criteria verified independently, zero regressions, zero boundary violations, zero drift.

### Boundary Compliance
Fully compliant across both review rounds. All edits stayed within Story 4's owned files (`commands/new-skill.md`, `commands/new-command.md`, `scripts/lint-skill.sh`, `.writ/docs/model-tiers.md`, `README.md`, `AGENTS.md`) plus one optional comment-only line in `.writ/manifest.yaml`. No overlap with Stories 1–3's locked artifacts.

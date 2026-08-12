# Story 3: Extract the User Challenge Presentation Format to a Skill

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** maintainer running a phase where no lane ever returns `challenge_required`
**I want to** stop loading the 1,267-byte challenge presentation procedure on every invocation
**So that** the rendering format lives in a capability file, while the two facts that make the escalation safe — `/implement-phase` is the sole presenter, and a malformed challenge is a contract error rather than a rendered prompt — stay in the command

## Acceptance Criteria

- [ ] Given `skills/` is a shared namespace, when this story starts, then the name is reconciled against `2026-08-12-disclosure-implement-story`, the six incumbents, and every `name:` in `.writ/manifest.yaml` (Business Rule 10), with the convention followed recorded in the notes
- [ ] Given Business Rule 9, when the skill is created, then it is authored via `/new-skill`, lint passes on the description before any file is written, and the file carries `disable-model-invocation: true` and `status: candidate`
- [ ] Given the source prose references `scripts/phase-state.py validate-challenge` / `record-challenge` / `resolve-challenge` and `commands/_preamble.md` by path, when the skill is written, then it reads as a portable capability — *how to present a four-part challenge and persist its resolution* — with no command, slash-command, skill, or subagent invocation, and `bash scripts/lint-skill.sh skills/<name>/SKILL.md` exits 0
- [ ] Given Business Rule 3 forbids redesign, when the skill is written, then it carries all four required parts by name (*What the roadmap/spec said*, *What Writ recommends*, *What context may be missing*, *Cost if the recommendation is wrong*), the validate → present → persist sequence, the pause-before-any-scope-changing-action rule, the audited-low-risk-reversible auto-proceed exception, and the resume guarantee that a decided question is never re-asked
- [ ] Given `check_phase_challenges` requires the literals `User Challenge` and `ordinary failures use their normal` in `commands/implement-phase.md`, when this story lands, then `git diff --name-only` shows **zero** changes to that file and both literals remain present — Story 4 owns re-stating them in the thin contract
- [ ] Given `commands/_preamble.md` carries the User Challenge contract itself (`## User Challenge`, `scope_degradation`, `select-or-pause`, `four required parts`) and is at 93 of 95 lines, when this story lands, then `git diff --name-only` shows **zero** changes to `commands/_preamble.md` (Business Rule 7) and the skill does not duplicate the preamble's normative definition — it describes presentation, and cites the contract as its consumer's
- [ ] Given Business Rule 4 requires reachability, when this story lands, then the skill is registered in `.writ/manifest.yaml` and `bash scripts/gen-skill.sh --check` reports no delta
- [ ] Given Business Rule 1's hard three-skill cap was **retired** by the 2026-08-12 ruling, when this story lands, then the three-skill total is measured and recorded (≈9,500 B projected) as the input to Story 5's path table — and the projected worst path (floor + all three) is stated, so Story 4 authors the thin contract knowing which paths sit above 54,096 and which below
- [ ] Given Business Rule 8, when this story lands, then `git diff --name-only` lists only `skills/<name>/SKILL.md`, `.writ/manifest.yaml`, and `SKILL.md`

## Implementation Tasks

- [ ] 3.1 Read `commands/implement-phase.md` lines 206–215, plus `commands/_preamble.md`'s `## User Challenge` section and `scripts/phase-state.py`'s `validate_challenge` / `CHALLENGE_TRIGGERS`, so the skill describes the four-part contract as it actually is rather than as the command's summary of it
- [ ] 3.2 Reconcile the skill name (Business Rule 10)
- [ ] 3.3 Run `/new-skill <name>` — description, pre-write lint, file, manifest entry, `gen-skill.sh --check`
- [ ] 3.4 Author the body: the four parts, the validate → present → persist sequence, the auto-proceed exception for audited low-risk reversible selections, and the resume guarantee. Rewrite reducer subcommands as described operations, not invocations
- [ ] 3.5 Explicitly **do not** carry into the skill: "`/implement-phase` is the sole presenter of User Challenges" and "a malformed challenge is a contract error routed to normal failure handling — never rendered as a User Challenge". Both are retained in the command by Story 4 and both are normative
- [ ] 3.6 Verify: lint exits 0; three-skill byte total measured against the budget; `gen-skill.sh --check` no delta; `grep -Fc 'User Challenge' commands/implement-phase.md` and `grep -Fc 'ordinary failures use their normal' commands/implement-phase.md` both still non-zero
- [ ] 3.7 Confirm ownership: `git diff --name-only` shows no `scripts/`, no `commands/` path

## Notes

**Technical considerations:**

- This is the smallest extraction and the last of the three. It no longer "absorbs whatever budget Stories 1 and 2 leave" — the 2026-08-12 ruling retired the shared cap — but sequencing it last still makes Task 3.6's cumulative measurement the one place the full path table can be computed before Story 4 writes the command.
- **This skill and `phase-decomposition` are the two genuinely rare loads**, and they are the reason the mechanism ruling was worth taking. Most phases raise no `User Challenge` at all, so on the common path these bytes are never paid — not amortised, not reduced, never. Under `required_skills:` every invocation paid them.
- The sole-presenter rule is a genuine safety property, not a stylistic one: if a nested subagent could render a User Challenge, the escalation would fire inside a lane with no persistence and no resume record. It stays in the command with the other invariants.
- `commands/_preamble.md` already defines the four-part contract and is eval-pinned on `four required parts`, `select-or-pause`, and `scope_degradation`. The skill must not become a second, drifting copy of that definition — ADR-021 §4's no-copying rule applies to the preamble as much as to commands.

**Risks / challenges:**

- **Three-way duplication.** The contract is in `_preamble.md`, the presentation is moving to a skill, and the sole-presenter rule stays in the command. Each of the three must say a different thing. The failure mode is a skill that restates the preamble, which adds bytes to the ceiling while removing none from the floor.
- **Trimming the four parts to fit.** They are the contract. If the budget bites, compress the surrounding prose or escalate under Business Rule 1 — the four part names are not negotiable.
- **Silently absorbing an overrun from Stories 1–2.** Task 3.6 measures the total; the acceptance criterion requires escalation, not accommodation.

**Integration points:**

- Story 4 loads this skill with one inline `Read skills/<name>/SKILL.md` placed **inside** the `challenge_required` branch, after validation — never at the top of failure handling, which runs on every failure — and authors the retained two-to-three line sole-presenter statement carrying both `check_phase_challenges` anchors.
- Story 5 measures the final `conditional_bytes` and the ceiling.
- `commands/_preamble.md` is read, never written (Business Rule 7 — owned by `2026-08-11-autonomy-gate-classes`).

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/<name>/SKILL.md` exits 0
- [ ] `bash scripts/gen-skill.sh --check` reports no delta
- [ ] Three-skill byte total recorded against the ≈7,841-byte budget; any overrun escalated before Story 4 starts
- [ ] `git diff --name-only` shows zero changes to `commands/implement-phase.md`, `commands/_preamble.md`, and any path under `scripts/`

## Context for Agents

- **Business rules:** [BR1 path-dependent ceiling (hard cap retired), BR3 relocate-not-redesign, BR4 precise placement, BR7 `_preamble.md` untouched, BR8 ownership, BR9 lint, BR10 name reconciliation] — from spec.md → 📋 Business Rules
- **Mechanism ruling:** [inline `Read` replaces `required_skills:`; this is one of the two genuinely rare loads] — from spec.md → ## Approved Scope Changes
- **Detailed requirements:** [What extracts, and where → `skills/user-challenge-presentation/SKILL.md`] — from spec.md → ## Detailed Requirements
- **Technical spec:** [Section Byte Ledger (lines 206–215); The 20 Blocking Anchors — `User Challenge`, `ordinary failures use their normal`] — from sub-specs/technical-spec.md

# Story 2: Extract `tdd-cycle` from `/implement-story`

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer shrinking the heaviest command
**I want to** lift the red → green → refactor discipline out of `/implement-story`'s Gate 1 into `skills/tdd-cycle/SKILL.md` and wire the coding and testing agents to load it
**So that** the TDD capability is authored once and reused by three live consumers while `commands/implement-story.md` shrinks toward orchestration

## Acceptance Criteria

- [ ] Given the extraction is complete, when I inspect `skills/tdd-cycle/SKILL.md`, then it exists with `status: candidate` and an evidence note, carries the red → green → refactor discipline as capability prose, and `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md` exits clean.
- [ ] Given the three consumers, when I inspect them, then `commands/implement-story.md` (Gate 1), `agents/coding-agent.md`, and `agents/testing-agent.md` each contain a literal `Read skills/tdd-cycle/SKILL.md` directive at the point where TDD discipline applies.
- [ ] Given the command shrink, when I compare `commands/implement-story.md` against its pre-extraction line count, then the Gate 1 TDD guidance is reduced to a D5-shaped orchestration note and the command is measurably shorter.
- [ ] Given the skill body, when the boundary lint runs, then it contains no gate names, agent orchestration, `Read commands/`, `Read skills/`, `Task(`, or line-leading slash commands — the *how* of TDD only, not *when* the pipeline invokes it.
- [ ] Given `tdd-cycle` is registered, when `bash scripts/gen-skill.sh` regenerates the catalog, then the root `SKILL.md` lists `tdd-cycle`.

## Implementation Tasks

- [ ] 2.1 Record the pre-extraction line count of `commands/implement-story.md` and identify the exact Gate 1 prose that is durable TDD capability (the *how*) versus pipeline orchestration (the *when/with-what-context* that stays).
- [ ] 2.2 Author `skills/tdd-cycle/SKILL.md` — red → green → refactor discipline as capability prose, `status: candidate` frontmatter with evidence note; run `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md` and rewrite any orchestration references (e.g. "send back to the coding agent") into capability prose until clean.
- [ ] 2.3 Wire `agents/coding-agent.md` to `Read skills/tdd-cycle/SKILL.md` at its TDD step (alongside its existing `conventional-commits` load), and wire `agents/testing-agent.md` to load it where it verifies test-first discipline.
- [ ] 2.4 Wire `commands/implement-story.md` Gate 1 to `Read skills/tdd-cycle/SKILL.md` and shrink the Gate 1 TDD guidance to a D5-shaped orchestration note (skill owns the cycle; the command owns context routing, BLOCKED handling, and gate flow).
- [ ] 2.5 Register `tdd-cycle` alphabetically under `skills:` in `.writ/manifest.yaml` and regenerate the root catalog with `bash scripts/gen-skill.sh`.
- [ ] 2.6 Confirm the command shrink preserved every behavior `/implement-story` still owns (context routing, `STATUS: BLOCKED` gate, degraded-story handling) — none of that moved into the skill.
- [ ] 2.7 Verify the story: `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md`, greps confirming all three consumers reference the skill path, and the recorded line-count drop for `commands/implement-story.md`.

## Notes

- `tdd-cycle` is the strongest extraction: ADR-009 explicitly names it as a skill used by `coding-agent` and `/prototype`, and this story gives it three live consumers, satisfying "in real use" by wiring.
- `agents/coding-agent.md` already `Read`s `conventional-commits` (line ~111) — the `tdd-cycle` load is an additive directive next to it, matching the established pattern.
- The skill must not mention Gate 0.5 boundary maps, `change_surface`, or BLOCKED escalation — those are pipeline orchestration owned by `commands/implement-story.md`.
- Keep the skill focused on the discipline: write the failing test first, implement to green, refactor under green, repeat per unit.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `skills/tdd-cycle/SKILL.md` lints clean
- [ ] Three consumers reference the skill by path
- [ ] `commands/implement-story.md` measurably shorter; root `SKILL.md` regenerated

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Author skill body`, `technical-spec.md` → `## Error & Rescue Map` → `Shrink command`, `technical-spec.md` → `## Error & Rescue Map` → `Wire consumer`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Extraction transform`, `technical-spec.md` → `## Shadow Paths` → `Catalog sync`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 3 (capability prose only), `spec.md` → `### Business Rules` → Rule 5 (in real use = wired consumers), `spec.md` → `### Business Rules` → Rule 7 (shrink preserves owned behavior)]
- **Experience:** [`spec.md` → `## Detailed Requirements` → R4 (extract tdd-cycle), `technical-spec.md` → `### D1 — The Extraction Set Is Committed at Four`, `technical-spec.md` → `### D5 — Command Shrink Note Shape`]

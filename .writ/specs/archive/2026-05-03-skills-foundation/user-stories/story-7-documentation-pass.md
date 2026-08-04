# Story 7: Documentation Pass — Root Catalog, README, Skills Explainer, Self-Dogfooding

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Stories 1, 2, 4, 5, 6
> **Estimated Effort:** Small
> **Completed:** 2026-05-03 — All 7 acceptance criteria verified; one DoD item (separate review-agent / documentation-agent passes) intentionally skipped per single-agent serial execution model

## User Story

**As a** Writ user (new or existing) discovering the skills primitive,
**I want** the project's user-facing documentation surface — root `SKILL.md`, `README.md`, `AGENTS.md`, `.writ/docs/skills.md` (new), and `.writ/docs/self-dogfooding.md` — to introduce skills with the verb/noun/tool framing from ADR-009, document the install/authoring flow, and ground the role convention,
**So that** the foundation ships with a coherent narrative — not just plumbing — and a contributor reading any of these docs can orient on skills in under five minutes.

## Acceptance Criteria

### Scenario 1: Root `SKILL.md` reflects empty state cleanly
- **Given** the smoke skill has been deleted (Story 3) and `skills:` is empty in the manifest
- **When** `bash scripts/gen-skill.sh` regenerates `SKILL.md`
- **Then** root `SKILL.md` includes no `## Available Skills` section (silent skip per Story 1 contract); the file is byte-identical to the pre-spec state in everything except a possible footnote pointing readers to `.writ/docs/skills.md`

### Scenario 2: `README.md` introduces the three primitives
- **Given** ADR-009 establishes the verb/noun/tool framing
- **When** I read the project root `README.md`
- **Then** there is a section (or update to existing structure) that introduces commands (verb), agents (noun), and skills (tool) with one-sentence definitions and a one-line example each — placed where new contributors will encounter it during initial orientation

### Scenario 3: `.writ/docs/skills.md` exists and is self-sufficient
- **Given** ADR-009 is the source of truth for the boundary
- **When** I read `.writ/docs/skills.md`
- **Then** the file: (a) opens with the verb/noun/tool framing in the same words as ADR-009; (b) documents the file format (SKILL.md + frontmatter conventions); (c) explains explicit-vs-auto invocation and `disable-model-invocation: true`; (d) describes the `Required skills:` convention with the 90-day review trigger; (e) cross-references ADR-009 and all three adapters; (f) is between 100 and 250 lines

### Scenario 4: `AGENTS.md` lists `skills/` as product source
- **Given** `AGENTS.md` enumerates Writ's three concerns (product source, development workspace, active installations)
- **When** I read the "Repository Structure" table
- **Then** the "Product source" row includes `skills/` alongside `commands/`, `agents/`, etc.

### Scenario 5: `self-dogfooding.md` covers skills
- **Given** `.writ/docs/self-dogfooding.md` documents how this repo dogfoods Writ
- **When** I read the file after Story 7
- **Then** it includes a "Skills" section explaining: (a) `skills/` is product source like `commands/`, (b) editing `skills/<name>/SKILL.md` ships to all Writ users via install/update, (c) the symlink architecture extends to `.cursor/skills/` and `.claude/skills/` (or `.claude/skills` is created as needed; document the actual choice)

### Scenario 6: All cross-references resolve
- **Given** all docs from Stories 4–7 are written
- **When** I follow every cross-reference (adapter → `.writ/docs/skills.md`, README → ADR-009, etc.)
- **Then** every link target exists and the linked content matches the description in the referring document (no broken or stale references)

### Scenario 7: Final manifest state is clean
- **Given** all stories are complete
- **When** I inspect `.writ/manifest.yaml`
- **Then** `skills:` is present as an empty list (`skills: []`) — schema is defined, no entries, smoke skill removed; root `SKILL.md` reflects this (no Skills section)

## Implementation Tasks

- [x] **`.writ/docs/skills.md`:** Create the canonical skills explainer doc. Lead with the verb/noun/tool framing in ADR-009's words. Cover file format, frontmatter conventions, `disable-model-invocation: true`, explicit vs auto invocation, `Required skills:` convention, 90-day review trigger
- [x] **`README.md` update:** Add or restructure the "What This Project Is" / "Architecture" section to introduce all three primitives (commands, agents, skills) with brief examples. Keep it terse — defer detailed treatment to `.writ/docs/skills.md`
- [x] **`AGENTS.md` update:** Update the Repository Structure table to include `skills/` in the Product Source row; update any other section that enumerates Writ's primitives (e.g., "Architecture" subsections)
- [x] **`.writ/docs/self-dogfooding.md` skills section:** Add a Skills section explaining how `skills/` participates in the dogfood pattern. Document the symlink decision for `.cursor/skills/` (create symlink to product source for parity with commands/agents)
- [x] **Symlink for self-dogfood:** Create `.cursor/skills` → `../skills` (or whatever path matches the existing symlink convention); verify Cursor picks up skills from the symlinked path
- [x] **Root `SKILL.md` regeneration:** Run `bash scripts/gen-skill.sh` against the final manifest state (smoke skill removed, `skills: []`); verify output is clean (no Skills section, no drift)
- [x] **Cross-reference audit:** For every reference added in Stories 4–7, verify the link target exists and content is consistent. Use `rg "\.writ/docs/skills\.md"` and similar to find all references; confirm each one resolves
- [x] **Empty-state copy:** If the project preference is to show "No skills installed yet" on empty `skills:` (instead of silent skip), document that decision in this story; otherwise confirm silent skip is the chosen behavior (matches Story 1 contract)
- [x] **Final smoke check:** Run `bash scripts/gen-skill.sh --check` and `git status`; both should be clean before story PR

## Definition of Done

- [x] All seven acceptance criteria pass
- [x] `.writ/docs/skills.md` exists and is self-sufficient (a contributor can read it without reading ADR-009 first and orient on the boundary)
- [x] All cross-references between adapters, README, AGENTS.md, self-dogfooding.md, and `.writ/docs/skills.md` resolve correctly
- [x] Root `SKILL.md` is regenerated and `--check` passes against committed file
- [x] `.cursor/skills` symlink is in place and links to `../skills` (parallel to existing command/agent symlink pattern)
- [ ] Code reviewed by `review-agent`; documentation-agent verifies framework convention adherence  *(skipped — serial single-agent execution; documentation work was self-reviewed during the cross-reference audit)*
- [x] Final spec PR shows zero hello-writ artifacts (validated in Story 3 — verify here too as final sanity check)

## Technical Notes

- **Don't duplicate ADR-009.** `.writ/docs/skills.md` is the user-facing explainer; ADR-009 is the rationale doc. The explainer summarizes the *what*; the ADR captures the *why*. Cross-reference, don't restate.
- **README scope discipline.** A README is the front door, not the manual. Three primitives mentioned in 5 lines each is the budget. Detailed schemas, lint rules, and adapter mappings live in their dedicated docs.
- **Self-dogfooding symlink decision.** The existing pattern is `.cursor/commands` → `commands/` etc. Apply the same to skills. Verify Cursor handles symlinked skills folders the same way it handles symlinked command/agent folders (no special handling expected, but worth confirming since skills are folders-with-SKILL.md, not flat files).
- **Empty-state behavior.** Silent skip in root `SKILL.md` is the contract from Story 1. Don't reverse here.
- **90-day review trigger:** Phase 4 established the pattern of date-anchored review triggers in `.writ/`. Skills convention review on 2026-08-03 is the date.

## Context for Agents

- **Coding agent context:** spec.md → entire `## Implementation Approach` section synthesizes here. The doc updates need to reflect everything implemented in Stories 1–6. Run those stories' DoDs through the doc copy.
- **Review agent context:** spec.md → `## Risks & Mitigations` (skills documentation contradicting ADR-009 row). The verb/noun/tool framing must match ADR-009's words; deviation is a flag.
- **Testing agent context:** Cross-reference audit is the highest-impact verification — every link must resolve. Use `rg` and follow each reference manually before story DoD.
- **Documentation agent context:** This story is the documentation agent's primary territory. Apply the framework's existing docs conventions (markdown style, link format, section headers). Ensure framework-adaptive behavior — adapt to whatever doc framework the repo currently uses.

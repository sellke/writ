# Story 2: research.md Refinement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** refine research.md to A-grade quality
**So that** every line teaches something non-obvious, sets a quality bar, or prevents a specific mistake — with the 4-phase structure and Exa-specific tips preserved as the crown jewels

## Acceptance Criteria

1. **Given** the refined research.md, **when** an AI agent executes the command, **then** the 4-phase structure (define scope → initial discovery → deep dive → synthesis) remains fully intact with per-phase Exa vs non-Exa search strategies preserved.

2. **Given** the refined file, **when** applying the litmus test to every line, **then** each line either teaches something non-obvious, sets a quality bar, or prevents a specific mistake — with no filler.

3. **Given** the refined file, **when** counting lines, **then** the total is within ~160 ±10% (144–176 lines), down from 343.

4. **Given** the refined file, **when** checking for removed sections, **then** the following are cut entirely: Research Document Template (lines 163–248, ~86 lines), Output Structure (lines 140–157), Todo progression examples (lines 280–313), Common Pitfalls to Avoid (lines 272–278), Best Practices: Critical Thinking (lines 258–264), Best Practices: Documentation (lines 266–270).

5. **Given** the refined file, **when** an AI agent reads Exa guidance, **then** it retains: `/answer` for orientation, `highlights` for scanning vs `text` with `max_characters` for reading, categories (`github`, `paper`, `news`, etc.) for targeting, and output path convention (`.writ/research/[DATE]-[topic-name]-research.md`) with date determination via `npx @devobsessed/writ date`.

## Implementation Tasks

1. **Read the current file** — Open `commands/research.md` and verify line numbers for sections to cut/compress. Confirm the 4-phase structure, Exa vs non-Exa per-phase strategies, and date determination process.

2. **Cut the Research Document Template** — Remove the 86-line template (lines 163–248). Replace with principles: what sections matter (research questions, key findings, options analysis, recommendations, sources) and quality bar for each (evidence-backed claims, pros/cons with rationale, cited sources). Preserve output path convention and date determination.

3. **Cut Output Structure and Todo progression examples** — Remove Output Structure (lines 140–157) — it duplicates the template. Remove Todo examples (lines 280–313) — the AI knows how to update todos; Phase 1 todo structure (lines 54–60) is sufficient.

4. **Cut generic advice sections** — Remove Common Pitfalls to Avoid (lines 272–278), Best Practices: Critical Thinking (lines 258–264), and Best Practices: Documentation (lines 266–270). These are generic; the litmus test excludes them.

5. **Compress Best Practices: Search Strategy** — Keep Exa-specific tips (lines 254–256): `type: "auto"`, highlights vs text, `max_characters`, parallel searches by category, `/answer` vs `/search`, `startPublishedDate` + `category: "news"`. Cut generic search advice (lines 251–253).

6. **Tighten phase action lists and When to Use** — Compress each phase's action list where wordy; preserve the Exa/Without Exa sub-bullets (they are non-obvious). Compress "When to Use" from 5 bullets to 2–3.

7. **Verification** — Confirm line count within target (~160 ±10%), run a mental execution to ensure no functional capability lost. Verify Exa tips are intact and 4-phase structure is clear.

## Notes

**Technical considerations:**
- Exa-specific tips are the crown jewel — `/answer` for orientation, highlights for scanning, text with max_characters for reading, categories for targeting. These encode API usage the AI might not infer from the skill alone.
- The per-phase Exa vs non-Exa distinction (what to do with vs without Exa in each phase) is genuinely non-obvious and must remain explicit.
- Output path and date determination are the only output contract — preserve them.

**Risks:**
- Over-compression of phase action lists could lose the Exa/Without Exa sub-bullets. Each phase has distinct Exa strategies (e.g., Phase 2: `/answer` first, highlights for scanning; Phase 3: categories, includeDomains, `/contents`).
- Replacing the template with principles may leave the AI unsure of structure — ensure principles enumerate required sections and quality bar clearly.

**Watch for:**
- Exa skill reference ("read it first") must remain — it's the entry point.
- `includeDomains` and `excludeDomains` examples (e.g., arxiv.org, docs.python.org) are concrete and helpful — preserve or compress to one line.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Line count within target range (~160 ±10%)
- [ ] No functional capability lost
- [ ] 4-phase structure and Exa-specific tips preserved

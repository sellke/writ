# Story 3: Extract `error-rescue-mapping` from `/create-spec`

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ maintainer consolidating a shared analysis technique
**I want to** lift the Error & Rescue Map, Shadow Paths, Interaction Edge Cases, and `[UNPLANNED]` marker technique out of `/create-spec`'s Step 2.8 into `skills/error-rescue-mapping/SKILL.md`
**So that** the same failure-mapping capability is authored once, consumed by `/create-spec` now and `/review` later, instead of duplicated across both

## Acceptance Criteria

- [x] Given the extraction is complete, when I inspect `skills/error-rescue-mapping/SKILL.md`, then it exists with `status: candidate` and an evidence note, carries the Error & Rescue / Shadow Path / Interaction Edge Case table technique plus the `[UNPLANNED]` marker discipline as capability prose, and `bash scripts/lint-skill.sh skills/error-rescue-mapping/SKILL.md` exits clean.
- [x] Given the consumer, when I inspect `commands/create-spec.md` Step 2.8, then it contains a literal `Read skills/error-rescue-mapping/SKILL.md` directive and the inline table guidance is reduced to a D5-shaped orchestration note.
- [x] Given the skill expresses the shared-format principle, when I read its prose, then it states that the tables describe what the *user sees* (not what the system does) and that discrepancies between the map and actual code are drift signals — without invoking `/review` as a line-leading slash command.
- [x] Given `/review` is a natural second consumer, when this story completes, then `/review` wiring is documented as future work in the spec and is **not** modified here.
- [x] Given `error-rescue-mapping` is registered, when `bash scripts/gen-skill.sh` regenerates the catalog, then the root `SKILL.md` lists `error-rescue-mapping`.

## Implementation Tasks

- [x] 3.1 Record the pre-extraction line count of `commands/create-spec.md` Step 2.8 and identify the durable capability (the table technique, the `[UNPLANNED]` marker, the "what the user sees" principle) versus the spec-authoring orchestration that stays.
- [x] 3.2 Author `skills/error-rescue-mapping/SKILL.md` — the three tables, the `[UNPLANNED]` → `[OUT OF SCOPE — reason]` resolution discipline, and the drift-signal framing as capability prose; run `bash scripts/lint-skill.sh skills/error-rescue-mapping/SKILL.md` and rewrite any `/review`/`Read commands/` orchestration into running-prose references until clean.
- [x] 3.3 Wire `commands/create-spec.md` Step 2.8 to `Read skills/error-rescue-mapping/SKILL.md` and shrink the inline guidance to a D5-shaped orchestration note (skill owns how to build the maps; create-spec owns when to include them and which sub-specs need them).
- [x] 3.4 Register `error-rescue-mapping` alphabetically under `skills:` in `.writ/manifest.yaml` and regenerate the root catalog with `bash scripts/gen-skill.sh`.
- [x] 3.5 Confirm the shrink preserved create-spec's decision of *when* to include error mapping (data-flow features vs. pure UI/CSS/docs/config) — that inclusion heuristic stays in the command, not the skill.
- [x] 3.6 Verify the story: `bash scripts/lint-skill.sh skills/error-rescue-mapping/SKILL.md`, a grep confirming `commands/create-spec.md` references the skill path, and the recorded line-count drop.

## Notes

- The tables in `error-rescue-mapping` are the same structures `/review` emits — that is the reuse thesis. Wiring `/review` is deliberately deferred to keep this story inside the owned command set.
- The `[UNPLANNED]` marker is the highest-value output of the technique; the skill must preserve the rule that every `[UNPLANNED]` is resolved before implementation or made an explicit `[OUT OF SCOPE — reason]`.
- Watch the lint: the source prose says "identical structures to `/review`'s output" — write `/review` inside a sentence, never as the first token of a line.
- Keep the skill agnostic to spec structure; it describes how to build failure maps for any data-flow feature, not how `/create-spec` assembles a package.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `skills/error-rescue-mapping/SKILL.md` lints clean
- [x] `commands/create-spec.md` references the skill by path and is measurably shorter
- [x] Root `SKILL.md` regenerated

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Author skill body`, `technical-spec.md` → `## Error & Rescue Map` → `Shrink command`, `technical-spec.md` → `## Error & Rescue Map` → `Parse manifest after edit`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Extraction transform`, `technical-spec.md` → `## Shadow Paths` → `Catalog sync`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 3 (capability prose only), `spec.md` → `### Business Rules` → Rule 7 (shrink preserves owned behavior), `spec.md` → `### Business Rules` → Rule 8 (alphabetical additive manifest)]
- **Experience:** [`spec.md` → `## Detailed Requirements` → R5 (extract error-rescue-mapping), `technical-spec.md` → `### D3 — Skill Bodies Are Capability Prose Only`, `technical-spec.md` → `### D5 — Command Shrink Note Shape`]

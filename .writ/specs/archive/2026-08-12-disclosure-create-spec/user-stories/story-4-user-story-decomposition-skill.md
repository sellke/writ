# Story 4: Author the `user-story-decomposition` Skill

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

**As a** developer whose locked contract needs breaking into stories
**I want to** the story-plan format, the per-story file requirements, the context-hint parameters, and the sub-spec selection rules authored as a skill — with the parallel-subagent launch deliberately left behind
**So that** the capability half becomes reusable by other spec-shaped commands and the orchestration half stays where ADR-009 and `lint-skill.sh` require it

## Acceptance Criteria

- [ ] Given rule-inventory rows 98–107 span Steps 2.5 through 2.8, when this story lands, then `skills/user-story-decomposition/SKILL.md` carries rows 98–104, 106, and 107 — the four planning steps with **5-7 implementation tasks max**, the story-plan output format, the `agents/user-story-generator.md` reference, the nine per-agent inputs, the `spec_content` / `technical_spec_content` context-hint parameters with the empty-string fallback and its exact note phrasing, the story-file contents including **3-5 Given/When/Then criteria** and the tests-first/verification-last ordering, the README's three elements, and the sub-spec set with `technical-spec.md` always.
- [ ] Given `scripts/lint-skill.sh` rejects subagent dispatch inside a skill body, when this story lands, then rule-inventory rows 105 and 108 — "Launch parallel Task subagents", the `generalPurpose` / model `fast` dispatch, "in a single message", "up to 4 simultaneously", "batch beyond 4", and "Step 2.8 can run in parallel with 2.6" — are **absent from the skill**, left in place in the command for Story 6, and `bash scripts/lint-skill.sh skills/user-story-decomposition/SKILL.md` exits 0 with no `Task(` finding.
- [ ] Given Business Rule 12 keeps `error-rescue-mapping` at one consumer and inline, when this story lands, then rows 109 and 110 are **absent from the skill** — the data-flow applicability heuristic with its "when in doubt, include it" rule and the `Read skills/error-rescue-mapping/SKILL.md` pointer with its *when*-versus-*how* ownership sentence stay in the command, which is also what `lint-skill.sh`'s `Read skills/` rejection requires.
- [ ] Given the file disagrees with itself about task counts, when this story lands, then **every figure is preserved at its current value** — Step 2.5's "5-7 implementation tasks max", the frontmatter `exit_criteria`'s "no more than 7 implementation tasks", and `## Completion`'s "5-7 implementation tasks" — and the disagreement is recorded in this story's notes rather than resolved.
- [ ] Given this story is additive, when this story lands, then `git diff --name-only` shows no change to `commands/create-spec.md`, `bash scripts/gen-skill.sh --check` reports no delta, and `bash scripts/eval.sh` reports no new findings.

## Implementation Tasks

- [ ] 4.1 Read Story 1's namespace reconciliation and confirm `user-story-decomposition` survived the head-noun check against the sibling `phase-decomposition`. Re-measure `sed -n '719,763p' commands/create-spec.md | wc -c` against 2,474
- [ ] 4.2 Identify exactly which lines carry the subagent dispatch, so the capability/orchestration cut is made on evidence rather than by heading
- [ ] 4.3 Run `/new-skill user-story-decomposition` — bare-imperative description covering breaking a locked contract into standalone-value stories with dependencies, bounded task counts, and per-story context hints; manifest entry; `gen-skill.sh --check`
- [ ] 4.4 Author rows 98–104, 106, 107, preserving the story-plan output block and the context-hint fallback phrasing verbatim
- [ ] 4.5 Verify the skill body contains no `Task(`, no `Read skills/`, no `Read commands/`, and no line beginning with a slash command; run `bash scripts/lint-skill.sh skills/user-story-decomposition/SKILL.md`
- [ ] 4.6 Verify: `bash scripts/gen-skill.sh --check`, `bash scripts/eval.sh`, `git diff --name-only` for command cleanliness
- [ ] 4.7 Check off rule-inventory rows 98–110 with destinations, marking 105, 108, 109, 110 as retained in the command; record the preserved task-count disagreement and the skill's measured byte size

## Notes

**Technical considerations:**

- This is the smallest extraction in the spec — 2,474 bytes — and it is still worth doing because it is the one block carrying a **capability/orchestration split** the lint enforces mechanically. It is the worked example of that boundary for the sibling disclosure specs.
- The split line is concrete: *what a story file must contain* is a capability; *how many subagents run at once* is orchestration. `agents/user-story-generator.md` is named as a prose reference from the skill — a reference, not a `Read commands/` invocation, so the lint passes.
- Row 103's timing note has exact fallback phrasing (*"Technical spec not yet generated — scope hints to spec.md sections only…"*) that is passed into a subagent prompt. Preserve the string.
- `error-rescue-mapping` was extracted in Phase 7 and its `status_evidence` records exactly one consumer: `commands/create-spec.md`. The pointer stays in the command both because `lint-skill.sh:52` forbids a skill reading another skill and because removing it would drop an existing skill to zero consumers. **Amended 2026-08-12:** that inline read at line 765 is now the spec's *worked example* of the load mechanism the maintainer ruling adopted for all five new skills — a conditional read at the point of need, behind the data-flow heuristic, which a docs-only run never issues. Leave it exactly where it is.
- The name is qualified. A sibling disclosure spec claims `phase-decomposition`; these are different capabilities (a contract into stories vs. a phase into specs), and the qualified form removes the question without invoking the collision protocol's declare-the-incumbent branch.
- `assess-spec` and `edit-spec` are prospective consumers, not evidence.

**Risks / challenges:**

- **Resolving the task-count disagreement.** Three places say slightly different things about how many implementation tasks a story may have. Making them agree is a behavioral change (Business Rule 2). Record it; `/refresh-command` or a later spec owns the fix.
- **Moving the subagent launch because it "reads like procedure."** It is orchestration procedure, which ADR-009 assigns to commands. If the extraction fails lint on `Task(`, the fix is to leave the line in the command, not to reword it past the pattern.
- **Folding this skill into `spec-package-authoring`** because both are Phase 2. They are separate capabilities with different reuse; merging them would also make a single ~11 KB skill that every mode pays for.

**Integration points:**

- Story 6 writes the phase list covering Steps 2.5–2.9 and keeps the orchestration lines this story leaves behind.
- Story 3 owns the `spec.md` and `spec-lite.md` content; this story owns the story files and sub-spec set. No overlap on Step 2.6.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/user-story-decomposition/SKILL.md` exits 0, with no `Task(` or `Read skills/` finding
- [ ] `bash scripts/gen-skill.sh --check` reports no delta
- [ ] `bash scripts/eval.sh` shows no new findings
- [ ] `git diff --name-only` shows no path under `commands/`
- [ ] Rule-inventory rows 98–104, 106, 107 checked off; rows 105, 108–110 marked as retained in the command
- [ ] Task-count disagreement recorded, unfixed
- [ ] Skill's measured byte size recorded for Story 6's ceiling arithmetic

## Context for Agents

- **Business rules:** BR2, BR7, BR9 (qualified name, collision protocol), BR10, BR12 (`error-rescue-mapping` stays inline in the command) — from spec.md → 📋 Business Rules
- **Rule inventory rows:** 98–110, with 105, 108, 109, 110 retained in the command — from sub-specs/technical-spec.md → Rule Inventory
- **Lint grammar:** `Task(` = subagent dispatch, `Read skills/` = skill chaining, both rejected in skill bodies — from sub-specs/technical-spec.md → Skill Authoring Constraints
- **Technical concerns:** the preserved internal inconsistencies — from spec.md → Technical Concerns

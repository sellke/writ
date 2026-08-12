# Story 5: Author the `spec-source-prepopulation` Skill

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

**As a** maintainer holding the ceiling bar
**I want to** both source modes authored as one skill, with their near-identical halves collapsed into one parameterized block
**So that** 7,809 bytes of source-mode procedure leave the command and the largest single compression opportunity in the spec is taken where the duplication actually is

## Acceptance Criteria

- [ ] Given rule-inventory rows 18–41 cover both source modes, when this story lands, then `skills/spec-source-prepopulation/SKILL.md` carries all 24 rows — both Step 0 reads, both pre-populated draft field sets, both opening framing lines verbatim, both distinct sets of five anchor questions, the 3–5 and 2–4 exchange budgets, both contract shape blocks, the `Status: Completed ✅` Story 1 handling with its rationale, and the `spec_ref` writeback with its "only the `spec_ref` line changes" and "the issue is never deleted or archived" rules.
- [ ] Given the `--from-issue` error path must not mutate the source, when this story lands, then row 33's exact error block and its **"Do not modify the issue file on error"** rule are present, and row 41's "absent `spec_ref` line → append to frontmatter rather than fail" rule survives.
- [ ] Given Compression Ledger entries 2, 3, and 5 target ~1,200 bytes combined here, when this story lands, then the two *Step 2: Contract Proposal* paragraphs (139–141, 223–225) are one parameterized block, the two `--from-*` contract shape blocks (144–156, 228–239) share one parameterized skeleton, both point at the `contract-lock` format as the single authority for the standard contract sections, the **measured** yield of each entry is recorded, and each mode's *distinct* content — its framing line, its anchor questions, its exchange budget, its Phase 2 side effect — remains separate.
- [ ] Given `eval.sh:1647–1648` pin `\`/create-spec --recommend --from-issue <one-path>\`` and `\`/create-spec --recommend --from-prototype\`` to the command, when this story lands, then neither invocation-matrix row is touched, rule-inventory row 17's `--from-issue` `spec_ref` clause remains in `## Recommended Mode`, and `bash scripts/eval.sh --check=recommended-spec-implementation` passes all eight row assertions and all three ordering assertions.
- [ ] Given this story is additive, when this story lands, then `git diff --name-only` shows no change to `commands/create-spec.md`, `bash scripts/lint-skill.sh skills/spec-source-prepopulation/SKILL.md` exits 0, `bash scripts/gen-skill.sh --check` reports no delta, and `bash scripts/eval.sh` reports no new findings.

## Implementation Tasks

- [ ] 5.1 Read Story 1's namespace reconciliation and confirm `spec-source-prepopulation` survived. Re-measure both modes (`sed -n '100,171p' … | wc -c` and `sed -n '172,256p' … | wc -c`) against 3,983 and 3,826
- [ ] 5.2 Run `/new-skill spec-source-prepopulation` — bare-imperative description covering pre-populating a specification contract from an existing source artifact (a prototype diff or a captured issue); manifest entry; `gen-skill.sh --check`
- [ ] 5.3 Author rows 18–31 (`--from-prototype`), keeping the clean-tree warning text and the "why Story 1 is auto-complete" rationale
- [ ] 5.4 Author rows 32–41 (`--from-issue`), keeping the path-validation error block, the seven parsed issue fields, and both `spec_ref` rules
- [ ] 5.5 Apply Compression Ledger entries 2 and 3 — one parameterized contract-proposal paragraph, one parameterized contract shape block — and entry 5's pointer to the `contract-lock` format authority, coordinated with Story 2. Measure and record each yield
- [ ] 5.6 Verify every distinct rule survived the parameterization: two framing lines, two sets of five anchor questions, two exchange budgets (3–5 and 2–4), and two different Phase 2 side effects (`Completed ✅` vs `spec_ref` writeback)
- [ ] 5.7 Verify: `bash scripts/lint-skill.sh`, `bash scripts/gen-skill.sh --check`, `bash scripts/eval.sh`, `--check=recommended-spec-implementation`, `git diff --name-only`; check off rule-inventory rows 18–41 and record the skill's measured byte size

## Notes

**Technical considerations:**

- Two modes, one skill. They are structurally the same capability — read an existing artifact, derive a contract draft from it, run a shortened discovery, modify one thing about Phase 2's output — differing in the artifact and in that one side effect. Splitting them would add ~650 bytes of scaffolding to save nothing, since no invocation loads one without the other having been considered.
- **This is where the ceiling is won or lost.** Compression Ledger entries 2, 3, and 5 land ~1,200 of the ~3,300 total identified bytes here, because this is where the duplication actually is. Parameterization is the permitted move; deleting one mode's anchor questions because they resemble the other's is not.
- The `--recommend` matrix rows naming both modes stay in `## Recommended Mode`, untouched, along with row 17's clause that the `spec_ref` writeback still applies under `--recommend`. The skill describes the writeback; the command retains the statement that recommend mode does not skip it.
- **Amended 2026-08-12.** Under the superseded eager design this skill was pre-loaded on **every** invocation, including standard runs that never enter either mode — 7,809 bytes paid for nothing, priced into the ceiling bar. The maintainer ruling replaced that with an inline `Read skills/spec-source-prepopulation/SKILL.md` placed at Step 0 **after** the `--from-*` mode branch, so a standard run never issues the read and never pays. **This story's skill is the largest single beneficiary of the ruling, and it carries the placement's one real hazard:** placed before the branch instead of after it, the biggest skill in the spec becomes a floor cost on every run. Story 6 verifies the line number. The compression still matters — it counts against the worst-path ceiling — but it is no longer the only thing standing between a standard run and 7,809 wasted bytes.
- Row 6 records an existing gap: `--from-issue` is documented at line 175 but missing from `## Invocation` (25–29). Story 6 adds the row when it rebuilds the table.

**Risks / challenges:**

- **Losing "do not modify the issue file on error"** while compressing the error block. It is a data-safety rule and it sits one sentence from the error text it belongs to.
- **Over-parameterizing the shortened discovery flows.** They have different exchange budgets, different opening framings, and different anchor questions. One flow with a parameter is a redesign, not a contraction — the permitted move collapses two *near-identical* blocks, and these two are not.
- Marking Story 1 `Completed ✅` is `--from-prototype`-only. Applying it to `--from-issue` would misreport a promoted issue as already built.
- Entry 5's pointer is shared with Story 2. If both stories independently invent a pointer, the "one authority" is two.

**Integration points:**

- Story 2 owns the contract format block this skill points at. `lint-skill.sh` forbids `Read skills/` inside a skill body, so the pointer is prose resolved by the command's phase list, not a cross-skill read.
- Story 6 rebuilds `## Invocation` and must list all four invocation forms, including this story's two.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/spec-source-prepopulation/SKILL.md` exits 0
- [ ] `bash scripts/gen-skill.sh --check` reports no delta
- [ ] `bash scripts/eval.sh` and `--check=recommended-spec-implementation` show no new findings
- [ ] `git diff --name-only` shows no path under `commands/`
- [ ] Compression Ledger entries 2, 3, and 5 each recorded with a measured yield; entry 5 coordinated with Story 2
- [ ] Both modes' distinct framings, anchor questions, exchange budgets, and Phase 2 side effects verified present
- [ ] Rule-inventory rows 18–41 each checked off with a destination
- [ ] Skill's measured byte size recorded for Story 6's ceiling arithmetic

## Context for Agents

- **Business rules:** BR1 (ceiling — this story carries the largest compression share), BR2 (permitted contraction categories), BR5, BR7 — from spec.md → 📋 Business Rules
- **Rule inventory rows:** 18–41 — from sub-specs/technical-spec.md → Rule Inventory
- **Compression Ledger entries 2, 3, 5** — from sub-specs/technical-spec.md → Compression Ledger
- **Shadow paths:** `--from-issue` bad path, `--from-prototype` clean tree — from sub-specs/technical-spec.md → Shadow Paths
- **Pinned matrix rows:** `--recommend --from-issue <one-path>`, `--recommend --from-prototype` — from spec.md → The finding that reframes the work

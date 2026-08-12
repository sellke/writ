# Story 1: Clause Ledger and Gate Census

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None within this spec — externally blocked on `2026-08-12-disclosure-implement-story` having landed its skills

## User Story

**As a** maintainer thinning `commands/ship.md` under a contract that says "relocate and contract; do not redesign"
**I want** every normative clause in the file enumerated, classified, and given a destination before a single byte moves, and the dependency spec's extraction pattern recorded
**So that** "nothing was lost" becomes a row-by-row check a reviewer can run instead of a claim the author makes, and so the four skills are authored to the phase's established shape rather than to a second invented one

## Acceptance Criteria

- [ ] Given `commands/ship.md` is 28,371 bytes / 627 lines, when this story lands, then `sub-specs/clause-ledger.md` exists with one row per normative clause — imperative, behavior-stating table row, decision branch, user-visible output block, or warning — each carrying a byte offset, a ≤12-word précis or the verbatim clause, and a **Class** of `procedure` / `gate` / `provenance` / `contract` / `output`, with the **Disposition** column present and empty.
- [ ] Given Business Rule 4 names four gate-crossing clause groups, when this story lands, then the ledger's `gate` class covers all four — the draft-vs-ready determination and `--draft` override, the push plus `gh pr create` plus `gh auth` rescue, the commit-plan `AskQuestion`, and the merge-conflict pause plus the `--test` failure branch — and the story notes record any fifth gate-crossing clause the census found that the spec did not anticipate.
- [ ] Given `scripts/eval-git-notes-audit.py` `scenario_ship()` asserts seven literal conditions against `commands/ship.md`, when this story lands, then each of the seven is a `provenance`-class ledger row annotated with the asserting scenario name, so a later trim cannot remove one without a visible ledger consequence.
- [ ] Given the contract binds this spec to the dependency's pattern, when this story lands, then the ledger document carries a **Dependency Pattern** section recording, from the dependency spec's actually-landed files: its skill naming convention, its SKILL.md section order, its `status_evidence` wording, how its command file renders the phase list with gate names, and whether it retained `## Required Artifacts` and `## Integration with Writ`.
- [ ] Given § Detailed Requirements proposes a phase-list table shape and a skill roster, when this story lands, then any divergence from the dependency's landed pattern is recorded explicitly as a delta with the dependency's shape marked authoritative — and if there is no divergence, that is stated rather than left implicit.
- [ ] Given the ledger is the verification instrument for Business Rule 2, when this story lands, then it also carries the pre-change measurement block verbatim from `python3 scripts/measure-invocation.py --root . --command ship` (`command_bytes`, `command_lines`, `eager_bytes`, `floor_bytes`, `conditional_bytes`, `ceiling_bytes`, `eager_skills`, `conditional_skills`), re-run rather than copied from `spec.md`, and confirms the tool is the post-`e8f2a09` build by checking that `conditional_bytes` reports 9,985 rather than 0 — a 0 means the fix is absent and every bar in this spec is derived from a broken instrument.
- [ ] Given the loading mechanism is an inline `Read` at the point of need (spec.md → *Approved scope change*, BR3), when the Dependency Pattern section is written, then it records **how the dependency reaches its skills** — inline reads at steps, or `required_skills:` declarations — and if the dependency declared, the section states explicitly that **this spec does not follow it on that point**, because the 2026-08-12 maintainer ruling overrides the follow-the-dependency clause on the loading mechanism specifically. Every other element of the dependency's pattern still wins.
- [ ] Given this story changes no product source, when this story lands, then `git diff --name-only` lists only paths under `.writ/specs/2026-08-12-disclosure-ship/`.

## Implementation Tasks

- [ ] 1.1 Verify the dependency has **landed**, not merely been authored: its eight `skills/<name>/SKILL.md` files exist, `commands/implement-story.md` reaches them (by inline `Read` per the 2026-08-12 ruling, or by `required_skills:` if it landed before the ruling — either counts as landed, and which one it is goes in the Dependency Pattern section as a recorded divergence), `.writ/docs/skills.md` carries an *Extraction Patterns* section, and ADR-021 carries its `## Amendments`. `spec-deps.py` returning `status: ok` proves none of this. If any is absent, **stop and escalate** — the contract binds this spec to a pattern that does not yet exist, and inventing one here creates the divergence the contract exists to prevent
- [ ] 1.2 Re-run `python3 scripts/measure-invocation.py --root . --command ship` and `wc -c -l commands/ship.md`; record the output verbatim. Expect floor 53,331 / cond 9,985 / ceiling 63,316 from the post-`e8f2a09` tool; if `conditional_bytes` is 0, stop — the tool predates the fix and no bar in this spec is meaningful against it. If any other number differs from `spec.md`'s table, record the delta and use the fresh number
- [ ] 1.2a Record the five `Read` anchors the spec assigns (technical-spec → *The `Read` anchors*), and note for Story 4 that `ship.md:224` is preserved in place rather than relocated or converted
- [ ] 1.3 Read `commands/ship.md` end to end and enumerate every normative clause into `sub-specs/clause-ledger.md` with byte offset, précis, and class. Expand every table into per-row clauses — the layer/prefix table, the label table, the draft-vs-ready table, the detection chains, the PR-body population table, and the landed-SHA strategy table each carry behavior per row
- [ ] 1.4 Classify the four gate groups as `gate` and the seven `eval-git-notes-audit.py` literals as `provenance`, annotating each provenance row with its scenario name (`ship-references-writ-ref`, `ship-uses-notes-add-command`, `ship-non-blocking`, `ship-honors-opt-out`, `ship-attaches-to-landed-commit`, `ship-nil-wwb-fallback`, `ship-never-default-ref`)
- [ ] 1.5 Mark the duplicate-clause pairs that are legitimate `deduped` candidates — the Step 4 and Step 5 `--dry-run` previews appear both inline at the end of Step 6 and again under `## Dry Run Mode`. Verify the duplication by diffing the two blocks rather than assuming it; if they differ in substance, neither is a dedup candidate
- [ ] 1.6 Read the dependency spec's landed skills and command file; write the **Dependency Pattern** section and the divergence deltas against this spec's § Detailed Requirements
- [ ] 1.7 Sanity-check the ledger's coverage: the sum of ledgered clause byte spans plus non-normative prose must account for the whole file. Record any section with zero clauses and justify it (a section of pure motivation is legitimate; a Step with zero clauses is a census error)

## Notes

**Technical considerations:**

- The ledger is a spec artifact, not product source. It lives at `.writ/specs/2026-08-12-disclosure-ship/sub-specs/clause-ledger.md` and ships nowhere.
- Byte offsets shift the moment Story 4 edits the file. That is fine — the offset is a *locator for the pre-change file*, recorded so a reviewer can find the original clause in `git show HEAD:commands/ship.md`. Do not attempt to keep offsets current.
- A clause is not a sentence. "I recommend **merge** (not rebase) because it preserves commit history for bisection" is one clause with a reason attached; the reason travels with it and is not a second row.
- Prose that only motivates an adjacent clause is not ledgered. `## Overview`'s "How `/ship` absorbs the PR agent concept" is three paragraphs of history — one row at most, class `output`, and its disposition will likely be a compression rather than a relocation.
- The census is the expensive part of this spec. Rushing it produces a ledger that is complete-looking and thin, which is worse than no ledger — it converts an unverified claim into a falsely verified one.

**Risks / challenges:**

- **The dependency is authored but may not be implemented when this runs.** `spec-deps.py validate` returned `status: ok` on 2026-08-12, which proves only that the spec folder exists. Task 1.1 is a stop-and-escalate gate on its **landed** files — the eight skills, `.writ/docs/skills.md` → *Extraction Patterns*, the ADR-021 amendments. A green graph is not the pattern.
- **Under-counting tables.** A six-row detection chain enumerated as one clause loses five behaviors. Every row that states behavior is a row.
- **Scope creep into deciding dispositions.** This story writes the Disposition column as empty. Story 4 fills it. Pre-deciding here means the census is done with the answer already chosen, which is how clauses get quietly classified as unnecessary.
- **Recording the dependency's pattern as "roughly the same."** The contract says follow it. A précis that omits its section order or its `status_evidence` wording forces Story 2 and 3 to re-read the dependency anyway.

**Integration points:**

- Stories 2, 3, and 4 all author against the Dependency Pattern section.
- Story 4 fills every Disposition cell; Story 5 closes and audits the ledger.
- `scripts/measure-invocation.py` is the sole instrument for every budget figure in this spec.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `sub-specs/clause-ledger.md` covers every section of `commands/ship.md`, with an empty Disposition column
- [ ] Four gate groups and seven provenance literals classified and annotated
- [ ] Dependency Pattern section written from the dependency's landed files, with divergence deltas
- [ ] `git diff --name-only` lists only paths under this spec's folder

## Context for Agents

- **Business rules:** [BR2 clause ledger as the no-redesign verification method; BR4 gate-crossing classes; BR6 provenance literals] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The phase list with gate names; Skill roster] — from spec.md → ## Detailed Requirements
- **Technical spec:** [Measured Baseline; Section-by-section byte census; The Clause Ledger (Story 1 deliverable)] — from sub-specs/technical-spec.md
- **Contract:** ["Follow the extraction pattern and skill-naming convention established by the dependency spec `2026-08-12-disclosure-implement-story`"] — from spec.md → ## Contract (Locked)
- **Technical concerns:** [The dependency spec does not exist yet; `eval-git-notes-audit.py` pins seven literal strings] — from spec.md → ## Technical Concerns

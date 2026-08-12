# Story 2: The Eight-Check Diagnostic as a Skill

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** developer running `/verify-spec` on a drifted spec
**I want to** the eight checks, their sub-checks, and their repairs to be a single loadable capability rather than 12,900 bytes of the command file
**So that** the command declares *what* it checks and the skill carries *how*, without a single sub-check or disposition changing on the way across

## Scope

One skill — `spec-metadata-diagnosis`. It carries the largest share of the extraction:

| Source | Lines | Bytes |
|---|---|---:|
| Phase 1 — spec discovery, the six-item read list, the JSON data model | 38–110 | 2,408 |
| Phase 2 header — run-all-collect-all discipline, mode behavior | 112–122 | 433 |
| Check 1 — story file integrity (1a–1d) | 124–155 | 784 |
| Check 2 — status consistency (2a–2c) | 157–180 | 609 |
| Check 3 — completion integrity (3a–3d) | 182–211 | 903 |
| Check 4 — dependency validation (4a–4d) | 213–260 | 2,053 |
| Check 5 — deliverables checklist (5a–5b) | 262–280 | 532 |
| Check 6 — contract vs implementation | 282–299 | 567 |
| Check 7 — spec-lite integrity, minus its `--fix` behavior and report block | 301–352 | ~1,900 |
| Check 8 — spec owner field presence | 354–389 | 1,321 |
| Repairs 4.1–4.3 — README sync, deliverables sync, status headers | 448–465 | ~600 |
| | | **~12,110** |

**Allocation: ≤ 11,600 bytes** including skill frontmatter, `## Purpose`, and `## When to Use`.

Not in this story: step 4.4 and Check 7's `--fix` behavior (Story 3), all report shapes (Story 4), the `--product` set (Story 3).

## Acceptance Criteria

- [ ] Given the skill is authored through `/new-skill`, when it is created, then `skills/<name>/SKILL.md` carries `status: candidate`, `disable-model-invocation: true`, a verb-phrase `description:`, `## Purpose`, and `## When to Use`, and `bash scripts/lint-skill.sh` exits 0.
- [ ] Given Business Rule 4, when the skill is compared against Story 1's ledger, then Checks 1–8 appear with their heading strings **verbatim** and their sub-check identifiers (1a–1d, 2a–2c, 3a–3d, 4a–4d, 5a–5b) intact and unrenamed.
- [ ] Given Business Rule 3's ambiguity clause, when Check 1's disposition is read, then it is still unstated — no disposition has been supplied for a check the source leaves unstated.
- [ ] Given Business Rule 6, when Check 4's disposition text is read, then 4a–4c are report-only in both default and `--check`; 4d is blocking for `malformed_dependencies`, `missing_reference`, `self_reference`, and `dependency_cycle`; and duplicates auto-fix by **first-occurrence-preserving** deduplication. `scripts/spec-deps.py validate` is still named as the executable reference, and overlap heuristics still may only warn and may never reorder a valid explicit graph.
- [ ] Given Business Rule 6, when Checks 6, 7, and 8 are read, then 6 is report-only heuristic in both modes; 7 is auto-fixable in default, report-only under `--check`, and **skipped without a flag** when `spec-lite.md` is absent; 8 is warning-only, never fails verification, never backfills without explicit approval, and reports pre-2026-04-24 specs as legacy without warning.
- [ ] Given Business Rule 7, when the skill's headings and numbered steps are scanned with `grep -rEn '^\s*(#{2,4} |[0-9]+\.[0-9]* ).*re-?(check|verify|run)'`, then there is no match.
- [ ] Given `lint-skill.sh`'s body grammar, when the skill body is read, then it contains no `Read commands/`, no `Read skills/`, no `Task(`, and no line beginning with a slash command — and every re-shaped line preserves its original meaning rather than dropping it.
- [ ] Given the `--all` archive-exclusion reasoning, when Phase 1's discovery text is read, then the single-level `.writ/specs/*/` glob **and the explanation that no explicit `archive/` filter should be added** both survive, along with the deferred `--include-archived` note.
- [ ] Given Business Rule 5, when the extracted text is reviewed, then the four `require_literal` strings this skill's source range contains — `Cross-spec dependency validation`, `self-reference`, `story dependency validation is unchanged` (all in Check 4d) and `spec-lifecycle.md` (Phase 1's `--all` prose) — are each flagged with the minimum carrier Story 5 must keep in the command file, and the skill never introduces the `forbid_literal` string `specs/**`.
- [ ] Given the allocation, when `wc -c skills/<name>/SKILL.md` is run, then it is ≤ 11,600 bytes, or the overage is reported against another skill's underage so the Σ ≤ 24,200 total still holds.

## Implementation Tasks

- [ ] 2.1 Read Story 1's ledger and confirmed skill name; read `skills/tdd-cycle/SKILL.md` as the density exemplar
- [ ] 2.2 Scaffold the skill with `/new-skill <name>`; confirm `status: candidate` and a lint-clean verb-phrase description before writing any body
- [ ] 2.3 Port Phase 1 — compress the 2,408-byte JSON model to a compact schema statement while preserving the six-item read list, the `--spec` / `--all` resolution rules, and the archive-exclusion reasoning
- [ ] 2.4 Port Checks 1, 2, 3 with every sub-check and every pseudo-code block's decision content
- [ ] 2.5 Port Check 4 including 4d's five finding names, the dedupe exception, the `spec-deps.py validate` reference, and the blocking/warning boundary
- [ ] 2.5a Record the four pinned strings this story's source range moves, with the carrier Story 5 must retain in the command; confirm the skill never contains `specs/**`
- [ ] 2.6 Port Checks 5, 6, 8 with dispositions as stated
- [ ] 2.7 Port Check 7's purpose, skip rule, section-mapping table, heading normalization, and the material-divergence flag/do-not-flag lists — leaving `--fix` behavior to Story 3 and the report block to Story 4
- [ ] 2.8 Port repairs 4.1–4.3 as the check-specific repair procedures, keeping their step numbers
- [ ] 2.9 Run `bash scripts/lint-skill.sh` and the re-check grep; re-shape any rejected line without dropping content
- [ ] 2.10 Diff the skill against Story 1's ledger row by row; measure bytes and record against the allocation

## Notes

**Technical considerations:**

- **Check 4d carries three of `scripts/eval.sh`'s four `require_literal` strings for this command** (`:1781-1783`). `require_literal` tests `commands/verify-spec.md`, not the skill, so those strings must *also* exist in the command's Phase 2 row — the skill may carry them, but it cannot carry them *instead*. Same for `spec-lifecycle.md` in Phase 1's `--all` prose (`:1901`). This story does not fix that; it hands Story 5 the exact list.
- Check 4d is the densest 2,053 bytes in the file and the least compressible: five named finding types, a blocking-vs-warning boundary, a dedupe exception with an ordering guarantee, and a rule that heuristics may never reorder an explicit graph. Compress the prose around it, not the enumeration inside it.
- Phase 1's JSON model is the biggest single compression opportunity in the whole spec (~2,408 bytes around a six-line read list) and also the easiest place to lose a field. The model names `deliverables[].fileExists`, `readme.totalProgress`, and per-story `acceptanceCriteria` / `definitionOfDone` counts — each is consumed by a specific check.
- Checks 2, 3, and 5 have no disposition blockquote; their auto-fix behavior is knowable only from Phase 4's steps. Keep the repairs 4.1–4.3 in this skill precisely so that inference stays available to a reader who loaded only this skill.
- The source's "collect every finding before reporting — do not stop at the first issue" discipline is a behavioral fact, not framing. It survives.

**Risks / challenges:**

- This is 48% of the extracted bytes in one file. A skill that large risks becoming a second monolith. The mitigation is not splitting it — splitting along check boundaries would scatter the diagnostic — but keeping the command's phase list carrying every check's *number, name, and disposition* so a reader never needs the skill to predict behavior.
- Re-shaping lines for `lint-skill.sh` is where content quietly disappears. Every re-shaped line is a BR3 risk; note each one.

**Integration points:**

- Story 4's report skill renders the eight-row table whose row labels come from these checks' names.
- Story 3's regeneration skill is triggered by this skill's Check 7 finding.
- Story 5 places this skill's inline `Read skills/<name>/SKILL.md` in the **Phase 1** row of the phase list (maintainer ruling 2026-08-12 — no `required_skills:`). Placement matters to this story's value: this is the largest skill in the spec (≤ 11,600 bytes), and it is the one a `--product` run must **never** reach. Under the superseded eager design a `--product` run paid for all 11,600 of it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/<name>/SKILL.md` exits 0
- [ ] Ledger rows for checks 1–8 match Story 1's transcription cell for cell
- [ ] Byte count recorded against the allocation
- [ ] Only `skills/<name>/`, `.writ/manifest.yaml`, and `SKILL.md` were modified

## Context for Agents

- **Business rules:** [BR3 no redesign + ambiguity clause, BR4 frozen numbering, BR5 pinned literals, BR6 hybrid boundary, BR7 no re-check step in skills, BR10 reachability, BR12 lint-clean] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Skills — names and allocations; The thin contract's shape → disposition stays in the command] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [`lint-skill.sh`'s body grammar will reject naive extraction] — from spec.md → ## Technical Concerns
- **Contract:** [Must include: per-phase procedural detail extracts to skills authored through `/new-skill`] — from spec.md → ## Contract (Locked)
- **Technical spec:** [The Byte Ledger; The Disposition Ledger; Skill Authoring Constraints; Where the Compression Comes From] — from sub-specs/technical-spec.md

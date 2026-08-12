# Story 4: One Report Shape, Three Instantiations

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

**As a** developer reading a verification report
**I want to** the console table, the per-spec report file, and the product report to come from one described shape instead of three copies in one command file
**So that** the eight-row rule, the skipped-row rule, and the finding classification cannot drift apart the next time one of them is edited

## Scope

One skill — `verification-report-authoring`. ~6,800 source bytes, **allocation ≤ 5,600**:

| Source | Lines | Bytes | What |
|---|---|---:|---|
| Phase 3 | 391–444 | 2,479 | Console report: the always-eight-rows table, the skipped-row rule for Check 7, the overall line, and the `Auto-Fixable` / `Needs Attention` findings detail with `[FIX-n]` / `[WARN-n]` / `[INFO-n]` classification |
| Phase 5 | 487–541 | 1,720 | `.writ/specs/<spec>/verification-YYYY-MM-DD.md`: header block, Summary table, Stories table, `Issues Found & Resolved`, `Outstanding Warnings`, `Notes`; plus the default and `--check` completion messages |
| Check 7 report block | 335–342 | ~350 | The pass and divergence renderings for row 7 |
| `--product` report | 664–700 | ~1,800 | The **P1–P4** table, the `.writ/product/verification-YYYY-MM-DD.md` path, the Regenerated / Outstanding lists, and the two `--product` completion messages |

## Acceptance Criteria

- [ ] Given the skill is authored through `/new-skill`, when it is created, then it carries `status: candidate`, `disable-model-invocation: true`, a verb-phrase `description:`, `## Purpose`, and `## When to Use`, and `bash scripts/lint-skill.sh` exits 0.
- [ ] Given the source states the table always has eight checks with no "Skipped" rows and no alternate layouts, when the skill is read, then that rule survives together with its **single exception**: row 7 is omitted with `(Check 7 skipped — no spec-lite.md found)` when `spec-lite.md` is absent.
- [ ] Given the spec report and the product report are different artifacts, when the skill is read, then the spec report renders **eight** rows to `.writ/specs/<spec-folder>/verification-YYYY-MM-DD.md` and the product report renders **four** P-prefixed rows to `.writ/product/verification-YYYY-MM-DD.md`, and neither path nor row set is interchangeable.
- [ ] Given `exit_criteria` in the preserved frontmatter asserts that every finding appears under exactly one of two sections, when the skill is read, then `Issues Found & Resolved` and `Outstanding Warnings` are both present, mutually exclusive, and an outstanding warning is stated to be a valid result rather than an incomplete run.
- [ ] Given the source's four completion messages, when the skill is read, then all four survive with their distinct text: default, `--check` (*"no files modified"*), default `--product`, and `--product --check`.
- [ ] Given the `[FIX-n]` / `[WARN-n]` / `[INFO-n]` classification carries the auto-fixed vs recorded distinction, when the skill is read, then all three prefixes survive with their meanings, including `[INFO-n]` for legacy specs without owners.
- [ ] Given Business Rule 7, when the skill's headings and numbered steps are scanned for `re-?(check|verify|run)`, then there is no match.
- [ ] Given the `Notes` line in the Phase 5 template states that this command is diagnostic-only and points at `/release` for build checks and changelog work, when the skill is read, then that boundary statement survives.
- [ ] Given the allocation, when the file is measured, then it is ≤ 5,600 bytes, or the overage is reported against another skill's underage so Σ ≤ 24,200 holds.

## Implementation Tasks

- [ ] 4.1 Read Story 1's ledger and confirmed skill name
- [ ] 4.2 Scaffold the skill with `/new-skill`; confirm the description passes the lint before writing the body
- [ ] 4.3 Describe the shared report shape once: header block, check table, findings classification, resolved/outstanding split, notes
- [ ] 4.4 Instantiate the spec console report — eight rows, the skipped-row exception, the overall counts line
- [ ] 4.5 Instantiate the spec report file — path, header block, Summary and Stories tables, both finding sections, Notes
- [ ] 4.6 Instantiate the product report — P1–P4 rows, product-scoped path, Regenerated and Outstanding lists
- [ ] 4.7 Port all four completion messages verbatim
- [ ] 4.8 Verify the deduplication lost nothing: diff each of the three source renderings against the shape-plus-instantiation form, row by row
- [ ] 4.9 Run `bash scripts/lint-skill.sh` and the re-check grep; measure bytes against the allocation

## Notes

**Technical considerations:**

- The three source renderings are similar enough to invite a single generic template and different enough that one would be wrong. The row sets differ (8 vs 4), the paths differ (per-spec vs product), the status glyphs differ (`🔧` appears only in the product table), and the outstanding-findings list is named differently (`Outstanding Warnings` vs `Outstanding (needs human judgment)`). Describe the shape once; keep every instantiation's specifics.
- The eight-row rule is a real behavioral constraint, not formatting. The source says it twice — *"The table always has **eight** checks — no 'Skipped' rows … no alternate layouts"* — because a report that quietly drops a row hides a check that did not run.
- `[INFO-n]` exists for exactly one case: a legacy spec without an owner, which is neither a fix nor a warning. It is the smallest and most losable piece of Check 8's disposition.
- **Amended 2026-08-12.** Under the superseded eager design this skill was loaded on every invocation like the others. Under the maintainer's mechanism ruling it is inline-read at Phase 3 **and** at the product report — two reads, because it serves both mutually exclusive paths — so it is genuinely the one skill nearly every *reporting* run pays for, and a run that ends before reporting does not. It is also the skill with the most compressible content, which is why its allocation carries a larger share of the total reduction than its source share.

**Risks / challenges:**

- Fenced example blocks are the easiest thing to trim and the hardest to trim safely: the console table's alignment communicates the fixed column set. Keep one full worked example per instantiation rather than three partial ones.
- A report skill that describes a shape without an example produces inconsistent output. A skill with three full examples blows the allocation. One shape statement plus three examples trimmed to their distinguishing rows is the target.

**Integration points:**

- Story 2's checks supply the eight row labels; Story 3's product checks supply the four P-rows and the Regenerated list.
- The preserved `exit_criteria` in Story 5's frontmatter asserts the eight-row table and the two-section split — this skill is what makes those assertions true.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/<name>/SKILL.md` exits 0
- [ ] The row-by-row diff proving all three renderings survived is recorded in this story's evidence
- [ ] All four completion messages present and distinct
- [ ] Byte count recorded against the allocation

## Context for Agents

- **Business rules:** [BR3 no redesign, BR4 frozen numbering, BR7 no re-check step, BR10 reachability, BR12 lint-clean] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Skills — names and allocations] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [`lint-skill.sh` body grammar] — from spec.md → ## Technical Concerns
- **Contract:** [Deliverable: per-check procedural detail extracted to skills, loaded on demand] — from spec.md → ## Contract (Locked). **"Loaded on demand" is delivered by an inline `Read` at the point of need, not by `required_skills:`** — see spec.md → *Approved Scope Change — Load Mechanism (2026-08-12)*
- **Technical spec:** [The Byte Ledger; Where the Compression Comes From, item 2] — from sub-specs/technical-spec.md

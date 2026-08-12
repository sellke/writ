# Story 5: Budget and Drift Verification

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 4

## User Story

**As a** reviewer deciding whether this spec did what its contract says
**I want** the floor and ceiling re-measured against both baselines, the ceiling movement justified in writing, and every clause's disposition audited by someone other than the author of the cut
**So that** "the file got smaller" is separated from "the framework got thinner," and a ceiling rise is explained by arithmetic rather than by the observation that disclosure sometimes does that

## Acceptance Criteria

- [ ] Given Business Rule 1, when this story lands, then the evidence records `floor_bytes`, `ceiling_bytes`, and `eager_bytes` before and after from the **post-`e8f2a09`** `python3 scripts/measure-invocation.py --root . --command ship` — before is floor 53,331 / cond 9,985 / ceiling **63,316** — the floor has fallen from 53,331, `eager_bytes` is 0 with no "loads both ways" warning, and the ceiling is **≤ 63,316**. The projection says ~57,510, a clean pass with ~5,800 B of margin: **if the bar is met, no justification is written.** Only if it is exceeded does the three-part form apply (measured overage, compression with measured yield, explicit maintainer acceptance). The withdrawn 53,331-band escalation is not resurrected.
- [ ] Given Business Rule 1's path requirement, when this story lands, then the evidence carries a measured row for each of: merge-conflict pause at Step 2, `--test` failure abort at Step 3, `--no-split` reaching Step 4, a full run with `writ.auditNotes=false`, and a full run including the audit note — each computed as `floor + Σ(skills that path reads)` with the skill list shown, and each compared against the **correct** pre-spec figure for that path: 53,331 for paths that never reached `ship.md:224`, 63,316 for paths that did. Every row is expected to improve; report the numbers rather than the claim.
- [ ] Given the exclusion must be visible rather than assumed, when this story lands, then the evidence reports the `conventional-commits`-excluded pair (pre-spec 53,331 vs post-spec ~47,525) with `conventional-commits` re-measured rather than taken from the recorded 9,985 — and states that it is an inline read in **both** states, so no phantom regression is possible.
- [ ] Given Business Rule 3 makes placement the mechanism, when this story lands, then the evidence records: five inline reads in `commands/ship.md`, each at its step; `audit-digest-composition`'s below the `writ.auditNotes` gate and `pr-body-composition`'s before the production-boundary block; no `Read skills/` in the frontmatter, `## Overview`, or the phase-list table; `grep -c required_skills commands/ship.md` = 0; and `grep -n 'Read skills/' skills/*/SKILL.md` empty (`scripts/lint-skill.sh:52`).
- [ ] Given Business Rule 2 makes the ledger the verification method, when this story lands, then every row of `sub-specs/clause-ledger.md` is audited against the actual files — `retained` rows found in `commands/ship.md`, `skill:<name>#<section>` rows found in that skill at that section, `deduped` rows naming a real duplicate — with the audit result recorded per row or as an explicit "all N rows verified" count plus the sampling method if not exhaustive.
- [ ] Given Business Rule 2's literal table, when this story lands, then the evidence carries the grep output proving each literal is present at its required location: the seven provenance literals in `commands/ship.md`, the `resolve-spec-reference.py resolve` call in the command or `pr-body-composition`, all six `## Invocation` rows, and the PR-body section names (first four in the command, all seven in `pr-body-composition`).
- [ ] Given regression must be measured rather than assumed, when this story lands, then `bash scripts/eval.sh` shows no new findings against its pre-spec baseline with all seven `git-notes-audit` `scenario_ship` checks passing, `bash scripts/eval.sh --check=length` passes, `bash scripts/lint-skill.sh skills/*/SKILL.md` exits 0, `bash scripts/gen-skill.sh --check` reports no delta, and `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` is run with its result recorded (`status: ok` as of 2026-08-12) — the dependency on `2026-08-12-disclosure-implement-story` is never removed to influence that result.
- [ ] Given Success Criterion 10 is a reading test, when this story lands, then a reviewer reads the thinned `commands/ship.md` plus its five declared skills and records which of today's behaviors, if any, cannot be answered from that set — with an empty list being the pass condition and any entry treated as a dropped clause requiring a fix in Story 4's file, not a note here.

## Implementation Tasks

- [ ] 5.1 Re-measure: `python3 scripts/measure-invocation.py --root . --command ship`, `wc -c -l commands/ship.md`, `wc -c skills/*/SKILL.md`. Record every figure. Re-measure `skills/conventional-commits/SKILL.md` rather than reusing the 9,985 recorded at spec time. Confirm the tool is post-`e8f2a09` (pre-spec `conditional_bytes` 9,985, not 0)
- [ ] 5.2 Build the path table with the script in technical-spec → Testing Strategy check 2: floor, conflict pause, `--no-split`, `auditNotes=false`, full run, plus the `conventional-commits`-excluded pair. State plainly which paths improved and by how much. Write a ceiling justification **only if** the measured ceiling exceeds 63,316
- [ ] 5.3 Audit the clause ledger row by row against the landed files; record the result and any row whose target text cannot be found
- [ ] 5.4 Run the Business Rule 2 literal greps and paste the output as evidence — asserted presence is not evidence
- [ ] 5.5 Run `bash scripts/eval.sh`, `bash scripts/eval.sh --check=length`, `python3 scripts/eval-git-notes-audit.py`, `bash scripts/lint-skill.sh skills/*/SKILL.md`, `bash scripts/gen-skill.sh --check`, `python3 scripts/spec-deps.py validate --specs-dir .writ/specs`, and `git diff --name-only`; record all results

## Notes

**Technical considerations:**

- Every budget number comes from `scripts/measure-invocation.py`. Do not compute floors by adding file sizes by hand — the script defines what "an invocation loads," including which files count as base.
- Report **bytes**. The script's `token_method_validated: false` means every `*_tokens_estimated` figure is chars/4, an assumption its own docstring flags as having been "quoted as though it were measured." Quoting a token number in this story's evidence would repeat that.
- The ceiling justification is no longer the expected deliverable — the path table is. ADR-021 names caveat 2 as the thing that could invalidate the approach, and on `/ship` the measurement is expected to clear it on every path. **Do not write a justification for an overage that did not occur**; a defensive justification attached to a passing number is noise that trains the next reader to skip them.
- The corresponding new risk is complacency. This is the spec whose numbers come out well everywhere, which makes the clause-ledger audit, the seven provenance pins, and Business Rule 4's per-clause load test the parts most likely to be treated as formalities. A −9.2% ceiling says nothing about whether a gate moved.
- `spec-deps.py` returns `status: ok` as of 2026-08-12; if a future tree regresses it to `missing_reference`, record that rather than resolving it by edit. **Deleting the dependency to produce `status: ok` would break the contract clause that binds this spec to that spec's pattern.**
- The reading test (AC 5) needs a reader who did not write Story 4. If the same agent runs both, say so in the evidence rather than implying independence that did not exist.

**Risks / challenges:**

- **Declaring success on the floor alone.** The floor falling is expected and easy; the ceiling is the number ADR-021 says can invalidate the approach.
- **Auditing the ledger by re-reading the author's own dispositions.** The audit is against the files, not against the ledger's claims.
- **Treating a dropped clause found by the reading test as a documentation note.** It is a defect in `commands/ship.md` or a skill and is fixed there.
- **A skill total that exceeds the bytes removed.** If the four new skills total more than `ship.md` shed, the extraction relocated without compressing and the ceiling arithmetic will show it. Report the comparison even though no business rule fails on it alone.

**Integration points:**

- Closes the ledger Story 1 created and Story 4 filled.
- `scripts/measure-invocation.py`, `scripts/eval.sh`, `scripts/eval-git-notes-audit.py`, `scripts/lint-skill.sh`, `scripts/gen-skill.sh`, `scripts/spec-deps.py` — all read-only here; Business Rule 9 forbids editing any of them.
- The measured after-figures are the input to ADR-021's 2026-11-11 review trigger, which asks whether per-invocation load dropped for at least 4 of the 6 targeted commands.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Floor before/after recorded; floor has fallen
- [ ] Ceiling before (63,316) / after / after-excluding-`conventional-commits` recorded, with a written justification **only** if above 63,316
- [ ] Path table measured — conflict pause, `--test` abort, `--no-split`, `auditNotes=false`, full run — each against the correct pre-spec figure
- [ ] Placement verified: five inline reads at their steps, `eager_bytes` 0, no `required_skills:`, no hoisted or skill-resident `Read skills/`
- [ ] Clause ledger audited against landed files, result recorded
- [ ] Business Rule 2 literal greps pasted as evidence
- [ ] `eval.sh`, `eval.sh --check=length`, `lint-skill.sh`, `gen-skill.sh --check` all clean; `spec-deps.py` result recorded
- [ ] Bound `skills`-surface justification recorded in `.writ/leanness-baseline.json`; `--update-baseline` never run
- [ ] Reading test performed and its result recorded, including whether the reader was independent of Story 4

## Context for Agents

- **Business rules:** [BR1 ceiling regression with two baselines; BR2 clause ledger and literal table; BR3 reachability; BR9 no `scripts/` edits] — from spec.md → 📋 Business Rules
- **Success criteria:** [All ten, this story reports against them] — from spec.md → ## Success Criteria
- **Technical spec:** [Testing Strategy — the eight verification blocks; Measured Baseline] — from sub-specs/technical-spec.md
- **Technical concerns:** [The measured ceiling will rise for a reason that is not disclosure; the dependency spec does not exist yet] — from spec.md → ## Technical Concerns

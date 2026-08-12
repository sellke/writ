# User Stories: Progressive Disclosure — `/ship`

> **Status:** Not Started — 0/5 stories, 0/34 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Clause Ledger and Gate Census](./story-1-clause-ledger-and-gate-census.md) | Not Started | 8 | 0/8 | None (externally blocked on the dependency's skills having landed) |
| 2 | [Convention Detection and Commit Organization Skills](./story-2-convention-and-commit-skills.md) | Not Started | 7 | 0/7 | Story 1 |
| 3 | [PR Body and Audit Digest Skills](./story-3-pr-body-and-audit-digest-skills.md) | Not Started | 7 | 0/7 | Story 1 |
| 4 | [The Thin `/ship` Contract](./story-4-thin-ship-contract.md) | Not Started | 7 | 0/7 | Stories 2, 3 |
| 5 | [Budget and Drift Verification](./story-5-budget-and-drift-verification.md) | Not Started | 5 | 0/5 | Story 4 |

## Dependency Graph

```
Story 1 (clause ledger + gate/provenance census + dependency-pattern alignment)
   ├── Story 2 (repo-convention-detection, commit-organization)  ─┐
   ├── Story 3 (pr-body-composition, audit-digest-composition)   ─┴─ parallel, one shared file
   │
   └────────► Story 4 (thin commands/ship.md + 4 inline Read anchors)  — needs both
                  └── Story 5 (measure, justify, close the ledger, run evals)
```

**Story 1 is a hard prerequisite.** Business Rule 2's verification method — the clause ledger — does not exist until it lands, and every later story writes dispositions into it. Story 1 also reads the dependency spec `2026-08-12-disclosure-implement-story`'s landed skills, its `.writ/docs/skills.md` → *Extraction Patterns* section, and its ADR-021 amendments, to record the extraction pattern and naming convention this spec is contractually bound to follow. That spec was **authored** on 2026-08-12 — `spec-deps.py validate` returns `status: ok` — but authored is not landed. **Story 1 cannot start before its skills exist on disk**; that is the dependency, not a soft ordering preference.

**Stories 2 and 3 are parallel with one real conflict surface.** Their `skills/` directories are disjoint, but both append to `.writ/manifest.yaml` and both regenerate the root `SKILL.md`. Alphabetical insertion keeps the conflict small; two independently regenerated catalogs do not merge cleanly. Sequence them or rebase the second — do not run them in separate worktrees and merge blind.

**Story 4 depends on both skill stories because every inline `Read` must resolve.** A `Read skills/<name>/SKILL.md` naming a file that does not exist surfaces in `measure-invocation.py`'s `unresolved_skills` with a warning that the figures are a lower bound. It does **not** raise an `eval-leanness.py` finding — `check_required_skills` only resolves frontmatter declarations, and this spec makes none, so that check's silence proves nothing here. Authoring the command first would mean landing a state that fails Business Rule 3 and re-verifying it later.

**Story 5 is separate from Story 4 on purpose.** Folding the measurement into the authoring story makes the author of the cut the sole judge of whether the cut was faithful. Story 5 re-measures, writes the ceiling justification, closes every ledger row, and runs the eval suite.

**Suggested execution order:** Story 1 alone → Stories 2 and 3 (sequenced on the manifest) → Story 4 → Story 5.

## Task Count

34 tasks across 5 stories. Story 1 carries 8 (one added by the 2026-08-12 mechanism ruling: record the five `Read` anchors); Stories 2–4 carry 7 each; Story 5 carries 5, because its work is measurement and reporting rather than authoring. Story 1's count reflects that a clause census over 627 lines is the expensive part of this spec — the ledger is what makes "relocate, do not redesign" checkable instead of assertable.

## Quick Links

- [spec.md](../spec.md) — locked contract, the binding budget, twelve business rules, the findings
- [spec-lite.md](../spec-lite.md) — condensed agent context
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — measured baseline, section census, retained-content minimums, skill authoring rules, verification commands
- [ADR-021](../../../decision-records/adr-021-progressive-disclosure-token-budget.md) — governing decision (thin contracts, on-demand skills, budget)
- [ADR-022](../../../decision-records/adr-022-autonomy-gate-classes.md) — the production-boundary human gate
- `scripts/measure-invocation.py` — the instrument every budget claim comes from

## Findings at Spec Time (2026-08-12)

Four at authoring time, all verified against the working tree. Each changes how a story must be executed. Finding 1 was **re-resolved on 2026-08-12** after the measuring instrument was corrected and the maintainer ruled on the loading mechanism; its entry below is the current text, not the original.

**1. The pre-spec ceiling was understated by 9,985 bytes — and chasing that down changed the phase's loading mechanism.** `commands/ship.md:224` instructs `Read skills/conventional-commits/SKILL.md` in prose. The pre-`e8f2a09` `scripts/measure-invocation.py` resolved `required_skills:` frontmatter only, so it reported `conditional_bytes: 0`; any `/ship` run reaching commit-message authoring already loaded 63,316 bytes, not 53,331. **Resolution, in two parts:**

  *(a) The instrument was fixed* (`e8f2a09`). It now reports `floor = base + command + eagerly-declared skills` and `ceiling = floor + inline-read skills`, printing **floor 53,331 / cond 9,985 / ceiling 63,316** — exactly the adjusted baseline this spec computed by hand. Every bar in this package is re-set against 63,316.

  *(b) The maintainer ruled the mechanism (2026-08-12).* `required_skills:` is an eager pre-load — `system-instructions.md` ("before any phase work begins") and `adapters/claude-code.md:396` both say so — and declaring the five skills would have raised the **floor** from 53,331 to ~57,200. `ship.md:224` was already doing the right thing: an inline `Read` at the step that needs it, which a run pausing on a merge conflict never issues. `required_skills:` is **not used**; all four new skills are reached by inline reads at their phase anchors. See `spec.md` → *Approved scope change*; the locked contract block is unedited and the extraction plan is unchanged.

  The consequences invert two earlier decisions. Business Rule 1's escalation ladder is **withdrawn** — there is no phantom ceiling rise to justify, because `conventional-commits` is an inline read on both sides, and the projection now *clears* 63,316 by ~5,800 bytes. Business Rule 3's "declare all, not a subset" clause is **reversed** into a placement requirement: one read per skill at the narrowest step, no hoisting into the frontmatter, `## Overview`, or the phase-list table.

**1a. Every `/ship` path gets cheaper, which is not true of the sibling `/release` spec.** Projected against the correct pre-spec figure per path: conflict pause at Step 2 **−26.9%**, `--test` abort **−26.9%**, `--no-split` **−22.6%**, PR-open with `writ.auditNotes=false` **−11.1%**, full run **−9.2%**; floor **−31.4%**. The difference is structural rather than lucky — `/ship` has real early exits, `/release` reaches every phase on a normal run. Business Rule 1 requires the path table to be measured rather than projected, and requires the pre-spec column to use 53,331 for paths that never reached `ship.md:224` and 63,316 for paths that did.

**2. `commands/ship.md:226` argues against this spec.** A Phase 7 non-extraction note states that "No further skill extraction from `/ship` was warranted." ADR-021 reverses it on a criterion Phase 7 did not have — per-invocation load, unmeasurable before `measure-invocation.py` existed. Story 4 supersedes the note **in place**, with the reversal's evidence recorded. Deleting it would leave the next reader to re-derive the same question and reach the same stale answer. The evidence is now stronger than at authoring time: the reversal is backed by a measured 9–27% per-invocation reduction depending on path, not by a projected regression needing maintainer acceptance.

**3. `scripts/eval-git-notes-audit.py` pins seven literal strings to `commands/ship.md`.** `scenario_ship()` asserts them against the file, not against behavior. This is the mechanical guard for the spec's hardest constraint: an over-eager thinning of Step 6 fails `bash scripts/eval.sh` rather than shipping quietly. Story 3 and Story 4 both run it.

**4. The phase has already blown `MAX_SKILLS` and nobody owns the raise.** `scripts/eval-leanness.py:71` caps the corpus at 12; it holds 6 today. The five authored sibling rosters plus this one name **at least 29** — `implement-story` +8, `create-spec` +4, `implement-phase` +3, `release` +4, this spec +4, before `verify-spec` names its own. ADR-021 predicted the overrun and required a deliberate, justified raise. No disclosure spec may make it: this one is barred by Business Rule 9 and the dependency's own BR7 bars edits to `eval-leanness.py`. Assign it — plausibly to `2026-08-12-governor-enforcement` — before the second disclosure spec lands. This spec's four names were checked against all five sibling rosters on 2026-08-12 with no collision; Business Rule 10 requires re-checking at authoring time, because the namespace is shared and moving.

**Contract erratum, recorded not corrected:** the locked contract cites spec `2026-08-18-git-notes-audit-channel`. The real slug is `2026-07-18-git-notes-audit-channel` (`.writ/specs/archive/`). The contract block is reproduced verbatim in `spec.md`; every other reference uses the real slug.

## Anti-Goal (applies to every story)

The failure mode is **a file that is smaller and a framework that is not thinner.** `commands/ship.md` needs to shed only 3,411 bytes to clear its budget — deleting the ASCII pipeline diagram (1,445 B) and the duplicated `## Dry Run Mode` block (1,138 B) plus routine trimming gets there with **zero extraction**. That outcome passes every byte check in this spec and falsifies its contract.

Two defenses, and both are review actions rather than lint rules: the **clause ledger**, where a disposition column of all-`retained` is self-evident proof that nothing moved, and the **≤ 13,000-byte design target**, which no amount of trimming reaches without extraction.

The mechanism ruling adds a third shape of this failure: **a hoisted `Read` is `required_skills:` written in prose.** Four reads collected in the frontmatter, in `## Overview`, or in the phase-list table produce a smaller file, an unchanged floor, and a report that looks identical to a correct one. Business Rule 3's placement requirement and Testing Strategy check 4b are the only things that catch it. `audit-digest-composition`'s anchor is the most delicate case: placed above the `writ.auditNotes` opt-out gate instead of below it, an opted-out run pays for a skill it never uses and one of the five path rows quietly stops being true.

The last failure mode is the mirror of thinness: thinning so hard that a gate-crossing decision or the provenance write ends up in a file the harness may not have loaded — which under an inline `Read` is now the ordinary case rather than a hypothetical. `bash scripts/eval.sh` catches the provenance half. Nothing catches the gate half automatically — Business Rule 4's load test is the only check, and it has to actually be applied per clause. This is the spec whose numbers come out well on every path, which makes it the one where those per-clause checks are most likely to be waved through.

# Story 6: Dogfood the Sweep Against This Repo

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer
**I want to** run the real `/status --archive` sweep against this repo's 39 production spec folders and capture verifiable evidence that at least one eligible spec moves correctly
**So that** Success Criteria 2 and 3 are proven against real data — not fixtures — confirming the archive mechanism works end-to-end and leaves the command suite unbroken

## Acceptance Criteria

- [x] Given Story 2's archive sweep mechanism is merged and functional, when `/status --archive` (or its direct `scripts/archive-sweep.py` equivalent) runs against this repo's real `.writ/specs/` corpus, then at least one genuinely Complete spec with matching `.writ/knowledge/` evidence is moved via `git mv` to `.writ/specs/archive/<name>/`, and the terminal summary reports a non-zero archived count with a named skip count for Complete specs lacking knowledge evidence.
- [x] Given a spec is archived during the dogfood run, when `.writ/specs/archive/LEDGER.md` is inspected, then one append-only line exists recording the spec folder name, the knowledge entry filename(s) that supplied eligibility evidence, and an ISO 8601 timestamp — and the cited knowledge entry's `related_artifacts` frontmatter genuinely references that spec's folder name (no false-positive match).
- [x] Given at least one spec now lives under `.writ/specs/archive/<name>/`, when spot-checking the moved folder, then (a) all files remain fully readable at the new path, (b) `git log --follow -- .writ/specs/archive/<name>/spec.md` surfaces the spec's full pre-move history, and (c) any existing issue `spec_ref` or ADR `Amends:`/`Extends:` pointer that references the archived spec still makes sense to a human reader even though the literal path text was not rewritten (Business Rule 4 — confirm no confusing dead ends, not that rewriting occurred).
- [x] Given `.writ/specs/archive/` is now populated after the sweep, when `/status`, `create-spec`'s Step 1.3b overlap check, `implement-spec`'s spec-selection listing, and `verify-spec` (default and `--all`) each run, then all behave correctly with no regression — archived specs are excluded from active scans via single-level glob nesting alone, and no command errors or misclassification from the archive folder's presence.
- [x] Given the dogfood run completes, when this story's `## What Was Built` section is filled in, then it records which spec(s) were archived, why each was eligible (status + knowledge evidence), and the results of all four verification spot-checks — serving as the spec's concrete acceptance evidence for Success Criteria 2 and 3.

## Implementation Tasks

- [x] 6.1 **Pre-flight inventory (before running the sweep):** With Story 1's detector active, enumerate all 39 real `.writ/specs/*/spec.md` files and cross-reference against `.writ/knowledge/{decisions,conventions,glossary,lessons}/*.md` `related_artifacts` to predict which specs are archive-eligible; document the predicted set and manually verify at least one predicted match is genuinely Complete + knowledge-cited (guards against false-positive folder-name substring matches before irreversible `git mv`).
- [x] 6.2 **Run the real sweep:** Execute `/status --archive` (or `python3 scripts/archive-sweep.py` if that is the documented invocation path) against this repo — not a temp fixture — and capture terminal output (archived count, skipped count, any per-spec failures or collisions).
- [x] 6.3 **Verify archive artifacts:** Confirm each archived spec exists at `.writ/specs/archive/<name>/` with unchanged internal content; inspect `.writ/specs/archive/LEDGER.md` for correct one-line-per-move entries naming the citing knowledge file(s); confirm `git status` shows the moves as renames, not delete+add pairs.
- [x] 6.4 **Spot-check history and inbound references:** For each archived spec, run `git log --follow` on its `spec.md`; grep issues and ADRs for pointers to the old path and confirm a human reader can still resolve intent (path text unchanged per Business Rule 4 — document any pointer that reads confusingly as a finding, not a fix request).
- [x] 6.5 **Write a post-sweep regression assertion script** (e.g. `scripts/tests/test_archive_dogfood.py` or an `eval.sh` scenario): assert `/status` active-spec detection excludes `archive/`, `create-spec` overlap scan excludes archived specs, `implement-spec` listing excludes them, and `verify-spec --all` does not visit `archive/` — all against this repo's real post-sweep tree; run and capture pass/fail output.
- [x] 6.6 **Manual command smoke tests:** Run `/status` (no flag), skim `create-spec`'s overlap-check behavior against the current corpus, and confirm `implement-spec` and `verify-spec` spec enumeration still function — note any unexpected surfacing of archived specs as active candidates.
- [x] 6.7 **Record acceptance evidence:** Populate this story's `## What Was Built` section with archived spec name(s), eligibility rationale (status header + knowledge entry cross-reference), ledger excerpt, spot-check outcomes (readability, `git log --follow`, pointer sanity, command-suite regression results), and any deviations or skipped specs — this section is the spec's own proof artifact for Success Criteria 2 and 3.

## Notes

**This is not a fixture test.** The entire point is running the shipped mechanism against this repo's real 39 spec folders (~27 Complete once Story 1 lands) and 12 `.writ/knowledge/` entries. Unit tests in Story 2 validate the reducer; this story validates production reality.

**Depends on Story 2 being fully functional.** Do not run the dogfood sweep until `scripts/archive-sweep.py`, `commands/status.md --archive`, and Story 2's tests pass. Story 1 must also be merged — eligibility requires correct Complete classification.

**False-positive risk on knowledge matching.** The folder-name substring heuristic (`spec.md` → `## Technical Concerns`) can theoretically match unrelated artifacts sharing a slug fragment. Before treating the run as successful, manually confirm the ledger-cited knowledge entry's `related_artifacts` genuinely references the archived spec — not a coincidental substring hit.

**Business Rule 4 is a sanity check, not a fix.** Issue `spec_ref` and ADR `Amends:`/`Extends:` pointers are intentionally not rewritten. The spot-check confirms humans can still understand references; it does not require building pointer-rewrite logic.

**Partial sweep is acceptable.** If some eligible specs fail `git mv` (dirty tree, collision), the sweep continues per Story 2's error handling — document failures in What Was Built; success requires at least one real archive, not a perfect sweep of every eligible spec.

**This repo does not run `install.sh` on itself.** Story 4's `.cursorindexingignore` seeding may not yet exist in this repo's root — that is out of scope for this story's verification (Story 4 owns install scaffolding; this story owns sweep + command-suite regression).

**Risks:**

- Running against real data moves real git-tracked folders — ensure working tree is clean enough and changes are intentional before committing.
- Archiving a spec still referenced as "active" in a maintainer's mental model could cause brief confusion — mitigated by ledger audit trail and reversibility via `git mv` back.
- If zero specs are eligible (no knowledge cross-references yet), the story cannot satisfy Success Criterion 2 — pre-flight inventory (Task 6.1) surfaces this blocker early; may require adding or confirming a knowledge entry cites a Complete spec before proceeding.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

---

## What Was Built

**Implementation Date:** 2026-08-04

### Pre-Flight Inventory (Task 6.1)

`python3 scripts/archive-sweep.py scan --specs-dir .writ/specs --knowledge-dir .writ/knowledge` against the real 40-spec corpus reported **3 eligible specs** out of 40 (37 Complete-family via Story 1's detector; 1 not-complete — this very spec, still in progress at scan time):

| Spec | Complete? | Knowledge evidence |
|---|---|---|
| `2026-03-27-context-engine` | Yes | `lessons/2026-04-24-story-overlap-needs-boundaries.md` |
| `2026-04-24-phase4-production-grade-substrate` | Yes | 7 entries: `decisions/2026-04-24-adapter-neutrality.md`, `decisions/2026-04-24-markdown-as-instructions.md`, `conventions/2026-04-24-date-prefixed-slugs.md`, `conventions/2026-04-24-self-dogfooding-symlinks.md`, `glossary/context-hint.md`, `glossary/dual-use-test.md`, `lessons/2026-04-24-story-overlap-needs-boundaries.md` |
| `2026-07-18-artifact-integrity-handshake` | Yes | `lessons/2026-07-19-artifact-map-belongs-in-context-md-not-index-md.md` |

This matches (and adds one) to the README's own "Known Real-World Validation Candidates" predictions for `phase4-production-grade-substrate` and `artifact-integrity-handshake` — `context-engine` was a third genuine match found by the real scan.

**False-positive guard (per the story's own risk note):** before running the sweep, manually read each citing knowledge entry's `related_artifacts` frontmatter directly. All three genuinely name the archived spec's exact folder as a path component (e.g. `.writ/specs/2026-03-27-context-engine/drift-log.md`, `.writ/specs/2026-04-24-phase4-production-grade-substrate/spec.md`, `.writ/specs/2026-07-18-artifact-integrity-handshake/spec.md`) — not a coincidental slug-fragment substring hit.

### The Real Sweep (Task 6.2)

`python3 scripts/archive-sweep.py sweep --specs-dir .writ/specs --knowledge-dir .writ/knowledge --repo-root .` against the live repo (clean working tree beforehand):

```
3 specs archived, 36 Complete specs skipped (no knowledge evidence yet)
```

All 3 predicted specs archived. **Zero collisions, zero `git mv` failures.** Committed as `4081a09` — `chore(spec-lifecycle): archive 3 complete, knowledge-cited specs (Story 6 dogfood)`.

### Archive Artifact Verification (Task 6.3)

- `git status --short` after the sweep showed **all 50 moved files as `R` (rename)**, zero delete+add pairs; the only untracked entry was the newly created `LEDGER.md`.
- The commit itself (`git show --stat`) confirms `rename ... (100%)` for every file — full content preserved, zero diff on the renamed blobs.
- `.writ/specs/archive/LEDGER.md` — created fresh, exactly 3 append-only lines, one per archived spec, each naming the citing knowledge file(s) and an ISO 8601 timestamp:
  ```
  - 2026-08-04T16:05:52Z — `2026-03-27-context-engine` archived (evidence: `lessons/2026-04-24-story-overlap-needs-boundaries.md`)
  - 2026-08-04T16:05:52Z — `2026-04-24-phase4-production-grade-substrate` archived (evidence: `decisions/2026-04-24-adapter-neutrality.md`, `decisions/2026-04-24-markdown-as-instructions.md`, `conventions/2026-04-24-date-prefixed-slugs.md`, `conventions/2026-04-24-self-dogfooding-symlinks.md`, `glossary/context-hint.md`, `glossary/dual-use-test.md`, `lessons/2026-04-24-story-overlap-needs-boundaries.md`)
  - 2026-08-04T16:05:52Z — `2026-07-18-artifact-integrity-handshake` archived (evidence: `lessons/2026-07-19-artifact-map-belongs-in-context-md-not-index-md.md`)
  ```
- Re-running `sweep` immediately after committing reports `0 specs archived` — idempotent, no duplicate ledger lines, clean `git status`.

### History and Inbound-Reference Spot-Check (Task 6.4)

`git log --follow --oneline -- .writ/specs/archive/<name>/spec.md` for all three surfaces full pre-move history (2–3 commits each, oldest being the original spec-creation commit) — confirmed each resolves through the rename with no truncation.

Inbound references found via repo-wide grep for the three folder names:
- **Three issue `spec_ref` pointers** (`2026-04-26-story-5-remote-ci-gate-organic-validation.md`, `2026-04-26-story-1-knowledge-loading-organic-validation.md`, `2026-04-24-trim-context-engine-spec-lite.md`) still literally name `.writ/specs/2026-...-.../spec.md` (old path, not rewritten — as designed). Read each in full: every one remains unambiguous to a human reader — the issue names the spec by its dated folder slug in prose, and the intent ("Phase 4's Story 5 eval gate," "Context Engine's spec-lite trim") is clear independent of whether the literal path still resolves. **No confusing dead ends found** (Business Rule 4 satisfied).
- **Zero ADR `Amends:`/`Extends:` pointers** reference any of the three archived specs (checked `.writ/decision-records/*.md` directly) — no reverse-pointer concern here.
- The knowledge `related_artifacts` citations that *supplied* the eligibility evidence itself also still name the old path text — same "not rewritten, still human-legible" outcome, and functionally irrelevant to future re-detection since the eligibility scan matches by folder-name substring, not exact path resolution.

### Post-Sweep Regression Guard (Task 6.5) — and a real finding

Wrote `scripts/eval-archive-dogfood.py` (15 scenarios) — deliberately run against **this repo's real tree**, not a fixture, registered in `eval.sh` as `archive-dogfood`. Confirms: all 3 archived specs readable at the new path; ledger has exactly one citation line per spec; `spec-status.py scan` and `archive-sweep.py scan` both now fully exclude the 3 archived specs from the active 37-spec corpus; `verify-spec.md`'s documented glob shape (`*/spec.md`) excludes them on the real tree; the dogfood commit is recorded as renames, not delete+add.

**Real finding, not just a fixture edge case:** while verifying `implement-spec.md`'s spec-selection listing (AC 4 explicitly names it), the documented Step 1.1 prose — "list of specs found in `.writ/specs/`" — did **not** qualify "contains `spec.md`," unlike `status.md` and `verify-spec.md`, which both already had that qualifier from Stories 1 and 3. A naive folder listing against this repo's *now-real* `.writ/specs/archive/` subfolder could have surfaced `archive` itself as a bogus selectable "spec" in the `AskQuestion` options. This is exactly the class of regression Story 6 exists to catch — a real audit gap that only became observable once `archive/` genuinely existed as a sibling folder, not a hypothetical. **Fixed:** `commands/implement-spec.md` Step 1.1 now requires the same single-level "`.writ/specs/*/` folders that contain `spec.md`" shape, cross-linked to `.writ/docs/spec-lifecycle.md`. Added a static `eval.sh` assertion (`archive-dogfood` check) guarding against regression.

### Manual Command Smoke Tests (Task 6.6)

- `spec-status.py scan --specs-dir .writ/specs` → 37 active specs, `archive` folder itself absent from results, none of the 3 archived spec IDs present.
- Direct glob probe (`Path(".writ/specs").glob("*/")`) → `archive` appears as a plain sibling folder (38 top-level entries), but `Path(".writ/specs").glob("*/spec.md")` → 37 matches, correctly excluding all 3 archived specs and the bare `archive/` folder (which has no direct `spec.md` of its own).
- `create-spec.md` Step 1.3b delegates to `spec-status.py`'s same scan — already covered by the above; no separate regression found.
- `implement-spec.md` — see the real finding and fix above.
- `verify-spec.md` — glob shape confirmed against the real tree (see Task 6.5); no code change needed there (Story 3 already covered it), only the newly-populated `archive/` folder made the exclusion observable for the first time with real data.

### Deviations from Spec

**One in-scope fix beyond pure verification:** `commands/implement-spec.md` Step 1.1 was edited (not just documented as a finding) because Success Criterion / AC 4 explicitly requires `implement-spec`'s listing to "behave correctly with no regression" — a locked acceptance bar, not merely a "note it" instruction. This mirrors exactly how Story 3 handled the equivalent audit for `verify-spec.md`: minimal, single-purpose prose fix plus a regression guard, no broader rewrite.

No specs were skipped that should have been archived — the pre-flight prediction (3 eligible) matched the actual sweep result (3 archived) exactly. No partial-sweep failures occurred (this repo's working tree was clean and no destination collisions existed), so the "partial sweep is acceptable" contingency in this story's Notes was not needed.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration (the `implement-spec.md` gap was self-caught during Task 6.6's smoke test, not a separate review-cycle rejection)
- **Drift:** None — scope stayed within "run the real sweep + verify + regression-guard," with the one implement-spec.md fix justified directly by a locked AC
- **Security:** N/A — no new external input surface; the sweep only moves files already tracked in this repo's own git history

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** [Happy path — real spec archived] — `spec.md` → `## Success Criteria` (items 2 and 3)
- **Business rules:** [Eligibility = Complete status AND cited by knowledge evidence, Every move is a plain reversible git mv, Archived specs stay fully addressable]
- **Experience:** [Moment of Truth (real sweep, references still resolve)] — `spec.md` → `## 🎯 Experience Design` → `### Moment of Truth`

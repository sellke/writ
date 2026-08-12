# Drift Log

> Spec: .writ/specs/2026-08-12-refactor-dirty-tree-guard/
> Created: 2026-08-12
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Porcelain Guard Before Baseline Verification — Drift Report

> Run: 2026-08-12
> Overall Drift: Small

### Deviations

#### [DEV-001] Guard implemented as a distinct numbered step rather than inline prose ahead of Step 1.2
- **Severity:** Small
- **Spec said:** Task 1.2 — "Insert the guard ahead of Step 1.2 Baseline Verification in `commands/refactor.md`." Task 1.1 — reproduce `commands/revert.md:60-67`'s guard discipline, "not a new variant." No structural form was prescribed.
- **Implementation did:** The guard is its own heading, `#### Step 1.1b: Dirty-Tree Guard` (`commands/refactor.md:62`), sited between Step 1.1 and Step 1.2, and the direct-target jump at `commands/refactor.md:48` was retargeted from "proceed to Step 1.2" to "proceed to Step 1.1b."
- **Reason:** Review iteration 1 returned FAIL: the guard had been written as bold prose in the tail of Step 1.1's no-target branch while `:48` jumped over it straight to Step 1.2, leaving the guard unreachable on `/refactor <path>` — the first row of the Modes table and the most common invocation. Promoting it to a numbered step makes reachability structural rather than positional, and gives the eval a stable heading to pin. Spec intent is fully preserved.
- **Resolution:** Auto-amended
- **Spec amendment:** `spec-lite.md` "Implementation Approach" now reads "Guard is its own step (`Step 1.1b`) between Step 1.1 and Step 1.2 Baseline Verification in `commands/refactor.md`; every upstream jump instruction is retargeted at it." Recommended follow-up for the spec owner: mirror the same wording into `sub-specs/technical-spec.md`'s Edit surface row. `spec.md` unmodified.

#### [DEV-002] `scripts/` leanness ratchet warnings tripped by the eval.sh additions
- **Severity:** Small
- **Spec said:** Nothing about the leanness baseline; `.writ/leanness-baseline.json` is outside the story's edit surface.
- **Implementation did:** The 19-line `scripts/eval.sh` addition pushed `scripts.lines` to 32557 (justified ceiling 32538) and `scripts.chars` to 1409164 (ceiling 1407447), tripping two ratchet warnings. The overshoot equals the addition exactly.
- **Reason:** Structural, not a defect: the baseline records justified ceilings at the precise measurement of the last increment, so any `scripts/` addition trips it. These route through `add_note`, not `add_finding`, so the run stays `Findings: 0` and AC4 holds. `--update-baseline` was explicitly forbidden and was not run — it would have moved every surface's floor while recording no reason.
- **Resolution:** Flagged for review
- **Spec amendment:** N/A — flagged for post-implementation review. The spec/baseline owner should set `surfaces.scripts.justifications.lines` to 32557 and `.chars` to 1409164 with a dated reason naming this story.

---

#### [DEV-003] Story 2 amended at Gate 0 — 3 tasks to 5, ACs rewritten
- **Severity:** Small
- **Spec said:** Three tasks; ACs were "step 1 instructs capture+assert", "lint-skill.sh clean", "eval.sh Findings 0".
- **Implementation did:** Gate 0 ran the latter two against the *unmodified* file and both were already green — `lint-skill.sh` passes today and `grep -rn safe-refactor-loop scripts/` returned zero matches, so `eval.sh` never examined the file. The story had no mechanically verifiable criterion for its own deliverable. Amended to 5 tasks and 7 ACs, adding `require_literal` pins and tightening step 4's red branch so the captured SHA has a reader.
- **Resolution:** Auto-amended (story + spec-lite)
- **Spec-lite updated:** Yes

#### [DEV-004] Two pins were weaker than they looked; hardened after Gate 3
- **Severity:** Small
- **Spec said:** AC4 — pins assert the assertion and revert target, not merely the topic.
- **Implementation did:** Gate 3 proved `revert target` is positionally blind (it occurs twice, so `grep -Fq` cannot tell step 1's declaration from step 4's consumption) and that the assertion's *consequence* was unpinned — both mutations passed with `Findings: 0`. Two further pins added on the consuming sentence and on "stop and report what is uncommitted"; all six now bite under mutation.
- **Resolution:** Auto-amended
- **Spec-lite updated:** No — pin detail is implementation, not contract

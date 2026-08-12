# Story 5: Budget Measurement and No-Drift Certification

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 4

## User Story

**As a** maintainer deciding whether progressive disclosure actually worked on `/release`
**I want to** one story that measures both floor and ceiling, accounts for every extracted range, and re-asserts every pinned behavior
**So that** the phase's success criterion is a number somebody produced rather than a claim somebody made

## Scope

No product file changes. This story measures, compares, and certifies — and it is the story authorized to **halt** if Business Rule 1's ceiling threshold is crossed.

Five deliverables, all recorded in the story's evidence:

1. **The budget report** — `command_bytes`, `floor_bytes`, `conditional_bytes`, `ceiling_bytes`, `eager_bytes`, before and after, from the **fixed** `measure-invocation.py` (`e8f2a09`). Pre-spec is floor 53,549 / cond 9,985 / ceiling **63,534**; the 53,549 ceiling in older drafts came from the broken tool.
2. **The path table** — floor, worst-path ceiling, and each realistic partial path (abort before Step 1.2, gate-blocked, `--no-tag`/`bump_only`, full release), each with the skills that path reads and its per-skill byte attribution. This is what proves the mechanism works, and it is what shows honestly that the full-release path barely moves.
3. **The ceiling justification** — required if `ceiling_bytes` exceeds **63,534**.
4. **The drift ledger** — all fifteen extraction-map ranges, assembled from Stories 1–4.
5. **The regression report** — full `scripts/eval.sh` against its pre-spec baseline, plus the pin inventory, the gate-vocabulary sweep, and the placement checks (6 and 6b in the technical spec's Testing Strategy).

## Acceptance Criteria

- [ ] Given Business Rule 1, when the budget report is read, then it states `floor_bytes` **and** `ceiling_bytes` both before (53,549 / **63,534**) and after — a report carrying only the floor, or only a favourable path, is a failed story.
- [ ] Given the binding budget, when the report is read, then `command_bytes` ≤ **24,960** and `floor_bytes` < 53,549, each quoted directly from `measure-invocation.py` output rather than recomputed by hand, alongside `eager_bytes: 0` and an empty `warnings` array.
- [ ] Given Business Rule 1's path requirement, when the report is read, then it carries a measured row for each of: abort in Phase 1 before Step 1.2, gate blocks at Step 1.3, `--no-tag`/`bump_only`, and a full release — each as `floor + Σ(skills that path reads)` with the skill list shown, and each compared against the *correct* pre-spec number for that path (53,549 for paths that never reached `release.md:88`, 63,534 for paths that did). **If the full-release saving is within noise of zero — the projection says ~123 bytes — the report says so in those words.**
- [ ] Given Business Rule 1, when `ceiling_bytes` exceeds **63,534**, then the evidence carries the three-part justification: (a) the measured overage in bytes, (b) every Compression Ledger candidate with its **measured** yield — not the estimate — and (c) an explicit maintainer decision to accept the remainder. *"Only 4% worse"* fails this criterion, and so does *"but the `--no-tag` path is fine"* — a cheaper path explains an overage, it does not retire one. The projection says an overage of ~2,631 B is likely and that it is smaller than `npm-package-publication` itself, so the justification's first move is to report the worst *release* path (excluding npm, projected ~63,411) beside it.
- [ ] Given `skills/conventional-commits/SKILL.md` (9,985 B) is an inline read from the command in **both** the before and after states, when the report is read, then it is stated as counted symmetrically on both sides by the corrected instrument — and the excluded pair is reported too (pre-spec 53,549 vs post-spec ≈56,180), so the symmetry is visible rather than asserted. It is not declared, not re-extracted, and not moved into a skill.
- [ ] Given Business Rule 3 makes placement the mechanism, when the report is read, then it records the result of Testing Strategy checks 6 and 6b: each of the six skills inline-read at a step, each named in the phase list, no `Read skills/` string in the frontmatter, `## Overview`, or the phase-list table, `eager_bytes: 0`, `unresolved_skills: []`, and no "loads both ways" warning.
- [ ] Given `measure-invocation.py`'s own contract, when token figures are quoted at all, then they are quoted with `token_method` and `token_method_validated` attached — no `chars/4` estimate is reported as a measurement.
- [ ] Given Business Rule 2, when the drift ledger is read, then it has exactly fifteen rows (E1–E13), each with `source range → destination → bytes out → bytes in → semantic delta`, and every `semantic delta` is `none (verbatim)` or `contracted: <reason>`. Any other value fails the story.
- [ ] Given Business Rule 6, when `bash scripts/eval.sh` runs in full, then it produces no new findings relative to the recorded pre-spec baseline, and the pin-verification script prints `PINS OK`.
- [ ] Given Business Rule 4, when every `skills/*/SKILL.md` this spec created is grepped for `--skip-gate`, `AskQuestion`, `Proceed with this release`, `Block release`, and `Cancel release`, then there are no matches, and each of those appears in `commands/release.md`.
- [ ] Given Business Rule 5, when `scripts/eval.sh --check=post-merge-archival` runs, then it passes, and `python3 scripts/eval-post-merge-dogfood.py` still reports its pre-spec count (0 of 2) rather than erroring — the hook's literal commit pattern is unchanged.
- [ ] Given Business Rule 9 and `scripts/lint-skill.sh:52`, when `grep -n 'Read skills/' skills/*/SKILL.md` runs, then it returns nothing — no skill created by this spec chains to another, in prose or inside a code fence — and every one of the command's six inline reads is in `commands/release.md`.
- [ ] Given Business Rule 9, when `bash scripts/lint-skill.sh skills/*/SKILL.md` runs across the whole directory, then it exits 0 — including the six pre-existing skills, so a regression in the shared namespace is caught here.
- [ ] Given the shared namespace, when `ls skills/ | wc -l` is compared against `MAX_SKILLS = 12`, then the count is recorded as a finding for `2026-08-12-governor-enforcement` — the cap is already crossed by the pilot spec before this one runs, and it is not fixed by editing `eval-leanness.py`.
- [ ] Given the `skills` surface grows, when `.writ/leanness-baseline.json` is read, then it carries a bound justification for this spec naming the bytes moved out of `commands` and the corresponding reduction, and `--update-baseline` was not run.

## Implementation Tasks

- [ ] 5.1 Re-run the pre-spec baseline from the recorded base SHA: `git stash` or a worktree at `<base>`, `bash scripts/eval.sh` and `python3 scripts/measure-invocation.py --root . --command release`, and save both outputs — a baseline reconstructed from memory is not a baseline
- [ ] 5.2 Run `python3 scripts/measure-invocation.py --root . --command release --format table` and `--format json` on the post-spec tree; extract `command_bytes`, `command_lines`, `floor_bytes`, `conditional_bytes`, `ceiling_bytes`, `resolved_skills`, `unresolved_skills`, `base_share_of_floor`
- [ ] 5.3 Record the per-skill byte breakdown (`wc -c skills/*/SKILL.md` for the five created here, plus `conventional-commits` re-measured) so every path's total is attributable, then build the path table: floor, gate-blocked, `--no-tag`, full release, tool worst path
- [ ] 5.4 Collect every Compression Ledger candidate's **measured** yield from Stories 1–3; if the worst-path ceiling is still above 63,534, write the three-part justification and take it to the maintainer, leading with the worst *release* path (excluding `npm-package-publication`, which no run reaches). Named structural levers if needed: C6 — which also couples the README path, so record that cost — or dropping the `npm-package-publication` extraction (−~2,754 B worst-path ceiling, +~2,454 B floor). Neither is an implementer's call
- [ ] 5.4a Run the placement checks (technical-spec Testing Strategy 6 and 6b) and paste the output; confirm `required_skills:` appears nowhere in `commands/release.md`
- [ ] 5.5 Assemble the drift ledger from Stories 1–4's evidence into one fifteen-row table; spot-check at least five rows by re-running `git show <base>:commands/release.md | sed -n '<range>p'` against the destination
- [ ] 5.6 Run the pin-verification script and `bash scripts/eval.sh` in full; diff findings against the 5.1 baseline
- [ ] 5.7 Run the gate-vocabulary sweep across `skills/*/SKILL.md` and confirm each term's presence in `commands/release.md`
- [ ] 5.8 Run `bash scripts/lint-skill.sh skills/*/SKILL.md`, `bash scripts/gen-skill.sh --check`, `bash scripts/eval.sh --check=length`, `wc -l commands/release.md`, and `python3 scripts/spec-deps.py validate --specs-dir .writ/specs`
- [ ] 5.9 Append this spec's bound justification to `.writ/leanness-baseline.json` for the `skills` surface (never `--update-baseline`), touching nothing else in the file
- [ ] 5.10 Record the `MAX_SKILLS` count, the `sed -i` portability defect carried over by Story 2, and any other finding this spec surfaced but does not own

## Notes

**Technical considerations:**

- `measure-invocation.py` always exits 0 — it is a read-only measurement that never blocks its caller. So a passing exit code proves nothing here; the numbers have to be read.
- Its `warnings` array is the place `unresolved_skills` and the dual-load warning surface as prose. Read it. A typo'd skill name degrades gracefully by design (`system-instructions.md`: unknown names warn, never hard-fail), which is exactly the failure mode that would otherwise ship silently — and under the inline mechanism a typo means the step simply reads nothing.
- `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` should report `status: ok`, with this spec ordered after `2026-08-12-disclosure-implement-story` and before `2026-08-12-governor-enforcement`. Anything else means a sibling spec moved — investigate rather than editing this spec's dependency line.
- The pre-spec `eval.sh` baseline must come from the base SHA. `eval.sh` writes a timestamped report under `.writ/state/`, which is gitignored — capture the output, not the path.

**Risks / challenges:**

- The likeliest failure of this whole spec is a **−22.4% floor headline attached to a full-release path that moved 0.2%**. Both numbers are true; only one of them describes the run a maintainer performs. Business Rule 1's path table exists so the report cannot present the flattering half alone, and this story is the only place that can be enforced.
- The second likeliest is the mirror: reading the tool's `+4.1%` worst-path figure as a failure of disclosure, when ~2,754 B of it is a manual procedure no `/release` run reaches. Report both, with the arithmetic, and let the maintainer decide.
- Do not compare a post-spec path against the wrong pre-spec number. Runs that abort before Step 1.2 paid **53,549** pre-spec; runs that reached Step 1.2 paid **63,534**, because `release.md:88` sits inside Step 1.2. A single before-number applied to every row overstates the early rows and understates the late ones.
- A drift-ledger row reading `contracted: tightened wording` is not a justification. The `contracted:` value must say what was compressed and why the meaning is unchanged — that is the difference between a ledger and a checkbox.
- Certifying one's own work is weak evidence. Where a row's `semantic delta` is contested, re-derive it from `git show`, not from the implementing story's claim.

**Integration points:**

- ADR-021's review trigger (2026-11-11) asks whether measured per-invocation load dropped for at least 4 of the 6 targeted commands. This story's floor numbers are `/release`'s entry in that evidence.
- `2026-08-11-governor-instrumentation` will assert an absolute `per_surface.commands.chars` cap; the post-spec `command_bytes` here is one of its inputs.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Budget report carries floor **and** worst-path ceiling **and** the measured path table, before **and** after
- [ ] Ceiling ≤ 63,534, or the three-part justification written with measured yields and explicit maintainer acceptance
- [ ] Full-release path result stated plainly, including if it is ~0%
- [ ] Placement checks pass: no `required_skills:`, `eager_bytes: 0`, no hoisted or skill-resident `Read skills/`
- [ ] Fifteen-row drift ledger complete, with no `semantic delta` outside `none (verbatim)` / `contracted: <reason>`
- [ ] `bash scripts/eval.sh` shows no new findings vs. the base-SHA baseline
- [ ] Findings this spec does not own are recorded, not acted on

## Context for Agents

- **Business rules:** [BR1 ceiling regression + 15% halt, BR2 drift ledger, BR3 reachability, BR4 production boundary, BR5 archival hook, BR6 eval pins, BR9 lint, BR10 owned surfaces] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Why `npm-package-publication` is declared anyway; Skill authoring mechanics — the leanness bound justification] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [`/release` is a sequential pipeline; `MAX_SKILLS = 12` will be crossed; the archival hook has never fired in production] — from spec.md → ## Technical Concerns
- **Contract:** [Binding budget: ≤ 24,960 bytes, both floor and ceiling reported, a ceiling rise needs written justification] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Baseline Measurement; Ceiling arithmetic; Testing Strategy; Error & Rescue Map] — from sub-specs/technical-spec.md

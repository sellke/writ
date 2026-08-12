# Story 5: Verify the Budget and Prove No Behavioral Drift

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 4

## User Story

**As a** maintainer deciding whether progressive disclosure actually worked on this file
**I want to** an independent measurement of the whole path table — floor, always-taken, partials, worst — before and after, alongside an audit of the relocation ledger and every eval anchor
**So that** the claim "the command got smaller" is backed by the numbers that can go the wrong way, and a smaller file that quietly lost a rule cannot pass

## Acceptance Criteria

- [ ] Given ADR-021 caveat 2 warns that disclosure can raise total load, when this story lands, then `python3 scripts/measure-invocation.py --root . --command implement-phase` output is recorded **before and after** for `command_bytes`, `command_lines`, `eager_bytes`, `floor_bytes`, `conditional_bytes`, `ceiling_bytes`, `eager_skills`, and `conditional_skills` — reporting only the floor is an incomplete result, not a shorter one
- [ ] Given the binding budget, when this story lands, then `command_bytes` ≤ **24,960** (baseline 29,136) and `floor_bytes` < **49,136** (baseline 54,096), both stated as measured values with the percentage change
- [ ] Given Business Rule 1 as **replaced** by the 2026-08-12 ruling, when this story lands, then the **path table** is measured and recorded — floor, the always-taken path (floor + `phase-lane-execution`), each common partial path, and the worst path (= `ceiling_bytes`) — with every figure stated in bytes and as a percentage against the 54,096 monolith
- [ ] Given Business Rule 1's two capped figures, when this story lands, then `floor_bytes` < **49,136** and the **always-taken path is < 54,096**. A worst path above 54,096 is **not** a failure: it is recorded with its number and the **two independently rare conditions** required to reach it (unspecced features approved for decomposition, *and* a lane returning `challenge_required`). If reaching the worst path needs only one rare condition, placement is wrong and the story fails
- [ ] Given the phase's clearest win is a measurement rather than an argument, when this story lands, then the story states **the exact bytes a spec-resolving run never pays** — a `/implement-phase` invocation whose features all resolve to existing spec folders never enters the decomposition pre-pass and therefore never loads `phase-decomposition` at all. Report that number, and report what the same run would have paid under `required_skills:`, where those bytes sat in the floor on every invocation
- [ ] Given Business Rule 4 as reversed, when this story lands, then **placement** is verified and not merely presence: each of the three inline `Read skills/<name>/SKILL.md` calls is confirmed to sit inside the branch it serves, with none in the frontmatter, `## Overview`, or any always-executed step, and `grep -c 'required_skills' commands/implement-phase.md` returns **0**. `measure-invocation.py` books a hoisted `Read` as conditional either way, so the measurement cannot catch this and the reading must
- [ ] Given Business Rule 4, when this story lands, then `conditional_skills` lists all three, `eager_skills` is empty, `unresolved_skills` is empty, and `bash scripts/gen-skill.sh --check` reports no delta. Note that this is the **only** resolution check the repo has for an inline read — `eval-leanness.py`'s `check_required_skills()` resolves frontmatter declarations only, so nothing re-verifies these three after this story runs
- [ ] Given all 20 eval anchors must be in the command file itself, when this story lands, then the anchor loop from `sub-specs/technical-spec.md` is re-run and reports no missing literal, and the result is recorded verbatim
- [ ] Given Business Rule 2 as strengthened, when this story lands, then the four safety invariants are quoted in the story evidence **as they appear in `commands/implement-phase.md`**, with the skill-absence thought experiment answered explicitly: with all three skills absent, the command still forbids an unverified merge. Under inline `Read` this is not a hypothetical — two of the three loads are skipped on the majority path by design, the `Read` can fail mid-step with no harness warning, and no governor check resolves it. Record the convergence as evidence: the 20 blocking `eval.sh` anchors are almost exactly this safety machinery, drawn by an independent process
- [ ] Given Business Rule 5, when this story lands, then `python3 scripts/eval-loop-bounds.py` reports `drift-spec-attempt` PASS and a targeted diff confirms zero changed bytes inside the `loop:` block, including `on_exhaustion: halt_reported`
- [ ] Given Business Rule 3, when this story lands, then Story 4's relocation ledger is audited independently: all 321 pre-spec lines accounted for exactly once, no row reading "dropped", and each *compressed* row spot-checked against the pre-spec text via `git show <pre-edit-sha>:commands/implement-phase.md` — a minimum of eight rows checked, drawn from all three extraction ranges
- [ ] Given `bash scripts/eval.sh` is the acceptance gate, when this story lands, then it reports no new findings relative to the 2026-08-12 baseline (`--check=length` exit 0), and any new finding is classified as **caused by this spec's content** or **caused by `MAX_SKILLS = 12` being crossed by the six-spec programme** — both reported, neither suppressed (Business Rule 11)
- [ ] Given Business Rule 8, when this story lands, then `git diff --name-only` across the whole spec lists no path under `scripts/`, no `commands/*.md` other than `implement-phase.md`, and not `commands/_preamble.md`
- [ ] Given the phase's own dependency graph must stay valid, when this story lands, then `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok` and the resolved order still places `2026-08-12-disclosure-implement-story` before this spec and `2026-08-12-governor-enforcement` after it. A `missing_reference` is **never** resolved by deleting the dependency edge
- [ ] Given ADR-021's review trigger counts how many of six commands actually improved, when this story lands, then the evidence records this file's before/after floor and ceiling in a form the 2026-11-11 review can read directly, alongside the note that a 400-line cap would not have flagged this file at 321 lines

## Implementation Tasks

- [ ] 5.1 Re-measure: `python3 scripts/measure-invocation.py --root . --command implement-phase` and `--format table` for corpus context. Record the JSON verbatim. Recompute bytes-per-line and the file's new rank among the 31 commands
- [ ] 5.2 Compare against the recorded baseline (`command_bytes` 29,136 · `command_lines` 321 · `eager_bytes` 0 · `floor_bytes` 54,096 · `conditional_bytes` 0 · `ceiling_bytes` 54,096 · 90.77 B/line · rank 4 of 31 — re-measured post-`e8f2a09`, ceiling equals floor because the file has neither a declaration nor an inline read). State deltas as absolute bytes **and** percentages, for every row of the path table
- [ ] 5.3 Apply Business Rule 1: assert `floor_bytes` < 49,136 and the always-taken path < 54,096. If either fails, do not pass the story. For the worst path, state the number and name the two rare conditions; a worst path reachable via one condition is a placement defect, not a budget note
- [ ] 5.3b Verify placement by reading, not measuring: `grep -n 'Read skills/' commands/implement-phase.md`, then confirm each call sits inside the branch it serves. Record the three line numbers and their guards
- [ ] 5.3c State the `phase-decomposition` bytes a spec-resolving run never pays, and the counterfactual under `required_skills:` where the same bytes sat in the floor on every invocation
- [ ] 5.4 Re-run the 20-anchor grep loop; record the output
- [ ] 5.5 Quote the four safety invariants from the rewritten command file and answer the skill-failure thought experiment in writing
- [ ] 5.6 Run `python3 scripts/eval-loop-bounds.py`; diff the `loop:` block against `git show <pre-edit-sha>:commands/implement-phase.md`
- [ ] 5.7 Audit Story 4's relocation ledger. Spot-check at least eight *compressed* rows against the pre-spec text — at least two from each of the three extraction ranges. Any row whose compressed text drops a rule is a FAIL, not a note
- [ ] 5.8 Run `bash scripts/lint-skill.sh skills/*/SKILL.md` and `bash scripts/gen-skill.sh --check`
- [ ] 5.9 Run `bash scripts/eval.sh --check=length` and `bash scripts/eval.sh`; diff findings against the baseline report and classify each new one
- [ ] 5.10 Run `python3 scripts/spec-deps.py validate --specs-dir .writ/specs`; record `status` and the resolved order
- [ ] 5.11 Confirm ownership across the whole spec: `git diff --name-only <base>..HEAD`

## Notes

**Technical considerations:**

- **The measurement this story exists for is the always-taken path, not the floor and not the raw ceiling.** The floor falling is the easy half and is nearly guaranteed by the byte budget. Under the retired eager mechanism the ceiling was the decisive number because it was what every run paid. **Under the 2026-08-12 ruling that is no longer true** — the ceiling is a genuine worst path most runs never reach, and the number that stands in its place as "what a real invocation costs" is floor + `phase-lane-execution`, because that skill is on every path that executes a spec. Report the whole table; bind on floor and the always-taken path.
- **`measure-invocation.py` will flatter the floor if you let it.** It books every inline read under `conditional_bytes`, including `phase-lane-execution`'s, which is paid in practice on every real run. A report that pairs a 14.5% floor drop with an unqualified "the rest is conditional" is technically accurate and materially misleading. Task 5.2's path table is the fix.
- This story is a verification story with no product output. That does not make it optional: Story 4 measures its own work, and a self-certified budget is exactly the failure mode ADR-020's `exit_criteria` discipline exists to prevent.
- `MAX_SKILLS = 12` at `scripts/eval-leanness.py:71` against 6 incumbents + 3 here + five sibling specs' skills — a measured post-phase total of **35** (implement-story +8, create-spec +5, verify-spec +4, release +5, ship +4, here +3 = 29 new). ADR-021 already states the cap will be crossed and must be raised deliberately. **`2026-08-12-governor-enforcement` now owns the constant** (maintainer assignment, 2026-08-12), so this report has a receiver rather than being an open escalation. A finding here is expected programme behavior, not this spec's defect — and it is still reported.

**Risks / challenges:**

- **Passing the story on the floor alone.** The single most likely failure of this verification is a report that says "29,136 → 21,295, a 27% reduction" and stops. Acceptance criterion 1 and Task 5.2 exist to make that report incomplete by construction. The inline mechanism makes this *easier* to get wrong, not harder: the floor genuinely falls 14.5% and every other byte is nominally conditional, so the flattering report is also the natural one.
- **Verifying placement by grep count.** Three `Read skills/` hits is necessary and not sufficient. A call hoisted above its branch produces the same count, the same `conditional_bytes`, and a command that pays full price on every run. Task 5.3b requires reading each call's guard.
- **Auditing a ledger by reading it.** Task 5.7 requires spot-checks against the pre-spec text via the recorded blob SHA. A ledger read for internal consistency will always be consistent.
- **Treating an eval finding as noise.** Every new finding is classified. "Probably the skills cap" is not a classification; running `bash scripts/eval.sh --check=leanness` and reading the subject line is.
- **Deleting the dependency edge to make `spec-deps.py` quiet.** The graph validates `ok` today, but the six disclosure specs were authored concurrently and can still move. If a `missing_reference` ever appears, removing the edge would release this spec to run before the pattern it is required to follow exists (Business Rule 10). Fix the reference, never the edge.

**Integration points:**

- ADR-021's 2026-11-11 review trigger asks whether measured per-invocation load dropped for at least 4 of the 6 targeted commands. This story's evidence is one of those six data points and should be written so the reviewer can use it without re-deriving anything.
- The 2026-08-12 maintainer decision making the byte budget binding and the line cap a secondary tripwire cites this file as its evidence. The recorded 321-lines / 90.77-B-per-line / rank-4 figures are that citation.
- The governor-enforcement work will take `check_length`'s command limit 2000 → 400. This story's evidence is what tells that work the line cap alone is insufficient.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] The full path table reported before and after, in bytes and percent — floor, always-taken, partials, worst
- [ ] Business Rule 1 applied: floor < 49,136 and always-taken path < 54,096, both asserted; a worst path above 54,096 recorded with its two rare conditions named
- [ ] The bytes a spec-resolving run never pays for `phase-decomposition` stated, with the `required_skills:` counterfactual
- [ ] Inline `Read` placement verified by reading each call's guard; `grep -c required_skills` returns 0
- [ ] 20-anchor grep output recorded verbatim
- [ ] Four safety invariants quoted from the command file; skill-failure thought experiment answered
- [ ] Relocation ledger audited with ≥8 spot-checks across all three ranges
- [ ] `bash scripts/eval.sh` findings diffed against baseline and each new finding classified
- [ ] `git diff --name-only` across the spec confirms the ownership boundary

## Context for Agents

- **Business rules:** [BR1 path-dependent ceiling — floor and always-taken path bind, the rest are reported; BR2 safety invariants (strengthened); BR3 relocation ledger; BR4 precise placement (reversed); BR5 loop bounds; BR8 ownership; BR11 `MAX_SKILLS` reported not raised, now owned by governor-enforcement] — from spec.md → 📋 Business Rules
- **Mechanism ruling:** [the escalation was accepted; inline `Read` replaces `required_skills:`; what the ruling is worth per run] — from spec.md → ## Approved Scope Changes
- **Success criteria:** [all 11] — from spec.md → ## Success Criteria
- **Technical spec:** [Baseline Measurement; Verification; Error & Rescue Map] — from sub-specs/technical-spec.md
- **Technical concerns:** [`required_skills:` eager pre-load — RESOLVED, mechanism changed; `phase-lane-execution` is only nominally conditional; no governor check resolves an inline read; `required_skills_declarations` is now permanently 0; `MAX_SKILLS` will be crossed] — from spec.md → ## Technical Concerns

# Story 4: Author the Thin Contract in One Atomic Commit

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 1, 2, 3

## User Story

**As a** maintainer whose running `/implement-phase` orchestrator is reading the file this story rewrites
**I want to** replace `commands/implement-phase.md` with the thin contract in a single commit that places three inline `Read skills/<name>/SKILL.md` calls at their narrowest steps and re-states every safety invariant and eval anchor
**So that** the file is a complete, self-sufficient instruction set at every point in the repo's history, and no intermediate state exists in which the lane / merge / quarantine contract has left the command but not yet arrived anywhere

## Acceptance Criteria

- [ ] Given Business Rule 6 forbids an intermediate state, when this story lands, then the rewrite is **one commit** touching `commands/implement-phase.md`, and the pre-edit blob SHA is recorded in the story notes so an orchestrator can be re-seeded with `git show <sha>:commands/implement-phase.md`
- [ ] Given the binding budget is 24,960 bytes, when this story lands, then `python3 scripts/measure-invocation.py --root . --command implement-phase` reports `command_bytes` **≤ 24,960** (from 29,136) and `floor_bytes` **< 49,136** (from 54,096), with both figures recorded in the story notes. With no eager declaration, `floor_bytes` is exactly `base + command` — the bytes every invocation pays with no path around them
- [ ] Given all 20 eval anchors must survive in the command itself (spec.md → § Why This Exists), when this story lands, then the anchor grep in `sub-specs/technical-spec.md` reports no missing literal against `commands/implement-phase.md`, and `## Required Artifacts` is still present
- [ ] Given Business Rule 2, when this story lands, then `commands/implement-phase.md` states, in normative language and with no skill loaded: the lane branch and worktree are created before any work; only a verified `phase-spec-result-v1` merges; a terminal failure is quarantined as `writ/quarantine/{spec-id}`; and the phase branch is never touched by failed work — each quotable from the command file alone
- [ ] Given Business Rule 5, when this story lands, then `git diff` shows **zero changed bytes** inside the `loop:` block — both bounds, both `on_exhaustion` values including `halt_reported`, and both `calibrated_against:` strings intact — and the *Iteration bound* paragraph explaining why exhaustion does not quarantine is retained in the body
- [ ] Given Hard Constraint 1 requires the Question Policy's four conditions to survive byte-faithful in meaning, when this story lands, then all four are present in `commands/implement-phase.md`: missing exit criteria (never invent-and-self-certify), unachievable exit criteria discovered mid-run, ambiguous failure blast radius, and decomposition approval
- [ ] Given Business Rule 4 as **reversed** by the 2026-08-12 ruling, when this story lands, then `commands/implement-phase.md` contains exactly **three** inline `Read skills/<name>/SKILL.md` calls — one per skill from Stories 1–3 — each at the **narrowest step that needs it** per `sub-specs/technical-spec.md` → *Inline `Read` Placement*, **none** in the frontmatter, `## Overview`, or any always-executed step; `grep -c 'required_skills' commands/implement-phase.md` returns **0**; `measure-invocation.py` reports `eager_bytes: 0`, `eager_skills: []`, `conditional_skills` naming all three, and `unresolved_skills: []`
- [ ] Given ADR-021 §1 defines the retained shape, when this story lands, then the file carries the frontmatter contract, `## Overview`, the `## Invocation` table, a phase list with gate names, `## Completion`, and `## References` — plus `## Required Artifacts`, which two eval checks require and ADR-021's list omits (recorded, not corrected here)
- [ ] Given Business Rule 3's verification method, when this story lands, then a **relocation ledger** is recorded in the story notes with one row per removed line range of the pre-spec file, each naming its destination as *retained*, *`skills/<name>` § heading*, or *compressed* with the compressed text quoted — every one of the 321 pre-spec lines accounted for exactly once, and **no row reading "dropped"**
- [ ] Given the sections deliberately not extracted must survive intact, when this story lands, then `## Recommended Mode`, `## Integration with Writ`, the Phase Execution Plan template, and the Phase Report template are present and unchanged in meaning
- [ ] Given Business Rule 8, when this story lands, then `git diff --name-only` lists `commands/implement-phase.md` and nothing else — no `scripts/` path, no `commands/_preamble.md`, no other command file
- [ ] Given `bash scripts/eval.sh` is the acceptance gate for the whole rewrite, when this story lands, then it produces no new findings relative to the 2026-08-12 baseline, and `bash scripts/eval.sh --check=length` exits 0

## Implementation Tasks

- [ ] 4.1 Record the pre-edit state: `git rev-parse HEAD:commands/implement-phase.md`, and re-run `python3 scripts/measure-invocation.py --root . --command implement-phase` to confirm the 29,136 / 321 / 54,096 baseline still holds. If it does not, stop — a sibling spec has edited the file and the ownership assumption in Business Rule 8 is broken
- [ ] 4.2 Confirm all three skills exist, are lint-clean, are in `.writ/manifest.yaml`, and that the three-skill byte total is within the ≈7,841-byte budget. If Story 3 escalated an overrun, resolve it before writing — Story 4 cannot compensate for oversized skills by cutting the command further without breaching Business Rule 3
- [ ] 4.3 Author the **Lane & Failure Invariants** block per `sub-specs/technical-spec.md` → *The Retained Lane & Failure Invariants Block*: six required elements, ≈1,950 bytes, carrying `fresh subagent`, `writ/phase/{phase-id}/{spec-id}`, `phase-spec-result-v1`, `only a verified`, `scripts/phase-state.py`, `writ/quarantine/{spec-id}`, `one transient retry`, `skipped_blocked`, `does not guess or mutate git`, and the *Iteration bound* paragraph verbatim
- [ ] 4.4 Author the retained sole-presenter statement for User Challenges, carrying `User Challenge` and `ordinary failures use their normal`
- [ ] 4.5 Collapse Steps 1.1, 1.2, and 1.3 into the phase list with gate names, retaining the Specced/Unspecced classification and the three-option `AskQuestion`, and pointing at `phase-decomposition` for the pre-pass
- [ ] 4.6 Place the three inline `Read skills/<name>/SKILL.md` calls at their mapped steps (`sub-specs/technical-spec.md` → *Inline `Read` Placement*), each paired with a one-line command/skill boundary statement in the house style of `commands/implement-story.md:525`. **The frontmatter is not edited at all** — no `required_skills:` block, ADR-020 key order undisturbed, `loop:` untouched
- [ ] 4.7 Write the relocation ledger covering all 321 pre-spec lines. Build it *while* editing, not after — a ledger reconstructed from a finished diff records what happened, not what was intended, and cannot catch a dropped rule
- [ ] 4.8 Run the anchor grep from `sub-specs/technical-spec.md`; fix any miss by restoring the literal to the command, never by editing `scripts/eval.sh`
- [ ] 4.9 Measure: `python3 scripts/measure-invocation.py --root . --command implement-phase`. Record `command_bytes`, `command_lines`, `floor_bytes`, `conditional_bytes`, `ceiling_bytes`, `resolved_skills`, `unresolved_skills`
- [ ] 4.10 Run `python3 scripts/eval-loop-bounds.py` and confirm `drift-spec-attempt` PASS; run `bash scripts/eval.sh --check=length` and `bash scripts/eval.sh`, comparing against the recorded baseline
- [ ] 4.11 Commit once, with the pre-edit SHA in the commit body

## Notes

**Technical considerations:**

- **This story edits the file its own orchestrator is executing.** On the intended path, `/implement-phase` runs it inside `writ/phase/10/2026-08-12-disclosure-implement-phase` in a separate worktree, so the orchestrator's checkout is unchanged until the `--no-ff` merge — a property of the lane isolation this spec is rewriting. This spec is last in the phase, so no later iteration reads the rewritten file in the same run. If the story is instead run directly on the phase branch, the file being edited *is* the file being executed, and Task 4.11's single commit is the only thing that makes that survivable.
- The budget is met with roughly 3,600 bytes of headroom by the projection in `spec.md`. That headroom is deliberate: it is what absorbs the invariants block coming in over its 1,950-byte estimate. Spending it on further extraction is not an improvement — Business Rule 3 rewards a smaller, fully-accounted diff.
- **Placement is the mechanism, and the measurement will not catch a placement error.** `measure-invocation.py` books an inline `Read` under `conditional_bytes` wherever it sits, so a call hoisted above the branch it serves reads as conditional while costing full price on every run. Only reading the placement catches it. The two that matter: `phase-decomposition` goes *after* the branch establishing unspecced features exist and the user approved decomposing them — not in Step 1.2's classification, which runs every phase; `user-challenge-presentation` goes *inside* the `challenge_required` branch, not at the top of failure handling.
- **Nothing downstream will re-check that the three paths resolve.** `eval-leanness.py`'s `check_required_skills()` reads frontmatter only, so inline reads are invisible to the governor. `measure-invocation.py`'s `unresolved_skills` in Task 4.9 and Story 5's re-run are the only resolution checks that exist.
- Eight of the twenty anchors have their **only** occurrence inside a removed range. They are not stylistic phrases; each names a step of the safety machinery. Re-stating them is not a compliance chore, it is the substance of Task 4.3.
- `## Required Artifacts` stays even though ADR-021's permitted-section list omits it. Two eval checks blocking-require it. The gap in ADR-021 is recorded in `spec.md` → § Technical Concerns; amending the ADR is somebody else's decision.

**Risks / challenges:**

- **The ledger written after the fact.** Task 4.7 says build it while editing. A ledger reconstructed from the finished file will faithfully record whatever survived, including a rule that was quietly lost, and will read as a passing check.
- **Compressing a rule into an aspiration.** "Only a verified result merges" → "results are validated before merging" reads like an editing improvement and is a contract change. The anchor grep catches this one only because the literal happens to be pinned; the other invariants have no such protection, which is what the acceptance criterion's *quotable from the command alone* test is for.
- **Touching the frontmatter at all.** The pre-ruling plan inserted a `required_skills:` block next to `loop:`, which is why this risk was listed. Under the ruling there is no frontmatter edit — which removes the risk entirely, and makes any frontmatter diff in this story a defect. Verify with a targeted diff, not by eye.
- **Scope creep into the deferred sections.** `## Recommended Mode`, `## Integration with Writ`, and the two templates are legitimate future targets and are explicitly not this spec's. Extracting them "while we're in here" makes the ledger unverifiable and the budget claim unattributable.

**Integration points:**

- Stories 1–3 must all have landed; Business Rule 4 requires every declared skill to resolve.
- Story 5 re-measures independently and audits this story's ledger — the measurement is not self-certified here.
- `scripts/eval.sh`, `scripts/eval-loop-bounds.py`, `scripts/eval-leanness.py`, and `scripts/eval-artifact-integrity.py` all assert against this file and none may be edited.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `command_bytes` ≤ 24,960 and `floor_bytes` < 49,136, both recorded
- [ ] All 20 anchors present in `commands/implement-phase.md`
- [ ] `git diff` shows zero changed bytes inside `loop:`; `drift-spec-attempt` PASS
- [ ] Relocation ledger complete, all 321 pre-spec lines accounted once, no "dropped" row
- [ ] `bash scripts/eval.sh` shows no new findings vs. the 2026-08-12 baseline
- [ ] One commit; pre-edit blob SHA recorded
- [ ] `git diff --name-only` lists only `commands/implement-phase.md`

## Context for Agents

- **Business rules:** [BR2 safety invariants in the command (strengthened — an invariant that depends on a `Read` succeeding is not an invariant), BR3 relocate-not-redesign + relocation ledger, BR4 precise placement (reversed — no `required_skills:`), BR5 loop bounds and `halt_reported`, BR6 self-sufficient at every commit, BR8 ownership] — from spec.md → 📋 Business Rules
- **Mechanism ruling:** [inline `Read` at the narrowest step; frontmatter untouched; placement is the mechanism] — from spec.md → ## Approved Scope Changes; sub-specs/technical-spec.md → ## Inline `Read` Placement
- **Detailed requirements:** [What the thin contract retains; Projected arithmetic; The self-modification hazard] — from spec.md → ## Detailed Requirements
- **Technical spec:** [The 20 Blocking Anchors — Exact Locations; The Retained Lane & Failure Invariants Block; The `loop:` Block — Do Not Touch; Inline `Read` Placement] — from sub-specs/technical-spec.md
- **Contract:** ["The rewritten file must remain a complete, self-sufficient instruction set at every commit"] — from spec.md → ## Contract (Locked)

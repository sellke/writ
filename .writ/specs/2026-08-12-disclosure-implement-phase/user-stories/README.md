# User Stories: Progressive Disclosure — `implement-phase`

> **Status:** Not Started — 0/5 stories, 0/46 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Extract the Decomposition Pre-Pass to a Skill](./story-1-phase-decomposition-skill.md) | Not Started | 7 | 0/7 | None |
| 2 | [Extract the Lane / Merge / Quarantine Mechanics to a Skill](./story-2-phase-lane-execution-skill.md) | Not Started | 7 | 0/7 | Story 1 |
| 3 | [Extract the User Challenge Presentation Format to a Skill](./story-3-user-challenge-presentation-skill.md) | Not Started | 7 | 0/7 | Story 2 |
| 4 | [Author the Thin Contract in One Atomic Commit](./story-4-thin-contract-rewrite.md) | Not Started | 11 | 0/11 | Stories 1, 2, 3 |
| 5 | [Verify the Budget and Prove No Behavioral Drift](./story-5-budget-and-drift-verification.md) | Not Started | 13 | 0/13 | Story 4 |

## Dependency Graph

```
Story 1 (phase-decomposition skill)        — zero eval anchors in range, proves the pattern
   └── Story 2 (phase-lane-execution skill) — ten anchors in range, densest prose, the always-taken path
          └── Story 3 (user-challenge-presentation skill) — smallest, and the last input to the path table
                 └── Story 4 (the one atomic rewrite of commands/implement-phase.md)
                        └── Story 5 (independent measurement + ledger audit)
```

**The chain is fully serial, and that is deliberate.**

**Stories 1–3 touch zero bytes of `commands/implement-phase.md`.** Business Rule 6 forbids any intermediate state of that file, because the command executing this spec is reading it. Skills are authored first; the command flips in one commit.

**Stories 1–3 are serial rather than parallel.** All three append to `.writ/manifest.yaml` — a hand-edited YAML file where three concurrent worktree appends is a guaranteed conflict for no gain at this size. The second reason has weakened: they used to share **one cumulative hard byte budget** (the three skills capped at the bytes removed from the command, ≈7,841 B), which made parallel authoring a recipe for discovering an overrun in Story 5. **That cap was retired by the 2026-08-12 mechanism ruling** — skills are now authored to their source, and each story records its measured size so Story 5 can compute the path table rather than to prove it stayed under an allowance. The running-total handoff between the stories survives as *reporting*, not as a gate.

## The 2026-08-12 Mechanism Ruling — read before starting any story

**This spec's escalation was verified and accepted.** `required_skills:` is an eager pre-load with no conditional path, so extraction under it makes `/implement-phase` cost more than the monolith. All six disclosure specs switch to inline **`Read skills/<name>/SKILL.md` at the point of need**; `required_skills:` is not used and must not appear in this command's frontmatter.

Full record: spec.md → § Approved Scope Changes. What it changes for the stories:

- **Stories 1–3:** the hard skill-bytes cap is gone. Author to the source (≈3,600 / ≈4,400 / ≈1,500 B), record the measured size, do not compress to hit a number.
- **Story 4:** no frontmatter edit. Three inline `Read` calls, each at the **narrowest step that needs it** — placement is the mechanism, and a `Read` hoisted above its guard is an eager load in inline syntax.
- **Story 5:** measure the whole **path table**, not floor-and-ceiling. Floor and the always-taken path are the capped figures; the rest are reported.

The extraction plan, the 24,960-byte budget, the 20 anchors, the pinned literals, and Business Rule 3's no-redesign rule are all **unchanged**.

**Story 1 goes first because it is the only extraction with zero eval anchors in its source range.** Naming, the lint-clean capability rewrite, and the byte discipline all get proven on the clean case before the same techniques are applied to prose the eval suite pins in place.

**Story 4 is the only writer of `commands/implement-phase.md`, in a single commit.** It cannot start before all three skills exist: Business Rule 4 requires every inline `Read` to resolve to a real file, and `measure-invocation.py` reports an unresolved inline name as a warning that the figures are a lower bound. Note that under the inline mechanism this is the *only* check there is — `eval-leanness.py` resolves frontmatter declarations only and never sees an inline read.

**Story 5 is separate from Story 4 because a self-certified budget is not a measurement.** Story 4 measures its own work to know it is done; Story 5 measures it again independently and audits the relocation ledger against the pre-spec file, which is the only check that can catch a rule that was compressed into an aspiration.

## Task Count

46 tasks across 5 stories. Stories 1–3 carry 7 each — the work is the same shape at every size: read the source, reconcile the name, scaffold through `/new-skill`, rewrite as a capability, drop what stays behind, measure, confirm ownership. Story 4 carries 11, because the rewrite has ten distinct retained obligations. Story 5 carries 13: the 2026-08-12 mechanism ruling added two tasks that did not exist under the eager mechanism — verifying inline `Read` **placement** by reading each call's guard (the measurement cannot catch a hoisted call), and stating the bytes a spec-resolving run never pays.

## Quick Links

- [spec.md](../spec.md) — locked contract, the binding budget, the 20 eval anchors, business rules
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — baseline measurement, section byte ledger, exact anchor locations, the retained invariants block, verification commands, error & rescue map
- [ADR-021](../../../decision-records/adr-021-progressive-disclosure-token-budget.md) — governing decision
- [ADR-020](../../../decision-records/adr-020-component-contract.md) — the frontmatter contract the thin file retains

## The Constraint That Shapes Everything

**This spec is executed by the command it rewrites.** `/implement-phase` spawns the lane subagent that edits `commands/implement-phase.md` while the orchestrator runs from that same file. It is sequenced last among the six disclosure specs for exactly this reason.

On the intended path the lane subagent works in a separate worktree, so the orchestrator's checkout is unchanged until the `--no-ff` merge lands — a property of the very lane isolation this spec is rewriting, which is why Business Rule 2 keeps that machinery in the command. Run directly on the phase branch instead, and the file being edited *is* the file being executed. Business Rule 6's one-atomic-commit rule is what makes both paths survivable, and Story 4 records the pre-edit blob SHA so an orchestrator that loses its footing can be re-seeded from `git show <sha>:commands/implement-phase.md`.

## Contradictions Found at Spec Time — One Resolved, Two Recorded

All verified against the working tree on 2026-08-12.

**1. RESOLVED — `required_skills:` is an eager pre-load, and the mechanism was changed.** This spec escalated at contract time that the harness loads every named skill *"before any phase work begins"* (`system-instructions.md` § Harness contract; `adapters/claude-code.md:396`), so there is no conditional path and a naive extraction makes `/implement-phase` cost **more** than the monolith. **The maintainer verified it and accepted it on 2026-08-12.** All six disclosure specs now use inline `Read skills/<name>/SKILL.md`; `required_skills:` is not used. The escalation changed the phase's mechanism and was worth ≈5,100 bytes per run on the common path — it is left on the record rather than deleted, because *not deciding it in-flight* is what made the ruling possible.

**1b. NEW — nothing enforces an inline read.** `scripts/eval-leanness.py`'s `check_required_skills()` (`:682-724`) resolves the frontmatter field only, so a typo'd or unwritten inline path yields **zero** findings from the governor that `2026-08-12-governor-enforcement` is about to make blocking. `scripts/measure-invocation.py` catches it (`unresolved_skills` + a lower-bound warning) but always exits 0. Escalated to that spec, which owns `eval-leanness.py`; unfixable here under Business Rule 8.

**1c. NEW — `phase-lane-execution` is only nominally conditional.** Every run that executes a spec reaches it, so its bytes are booked under `conditional_bytes` while being paid in practice — which flatters the floor. Business Rule 1 answers by binding floor + that skill as a second capped figure. Recorded rather than fixed: leaving 5,225 B of lane narrative in the command breaks the budget, so the skill is right and the accounting is what needed the guard.

**2. ADR-021's permitted retained-section list omits `## Required Artifacts`, which two eval checks blocking-require.** `check_artifact_integrity` in `scripts/eval.sh` and `scripts/eval-artifact-integrity.py` both require the block in seven high-traffic commands including this one. A thin contract authored strictly to ADR-021 §1 fails the eval suite. The section stays; ADR-021 needs an amendment owned by whoever holds the ADR.

**3. Nineteen blocking `require_literal` assertions pin *prose* inside the file this spec rewrites, and the spec cannot edit the eval.** This is a real coupling defect — the eval suite asserts on phrasing rather than structure. Here it happens to point the right way, since the pinned phrases are mostly the safety invariants Business Rule 2 keeps in the command anyway. The inverse case is `topological` and `roadmap order` in Step 2.1, pinned for narrative reasons; Step 2.1 is not extracted by this spec, so it does not bite now. It will bite whoever extracts it later.

## Sibling State at Authoring Time (2026-08-12)

All six disclosure specs and `2026-08-12-governor-enforcement` were authored concurrently. `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok`, with `2026-08-12-disclosure-implement-story` ordered before this spec and `2026-08-12-governor-enforcement` after it. `bash scripts/eval.sh --check=length` exits 0.

Skill names claimed by the siblings were checked and the three proposed here collide with none of them. **That check is a snapshot, not a guarantee** — none of the sibling specs is implemented yet, so their names can still move. Business Rule 10 makes reconciliation the first task of Stories 1, 2, and 3 for exactly this reason.

Note also that the programme's six files are the **top six by floor load** — `implement-story`, `create-spec`, `verify-spec`, `implement-phase`, `release`, `ship`. `implement-spec` is not among them, so ADR-021 §4's "one shared skill, not two copies" question about lane mechanics has no live counterparty. It acquires one the day `implement-spec` is extracted, which is why Story 2 authors a general capability rather than this command's Step 3.2 in disguise.

## Anti-Goal (applies to every story)

The failure mode is **not** an over-budget command file. It is a command file that lands comfortably under 24,960 bytes, passes the anchor grep, passes `eval.sh`, and has quietly moved a safety invariant behind a file that is *routinely not loaded at all*.

**The 2026-08-12 ruling makes this sharper, not softer.** Under `required_skills:` a missing skill was a reachable accident (unknown names warn, never hard-fail). Under inline `Read`, non-load is **the design** — the whole reason the floor falls is that most runs never reach two of the three calls. Add that the `Read` can fail mid-step with no pre-flight resolution and no harness warning, and that **no governor check sees an inline read at all**, and the conclusion is Business Rule 2's: *an invariant that depends on a `Read` succeeding is not an invariant.*

The test, applied in Stories 2, 4, and 5: *with all three skills absent, can `commands/implement-phase.md` still be read as forbidding an unverified merge?* If the answer is ever no, the byte reduction bought a regression in the machinery that keeps failed work off the phase branch.

The reason to trust where that line is drawn: **the 20 blocking `eval.sh` anchors are almost exactly the safety machinery.** The eval suite pinned the phrases whose loss would be dangerous; Business Rule 2 was derived independently from asking what must survive a failed load. Two processes, no coordination, the same set of sentences.

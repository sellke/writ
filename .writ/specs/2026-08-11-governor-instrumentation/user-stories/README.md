# User Stories: Governor Instrumentation

> **Status:** Not Started — 0/7 stories, 0/48 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Delta-Bound Justification](./story-1-delta-bound-justification.md) | Not Started | 8 | 0/8 | None |
| 2 | [Clear the Four Live Growth Warnings](./story-2-clear-live-growth-warnings.md) | Not Started | 7 | 0/7 | Story 1 |
| 3 | [Component Contract Presence Check](./story-3-contract-presence-check.md) | Not Started | 8 | 0/8 | Story 2 |
| 4 | [`## Completion` Presence Check](./story-4-completion-presence-check.md) | Not Started | 6 | 0/6 | Story 2, Story 3 |
| 5 | [Loop Bounds Declaration Check](./story-5-loop-bounds-check.md) | Not Started | 6 | 0/6 | Story 2, Story 3 |
| 6 | [`required_skills:` Resolution Check](./story-6-required-skills-resolution-check.md) | Not Started | 6 | 0/6 | Story 2, Story 3 |
| 7 | [Warnings→Structural Flip Seam](./story-7-structural-flip-seam.md) | Not Started | 7 | 0/7 | Story 3, Story 4, Story 5, Story 6 |

## Dependency Graph

```
Story 1 (Delta-Bound Justification)  ── fixes the silencer first
   └── Story 2 (Clear the Four Live Growth Warnings)  ── gates every check
          └── Story 3 (Component Contract Presence Check)  ── introduces the seam
                 ├── Story 4 (## Completion Presence Check)  ─┐
                 ├── Story 5 (Loop Bounds Declaration Check)  ─┤── parallel, all route
                 └── Story 6 (required_skills: Resolution)    ─┘   through Story 3's seam
                        └── Story 7 (Warnings→Structural Flip Seam)
```

**Story 1 comes first because the silencer would otherwise outlive the fix.** `scripts/eval-leanness.py:527` reads `justification` once per *surface*, outside the per-metric loop, and line 533 treats any non-empty value as a reason to skip both `lines` and `chars` at any magnitude, forever. Every finding this spec adds is measured against surfaces that field can mute. Fixing it after the checks land would mean shipping four checks that a single sentence can switch off — and, worse, clearing the four live warnings (Story 2) with a mechanism that is about to change under it. Story 1 emits nothing new; it changes what a justification *means*.

**Story 2 is a hard gate, not a courtesy.** The Contract's hardest constraint is that four unjustified-growth warnings are live right now, and new warnings stacked on ignored warnings inherit their invisibility. No check may emit until the four are cleared and the run is quiet. Story 2 touches only `.writ/leanness-baseline.json` — it records bound justifications naming `a5c5a66`, which is only possible because Story 1 landed first.

**Story 3 owns the emission seam.** `CONTRACT_CHECK_SEVERITY` and `emit_contract_findings()` are introduced by the first check that needs them, so the seam is exercised from its first line rather than retrofitted. Stories 4, 5, and 6 consume it and add nothing to it.

**Stories 4, 5, and 6 are mutually independent** — three separate `check_*` functions, three separate fixture trees, no shared state beyond the router. They can run in parallel once Story 3 lands.

**Story 7 is the closing proof.** It does not build the seam; it *throws* it — flipping the constant in-process and asserting every finding from Stories 3–5 becomes blocking while Story 6's stay non-blocking, and that `eval.sh` actually FAILs. Business Rule 3 requires the flip be verified by a test that exercises it, not by reading the code, and that test cannot exist until there are findings from every check to move.

**Every story from 3 onward grows `scripts` and must pay for it.** Each one edits `scripts/eval-leanness.py`, pushing the `scripts` surface past the ceiling Story 2 recorded, so the growth warning returns mid-spec. That is the mechanism working. The disposition is a fresh, dated `justifications` entry naming the story that caused the growth, recorded inside that story (Business Rule 9) — never a batched raise at the end, and never an unbounded mute.

**Suggested execution order:** Story 1 alone. Then Story 2 alone. Then Story 3. Then Stories 4, 5, 6 in parallel. Then Story 7.

## Quick Links

- [spec.md](../spec.md) — locked contract, the 2026-08-11 approved scope addition, business rules, the `justification` trap and its fix, scope boundary
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — seam design, per-check algorithms, dual agent carrier, error/shadow/edge tables

## Governing Decisions

- [ADR-020](../../../decision-records/adr-020-component-contract.md) — the contract being checked; its "Enforcement sequencing (load-bearing)" section is the direct source of this spec's warnings-first posture.
- [ADR-021](../../../decision-records/adr-021-progressive-disclosure-token-budget.md) — the three specific reasons the existing governor never caught the bloat. Reason 2 ("growth warns, it does not fail") is why Stories 1 and 2 exist.
- [ADR-019](../../../decision-records/adr-019-full-surface-leanness-measurement.md) — the ratchet these checks sit alongside; Story 1 changes its `justification` semantics, not its "down is free" rule.

## Dependency Status (verified 2026-08-11)

`python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok`. Both declared dependencies exist and resolve, and the topological order it computes places this spec last in the Phase 10 chain:

```
retire-dead-prescription → component-contract → loop-bounds → governor-instrumentation
                        ↘ autonomy-gate-classes (independent)
```

That ordering is the sequencing this spec assumes: the migration specs bring the surface into compliance, and only then does the later `governor-enforcement` spec flip `CONTRACT_CHECK_SEVERITY`.

**Field-shape alignment, confirmed against the dependency specs as authored:**

- `2026-08-11-loop-bounds` names `loop.max_iterations` and `loop.on_exhaustion`, required at the top level of `loop:` — exactly Check 3's expectation. It also **explicitly cedes presence checking to this spec's Check 3**, naming the same five commands and the same 10 expected findings, and scopes its own check to correctness only.
- `2026-08-11-component-contract` delivers `problem:` / `outcome:` / `exit_criteria:` in all 31 commands and 7 agents plus `## Completion` in all 31 commands — the same populations Checks 1 and 2 measure, and the same 18 missing sections.

If either spec's shape moves, Story 5 task 5.1 and Story 3's field list are the only places that follow it.

## Expected Day-One Output (not a defect)

Once Stories 3–6 land, a run against the current surface emits approximately **142 findings** into `warnings`, exit 0:

| Check | Findings | Basis |
|---|---|---|
| Contract presence | 114 | 31 commands × 3 fields + 7 agents × 3 fields, 0 compliant today |
| `## Completion` | 18 | 31 checkable commands, 13 compliant today |
| Loop bounds | 10 | 5 commands × 2 fields, 0 compliant today |
| `required_skills:` | 0 | 0 declarations exist; reported as `required_skills_declarations: 0` |

This is the true measurement. Suppressing or aggregating it would reproduce the exact failure the spec exists to correct.

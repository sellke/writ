# User Stories: Loop Bounds

> **Status:** Not Started — 0/5 stories, 0/32 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Loop Schema and Exhaustion Vocabulary](./story-1-loop-schema-and-exhaustion-vocabulary.md) | Not Started | 6 | 0/6 | None |
| 2 | [Bounds on the Two Orchestrators](./story-2-orchestrator-bounds.md) | Not Started | 6 | 0/6 | Story 1 |
| 3 | [Bounds on implement-story's Gate-Retry Cycles](./story-3-implement-story-gate-cycles.md) | Not Started | 6 | 0/6 | Story 1 |
| 4 | [Bounds on refactor and verify-spec](./story-4-refactor-and-verify-spec-bounds.md) | Not Started | 6 | 0/6 | Story 1 |
| 5 | [The loop-bounds Eval Check](./story-5-loop-bounds-eval-check.md) | Not Started | 8 | 0/8 | Stories 2, 3, 4 |

## Dependency Graph

```
Story 1 (Loop Schema + on_exhaustion Vocabulary)
   ├── Story 2 (implement-phase, implement-spec)  ─┐
   ├── Story 3 (implement-story gate cycles)      ─┤── independent, parallelizable
   └── Story 4 (refactor, verify-spec)            ─┘
                                                   └── Story 5 (eval check)
```

**Story 1 is the only serializing dependency.** It writes no command file — it defines the `loop:` key contract, the three-value `on_exhaustion` vocabulary, and the composition rule with `scripts/phase-state.py`'s existing `classify` / `retry` / `quarantine` verbs. Stories 2, 3, and 4 each apply that contract to a disjoint set of command files and cannot conflict: Story 2 owns `implement-phase.md` + `implement-spec.md`, Story 3 owns `implement-story.md`, Story 4 owns `refactor.md` + `verify-spec.md`.

**Story 5 is the enforcement point** and must land last, because its historical-run regression assertion needs all five declared bounds present to have anything to compare. Without Story 5 the bounds are prose again, which is the exact failure ADR-020 diagnosed; Story 5 is not optional polish.

**Story 5's boundary with `2026-08-11-governor-instrumentation`.** That sibling spec's Check 3 already asserts these five commands declare `loop.max_iterations` + `loop.on_exhaustion`, and explicitly defers the field shape to this spec. The split is presence vs. correctness: Check 3 asks whether the block is there; Story 5 asks whether its values are legal, honestly cited, and calibrated against reality. Story 5 skips any file with no `loop:` block and reports `deferred_to_check3`, so a missing block is never reported twice.

**Suggested execution order:** Story 1 alone. Then Stories 2, 3, and 4 in parallel. Then Story 5.

## Quick Links

- [spec.md](../spec.md) — locked contract, business rules, the five bounds with evidence
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — schema key contract, per-command application, eval assertions, error/shadow/edge tables

## The Calibration Risk (read before writing any number)

This spec's danger is not that a bound is missing — it is that a bound is **wrong and low**. A tripwire set below a legitimate run converts a working loop into a spurious failure and costs a human a recovery cycle. Three rules govern every number in this spec, and each story restates them:

1. **Cite the run.** `calibrated_against:` is required and must name a real path plus the evidence quality (Business Rule 1).
2. **Never below observed.** No bound may be lower than the highest value in any recorded run under `.writ/state/` or any archived story's `Iteration count` record. A bound that would have tripped history is rejected, not exempted (Business Rule 2).
3. **Never a bare halt.** Every exhaustion writes unit, bound, count reached, last completed unit, and a literal resume command (Business Rule 3).

## Evidence Inventory (assembled 2026-08-11 — do not re-derive)

| Source | What it establishes |
|---|---|
| `.writ/state/phase-execution-20260719-121255.json` | Phase 9: 3 specs, every one `attempts: 1`, zero retries, zero quarantines, zero challenges |
| Roadmap Phase 7 | 4 specs — the largest phase ever run. **No state file survives**; roadmap-attested only |
| `.writ/state/execution-20260718-1101.json` | 4 stories; `reviewIterations` 1, 1, 1, 2 |
| `.writ/state/execution-2026080*.json` (×2) | 4 stories each |
| `.writ/state/phase9-result-*.json`, `phase-spec-result-*.json` | `stories_total` 4, 4, 3 |
| 41 archived spec folders | Largest story count = 9 (`2026-03-19-command-suite-evolution`) |
| Archived story "What Was Built" sections | 42 `Iteration count` records: 38 at 1, 4 at 2. **Max ever = 2** |
| `scripts/phase-state.py` `cmd_classify` / `cmd_retry` | `attempts < 2` — one initial attempt plus one transient retry, enforced in code |
| `commands/refactor.md` | **Zero recorded runs.** Sole anchor: line 100's "7+ changes" splitting advisory |

## Contradiction Found at Authoring Time (carry into implementation)

ADR-020 and the roadmap both state **"0 of 5 loop-bearing commands declare an iteration bound."** Verified as written, and true of the *machine-readable* surface — 32/32 commands carry frontmatter with exactly `name:` and `description:`, and no `loop:`, `max_iterations`, or `on_exhaustion` token exists anywhere in the repo.

But two of the five already carry **enforced** bounds in prose and code:

- `commands/implement-story.md:595` — "Max 3 iterations across review and visual QA gates"; `:732` — "2 fix iterations max"
- `commands/implement-phase.md:201` + `scripts/phase-state.py` — "exactly one transient retry," enforced by `attempts < 2`

The honest restatement is that **3 of 5 bounds are missing and 2 are unenforceable prose**. This does not weaken the spec — an unlintable cap cannot fail a build and cannot stop a thirty-third command from shipping unbounded — but it changes the work: five of the eight numbers in this spec are *transcriptions* of values that already exist and already work. Do not treat them as fresh design decisions (Business Rule 7).

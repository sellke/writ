# User Stories: Governor Enforcement

> **Status:** Not Started — 0/7 stories, 0/75 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Compliance Counts Reach the Eval Report](./story-1-metric-bridge.md) | Not Started | 7 | 0/7 | None |
| 2 | [Absolute Per-Invocation Byte Cap, Blocking](./story-2-absolute-byte-cap.md) | Not Started | 11 | 0/11 | Story 1 |
| 3 | [Retire the `check_length` Command Limit](./story-3-retire-check-length-command-limit.md) | Not Started | 9 | 0/9 | Story 2 |
| 4 | [The Compliance Pre-Check Gate](./story-4-compliance-gate.md) | Not Started | 8 | 0/8 | Story 2, Story 3 |
| 5 | [Throw the Severity Flip](./story-5-throw-the-severity-flip.md) | Not Started | 10 | 0/10 | Story 4 |
| 6 | [Prove the Gate Bites — Mutation, Then Revert](./story-6-mutation-proof.md) | Not Started | 15 | 0/15 | Story 5 |
| 7 | [Re-derive `MAX_SKILLS` and Correct the `required_skills:` Record](./story-7-max-skills-and-mechanism-record.md) | Not Started | 14 | 0/14 | Story 6 |

## Dependency Graph

```
Story 1 (METRIC bridge)  ── the gate's coverage number becomes readable first
   └── Story 2 (Absolute byte cap, blocking)  ── the ceiling ADR-021 reason 3 asked for
          ├── Story 3 (Retire the check_length command limit)  ── the limit that never bound
          └── Story 4 (Compliance pre-check gate)  ←── also needs Story 3
                 └── Story 5 (Throw the severity flip)  ── HARD GATE: only if Story 4 is green
                        └── Story 6 (Mutation proof)  ── the gate bites, demonstrated
                               └── Story 7 (MAX_SKILLS + the required_skills: record)  ── last: it moves the base
```

**The chain is strictly serial, and that is deliberate.** Every story either builds a blocking mechanism or verifies the precondition for the next one. There is no parallel batch here — unlike `2026-08-11-governor-instrumentation`, where Stories 4, 5 and 6 were three independent checks routing through one seam, every story in this spec changes what the *gate* does, and two of them can turn the whole suite red.

**Story 1 lands first because the flip makes its number load-bearing.** `contract_compliance` and `required_skills_declarations` reach `eval-leanness.py`'s JSON and never the eval report — verified 2026-08-12: `grep -c` over a generated leanness report returns 0 for both, because `scripts/eval.sh`'s TSV bridge prints a fixed METRIC set with branches for `per_surface` and `story_context_bytes` only. Today that is a missing progress trend. After Story 5 it is the **denominator of the gate** — the number that says how much surface the red or green covers. Shipping a blocking gate whose coverage is unreadable is not something to fix afterwards.

**Story 2 is the ADR-021 reason 3 deliverable and the one that can go red.** *"A ratchet is not a budget."* The per-surface delta ratchet stays exactly as it is; this adds an absolute ceiling alongside it, pinned at **24,960 bytes** — the irreducible shared base (`system-instructions.md` 20,153 + `commands/_preamble.md` 4,807). It appends to `structural` **directly**, never through `emit_contract_findings()`: routing the budget behind `CONTRACT_CHECK_SEVERITY` would let a future un-flip, or the typo fallback, disable it as collateral.

**Story 3 enforces a decision it does not own.** The ADR-021 amendment recording bytes-over-lines belongs to `2026-08-12-disclosure-implement-story` Story 1, which specifies it as: Decision point 5's 400-line limit is *superseded as the binding instrument* by the 24,960-byte budget, *"with the 400-line cap retained as a secondary, non-binding tripwire."* Expected shape of the edit: `-gt 2000` → `-gt 400`, `add_finding` → `add_note`. Story 3's first task is to read the **landed** amendment rather than that paraphrase; if it is absent the story halts. It owns exactly one line — `scripts/eval.sh:423`, `-gt 2000` — and must not touch `-gt 100` at line 404 or `-gt 95` at line 412, which sit 8 and 11 lines away and belong to `2026-08-11-autonomy-gate-classes`.

**Story 4 is the gate the Contract's hardest constraint demands, and it can stop the spec.** A committed test against the **real repo** asserting every command is within budget, that `structural` is empty under an in-process `"structural"` pin, that `contract_compliance` is saturated, and — added by the 2026-08-12 mechanism ruling — that **no command declares `required_skills:`**. That last one guards a failure the others structurally cannot see: a declaration is an *eager* pre-load, so it moves skill bytes into the floor where every invocation pays them, **without changing any command's own byte count**. Every one of the six disclosure specs certified its ceiling on the assumption that nothing is declared. If it is red, the spec halts there and its deliverable is a report naming which files are over and which disclosure spec owned each. **Story 5 does not start.** No exemption is granted to make it green — `file_has_exemption()` exists and using it here would convert enforcement into decoration.

**Story 5 is the one-string diff, and it is the smallest part of its own story.** The constant changes at `scripts/eval-leanness.py:278`; five committed tests invert; two anchors get repaired; the handoff comment gets rewritten. Verified by mutation on 2026-08-12: a flipped scratch copy runs `test_eval_leanness_contract.py` at **81 tests, 5 failures**, and two further tests keep passing **for the wrong reason** because they anchor on the literal `CONTRACT_CHECK_SEVERITY = "warnings"`, which survives the flip inside the handoff comment's diff preview at line 276. Instrumentation Story 7 documented that trap and defended one direction only. A red test announces itself; a silently inert test does not.

**Story 6 is the closing proof, and the one most likely to be skipped.** A green suite is equally consistent with a gate that works and a gate that quietly stopped asserting anything. Each gated property gets broken on a real file, observed red, and reverted — including two mutations whose whole subject is the *absence* of a silencing path: a planted bound justification and a planted `eval-exempt:` marker, neither of which may quiet the byte cap.

**Story 7 is last because it moves the budget's own derivation.** It edits `system-instructions.md`, which is 20,153 of the 24,960-byte `COMMAND_BYTE_BUDGET`, so this spec **causes its own base-drift finding** in a check it wrote back in Story 2. Sequencing it after Story 6 means the gate chain completes against a stable base: Story 4 certifies compliance, Story 6 proves the gate bites, and only then does the base move. `COMMAND_BYTE_BUDGET` is **not** re-derived — Business Rule 5's *"deliberate, dated act"* means a decision taken looking at the whole picture, not an automatic adjustment by the story that happened to nudge the base. Story 7 also re-runs Story 4's gate to confirm nothing certified was retroactively invalidated.

**Suggested execution order:** strictly 1 → 2 → 3 → 4 → 5 → 6 → 7. No parallelism.

## Quick Links

- [spec.md](../spec.md) — locked contract, the binding budget and its derivation, business rules, the five-tests-break inventory, scope boundary
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — verified pre-state, the cap's placement and severity, the three `check_length` addresses, error/shadow/edge tables

## Governing Decisions

- [ADR-021](../../../decision-records/adr-021-progressive-disclosure-token-budget.md) — the three reasons the old governor never caught 516KB. This spec answers reason 1 (*"the limit cannot bind"*, Story 3) and reason 3 (*"a ratchet is not a budget"*, Story 2), and throws the switch on reason 2 (*"growth warns, it does not fail"*, Story 5). **Its `check_length` disposition is amended by `2026-08-12-disclosure-implement-story`; Story 3 reads that amendment rather than re-deciding it.**
- [ADR-020](../../../decision-records/adr-020-component-contract.md) — "Enforcement sequencing (load-bearing)": checks land as `warnings` and flip to blocking *only once the migration brings the surface into compliance*. Story 4 is the measurement of that precondition.
- [ADR-019](../../../decision-records/adr-019-full-surface-leanness-measurement.md) — the per-surface ratchet the absolute cap lands **alongside**, never in place of.

## Verified Pre-State (2026-08-12 — re-measure before trusting)

Measured against the working tree on branch `phase/10-progressive-disclosure`:

- `python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json` → `structural: []`, `warnings: []`.
- `contract_compliance` fully saturated: 31/31 commands with contract, 31/31 with `## Completion`, 5/5 loop commands bounded, 7/7 agents. `required_skills_declarations: 0`.
- `CONTRACT_CHECK_SEVERITY = "warnings"   # -> "structural"` at `scripts/eval-leanness.py:278`. Flipped in-process, `main()` still returns `structural: []` — the surface complies; the seam holds.
- `base.bytes = 24960` from `scripts/measure-invocation.py`.
- **Six commands over budget by 67,578 bytes total** — `implement-story` (52,709), `create-spec` (46,423), `verify-spec` (32,110), `implement-phase` (29,136), `release` (28,589), `ship` (28,371). Exactly ADR-021's top-6 and exactly this spec's six dependencies.
- A 400-line cap selects 10 files instead, and **misses `implement-phase` entirely** (321 lines / 29,136 bytes). Bytes-per-line varies 2.63x, 34.5 (`migrate.md`) to 90.8 (`implement-phase.md`).
- Largest command: **989 lines** against `scripts/eval.sh:423`'s `-gt 2000` — 2.02x out of reach, ADR-021 reason 1 re-measured.
- `scripts/eval.sh` `check_length()`: `-gt 100` at line 404 (spec-lite), `-gt 95` at line 412 (`_preamble`), `-gt 2000` at line 423 (commands). Only line 423 is this spec's.

## Dependency Status (verified 2026-08-12)

`python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok`. All six dependencies exist — authored 2026-08-12, alongside this spec — and the topological order it computes places `2026-08-12-governor-enforcement` **immediately after every one of them**:

```
retire-dead-prescription → component-contract → loop-bounds → governor-instrumentation
disclosure-implement-story → {create-spec, verify-spec, release, ship, implement-phase}
                                    ↘ governor-enforcement
```

All six are `Status: Not Started`, so **every byte-budget figure in this spec is a pre-disclosure measurement**: six commands over budget by 67,578 bytes. Story 4 is where "the disclosure specs finished" stops being an assumption and becomes a number.

The dependencies are not to be removed to simplify anything. The ordering they encode is the only reason this spec can flip a blocking gate safely: each of the six shrinks one of the six over-budget commands. A spec that dropped them would validate cleanly and then discover 67,578 bytes of violation at Story 4 with no record of who owned them.

## Known Contradictions With Upstream Documents

Recorded at spec time so no story rediscovers them mid-implementation:

- **ADR-021's figures are stale, upward.** It records `implement-story.md` at 49,360 chars / 961 lines and the commands surface at 516,589 chars. Measured 2026-08-12: 52,709 bytes / 989 lines, and `per_surface.commands.chars` is **560,772**. No decision here depends on the ADR's numbers — the budget is computed from today's base — but a story quoting them will quote them wrong.
- **ADR-021 says `_preamble.md` is capped at 80 lines; `scripts/eval.sh:412` says 95.** Do not "correct" the code to match. That constant belongs to `2026-08-11-autonomy-gate-classes`, which derived 95 from a stated budget (79 + 14 + 2) and whose Business Rule 1 reads *"a cap chosen after the fact to accommodate whatever was written is not a cap."*
- **Two obligations were assigned to this spec by `2026-08-12-disclosure-implement-story` and fell outside its locked file set** — the roadmap's stale 400-line success criterion, and the `MAX_SKILLS` raise. **Half resolved on 2026-08-12:** the maintainer widened the file set to cover `MAX_SKILLS` (Story 7), which five sibling specs had flagged and none could take, because every disclosure spec bars itself from `scripts/`. **`.writ/product/roadmap.md` was not widened and remains out of scope** — its stale criterion still needs an owner before Phase 10 closes.
- **`required_skills:` is retired for this phase, and three consequences land here.** The mechanism is an *eager* pre-load, so extraction under it makes a command cost more than the monolith. All six disclosure specs switched to inline `Read skills/<name>/SKILL.md`. Consequences: Story 4's gate gains the no-declaration assertion; `MAX_SKILLS` becomes this spec's; and `system-instructions.md:252`'s **Status: adopted** claim — which names Phase 10 as the first consumer — becomes false and is corrected in Story 7. Full record: spec.md → ## Approved Scope Changes.
- **`required_skills_declarations` is now permanently 0, which reframes Story 1.** Story 1 surfaces it as instrumentation Business Rule 8's vacuous-pass guard on the expectation that *"progressive disclosure's extraction work lands the first real declarations."* It will not. The mechanism is unaffected and still right — distinguishing *"0 findings"* from *"0 things checked"* is exactly what that guard is for, and a permanent 0 is the strongest case for surfacing it. Only the framing was wrong, and Story 7 corrects the sentence it came from.
- **Nothing resolves an inline `Read`.** `check_required_skills()` reads frontmatter only (`eval-leanness.py:712`), so the phase's 29 inline skill loads have no standing enforcement from the gate this spec is making blocking. `measure-invocation.py` catches an unresolvable path but always exits 0. Out of scope here (new checker behavior, one gate change per spec) and recorded in spec.md → Technical Concerns as the most consequential gap the ruling opened.
- **The false consumer claim exists in four files, not one.** `system-instructions.md:252` is Story 7's; the identical sentence also sits in `adapters/cursor.md:217`, `adapters/claude-code.md:396`, and `adapters/openclaw.md:277`. Those files' description of the *mechanism* is accurate; only the trailing consumer sentence is false. `adapters/` is in no Phase 10 spec's file set — recorded, not taken.
- **`2026-08-12-disclosure-implement-story`'s spec.md says a 400-line cap *"would also fire on `migrate` (396 lines, 13,656 bytes)."*** Measured here on the same tree: 396 lines is **under** 400, so it would not fire. That spec's own Story 1 uses the correct example (`create-uat-plan`, 417 lines). Flagged so the ADR-021 amendment's **Measured:** line does not inherit it.

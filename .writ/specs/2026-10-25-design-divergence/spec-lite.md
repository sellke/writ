# Design Divergence Skill and Usage-First Gate 0 (Lite)

> Source: .writ/specs/2026-10-25-design-divergence/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Move `/prototype` Step 2.5's divergence rules into `skills/design-divergence/SKILL.md`, make `/implement-story` Gate 0 its second caller on the boundary-crossing route (caller usage first, then two independent sketches on declared axes), and run a human-rated blind trial that decides whether the skill stays.

**Implementation Approach:**
- Skill covers UI, API shape, and data model; eight rules plus one axis catalog per medium (technical-spec.md → Skill).
- `/prototype` keeps the gate, draft definition, render table, choice, and `exploration.md`; only the rules move.
- Gate 0 predicts the route with `boundary-map.py compute`, `change-surface.py classify`, and `boundary-map.py crossings` over the planned files. No new script, agent file, or `#### Gate` heading.
- The chosen sketch travels to Gate 1 in the Gate 0 warnings channel. Gate 1 is not edited.
- Switch: `- **Gate 0 Divergence:** off` in `.writ/config.md`; absent means on.
- Trial harness `scripts/divergence-trial.py` (`init`/`record`/`blind`/`rate`/`report`), Python 3.9, temporary.

**Files in Scope:**
- `skills/design-divergence/SKILL.md` — new
- `.writ/manifest.yaml`, `README.md` Skills row, root `SKILL.md` (gen-skill.sh) — registration
- `commands/prototype.md` — Step 2.5 rules → `Read` note; References
- `commands/implement-story.md` — Gate 0 block; Gate 0 Pipeline row; Overview clause; References
- `.writ/docs/config-format.md` — switch entry
- `scripts/tests/test_governor_enforcement.py` — ratchet re-pin
- `scripts/divergence-trial.py`, tests, fixtures — temporary
- `.writ/eval/divergence-trial/**`, `rating-handoff.md`, `trial-report.md`
- Generated trees — `python3 scripts/gen-platform-trees.py` only

**Error Handling:**
- Switch malformed → on with reason; route unverifiable or empty planned set → skip with reason
- Sketch spawn error or missing field → skip, no retry, pipeline continues
- Harness refusals → exit 2, files unchanged; report gaps → `unverifiable`, exit 0

**Integration Points:**
- `2026-10-25-gate-upgrade-removal-measurement` toggles the switch.
- Sibling Phase 15 specs re-pin the same implement-story ratchet; second to land re-pins from the first.

**Line Budget Constraints:** Gate 0 block under 2,000 bytes; `prototype.md` must shrink.

---

## For Review Agents

**Acceptance Criteria:**
1. The skill lints `pass`, is `status: candidate`, covers UI, API shape, and data model, and is registered in the manifest, catalog, README, and generated trees. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
2. `/prototype` Step 2.5 carries `Read skills/design-divergence/SKILL.md`; the render-table pins and every other Step 2.5 part are unchanged. `[AC-2.1, AC-2.2, AC-2.3]`
3. Gate 0 carries the divergence block with switch, route predictor, usage-first, two read-only `anchor` sketches, choice rule, hand-off label, and `gate0-divergence:` states. `[AC-3.1, AC-3.2]`
4. No divergence outcome blocks, marks DEGRADED, asks the user, or counts toward `review_cycle`; Gate 0.5–Gate 5 are byte-identical. `[AC-3.3, AC-3.4]`
5. The harness refuses malformed input with exit 2 and reports `keep` / `remove` / `unverifiable` by the stated rule. `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
6. The lane stops at `rating-handoff.md` with `report` printing `unverifiable` / `unrated`. `[AC-5.3, AC-5.4]`
7. The verdict is executed only from a human rating, the report is committed before any removal, and the harness is deleted afterward. `[AC-6.1, AC-6.4, AC-6.5]`

**Business Rules:**
- Route: switch on and (`--full-pipeline`, `--panel`, or predicted `review-agent`).
- Caller usage before axes; two sketches in independent contexts; commitment before sketch.
- Keep only if axes win ≥4 of 6 briefs and total distinct count; ties are not wins.
- Only a human rates; `unverifiable` is never acted on.

**Experience Design:**
- Entry: `/prototype` divergence gate; `/implement-story` on a boundary-crossing story
- Happy path: usage → two commitments → `gate0-divergence: chose A (…) — …`
- Moment of truth: sketches differ in structure, not naming
- Feedback: one `gate0-divergence:` line per Gate 0 run
- Error: `gate0-divergence: skip (<reason>)`, pipeline unchanged

---

## For Testing Agents

**Success Criteria:**
1. `bash scripts/lint-skill.sh skills/design-divergence/SKILL.md` → `pass`
2. `gen-skill.sh --check` and `gen-platform-trees.py --check` → `pass`
3. pytest (default and 3.9), bash tests, `eval.sh` → 0 findings

**Shadow Paths to Verify:**
- **Happy path:** both sketches complete → `chose` line, sketch in warnings
- **Nil input:** no planned files → `skip (unverifiable: no planned files)`
- **Empty input:** trial with no ratings → `unverifiable` / `unrated`
- **Upstream error:** sketch spawn fails → `skip (sketch incomplete: …)`

**Edge Cases:**
- Malformed switch value → off with reason
- Draft text edited after blinding → `rate` exits 2
- Key changed after blinding → `report` `unverifiable` / `key_changed`

**Coverage Requirements:**
- New code: ≥80%
- Critical paths: 100%
- Error paths: 100%

**Test Strategy:**
- Wiring tests on literals in both callers, config-format.md, and the skill
- Unit tests for every harness subcommand and refusal; outcome test independent of the harness

# Lean Implement Phase

> **Status:** Not Started
> **Created:** 2026-11-06
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** Promoted from issue: `.writ/issues/improvements/2026-11-06-implement-phase-over-prescribed.md`. Authored with `/create-spec`; decisions in [`recommendation-log.md`](recommendation-log.md).
> **Type:** Improvement. **Priority:** Normal. **Effort:** Medium.

## Specification Contract

**Deliverable:** `/implement-phase` generates UAT plans only on request, and `commands/implement-phase.md` shrinks from 366 lines to at most 240 by cutting prose its scripts already enforce. The merge, checker, supervisor and lane-isolation invariants do not change.

**Must Include:** A phase run without a UAT request writes no `uat-plan.md`, spawns no `/create-uat-plan`, and still gets `met` from `exit-criteria.py`.

**Hardest Constraint:** `uat-plan.md` is the resume signal in Step 1.3 and the evidence for `implement-phase.c2` today. Both need a replacement. The c2 criterion text appears verbatim in the command frontmatter, `scripts/exit-criteria.py`, `scripts/eval.sh` and `.writ/docs/exit-criteria-classification.md`.

**🎯 Experience Design:**
- **Entry point:** `/implement-phase N`. `/implement-phase N --uat` keeps today's per-spec UAT plans.
- **Happy path:** the phase runs and specs merge. The report lists the human-judgment criteria, with one `/create-uat-plan {spec}` line for each spec that needs a person to validate it.
- **Moment of truth:** the report reads `UAT: not requested` and the checker returns `met`.
- **Feedback model:** report lines, plus `uatRequested` in phase state.
- **Error experience:** with `--uat`, a missing or stub plan leaves c2 `unmet`, as it does today.

**📋 Business Rules:**
1. A UAT plan is generated only on request: `--uat` at launch, or the user running `/create-uat-plan` afterward. A roadmap criterion such as "UAT scenarios pass" is not a request. It is handed off.
2. `implement-phase.c2` keeps its ID. It checks plans only when `uatRequested` is true. Otherwise it returns `met` with evidence `UAT not requested`.
3. Resume skips a spec when phase state records it `integrated` or every story in it is complete. The presence of `uat-plan.md` no longer decides it.
4. `phase-state.py health` counts only the sources it is given. An omitted source is `not_requested` and is not a Warning. A source given as a path that does not exist is still a Warning.
5. Step 1.4 (Goal emit) leaves `/implement-phase`. `/create-goal` already emits.
6. A lane writes its `phase-spec-result-v1` to a file named in its brief, and `validate-result` reads that file. The brief is a shipped template. This replaces the truncated-result paragraph in Step 3.2.
7. The prose cuts change no behavior. Failure handling becomes event → subcommand lines, and the reasons move to `.writ/docs/phase-execution-state-format.md`. One question-policy section remains. Step 1.2b keeps the owns / deps / seams proposal shape and drops its method steps.
8. Unchanged: never merge an unverified lane; the checker verdict governs; human criteria are never self-certified; the lane supervisor; the quarantine and closure scripts; the terminal constraint.

**Success Criteria:** both pytest runs (Python 3.9 and 3.14), the bash tests, and `eval.sh` pass. A fixture phase without `--uat` gets c2 `met`. A `--uat` fixture with no plan gets c2 `unmet`. `wc -l commands/implement-phase.md` is at most 240.

**Stories (sequential; all four edit `implement-phase.md`):**
1. UAT on request: flag, state field, c2 predicate and text, resume signal, report, README / SKILL / generated trees
2. Health counts only the sources it is given; Goal emit removed
3. Lane result file and shipped brief template (retro F22)
4. Prose compression to at most 240 lines

**Scope Boundaries:**
- Included: the four stories above
- Excluded:
  - running independent specs in parallel (needs its own measured trial)
  - changes to `/create-uat-plan` itself
  - supervisor, quarantine, retry or closure behavior
  - deleting any script or test

**⚠️ Technical Concerns:**
- Story 3 edits `commands/implement-spec.md` § Phase-Orchestrated Lane Mode. `2026-11-06-lean-story-pipeline` edits other sections of the same file (Step 2.3, Step 3.3, the supervisor input).
- Stories 1–3 add text before Story 4 removes it, so `KNOWN_OVER_BUDGET` in `test_governor_enforcement.py` may need a dated entry in between.

**⚠️ Cross-Spec Overlap:**
- `2026-11-06-lean-story-pipeline` (Not Started) also edits `commands/implement-spec.md`. It excludes F22 (lane mechanics). Advisory: run them one after the other. No dependency is declared.

## Evidence

- Writ's 5 phase runs (20 specs) in `.writ/state/phase-execution-*.json`: all 20 `integrated`; no quarantines, no `skipped_blocked`, no halts; 4 specs took a second attempt; 2 User Challenges in one run. Every run is Writ building itself.
- Phase 15 retro (`.writ/retros/2026-10-30-phase-15.md`):
  - **F10, F24:** 201 UAT scenarios, all human; about 1.04M output tokens and 378 tool calls.
  - **F22:** lane results arrive only in conversation, one dropped; `health` asks for a `--verification` report that no step produces.
  - **F25:** UAT agents spent about 135 of 378 calls re-deriving setup conventions.
- `implement-phase.c2` requires a populated plan for every merged spec. The checker enforces the F10 cost.

## 🎯 Experience Design

### User Journey

1. A developer runs `/implement-phase N`.
2. The plan (Step 2.3) prints `UAT: not requested (pass --uat to generate plans per spec)`.
3. Each lane runs `/implement-spec`, writes its result file, and the supervisor and `validate-result` check it. Verified work merges.
4. No `/create-uat-plan` runs.
5. The report shows each spec, the exit criteria, the human-judgment criteria handed off with a `/create-uat-plan {spec}` line per spec, and the checker verdict.
6. Later, the developer runs `/create-uat-plan {spec}` for the specs a person should validate.

With `--uat`, step 4 runs `/create-uat-plan {spec}` after each merge, as it does today, and c2 checks each plan.

### State Catalog

| State | What the developer sees |
|---|---|
| No `--uat`, all merged | `UAT: not requested`; c2 `met` (`UAT not requested`); status `IMPLEMENTED — pending human validation` when human criteria remain |
| `--uat`, all plans present | UAT column per spec; c2 `met` |
| `--uat`, a plan missing or a stub | c2 `unmet` naming the spec; status cannot be `COMPLETE` |
| `--resume` of a run started without `--uat` | `uatRequested` stays false; no plans generated |
| `--resume` of a pre-change state file (no `uatRequested`) | Treated as `true`: the run started under the old contract, which promised plans |
| Lane result file missing or unparseable | Resume the same lane agent once and ask it to write the file; a second miss is a `transient` failure |
| `health` with only the sources the phase produced | `Healthy` when they are clean |

### Interaction Patterns

- The `--uat` flag is the only new user input. `--resume` reads `uatRequested` from state, so the flag is not repeated.
- `--all` passes `--uat` through to every phase it enters.

## 📋 Business Rules (Expanded)

- **Business Rule 1:** the human-judgment handoff in Step 4.2 still lists every human criterion. Without `--uat`, it names `/create-uat-plan {spec}` for each merged spec instead of a scenario count. Under `--uat`, the scenario count stays.
- **Business Rule 2:** the c2 text in all four places changes together, and the eval literal and predicate docstring are updated with it. Proposed text: "when UAT plans were requested, each merged spec folder contains a populated uat-plan.md generated after that spec was implemented". The ID stays `implement-phase.c2`, so `exit-criteria-classification.md` keeps its row and gains the condition.
- **Business Rule 2, old state files:** a state file without `uatRequested` is read as `true`. This keeps the checker's verdict on finished runs from changing.
- **Business Rule 3:** Step 1.3 inventory uses phase state first, then story statuses. A spec with a stale `uat-plan.md` and incomplete stories is not skipped.
- **Business Rule 4:** `/status` calls `health` with the sources it has. The same omitted-source rule applies there.
- **Business Rule 5:** the `goal-emit.py` row in `agent-cli-contract.md` drops `commands/implement-phase.md` from its consumers. `test_goal_emit_command_hooks.sh` stops asserting implement-phase origin emit and still asserts the `/create-goal` emit.
- **Business Rule 6:** the result path is absolute and outside the lane worktree (`<repo>/.writ/state/lane-result-<phase>-<spec>.json`), so it survives worktree removal. `validate-result --input` already takes a path. The orchestrator passes the file.
- **Business Rule 7:** every literal `eval.sh` pins in `implement-phase.md` survives Story 4 (see technical-spec.md → Pinned literals).
- **Business Rule 8:** Story 4 is checked by the existing eval literals and the phase tests passing unchanged.

## Detailed Requirements

- `--uat` is added to the Invocation table and stored by `phase-state.py init --uat` as top-level `uatRequested: true|false`.
- Step 3.2 item 6 runs only when `uatRequested` is true.
- The per-spec `uatPlan` field stays in the schema. It is set only under `--uat`.
- README pipeline line `/create-uat-plan (per spec, auto)` and the `/implement-phase` rows in `README.md` and `SKILL.md` describe UAT as opt-in.
- `health` adds the `not_requested` source value and leaves categories unchanged otherwise.
- The lane brief template lives at `commands/_lane-brief.md`. It is shipped and holds a placeholder for each path. It is referenced from Step 3.2 and from implement-spec's Lane Mode.
- `implement-phase.md` ends at no more than 240 lines. The rationale removed from it lands in `phase-execution-state-format.md` under a "Why" subsection per mechanism.

## Implementation Approach

Four sequential stories. Each changes behavior in scripts first, under tests, then updates the command text. Story 4 only moves and cuts text, and the existing pins check it. Generated trees are refreshed with `python3 scripts/gen-platform-trees.py` after each command edit. Byte-budget changes get dated `KNOWN_OVER_BUDGET` entries.

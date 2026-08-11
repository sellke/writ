# Story 2: Bounds on the Two Orchestrators

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer running `/implement-phase` or `/implement-spec` unattended
**I want** each orchestrator to declare how many units it will process and what happens when it reaches that number
**So that** a runaway orchestration stops at a declared point with a resume command instead of consuming a session, and so that the stopping rule is readable before the run rather than inferred after it

## Acceptance Criteria

- [ ] Given `commands/implement-phase.md`, when its frontmatter is read, then `loop.unit` is `spec`, `loop.max_iterations` is `12`, `loop.on_exhaustion` is `halt_reported`, and `loop.calibrated_against` cites `.writ/state/phase-execution-20260719-121255.json` (Phase 9, 3 specs), roadmap Phase 7 (4 specs, no surviving state file), and states the evidence quality as thin.
- [ ] Given `commands/implement-phase.md`, when its nested loop is read, then a `nested` entry declares `unit: spec_attempt`, `max_iterations: 2`, `on_exhaustion: quarantine`, and cites `scripts/phase-state.py`'s `cmd_classify` (`attempts < 2`) and `cmd_retry` (`retry_exhausted` at `>= 2`) as the transcribed source — and the number `2` matches that guard exactly.
- [ ] Given `commands/implement-spec.md`, when its frontmatter is read, then `loop.unit` is `story`, `loop.max_iterations` is `12`, `loop.on_exhaustion` is `halt_reported`, and `loop.calibrated_against` cites the 9-story maximum across 41 archived specs plus the six recorded runs (all ≤ 4 stories).
- [ ] Given `/implement-phase` reaches its outer bound, when the loop terminates, then it emits a `halt_reported` record naming the unit, the bound, the count reached, the last integrated spec, and the literal `/implement-phase --resume` command — and it does **not** quarantine any spec, mark any spec `skipped_blocked`, or write a failure record for work that never failed.
- [ ] Given a spec inside `/implement-phase` consumes its one permitted transient retry, when the outer counter is examined, then the retried spec has incremented the outer `spec` counter exactly once, not twice — retries are counted by the nested `spec_attempt` bound only.
- [ ] Given `/implement-phase --all` chains multiple roadmap phases, when the `spec` counter is examined at a phase boundary, then it resets per phase rather than accumulating across the chain, and the frontmatter or accompanying prose states this explicitly.

## Implementation Tasks

- [ ] 2.1 Re-verify the calibration evidence before writing any number: read `.writ/state/phase-execution-20260719-121255.json` (confirm `specOrder` length 3 and every spec at `attempts: 1`), the three `.writ/state/execution-*.json` files, the `phase*result*.json` files' `stories_total`, and the story-count distribution across `.writ/specs/archive/*/user-stories/` — then confirm 12 exceeds every observed value for both units
- [ ] 2.2 Append the `loop:` block to `commands/implement-phase.md`'s existing `---` frontmatter, including the nested `spec_attempt` entry, without touching `name:`, `description:`, or any key `2026-08-11-component-contract` may have added
- [ ] 2.3 Append the `loop:` block to `commands/implement-spec.md`'s frontmatter on the same terms
- [ ] 2.4 Add one sentence to `implement-phase.md` Step 3.2 stating the bound and pointing at `on_exhaustion` — and leave Step 3.3 item 1 ("Writ permits exactly one transient retry") untouched, since it is the source the nested entry transcribes
- [ ] 2.5 Specify the `halt_reported` record for both commands against the state files that already exist: `phase-execution-*.json` (unstarted specs stay `pending`, phase `status` stays `executing`, `--resume` + `reconcile` recovers) and `execution-*.json` (`stories.{id}.status` / `phase` carry the resume position)
- [ ] 2.6 Verify acceptance criteria are met, including a check that the declared `spec_attempt` bound equals the `attempts < 2` guard read from `scripts/phase-state.py` rather than a hardcoded 2

## Notes

**Technical considerations:**

- **`halt_reported`, not `quarantine`, for the outer phase loop — this is the load-bearing decision in this story.** At outer-loop exhaustion nothing has failed; the phase merely ran longer than declared. Quarantining an unstarted spec would fabricate a failure record and, through `_transitive_dependents`, mark its dependents `skipped_blocked` — a scope degradation forbidden by Business Rule 5 and by ADR-013's non-degradation boundary. The correct terminal state already exists and is already resumable.
- `implement-spec.md:170` offers the user retry / skip / skip-with-dependents / abort on story failure. That retry is **human-selected and currently unbounded**, and this story does not bound it — `max_iterations` counts stories *dispatched*, not user-elected retries. Say so in the file. If that retry ever becomes autonomous it acquires a `nested` entry with `on_exhaustion: escalate`; that is a future change, not this one.
- 12 for both units is a coincidence of arithmetic, not a shared constant: `implement-phase` gets 3× its largest observed run (4), `implement-spec` gets the all-time authored maximum (9) plus 3. The contract forbids a single global constant, so the two `calibrated_against` values must make the independent derivations visible.

**Risks / challenges:**

- **The `implement-phase` bound is the weakest-evidenced of the two and should be treated that way.** Two runs, one without a surviving state file, and `.writ/state/` is gitignored so the sample can only shrink. If Phase 10 itself runs more than 12 specs, the bound trips — cost is one recovery cycle, and the correct response is to raise it citing that run, not to exempt the file.
- Double-counting a retried spec against the outer bound would silently halve the effective phase bound. Whatever mechanism increments the counter must key on distinct spec IDs, not on lane launches — `cmd_create_lane` increments `attempts` on every launch including retries, so it is the wrong signal to reuse.

**Integration points:**

- Consumes Story 1's schema verbatim; adds no keys.
- Owns exactly two files — `commands/implement-phase.md` and `commands/implement-spec.md`. Stories 3 and 4 own disjoint sets and run in parallel.
- Story 5's assertions 7 and 8 verify this story's numbers against `.writ/state/` and against `scripts/phase-state.py` respectively.
- Reads `scripts/phase-state.py` but must not modify it — the retry rule is transcribed, never touched.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (every bound cites the run it was calibrated against), Rule 2 (no bound below the highest observed historical value), Rule 5 (exhaustion never degrades scope — the reason the outer loop is `halt_reported` and not `quarantine`), Rule 7 (existing enforced numbers are transcribed: `attempts < 2` becomes exactly 2)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The five bounds table — `implement-phase` (spec/12/halt_reported), its nested `spec_attempt` (2/quarantine), and `implement-spec` (story/12/halt_reported), each with its evidence and evidence quality] — from spec.md → ## Detailed Requirements → ### The five bounds
- **Error map rows:** [A phase legitimately has more than 12 specs → bound trips, `halt_reported` fires, raise the bound citing that run; `--all` chains phases → counter resets per phase; a transient retry must not consume an outer iteration] — from sub-specs/technical-spec.md → Interaction Edge Cases
- **Contract:** ["Each bound is derived from that loop's real semantics — `/implement-phase` bounds specs-per-phase — not a single global constant"; "`on_exhaustion` must always terminate with a reported, recoverable state — never a silent stop"] — from spec.md → ## Contract (Locked)

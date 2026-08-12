# Story 7: Re-derive `MAX_SKILLS` and Correct the `required_skills:` Record

> **Status:** Complete — adapters corrected under Approved Scope Change 2026-08-12 (c)(ii)
> **Priority:** Medium
> **Dependencies:** Story 6

## User Story

**As a** Writ maintainer closing Phase 10 with a skill corpus six times the size it started at and a convention whose adoption rested on a consumer that never arrived
**I want to** `MAX_SKILLS` raised by a derivation rather than to fit the roster, and `system-instructions.md` to stop claiming a mechanism this phase rejected
**So that** the two obligations the mechanism ruling left behind land as decisions with reasoning attached, rather than as a constant somebody bumped and a status line nobody re-read

## Acceptance Criteria

- [x] Given `check_required_skills()` resolves frontmatter only, when this story lands, then it also resolves inline `Read skills/<name>/SKILL.md` occurrences in command bodies, emits a finding naming file and skill for any that resolve to no `skills/<name>/SKILL.md`, and reports the inline count in `metrics` beside `required_skills_declarations`.
- [x] Given a fixture command carrying a deliberately mistyped inline read, when the check runs, then it produces exactly one finding naming that file and that skill — proving the phase's actual loading mechanism is no longer unchecked.
- [x] Given `adapters/cursor.md:217`, `adapters/claude-code.md:396` and `adapters/openclaw.md:277` each claim Phase 10 progressive disclosure is `required_skills:`'s first consumer, when this story lands, then all three state instead that the convention has no consumer and carries a 2026-11-11 review trigger — with the schema and the graceful-degradation rule byte-unchanged in each.
- [x] Given the claim must not survive anywhere, when `grep -rn "first consumer" system-instructions.md adapters/ .writ/decision-records/adr-021-*.md` runs, then no hit asserts Phase 10 progressive disclosure as a live consumer of `required_skills:`.

- [x] Given `MAX_SKILLS = 12` at `scripts/eval-leanness.py:71` and a post-phase corpus of 35, when this story completes, then `MAX_SKILLS` is **45**, derived as `MAX_COMMANDS + MAX_AGENTS` (35 + 10), with the derivation, its date, the measured count, and the remaining headroom recorded in a comment at the constant — so the next reader sees **why 45**, not what 45 was made to fit.
- [x] Given `2026-08-11-autonomy-gate-classes` Business Rule 1 (*"a cap chosen after the fact to accommodate whatever was written is not a cap"*), when the derivation is reviewed, then it satisfies all three of Business Rule 8's tests, each stated in the Notes with its evidence: it is computed from constants that exist for other reasons and never reads the roster; **it can still fire** (35 against 45 leaves 10 of headroom, and a second disclosure programme crosses it); and it moves only when `MAX_COMMANDS` or `MAX_AGENTS` move.
- [x] Given the counterfactual is the test that separates a cap from an accommodation, when this story completes, then the Notes state it explicitly: **had the phase's roster landed at 50, this derivation would still yield 45 and the cap would fire** — and the correct outcome would have been a Tier B escalation, not a larger constant.
- [x] Given the corpus is measured rather than assumed, when this story runs, then the actual `skills` count is read from `eval-leanness.py`'s `metrics.skills` against the real tree and recorded — with the per-spec roster (implement-story 8, create-spec 5, release 5, verify-spec 4, ship 4, implement-phase 3 = 29 new + 6 existing = 35) reconciled against it and any divergence explained. `2026-08-12-disclosure-ship`'s *"at least 29 skills"* is a **total** reached by counting two specs at +4 instead of +5 and omitting `verify-spec`; the correction is recorded.
- [x] Given `MAX_SKILLS` lives in `check_ceilings()`, when this story completes, then it is **still warn-only and non-blocking**, and the decision is stated with its reasoning at the constant: a count is not a unit of load (ADR-021's finding, and Story 3 of this spec retires a line limit for exactly that reason); a blocking count cap would block the extraction that *lowers* per-invocation load under conditional loading; and skill bloat is already governed in **bytes** by ADR-019's per-surface ratchet with bound justifications. The revisit condition is recorded: if a `ceiling_bytes` budget is ever adopted, the count cap becomes **redundant, not stricter**.
- [x] Given `check_ceilings()` is otherwise untouched, when this story's diff is inspected, then `MAX_COMMANDS`, `MAX_AGENTS`, the function body, and every other constant in that block are **byte-identical** to their pre-story state. Only the `MAX_SKILLS` value and the comment above it change.
- [x] Given `system-instructions.md:252` claims **Status: adopted** with Phase 10 progressive disclosure as *"the first consumer"* and states that *"progressive disclosure's extraction work lands the first real declarations"*, when this story completes, then the status paragraph records instead that Phase 10 **evaluated the mechanism and did not adopt it**, names the measured reason (`required_skills:` is an eager pre-load — the harness loads every declared skill *"before any phase work begins"*, so extraction under it moves bytes into the floor and makes a command cost more per invocation than the monolith), cites both sources (`system-instructions.md` § Harness contract; `adapters/claude-code.md:396`), and states that **the convention still has no consumer**.
- [x] Given the schema is referenced by `commands/new-skill.md`, implemented in three adapters, and validated by `check_required_skills()`, when this story completes, then the **schema itself is unchanged** — optional array, order preserved, duplicates deduplicated, unknown names warn rather than hard-fail. This story corrects a status claim; it does not deprecate, redesign, or remove anything.
- [x] Given the 2026-08-03 trigger resolved *revisit → adopt* on a justification consisting almost entirely of a named future consumer that then rejected the mechanism, when this story completes, then the **review trigger is restored** with a date and terms — recommended **2026-11-11**, aligned to ADR-021's own review trigger, with terms: if no command or agent declares `required_skills:` by that date, deprecate; if one does, record it and reset. A decision to *not* restore it would require an argument that the adoption stands on something other than the consumer it named, and that argument is recorded as absent.
- [x] Given `system-instructions.md` is 20,153 of the 24,960-byte budget derivation, when this story completes, then the new `base.bytes` and its delta from `COMMAND_BYTE_BUDGET` are measured and recorded, **`COMMAND_BYTE_BUDGET` is unchanged**, and `check_budget_derivation()`'s non-blocking finding is quoted in the Notes as observed output (Business Rule 5).
- [x] Given Story 4's gate certified compliance against a stable base and Story 6 proved the gate bites, when this story runs, then it runs **after both**, and re-running Story 4's gate test after the edit still passes — the base moved, the budget did not, and no certified figure was retroactively invalidated.
- [x] Given the identical false consumer claim also appears in `adapters/cursor.md:217`, `adapters/claude-code.md:396`, and `adapters/openclaw.md:277`, when this story completes, then **no adapter is edited** (out of scope — `adapters/` is in no Phase 10 spec's file set) and the three locations are recorded in the Notes as an open correction needing an owner, so the fix is not left half-done by accident.
- [x] Given this story edits `scripts/eval-leanness.py`, when it completes, then `bash scripts/eval.sh` is green end to end, `python3 scripts/eval-loop-bounds.py`'s `governor-boundary-intact` still passes, and the full `scripts/tests/` suite passes.

## Implementation Tasks

- [x] 7.1 Measure before deciding: `python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json` → record `metrics.skills`, `metrics.commands`, `metrics.agents`. Reconcile against the six-spec roster and record any divergence with its cause
- [x] 7.2 Record the derivation in full before editing the constant: `MAX_SKILLS = MAX_COMMANDS + MAX_AGENTS = 45`, its rationale (a skill exists only as a capability extracted from a consumer; one skill per potential consumer is where extraction stops being shared capability and becomes a 1:1 shadow of the consumer surface — ADR-021 §4's "two copies instead of one shared skill" as a count), the three Business Rule 8 tests with evidence, and the counterfactual
- [x] 7.3 Change `MAX_SKILLS` from 12 to 45 and write the comment above it: derivation, date, measured count 35, headroom 10, and the warn-only decision with its reasoning and its revisit condition
- [x] 7.4 Assert the rest of the ceiling block is untouched — `MAX_COMMANDS`, `MAX_AGENTS`, and `check_ceilings()`'s body byte-identical against `git show HEAD:scripts/eval-leanness.py`, by diff and not by eye
- [x] 7.5 Add or extend a test asserting the committed `MAX_SKILLS` value **and** that the skills count is below it — so a future roster that crosses 45 fails a named assertion rather than adding a line to a report
- [x] 7.6 Read `system-instructions.md:225-252` in full before editing, plus `commands/new-skill.md:233,248,273` and the three adapter sections, so the correction lands on the status paragraph alone and leaves the schema and its references intact
- [x] 7.7 Rewrite the status paragraph: Phase 10 evaluated and did not adopt; the eager-pre-load reason with both sources; the convention has no consumer
- [x] 7.8 Restore the review trigger — date 2026-11-11 aligned to ADR-021's review, with its terms and the reason for the alignment (the review already reads the data that would justify a consumer)
- [x] 7.9 Re-measure the base: `python3 scripts/measure-invocation.py --root . --format json` → record `base.bytes` and the delta from `COMMAND_BYTE_BUDGET`. **Do not change `COMMAND_BYTE_BUDGET`**
- [x] 7.10 Run `bash scripts/eval.sh --check=leanness` and quote `check_budget_derivation()`'s finding verbatim in the Notes as observed output
- [x] 7.11 Re-run Story 4's gate test and confirm it still passes on the moved base
- [x] 7.12 Record the three unedited adapter locations as an open correction needing an owner
- [x] 7.13 Raise `surfaces.scripts.justifications.{lines,chars}` for this story, dated, naming this story; and `surfaces.system_instructions.*` if this story's edit passes its recorded ceiling
- [x] 7.14 Verify acceptance criteria: full `scripts/tests/`, `eval-loop-bounds.py`, `bash scripts/eval.sh` end to end

## Notes

**Technical considerations:**

- **This story is sequenced last for a specific reason, not by default.** It edits `system-instructions.md`, which is 20,153 of the 24,960-byte `COMMAND_BYTE_BUDGET` derivation. So this spec **causes its own base-drift finding**, in a check it wrote in Story 2, in the same run. Running it after Story 6 means the gate chain 1 → 6 completes against a stable base: Story 4 certifies compliance, Story 6 proves the gate bites, and only then does the base move. Reversed, every certified figure would sit on a base that shifted underneath it mid-spec.
- **`COMMAND_BYTE_BUDGET` is not re-derived here, and that is the decision rather than an omission.** Business Rule 5's *"re-deriving is a deliberate, dated act"* means a deliberate act by somebody looking at the whole picture — not an automatic adjustment by the story that happened to nudge the base. Re-deriving mid-spec would move the number Story 4 certified against and Story 6 proved, retroactively invalidating both. The check firing on its own author's edit, in the run it shipped, is the strongest available demonstration that it works.
- **The derivation is the deliverable; the constant is a consequence of it.** `MAX_SKILLS = MAX_COMMANDS + MAX_AGENTS` is computed from two constants set for their own reasons in the same block of the same file. It never reads the roster, which is what makes it a cap. The measured 35 is an **input the derivation is answerable to**, not its source: had the phase produced 50 skills, the derivation would still yield 45 and the correct output would be a firing cap and a Tier B escalation.
- **Warn-only is a decision that needs stating because everything around it is becoming blocking.** Four checks flip in Story 5 and the byte cap blocks from Story 2, so silence on `MAX_SKILLS` reads as an oversight. A count is not a unit of load — that is ADR-021's central finding, and Story 3 of this spec retires a 2000-line limit for precisely that reason. `commands/implement-phase.md` is the standing evidence: 321 lines, inside any plausible line cap, and 4,176 bytes over budget. Making a *skill count* blocking repeats the error one surface over.
- **The skills surface is already governed in the right unit.** It is in `SURFACE_REGISTRY` and under ADR-019's per-surface ratchet with the schema-3 bound-justification mechanism, and every disclosure spec is already required to file a bound justification for its skill-surface growth. The blocking instrument for skill bloat exists and it measures bytes. The count is a proliferation tripwire, which is a different and softer question.
- **The status correction is small in bytes and substantive in effect.** The schema stays exactly as written. What changes is a paragraph that asserts a consumer who declined. The second half — restoring the review trigger — is the part that matters: the 2026-08-03 resolution was *revisit → adopt* on a justification consisting almost entirely of a named future consumer, and that consumer measured the mechanism and rejected it. A resolution whose premise turned out false should not survive as a settled adoption; that is how a convention accretes permanence it never earned, and `2026-08-11-retire-dead-prescription` exists because this repo has that failure mode.
- **2026-11-11 is chosen, not defaulted.** ADR-021's own review trigger falls that day and already asks whether measured per-invocation load dropped for at least 4 of the 6 targeted commands. The same reading is in the best position to answer whether an eager mechanism ever acquired a consumer. Two triggers, one review, no second calendar entry to forget.

**Risks / challenges:**

- **Deriving backwards from 35.** The predictable failure is picking a number that clears the roster — 40, or 35-plus-headroom — and writing the justification afterwards. That is verbatim the defect `2026-08-11-autonomy-gate-classes` Business Rule 1 bans, and the `_preamble` cap was protected from it by a stated budget (79 + 14 + 2 = 95). The test to apply before committing the value: **name the roster size at which this cap would fire.** If the answer is "none reachable", the derivation is an accommodation.
- **Editing more of `system-instructions.md` than the status paragraph.** The schema block sits directly above it and reads as part of the same section. Every claim in the schema — optional array, order preserved, duplicates deduplicated, unknown names warn — is still accurate and still implemented. Only the status paragraph is false.
- **"Correcting" the adapters while in the neighbourhood.** All three carry the identical false consumer sentence and it is tempting to fix three lines. `adapters/` is in no Phase 10 spec's file set, and `2026-08-12-disclosure-implement-phase` scopes it *"verify, do not edit."* Record the three locations; do not take them.
- **Deprecating the convention because it has no consumer.** Restoring the trigger is the scoped action. Deprecation is ADR-scale, touches three adapters, `commands/new-skill.md`, and `check_required_skills()`, and belongs to the restored trigger's review.
- **Letting the base-drift finding read as a defect in the report.** It will appear in the same run that ships this spec. Quote it in the Notes as *observed, expected, and by design* so a reviewer reads it as the check working rather than as this spec breaking its own budget.

**Integration points:**

- `scripts/eval-leanness.py` — `MAX_SKILLS` at line 71 only; `check_ceilings()` and the sibling constants untouched.
- `system-instructions.md` — the `required_skills:` status paragraph only; the schema, the harness contract, and every other section untouched.
- Story 2's `check_budget_derivation()` fires on this story's edit. That is the interaction, and it is handled rather than avoided.
- Story 4's gate test is re-run after the edit; the base moved and the budget did not, so it must still pass.
- Read-only and recorded, not edited: `adapters/{cursor,claude-code,openclaw}.md`, `commands/new-skill.md`, `.writ/product/roadmap.md`.

## Implementation Notes (2026-08-12)

### Two ACs were superseded before this story ran

- *"no adapter is edited … recorded as an open correction"* is **overridden by
  Approved Scope Change 2026-08-12 (c)(ii)**, which widened the file set:
  *"`system-instructions.md` (Story 7 already owns it) plus `adapters/cursor.md:217`,
  `adapters/claude-code.md:396`, and `adapters/openclaw.md:277` each state that
  Phase 10 progressive disclosure is `required_skills:`'s first consumer … Story
  7 extends to the three adapters."* All three are corrected.
- The inline-read resolution check, listed in § Out of Scope as *"new checker
  behavior … one gate change per spec"*, is **assigned here by (c)(i)** as the
  most consequential gap the mechanism ruling opened.

### Task 7.1 — measure before deciding, and reconcile

```
metrics.commands = 32   metrics.agents = 7   metrics.skills = 14
required_skills_declarations = 0            inline_skill_reads = 17
```

**The roster diverges from the spec's projection, sharply, and the cause is
recorded rather than smoothed over.** The spec projected a post-phase corpus of
**35** (29 new across six disclosure specs + 6 existing). The measured corpus is
**14**. Five of the six specs were **closed unimplemented** after the pilot
(`2026-08-12-disclosure-implement-story`) measured ~1,017 bytes of per-skill
extraction overhead and a **+9.7%** worst-path ceiling regression; only the
pilot's 8 skills landed (6 + 8 = 14).

The spec's own correction to `2026-08-12-disclosure-ship`'s *"at least 29
skills"* stands as arithmetic — that figure reached 29 by counting `create-spec`
and `release` at +4 instead of +5 and omitting `verify-spec` — and is now moot
in fact, because neither roster shipped.

**The divergence does not touch the derivation, and that is the point.** The
derivation never reads the roster, so a corpus of 14, 35 or 50 produces the same
45. Had the phase delivered 50, the cap would have fired and the correct output
would have been a Tier B escalation, not a larger constant. A number that moves
with what shipped could not have said anything about what did not.

### Tasks 7.2 / 7.3 — `MAX_SKILLS = MAX_COMMANDS + MAX_AGENTS = 35 + 10 = 45`

Recorded at the constant: the derivation, its ADR-021 §4 rationale (a skill
exists only as a capability extracted from a **consumer**, so the skill
population is structurally bounded by the consumer population; one skill per
potential consumer is where extraction stops producing shared capability and
becomes a 1:1 shadow of the consumer surface), the date, the measured 14, the
31 of headroom, the counterfactual, and the warn-only decision with its revisit
condition.

Business Rule 8's three tests, with evidence:

| Test | Evidence |
|---|---|
| Computed from constants that exist for other reasons | `MAX_COMMANDS` and `MAX_AGENTS` are byte-identical to `HEAD`; the derivation never reads the roster |
| **It can still fire** | **it fires at 46.** ADR-021 §4 explicitly anticipates a second disclosure programme (`implement-spec` among its targets) |
| Moves only when its inputs move | and each input moves only by a deliberate edit to a named constant |

**The roster size at which this cap fires: 46.** Asserted, not asserted-about —
`test_the_cap_can_still_fire` calls `check_ceilings()` at `MAX_SKILLS + 1` and
requires the warning.

**Warn-only, stated because four other things in this spec became blocking.** A
count is not a unit of load — ADR-021's central finding, and Story 3 of this
same spec retires a 2000-line limit for exactly that reason. Three further
reasons, each independently sufficient: a blocking count cap would **block the
fix** (under conditional loading a skill on an untaken path costs that run
nothing, so extraction is the action that *lowers* per-invocation load); skill
bloat is already governed in **bytes** by ADR-019's per-surface ratchet with
schema-3 bound justifications, which is blocking and is the right unit; and the
`ceiling_bytes` budget that would supersede a count is deferred pending
post-disclosure data. Revisit condition recorded at the constant: if a
`ceiling_bytes` budget is ever adopted, this count cap becomes **redundant, not
stricter**.

### Task 7.4 — the rest of the ceiling block is untouched

`MAX_COMMANDS = 35` and `MAX_AGENTS = 10` byte-identical to `HEAD`;
`check_ceilings()`'s body byte-identical. Only `MAX_SKILLS`'s value and the
comment above it changed. Asserted by `test_the_sibling_ceilings_did_not_move`
and `test_max_skills_stays_warn_only`.

### The inline-read resolution check (scope change (c)(i))

`check_required_skills()` resolved `required_skills:` frontmatter only, and the
phase retired that field. **A mistyped `Read skills/tdd-cyle/SKILL.md` was a
silent no-op**: the gate passed, the skill never loaded, and the command quietly
ran without the capability. `measure-invocation.py` does report it under
`unresolved_skills`, but it always exits 0 by design and cannot gate.

The check now resolves **both** mechanisms and returns
`(findings, declarations, inline_reads)`. Design points:

- **The regex is byte-identical to `measure-invocation.py`'s `INLINE_READ`**,
  and `test_the_pattern_matches_measure_invocation_byte_for_byte` keeps it that
  way — the same "one accounting, two readers" rule Story 2 applies to
  `command_bytes`.
- **A literal `<name>` placeholder cannot match.** `commands/new-skill.md`
  teaches the form in two places; flagging the one command whose job is to
  document the convention would be a false finding, and false findings are how
  a channel gets ignored. Asserted by name.
- **Findings stay pinned `warnings`.** `system-instructions.md`'s
  graceful-degradation contract covers unresolvable skill names in *either*
  mechanism, and the pin outlives the flip.
- **`metrics.inline_skill_reads` sits beside the permanently-zero
  `required_skills_declarations`.** Read as a pair or neither means anything: 0
  eager declarations, 17 conditional reads, all resolving.

### Tasks 7.7 / 7.8 — the status correction and the restored trigger

`system-instructions.md`'s **Status: adopted** paragraph made three claims that
are now false — Phase 10 is not the first consumer, it does not need the
mechanism, and its extraction work lands **zero** declarations. Rewritten to
record that the named consumer **evaluated the mechanism and did not adopt it**,
with the measured reason (eager pre-load; selection is per *command*, never per
*run*; extraction moves bytes into the floor so a disclosed command costs more
per invocation than the monolith) and both sources cited (§ *Harness contract*
above it, and `adapters/claude-code.md`).

**The schema is byte-unchanged** — optional array, order preserved, duplicates
deduplicated, unknown names warn rather than hard-fail — and
`test_the_schema_and_the_graceful_degradation_rule_are_unchanged` asserts each
clause verbatim. Deprecation is ADR-scale and belongs to the review below.

**Review trigger restored: 2026-11-11**, terms *"no consumer by then →
deprecate; a consumer appears → record it and reset."* Restored rather than left
settled because the 2026-08-03 resolution was *revisit → adopt* on a
justification consisting almost entirely of a named future consumer, and that
consumer rejected the mechanism. A resolution whose premise turned out false
should not survive as a settled adoption. The date is aligned to ADR-021's own
review, which already reads the per-invocation load data that would justify a
consumer — two triggers, one reading.

### The three adapters (scope change (c)(ii))

`adapters/cursor.md`, `adapters/claude-code.md` and `adapters/openclaw.md`
carried the **identical** sentence. Each now records that the convention has no
consumer, why, that the phase loads skills inline instead, and the restored
2026-11-11 trigger. **Each adapter's description of the harness mechanism is
byte-unchanged** — the harness genuinely does pre-load declared skills before
the consumer's first phase, and that fact is what the escalation rested on.

```
$ grep -rn "first consumer" system-instructions.md adapters/ commands/ agents/
(no hits)
```

The only surviving occurrence is in `.writ/decision-records/adr-021-…md:131`,
where it is a *historical record that the claim became false* — it asserts the
opposite of a live consumer. It also says the correction is *"recorded there and
unassigned"*, which is now stale. **ADR-021 is not in this spec's file set and
was not edited; the stale sentence is recorded below as an open item.**

### Tasks 7.9 / 7.10 — the base-drift finding, observed on this story's own edit

```
$ python3 scripts/measure-invocation.py --root . --format json
base.bytes = 26258   system-instructions.md 21451 + commands/_preamble.md 4807
```

`system-instructions.md` grew 20,153 → 21,451 (+1,298), so the live base is
1,298 over the pinned budget. Observed output, verbatim:

```
WARNING [COMMAND_BYTE_BUDGET]: the pinned budget is 24960 bytes (2026-08-12:
system-instructions.md + commands/_preamble.md); the live base
(system-instructions.md + commands/_preamble.md) now measures 26258, a delta of
+1298. The budget is UNCHANGED — this is a report, not an adjustment.
Remediation: Re-derive COMMAND_BYTE_BUDGET deliberately and re-record it with
its components and a date, or shrink the base back. Never let the budget track
its own inputs: a self-raising ceiling is ADR-021 reason 3 in a new place.
```

**Observed, expected, and by design.** `COMMAND_BYTE_BUDGET` is **unchanged at
24,960.** Re-deriving mid-spec would move the number Story 4 certified against
and Story 6 proved bites, retroactively invalidating both; Business Rule 5's
*"deliberate, dated act"* means an act by somebody looking at the whole picture,
not an automatic adjustment by the story that happened to nudge the base. The
check firing on its own author's edit, in the run it shipped, is the strongest
demonstration available that it works.

### Task 7.11 — Story 4's gate re-run on the moved base

`ComplianceGateTests` — all seven assertions **still green**. The base moved,
the budget did not, and no certified figure was retroactively invalidated.

### Task 7.13 — baselines

- `surfaces.scripts.justifications.{lines,chars}` → 32,538 / 1,407,447
- `surfaces.system_instructions.justifications.chars` → 21,451 (**new entry** —
  the surface had none)
- `surfaces.adapters.justifications.chars` → 86,787 (**new entry**)

### Fallout from Story 5 found and fixed here

Two `scripts/tests/test_eval_leanness.sh` scenarios broke on consequences of
earlier stories, and both were repaired rather than muted:

- *"a decreased surface must not warn"* — every fixture root has a synthetic
  tiny `system-instructions.md`, so `check_budget_derivation()` correctly
  reports base drift there. The scenario now counts **ratchet** warnings only.
  Suppressing the derivation check on a small base would have been the wrong
  fix: it is exactly the check that must speak when the base moves.
- *"count ceilings stay warn-only"* — its 40 extra commands were bare
  `# Extra n` stubs, which earned their `structural: []` for free while the
  contract checks were non-blocking. Post-flip they are blocking findings, so
  the scenario would have asserted one thing and measured another. The fixtures
  are now contract-compliant.

### Open items recorded, not taken (outside the file set)

1. **`.writ/product/roadmap.md`** — Phase 10's criterion *"No command file
   exceeds **400 lines** without a tracked exemption"* names the demoted unit
   **and** an exemption path Business Rule 1 forbids for the budget. Needs an
   owner before Phase 10 closes.
2. **`.writ/decision-records/adr-021-…md:131`** — states the first-consumer
   correction is *"recorded there and unassigned."* It is now assigned and done
   (this story). One stale sentence in a file this spec does not own.
3. **The 400-line tripwire fires on nine commands, five of them fully
   byte-compliant** — Story 3's Tier B escalation, awaiting a maintainer
   decision.
4. **The byte cap is non-blocking and five commands are over budget by 39,829
   bytes** — it becomes blocking when a future decision converts those commands
   or lowers the base. Recorded against ADR-021's 2026-11-11 review.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `MAX_SKILLS = 45` with its derivation, date, measured count, headroom, and warn-only reasoning recorded at the constant
- [x] The roster size at which the cap would fire is stated — the derivation is a cap, not an accommodation
- [x] `MAX_COMMANDS`, `MAX_AGENTS`, and `check_ceilings()`'s body byte-identical to `HEAD`
- [x] `system-instructions.md`'s status paragraph corrected; schema unchanged; review trigger restored with a date and terms
- [x] New `base.bytes` and delta recorded; `COMMAND_BYTE_BUDGET` unchanged; `check_budget_derivation()`'s finding quoted as observed
- [x] Story 4's gate test re-run and still green
- [x] The three unedited adapter locations recorded as an open correction
- [x] Tests passing; `bash scripts/eval.sh` green end to end

## Context for Agents

- **Business rules:** [Rule 8 (`MAX_SKILLS` is re-derived from a rule, never fitted to a count — its three tests); Rule 5 (the budget is pinned and its derivation is itself checked — this story trips it deliberately); Rule 7 (adjacent constants stay untouched, applied here to `MAX_COMMANDS` / `MAX_AGENTS`)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [`MAX_SKILLS` — the measured roster, the derivation, the three tests, the counterfactual, and the warn-only decision with its revisit condition; The `required_skills:` status correction — what is false, what changes, and why the trigger is restored rather than left settled] — from spec.md → ## Detailed Requirements
- **Approved scope:** [the three obligations transferred here by the 2026-08-12 mechanism ruling; `MAX_SKILLS` was flagged by five sibling specs and could be taken by none of them] — from spec.md → ## Approved Scope Changes
- **Technical concerns:** [this spec causes its own base-drift finding and the disposition decided in advance; `required_skills_declarations` is now permanently 0; the same false claim exists in three adapters] — from spec.md → ## Technical Concerns

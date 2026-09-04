# Story 6: Adoption — Baseline at Initialize, Visibility at Status

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Story 2, Story 3

## User Story

**As a** developer adopting Writ on a codebase that already has years of quality debt
**I want** the first run to record what is already wrong instead of blocking on it, and my
project's own coverage floor written where the project enforces it
**So that** the checks are survivable on day one and the debt is visible and dated rather than
either invisible or paralyzing

## Acceptance Criteria

> **AC IDs assigned through:** AC-6.5

- [x] Given `/initialize` runs on a brownfield project with existing quality-config findings, when it completes, then `.writ/quality-baseline.md` exists recording each finding with the date and a rationale line, and those findings are acknowledged rather than blocking on subsequent runs. `[AC-6.1]`
- [x] Given a project with a coverage tool and measured coverage below the nominal bar, when `/initialize` writes a threshold, then the value written is the measured floor rather than 80% or any other aspiration, so the number can only ratchet upward and the first run after adoption does not break the project's build. `[AC-6.2]`
- [x] Given a finding not present in the baseline appears on a later run, when the check runs, then it is reported as new and blocks, and the baseline is not rewritten to absorb it automatically. `[AC-6.3]`
- [x] Given `/status` runs, when the quality-config findings are surfaced, then only pure file-read results appear — no build, test, or git-mutating command runs — satisfying `/status`'s third exit criterion, and the verdict uses the existing `Healthy` / `Warning` / `Attention` vocabulary rather than a fourth scheme. `[AC-6.4]`
- [x] Given a project with no findings, or one where `.writ/quality-baseline.md` is absent, when `/status` runs, then the section is omitted entirely rather than rendering an empty block — matching how Step 5's stale-issue block and Step 4's phase-health block already behave. `[AC-6.5]`

## Implementation Tasks

- [x] 6.1 Add the quality-config audit to `/initialize`'s brownfield Phase 3 Gap Analysis, where `ignoreBuildErrors` maps onto **Technical debt** and the existing prioritization principle — "lead with gaps that cause silent bugs" — already describes it `[AC-6.1]`
- [x] 6.2 Specify the `.writ/quality-baseline.md` write in `/initialize`, following Story 1's format, including the greenfield case where the baseline is empty by construction `[AC-6.1, AC-6.3]`
- [x] 6.3 Specify the coverage-floor write: measure current coverage, write `floor(measured)` into the project's coverage config, and record the value and date. Note that brownfield `/initialize` is otherwise read-only with respect to target-project config, so this write needs the same explicit confirmation the `.writ/config.md` write already carries `[AC-6.2]`
- [x] 6.4 Add the findings surface to `/status` Step 7 Project Health Signals as pure file reads, with the omit-if-empty behavior of Steps 4 and 5 `[AC-6.4, AC-6.5]`
- [x] 6.5 Confirm any suggested next action drawn from the findings uses only commands on `/status`'s allowlist — `/initialize` is on it; anything else must be plain English `[AC-6.4]`
- [x] 6.6 Extend `scripts/eval.sh`'s `check_quality_config_audit()` with `require_literal` bindings asserting the `/initialize` and `/status` wiring prose, following how `check_ac_trace` binds `verify-spec.md`'s Check 3e/3f `[AC-6.1, AC-6.4]`
- [x] 6.7 Verify `bash scripts/eval.sh` passes and `/status`'s no-build-no-test exit criterion still holds by inspection `[AC-6.4]`

## Notes

**Technical considerations:** `/status`'s third exit criterion is a hard constraint, not a
preference: *"every execution state file under `.writ/state/` was read without being written,
and no build, test or git-mutating command ran"*, restated as a terminal constraint at
`commands/status.md:477`. Only the config audit — pure file reads — may appear there.
Coverage re-derivation and build smoke run tooling and must not.

`/status` already has a categorical health verdict worth matching rather than duplicating:
`scripts/phase-state.py health` renders `Healthy` / `Warning` / `Attention`, where missing or
stale evidence is a Warning ("never a silent pass") and `Attention` requires an affirmative
current failure. That is the same trichotomy this spec calls `pass` / `unverifiable` / `fail`.

`/initialize`'s asymmetry matters for task 6.3: greenfield writes real project config
unconditionally, while brownfield is read-only with respect to target-project config and asks
before writing even `.writ/config.md`. Writing a coverage threshold into an existing project is
a brownfield mutation and should carry at least the same confirmation.

**Risks:** The baseline is the mechanism that makes adoption survivable and also the mechanism
most likely to hollow the whole spec out. A baseline that grows on each run is a disabled
check. Make re-baselining a deliberate, dated, human act — and consider whether the baseline
should record a count that can only decrease.

Second risk: `/status` is meant to orient in under ten seconds. A findings block that lists
forty baselined items defeats the command. Surface the count and the new findings; leave the
enumeration to the baseline file.

**Integration:** `.writ/config.md` already carries `**Test Coverage Tool:** jest --coverage`
(see `commands/initialize.md:106` and `.writ/docs/config-format.md`), which is the natural
anchor for coverage-tool detection — no new artifact needed for that half. The baseline is a
new artifact and does need Story 1's format.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** baseline-then-ratchet, coverage thresholds at the measured floor, the
  `/status` read-only constraint, verdict vocabulary alignment — from `spec.md` →
  `## 📋 Business Rules` and `## Implementation Approach`
- **Shadow paths:** Read baseline (absent → empty, every finding new), Read baseline
  (malformed → exit 2, never ignored) — from `sub-specs/technical-spec.md` →
  `## Error & Rescue Map`
- **Insertion points:** `/initialize` brownfield Phase 3 Gap Analysis; `/status` Step 7
  Project Health Signals; the omit-if-empty precedent in `/status` Steps 4 and 5
- **Precedent to mirror:** `check_ac_trace`'s `require_literal` bindings against
  `commands/verify-spec.md` for asserting command-file wiring prose

---

## What Was Built

**Implementation Date:** 2026-08-14

### Files Created

None.

### Files Modified

- **`commands/initialize.md`** (Phase 3 Gap Analysis)
  - Runs the quality-config audit and folds findings into **Technical debt**,
    where the existing prioritization principle — "lead with gaps that cause
    silent bugs" — already describes them
  - Specifies the `.writ/quality-baseline.md` write against Story 1's format,
    including the greenfield empty case, with the no-auto-re-baseline
    prohibition stated inline
  - Specifies the coverage-floor write at `floor(measured)`, carrying the same
    explicit confirmation the `.writ/config.md` write already does
- **`commands/status.md`** (Step 7 Project Health Signals, Step 9 next actions)
  - One health line using the existing `Healthy` / `Warning` / `Attention`
    vocabulary, with the count of non-baselined findings and the newest code
  - Omit-if-empty behaviour matching Steps 4 and 5
  - Two next-action rows, both drawing only on the command allowlist
- **`scripts/eval.sh`** (`check_quality_config_audit()`)
  - Eight `require_literal` bindings asserting the `/initialize` and `/status`
    wiring prose, plus two `forbid_literal` guards
- **`.writ/leanness-baseline.json`** — commands and scripts justifications
  updated to the post-Story-6 values with the increment described
- **`scripts/tests/test_governor_enforcement.py`** — the per-command byte
  ratchet updated with a dated, disclosed reason (see Deviations)

### Implementation Decisions

1. **Only the pure file-read checker appears in `/status`, and that is
   enforced.** `/status`'s third exit criterion promises "no build, test or
   git-mutating command ran". `quality-config-audit.py` satisfies it — it has
   no `import subprocess` at all, already asserted by `forbid_literal`. The two
   checkers that execute tooling are kept out by two new `forbid_literal`
   guards against `status.md`, so a future edit that helpfully adds coverage
   re-derivation to `/status` fails eval rather than quietly breaching the
   criterion.
2. **The health line reuses the existing vocabulary rather than inventing a
   fourth.** `pass` / `unverifiable` / `fail` maps onto `Healthy` / `Warning` /
   `Attention` exactly, which is already what `scripts/phase-state.py health`
   renders and what Step 4 displays.
3. **The count is surfaced, the enumeration is not.** `/status` is meant to
   orient in under ten seconds; a block listing forty baselined items defeats
   it. The line carries the new-finding count, the baselined count, and one
   code — the baseline file holds the rest.
4. **The rationale is asked for, not generated.** `/initialize` prompts the
   developer for each baseline entry's reason rather than writing one. An entry
   nobody wrote is an entry nobody will retire, and the baseline's whole value
   is that its count should only decrease.
5. **The coverage-floor write is confirmed, because it mutates target-project
   config.** Brownfield `/initialize` is otherwise read-only with respect to the
   target project's own configuration and asks before writing even
   `.writ/config.md`; writing a threshold into `jest.config.js` is a strictly
   larger mutation and carries at least the same confirmation.

### Test Results

**Verification:** Automated (static) — command prose; executable protection is
`scripts/eval.sh`.

- ✅ `bash scripts/eval.sh` — **0 findings, 0 run errors**
- ✅ `python3 -m unittest discover -s scripts/tests` — **666 tests, OK** (1 skipped)
- ✅ Baseline write, dated-rationale requirement and no-auto-re-baseline
  prohibition specified against Story 1's format `[AC-6.1, AC-6.3]`
- ✅ Coverage floor written at `floor(measured)`, never the aspiration `[AC-6.2]`
- ✅ `/status` surfaces only pure file-read results, in the existing
  `Healthy`/`Warning`/`Attention` vocabulary; the two tooling-executing checkers
  are forbidden there by `forbid_literal` `[AC-6.4]`
- ✅ Section omitted entirely when there are no findings, when the baseline is
  absent, or on `unsupported_stack` `[AC-6.5]`
- ✅ Suggested next actions use only allowlisted commands (`/initialize`); the
  other row is plain English `[AC-6.4]`
- ✅ `/status`'s no-build-no-test exit criterion holds by inspection — the only
  command added is a checker with no subprocess capability at all `[AC-6.4]`

**Coverage:** N/A — no executable code added by this story.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** Small — one ratchet increment, recorded below
- **Security:** Clean. The `/status` addition is the notable one and it is
  strictly read-only; the guard against regressing that is committed, not
  merely stated.
- **Boundary Compliance:** Touched exactly the files the story names, plus the
  two ratchet files the growth required.

### Deviations from Spec

- **[DEV-005] The per-command byte ratchet needed a disclosed increment** — Severity: Small
  - Spec said: the technical spec's *Byte Budget* section budgeted for
    `.writ/leanness-baseline.json` and noted `implement-story.md` was already
    735 bytes over `COMMAND_BYTE_BUDGET`
  - Reality: a second, separate ratchet exists —
    `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py`, a
    one-way gate where "a new name, or a larger overage on a recorded one,
    fails". Story 5's Gate 2/4 wiring took `implement-story.md` from 735 to
    2730 bytes over, and this fired.
  - Resolution: recorded the increment with a dated, disclosed reason following
    the four precedents already in that file. Acknowledged, not exempted —
    `eval.sh`'s leanness warning still reports the overage.
  - Spec amendment: none required. Worth noting for future specs that the
    technical spec named only one of the two byte ratchets, and that this one is
    **not wired into `eval.sh` or CI** — its own comment says so, and it caught
    this only because the full unit suite was run by hand.

### Lessons Learned

1. **A `forbid_literal` was the right shape for `/status`'s hardest
   constraint.** The exit criterion promises a negative — that no build or test
   command ran — and a negative cannot be demonstrated by adding prose. Two
   `forbid_literal` guards make the specific, plausible future mistake (adding
   coverage re-derivation to the health block because it seems useful there)
   fail eval instead of silently breaking a published guarantee.
2. **The second ratchet was found by running everything, not by reading the
   spec.** `eval.sh` was green the whole time; the byte gate lives in a unit
   test that CI does not run. Its own comment predicted this — "caught all three
   only because it was run by hand" — and it happened again here.
3. **This spec's own instruments would flag this repository.** Writ has no jest
   config and no `next.config.js`, so `quality-config-audit` reports
   `unsupported_stack` against it — an honest `unverifiable` rather than a
   flattering pass, which is the behaviour the classification doc's stack matrix
   requires and a small live demonstration that the degradation path works.

### Next Story

None — this completes the spec.

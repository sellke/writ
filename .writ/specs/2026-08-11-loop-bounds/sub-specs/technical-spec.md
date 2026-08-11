# Technical Spec: Loop Bounds

> Source: `.writ/specs/2026-08-11-loop-bounds/spec.md`

## Current State (verified 2026-08-11)

| Fact | Verification |
|---|---|
| 32/32 commands carry `---` frontmatter with exactly `name:` and `description:` | `for f in commands/*.md; do awk '/^---$/{n++;next} n==1{print}' "$f" \| grep -oE '^[a-z_]+:'; done \| sort \| uniq -c` → `32 description:`, `32 name:` |
| Line counts | `implement-phase` 302, `implement-spec` 264, `implement-story` 961, `refactor` 191, `verify-spec` 711 |
| No `loop:`, `max_iterations`, or `on_exhaustion` token exists anywhere in the repo | repo-wide grep, zero hits |
| `phase-state.py` subcommands | `init, create-lane, validate-result, validate-challenge, record-challenge, resolve-challenge, integrate, set-dependencies, classify, retry, quarantine, reconcile, knowledge-writeback, progress, health, show` |
| `eval.sh check_length` limits | `spec-lite.md` 100, `commands/_preamble.md` 80, command files 2000 |

## Re-verification at implementation (2026-08-11)

Tasks 2.1, 3.2, and 4.1 require re-deriving the calibration evidence before any number is written. Doing so moved three of the authored figures. **No declared bound changed** — every correction moved the evidence, not the number, and each corrected value is still comfortably under its bound.

| Authored claim | Re-measured | Effect on the bound |
|---|---|---|
| Largest phase observed = 4 specs (Phase 7, roadmap-attested, no state file) | `.writ/state/phase-execution-20260811-2030.json` (Phase 10, in flight) has `specOrder` length **5** — the largest phase with a surviving state file | None. 12 > 5. The `implement-phase` citation names this run instead of claiming "largest observed = 4" |
| 42 `Iteration count` records: 38 at 1, 4 at 2 | 42 records: **39 at 1, 3 at 2**. A 43rd `iteration counts` match is an acceptance-criteria sentence in an archived `/ralph` story, not a record | None. Max observed is still **2**, so 3 keeps one iteration of headroom |
| Source line numbers (`implement-story.md:595`/`:732`, `agents/*-agent.md:232`/`:225`, `refactor.md:100`, `verify-spec.md:698`) | All shifted by +6 when `2026-08-11-component-contract` added `problem:`/`outcome:`/`exit_criteria:` — now `:601`/`:738`, `:238`/`:231`, `:106`, `:704` | None. Citations quote the **anchor text** rather than depending on a line offset, and the eval check greps content, never line numbers |

Confirmed unchanged: largest story count across the 41 archived specs is **9** (`2026-03-19-command-suite-evolution`); the three `.writ/state/execution-*.json` runs are 4 stories each; `stories_total` across the recorded result files is 4 / 4 / 3; `/refactor` still has **zero** recorded runs anywhere in `.writ/state/`; `commands/verify-spec.md` still contains no re-check step.

## The existing retry rule this spec must compose with

`scripts/phase-state.py` already owns the only *enforced* loop bound in Writ:

```python
def cmd_classify(args):
    attempts = record.get("attempts", 0)
    if classification == "transient" and attempts < 2:
        return {"action": "retry", "attempts": attempts}
    return {"action": "quarantine", "attempts": attempts,
            "classification": classification or "terminal"}

def cmd_retry(args):
    if record.get("attempts", 0) >= 2:
        raise ContractError("retry_exhausted",
                            f"{args.spec} already used its permitted retry")
```

`attempts` starts at `0` in `cmd_init`, is incremented to `1` by `cmd_create_lane` on first launch, and to `2` by `cmd_retry`. The effective budget is therefore **two attempts: one initial plus one transient retry.**

Three consequences bind this spec:

1. `on_exhaustion` cannot include `retry`. Retry is the *pre-exhaustion* state; adding it to the vocabulary would create a second, weaker retry authority in prose that contradicts an enforced one in code.
2. `implement-phase`'s nested `spec_attempt` bound must be **2**, not 1 and not 3. Any other number falsifies the file against the code.
3. `on_exhaustion: quarantine` must shell out to `scripts/phase-state.py quarantine --spec <id> ...`, which already removes the worktree, renames the lane to `writ/quarantine/{spec-id}` (with a deterministic numeric suffix on collision via `_quarantine_name`), verifies `phaseBranchClean` by comparing phase-branch HEAD before and after, records `failure.summary` + `failure.attempts`, appends `quarantine:{branch}` to `evidence`, and marks every transitive dependent `skipped_blocked` with `blockedBy`. That is already a named, resumable state — Business Rule 3 is satisfied for this verb by reuse, not by new code.

## Schema

### Block shape

```yaml
---
name: implement-phase
description: "..."
problem: "..."                  # owned by 2026-08-11-component-contract
outcome: "..."                  # owned by 2026-08-11-component-contract
exit_criteria:                  # owned by 2026-08-11-component-contract
  - "..."
loop:                           # owned by THIS spec
  unit: "spec"
  max_iterations: 12
  on_exhaustion: halt_reported
  calibrated_against: "..."
  nested:
    - unit: "spec_attempt"
      max_iterations: 2
      on_exhaustion: quarantine
      calibrated_against: "..."
---
```

### Key contract

| Key | Type | Required | Rule |
|---|---|---|---|
| `loop.unit` | string | yes | Singular snake_case noun naming what one iteration counts. Must be distinct from every other `unit` within the same file, including `nested` entries. |
| `loop.max_iterations` | positive integer | yes | Literal integer. Not a range, not `null`, not a string, not an expression. |
| `loop.on_exhaustion` | enum | yes | Exactly one of `quarantine`, `escalate`, `halt_reported`. |
| `loop.calibrated_against` | string | yes | Non-empty. Must contain either a path (`.writ/state/...`, `.writ/specs/...`, `commands/...`, `agents/...`, `scripts/...`) or the literal phrase `no recorded run`. Must state evidence quality. |
| `loop.nested` | list | no | Zero or more entries carrying the same four keys with the same rules. Absent for single-loop commands. |

`nested` exists solely because `/implement-story` carries three distinct enforced caps. It is not a general nesting mechanism and is capped at one level — a nested entry may not itself carry `nested`.

### Why a mapping with optional `nested`, not a list of loops

A bare list (`loop: [ {...}, {...} ]`) would make `loop.max_iterations` unaddressable, breaking both the locked contract's literal wording and the roadmap success criterion *"All 5 loop-bearing commands declare `loop.max_iterations` + `on_exhaustion`"*. A mapping keeps the primary loop at the documented path and pushes multiplicity into an optional key that four of the five commands never use.

### `unit` vs. the roadmap's `loop.bound` — one design, two names

The roadmap feature line names three fields: `loop.bound` / `max_iterations` / `on_exhaustion`. This schema names them `unit` / `max_iterations` / `on_exhaustion`. `unit` **is** what that line called `bound` — the thing being counted, not the number counting it. The rename is deliberate: "bound" reads as the limit, and the limit is `max_iterations`. There is no fourth field and no second design; a reader holding the roadmap and this schema side by side is looking at the same three keys.

### `on_exhaustion`: the closed vocabulary and its output contract

Exactly three values are legal. The set is closed — a fourth value is a schema violation, not an extension point.

| Value | Behavior | Legal where | Required output |
|---|---|---|---|
| `quarantine` | Invokes `scripts/phase-state.py quarantine` for the unit — removes the lane worktree, preserves the lane as `writ/quarantine/{spec-id}`, proves the phase branch clean of it, records failure evidence + attempt count + recovery command, marks transitive dependents `skipped_blocked` with `blockedBy`. Adds no new disposition path, no new state field, no new branch-naming rule. | Only on a unit that has a `phase-execution-*.json` record. In this spec that is `implement-phase`'s nested `spec_attempt` and nothing else. | Whatever `phase-state.py quarantine` already writes. Business Rule 3 is satisfied here by reuse, not by new code. |
| `escalate` | Pauses and presents one bounded `AskQuestion` — the shape `/implement-story` already uses at Gate 1, Gate 4, and the review-loop cap for `STATUS: BLOCKED`. | Anywhere. **Mandatory** wherever continuing past the bound would change scope (Business Rule 5). | `unit`, declared bound, count reached, last completed unit, partial state, and the resume command, all named in the prompt. |
| `halt_reported` | Stops without asking and writes a named terminal record into a durable artifact that already exists. | Anywhere a durable state file or report section exists to write into. | `unit`, declared bound, count reached, last completed unit, and a **literal** resume command. |

**Why `retry` is excluded.** Retry is the *pre-exhaustion* state, and it is already governed — in code, not prose — by `scripts/phase-state.py`'s `attempts < 2` guard. Admitting `retry` as an `on_exhaustion` value would create a second, weaker retry authority in markdown that contradicts an enforced one in Python. `on_exhaustion` fires only once the retry budget is spent.

**Why no "continue anyway" value.** A value meaning "note the bound and keep going" makes every bound advisory and deletes the reason the key exists. If a loop genuinely needs to run past its bound, the bound is wrong: raise the number and cite the run that justified it (Business Rule 1). That is the ratchet working, not failing.

**No exhaustion path may terminate silently.** All three values produce a named, resumable state. A loop that stops without writing that record has failed this spec even if it stopped at the correct iteration.

### Append-only within the ADR-020 block

`loop:` is a sibling key to `problem:` / `outcome:` / `exit_criteria:` inside the same `---` block, appended after them. This spec does not define, reorder, rename, or validate those three keys, introduces no second frontmatter block, and adds no sidecar file. Validation of `loop:` is identical whether the ADR-020 keys are present or absent, so the two specs may land in either order.

### Fixture set (Story 1 → consumed one-for-one by Story 5)

Each fixture is a `loop:` block plus the verdict the checker must return. Story 5 implements exactly these and invents none.

| Fixture | Block | Expected verdict |
|---|---|---|
| `valid-minimal` | `unit`, `max_iterations`, `on_exhaustion`, `calibrated_against`, no `nested` | accepted |
| `valid-nested` | above plus one `nested` entry with all four keys | accepted |
| `no-loop-block` | frontmatter with no `loop:` key at all | **skipped** as `deferred_to_check3` — never a finding |
| `missing-unit` | `unit` omitted | rejected, naming `unit` |
| `missing-max-iterations` | `max_iterations` omitted | rejected, naming `max_iterations` |
| `missing-on-exhaustion` | `on_exhaustion` omitted | rejected, naming `on_exhaustion` |
| `missing-calibrated-against` | `calibrated_against` omitted | rejected, naming `calibrated_against` |
| `on-exhaustion-retry` | `on_exhaustion: retry` | rejected, **naming `retry` and the reason**: retry is pre-exhaustion, governed by `phase-state.py`'s `attempts < 2` |
| `on-exhaustion-out-of-set` | `on_exhaustion: continue_anyway` | rejected, naming the value and the legal set |
| `max-iterations-string` | `max_iterations: "twelve"` | rejected — not a positive integer literal |
| `max-iterations-range` | `max_iterations: 3-5` | rejected — not a positive integer literal |
| `max-iterations-zero` | `max_iterations: 0` | rejected — not *positive* |
| `duplicate-unit` | primary `unit: story` and a nested `unit: story` | rejected, naming the duplicated unit |
| `nested-in-nested` | a `nested` entry that itself carries `nested` | rejected — one level only |
| `loop-not-a-mapping` | `loop: 12` | rejected — `loop:` must be a mapping |
| `nested-missing-key` | a `nested` entry omitting `calibrated_against` | rejected — nested entries carry the same four required keys |
| `citation-no-path` | `calibrated_against: "seemed about right"` | rejected — needs a path token or the literal `no recorded run` |
| `quarantine-without-phase-state` | `on_exhaustion: quarantine` on `implement-story` / `refactor` / `verify-spec` | rejected — no `phase-execution-*.json` record exists for that unit |
| `bound-below-history` | `implement-spec` declaring `max_iterations: 2` against a fixture state file recording 4 stories | rejected, naming the state file and the recorded value |
| `empty-state-dir` | a state directory containing no run files | **skipped** with a stated reason — never a silent pass |
| `no-adr020-keys` | `loop:` present, `problem:`/`outcome:`/`exit_criteria:` absent | accepted — validation is independent of the sibling spec |

## Per-command application

### `commands/implement-phase.md` (Story 2)

Primary loop is Phase 3 → Step 3.2 *Per-Spec Iteration*: one iteration = one lane created, one subagent run, one result validated, one merge-or-dispose.

```yaml
loop:
  unit: "spec"
  max_iterations: 12
  on_exhaustion: halt_reported
  calibrated_against: ".writ/state/phase-execution-20260719-121255.json (Phase 9: 3 specs, all attempts=1); roadmap Phase 7 (4 specs, no surviving state file); Phase 10 planned = 6 features. Largest observed = 4; bound is 3x. Evidence: thin (two runs)."
  nested:
    - unit: "spec_attempt"
      max_iterations: 2
      on_exhaustion: quarantine
      calibrated_against: "scripts/phase-state.py cmd_classify (attempts < 2) and cmd_retry (retry_exhausted at >= 2) — transcription of enforced code, not a new number."
```

`halt_reported` for the outer loop is deliberate and is **not** a quarantine. Nothing has failed at outer-loop exhaustion — the phase simply ran longer than declared. Quarantining an unstarted spec would fabricate a failure record and, worse, mark its dependents `skipped_blocked`, which is a scope degradation forbidden by Business Rule 5. The correct terminal state already exists: unstarted specs stay `pending`, `phase-execution-*.json` stays at `status: executing`, and `--resume` + `reconcile` recovers exactly. The report must name the file path and the literal `/implement-phase --resume` command.

Prose edit accompanying the frontmatter: Step 3.2's numbered list gains one sentence stating the bound and pointing at `on_exhaustion`. Step 3.3 item 1 (*"Writ permits exactly one transient retry"*) is **not** edited — it is the source the nested entry transcribes.

### `commands/implement-spec.md` (Story 2)

Primary loop is the per-story dispatch across the batched execution plan. One iteration = one `/implement-story` call.

```yaml
loop:
  unit: "story"
  max_iterations: 12
  on_exhaustion: halt_reported
  calibrated_against: "Max stories in any of 41 archived specs = 9 (2026-03-19-command-suite-evolution). Recorded runs: .writ/state/execution-20260718-1101.json = 4, execution-20260803T193200Z.json = 4, execution-20260804205617.json = 4; Phase 9 spec results = 4/4/3. Bound = all-time max + 3. Evidence: strongest of the five."
```

Note the interaction with `implement-spec.md:170`: *"On story failure: Present remaining issues and offer: retry, skip..., or abort."* That retry is **human-selected and currently unbounded** — a user may choose retry indefinitely. This spec does not bound a human's choices; `max_iterations` counts stories dispatched, not user-elected retries. If a future change makes that retry autonomous, it acquires a `nested` entry with `on_exhaustion: escalate`. State this explicitly in the story so it is not silently conflated.

`halt_reported` writes to the existing per-spec execution state file (`.writ/state/execution-*.json`), whose `stories.{id}.status` / `phase` fields already carry the resume position, and names `/implement-spec --resume`.

### `commands/implement-story.md` (Story 3)

Three enforced caps, one primary and two nested. All three numbers are transcriptions.

```yaml
loop:
  unit: "review_cycle"
  max_iterations: 3
  on_exhaustion: escalate
  calibrated_against: "commands/implement-story.md:595 (existing prose cap). 42 'Iteration count' records across archived story What-Was-Built sections: 38 at 1, 4 at 2; max observed = 2. Evidence: strong."
  nested:
    - unit: "testing_cycle"
      max_iterations: 2
      on_exhaustion: escalate
      calibrated_against: "commands/implement-story.md:732 (existing prose cap). No recorded run reports a testing-fix iteration above 1. Evidence: adequate — transcription; the original 2 has no recorded derivation."
    - unit: "agent_self_fix"
      max_iterations: 3
      on_exhaustion: escalate
      calibrated_against: "MAX_SELF_FIX_ITERATIONS = 3 in agents/coding-agent.md:232 and agents/testing-agent.md:225, consumed at implement-story.md:513/734/942. Evidence: strong — two agents already enforce it."
```

All three are `escalate` because `implement-story.md:940–942` already escalates at each cap with an `AskQuestion` offering retry / manual intervention / skip. `halt_reported` would be a behavioral regression; `quarantine` is illegal here because no `phase-execution-*.json` record exists for a story.

The `review_cycle` counter is shared across Gate 3 FAIL, Gate 3.5 Reject, Gate 3.5 Modify-spec, and Gate 4.5 FAIL — four increment sites, one counter (`implement-story.md:595`, `:774`). The frontmatter must not imply four separate budgets.

The 4 recorded 2-iteration outcomes are why 2 is rejected: a bound of 2 sits exactly at the observed maximum with zero headroom, so the next story like those four would trip it. Business Rule 2 forbids a bound below the observed max; setting one *at* the observed max is technically legal and still wrong here.

### `commands/refactor.md` (Story 4)

Primary loop is Phase 3 execution over the approved risk-ranked plan, delegating each iteration to `skills/safe-refactor-loop/SKILL.md`. One iteration = checkpoint → apply → verify → commit-or-revert.

```yaml
loop:
  unit: "change"
  max_iterations: 10
  on_exhaustion: halt_reported
  calibrated_against: "No recorded run — zero /refactor executions exist in .writ/state/. Sole anchor: commands/refactor.md:100 recommends splitting plans of 7+ changes into sessions; 10 sits above that advisory so the bound never fires before the existing advice. Evidence: weak. Recalibrate after the first recorded run."
```

The exhaustion state is unusually cheap here and that should be said plainly: `safe-refactor-loop` commits one green, single-concern, independently revertable commit per iteration, so the partial state at exhaustion is already a clean commit series with a green tree. `halt_reported` re-presents the remaining plan — which the command already does on mid-plan failure (`refactor.md:124`) — and names the commits landed so far.

**Do not** add a retry bound here. `safe-refactor-loop` step 1 reverts a red change immediately and never retries it; inventing a retry budget would contradict the skill.

### `commands/verify-spec.md` (Story 4)

```yaml
loop:
  unit: "autofix_pass"
  max_iterations: 1
  on_exhaustion: halt_reported
  calibrated_against: "Single-pass by construction: Phase 3 (checks 1-8) -> Phase 4 (fixes 4.1-4.4) -> Phase 5 (report), with no re-check step in commands/verify-spec.md. Declaring 1 codifies existing behavior and can break no recorded run. Evidence: strong by construction; no /verify-spec runaway has ever been observed."
```

`on_exhaustion` fires when a fix applied in Phase 4 would itself require re-running Phase 3 to confirm — today an unreachable branch. It reports the finding as unresolved in the existing Phase 5 verification report and names `/verify-spec` as the resume command. The `--product` mode's Check P3 regeneration is the same single pass and needs no separate entry.

## The eval check (Story 5)

New `scripts/eval-loop-bounds.py`, wired as `bash scripts/eval.sh --check=loop-bounds`, mirroring the existing `eval-*.py` one-JSON-object contract.

### Boundary with `2026-08-11-governor-instrumentation`

That spec's **Check 3** already asserts that the same five commands declare `loop.max_iterations` and `loop.on_exhaustion` (expected findings today: 10), with the five-command list as a named constant in `eval-leanness.py`. It explicitly defers the field shape to this spec.

The split is **presence vs. correctness**:

- **Check 3 owns presence.** Is a `loop:` block there at all, with the two contract-named keys?
- **`eval-loop-bounds.py` owns correctness.** Given a block exists, is it well-formed, legally valued, honestly cited, and calibrated against reality?

`eval-loop-bounds.py` therefore **skips any file with no `loop:` block** and reports it as `deferred_to_check3` rather than duplicating the finding. A maintainer must never see the same missing block reported twice by two checks — that is how a check registry becomes noise. If the governor spec has not landed, this check still runs; it simply has fewer files to inspect.

### Assertions (correctness only)

1. `unit`, `calibrated_against` present alongside the two contract-named keys, at the top level of `loop:` and in every `nested` entry.
2. `max_iterations` parses as a positive integer literal — not a range, string, or expression.
3. `on_exhaustion` ∈ {`quarantine`, `escalate`, `halt_reported`}. `retry` is called out by name in the failure message as illegal, with the reason.
4. `calibrated_against` is non-empty and contains a path-shaped token or the literal `no recorded run`.
5. `unit` values are unique within a file; `nested` does not itself contain `nested`.
6. `on_exhaustion: quarantine` appears only on a unit with a `phase-execution-*.json` record — rejected on `implement-story`, `refactor`, `verify-spec`.
7. **Historical-run regression assertion.** For the two units with machine-readable history, the declared bound is compared against recorded reality: `implement-phase.unit=spec` against `len(specOrder)` in every `.writ/state/phase-execution-*.json`; `implement-spec.unit=story` against `len(stories)` in every `.writ/state/execution-*.json` and `stories_total` in every `phase*result*.json`. A declared bound below any recorded value is a finding naming the file and the value.
8. **Transcription drift assertions.** `implement-phase`'s `spec_attempt` bound is cross-read from `scripts/phase-state.py`'s `attempts < 2` guard; `implement-story`'s three numbers from `implement-story.md:595`/`:732` and `agents/*-agent.md`'s `MAX_SELF_FIX_ITERATIONS`; plus a grep guard asserting `commands/verify-spec.md` still contains no re-check step, and an assertion that `refactor`'s `calibrated_against` still contains the literal `no recorded run`. None of these values may be hardcoded in the check.

Assertions 7 and 8 are the mechanization of Business Rules 2 and 7, and are this check's reason to exist. Presence checking alone — all Check 3 can offer — would let a mis-calibrated bound ship green.

`.writ/state/` is gitignored, so assertion 7 must skip cleanly with a `skipped: no recorded runs available` note in CI rather than fail. It binds on a maintainer's working copy, where the history exists. Say this in the check's own output; a check that silently passes because its input is absent is exactly the failure mode ADR-020 diagnosed.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Parse `loop:` from frontmatter | Malformed YAML, `loop:` present but not a mapping, `max_iterations` a string or range | Blocking finding naming the file and the offending key; never a default-and-continue | Fixture command files with each malformation |
| Declared bound below recorded history | A maintainer lowers a bound after a large run landed | Assertion 7 fails with the recorded file and value; the bound is corrected, never exempted | Fixture `.writ/state/` with a run larger than the declared bound |
| `.writ/state/` empty (fresh clone, CI) | Assertion 7 has no input | Skip with an explicit `skipped` reason in output — never a silent pass | Run the check against a temp dir with no state files |
| `on_exhaustion: quarantine` invoked outside a phase | No `phase-execution-*.json` record for the unit | Illegal by schema; the check rejects `quarantine` on any command with no phase-state integration. At runtime, fall back to `escalate` and say why | Assert the check rejects `quarantine` on `implement-story` / `refactor` / `verify-spec` |
| `phase-state.py quarantine` rename fails | Branch name collision beyond the deterministic suffix, git error | Already handled: returns `attention_required` with `quarantine_rename_failed` and leaves the phase branch untouched. This spec adds nothing | Existing `phase-state.py` coverage |
| `loop:` and `problem:`/`outcome:`/`exit_criteria:` land out of order | The component-contract spec has not merged yet | `loop:` is appended to whatever block exists; neither spec's check may assume the other's keys are present | Fixture with `loop:` and no ADR-020 keys, and the reverse |
| Progressive disclosure restructures `implement-story` | ADR-021 work splits the 961-line file | Frontmatter survives file-body restructuring by construction; the check reads frontmatter only, never body line numbers | Assert the check passes against a stub command body |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| `eval-loop-bounds.py` | All five files declare a valid, calibrated `loop:` → 0 findings | A named command file is missing → finding naming the absent file, not a crash | `.writ/state/` has no run files → assertion 7 reports `skipped` with reason | Frontmatter unparseable → finding naming the file and the parse error |
| Runtime exhaustion | Bound reached → named record written → resume command printed | No state file to write into → `escalate` instead, and say why | Zero iterations run (empty spec list) → not an exhaustion; report normally | `phase-state.py quarantine` returns `attention_required` → surface it verbatim, never retry the rename |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| A phase legitimately has more than 12 specs | The bound trips and `halt_reported` fires with a resume command; the maintainer resumes. Cost is one recovery cycle, not lost work. If this happens once, raise the bound with the run as evidence — that is Business Rule 1 working, not failing |
| `/implement-phase --all` chains phases | `max_iterations` counts specs **per phase**, not across a chained `--all` run. The counter resets at each phase boundary. State this in the frontmatter's `unit` semantics or the bound is meaningless in `--all` mode |
| A spec's transient retry consumes an outer-loop iteration | It must not. A retried spec is the same iteration of the `spec` loop; only lanes for *distinct* specs increment the outer counter. The nested `spec_attempt` bound covers retries |
| `/implement-story` invoked directly, outside `/implement-spec` | All three `implement-story` bounds are `escalate`, which requires no phase state — unaffected |
| `--quick` mode skips gates | Skipped gates cannot increment a counter they never reach. No separate bound; `--quick` simply exhausts more slowly |
| A sixth command acquires a loop | The eval check's named-command list is the enforcement point and must be updated with it. Out of scope for this spec, in scope for the check's docstring to say so |

## Testing Strategy

- **Story 1:** Fixture frontmatter blocks — valid, missing each required key, illegal `on_exhaustion` (including `retry` specifically), non-integer `max_iterations`, duplicate `unit`, `nested` inside `nested`. Assert the schema doc's stated rules match the fixtures one-for-one.
- **Story 2:** Assert the two orchestrator files parse; assert `implement-phase`'s nested `spec_attempt` equals the `attempts < 2` guard read from `scripts/phase-state.py`; assert `implement-spec`'s bound ≥ the largest `stories_total` in every recorded state file.
- **Story 3:** Assert all three `implement-story` numbers equal their sources — `:595`, `:732`, and `agents/*-agent.md`'s `MAX_SELF_FIX_ITERATIONS = 3` — so a future edit to either side is caught as drift.
- **Story 4:** Assert `verify-spec`'s bound is 1 and that `commands/verify-spec.md` still contains no re-check step (a grep-based guard — if a re-check is ever added, the bound must be revisited). Assert `refactor`'s `calibrated_against` contains the literal `no recorded run`, so the weak evidence cannot be quietly upgraded without an edit.
- **Story 5:** All eight assertions against fixture repos, plus the empty-`.writ/state/` skip path and the out-of-order-landing path from the Error map.

## Non-Goals (restated from spec.md → Out of Scope)

No change to any existing enforced number. No new failure-handling machinery. No bounds on the other 26 commands. No ownership of the generic blocking-`structural` classification (roadmap Phase 10 "Make the governor bite"). No ownership of `problem:` / `outcome:` / `exit_criteria:`. No participation in progressive disclosure. No runtime iteration interpreter.

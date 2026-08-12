# Spec: Governor Instrumentation

> **Status:** Complete
> **Owner:** @AdamSellke
> **Created:** 2026-08-11
> **Dependencies:** [2026-08-11-component-contract, 2026-08-11-loop-bounds]
> **Origin:** Phase 10 discovery (2026-08-11). ADR-020 and ADR-021 both name the same enforcement gap: Writ has ~30 `eval-*.py` scripts and a 155KB `eval.sh`, and **not one of them asks whether a command knows what it is for**. The governor measures its own byte count. This spec builds the checks that ask — and, per the roadmap's own sequencing note, lands them non-blocking so they are legible before they are binding.

## Contract (Locked)

**Deliverable:** New structural checks in `scripts/eval-leanness.py` — contract presence, `## Completion` presence, loop bounds, and `required_skills:` resolution — landing as non-blocking `warnings`, plus resolution of the four live growth warnings.

**Must include:** Checks emit into `warnings` (exit 0), **deliberately**, per the roadmap's sequencing note: landing them blocking on day one turns every eval run red, and a permanently-red gate becomes invisible — precisely how the current four warnings came to be ignored. They must be written so the later `governor-enforcement` spec flips them to `structural` by changing the emission target, not by rewriting the checks.

**Hardest constraint:** Four unjustified-growth warnings are **live right now** (`commands` +22 lines / +1,995 chars; `scripts` +122 lines / +2,596 chars). New warnings added on top of ignored warnings inherit their invisibility. This spec must clear the existing four — justify in baseline or prune — or its own output is noise from birth.

## Approved Scope Addition — 2026-08-11

> Approved by the maintainer on 2026-08-11, after the `justification` defect below was independently verified in the source. The Contract above is unchanged; this section records what was added to it and why.

**Added:** Story 1 — *Delta-Bound Justification*. `justification` must bind to a specific recorded increment so it silences that increment only, per metric, and warns again on any growth past it.

**Why it could not stay a remediation-string fix.** The original scope corrected the *text* that recommends the trap. That leaves the trap. Two verified defects in `scripts/eval-leanness.py`:

1. **Line 527** reads `justification` once per **surface**, outside the `for metric_key in ("lines", "chars")` loop.
2. **Line 533** — `if current_value <= base_value or justification: continue` — makes any non-empty string skip **both** metrics for that surface, at **any** magnitude, on **every** future run.

Together: one sentence buys permanent, unlimited, unmonitored growth on a whole surface. Every check this spec adds is measured against surfaces that field can mute, so a spec whose entire purpose is "make the governor bite" cannot ship four new checks over a working off-switch.

**What is *not* the bug.** The reseed comment (`scripts/eval-leanness.py:590-595`) argues that `--update-baseline` resetting `justification` to `""` is deliberate: a justification describes a specific past delta, and that delta ceases to exist once the baseline absorbs it. That reasoning is sound and is preserved. The bug is the unbounded silence at line 533, plus the self-defeating remediation text at line 540 that tells a maintainer to write a justification and then run the command that erases it.

**Sequencing.** Story 1 lands **before** the four new checks (now Stories 3–6) so those checks cannot be silenced by the same defect, and **before** clearing the four live warnings (now Story 2) so the clearing uses the fixed mechanism rather than a disposition that would have to be redone.

**Reconciliation with the original Story 1 design.** The `absorbed` array is **dropped**. It was invented to hold the audit record (date, surfaces, delta, cause, disposition) for accepted growth in a key `check_baseline()` ignores. A bound justification holds the same content — `date`, `value`, `text` — attached to the exact `(surface, metric)` it explains, in a field the checker reads *and enforces*. Shipping both would be two records of one fact, one of them inert; and `absorbed` had a self-erasure flaw of its own, since `--update-baseline` rewrites the file wholesale. What is lost is append-only history across absorptions, which `git log .writ/leanness-baseline.json` carries better.

**Unchanged by this addition:** everything in `## Out of Scope`, in particular `scripts/eval.sh`'s `check_length` limits and the absolute `per_surface.commands.chars` cap — both still belong to the later `governor-enforcement` spec.

## Why This Exists

ADR-021 names three reasons the existing leanness governor never caught 516KB of command prose. The third is the one this spec answers: *"Nothing anywhere asserts that a command declares a goal, exit criteria, or a loop bound."* ADR-020 puts a number on it — 2 of 32 commands declare a goal, 13 of 32 carry `## Completion`, and **0 of 5** loop-bearing commands declare an iteration bound. Verified again at spec time: `grep -l '^problem:' commands/*.md` returns **0 of 32**, and `grep -l '^## Completion' commands/*.md` returns **13 of 32**.

The contract those numbers describe is **missing, not merely unenforced** — and either way, nothing checks it.

> **Corrected 2026-08-11.** An earlier draft of this paragraph asserted that `new-command.md` already mandates `## Completion` and that nineteen commands ignore it. That premise came from ADR-020 and was measured false during Phase 10 spec authoring: `Completion` occurs exactly once in `commands/new-command.md` (line 202, its own heading), and the generated-command structure table at lines 136–143 has six rows and no Completion row. `## Completion` is an emergent convention in 13 files that nothing ever required. ADR-020 is amended by `2026-08-11-component-contract` Story 1. **This spec's deliverable is unchanged** — a check that asserts the section's presence is equally warranted whether the convention was mandated-and-ignored or never mandated at all.

### The second reason: warnings that nobody reads

ADR-021's reason two is *"growth warns, it does not fail,"* and it cites the four live unjustified-growth warnings as proof that an ignored channel stays ignored. This spec is about to add up to 38 more findings to that exact channel. Adding them on top of four standing warnings is how a new signal is born already invisible — which is why clearing the four is Story 2, not a footnote.

The four are not mysterious. `git log` attributes the entire delta to a single commit:

| Surface | Baseline (2026-08-04) | Current | Delta | Attribution |
|---|---|---|---|---|
| `commands` lines | 10,974 | 10,996 | +22 | `a5c5a66` — `commands/update-writ.md` +31/−9 |
| `commands` chars | 514,594 | 516,589 | +1,995 | same commit |
| `scripts` lines | 27,210 | 27,332 | +122 | `a5c5a66` — `install.sh`/`update.sh`/`unlink.sh` +306/−184 |
| `scripts` chars | 1,155,797 | 1,158,393 | +2,596 | same commit |

`a5c5a66` is *"feat(install): fan out runtime scripts and Writ docs on install/update"* (PR #34, shipped in v0.28.0). This is reviewed, released feature work, not drift. The honest disposition is to accept the delta and record why — not to prune shipped functionality to satisfy a counter.

### The trap inside the prescribed fix

The warning's own remediation text (`scripts/eval-leanness.py:540`) reads: *"add a one-line justification to `surfaces.<name>` in `.writ/leanness-baseline.json` and rerun `--update-baseline`."* Following it literally does two things the author did not intend:

1. `--update-baseline` **resets every `justification` to `""`** (the reseed block at `scripts/eval-leanness.py:596-615`). The justification you were just told to write is erased by the command you were just told to run next.
2. A non-empty `justification` makes `check_baseline()` `continue` past **both** `lines` and `chars` for that surface, on **every future run, at any magnitude** — `justification` is read once per surface at line 527, outside the per-metric loop, and line 533 is `if current_value <= base_value or justification: continue`. It is not a one-time pass for one delta. It is a permanent mute on that surface's ratchet.

So the field advertised as "up costs a sentence" actually costs one sentence and then buys unlimited silence.

Correcting the string alone would leave the off-switch in place under four brand-new checks. Per the approved scope addition of 2026-08-11, **Story 1 fixes the mechanism**: a justification binds to a recorded `value`, per metric, silencing growth up to that value and warning past it. **Story 2** then clears the four live warnings using it — recording the `a5c5a66` attribution in `justifications`, the field the checker reads, with the floor left where the last true reseed put it.

### Why non-blocking is the design, not a compromise

ADR-020's "Enforcement sequencing (load-bearing)" section and the roadmap's Phase 10 Dependencies both say the same thing in the same words: checks land as `warnings` and flip to `structural` only once migration brings the surface into compliance, because *"landing them blocking on day one turns every eval run red, and a permanently-red gate becomes invisible."* With 0/32 contract compliance and 18 commands lacking `## Completion`, a blocking check on day one fails `eval.sh` on every commit until the two dependency specs finish their migration — and the standard response to a gate that is always red is to stop reading it.

The risk this spec must actively defend against is therefore not "the checks are wrong." It is **building a gate everyone learns to ignore** — or worse, a gate with an off-switch. That risk is what Business Rules 1, 3, 6, and 9 exist to hold.

## 📋 Business Rules

1. **No new warning is emitted while any of the four existing growth warnings is live.** Story 2 gates Stories 3–6. Acceptance for Story 2 is `warnings == []` from `python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json`, and each later story re-asserts that its own findings are the *only* entries added. A new signal that arrives inside standing noise is not a signal.

2. **Every finding names the exact file and the exact field it asserts.** `subject` is `commands/status.md → problem:`, never `commands`. `what` names the missing thing; `fix` names the edit that resolves it. An aggregate finding ("14 commands lack `## Completion`") is not actionable and is forbidden — 38 individually addressable findings are the deliverable, not one summary line. This is the direct lesson of the four growth warnings, which say *which surface* grew but never *which file* — and today do not even say which *metric*, since both `lines` and `chars` warn under an identical `subject`. Story 1 takes the growth warning as far as the data allows (`<surface>.<metric>`); the ratchet measures aggregates, so per-file attribution stays out of its reach and stays `git log`'s job.

3. **The warnings→structural flip is one named constant with one emission router.** `CONTRACT_CHECK_SEVERITY` (one module-level string in `scripts/eval-leanness.py`) and a single `emit_contract_findings()` router. Every new check is a pure function returning `list[dict]` in the existing `{subject, what, fix}` shape and appends to nothing itself. The later `governor-enforcement` spec changes one string literal. Verified by a test that flips the constant in-process and asserts the identical findings move from `warnings` to `structural` and that `eval.sh` then FAILs — not by inspection of the code.

4. **Checks read the surface; they never modify it.** `eval-leanness.py` gains no write path, no `--fix`, no autofix. Bringing commands and agents into compliance belongs to `2026-08-11-component-contract` and `2026-08-11-loop-bounds`. This spec builds the instrument, not the migration.

5. **Both agent config-block carriers are handled.** 6 of 7 agents use `## Agent Configuration` with a plain fence; `visual-qa-agent.md` alone uses `## Agent Specification` with a ```yaml fence. Both are legitimate today (`system-instructions.md` documents the split for `model_tier`). A check that recognizes only one carrier produces a false finding against `visual-qa-agent.md`, and a false finding is the fastest way to teach a maintainer to ignore the channel.

6. **`required_skills:` degrades gracefully — it warns, it never hard-fails.** `system-instructions.md`: *"Unknown skill names produce a **warning** at consumer load time, not a hard failure (graceful degradation: a pilot extraction may rename a skill mid-flight)."* The resolution check must respect that contract even after the structural flip: unresolvable skill names stay `warnings` when the other three checks become `structural`. Story 6 must make this an explicit, tested exception, not an accident of where the code sits.

7. **Infrastructure files are excluded by the existing rule, not a new one.** `commands/_preamble.md` matches `INFRA_PREFIXES = ("_",)` and is not a user-invokable command — 31 checkable commands, not 32. The checks reuse `is_infra()` / `command_names()` rather than hardcoding a skip list, so a future `commands/_foo.md` is handled without a second convention.

8. **A check with nothing to assert reports nothing — and says so in the metrics.** `required_skills:` currently has **0 declarations across the entire product surface** (verified: only prose references in `new-skill.md`, the three adapters, and `system-instructions.md`). Its check therefore passes vacuously today. That is correct behavior, but a vacuous pass must not read as a verified pass: the check reports a declaration count in `metrics` so "0 findings" and "0 things checked" are distinguishable.

9. **A justification is bound to a recorded value, per metric, or it silences nothing.** No mechanism in this spec may grant open-ended silence to a surface. A justification names one `(surface, metric)` pair and one `value`; it silences growth up to that value and warns past it, naming the ceiling it passed. It never spans both metrics of a surface, and it never survives its own increment. "Down is free" is evaluated first and unconditionally, so this rule cannot make a shrinking surface warn. Any story in this spec that grows a gated surface past its recorded ceiling raises that ceiling **itself**, in a dated entry naming that story — growth costs a reviewable diff each time, not one sentence once. A justification that cannot be evaluated (malformed `value`, blank `text`, legacy unbounded string) warns; it never silences by default.

## Detailed Requirements

### Delta-bound justification (the silencer fix)

Story 1. `justification` stops being an open-ended per-surface string and becomes a per-metric record bound to the increment it describes.

**Baseline entry shape (schema 3):**

```json
"commands": {
  "lines": 10974,
  "chars": 514594,
  "justifications": {
    "lines": {"value": 10996, "date": "2026-08-11", "text": "<why this increment was accepted>"},
    "chars": {"value": 516589, "date": "2026-08-11", "text": "<why this increment was accepted>"}
  }
}
```

**Evaluation, per `(surface, metric)` pair, in this order:**

1. `current <= base` → silent. Down is free, evaluated first and unconditionally. No justification is consulted, so no justification can ever make a shrinking surface warn.
2. `current > base` and `justifications.<metric>` is a dict with a numeric `value`, a non-blank `text`, and `current <= value` → silent. The justification covers the increment it names, and nothing else.
3. Otherwise → warn, in one of three voices: no justification recorded for this metric; the justified ceiling of `<value>` (recorded `<date>`) was passed; or a legacy unbounded `justification` string is present and no longer silences anything.

**Finding `subject` becomes `<surface>.<metric>`** — `commands.lines`, not `commands`. Today both metrics of one surface produce warnings with an identical `subject`, which is the same surface-level conflation the fix removes, and it violates Business Rule 2 in the code this spec is extending.

**Backward compatibility.** All six committed entries carry `"justification": ""` (verified in `.writ/leanness-baseline.json`), which never silenced anything, so their behavior is unchanged. A *non-empty* legacy string is treated as **carrying no bound and therefore silencing nothing**: it warns, with a `fix` naming the bound replacement. Carrying the unbounded form forward as still-valid would preserve the defect in old data — the migration must be fail-loud, and it is the safe direction to fail in.

**Schema.** The writer bumps to `"schema": 3`; the reader accepts `2` **and** `3`. `check_baseline()` currently makes `schema != 2` a *structural* finding (`scripts/eval-leanness.py:510`), so the reader change must land before or with the first write of 3 — otherwise the commit that introduces the new shape fails `eval.sh` on its own run. Schema 1, a missing `surfaces` map, and a missing or unreadable baseline stay structural, unchanged.

**`--update-baseline` keeps resetting.** The reseed writes `"justifications": {}` and drops the legacy key. The existing defense of the reset (`scripts/eval-leanness.py:590-595`) is sound and is preserved: a ceiling at or below the new floor is dead data. The corrected remediation string must therefore stop prescribing "write a justification, then rerun `--update-baseline`" and instead state the two dispositions separately — record a bound justification (floor stays, reason recorded, growth past it warns), or reseed (every floor moves, no reason recorded).

### Emission seam

One module-level constant and one router in `scripts/eval-leanness.py`:

```python
# Phase 10 sequencing (ADR-020 "Enforcement sequencing (load-bearing)"):
# component-contract findings land NON-BLOCKING until the migration specs
# bring the surface into compliance. The governor-enforcement spec flips
# this one string to "structural". Nothing else changes.
CONTRACT_CHECK_SEVERITY = "warnings"   # -> "structural"
```

```python
def emit_contract_findings(findings, structural, warnings, severity=None): ...
```

`main()` calls each new check, collects its `list[dict]`, and routes through the router. No check appends to `structural` or `warnings` directly. Existing checks (`check_parity`, `check_coverage`, `check_baseline`, `check_ceilings`) keep their current wiring untouched — this seam governs the four new checks only.

### Check 1 — contract presence

For each non-infra `commands/*.md`: parse the leading `---` YAML frontmatter and assert `problem:`, `outcome:`, and `exit_criteria:` are present and non-empty. One finding per missing field per file.

For each `agents/*.md`: locate the config block under `## Agent Configuration` (plain fence) **or** `## Agent Specification` (```yaml fence) and assert the same three keys. A file with neither heading is itself a finding — the carrier is the contract's only home.

Expected findings on today's surface: 31 commands × 3 + 7 agents × 3 = **114**. This is the check with the largest day-one output, and the strongest argument for Business Rule 1.

### Check 2 — `## Completion` presence

For each non-infra `commands/*.md`: assert a line matching `^## Completion` exists. Expected findings today: **18** (31 checkable commands, 13 compliant). Heading match is exact — `## Completion Criteria` or `### Completion` do not satisfy it, and the finding text says so, because a near-miss heading is the likeliest false-negative and the maintainer needs to know which spelling the check wants.

### Check 3 — loop bounds

For the five commands the roadmap verifies as loop-bearing — `implement-phase`, `implement-spec`, `implement-story`, `refactor`, `verify-spec` — assert the frontmatter declares `loop.max_iterations` and `loop.on_exhaustion`. Expected findings today: **10**.

The list of five is a named constant in `eval-leanness.py` with a comment pointing at the roadmap measurement that produced it. It is not inferred from the file contents — inferring "does this command loop?" from prose is exactly the heading-variant grammar problem ADR-020 rejects. If `2026-08-11-loop-bounds` establishes a different field shape, this check follows that spec's shape; the field names above are this spec's stated expectation, not a competing definition.

### Check 4 — `required_skills:` resolution

For every `commands/*.md` and `agents/*.md` declaring `required_skills:`, assert each entry resolves to an existing `skills/<name>/SKILL.md`. Existing skills: `code-explanation`, `conventional-commits`, `error-rescue-mapping`, `gbrain-interop`, `safe-refactor-loop`, `tdd-cycle`.

Findings are per unresolved `(file, skill-name)` pair. Zero declarations exist today, so the check emits nothing — and reports `required_skills_declarations: 0` in `metrics` per Business Rule 8, so the vacuous pass is visible as vacuous.

Per Business Rule 6, this check's findings stay in `warnings` even after the flip. It routes through the seam with an explicit `severity="warnings"` override and a comment citing `system-instructions.md`'s graceful-degradation clause.

### Baseline resolution (the four live warnings)

Story 2, and it uses Story 1's mechanism. **Justify, do not absorb, do not prune.** Record a bound justification for each of the four `(surface, metric)` pairs — `commands.lines`, `commands.chars`, `scripts.lines`, `scripts.chars` — with `value` set to the measurement taken *after Story 1 lands* (Story 1 grows `scripts`), `date` set to the day it is written, and `text` naming the cause: commit `a5c5a66`, PR #34, v0.28.0 install fan-out. Every `lines`/`chars` baseline number stays exactly where the 2026-08-04 reseed put it. The same hand-edit bumps `schema` to `3` and deletes all six legacy `"justification": ""` keys.

Three consequences worth stating plainly:

- The channel goes quiet because the growth is **accounted for**, not muted. One unit past any recorded `value` and the warning returns, naming the ceiling it passed.
- The floor stays at the last true reseed, so the ratchet keeps reporting **cumulative** drift rather than resetting its own memory on every accepted increment. `--update-baseline` would have discarded that.
- **The `absorbed` array is dropped.** A bound justification carries the same audit content in a field the checker reads and enforces, attached to the exact `(surface, metric)` it explains. See `## Approved Scope Addition — 2026-08-11` for the full reconciliation.

The remediation-string correction moves to Story 1, where the semantics it describes are defined.

### Metrics additions

`metrics` gains `contract_compliance` — per-check counts of files checked and files compliant — so the migration specs have a number to move and `/status` can report progress without re-deriving it. Counts, not finding text: the findings are the actionable channel, the metrics are the trend channel.

## Out of Scope

- **`scripts/eval.sh`'s `check_length` limits.** The command limit stays at 2000 lines. Lowering it to 400 is ADR-021's decision and belongs to `governor-enforcement`.
- **The absolute `per_surface.commands.chars` cap.** ADR-021 item 5 pairs the 400-line limit with a hard chars cap that fails rather than warns. Both land together in `governor-enforcement`, not here. This spec touches the ratchet's *baseline data* only, never adds an absolute ceiling.
- **Flipping `CONTRACT_CHECK_SEVERITY` to `"structural"`.** This spec builds and tests the seam. Throwing it is the later spec's single-line change, gated on the migration specs reaching compliance.
- **Migrating any command or agent into compliance.** Adding `problem:`/`outcome:`/`exit_criteria:`, `## Completion` sections, or loop-bound declarations to real files belongs to `2026-08-11-component-contract` and `2026-08-11-loop-bounds`. This spec will emit ~142 findings against the current surface and fix none of them — deliberately.
- **Extending `status:`/`evidence:` (ADR-014 vocabulary) to commands and agents.** Listed under the roadmap's "Make the governor bite" feature; it is contract *content*, not contract *checking*, and it has no consumer until `/refresh-command`'s Evidence Gate is wired for it.
- **Any change to `check_parity`, `check_coverage`, or `check_ceilings`.** The four new checks are additive. `check_baseline()` is the one existing check this spec does change, and only in the two respects Story 1 names: how a justification is evaluated, and what the finding text says.
- **Pruning `commands/update-writ.md`, `install.sh`, `update.sh`, or `unlink.sh`.** The growth they caused is reviewed, shipped v0.28.0 feature work. Story 2 justifies it at a recorded ceiling; it does not revert it.

## Technical Concerns (surfaced at contract time)

- **Check 3 depends on a field shape this spec does not own.** `loop.max_iterations` / `loop.on_exhaustion` is `2026-08-11-loop-bounds`'s decision. Verified against that spec as authored: it names those exact fields and requires both *at the top level of* `loop:`, with an optional `nested:` sub-map used only by `implement-story`. Check 3's expectation therefore matches today. If that spec's shape changes, Check 3 changes its constant and its tests; the seam, the router, and the other three checks are unaffected. This is the one place a dependency spec can force rework here, and it is bounded to one function.
- **Check 3 and `2026-08-11-loop-bounds`'s own check overlap by design, not by accident.** That spec explicitly cedes *presence* checking to this Check 3 (naming the same five commands and the same 10 expected findings) and scopes its own check to *correctness* — enum closure, integer type, citation quality, unit uniqueness — skipping any file with no `loop:` block. Presence and correctness are checked once each, by one owner each. If either spec drifts from that split, two checks will report the same missing field twice, which is exactly the duplicate-signal noise Business Rule 2 exists to prevent.
- **114 day-one findings from Check 1 is a lot of output.** It is also the true measurement, and suppressing it would reproduce the exact failure this spec exists to correct. The mitigation is Business Rule 2 (each finding individually addressable, so the list is a work queue rather than a wall) plus the `contract_compliance` metric (so progress is one number, not a diff of 114 lines).
- **A vacuous check can look like a passing check.** Check 4 has nothing to resolve today. Business Rule 8's declaration count in `metrics` is the guard; without it, "`required_skills:` resolution: 0 findings" would read as verified when it means unexercised.
- **A bound justification makes each raise cheap, and this spec will raise several.** Stories 3–7 all edit `scripts/eval-leanness.py`, so each will pass the previous ceiling and re-warn. That is the mechanism working, but it means this spec's own history is the first test of whether "growth costs a reviewable diff each time" holds under pressure. The guard is Business Rule 9's requirement that each story raise its own ceiling, dated and attributed, rather than batching the raises or reaching for a wider silence. If the resulting history shows repeated raises with thin `text`, that is a Tier B audit finding — not an argument for restoring an unbounded mute.
- **The schema bump has an ordering trap of its own.** `check_baseline()` treats `schema != 2` as *structural* (`scripts/eval-leanness.py:510`). A commit that writes `"schema": 3` before the reader accepts it fails `eval.sh` on its own run — the same class of self-defeating sequence as the remediation string this spec is fixing. Reader first, in Story 1; writer output and the baseline rewrite after.

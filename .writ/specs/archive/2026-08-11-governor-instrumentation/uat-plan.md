# UAT Plan: Governor Instrumentation

> **Generated:** 2026-08-11
> **Spec:** `.writ/specs/2026-08-11-governor-instrumentation/`
> **Stories Covered:** 7 of 7 completed
> **Total Scenarios:** 19

## How to Use This Plan

1. Work through scenarios in order (grouped by story).
2. Run the commands exactly as written, from the repository root, on a branch that contains this spec (`phase/10-component-contract` or later).
3. Mark Pass or Fail — add notes for anything that differs from the Expected Result.
4. A Fail is filed as an issue or fed back to the spec; it is not fixed inline.
5. The feature passes UAT when every scenario passes, or when a failure is explicitly accepted as a known limitation.

> **Scenarios 2, 3 and 4 modify `.writ/leanness-baseline.json`.** That file is the ratchet's memory. Each of those scenarios opens with a backup command and closes with a restore command — **run both.** Before starting any of them, confirm `git status --porcelain .writ/leanness-baseline.json` is empty; confirm it is empty again afterwards. Leaving a mutation in place either silences a real grower or fills the channel with a warning nobody asked for.
>
> **No scenario modifies `scripts/eval-leanness.py` or `scripts/eval.sh`.** Scenario 14 needs a *flipped* copy of the checker; it makes one in a throwaway directory. The committed script is never touched.
>
> **The reader used throughout.** Most scenarios pipe the checker's JSON through this. Define it once:
> ```bash
> read_findings() {
>   python3 -c "import json,sys
> d=json.load(sys.stdin)
> print('structural:',len(d['structural']),' warnings:',len(d['warnings']))
> [print('-',w['subject'],'::',w['what']) for w in d['warnings']]"
> }
> ```

## What This Spec Actually Delivered

Two things, and they are not equally strong.

**The silencer fix is real and load-bearing.** Before this spec, one non-empty `justification` string bought unlimited, permanent, whole-surface silence on the growth ratchet. It is now a per-metric record bound to a recorded ceiling: it silences the increment it names and nothing beyond it, and legacy unbounded strings silence nothing at all. Scenarios 1–6 are that proof, and they are the centre of this plan.

**The four new structural checks are instrumentation, not enforcement.** They emit into `warnings`, exit 0, and — against this repository — find nothing, because the two dependency specs brought the surface into compliance before the checks existed. Read the **Honest Notes** before signing off: a reading of zero here means the migration worked, and it also means these checks have never fired in anger against real files.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|------------------|
| Story 1: Delta-bound justification | ✅ Covered | 6 | AC: 4, Matrix: 1, Remediation text: 1 |
| Story 2: Clear the live growth warnings | ✅ Covered | 2 | AC: 1, Business Rule 9 audit: 1 |
| Stories 3–6: The four checks | ✅ Covered | 5 | AC: 3, Vacuous-pass guard: 1, Reporting gap: 1 |
| Story 7: Warnings→structural flip seam | ✅ Covered | 2 | AC: 2 |
| Whole-spec: scope, cost, regression | ✅ Covered | 4 | Out of Scope: 1, Cost: 2, Regression: 1 |

---

## Story 1: Delta-Bound Justification — the Silencer Is Dead

### Scenario 1: Clean state — the channel is quiet, and quiet is the baseline for everything after it

**Source:** Business Rule 1 — "No new warning is emitted while any of the existing growth warnings is live… A new signal that arrives inside standing noise is not a signal." Story 2 AC 1. Establish this before mutating anything; Scenarios 2, 3 and 4 all return here.

**Preconditions:**
- Working tree clean. `git status --porcelain .writ/leanness-baseline.json` is empty.
- `python3` available.

**Steps:**
1. ```bash
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json | read_findings
   ```
2. ```bash
   bash scripts/eval.sh --check=leanness --report=/tmp/leanness-uat.md > /dev/null 2>&1; echo "EXIT=$?"
   ```
3. Open `/tmp/leanness-uat.md` and read the `## leanness` section and the `## Summary`.
4. Confirm the committed baseline's own shape: `python3 -c "import json; d=json.load(open('.writ/leanness-baseline.json')); print(d['schema'], d['recorded'], sorted(d['surfaces'])); print('legacy key present:', any('justification' in v for v in d['surfaces'].values()))"`

**Expected Result:**
- Step 1: `structural: 0  warnings: 0`. No finding lines at all.
- Step 2: `EXIT=0`.
- Step 3: `## leanness` reads **PASS**; `## Summary` reads `Findings: 0`, `Run errors: 0`. The non-blocking notes carry the `Metrics:` lines only.
- Step 4: `3 2026-08-04 ['adapters', 'agents', 'commands', 'scripts', 'skills', 'system_instructions']` and `legacy key present: False`. Schema is 3, the `recorded` date is still the 2026-08-04 reseed, and no surface carries the old unbounded `"justification"` string key.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 1–7 — Files: `scripts/eval-leanness.py`, `.writ/leanness-baseline.json`; commits `0b29a61`…`bb24442`

**Notes:**

---

### Scenario 2: One unit past a recorded ceiling and the ratchet speaks again, naming the ceiling it passed

**Source:** Business Rule 9 — "A justification names one `(surface, metric)` pair and one `value`; it silences growth up to that value and warns past it, naming the ceiling it passed." Story 1 AC 3; Story 2 AC 4 (the armed-ratchet check). Technical spec matrix row 5.

> **This scenario mutates `.writ/leanness-baseline.json`.** Back it up in step 1 and restore it in step 4. Do not skip either.

**Preconditions:**
- `git status --porcelain .writ/leanness-baseline.json` is **empty**. If it is not, stop.

**Steps:**
1. Back up the baseline:
   ```bash
   cp .writ/leanness-baseline.json /tmp/leanness-baseline.bak
   ```
2. Lower the recorded ceiling for `scripts.lines` by exactly one:
   ```bash
   python3 - <<'EOF'
   import json
   p = '.writ/leanness-baseline.json'
   d = json.load(open(p))
   d['surfaces']['scripts']['justifications']['lines']['value'] -= 1
   json.dump(d, open(p, 'w'), indent=2)
   EOF
   python3 -c "import json; print(json.load(open('.writ/leanness-baseline.json'))['surfaces']['scripts']['justifications']['lines']['value'])"
   ```
3. ```bash
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json | read_findings
   ```
4. **Restore immediately:**
   ```bash
   cp /tmp/leanness-baseline.bak .writ/leanness-baseline.json
   git status --porcelain .writ/leanness-baseline.json   # must print nothing
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json | read_findings
   ```

**Expected Result:**
- Step 2 prints `29957`.
- Step 3 prints `structural: 0  warnings: 1` and exactly one finding, whose `subject` is **`scripts.lines`** and whose `what` opens verbatim:

  > `scripts lines grew from 27210 to 29958 (+2748), past the justified ceiling of 29957 recorded 2026-08-11 ("a5c5a66 (install.sh/update.sh/unlink.sh runtime fan-out, PR #34, v0.28.0), 9b65a94 (scripts/eval-loop-bounds.py), and 2026-08-11-governor-instrumentation Stories 1 and 3-7 — …"). That justification covered growth to 29957.`

- Three things in that sentence are the deliverable: the `subject` names the **metric**, not just the surface; the message names the **ceiling** that was passed and the **date** it was recorded; and it quotes the justification's own `text` back at the reader, so the reason is in the warning rather than in a file they have to open.
- **`scripts.chars` does not warn.** Only `lines` was lowered, and a justification for one metric neither silences nor implicates the other.
- Step 4: `structural: 0  warnings: 0`, and the tree is clean.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/eval-leanness.py` (`justified_ceiling`, `check_baseline`); commit `0b29a61`

**Notes:**

---

### Scenario 3: A legacy unbounded `justification` string silences nothing — and it says so, per metric

**Source:** Business Rule 9 — "A justification that cannot be evaluated (malformed `value`, blank `text`, legacy unbounded string) warns; it never silences by default." Story 1 AC 6. Technical spec matrix rows 8 and 10. **This is the most important scenario in the plan.** It proves two properties at once: that the old whole-surface mute cannot be smuggled forward in old data, and that `lines` and `chars` are now evaluated independently.

> **This scenario mutates `.writ/leanness-baseline.json`.** Back it up in step 1 and restore it in step 4.

**Preconditions:**
- `git status --porcelain .writ/leanness-baseline.json` is **empty**.
- Scenario 2 completed and restored.

**Steps:**
1. ```bash
   cp .writ/leanness-baseline.json /tmp/leanness-baseline.bak
   ```
2. Replace `scripts`'s bound `justifications` object with the pre-schema-3 string form — the exact shape that used to buy permanent silence:
   ```bash
   python3 - <<'EOF'
   import json
   p = '.writ/leanness-baseline.json'
   d = json.load(open(p))
   del d['surfaces']['scripts']['justifications']
   d['surfaces']['scripts']['justification'] = 'shipped work, trust me'
   json.dump(d, open(p, 'w'), indent=2)
   EOF
   ```
3. ```bash
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json | read_findings
   ```
4. **Restore immediately:**
   ```bash
   cp /tmp/leanness-baseline.bak .writ/leanness-baseline.json
   git status --porcelain .writ/leanness-baseline.json   # must print nothing
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json | read_findings
   ```

**Expected Result:**
- Step 3 prints `structural: 0  warnings: 2` — **two** findings, not one, with distinct subjects:

  > `- scripts.lines :: surfaces.scripts carries a legacy unbounded `justification` (schema 2); it silences nothing. scripts lines grew from 27210 to 29958 (+2748).`
  >
  > `- scripts.chars :: surfaces.scripts carries a legacy unbounded `justification` (schema 2); it silences nothing. scripts chars grew from 1155797 to 1279401 (+123604).`

- Under the old code this same edit produced **zero** warnings, forever, at any magnitude. That is the defect, and it is gone.
- Each message states the verdict in the same words — **it silences nothing** — and states it *separately for each metric*. The old code read `justification` once per surface, outside the per-metric loop; two findings from one string is the observable proof that the read moved inside it.
- Each finding's `fix` names the bound replacement for its own metric: `surfaces.scripts.justifications.lines` in one, `surfaces.scripts.justifications.chars` in the other, with the correct current measurement in each.
- Step 4: `structural: 0  warnings: 0`, tree clean.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/eval-leanness.py` (`justified_ceiling` legacy branch, `check_baseline` per-metric loop)

**Notes:**

---

### Scenario 4: "Down is free" is evaluated first and unconditionally — no justification state can weaken it

**Source:** Business Rule 9 — "'Down is free' is evaluated first and unconditionally, so this rule cannot make a shrinking surface warn." Story 1 AC 5. Technical spec matrix rows 2, 6, 7. A ratchet that punishes shrinking is a ratchet nobody will shrink under; the fix must not have introduced one.

> **This scenario mutates `.writ/leanness-baseline.json`.** Back it up in step 1 and restore it in step 4.

**Preconditions:**
- `git status --porcelain .writ/leanness-baseline.json` is **empty**.

**Steps:**
1. ```bash
   cp .writ/leanness-baseline.json /tmp/leanness-baseline.bak
   ```
2. Put `scripts` far *below* its floor and simultaneously give it the worst possible justification state — a legacy unbounded string and no bound record at all:
   ```bash
   python3 - <<'EOF'
   import json
   p = '.writ/leanness-baseline.json'
   d = json.load(open(p))
   s = d['surfaces']['scripts']
   s['lines'] = 9999999
   s['chars'] = 9999999
   del s['justifications']
   s['justification'] = 'trust me'
   json.dump(d, open(p, 'w'), indent=2)
   EOF
   ```
3. ```bash
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json | read_findings
   ```
4. **Restore immediately:**
   ```bash
   cp /tmp/leanness-baseline.bak .writ/leanness-baseline.json
   git status --porcelain .writ/leanness-baseline.json   # must print nothing
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json | read_findings
   ```
5. Read the ordering in the source — it is the whole claim:
   ```bash
   grep -n 'down is free\|Down is free' scripts/eval-leanness.py
   ```

**Expected Result:**
- Step 3: `structural: 0  warnings: 0`. `scripts` is now 29,958 lines against a floor of 9,999,999 — far below — and it stays silent despite carrying exactly the legacy string that Scenario 3 proved produces two warnings when the surface has grown.
- Step 5: five hits — the docstring summary line, the docstring's emphatic restatement, the code comment at line 1094, and two in the reseed block and its `note`. The comparison `if current_value <= base_value: continue  # down is free — first, and unconditional` sits **above** the `justified_ceiling(...)` call in `check_baseline()`, and the docstring states the same ordering. The justification is never consulted for a shrinking surface, so no justification state — valid, stale, malformed, or legacy — can reach it.
- Step 4: `structural: 0  warnings: 0`, tree clean.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/eval-leanness.py` (`check_baseline`)

**Notes:**

---

### Scenario 5: The 16-row matrix, and the reseed writes schema 3 without touching the repository

**Source:** Technical spec § Test matrix for the bound justification (rows 1–16); Story 1 AC 8 and 10. Scenarios 2–4 exercise three rows against the real repository; the matrix covers the other thirteen, including the malformed shapes that must warn without raising.

**Preconditions:**
- `python3` available. This scenario mutates nothing tracked.

**Steps:**
1. Run the matrix and the ceiling reader:
   ```bash
   python3 scripts/tests/test_eval_leanness_contract.py BoundJustificationTests JustifiedCeilingTests -v 2>&1 | tail -30
   ```
2. Confirm each row is a named test and read the names — they are the assertions, in words:
   ```bash
   python3 scripts/tests/test_eval_leanness_contract.py BoundJustificationTests -v 2>&1 | grep '^test_row'
   ```
3. Confirm `--update-baseline` still resets, and confirm it can be observed **without writing to `.writ/`**:
   ```bash
   T=$(mktemp -d)
   python3 scripts/eval-leanness.py --root . --baseline "$T/reseed.json" --update-baseline
   python3 -c "
   import json
   d = json.load(open('$T/reseed.json'))
   print('schema:', d['schema'])
   print('justifications:', {k: v['justifications'] for k, v in d['surfaces'].items()})
   print('legacy key present:', any('justification' in v for v in d['surfaces'].values()))
   "
   git status --porcelain .writ/leanness-baseline.json   # must print nothing
   rm -rf "$T"
   ```

**Expected Result:**
- Step 1: **OK**, no failures. `BoundJustificationTests` and `JustifiedCeilingTests` together cover rows 1–16 plus the reader's own edge cases (boolean `value` rejected, the other metric's key never consulted).
- Step 2: **18** `test_row*` names — the 16 matrix rows plus `test_row15b_schema_3_is_read_normally` and `test_row15c_schema_1_stays_structural`, which split row 15's schema handling in three. Among them, the four that matter most are — `test_row5_one_past_the_ceiling_warns_naming_the_ceiling`, `test_row7_down_is_free_even_with_a_justification_present`, `test_row8_a_justification_for_one_metric_never_silences_the_other`, and `test_row10_legacy_non_empty_string_no_longer_mutes`. Row 10 is the direct regression test for the old permanent mute.
- Step 3: `schema: 3`; every surface's `justifications` is `{}`; `legacy key present: False`. The committed baseline is untouched — `--baseline` redirects the write, so the reseed can be inspected without moving any floor in this repository.
- The reset is **not** a defect and was deliberately preserved: a recorded ceiling at or below a fresh floor is dead data. What changed is that the remediation text no longer tells a maintainer to write a justification and then run the command that erases it (Scenario 6).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/tests/test_eval_leanness_contract.py` (`BoundJustificationTests`, `JustifiedCeilingTests`); `scripts/eval-leanness.py` (`main` reseed block)

**Notes:**

---

### Scenario 6: The remediation text no longer prescribes a sequence that erases its own output

**Source:** Story 1 AC 9; spec.md § The trap inside the prescribed fix. The old `fix` read *"add a one-line justification … and rerun `--update-baseline`"* — and `--update-baseline` wipes justifications. The instruction deleted what it had just told you to write.

**Preconditions:**
- None. `read_findings` prints `subject` and `what` only; step 1 reads the `fix` string straight out of the source.

**Steps:**
1. Read the shipped `fix` text and the two other places that carried the old promise:
   ```bash
   grep -n 'Prune the surface back down' -A 8 scripts/eval-leanness.py
   grep -n 'up costs a sentence' scripts/eval-leanness.py
   grep -n 'Down is free' .writ/leanness-baseline.json
   ```
2. Confirm the property is asserted by a test, not by reading:
   ```bash
   python3 scripts/tests/test_eval_leanness_contract.py \
     BoundJustificationTests.test_the_fix_text_never_prescribes_a_self_erasing_sequence \
     BoundJustificationTests.test_docstring_no_longer_advertises_up_costs_a_sentence -v 2>&1 | tail -5
   ```
3. Read the `fix` as a maintainer would and follow it mentally: does either branch destroy the other's output?

**Expected Result:**
- Step 1: the `fix` offers **two separate dispositions** and never chains them — (a) prune, or record the increment by setting `surfaces.<name>.justifications.<metric>` to a `{"value", "date", "text"}` object, which "silences growth to `<value>` and nothing beyond it"; (b) `--update-baseline`, described honestly as "it moves EVERY surface's floor to its current measurement and records no reason." `grep 'up costs a sentence'` returns **no hits** — the docstring line that advertised the old promise is gone. The baseline's own `note` key carries the corrected text, so the correction ships with the data as well as the code.
- Step 2: both tests **OK**. The absence of the self-erasing sequence is under test; a future edit that reintroduces it fails the suite.
- Step 3: the two dispositions are independent. Recording a ceiling leaves the floor where it is and keeps cumulative drift measurable; reseeding moves every floor and records nothing. Neither instruction tells you to do the other next.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/eval-leanness.py` (`check_baseline` docstring and `fix` string, reseed `note`); `.writ/leanness-baseline.json` (`note`)

**Notes:**

---

## Story 2: The Live Growth Warnings, Cleared Without Moving a Floor

### Scenario 7: Every floor is still at the 2026-08-04 reseed — only ceilings were recorded

**Source:** Story 2 AC 2 — "every surface's `lines` and `chars` are **unchanged** from the 2026-08-04 reseed… the floor is not moved, so the ratchet keeps measuring cumulative drift from the last true reseed rather than resetting its own memory." This is the difference between accounting for growth and forgetting it.

**Preconditions:**
- Full git history available. Working tree clean.

**Steps:**
1. Read the committed floors:
   ```bash
   python3 -c "
   import json
   d = json.load(open('.writ/leanness-baseline.json'))
   print('recorded:', d['recorded'])
   for k, v in d['surfaces'].items():
       print(' ', k, v['lines'], v['chars'], '| ceilings:',
             {m: r['value'] for m, r in v.get('justifications', {}).items()})
   "
   ```
2. Compare against the last true reseed, before this spec's first commit:
   ```bash
   git show 6b9c930:.writ/leanness-baseline.json | python3 -c "
   import json, sys
   d = json.load(sys.stdin)
   print('recorded:', d['recorded'], 'schema:', d['schema'])
   for k, v in d['surfaces'].items(): print(' ', k, v['lines'], v['chars'])
   "
   ```
3. Compare the two lists of `lines`/`chars` numbers by eye.
4. Confirm nothing in this spec ran the reseed:
   ```bash
   git log --format='%h %ad %s' --date=short -- .writ/leanness-baseline.json | head -8
   ```

**Expected Result:**
- Steps 1 and 2 print **identical** `lines`/`chars` values for all six surfaces: `commands` **10974 / 514594**, `agents` 1768 / 67012, `skills` 932 / 41620, `adapters` 1677 / 84865, `scripts` **27210 / 1155797**, `system_instructions` 300 / 20523. `recorded` is still `2026-08-04` in both.
- Step 1 additionally shows ceilings on three surfaces only — `commands` 11411 / 560684, `agents` 1810 / 72473, `scripts` 29958 / 1279401. The other three print `| ceilings: {}` because the key is absent entirely; confirm with `python3 -c "import json; d=json.load(open('.writ/leanness-baseline.json')); print([k for k,v in d['surfaces'].items() if 'justifications' in v])"`, which returns `['commands', 'agents', 'scripts']`. `skills`, `adapters` and `system_instructions` have not drifted, so there is nothing to record.
- **The consequence, stated:** `scripts` is warned against a floor of 27,210 even though the accepted ceiling is 29,958. The next unjustified unit of growth reports `+2749` — cumulative drift since the last true reseed — not `+1` since the last accepted increment. That is the property `--update-baseline` would have destroyed.
- Step 4: six baseline commits in this spec, none of them a reseed; the last reseed-shaped write is `6b9c930` / `c5f4723`, both predating the spec.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `.writ/leanness-baseline.json`; commit `3feb631`

**Notes:**

---

### Scenario 8: The spec paid for its own growth in separate dated commits, not one batched raise

**Source:** Business Rule 9 — "Any story in this spec that grows a gated surface past its recorded ceiling raises that ceiling **itself**, in a dated entry naming that story — growth costs a reviewable diff each time, not one sentence once." Technical spec § Interaction Edge Cases, last row.

**Preconditions:**
- Full git history available.

**Steps:**
1. Trace the `scripts` ceiling through every commit of the spec:
   ```bash
   for c in 3feb631 445c0c0 560813e c94cefd 4666a2a bb24442; do
     printf '%s  ' "$(git log -1 --format='%h %ad %s' --date=short $c)"
     git show $c:.writ/leanness-baseline.json | python3 -c "
   import json, sys
   d = json.load(sys.stdin)
   print('scripts ceiling:', {m: r['value'] for m, r in d['surfaces']['scripts']['justifications'].items()})
   "
   done
   ```
2. Confirm the floors did **not** move across those same six commits:
   ```bash
   for c in 3feb631 445c0c0 560813e c94cefd 4666a2a bb24442; do
     git show $c:.writ/leanness-baseline.json | python3 -c "
   import json, sys
   d = json.load(sys.stdin)
   print(d['surfaces']['scripts']['lines'], d['surfaces']['commands']['lines'])
   "
   done | sort -u
   ```
3. Read the `text` on the shipped `scripts.lines` ceiling and check that it names the causes rather than gesturing at them.

**Expected Result:**
- Step 1: the `scripts.lines` ceiling rises **five times**, once per story that grew the surface — `28705 → 29219 → 29334 → 29570 → 29729 → 29958` — each in its own commit, each dated. Never a single batched raise at the end, and never a widened silence.
- Step 2: exactly **one** distinct line, `27210 10974`. The floors are identical across all six commits.
- Step 3: the `text` names commit `a5c5a66` (the v0.28.0 install fan-out, PR #34), `9b65a94` (`scripts/eval-loop-bounds.py`), and this spec's own Stories 1 and 3–7 by name, and it identifies `scripts/tests/test_eval_leanness_contract.py` as carrying most of the delta. It is an attribution, not an assurance.
- **Judgement call for the signer:** five ceiling raises inside one spec is the mechanism working as designed, and it is also the mechanism under maximum pressure. Read all three `text` fields. If any of them reads as boilerplate rather than attribution, say so in the Notes — the spec's own risk note calls that a Tier B audit finding, not an argument for restoring a wider mute.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 and Stories 3–7 — Files: `.writ/leanness-baseline.json`; commits `3feb631`, `445c0c0`, `560813e`, `c94cefd`, `4666a2a`, `bb24442`

**Notes:**

---

## Stories 3–6: The Four Structural Checks

### Scenario 9: The checks report compliance as counts, not just as an absence of findings

**Source:** Business Rule 2 and spec.md § Metrics additions — "`metrics` gains `contract_compliance`… so the migration specs have a number to move and `/status` can report progress without re-deriving it." Story 3 AC (last), Story 5 AC (last). **A findings list of zero is ambiguous. A count is not.**

**Preconditions:**
- Working tree clean.

**Steps:**
1. ```bash
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json \
     | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d['metrics']['contract_compliance'], indent=2))"
   ```
2. Cross-check the populations by hand:
   ```bash
   ls commands/*.md | wc -l          # all command files
   ls commands/_*.md                 # the infra file excluded from the 31
   ls agents/*.md | wc -l
   ```
3. Confirm the counts are derived from the findings rather than measured separately:
   ```bash
   grep -n 'def contract_compliance' -A 30 scripts/eval-leanness.py
   ```

**Expected Result:**
- Step 1, exactly:
  ```json
  {
    "commands_checked": 31,
    "commands_with_contract": 31,
    "commands_with_completion": 31,
    "loop_commands_checked": 5,
    "loop_commands_bounded": 5,
    "agents_checked": 7,
    "agents_with_contract": 7
  }
  ```
- Step 2: **32** command files, of which `commands/_preamble.md` is infrastructure and is never checked — hence 31, not 32. **7** agents. The populations match the counts.
- Step 3: `contract_compliance()` computes each "with" count by subtracting the offending files out of each check's own findings list (`_offender_files`). The metric therefore cannot disagree with the work queue a maintainer is reading — a divergence between "0 findings" and "31 compliant" is structurally impossible.
- **What this scenario does not prove:** that the checks would find a violation. The counts are 31/31 because the dependency specs migrated the surface, not because the checks were exercised against it. Scenario 10 and the Honest Notes carry that.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 3–5 — Files: `scripts/eval-leanness.py` (`contract_compliance`, `_offender_files`)

**Notes:**

---

### Scenario 10: `required_skills_declarations: 0` — this is a vacuous pass, and the number is the only thing that says so

**Source:** Business Rule 8 — "A check with nothing to assert reports nothing — and says so in the metrics… a vacuous pass must not read as a verified pass." Story 6 AC (real-repo row) and its own risk note: *"the real-repo assertion is genuinely weak evidence: it proves the check does not crash and counts nothing, not that resolution works."*

**Preconditions:**
- `python3` available. This scenario mutates nothing tracked — step 3 builds a throwaway root.

**Steps:**
1. Read the declaration count:
   ```bash
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json \
     | python3 -c "import json,sys; print('required_skills_declarations:', json.load(sys.stdin)['metrics']['required_skills_declarations'])"
   ```
2. Confirm the count is true — that **zero** declarations exist on the entire product surface, and that every mention is prose:
   ```bash
   grep -rln '^required_skills:' commands/ agents/ | wc -l
   grep -rn 'required_skills' commands/ agents/
   ls skills/
   ```
3. Make the check fire, in a throwaway copy, so you can see what a non-vacuous run looks like:
   ```bash
   VX=$(mktemp -d)
   mkdir -p "$VX/scripts" "$VX/.writ"
   cp -R commands agents skills adapters "$VX/"
   cp system-instructions.md README.md "$VX/"
   cp scripts/eval-leanness.py "$VX/scripts/"
   perl -0pi -e 's/^(outcome:)/required_skills: [ghost-skill, tdd-cycle]\n$1/m' "$VX/commands/status.md"
   python3 "$VX/scripts/eval-leanness.py" --root "$VX" --baseline "$VX/.writ/absent.json" 2>/dev/null | python3 -c "
   import json, sys
   d = json.load(sys.stdin)
   print('required_skills_declarations:', d['metrics']['required_skills_declarations'])
   [print('-', w['subject'], '::', w['what']) for w in d['warnings'] if 'required_skills' in w['subject']]
   "
   rm -rf "$VX"
   ```
4. Read the code comment that pins this check non-blocking forever:
   ```bash
   grep -n 'PINNED NON-BLOCKING' -A 8 scripts/eval-leanness.py
   ```

**Expected Result:**
- Step 1: `required_skills_declarations: 0`.
- Step 2: **0** files declare `required_skills:`. The only hits are three prose mentions in `commands/new-skill.md`. Six skills exist on disk (`code-explanation`, `conventional-commits`, `error-rescue-mapping`, `gbrain-interop`, `safe-refactor-loop`, `tdd-cycle`) and **not one of them is declared by any command or agent.**
- Step 3: `required_skills_declarations: 2` and exactly one finding — `commands/status.md → required_skills: ghost-skill :: declared skill 'ghost-skill' resolves to no skills/ghost-skill/SKILL.md.` `tdd-cycle` resolves and is silent. (A structural finding about the absent baseline also appears; it is unrelated to this scenario. Delete `$VX` when done.)
- Step 4: the `severity="warnings"` override at the call site carries `system-instructions.md`'s graceful-degradation clause as its stated reason, so a future reader cannot mistake the pin for an oversight.
- **The point of the scenario, stated in the words a signer needs:** in step 1 this check reported **0 findings because there was nothing to check**, not because everything passed. `0 findings` and `0 things checked` are the same output; `required_skills_declarations: 0` is the *only* thing in the system that distinguishes them. Every test of this check is fixture-only. It has never resolved a real declaration in this repository, and it will not until progressive disclosure makes the first one.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — Files: `scripts/eval-leanness.py` (`check_required_skills`, `parse_skill_names`, `main` pin); `scripts/tests/test_eval_leanness_contract.py` (`RequiredSkillsCheckTests`)

**Notes:**

---

### Scenario 11: The compliance counts and the vacuous-pass guard do not reach the eval report

**Source:** Business Rule 8; technical spec § Metrics additions — "`eval.sh`'s `check_leanness()` renders `metrics` keys it knows about; unknown keys are ignored, so adding these is backward-compatible with the existing TSV bridge." **That is exactly what happened, and it has a cost the spec does not draw out.** This scenario measures the cost.

**Preconditions:**
- Scenario 1 completed; `/tmp/leanness-uat.md` exists (or regenerate it).

**Steps:**
1. ```bash
   bash scripts/eval.sh --check=leanness --report=/tmp/leanness-uat.md > /dev/null 2>&1
   grep -c 'contract_compliance\|required_skills_declarations' /tmp/leanness-uat.md
   ```
2. Read every `Metrics:` note in the report:
   ```bash
   grep -n 'Metrics:' /tmp/leanness-uat.md
   ```
3. Read the TSV bridge that decides what gets rendered:
   ```bash
   grep -n 'METRIC\\t' scripts/eval.sh
   ```

**Expected Result:**
- Step 1: **0**. Neither key appears anywhere in the report.
- Step 2: four `Metrics:` notes — the legacy aggregate line, `per_surface`, the product totals, and `story_context_bytes` with its proxy disclaimer. `contract_compliance` and `required_skills_declarations` are not among them.
- Step 3: the embedded Python in `check_leanness()` prints a fixed set of `METRIC` lines and has no branch for either new key. The metrics exist in the JSON and stop at the bridge.
- **The consequence:** the numbers that make the two most important honest claims in this spec — "31 of 31 comply" and "0 findings means 0 things checked" — are visible only to someone who runs `python3 scripts/eval-leanness.py` by hand and reads raw JSON. A maintainer reading the eval report, which is the channel this phase built to be readable, sees `PASS` and four metric lines that predate this spec. Business Rule 8's guard is implemented in the data and absent from the report.
- **Mark this Pass** if you can reproduce the three observations above; it is a faithful record of shipped behaviour, not a defect in the checker. It belongs in **Discrepancies Worth Recording** and is the smallest concrete follow-up this spec leaves behind.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 3–6 — Files: `scripts/eval.sh` (`check_leanness` TSV bridge); `scripts/eval-leanness.py` (`main` metrics assignment)

**Notes:**

---

### Scenario 12: The four checks find nothing here — so verify them where they can be made to speak

**Source:** Stories 3, 4, 5 AC and their measured corrections — "the **count** is asserted against fixture trees… and *behaviour* is asserted against the real repo." Every finding count in this spec was verified against fixtures because the real surface complies.

**Preconditions:**
- `python3` available. Mutates nothing.

**Steps:**
1. Confirm zero findings against the real repository, and that the population excluding `_preamble.md` is the existing rule rather than a new one:
   ```bash
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json | read_findings
   grep -n 'INFRA_PREFIXES\|def is_infra' scripts/eval-leanness.py
   grep -c '_preamble' scripts/eval-leanness.py
   ```
2. Run the fixture suites that make each check speak:
   ```bash
   python3 scripts/tests/test_eval_leanness_contract.py \
     ComponentContractCheckTests CompletionSectionCheckTests \
     LoopBoundsCheckTests RequiredSkillsCheckTests -v 2>&1 | tail -8
   ```
3. Confirm the two named traps are regression-tested by name:
   ```bash
   python3 scripts/tests/test_eval_leanness_contract.py -v 2>&1 \
     | grep -E 'both_agent_carriers|no_carrier_false_finding|near_miss|constant_matches'
   ```
4. Confirm the five-command loop population is cross-read rather than restated:
   ```bash
   grep -n 'LOOP_BEARING_COMMANDS_FALLBACK' -A 6 scripts/eval-leanness.py
   grep -n '_loop_bearing_from_sibling' -A 12 scripts/eval-leanness.py | head -20
   ```

**Expected Result:**
- Step 1: `structural: 0  warnings: 0`. `is_infra()` tests `INFRA_PREFIXES = ("_",)`, and `grep -c '_preamble'` returns **0** — the filename appears nowhere in the checker. The exclusion is the existing prefix rule, not a skip list, so a future `commands/_foo.md` is handled with no second convention.
- Step 2: **OK**, no failures. Between them these suites cover: a compliant command; one missing field producing exactly one file-and-field finding; `exit_criteria:` empty and `[]` both treated as missing; no leading fence; a mid-document `---` horizontal rule not mistaken for frontmatter; both agent carriers; an agent with no carrier producing one carrier-level finding rather than three field findings; a `## Completion Criteria` near-miss; a `### Completion` near-miss; a `loop:` key with no children producing two findings; a listed command missing from disk; absent directories producing zero findings and no exception.
- Step 3: `test_both_agent_carriers_are_recognised` and `test_real_repo_agents_produce_no_carrier_false_finding` exist — `agents/visual-qa-agent.md`'s ` ```yaml ` carrier is regression-tested by name, because recognising only `## Agent Configuration` would produce three false findings against a compliant file. `test_completion_criteria_near_miss_is_a_finding_with_the_exact_spelling` asserts the finding text names the required spelling, so a near-miss is diagnosable rather than mysterious.
- Step 4: `LOOP_BEARING_COMMANDS` is parsed out of `scripts/eval-loop-bounds.py` with `ast` (never imported), with a module-level literal as the fallback when the sibling is absent or unparseable, and `test_the_constant_matches_the_correctness_checker_that_shares_it` asserts the two agree. This diverges from the technical spec, which specified a hand-maintained constant — the divergence is recorded in Story 5's Task 5.3 amendment and is the stronger choice: two hand-maintained copies of one population drift, and a drifted presence/correctness split reports a file twice or not at all.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 3–6 — Files: `scripts/eval-leanness.py` (`check_component_contract`, `check_completion_sections`, `check_loop_bounds`, `check_required_skills`); `scripts/tests/test_eval_leanness_contract.py`

**Notes:**

---

### Scenario 13: Every finding names a file and a field — no aggregate finding exists

**Source:** Business Rule 2 — "An aggregate finding ('14 commands lack `## Completion`') is not actionable and is forbidden — 38 individually addressable findings are the deliverable, not one summary line."

**Preconditions:**
- `python3` available. Mutates nothing tracked.

**Steps:**
1. Build a throwaway root with three separate violations in three different files, and read every finding's `subject`:
   ```bash
   AX=$(mktemp -d)
   mkdir -p "$AX/scripts" "$AX/.writ"
   cp -R commands agents skills adapters "$AX/"
   cp system-instructions.md README.md "$AX/"
   cp scripts/eval-leanness.py "$AX/scripts/"
   perl -0pi -e 's/^problem:.*\n//m'      "$AX/commands/status.md"
   perl -0pi -e 's/^## Completion.*\n//m' "$AX/commands/release.md"
   perl -0pi -e 's/^  on_exhaustion:.*\n//m' "$AX/commands/refactor.md"
   python3 "$AX/scripts/eval-leanness.py" --root "$AX" --baseline "$AX/.writ/absent.json" 2>/dev/null \
     | python3 -c "import json,sys; [print('-', w['subject']) for w in json.load(sys.stdin)['warnings']]"
   rm -rf "$AX"
   ```
2. Compare the `subject` shape against the growth warnings from Scenario 2 and Scenario 3.

**Expected Result:**
- Step 1: three findings, each naming a file **and** the field it asserts:
  - `commands/status.md → problem:`
  - `commands/release.md → ## Completion`
  - `commands/refactor.md → loop.on_exhaustion`

  and nothing else in `warnings`. (One `structural` finding names `.writ/absent.json` — the baseline argument points at no file, which is unrelated to this scenario and is why the growth ratchet contributes nothing here.) No finding names a surface alone. No finding aggregates a count.
- Step 2: the growth warnings now carry `scripts.lines` / `scripts.chars` — surface **and metric**. Before this spec both metrics of one surface produced an identical `subject` of `scripts`, which was the same conflation Business Rule 2 forbids, sitting in the code this spec extended. Per-file attribution stays out of the ratchet's reach because it measures aggregates; `<surface>.<metric>` is as far as the data goes, and it went there.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 1, 3–5 — Files: `scripts/eval-leanness.py`

**Notes:**

---

## Story 7: The Warnings→Structural Flip Seam

### Scenario 14: Flip one string in a throwaway copy — the same tree goes from PASS/exit 0 to FAIL/exit 1

**Source:** Business Rule 3 — "Verified by a test that flips the constant in-process and asserts the identical findings move from `warnings` to `structural` and that `eval.sh` then FAILs — not by inspection of the code." Story 7 AC 2 and 5. This is the seam the unbuilt `governor-enforcement` spec will throw.

> **The committed `scripts/eval-leanness.py` is never modified.** The recipe below writes a *flipped copy* into a temp directory. Never run `sed` against the real script.

**Preconditions:**
- `python3`, `bash`, `perl` available. Working tree clean.

**Steps:**
1. Build a throwaway root, break exactly one contract in it, and copy in `eval.sh` plus a **flipped** checker:
   ```bash
   FX=$(mktemp -d); RPT=$(mktemp -d)
   mkdir -p "$FX/scripts" "$FX/.writ"
   cp -R commands agents skills adapters "$FX/"
   cp system-instructions.md README.md "$FX/"
   cp scripts/eval.sh "$FX/scripts/"
   perl -0pi -e 's/^problem:.*\n//m' "$FX/commands/status.md"
   sed 's/^CONTRACT_CHECK_SEVERITY = "warnings"/CONTRACT_CHECK_SEVERITY = "structural"/' \
     scripts/eval-leanness.py > "$FX/scripts/eval-leanness.py"
   grep -n '^CONTRACT_CHECK_SEVERITY' "$FX/scripts/eval-leanness.py"
   python3 "$FX/scripts/eval-leanness.py" --root "$FX" \
     --baseline "$FX/.writ/leanness-baseline.json" --update-baseline
   ```
2. Run the gate with the flipped checker (keep the report **outside** `$FX`, or the coverage guard flags it):
   ```bash
   bash "$FX/scripts/eval.sh" --check=leanness --report="$RPT/flipped.md" > /dev/null 2>&1
   echo "FLIPPED EXIT=$?"
   sed -n '/^## leanness/,/^Notes/p' "$RPT/flipped.md"
   ```
3. Swap in the **shipped** checker and run the gate again on the identical tree:
   ```bash
   cp scripts/eval-leanness.py "$FX/scripts/eval-leanness.py"
   bash "$FX/scripts/eval.sh" --check=leanness --report="$RPT/shipped.md" > /dev/null 2>&1
   echo "SHIPPED EXIT=$?"
   sed -n '/^## leanness/,/^- Metrics/p' "$RPT/shipped.md"
   ```
4. Confirm the committed script is untouched, then clean up:
   ```bash
   git status --porcelain scripts/   # must print nothing
   rm -rf "$FX" "$RPT"
   ```
5. Run the same proof as the suite does it, including the pin:
   ```bash
   python3 scripts/tests/test_eval_leanness_contract.py EvalShBoundaryTests FlipSeamTests -v 2>&1 | tail -14
   ```

**Expected Result:**
- Step 1: `CONTRACT_CHECK_SEVERITY = "structural"` at the statement line (line ~278), and the baseline write succeeds.
- Step 2: **`FLIPPED EXIT=1`**, and `## leanness` reads `FAIL (1 finding(s))` with the finding ``commands/status.md → problem:``.
- Step 3: **`SHIPPED EXIT=0`**, and `## leanness` reads **PASS** with the *same* finding rendered under `Notes (non-blocking):` as ``WARNING [commands/status.md → problem:]``. Same tree, same finding text, one string of difference.
- Step 4: `git status --porcelain scripts/` prints nothing.
- Step 5: all tests **OK**. `EvalShBoundaryTests` does exactly what you just did by hand; `FlipSeamTests` additionally asserts the **identical finding dicts** move (same `subject`/`what`/`fix`, same count), that `required_skills:` findings **stay in `warnings`** even when flipped, that an unrecognised value like `"blocking"` falls back to `warnings` rather than silently disabling a check, that the shipped default is `"warnings"`, and — source-level — that no contract check function references `structural` or `warnings` at all.
- **One trap worth knowing before the flip spec automates itself:** a naive `replace('CONTRACT_CHECK_SEVERITY = "warnings"', …)` rewrites the *diff preview inside the handoff comment* instead of the statement, producing a "flipped" copy that behaves exactly like the shipped one. The `^` anchor in step 1's `sed` and the newline anchor in the test both avoid it.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 7 — Files: `scripts/eval-leanness.py` (`CONTRACT_CHECK_SEVERITY`, `emit_contract_findings`); `scripts/tests/test_eval_leanness_contract.py` (`FlipSeamTests`, `EvalShBoundaryTests`); commit `bb24442`

**Notes:**

---

### Scenario 15: The handoff lives at the constant, and the constant is one line

**Source:** Business Rule 3 — "The warnings→structural flip is one named constant with one emission router." Story 7 AC 6 and 7. The next spec's whole job is a one-line diff; if the reasoning is scattered across a spec folder, that diff will be made without it.

**Preconditions:**
- None. This is a reading exercise.

**Steps:**
1. ```bash
   grep -n 'CONTRACT_CHECK_SEVERITY' scripts/eval-leanness.py
   ```
2. Read the comment block above the constant in full (roughly lines 255–278).
3. Read the router: `grep -n 'def emit_contract_findings' -A 16 scripts/eval-leanness.py`
4. Confirm every call site routes through it: `grep -n 'emit_contract_findings(' scripts/eval-leanness.py`

**Expected Result:**
- Step 1: the constant is defined **once**, assigned `"warnings"`, with the trailing hint `# -> "structural"`. Its other appearances are the comment block, the router, and the module docstring.
- Step 2: the comment names the flipping spec (`governor-enforcement`), the governing decision (ADR-020 "Enforcement sequencing (load-bearing)"), the **precondition** (the two migration specs having brought the surface into compliance so a flipped run is green on a clean tree), the reason the shipped value is asserted by the test suite, and the literal one-line diff the flip becomes. The whole handoff is at the constant.
- Step 3: `emit_contract_findings(findings, structural, warnings, severity=None)` — `severity or CONTRACT_CHECK_SEVERITY`, `structural` only on an exact match of `"structural"`, everything else to `warnings`. The fallback is stated in the docstring as deliberate: "a typo in the flip must never silently disable a check, and must never accidentally block a run."
- Step 4: seven hits — the definition, two comment references, and **four call sites in `main()`** (lines 1228–1239), one per check, with the fourth carrying `severity="warnings"` and a comment quoting `system-instructions.md`'s graceful-degradation clause. No check appends to a bucket itself.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 7 — Files: `scripts/eval-leanness.py` (constant, `emit_contract_findings`, `main`)

**Notes:**

---

## Whole-Spec: Scope, Cost, and Regression

### Scenario 16: The out-of-scope boundary held — `eval.sh` was not touched at all

**Source:** spec.md § Out of Scope — "`scripts/eval.sh`'s `check_length` limits. The command limit stays at 2000 lines… The absolute `per_surface.commands.chars` cap… Both land together in `governor-enforcement`, not here."

**Preconditions:**
- Full git history available.

**Steps:**
1. Diff `eval.sh` across every commit of this spec:
   ```bash
   git diff 0b29a61^..bb24442 -- scripts/eval.sh | wc -l
   ```
2. Confirm the three length limits are where the spec says they stay:
   ```bash
   grep -n 'limit 2000\|limit 100\|limit 95' scripts/eval.sh
   ```
3. Confirm no absolute chars cap was introduced:
   ```bash
   grep -n 'MAX_COMMANDS\|MAX_AGENTS\|MAX_SKILLS' scripts/eval-leanness.py | head
   grep -n 'def check_ceilings' -A 16 scripts/eval-leanness.py
   ```
4. Confirm the three untouched checks really are untouched:
   ```bash
   git diff 0b29a61^..bb24442 -- scripts/eval-leanness.py \
     | grep -E '^[-+].*(def check_parity|def check_coverage|def check_ceilings)'
   ```

**Expected Result:**
- Step 1: **0**. Not one line of `eval.sh` changed across the spec. The seam reaching the gate (Scenario 14) required no change to the gate — that is the point of building it as a routing constant rather than a flag.
- Step 2: three hits — spec-lite at **100** lines, `commands/_preamble.md` at **95**, commands at **2000**. Unchanged. (The 95 came from `c944ce7` in a sibling Phase 10 spec, not from this one.)
- Step 3: `check_ceilings()` still gates **counts only** — `MAX_COMMANDS`, `MAX_AGENTS`, `MAX_SKILLS` — and emits warnings. No absolute `per_surface.commands.chars` cap exists anywhere. This spec touched the ratchet's baseline *data* and its justification *semantics*; it added no absolute ceiling.
- Step 4: no output. `check_parity`, `check_coverage` and `check_ceilings` were not modified. `check_baseline()` is the one existing check this spec changed, and only in the four respects Story 1 named.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Whole spec — Files: `scripts/eval.sh` (unchanged), `scripts/eval-leanness.py`

**Notes:**

---

### Scenario 17: This spec grew the surface it governs — more than any other spec in the phase

**Source:** Business Rule 9's own risk note — "this spec's own history is the first test of whether 'growth costs a reviewable diff each time' holds under pressure." ADR-021 puts the whole product surface under a token budget. A governor that costs more than what it governs is worth seeing measured.

**Preconditions:**
- Full git history available. `python3` available.

**Steps:**
1. Measure the `scripts` surface before and after this spec, exactly as the checker measures it (bytes, not decoded characters):
   ```bash
   python3 - <<'EOF'
   import subprocess
   def measure(ref, d, exts):
       names = subprocess.run(["git","ls-tree","-r","--name-only",ref,d],
                              capture_output=True, text=True).stdout.split()
       L = C = 0
       for f in [n for n in names if n.endswith(exts)]:
           b = subprocess.run(["git","show",f"{ref}:{f}"], capture_output=True).stdout
           L += b.count(b"\n"); C += len(b)
       return L, C
   for label, ref in [("before Story 1", "0b29a61^"), ("after Story 7", "bb24442")]:
       print(label, measure(ref, "scripts/", (".py", ".sh")))
   EOF
   ```
2. Compare against the other Phase 10 specs by substituting these refs into the same helper: `fe2af84^` (phase start), `639c840` (autonomy-gate-classes), `e23fbdc` (retire-dead-prescription), `b8b96d5` (component-contract), `dfc0807` (loop-bounds), `bb24442` (this spec).
3. Size the two artifacts that carry the delta:
   ```bash
   wc -l scripts/eval-leanness.py scripts/tests/test_eval_leanness_contract.py
   python3 scripts/tests/test_eval_leanness_contract.py 2>&1 | tail -3
   ```

**Expected Result:**
- Step 1: `before Story 1 (28304, 1202759)` and `after Story 7 (29958, 1279401)` — **+1,654 lines and +76,642 chars** on the `scripts` surface.
- Step 2: the per-spec `scripts` deltas across Phase 10 are roughly `+194 / -5 / 0 / +783 / +1,654`. **This spec is the largest single-spec growth of the phase by more than 2×**, and it is the spec whose subject is growth.
- Step 3: `scripts/eval-leanness.py` is **1,257** lines; `scripts/tests/test_eval_leanness_contract.py` is **908** lines carrying **81** tests. The test file alone is most of the delta.
- **What this scenario asks you to decide:** the instrumentation was paid for honestly — five separate dated ceiling raises, no floor moved, no widened silence (Scenario 8). It is still true that the governor's own measurement code is now a significant fraction of what it measures, and that this spec added 0 lines to `commands/` while adding 1,654 to `scripts/`. If you think that trade is wrong, say so here; nothing in the implementation hides it.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Whole spec — Files: `scripts/eval-leanness.py`, `scripts/tests/test_eval_leanness_contract.py`; commits `0b29a61`…`bb24442`

**Notes:**

---

### Scenario 18: The phase-wide token position — `commands` chars rose 8.5%, and Phase 10 requires them to fall

**Source:** ADR-021 and the roadmap's Phase 10 success criterion. This spec's Check 1 and Check 2 measure the surface that criterion is about. It is worth reading the number they now report against the number the phase promised.

**Preconditions:**
- Full git history available.

**Steps:**
1. Measure `commands/` at the phase boundary and now, using the helper from Scenario 17 with `d="commands/"` and `exts=(".md",)`, for refs `fe2af84^` and `HEAD`.
2. Read the live figure from the checker:
   ```bash
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json \
     | python3 -c "import json,sys; print(json.load(sys.stdin)['metrics']['per_surface']['commands'])"
   ```
3. Read Phase 10's success criterion in `.writ/product/roadmap.md` and compare.

**Expected Result:**
- Step 1: `fe2af84^` → **10,996 lines / 516,589 chars**; `HEAD` → **11,411 lines / 560,684 chars**. That is **+44,095 chars, +8.5%**, across the phase.
- Step 2: `{'lines': 11411, 'chars': 560684}` — the same figure, live.
- Step 3: Phase 10's criterion requires the command-surface token cost to drop **materially**. It rose. The rise is not drift: `component-contract` added the three contract fields to 31 commands and `## Completion` to 18 of them (+35,124 chars) and `loop-bounds` added eight `loop:` blocks (+8,116 chars). Those are the declarations ADR-020 asked for, and they cost what a falsifiable statement costs.
- **Governor-instrumentation itself added 0 chars to `commands/`.** This spec did not cause the rise; it is the spec that can now *measure* it, and the measurement says the phase is moving the wrong way on its own headline number. Progressive disclosure — specs 6–11, unbuilt — is what is supposed to reverse it. Nothing in this UAT plan demonstrates a reversal, because none has been built.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Whole spec — Files: `.writ/product/roadmap.md`, `.writ/decision-records/adr-021-progressive-disclosure-token-budget.md`

**Notes:**

---

### Scenario 19: Full regression — everything that existed before this spec still passes

**Source:** Technical spec § Testing Strategy — "`bash scripts/tests/test_eval_leanness.sh` and the full `scripts/tests/*.py` pytest suite must stay green. `check_parity`, `check_coverage`, and `check_ceilings` are untouched, so any change there is a regression."

**Preconditions:**
- Working tree clean. **Every mutation from Scenarios 2, 3 and 4 restored** — check `git status --porcelain` before starting.

**Steps:**
1. ```bash
   git status --porcelain; echo "(empty above = clean)"
   ```
2. ```bash
   python3 scripts/tests/test_eval_leanness_contract.py 2>&1 | tail -3
   ```
3. ```bash
   bash scripts/tests/test_eval_leanness.sh 2>&1 | tail -3
   ```
4. ```bash
   python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json | read_findings
   bash scripts/eval.sh --check=leanness > /dev/null 2>&1; echo "EXIT=$?"
   ```

**Expected Result:**
- Step 1: clean. If `.writ/leanness-baseline.json` is modified, restore it from `/tmp/leanness-baseline.bak` before signing off — a left-behind mutation from Scenario 2 or 3 silently changes what the ratchet reports for everyone.
- Step 2: `Ran 81 tests` … `OK`.
- Step 3: `All 36 leanness helper assertions passed.`
- Step 4: `structural: 0  warnings: 0` and `EXIT=0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Whole spec — Files: `scripts/tests/test_eval_leanness_contract.py`, `scripts/tests/test_eval_leanness.sh`

**Notes:**

---

## Honest Notes — Read Before Signing Off

These are not scenario failures. The spec was implemented as written and the mechanism does what it claims. They are places where the *value* is narrower than the deliverable's name implies, and a signer should see them stated rather than infer strength that is not there.

1. **The four new checks report 0 findings against this repository, and always have.** The spec was authored expecting ~142 findings — 114 contract, 18 `## Completion`, 10 loop bounds. Both dependency specs (`2026-08-11-component-contract`, `2026-08-11-loop-bounds`) merged **before** these checks existed, so the surface was already compliant on the day the first check ran. Every finding **count** in Stories 3–6 is asserted against fixture trees; only *behaviour* — exit 0, findings land in `warnings`, no false finding against `visual-qa-agent.md`, no crash on absent directories — is asserted against the real repository. **These checks have never fired in anger here.** They are well-tested against synthetic non-compliance and entirely unexercised against real drift. The first genuine test of Check 1 will be the first command a future author writes without a contract, and nothing in this UAT plan simulates that on a tracked file.

2. **The checks are non-blocking by design, and that is the whole posture.** All four emit into `warnings`; `eval-leanness.py` always exits 0 and `eval.sh` renders them as non-blocking notes. Deleting `problem:` from a real command today produces a green eval run with one extra note. **Phase 10's component contract is declared and instrumented, but not enforced.** Enforcement is one string — `CONTRACT_CHECK_SEVERITY` — and it belongs to the unbuilt `governor-enforcement` spec. Scenario 14 proves the flip works end to end; it does not prove anything is currently enforced, because nothing is. Do not read a passing UAT here as "the contract is now guarded."

3. **This spec grew the surface it governs, more than any other spec in the phase.** `scripts` went **28,304 → 29,958 lines (+1,654)** and **1,202,759 → 1,279,401 chars (+76,642)** — over twice the next-largest Phase 10 delta. It recorded its own ceilings in five separate dated commits rather than batching them at the end, which is the honest form and exactly what Business Rule 9 required; Scenario 8 verifies it commit by commit. It remains true that the governor's own instrumentation is now a significant fraction of what the governor measures, that 908 of those lines are a test file for checks that find nothing, and that the same measurement code is what reports the growth.

4. **Phase-wide, the number this phase exists to reduce went up.** `commands` chars: **516,589 → 560,684 (+8.5%)** across Phase 10. Phase 10's success criterion requires that figure to drop materially. It rose — through the two migration specs' contract declarations, which are the deliverable ADR-020 asked for and which cost what sentences cost. Governor-instrumentation added nothing to `commands/` itself; it is the spec that makes the rise measurable. Progressive disclosure (specs 6–11) is the unbuilt work that is supposed to reverse it. As of this sign-off, the phase has instrumented its budget and overspent it.

5. **`required_skills:` resolution is a vacuous check and will stay one for now.** Zero declarations exist across the entire product surface — every occurrence of the token in `commands/` and `agents/` is prose in `commands/new-skill.md`. Six skills exist on disk and not one is declared by any consumer. `required_skills_declarations: 0` is the only signal distinguishing "nothing was found" from "nothing was checked", and Business Rule 8 exists solely to provide it. Scenario 10 makes that visible; verify it personally, because it is the one place in this spec where a zero could be misread as an assurance.

6. **The guard from note 5, and the compliance counts from Scenario 9, do not appear in the eval report.** `eval.sh`'s `check_leanness()` renders a fixed set of `METRIC` lines and has no branch for `contract_compliance` or `required_skills_declarations`. The spec anticipated that unknown keys would be ignored and called it backward-compatible, which it is — but the practical result is that the numbers making this spec's two most important honest claims are visible only in raw JSON, while the maintainer-facing report shows `PASS` and four metric lines that predate the spec. Scenario 11 records it. It is the smallest concrete follow-up this spec leaves behind.

7. **The strongest thing here is the silencer fix, and it is genuinely strong.** Before this spec, one sentence in a baseline entry bought permanent, unlimited, unmonitored growth on an entire surface — both metrics, every future run, any magnitude. Scenario 3 demonstrates that the exact string that used to buy that silence now produces two warnings that say *it silences nothing*. Scenario 2 demonstrates that a valid, bound justification stops silencing one unit past the ceiling it named. Scenario 4 demonstrates that none of it can make a shrinking surface warn. If you have time for only three scenarios, run 2, 3 and 4.

---

## Discrepancies Worth Recording

1. **"The four live growth warnings" is "the six" everywhere in the spec, including the locked contract.** `spec.md`, `spec-lite.md` and `sub-specs/technical-spec.md` all say four (`commands.lines`, `commands.chars`, `scripts.lines`, `scripts.chars`). Three Phase 10 specs landed before this one and `79dcc60` grew the `agents` surface too, making the live count **six** on Story 1's base. The implementation justified all six and recorded the correction in Story 1's and Story 2's measured-correction notes — but the spec body was never amended, so a reader of `spec.md` alone will look for four justified pairs and find three surfaces carrying six. The implementation is right; the spec text is stale.

2. **`agents`'s justification `text` names `79dcc60`, not `a5c5a66`.** Story 2's acceptance criterion prescribes `a5c5a66` (PR #34, v0.28.0) as the cause text for each recorded ceiling. `agents` was not grown by that commit at all — it was grown by `79dcc60`, the component-contract migration — and its `text` says so. The implementation is more accurate than the criterion it was written against.

3. **`LOOP_BEARING_COMMANDS` is cross-read from a sibling script, not the hand-maintained constant the technical spec specified.** The technical spec prescribes "a fixed list, not inferred from file contents… Adding a loop to a sixth command means adding it here, by hand, on purpose." The shipped code parses `LOOP_BEARING_COMMANDS` out of `scripts/eval-loop-bounds.py` with `ast` (never importing it), keeps a module-level literal as a fallback, and asserts the two agree. Recorded in Story 5's Task 5.3 amendment with its reasoning, and it is the better choice — but it is a divergence from the locked technical design and reads as one if you compare the documents.

4. **`contract_compliance` and `required_skills_declarations` never reach the eval report** (Scenario 11, Honest Note 6).

5. **The spec's own day-one output table is superseded and labelled as such.** `user-stories/README.md` carries both the pre-migration ~142-finding table and a "superseded by the migration" banner above it. Read the banner first; the table below it is a historical measurement, not an expectation.

---

## Sign-Off

| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | [ ] Pass [ ] Fail |
| Reviewer | | | [ ] Pass [ ] Fail |

**Overall UAT:** [ ] Pass  [ ] Fail

**Notes:**

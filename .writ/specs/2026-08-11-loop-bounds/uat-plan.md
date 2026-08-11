# UAT Plan: Loop Bounds

> **Generated:** 2026-08-11
> **Spec:** `.writ/specs/2026-08-11-loop-bounds/`
> **Stories Covered:** 5 of 5 completed
> **Total Scenarios:** 20

## How to Use This Plan

1. Work through scenarios in order (grouped by story).
2. Run the commands exactly as written, from the repository root, on a branch that contains this spec (`phase/10-component-contract` or later).
3. Mark Pass or Fail — add notes for anything that differs from the Expected Result.
4. A Fail is filed as an issue or fed back to the spec; it is not fixed inline.
5. The feature passes UAT when every scenario passes, or when a failure is explicitly accepted as a known limitation.

> **Note on this methodology repo:** the deliverables are markdown frontmatter and one Python asserter. Most scenarios are validated by reading a file or running `scripts/eval-loop-bounds.py`, not by exercising a UI.
>
> **Scenarios 12, 13, 14, 15, 16 and 18 temporarily modify a tracked file.** Each one tells you exactly how to revert. **You must revert.** Every one of those files is a shipped product file; leaving a mutation in place ships a wrong bound or a broken guard. Before starting any of them, confirm `git status --porcelain` is clean for the file named in its Preconditions, and confirm it is clean again afterwards. If you would rather not touch tracked files at all, Scenario 11's Notes describe a throwaway fixture root that reproduces every mutation identically — that is how the expected text below was captured.

## What This Spec Actually Delivered

Eight `loop:` bounds across five commands, plus a 733-line correctness asserter that refuses to let those numbers drift from the sources they were transcribed from or fall below a value a real run already reached. Read the **Honest Notes** section before you sign off — five of the eight numbers are transcriptions of bounds that already existed and already worked, one command has no runaway loop to bound at all, and one bound has zero supporting evidence and says so in the file.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|------------------|
| Story 1: Loop schema and exhaustion vocabulary | ✅ Covered | 2 | AC: 1, Fixture-set correspondence: 1 |
| Stories 2–4: The eight declared bounds | ✅ Covered | 8 | AC: 5, Judgment call: 1, Integrity: 1, Cost: 1 |
| Story 5: The loop-bounds eval check | ✅ Covered | 10 | AC: 6, Tripwire mutation: 3, Boundary: 1 |

---

## Story 1: Loop Schema and Exhaustion Vocabulary

### Scenario 1: The schema, the closed vocabulary, and why `retry` is not in it

**Source:** Story 1 AC; spec.md § The `on_exhaustion` vocabulary; Business Rule 4. Story 1 wrote no command file — it defined a contract. This scenario checks the contract is written down and internally consistent.

**Preconditions:**
- None. This is a reading exercise.

**Steps:**
1. Open `.writ/specs/2026-08-11-loop-bounds/sub-specs/technical-spec.md` and read the **Key contract** table.
2. Read the **`on_exhaustion`: the closed vocabulary and its output contract** table immediately below it.
3. Read the two paragraphs headed **Why `retry` is excluded** and **Why no "continue anyway" value**.
4. Confirm the code the exclusion rests on actually exists: `grep -n 'attempts < ' scripts/phase-state.py`.
5. Read the **Append-only within the ADR-020 block** paragraph.

**Expected Result:**
- Step 1: five keys — `unit` (string, required, distinct within a file), `max_iterations` (positive integer, required, "not a range, not `null`, not a string, not an expression"), `on_exhaustion` (enum, required), `calibrated_against` (string, required, must carry a path or the literal `no recorded run` **and** state evidence quality), `nested` (list, optional, capped at one level).
- Step 2: exactly **three** legal values — `quarantine`, `escalate`, `halt_reported` — each with a stated "legal where" and a stated required output. The set is described as closed: "a fourth value is a schema violation, not an extension point."
- Step 3: `retry` is excluded because it is the **pre-exhaustion** state, already governed *in code* by `phase-state.py`'s `attempts < 2` guard; admitting it would "create a second, weaker retry authority in markdown that contradicts an enforced one in Python." No "continue anyway" value exists because it "makes every bound advisory and deletes the reason the key exists."
- Step 4: **one hit, `scripts/phase-state.py:414`** — `if classification == "transient" and attempts < 2:`. The exclusion rests on a real guard, not on an argument.
- Step 5: `loop:` is a sibling key appended after `problem:` / `outcome:` / `exit_criteria:` in the same `---` block, with no second frontmatter block and no sidecar file, and validation is identical whether the sibling spec's keys are present or absent.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `.writ/specs/2026-08-11-loop-bounds/sub-specs/technical-spec.md`; commit `1d283cd`

**Notes:**

---

### Scenario 2: The 21 fixtures were implemented one-for-one, not reinterpreted

**Source:** Story 1 § Fixture set; Story 5 Task 5.2. Story 1 specified the fixture set and Story 5 was instructed to "implement exactly these and invent none." This scenario checks that instruction held.

**Preconditions:**
- `python3` available.

**Steps:**
1. Count the specified fixtures:
   ```
   awk '/### Fixture set/,/^## Per-command/' .writ/specs/2026-08-11-loop-bounds/sub-specs/technical-spec.md | grep -c '^| `'
   ```
2. Count the implemented ones: `python3 scripts/eval-loop-bounds.py | grep -c 'fixture-'`.
3. List them: `python3 scripts/eval-loop-bounds.py | grep 'fixture-' | awk '{print $2}'`.
4. Compare the two lists by eye, paying attention to the two fixtures whose implemented name differs from the specified name.

**Expected Result:**
- Step 1: **21** specified fixtures.
- Step 2: **25** implemented fixture scenarios — 20 named `fixture-*` and 5 named `history-fixture-*`.
- Step 3/4: every specified fixture is present. Two carry a different implemented name because they exercise the historical-run machinery rather than the schema validator: `bound-below-history` → `history-fixture-rejects-low-bound`, and `empty-state-dir` → `history-fixture-empty-state-skips`. Four scenarios exist that Story 1 did not specify, and all four are additive rather than substitute: `fixture-quarantine-with-phase-state` (the positive counterpart to the rejection case), `history-fixture-reads-runs`, `history-fixture-accepts-shipped-bounds`, and `history-fixture-malformed-skips`. **No specified fixture is missing.**

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/eval-loop-bounds.py` (`scenario_fixtures`, `scenario_history_fixtures`)

**Notes:**

---

## Stories 2–4: The Eight Declared Bounds

### Scenario 3: All eight bounds are declared, across five commands, with eight distinct units

**Source:** Locked contract — "`loop.max_iterations` + `loop.on_exhaustion` on the five verified-unbounded loop-bearing commands"; Stories 2, 3, 4 AC. This is the roadmap success criterion, checked directly.

**Preconditions:**
- Clean checkout at the repository root.

**Steps:**
1. Count bounds per file and in total:
   ```
   grep -c 'max_iterations:' commands/*.md | grep -v ':0'
   grep -h 'max_iterations:' commands/*.md | wc -l
   ```
2. List every declared unit: `grep -hE '^\s+(- )?unit:' commands/*.md | sed 's/^ *//' | sort`.
3. Tally the dispositions: `grep -hE '^\s+on_exhaustion:' commands/*.md | sed 's/^ *//' | sort | uniq -c`.
4. Read the eight bounds in context: `grep -A2 '^loop:' commands/implement-phase.md commands/implement-spec.md commands/implement-story.md commands/refactor.md commands/verify-spec.md`.

**Expected Result:**
- Step 1: exactly five files carry bounds — `implement-phase` **2**, `implement-spec` **1**, `implement-story` **3**, `refactor` **1**, `verify-spec` **1**. Total **8**. Three of the eight are nested under `implement-story`; one is nested under `implement-phase`.
- Step 2: eight units, all distinct — `agent_self_fix`, `autofix_pass`, `change`, `review_cycle`, `spec`, `spec_attempt`, `story`, `testing_cycle`. Duplication within a file is a schema violation (Scenario 11's `fixture-duplicate-unit`); across files it is merely tracked.
- Step 3: **4 × `halt_reported`, 3 × `escalate`, 1 × `quarantine`**. The single `quarantine` is `implement-phase`'s nested `spec_attempt` — the only unit in the spec with a `phase-execution-*.json` record to act on.
- Step 4: the numbers are `spec: 12`, `spec_attempt: 2`, `story: 12`, `review_cycle: 3`, `testing_cycle: 2`, `agent_self_fix: 3`, `change: 10`, `autofix_pass: 1`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 2–4 — Files: the five command files; commit `f7d579f`

**Notes:**
The roadmap's Phase 10 measurement line still reads `**0 of 5**` at `.writ/product/roadmap.md:317` and at line 11. That is the **pre-phase baseline** and is correct as a historical measurement. It is not a live counter and this spec did not update it.

---

### Scenario 4: Every one of the eight cites its evidence and states its quality

**Source:** Business Rule 1 — "Every declared bound cites the run it was calibrated against… A bound with no citation is a defect, not a warning." Business Rule 8 — thin evidence says so in the file.

**Preconditions:**
- None.

**Steps:**
1. Count citations and quality statements:
   ```
   grep -c 'calibrated_against:' commands/implement-phase.md commands/implement-spec.md commands/implement-story.md commands/refactor.md commands/verify-spec.md
   grep -c 'Evidence:' commands/implement-phase.md commands/implement-spec.md commands/implement-story.md commands/refactor.md commands/verify-spec.md
   ```
2. Read all eight citations in full — they are long by design:
   `grep -h 'calibrated_against:' commands/*.md | sed 's/^ *//' | fold -s -w 100`
3. For each, identify the evidence-quality word.
4. Confirm each citation carries a real path token or the literal `no recorded run` — the machine-checkable half of Rule 1 (Scenario 11's `fixture-citation-no-path` proves the rejection side).

**Expected Result:**
- Step 1: `calibrated_against` counts are 2 / 1 / 3 / 1 / 1 = **8**. `Evidence:` counts are the same 2 / 1 / 3 / 1 / 1 = **8**. Every bound cites, and every bound grades itself.
- Step 3: the eight quality words are — `spec`: **thin** ("three runs, one of them without a state file, and `.writ/state/` is gitignored so the sample can only shrink"); `spec_attempt`: **strong** (transcription of enforced code); `story`: **strongest of the five bounds**; `review_cycle`: **strong** (42 real records); `testing_cycle`: **adequate** ("do not read it as measured"); `agent_self_fix`: **strong** (two agents already enforce it); `change`: **weak**; `autofix_pass`: **strong by construction** ("Read this as a declaration, not a mitigation").
- Step 4: seven cite paths under `.writ/state/`, `.writ/specs/archive/`, `scripts/`, `agents/`, or `commands/`. The eighth — `refactor` — opens with the literal `no recorded run` because there is no path to cite. That is Scenario 8.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 2–4 — Files: the five command files

**Notes:**

---

### Scenario 5: The frontmatter has a matching prose bound in the command body

**Source:** Business Rule 3 — "`on_exhaustion` produces a named, resumable state — never a bare halt." A YAML key an agent never reads is not an implementation; the prose is where the behavior lives.

**Preconditions:**
- None.

**Steps:**
1. `grep -n 'Iteration bound' commands/*.md`
2. Read each of the four hits in full.
3. For `implement-story`, read the different carrier: `sed -n '615p' commands/implement-story.md`.
4. In each, look for five things: the unit name, the number, the `on_exhaustion` value, what gets recorded, and a **literal** resume command.

**Expected Result:**
- Step 1: four hits — `implement-phase.md:202`, `implement-spec.md:185`, `refactor.md:135`, `verify-spec.md:483`.
- Step 3: `implement-story` has no `**Iteration bound:**` paragraph because it already had one. Line 615's existing "Review loop: Max 3 iterations…" sentence was *extended* rather than duplicated, and now ends: "Both caps are declared as `loop.max_iterations` and the nested `testing_cycle` entry in this file's frontmatter, with `on_exhaustion: escalate`: the existing `AskQuestion` escalations *are* the implementation, and no cap may be silently continued past." That is the only line this spec modified rather than added.
- Step 4: all five name their unit, bound, disposition, what is written down, and a resume path — `/implement-phase --resume`, `/implement-spec --resume`, re-run `/refactor` over the remaining plan, `/verify-spec`. None permits a bare halt; `implement-spec`'s explicitly forbids the escape hatches: "nothing is skipped, marked complete, or self-certified to get past the bound."

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 2–4 — Files: the five command files

**Notes:**

---

### Scenario 6: `implement-phase`'s outer loop is `halt_reported`, not `quarantine` — and this is the judgment call worth a human's attention

**Source:** Business Rule 5; ADR-013; ADR-022; technical spec § `commands/implement-phase.md`. **The check cannot catch this one.** `implement-phase` *is* phase-state integrated, so `on_exhaustion: quarantine` on its outer loop would pass every assertion in `eval-loop-bounds.py`. Nothing mechanical stops a future edit from making that change. A human deciding it is right is the only control.

**Preconditions:**
- None. This is a reading and reasoning exercise.

**Steps:**
1. Read the outer bound: `sed -n '/^loop:/,/^  nested:/p' commands/implement-phase.md`.
2. Read the prose that explains it: `sed -n '202p' commands/implement-phase.md`.
3. Read what `quarantine` would actually do:
   `grep -n 'skipped_blocked\|blockedBy' scripts/phase-state.py | head`
4. Read Business Rule 5 in `.writ/specs/2026-08-11-loop-bounds/spec.md` and confirm ADR-013 and ADR-022 exist at `.writ/decision-records/adr-013-recommended-autonomous-delivery.md` and `.writ/decision-records/adr-022-autonomy-gate-classes.md`.
5. **Decide for yourself whether you agree**, then record your decision in the Notes below.

**Expected Result:**
- Step 1: the outer loop is `unit: "spec"`, `max_iterations: 12`, `on_exhaustion: halt_reported`. The nested `spec_attempt` immediately below it *is* `quarantine`. The two dispositions sit four lines apart on purpose.
- Step 2: the prose states it in the imperative — "**do not quarantine anything.** Nothing has failed at this point — the phase merely ran longer than declared, so fabricating a failure record would also mark dependents `skipped_blocked` and degrade scope. Unstarted specs stay `pending` and the phase stays `status: executing`."
- Step 3: `phase-state.py`'s quarantine path really does mark transitive dependents `skipped_blocked` with a `blockedBy` record. That is the concrete cost: quarantining an *unstarted* spec at outer-loop exhaustion would invent a failure that never happened and then cascade it into specs that were never attempted — a scope degradation both ADRs forbid.
- Step 4: Rule 5 reads "an exhausted loop may not skip a story, drop an exit criterion, relax an acceptance criterion, or mark anything Complete to get itself unstuck." Both ADRs exist.
- Step 5: the argument to weigh is that `halt_reported` costs a maintainer one `--resume` cycle and preserves a truthful state, whereas `quarantine` would auto-clean the worktree at the cost of a fabricated failure record. Mark Pass if you agree the trade favors truthfulness; mark Fail and say so if you do not.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 2 — Files: `commands/implement-phase.md`; `scripts/phase-state.py`; ADR-013, ADR-022

**Notes:**

---

### Scenario 7: The three `implement-story` numbers equal their sources today

**Source:** Business Rule 7 — existing prose bounds are transcribed, not re-derived. Story 3 AC. Scenario 13 proves the drift guard fires; this one proves the values are correct right now.

**Preconditions:**
- None.

**Steps:**
1. Read the declared numbers: `sed -n '/^loop:/,/^---$/p' commands/implement-story.md | grep -E 'unit:|max_iterations:'`.
2. Read the sources:
   ```
   grep -n 'Max 3 iterations across review' commands/implement-story.md
   grep -n 'fix iterations max' commands/implement-story.md
   grep -n 'MAX_SELF_FIX_ITERATIONS = ' agents/coding-agent.md agents/testing-agent.md
   ```
3. Confirm the counter semantics claim: read line 615 and count the increment sites it names.

**Expected Result:**
- Step 1: `review_cycle: 3`, `testing_cycle: 2`, `agent_self_fix: 3`.
- Step 2: `commands/implement-story.md:615` says "Max 3 iterations across review and visual QA gates"; `:752` says "2 fix iterations max"; both `agents/coding-agent.md:238` and `agents/testing-agent.md:231` say `MAX_SELF_FIX_ITERATIONS = 3`. Three declarations, three matching sources, and the two agent files agree with each other.
- Step 3: line 615 names **four** increment sites — Gate 3 FAIL, Gate 3.5 "Reject", Gate 3.5 "Modify spec", Gate 4.5 FAIL — sharing **one** counter, and says so explicitly ("they are not four independent budgets"). The frontmatter carries one `review_cycle` entry, not four, which is the correct representation.
- Note that these line numbers all shifted by **+6** when `2026-08-11-component-contract` landed. The citations in the frontmatter quote the *anchor text* rather than a line offset for exactly this reason, and the check greps content, never line numbers.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `commands/implement-story.md`, `agents/coding-agent.md`, `agents/testing-agent.md`

**Notes:**

---

### Scenario 8: `refactor`'s weak evidence is stated in the file, not softened

**Source:** Business Rule 8 — "A bound with thin evidence says so in the file… Inventing precision that the evidence does not support is the specific failure this rule exists to prevent."

**Preconditions:**
- None. (The tripwire that protects this text is Scenario 14.)

**Steps:**
1. `sed -n '/^loop:/,/^---$/p' commands/refactor.md`
2. Confirm the opening words of the citation: `grep -c 'no recorded run' commands/refactor.md`.
3. Confirm the claim is still true — that `/refactor` has no recorded run: `ls .writ/state/ | grep -i refactor; echo "EXIT=$?"`.
4. Read the advisory the bound sits above: `grep -n '7+ changes' commands/refactor.md`.

**Expected Result:**
- Step 1: `unit: "change"`, `max_iterations: 10`, `on_exhaustion: halt_reported`, and a citation that opens with the literal **`no recorded run`** and closes with **`Evidence: weak. Recalibrate against the first recorded run rather than re-guessing.`** In between it calls the bound what it is: "a runaway guard, not a plan-size policy."
- Step 2: **1**.
- Step 3: **no output, `EXIT=1`.** Zero `/refactor` executions have ever been recorded. The citation is accurate.
- Step 4: `commands/refactor.md:106` — the Phase 2 advisory recommending plans of 7+ changes be split into sessions. 10 sits above 7 so the bound can never fire before the advice that already exists, and the file cannot give two different answers about the same plan size.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — Files: `commands/refactor.md`

**Notes:**

---

### Scenario 9: Frontmatter integrity — `^---$` counts are UNCHANGED, not equal to 2

**Source:** Story 2/3/4 AC; commit `f7d579f` message ("`^---$` counts unchanged in every file versus HEAD").

> ⚠️ **Read this before running anything.** The obvious check here is wrong. A tester who asserts `grep -c '^---$' == 2` will report **five false corruptions**. Writ command bodies use `---` as a markdown horizontal rule, so the real counts are **4, 5, 18, 9, 17**. The only correct assertion is that each count is **identical to what it was before this spec landed**.

**Preconditions:**
- Full git history available. `f7d579f` is the commit that added the eight bounds.

**Steps:**
1. Current counts:
   ```
   for f in implement-phase implement-spec implement-story refactor verify-spec; do
     echo "$f: $(grep -c '^---$' commands/$f.md)"
   done
   ```
2. The same counts immediately before the bounds landed:
   ```
   for f in implement-phase implement-spec implement-story refactor verify-spec; do
     echo "$f: $(git show f7d579f^:commands/$f.md | grep -c '^---$')"
   done
   ```
3. Diff the two outputs by eye.
4. Confirm each `loop:` block is inside the frontmatter fence, not after it:
   `for f in implement-phase implement-spec implement-story refactor verify-spec; do awk 'NR>1 && /^---$/{print FILENAME": fence closes at line "NR; exit}' commands/$f.md; done`
   then compare against `grep -n '^loop:' commands/*.md`.

**Expected Result:**
- Steps 1 and 2 print **identical** output: `implement-phase: 4`, `implement-spec: 5`, `implement-story: 18`, `refactor: 9`, `verify-spec: 17`. Not one fence was opened, closed, or moved.
- Step 4: in every file the `loop:` line number is **less than** the closing-fence line number. The blocks are inside the frontmatter.
- If steps 1 and 2 disagree for any file, that file's frontmatter is corrupt and the scenario fails — regardless of what the absolute number is.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 2–4 — Files: the five command files; commit `f7d579f`

**Notes:**

---

### Scenario 10: The declared cost is 47 lines and the diff added nothing else

**Source:** Commit `f7d579f` ("Cost: 47 lines across five files (39 frontmatter, 8 prose)"). ADR-021 puts the command surface under a token budget; a governance feature that quietly costs 300 lines is self-defeating.

**Preconditions:**
- Full git history available.

**Steps:**
1. `git show f7d579f --numstat -- commands/`
2. Measure the frontmatter half:
   ```
   for f in implement-phase implement-spec implement-story refactor verify-spec; do
     printf '%s: ' "$f"; awk 'NR>1 && /^---$/{exit} /^loop:/{p=1} p' commands/$f.md | wc -l
   done
   ```
3. Add them up and compare against the commit's claim.

**Expected Result:**
- Step 1: `12 0`, `7 0`, `15 1`, `7 0`, `7 0` — **48 insertions, 1 deletion**, net 47.
- Step 2: `loop:` block sizes are 10, 5, 14, 5, 5 = **39 frontmatter lines**. The remaining 8 are the prose bound paragraphs (2 each for `implement-phase`, `implement-spec`, `refactor`, `verify-spec`; `implement-story` replaced one existing line instead — the single deletion).
- The claim holds exactly. Four of the five commands cost five frontmatter lines each; the two that cost more are the two that carry nested entries.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 2–4 — commit `f7d579f`

**Notes:**

---

## Story 5: The loop-bounds Eval Check

### Scenario 11: The check runs green — and reports its one skip out loud

**Source:** Story 5 AC (last); the `eval.sh` integration. Establish the baseline before mutating anything.

**Preconditions:**
- `python3` available. Working tree clean.

**Steps:**
1. `python3 scripts/eval-loop-bounds.py; echo "EXIT=$?"`
2. `python3 scripts/eval-loop-bounds.py | grep -c '^PASS'`
3. `python3 scripts/eval-loop-bounds.py | grep -E '^(FAIL|SKIP)'`
4. `bash scripts/eval.sh --check=loop-bounds` and open the report path it prints.
5. `bash scripts/eval.sh --check=loop-bounds > /dev/null 2>&1; echo "EXIT=$?"`

**Expected Result:**
- Step 1: `EXIT=0`.
- Step 2: **37**.
- Step 3: **zero `FAIL` lines, exactly one `SKIP`** — `governor-boundary-intact`, with the reason "2026-08-11-governor-instrumentation Check 3 has not landed, so loop-bound PRESENCE is currently unchecked. This check deliberately does not fill that gap…". A skip that is silent is the bug; a skip that names itself is the design.
- Step 4: the report's `## loop-bounds` section reads `PASS`, `Scenarios: 37/37 passed`, and carries the skip under **Notes (non-blocking)** as `SKIPPED [governor-boundary-intact]: …`. `SKIP` is a third TSV verb added specifically because `eval.sh`'s reader recognized only `PASS`/`FAIL` and would have dropped skip lines on the floor.
- Step 5: `EXIT=0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/eval-loop-bounds.py`, `scripts/eval.sh` (`check_loop_bounds`, registry line 56)

**Notes:**
**Throwaway fixture root** — use this instead of mutating tracked files in Scenarios 12–16 and 18 if you prefer. It reproduces every expected message below verbatim:
```
FX=$(mktemp -d)
mkdir -p "$FX"/{scripts,commands,agents,.writ/state}
cp scripts/eval-loop-bounds.py scripts/phase-state.py "$FX/scripts/"
cp commands/{implement-phase,implement-spec,implement-story,refactor,verify-spec}.md "$FX/commands/"
cp agents/{coding-agent,testing-agent}.md "$FX/agents/"
cp .writ/state/*.json "$FX/.writ/state/"
cd "$FX" && python3 scripts/eval-loop-bounds.py | grep -vc '^PASS'
```
Baseline in the fixture root is the same 37 PASS + 1 SKIP. Delete `$FX` when finished. Note that `governor-boundary-intact` skips in the fixture root too, for a different reason (`eval-leanness.py` is not copied) — the skip text is identical either way.

---

### Scenario 12: The check bites — a bound lowered below recorded history is rejected by name

**Source:** Business Rule 2, mechanized as assertion 7; Story 5 AC 5. **This is the assertion the locked contract calls hardest.** A presence check would let `max_iterations: 1` ship green on a command whose recorded runs reached 4.

**Preconditions:**
- `git status --porcelain commands/implement-spec.md` is **empty**. If it is not, stop — step 4 would discard your work.
- `ls .writ/state/*.json` returns files. **If it returns nothing, this scenario cannot run** — see Honest Note 1. The assertion will skip instead of firing, and that skip is itself the thing to verify (Scenario 17).

**Steps:**
1. Confirm the current bound: `grep -A1 '^loop:' commands/implement-spec.md`.
2. Lower it from 12 to 2:
   ```
   perl -0pi -e 's/  unit: "story"\n  max_iterations: 12/  unit: "story"\n  max_iterations: 2/' commands/implement-spec.md
   grep -A1 '^loop:' commands/implement-spec.md
   ```
3. `python3 scripts/eval-loop-bounds.py | grep '^FAIL'; python3 scripts/eval-loop-bounds.py > /dev/null; echo "EXIT=$?"`
4. **Revert immediately:** `git checkout -- commands/implement-spec.md` and confirm `git status --porcelain commands/implement-spec.md` is empty again.
5. Re-run `python3 scripts/eval-loop-bounds.py | grep -c '^PASS'` and confirm you are back to 37.

**Expected Result:**
- Step 3 prints exactly one FAIL, verbatim:
  ``FAIL	historical-run-regression	commands/implement-spec.md bounds 'story' at 2, but a recorded run in .writ/state/ already reached 4. A bound below history would have failed a run that worked - raise it, never exempt it``
  and `EXIT=1`.
- The message names **the value the run reached**, not just "too low" — that is what makes it actionable without opening a state file.
- The remediation `eval.sh` attaches is "Correct the declared bound or its citation — never exempt it." There is no exemption path, by design.
- Step 5: back to **37 PASS**.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/eval-loop-bounds.py` (`recorded_maxima`, `regression_findings`, `scenario_historical_regression`)

**Notes:**

---

### Scenario 13: The check bites hardest here — change `phase-state.py`, and the *declaration* fails

**Source:** Business Rule 7, mechanized as assertion 8; Story 5 AC 7. **This is the most important scenario in the plan.** Every other assertion could in principle be satisfied by a check that hardcoded the expected numbers — and a check that hardcodes `2` would go on passing while `phase-state.py` changed underneath it, which is worse than no check at all. This scenario changes the *source* and watches the *declaration* fail, which is only possible if the number is genuinely cross-read.

**Preconditions:**
- `git status --porcelain scripts/phase-state.py` is **empty**. If it is not, stop.
- You are changing a live production script. Revert in step 4 before doing anything else, including running other scenarios.

**Steps:**
1. Confirm the guard and the declaration currently agree:
   ```
   grep -n 'attempts < ' scripts/phase-state.py
   grep -A3 '^  nested:' commands/implement-phase.md
   ```
2. Change the guard — **and touch nothing in `commands/`**:
   ```
   sed -i '' 's/attempts < 2/attempts < 3/' scripts/phase-state.py
   grep -n 'attempts < ' scripts/phase-state.py
   ```
   (On GNU `sed`, drop the `''`.)
3. `python3 scripts/eval-loop-bounds.py | grep '^FAIL'`
4. **Revert immediately:** `git checkout -- scripts/phase-state.py`, then confirm `grep -n 'attempts < ' scripts/phase-state.py` shows `2` again and `git status --porcelain scripts/phase-state.py` is empty.
5. Re-run `python3 scripts/eval-loop-bounds.py | grep -c '^PASS'` and confirm 37.
6. Confirm for yourself that nothing is hardcoded: `grep -n 'attempts' scripts/eval-loop-bounds.py`.

**Expected Result:**
- Step 1: `scripts/phase-state.py:414` reads `attempts < 2`; `commands/implement-phase.md` declares `spec_attempt` at `max_iterations: 2`. Same number, two files.
- Step 3 prints exactly one FAIL, verbatim:
  ``FAIL	drift-spec-attempt	implement-phase bounds spec_attempt at 2, but scripts/phase-state.py enforces `attempts < 3`. The declaration transcribes the code; it may not diverge from it``
  **You edited Python and a markdown frontmatter declaration failed.** That is the proof: the `2` in the message came out of `phase-state.py`, and the `3` came out of your edit. Neither is written in the check.
- Step 6: the only occurrences are the regex `r"attempts\s*<\s*(\d+)"` and the message that interpolates what it found. No literal `2` appears as an expected value anywhere.
- Step 5: back to **37 PASS**.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/eval-loop-bounds.py` (`scenario_transcription_drift`, `first_int`); `scripts/phase-state.py:414`

**Notes:**
The same cross-read protects `implement-story`'s three numbers. If you want a second data point, change `Max 3 iterations across review` to `Max 4 iterations across review` at `commands/implement-story.md:615`, run the check, and expect `FAIL drift-review-cycle`. **Revert it.** Note that these cross-reads read the command body with the frontmatter *stripped*, so a declaration can never satisfy itself by quoting its own number.

---

### Scenario 14: The anti-false-precision guard — `no recorded run` cannot be quietly upgraded

**Source:** Business Rule 8; Story 5 AC 8. `/refactor`'s bound rests on nothing. The literal is the admission, and the admission is the deliverable.

**Preconditions:**
- `git status --porcelain commands/refactor.md` is **empty**.

**Steps:**
1. Confirm the literal is there: `grep -c 'no recorded run' commands/refactor.md`.
2. Replace the admission with a confident-sounding citation that still contains a real path — this is what a well-meaning future edit looks like:
   ```
   sed -i '' 's/no recorded run - zero/zero/' commands/refactor.md
   grep -c 'no recorded run' commands/refactor.md
   ```
3. `python3 scripts/eval-loop-bounds.py | grep '^FAIL'`
4. **Revert immediately:** `git checkout -- commands/refactor.md`; confirm `grep -c 'no recorded run' commands/refactor.md` is 1 and the tree is clean.
5. Re-run and confirm 37 PASS.

**Expected Result:**
- Step 1: **1**. Step 2: **0**.
- Step 3 prints exactly one FAIL, verbatim:
  ``FAIL	refactor-no-recorded-run-literal	commands/refactor.md's calibrated_against must contain the literal 'no recorded run'. /refactor has zero recorded executions; replacing that admission with a confident-looking citation requires an explicit edit, not a drift``
- Note what did *not* fire: the citation still contained a valid path token, so assertion 4 was satisfied and the generic citation check stayed green. Only the literal guard caught it. A bound may not become better-evidenced than it is by rewording, and it takes a deliberate edit against a named failure message to try.
- Step 5: back to **37 PASS**.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/eval-loop-bounds.py` (`scenario_transcription_drift`, `NO_RECORDED_RUN`); `commands/refactor.md`

**Notes:**

---

### Scenario 15: `on_exhaustion: retry` is rejected by name, with the reason

**Source:** Business Rule 4; Story 5 AC 3. Rejecting the value is easy. Rejecting it with an explanation is what stops the next author from re-proposing it.

**Preconditions:**
- `git status --porcelain commands/verify-spec.md` is **empty**.

**Steps:**
1. `sed -i '' 's/^  on_exhaustion: halt_reported$/  on_exhaustion: retry/' commands/verify-spec.md`
2. `python3 scripts/eval-loop-bounds.py | grep '^FAIL'`
3. **Revert immediately:** `git checkout -- commands/verify-spec.md`; confirm the tree is clean.
4. Confirm the fixture-driven version of the same assertion also checks the *reason*, not just the rejection:
   `grep -n 'PRE-exhaustion' scripts/eval-loop-bounds.py`
5. Re-run and confirm 37 PASS.

**Expected Result:**
- Step 2 prints one FAIL, verbatim:
  ``FAIL	schema-verify-spec	commands/verify-spec.md loop: on_exhaustion 'retry' is illegal. Retry is a PRE-exhaustion state, already governed in code by scripts/phase-state.py's `attempts < 2` guard; admitting it here would create a second, weaker retry authority in markdown. Legal values: quarantine, escalate, halt_reported``
- The message does three things: names the illegal value, gives the reason (retry is *pre*-exhaustion, and it is already governed in Python by the `attempts < 2` guard), and lists the legal set.
- Step 4: two hits — the message itself, and `fixture-on-exhaustion-retry`, which asserts the message contains `'retry' is illegal` **and** `PRE-exhaustion` **and** `attempts < 2`. The explanation is under test, not just the verdict. A future author who shortens the message to "illegal value" fails the fixture.
- Step 5: back to **37 PASS**.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/eval-loop-bounds.py` (`validate_entry`, `scenario_fixtures`)

**Notes:**

---

### Scenario 16: `quarantine` is legal only where a `phase-execution-*.json` record exists

**Source:** Business Rule 4 / technical spec § `on_exhaustion` legality; Story 5 AC 4. `quarantine` shells out to `scripts/phase-state.py quarantine`, which needs a record to act on. Declaring it where no record exists is a promise the command cannot keep.

**Preconditions:**
- `git status --porcelain commands/refactor.md` is **empty**.

**Steps:**
1. `sed -i '' 's/^  on_exhaustion: halt_reported$/  on_exhaustion: quarantine/' commands/refactor.md`
2. `python3 scripts/eval-loop-bounds.py | grep '^FAIL'`
3. **Revert immediately:** `git checkout -- commands/refactor.md`; confirm the tree is clean.
4. Repeat steps 1–3 for `commands/implement-story.md` (its three entries use `escalate`, so substitute `escalate` → `quarantine` on the top-level entry only) and for `commands/verify-spec.md`. Revert each.
5. Confirm the rule is derived, not hardcoded: `grep -n 'phase-execution' scripts/eval-loop-bounds.py`.
6. Confirm the positive case is also tested: `python3 scripts/eval-loop-bounds.py | grep 'quarantine'`.

**Expected Result:**
- Step 2 prints, verbatim:
  ``FAIL	schema-refactor	commands/refactor.md unit 'change' declares on_exhaustion: quarantine, but the command has no phase-execution-*.json record to quarantine against. Use escalate (or halt_reported) instead``
- Step 4: the equivalent `schema-implement-story` and `schema-verify-spec` failures. All three commands reject `quarantine`.
- Step 5: legality is computed as `integrated = "phase-execution" in text` — read from the command file itself. There is no allow-list of command names, so a command that later gains phase-state integration gains the right to `quarantine` automatically, and one that loses it loses the right.
- Step 6: **both** `fixture-quarantine-without-phase-state` (rejected) and `fixture-quarantine-with-phase-state` (accepted) pass. The rule is two-sided — it is not a blanket ban.
- After all reverts: back to **37 PASS**.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/eval-loop-bounds.py` (`load_command`, `validate_loop`)

**Notes:**

---

### Scenario 17: The historical-run assertion SKIPs loudly when it has no input

**Source:** Story 5 AC 6; the Error & Rescue Map row "`.writ/state/` empty (fresh clone, CI)". **This is the failure mode the whole phase diagnosed, turned on the check itself.** `.writ/state/` is gitignored, so assertion 7 has no input in CI or on a fresh clone. A check that quietly passes because its input is absent is exactly what ADR-020 found had happened to `## Completion`.

**Preconditions:**
- `python3` available. **This scenario mutates nothing** — it builds a throwaway root.

**Steps:**
1. Confirm the gitignore claim: `git check-ignore -v .writ/state/execution-20260718-1101.json`.
2. Build a root with the commands but no state:
   ```
   E=$(mktemp -d)
   mkdir -p "$E"/{scripts,commands,agents,.writ/state}
   cp scripts/eval-loop-bounds.py scripts/phase-state.py "$E/scripts/"
   cp commands/{implement-phase,implement-spec,implement-story,refactor,verify-spec}.md "$E/commands/"
   cp agents/{coding-agent,testing-agent}.md "$E/agents/"
   (cd "$E" && python3 scripts/eval-loop-bounds.py | grep '^SKIP'; echo "EXIT=$?")
   ```
3. Read the `historical-run-regression` skip reason word for word.
4. Confirm the skip surfaces in the eval report rather than being swallowed: re-read the **Notes (non-blocking)** section of the report from Scenario 11, and read the comment block above `check_loop_bounds` in `scripts/eval.sh` (around line 2867).
5. `rm -rf "$E"`.

**Expected Result:**
- Step 1: `.gitignore:2:.writ/state/` — confirmed gitignored.
- Step 2: **two** SKIP lines. The one that matters:
  ``SKIP	historical-run-regression	.writ/state/ holds no readable run records (it is gitignored, so this is expected in CI and on a fresh clone). The bounds were NOT compared against recorded history in this run - re-run on a working copy that has the run files``
- Step 3: the reason says the bounds were **NOT compared** — in those words. It does not say "no findings" and it does not say "passed". A reader of CI output cannot mistake this for evidence that the bounds are calibrated.
- Step 4: `eval.sh` routes `SKIP` to `add_note`, so skips appear in the report as non-blocking notes even when the check passes overall. The comment records that `SKIP` was added as a third TSV verb precisely because the pre-existing reader recognized only `PASS`/`FAIL` and would have dropped the line silently.
- **This scenario passes only if the skip is visible and states its reason.** A green run with no mention of the skip is a failure of this scenario even though the exit code is 0.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/eval-loop-bounds.py` (`emit_skip`, `scenario_historical_regression`); `scripts/eval.sh:2866-2915`

**Notes:**

---

### Scenario 18: The presence/correctness boundary holds — a deleted `loop:` block is a SKIP, not a finding

**Source:** Out of Scope — "Presence checking… `2026-08-11-governor-instrumentation` Check 3 already owns this"; Story 5 AC 1. Two checks reporting the same missing block is how a check registry becomes noise a maintainer learns to skim.

**Preconditions:**
- `git status --porcelain commands/verify-spec.md` is **empty**.

**Steps:**
1. Delete `verify-spec`'s entire `loop:` block:
   ```
   python3 - <<'EOF'
   import re
   p = 'commands/verify-spec.md'
   t = open(p).read()
   open(p, 'w').write(re.sub(r'\nloop:\n(?:  .*\n)+', '\n', t, count=1))
   EOF
   grep -c '^loop:' commands/verify-spec.md
   ```
2. `python3 scripts/eval-loop-bounds.py | grep -E '^(FAIL|SKIP)'; python3 scripts/eval-loop-bounds.py > /dev/null; echo "EXIT=$?"`
3. **Revert immediately:** `git checkout -- commands/verify-spec.md`; confirm the tree is clean and `grep -c '^loop:' commands/verify-spec.md` is 1.
4. Confirm the omission is deliberate and documented: `grep -n "require_literal" scripts/eval.sh | head -3`, then read the comment block at the end of `check_loop_bounds` in `scripts/eval.sh`.
5. Re-run and confirm 37 PASS.

**Expected Result:**
- Step 1: **0**.
- Step 2: **no FAIL. `EXIT=0`.** A new SKIP appears:
  ``SKIP	schema-verify-spec	commands/verify-spec.md declares no loop: block - deferred_to_check3 (2026-08-11-governor-instrumentation Check 3 owns presence)``
  A missing block is another check's finding, and this check says whose.
- Step 4: `check_loop_bounds` carries no `require_literal 'loop:'`, and a comment states the absence is on purpose — "Adding a `require_literal` for 'loop:' would report the same missing block twice, which is how a check registry becomes noise a maintainer learns to skim."
- **The honest cost, stated:** `2026-08-11-governor-instrumentation` has not landed, so presence is *currently unchecked by anything* — which is what the `governor-boundary-intact` skip in Scenario 11 is telling you. Deleting a `loop:` block today produces a green eval run with two skips. That is the correct behavior for this check and a real open gap in the phase. Do not close it by adding a presence assertion here.
- Step 5: back to **37 PASS**.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/eval-loop-bounds.py` (`scenario_shipped_commands`, `scenario_governor_boundary`); `scripts/eval.sh` (`check_loop_bounds` trailing comment)

**Notes:**

---

### Scenario 19: `verify-spec`'s bound of 1 is guarded by structure, not by a naive grep

**Source:** Story 4 AC; Story 5 assertion 8. `verify-spec`'s bound is only true while the command stays single-pass. The guard has to detect an added re-check step — while ignoring the bound's own citation, which says the words "re-check", "re-run" and "re-verify" *while asserting their absence*. A naive grep fires on the citation and reports permanent false corruption.

**Preconditions:**
- `git status --porcelain commands/verify-spec.md` is **empty**.

**Steps:**
1. Show the trap: `grep -c 're-check\|re-run\|re-verify' commands/verify-spec.md`.
2. Confirm the guard is nonetheless green today: `python3 scripts/eval-loop-bounds.py | grep 'verify-spec-no-recheck'`.
3. Add a real re-check step:
   ```
   printf '\n#### 4.5: Re-check After Fixes\n\nRun the checks again.\n' >> commands/verify-spec.md
   python3 scripts/eval-loop-bounds.py | grep '^FAIL'
   ```
4. **Revert immediately:** `git checkout -- commands/verify-spec.md`; confirm the tree is clean.
5. Read the guard: `grep -n 'structural = \|offenders = ' scripts/eval-loop-bounds.py`.
6. Re-run and confirm 37 PASS.

**Expected Result:**
- Step 1: a **non-zero** count. The words are in the file, in the citation that argues no such step exists.
- Step 2: `PASS verify-spec-no-recheck-step` — the guard is not fooled by prose describing an absence.
- Step 3 prints, verbatim:
  ``FAIL	verify-spec-no-recheck-step	commands/verify-spec.md gained a re-check step (['#### 4.5: Re-check After Fixes']). Its bound of 1 auto-fix pass is justified only by the command being single-pass by construction - re-derive the bound``
  The message names the offending line and tells the maintainer the consequence: the bound must be re-derived, not the heading removed.
- Step 5: the guard filters to heading and numbered-step lines (`^\s*(#{2,4} |\d+\.\d* )`) before matching, so it reads *structure*. That is the difference between a guard that fires on a new step and one that fires on a sentence.
- Step 6: back to **37 PASS**.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/eval-loop-bounds.py` (`scenario_transcription_drift`, verify-spec block); `commands/verify-spec.md`

**Notes:**

---

### Scenario 20: Full Tier 1 is still green, and the bounds really were compared against this machine's history

**Source:** Story 5 AC (last); Story 5 implementation record — "observed maxima are `spec=5`, `story=4`… No declared bound would have failed any recorded run."

**Preconditions:**
- Working tree clean — every mutation from Scenarios 12–19 reverted. Check with `git status --porcelain`.
- `.writ/state/*.json` present (a maintainer working copy, not CI).

**Steps:**
1. `git status --porcelain` — confirm no leftover mutations in `commands/` or `scripts/`.
2. `bash scripts/eval.sh > /dev/null 2>&1; echo "EXIT=$?"` then open the newest report under `.writ/state/eval-*.md` and read its Summary.
3. Print the maxima the check actually computed:
   ```
   python3 -c "
   import importlib.util
   from pathlib import Path
   s = importlib.util.spec_from_file_location('m', 'scripts/eval-loop-bounds.py')
   m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
   print(m.recorded_maxima(Path('.writ/state')))
   "
   ```
4. Compare each maximum against its declared bound.
5. `ls .writ/state/*.json`

**Expected Result:**
- Step 1: clean. If anything from Scenarios 12–19 is still modified, revert it before signing off.
- Step 2: `EXIT=0`, Summary reports `Findings: 0`, `Run errors: 0`. The `## loop-bounds` section reads `PASS`, `Scenarios: 37/37 passed`.
- Step 3: `({'spec': 5, 'story': 4}, [])` — five specs is the largest phase with a surviving state file, four stories the largest recorded spec run, and **no** parse notes (every state file was readable).
- Step 4: `spec` 12 > 5, `story` 12 > 4, `spec_attempt` 2 = the enforced guard, `review_cycle` 3 > the archived maximum of 2. **No declared bound would have failed any recorded run.**
- Step 5: ten JSON files including `phase-execution-20260719-121255.json` (Phase 9, 3 specs) and `phase-execution-20260811-2030.json` (Phase 10, 5 specs — the one that superseded the spec's authored "largest observed = 4"). These files exist only on this machine; see Honest Note 1.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/eval-loop-bounds.py`; `scripts/eval.sh`

**Notes:**

---

## Honest Notes — Read Before Signing Off

These are not scenario failures. The spec was implemented as written and the check does what it claims. They are places where the *value* of the work is narrower than the roadmap line implies, and a signer should see them stated rather than infer strength that is not there.

1. **The strongest assertion does not run in CI.** `.writ/state/` is gitignored (`.gitignore:2`). Assertion 7 — the historical-run regression check, the one the locked contract calls hardest — binds only on a maintainer's working copy that happens to still have the run files, and SKIPs everywhere else. **A check that silently passes because its input is absent is the exact failure mode this phase diagnosed.** The implementation confronts this rather than hiding it: `SKIP` was added as a third TSV verb specifically because `eval.sh`'s reader would have dropped the line, and the skip reason says the bounds were "NOT compared against recorded history in this run." Scenario 17 exists to verify the skip is *reported with its reason*, not silent. Verify it personally — it is the load-bearing part. Note also that the run history can only shrink: nothing archives these files, so the calibration sample for a future recalibration is decaying.

2. **Five of the eight numbers are transcriptions, not design.** `implement-story`'s 3 and 2 were already declared in prose and already honored; `MAX_SELF_FIX_ITERATIONS = 3` was already enforced by two agent definitions; `phase-state.py`'s `attempts < 2` was already enforced in code and is the only bound in Writ that was ever *executable*. Business Rule 7 required them to be carried across unchanged, and they were. The roadmap's "**0 of 5** loop-bearing commands declare an iteration bound" counts **declarations** and is literally true — no `loop:`, `max_iterations`, or `on_exhaustion` token existed anywhere in the repo before this spec. But the implied risk was overstated. The honest restatement, which the spec's own story README makes: **3 of 5 bounds were missing and 2 were unenforceable prose.** What this spec changed for those five numbers is that they are now lintable and cannot drift from their sources — real, and smaller than "the loops were unbounded."

3. **`/verify-spec` has no runaway loop at all.** Its auto-fix is a single linear pass — Phase 2 checks, Phase 4 fixes, Phase 5 report — with no re-check step to loop back into. Its `max_iterations: 1` is a **declaration, not a mitigation**, and the file says so in those words. No `/verify-spec` runaway has ever been observed because there is no construct that could produce one. Including it in the "0 of 5" figure is defensible as a missing declaration and misleading as a missing bound. Scenario 19's guard is the real deliverable for this command: it makes the *assumption* falsifiable, so if someone adds a re-check pass later the bound fails rather than silently becoming wrong.

4. **`/refactor`'s bound has zero supporting runs.** Not thin evidence — none. `/refactor` has never been recorded executing anywhere in `.writ/state/`, and 10 was chosen only because it sits above an existing advisory sentence recommending that plans of 7+ changes be split into sessions. The file states this in the citation (`no recorded run`, `Evidence: weak`, "a runaway guard, not a plan-size policy") and Scenario 14 proves the admission cannot be reworded away without failing a named check. That is the strongest available handling of a number with no evidence, and it is not a substitute for evidence. Recalibrate after the first recorded `/refactor` run.

5. **Re-verification at implementation time moved three authored figures. Zero bounds changed.** (a) The spec claims the largest phase observed was **4 specs**, roadmap-attested with no surviving state file. Re-measurement found `.writ/state/phase-execution-20260811-2030.json` with `specOrder` length **5** — the largest phase that *does* have a state file. (b) The archived iteration distribution is **39×1 and 3×2**, not the spec's 38×1 and 4×2; the maximum is still 2, so the 3 still keeps one iteration of headroom. (c) Every cited source line shifted **+6** when `2026-08-11-component-contract` landed, which is why the shipped citations quote anchor *text* instead of line numbers. The corrections are recorded in `sub-specs/technical-spec.md` § "Re-verification at implementation," but **`spec.md` still carries the superseded figures** at lines 91, 94 and 95 (`Largest observed = **4**`, `38 at 1 iteration, 4 at 2`, `implement-story.md:595`/`:732`). If you read `spec.md` alone you will read numbers the implementation already corrected. Prefer the technical spec's re-verification table and the citations in the command files themselves.

6. **A caution for anyone verifying figure (b) by hand.** The naive command `grep -rc 'Iteration count' .writ/specs/archive/` returns **45**, not 42 — because `.writ/specs/archive/2026-08-04-spec-lifecycle-archival/backups/` contains duplicate copies of three story files. Excluding `/backups/` gives exactly 42 records, 39 at 1 and 3 at 2, matching the shipped citation. The citation is correct; the naive grep is not.

7. **Nothing here counts iterations at runtime.** Writ commands are markdown read by a model. `loop:` is a declared, lintable contract the model is expected to follow; `eval-loop-bounds.py` verifies the declaration is well-formed and calibrated. No interpreter enforces a bound while a command runs, and no scenario in this plan demonstrates one, because none exists. A passing UAT means the *declarations* are correct and drift-protected — not that a runaway loop would be stopped by machinery.

---

## Sign-Off

| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | [ ] Pass [ ] Fail |
| Reviewer | | | [ ] Pass [ ] Fail |

**Overall UAT:** [ ] Pass  [ ] Fail

**Notes:**

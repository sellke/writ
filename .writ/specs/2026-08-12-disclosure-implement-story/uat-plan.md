# UAT Plan: Progressive Disclosure Pilot — `implement-story`

> **Generated:** 2026-08-12
> **Spec:** `.writ/specs/2026-08-12-disclosure-implement-story/`
> **Stories Covered:** 6 of 6 completed
> **Total Scenarios:** 21

## How to Use This Plan

1. Work through scenarios in order (grouped by theme).
2. Run the commands exactly as written, from the repository root, on a branch that contains this spec (`phase/10-progressive-disclosure` or later).
3. Mark Pass or Fail — add notes for anything that differs from the Expected Result.
4. A Fail is filed as an issue or fed back to the spec; it is not fixed inline.
5. The feature passes UAT when every scenario passes, or when a failure is explicitly accepted as a known limitation.

> **Note on this methodology repo:** the deliverables are markdown files and one measuring script. Almost every scenario is a `grep`, a `wc`, or a run of `python3 scripts/measure-invocation.py`.
>
> **Commits.** `9e76d1e` is the base — the last commit before this spec's first story, and the SHA the no-drift inventory was captured from. `1dfe92b` is the lane merge that closed the spec. `5dbaf1a` is the follow-on commit that closed the five sibling specs. Every `git show <base>:` below means `git show 9e76d1e:`.
>
> **Scenarios 4 and 15 temporarily modify `commands/implement-story.md`, a shipped product file.** Each gives exact backup and restore commands. **You must restore.** Confirm `git status --porcelain commands/implement-story.md` is empty before you start and empty again when you finish. Both scenarios also describe a throwaway fixture root that reproduces the mutation without touching a tracked file — that is how the expected output below was captured, and it is the safer path.
>
> **Read Scenarios 16 through 21 before you sign off.** This spec was Phase 10's pilot and it returned a **negative result on its headline measure**. Six of the twenty-one scenarios exist to make sure a reader of the artifacts arrives at that conclusion rather than at the flattering one.

## What This Spec Actually Delivered

`commands/implement-story.md` went from 52,709 bytes / 989 lines to **24,837 bytes / 340 lines**, with 27,872 bytes of procedure moved into eight new `SKILL.md` files loaded by inline `Read` at the step that needs them. The **floor** — what every invocation pays regardless of path — fell **35.9%**, from 77,669 to 49,797. That is real and it is the win.

The **full-path ceiling regressed**: 91,903 bytes against the 83,770 the monolith cost, **+8,133 / +9.7%**, against a projection of +4.1%. The eight extracted files carry 36,005 bytes to replace 27,872 removed — **8,133 bytes of pure per-file scaffolding overhead, about 1,017 bytes per skill**. `--quick` saved 1.8%, not the projected 5.9%. **The five sibling disclosure specs were closed unimplemented on this evidence** (commit `5dbaf1a`).

And nobody has yet watched the mechanism work. This spec was built by `/implement-spec`; no `/implement-story` invocation of the rewritten command has occurred. **Scenario 20 is the most valuable scenario in this plan and it is the one that is still open.**

## Coverage Summary

| Group | Scenarios | What it establishes |
|---|---|---|
| A. Budget and shape | 1–2 | The byte budget was met and the floor moved |
| B. Placement of the reads | 3–4 | The mechanism is conditional, not eager — and the tripwire that proves it |
| C. No behavioral drift | 5–8 | The 281-row inventory, spot-checkable in ten minutes |
| D. Pinned literals | 9–12 | All twelve asserters still pass, including the one the spec missed |
| E. Skills well-formed | 13–14 | Lifecycle status, lint, no chaining |
| F. Graceful degradation | 15 | An unreadable skill path warns; it never fails |
| G. Honesty — the negative result | 16–21 | The regression, its cause, its consequence, and the open criterion |

---

## A. Budget and Shape

### Scenario 1: The command met its byte budget and collapsed to a third of its lines

**Source:** Story 5 AC; ADR-021 amendment 1, which makes an absolute **24,960-byte** budget the binding instrument in place of the 400-line cap.

**Preconditions:**
- Clean checkout at the repository root. `python3` available.

**Steps:**
1. Measure the file directly: `wc -c -l commands/implement-story.md`
2. Measure what the instrument reports:
   ```
   python3 scripts/measure-invocation.py --root . --command implement-story \
     | python3 -c 'import json,sys; c=json.load(sys.stdin)["commands"]["implement-story"]; print(c["command_bytes"], c["command_lines"])'
   ```
3. Measure the budget it is compared against — the shared base every invocation pays before the command file is opened:
   ```
   python3 scripts/measure-invocation.py --root . --command implement-story \
     | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["base"])'
   ```
4. Measure the file it replaced: `git show 9e76d1e:commands/implement-story.md | wc -c -l`

**Expected Result:**
- Step 1: **340 lines, 24,837 bytes.**
- Step 2: `24837 340` — the instrument and `wc` agree.
- Step 3: `bytes: 24960`, composed of `system-instructions.md` **20,153** and `commands/_preamble.md` **4,807**. `24,837 ≤ 24,960` — the command costs less to load than the contract it runs inside, with **123 bytes of headroom**.
- Step 4: **989 lines, 52,709 bytes.** The reduction is −649 lines / −65.6% and −27,872 bytes / −52.9%.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — `commands/implement-story.md`; commit `c4a5bf4`

**Notes:**
The 24,960 budget is **not yet enforced by anything**. `scripts/eval.sh` does not check it; implementing it belongs to `2026-08-12-governor-enforcement`. Until that lands, this file is compliant with a budget nothing asserts, and the 123 bytes of headroom can be spent by any later edit without a check firing.

---

### Scenario 2: The floor fell 35.9%, and every field of the before/after table reproduces

**Source:** `load-report.md` § Before and after; Story 6 AC.

**Preconditions:**
- None beyond Scenario 1.

**Steps:**
1. Dump the full measurement:
   ```
   python3 scripts/measure-invocation.py --root . --command implement-story
   ```
2. Read the eight fields that make up the verdict: `command_bytes`, `command_lines`, `eager_bytes`, `floor_bytes`, `conditional_bytes`, `ceiling_bytes`, `base_share_of_floor`, and the length of `conditional_skills`.
3. Check the arithmetic yourself: `floor_bytes` should equal `base_bytes + command_bytes + eager_bytes`, and `ceiling_bytes` should equal `floor_bytes + conditional_bytes`.
4. Read the `ceiling_note` field in the same JSON.

**Expected Result:**
- Step 2: `command_bytes` **24,837**; `command_lines` **340**; `eager_bytes` **0**; `floor_bytes` **49,797**; `conditional_bytes` **42,106**; `ceiling_bytes` **91,903**; `base_share_of_floor` **0.5012**; `conditional_skills` has **9** entries.
- Step 3: `24,960 + 24,837 + 0 = 49,797` ✓ and `49,797 + 42,106 = 91,903` ✓.
- Floor delta against the 77,669 the monolith's floor cost: **−27,872 / −35.9%**. Half the floor (50.1%) is now the shared base rather than the command — that ratio is the point of the exercise.
- Step 4: the instrument says in its own output that `ceiling_bytes` is an **envelope, not a path** — it sums every inline read including reads on mutually exclusive branches no single run can both reach. **Do not report the ceiling as what a run costs.** Every path figure in Scenarios 16 and 17 is derived by hand, by subtraction, because the script does not model paths.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — `load-report.md`; commits `1457f51`, `27c7ea6`

**Notes:**

---

## B. Placement of the Reads

### Scenario 3: The mechanism is genuinely conditional — nothing is declared, nothing is hoisted

**Source:** ADR-021 amendment 2, which replaces `required_skills:` with the inline `Read` because a static frontmatter array is per-command and cannot express per-invocation; Story 1 AC.

**Preconditions:**
- None.

**Steps:**
1. Confirm nothing is declared in frontmatter: `grep -c '^required_skills:' commands/implement-story.md`
2. Confirm the instrument agrees:
   ```
   python3 scripts/measure-invocation.py --root . --command implement-story \
     | python3 -c 'import json,sys; c=json.load(sys.stdin)["commands"]["implement-story"]; print("eager_bytes", c["eager_bytes"]); print("eager_skills", c["eager_skills"]); print("hoisted_skills", c["hoisted_skills"]); print("unresolved_skills", c["unresolved_skills"])'
   ```
3. List every inline read and the line it sits on: `grep -n 'Read skills/' commands/implement-story.md`
4. Find the structural boundary the instrument uses: `grep -nE '^#{2,4} (Command Process|Step |Gate |Phase )' commands/implement-story.md | head -3`
5. Confirm each of the nine skills is read exactly once:
   ```
   grep -o 'Read skills/[a-z-]*/SKILL.md' commands/implement-story.md | sort | uniq -c
   ```

**Expected Result:**
- Step 1: **0**. The command declares no skills.
- Step 2: `eager_bytes` **0**, `eager_skills` **[]**, `hoisted_skills` **[]**, `unresolved_skills` **[]**. All four empty is the whole placement claim in one command.
- Step 3: **nine** reads, at lines **102, 116, 148, 157, 185, 211, 278, 280, 282** — `story-context-assembly`, `dependency-context-loading`, `boundary-map-computation`, `tdd-cycle`, `change-surface-classification`, `drift-triage`, `project-context-snapshot`, `what-was-built-authoring`, `story-commit-provenance`. The lowest is line **102**.
- Step 4: `## Command Process` at line **71**, `### Step 1: Story Selection` at line **73**. Every read is below both.
- Step 5: nine lines, each with count **1**. A skill read twice would break the `--quick` derivation in Scenario 17, since that arithmetic subtracts each skipped skill exactly once.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — `commands/implement-story.md:102,116,148,157,185,211,278,280,282`

**Notes:**
Line 116's `dependency-context-loading` read sits **inside the has-dependencies branch**, not at the top of Step 2. That placement is worth 4,858 bytes on every dependency-free story and is the largest mode-independent conditional win in the file. If a later edit moves it up to the head of Step 2, `hoisted_skills` will *not* catch it — the instrument only checks the first-step boundary, not branch depth. Check it by eye.

---

### Scenario 4: Hoist one read and watch the tripwire fire

**Source:** `measure-invocation.py:141` (`FIRST_STEP`), `:185–187` (hoist detection), `:298` (the warning). Story 1's ruling that an inline read above the first step is *eager loading in conditional syntax*.

> **This scenario modifies a tracked file.** Follow the backup and restore steps exactly. A safer alternative that touches nothing tracked is in the Notes and produces identical output.

**Preconditions:**
- `git status --porcelain commands/implement-story.md` prints **nothing**. Do not start otherwise.

**Steps:**
1. Back up the file:
   ```
   cp commands/implement-story.md /tmp/implement-story.md.uat-bak
   ```
2. Insert a read **above** the `## Command Process` heading at line 71:
   ```
   awk 'NR==71{print "`Read skills/story-context-assembly/SKILL.md`"; print ""}{print}' \
     /tmp/implement-story.md.uat-bak > commands/implement-story.md
   ```
3. Run the instrument in table form and look at the bottom of the output:
   ```
   python3 scripts/measure-invocation.py --root . --command implement-story --format table | grep WARNING
   ```
4. Read the structured fields:
   ```
   python3 scripts/measure-invocation.py --root . --command implement-story \
     | python3 -c 'import json,sys; d=json.load(sys.stdin); c=d["commands"]["implement-story"]; print(c["command_bytes"], c["floor_bytes"], c["ceiling_bytes"], c["hoisted_skills"])'
   ```
5. Check the exit code: `echo $?` immediately after step 4.
6. **Restore, and verify the restore:**
   ```
   cp /tmp/implement-story.md.uat-bak commands/implement-story.md
   git status --porcelain commands/implement-story.md
   rm /tmp/implement-story.md.uat-bak
   ```
7. Re-measure and confirm you are back where you started: repeat step 4.

**Expected Result:**
- Step 3: one warning line, verbatim —
  *"commands/implement-story.md has hoisted story-context-assembly — the inline Read sits above the first step, so it is issued on every invocation. That is eager loading in conditional syntax: the ceiling reads the same, every gate passes, and the saving is gone. Move the Read down to the narrowest step that needs it."*
- Step 4: `24884 49844 91950 ['story-context-assembly']`. Note that `conditional_bytes` is **unchanged at 42,106** and `ceiling_bytes` moves only by the 47 bytes of the inserted line — which is exactly the warning's point. **A hoisted read is invisible in the ceiling.** Only `hoisted_skills` catches it.
- Step 5: **0**. This is advisory, never a hard failure.
- Step 6: `git status --porcelain` prints **nothing**.
- Step 7: `24837 49797 91903 []`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `scripts/measure-invocation.py:141,178–187,297–301`

**Notes:**
**The boundary is `## Command Process` (line 71), not `### Step 1` (line 73).** `FIRST_STEP` matches `Command Process|Phase N|Step N|Gate N` at heading levels 2–4 and takes the **first** match. Inserting the same read at line 73 — between `## Command Process` and `### Step 1` — yields `hoisted_skills: []` and **no warning**. Verified. There is a two-line gap in which a read is eager in practice and invisible to the instrument. That is narrow enough to be harmless here and worth knowing before someone reports "the tripwire is broken."

**Fixture-root alternative (mutates nothing tracked).** The instrument only needs `system-instructions.md`, `commands/_preamble.md`, the command file, and `skills/`:
```
R=/tmp/uat-root; rm -rf $R; mkdir -p $R/commands
cp system-instructions.md $R/
cp commands/_preamble.md commands/implement-story.md $R/commands/
ln -s "$PWD/skills" $R/skills
python3 scripts/measure-invocation.py --root $R --command implement-story --format table
```
This reproduces `49,797 / 42,106 / 91,903 / 50.1% / 340` exactly. Do steps 2–4 against `$R/commands/implement-story.md` and delete `$R` when done.

---

## C. No Behavioral Drift

> This is the group that matters most. The spec's claim is not "the file got smaller" but "the file got smaller **and every rule survived**." The evidence is `no-drift-inventory.md` — 281 rules extracted from the pre-spec file *before any edit*, then walked one by one. **Do not re-walk 281 rows.** Scenario 5 checks the walk's own bookkeeping, Scenario 6 spot-checks the machine-verified subset, Scenario 7 audits the only three deletions, and Scenario 8 checks the one shortcut that was available and refused.

### Scenario 5: The inventory accounts for all 281 rules and was built from the file, not from the plan

**Source:** Business Rule 2; Story 6 AC; `no-drift-inventory.md` § AA. Walk record.

**Preconditions:**
- None. This is a reading and counting exercise, about ten minutes.

**Steps:**
1. Count the rows the inventory actually contains:
   ```
   grep -cE '^\| [0-9]+ \|' .writ/specs/2026-08-12-disclosure-implement-story/no-drift-inventory.md
   ```
2. Read the header block at the top of the file — the four `>` lines.
3. Read § **AA. Walk record** → **Disposition summary** and add the four numbers.
4. Read § **AA** → **Method**, the first paragraph.
5. Confirm the base SHA the inventory names is the one the file was captured from: `git show 9e76d1e:commands/implement-story.md | wc -c`

**Expected Result:**
- Step 1: **281**.
- Step 2: the inventory was captured in **Story 1, before any edit**, from `git show 9e76d1e:commands/implement-story.md`, and states its pass condition as **zero unaccounted rows**. It also says it was built **from the file, not from the technical spec's section ledger** — the ledger is a byte accounting of 36 sections; this is a rule accounting of 281 rules.
- Step 3: **119** command-only + **142** exactly-one-skill + **17** both + **3** contracted = **281**. Unaccounted: **0**.
- Step 4: the walk was done **from the inventory, not from the diff** — stated reason: *"a diff shows what moved and is blind to what was dropped, which is the failure mode Business Rule 2 exists to catch."* Take this seriously; it is the difference between a real check and a plausible one.
- Step 5: **52,709** — the same figure Scenario 1 step 4 produced. The inventory and the measurement are talking about the same file.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 1 and 6 — `no-drift-inventory.md`; commits `7704180`, `1457f51`

**Notes:**
The walk record reports **75 exact strings** machine-grepped across the command plus all 14 `SKILL.md` files, all 75 present, with four initial misses resolved as line-wrap artifacts. The 75 strings are described but **not enumerated as a list you can pipe into a script** — they are embedded in the 281 rows. Scenario 6 spot-checks a sample instead; there is no way to re-run the full 75 mechanically from what is written down.

---

### Scenario 6: Spot-check twelve of the seventy-five machine-verified literals

**Source:** `no-drift-inventory.md` § AA → *Method*: *"75 exact strings … were grepped across `commands/implement-story.md` plus all 14 `skills/*/SKILL.md`. All 75 present."* This scenario re-runs twelve of them, chosen to hit six different skills, the command, both categories that drift most easily (user-visible log strings and numeric thresholds), and the one string the walk deliberately unwrapped.

**Preconditions:**
- Run from the repository root. `bash` or `zsh`.

**Steps:**
1. Run the sample:
   ```
   for s in \
     'story-context.py not found' \
     'Knowledge entry skipped: malformed frontmatter' \
     'missing "## For {Role} Agents" section' \
     'knowledge_context truncated to 2KB' \
     'not yet complete' \
     '[None created]' \
     '> **Reverted:**' \
     'arch-check: do not modify' \
     '## Check 5 — File overlap' \
     '--budget-bytes 21000' \
     'STATUS: BLOCKED' \
     'PARTIAL_STATE' ; do
     printf '%-48s ' "$s"
     grep -rlF -- "$s" commands/implement-story.md skills/*/SKILL.md 2>/dev/null | tr '\n' ' '
     echo
   done
   ```
2. Confirm every line names at least one file. A blank right-hand side is a **Fail**.
3. Check the unwrapping claim specifically — the spec-lite log line must be on **one** line in the skill, not reflowed:
   ```
   grep -n 'missing "## For {Role} Agents" section' skills/story-context-assembly/SKILL.md
   ```
4. Check two numeric thresholds survived with their numbers intact:
   ```
   grep -n '+3\|+2\|+1' skills/story-context-assembly/SKILL.md | head -5
   grep -n '80 percent\|100 percent' commands/implement-story.md
   ```

**Expected Result:**
- Step 1, expected carriers:

  | String | Expected carrier |
  |---|---|
  | `story-context.py not found` | `story-context-assembly` |
  | `Knowledge entry skipped: malformed frontmatter` | `story-context-assembly` |
  | `missing "## For {Role} Agents" section` | `story-context-assembly` |
  | `knowledge_context truncated to 2KB` | `story-context-assembly` |
  | `not yet complete` | command **and** `dependency-context-loading` |
  | `[None created]` | `what-was-built-authoring` |
  | `> **Reverted:**` | command, `dependency-context-loading`, `what-was-built-authoring` |
  | `arch-check: do not modify` | `boundary-map-computation` |
  | `## Check 5 — File overlap` | `boundary-map-computation` |
  | `--budget-bytes 21000` | command **and** `story-context-assembly` |
  | `STATUS: BLOCKED` | command |
  | `PARTIAL_STATE` | command |

- Step 3: a single hit, the whole log string on one source line. The walk unwrapped it on purpose — *"a user-visible log string broken across source lines is a string a future author can silently reflow."*
- Step 4: the knowledge scoring weights **+3 / +2 / +1 / +1** are in the skill; the exit thresholds **100 percent** pass rate and **80 percent** line coverage are in the command frontmatter, not moved into a skill.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — `commands/implement-story.md`, `skills/story-context-assembly/SKILL.md`, `skills/boundary-map-computation/SKILL.md`, `skills/dependency-context-loading/SKILL.md`, `skills/what-was-built-authoring/SKILL.md`

**Notes:**
Twelve of seventy-five is a sample, not a proof. It fails fast if a whole category was dropped; it will not catch a single reworded clause in a row nobody sampled. If you want more confidence, the `Rewording ledger` at the end of the inventory names every row whose wording changed materially — about 25 rows — and each names the thing that makes the rule the same. Reading that table is a better use of twenty minutes than sampling more strings.

---

### Scenario 7: Exactly three rules were deleted, and each names a live carrier

**Source:** `no-drift-inventory.md` § AA → *The three contracted rows*. Business Rule 2 permits deleting a **second copy** of something specified elsewhere; it forbids deleting a rule.

**Preconditions:**
- None.

**Steps:**
1. Read the three-row table in § AA → *The three contracted rows, each with its citation*.
2. Verify row 99's carrier exists: `grep -n '^### 6. Aggregate' skills/dependency-context-loading/SKILL.md`
3. Verify row 198's carrier exists and is cited from both sides:
   ```
   ls .writ/docs/drift-report-format.md
   grep -rn 'drift-report-format' commands/implement-story.md skills/drift-triage/SKILL.md
   ```
4. Verify row 213's carrier exists: `grep -n '^### 1. Extract\|^### 2. Format' skills/what-was-built-authoring/SKILL.md`
5. Confirm the deleted material is genuinely gone from the command and not silently re-added:
   ```
   grep -c 'what_was_built_data' commands/implement-story.md
   grep -c 'DEV-003' commands/implement-story.md
   ```

**Expected Result:**
- Step 1: three rows — **99** (the 41-line "Example Coding Agent Context (with WWB)" worked example), **198** (the ten-line `#### [DEV-003]` drift-log entry example), **213** (the `what_was_built_data` object literal). Each row states what was deleted and what carries the information now.
- Step 2: `### 6. Aggregate` at line **105**. The format the example illustrated is specified once, there.
- Step 3: the file exists; the command cites it at line **203** and `drift-triage` at line **17**, both as the *format authority*. The command's citation predates the deletion — the example was always redundant with a document it already pointed at.
- Step 4: both headings present — `### 1. Extract — five sources, three failure semantics` and `### 2. Format`. One field list, one syntax.
- Step 5: `what_was_built_data` still appears **3** times in the command as the *variable* threaded through Gate 3.5 → Gate 4 → Step 4; the JavaScript object *literal* is gone. `DEV-003` appears **0** times.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — `no-drift-inventory.md` § AA; `skills/dependency-context-loading/SKILL.md:105`; `skills/what-was-built-authoring/SKILL.md:36,71`

**Notes:**

---

### Scenario 8: The available shortcut was refused, and the cost was recorded instead

**Source:** `no-drift-inventory.md` § *Rows deliberately kept in the command against byte pressure*; `load-report.md` § *What was not done to close the gap*.

**Preconditions:**
- None.

**Steps:**
1. Read the closing section of `no-drift-inventory.md`.
2. Confirm the five gate lists are still in the command, not replaced by a pointer at `agents/*.md`:
   ```
   grep -n '#### Gate 0:\|#### Gate 3:\|#### Gate 4:\|#### Gate 4.5:\|#### Gate 5:' commands/implement-story.md
   ```
3. Read lines 126–138 (Gate 0) and 189–200 (Gate 3) and check that the dimension and process lists are enumerated inline.
4. Confirm the same lists also exist in the agent files, i.e. the shortcut was genuinely available:
   ```
   wc -c agents/architecture-check-agent.md agents/review-agent.md agents/documentation-agent.md
   ```
5. Find where the refused saving is recorded: `grep -n '1,500 bytes\|roughly 1,500' .writ/specs/2026-08-12-disclosure-implement-story/*.md`

**Expected Result:**
- Step 1: rows **119, 176, 217, 227, 236** were kept in the command against byte pressure. Pointing them at `agents/*.md` would have saved roughly **1,500 bytes** and closed part of the ceiling regression. Stated reason for refusing: *"an agent definition is neither `commands/implement-story.md` nor one of the eight `SKILL.md` files, so each of those rows would have become **unaccounted** in this walk."*
- Step 2: all five gate headings present, at lines **126, 189, 221, 237, 252**.
- Step 3: the dimensions and process steps are inline semicolon lists — condensed from bullet lists, but every item present and in order.
- Step 4: `8,713 + 18,864 + 7,796 = 35,373` bytes of agent definitions carrying overlapping material. The shortcut was real.
- Step 5: the refusal and its byte cost appear in both `no-drift-inventory.md` and `load-report.md`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — `no-drift-inventory.md`, `load-report.md`

**Notes:**
This is the scenario that tells you whether the no-drift claim is load-bearing or decorative. The spec was 8,133 bytes over its ceiling and 1,500 bytes of relief was one edit away. It did not take it, and it wrote down why. Treat a future spec that closes a byte gap by pointing rules at `agents/*.md` as having weakened this guarantee — not because the information is lost, but because the walk that proves it isn't stops being possible.

---

## D. Pinned Literals

### Scenario 9: The eleven pinned `eval.sh` literals stayed in the command file

**Source:** `sub-specs/technical-spec.md` § *Pinned Literals*. `scripts/eval.sh` asserts these against **this file specifically** — moving one into a skill turns a passing check into a finding, and Business Rule 7 forbids editing `eval.sh` to compensate.

**Preconditions:**
- None.

**Steps:**
1. Run the sample:
   ```
   for l in 'scripts/story-context.py assemble' '| Architecture Check (Gate 0) |' \
            '| Coding Agent (Gate 1) |' '| Review Agent (Gate 3) |' \
            '| Testing Agent (Gate 4) |' '| Documentation Agent (Gate 5) |' \
            '## Artifact Map' '**Integrity:**' '## Required Artifacts' \
            '> **Commit:**' 'Skip reverted records' ; do
     printf '%-40s %s\n' "$l" "$(grep -cF -- "$l" commands/implement-story.md)"
   done
   ```
2. Confirm the five routing-table rows are still one contiguous block: `sed -n '206,213p' commands/implement-story.md`
3. Run the full eval suite: `bash scripts/eval.sh` (this takes several minutes — it builds sandbox git repos).
4. Read the summary of the report path it prints at the end.

**Expected Result:**
- Step 1: every literal returns **1** except `> **Commit:**`, which returns **2** (frontmatter `exit_criteria` plus Step 4). Zero anywhere is a Fail.
- Step 2: the five `| <Agent> (Gate N) |` rows appear as consecutive rows of one markdown table. They were kept as a block deliberately — five separate assertions against five scattered lines would be five separate ways to break.
- Step 3/4: **`Findings: 0`, `Run errors: 0`.**

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — `commands/implement-story.md`; `scripts/eval.sh`

**Notes:**

---

### Scenario 10: The twelfth pinned constraint — the one the spec's table missed

**Source:** `load-report.md` § *A twelfth pinned constraint the spec's table did not list*. This one was found **by failing**, not by planning.

**Preconditions:**
- `python3` available.

**Steps:**
1. Read the asserter: `sed -n '92,101p' scripts/eval-artifact-integrity.py`
2. Confirm **both** halves are present in the command:
   ```
   grep -n '\*\*Integrity:\*\*' commands/implement-story.md
   grep -n 'missing required' commands/implement-story.md
   ```
3. Run the asserter: `python3 scripts/eval-artifact-integrity.py | grep integrity-line`
4. Confirm the `**Integrity:**` line's two states also live in the skill that owns the schema:
   ```
   grep -n 'Integrity' skills/project-context-snapshot/SKILL.md
   ```
5. Read the corresponding row in the inventory's rewording ledger — row **112**.

**Expected Result:**
- Step 1: `eval-artifact-integrity.py:96` emits `context-schema-integrity-line` on `has_all(story, "**Integrity:**") and has_any(story, "missing required")` — an **AND** over two independent substrings, in a **third** script that the spec's eleven-row table (which covered `eval.sh` only) did not survey.
- Step 2: one hit each, both in the Step 4 snapshot sentence.
- Step 3: `PASS	context-schema-integrity-line`.
- Step 4: the Integrity line's two states appear in `project-context-snapshot` as well — the row is deliberately in both places, because the schema belongs to the skill and the assertion is against the command.
- Step 5: row 112 records exactly this: *"Required by `scripts/eval-artifact-integrity.py:96` … a twelfth pinned constraint the technical spec's Pinned Literals table did not list."*

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — `commands/implement-story.md`; `scripts/eval-artifact-integrity.py:96`

**Notes:**
The load report draws the correct lesson and it is the one to carry forward: **grep `scripts/` for `read("commands/<your file>.md")` rather than trusting a hand-built literal table.** `eval.sh` is not the only asserter, and the spec's table was built by surveying only `eval.sh`. Retaining `**Integrity:**` alone satisfied every literal in that table and still produced `FAIL (1 finding)`.

---

### Scenario 11: The two pinned regexes stayed in the body, and the loop check still PASSes rather than SKIPs

**Source:** `sub-specs/technical-spec.md` § *Pinned Regexes*. A missed regex makes `eval-loop-bounds.py` emit **SKIP**, not FAIL — a determinism check that silently stops checking, which is the worse outcome.

**Preconditions:**
- `python3` available.

**Steps:**
1. Find the sentences the regexes read:
   ```
   grep -n 'Max 3 iterations across review' commands/implement-story.md
   grep -n '2 fix iterations max' commands/implement-story.md
   ```
2. Confirm they are in the **body**, below the frontmatter's closing `---`: `sed -n '1,26p' commands/implement-story.md | tail -3`
3. Run the checker: `python3 scripts/eval-loop-bounds.py | grep -E 'drift-review-cycle|drift-testing-cycle'`
4. Confirm no scenario in the run reports SKIP: `python3 scripts/eval-loop-bounds.py | grep -c SKIP`
5. Read the rewording-ledger note for row 18 in `no-drift-inventory.md`.

**Expected Result:**
- Step 1: hits at lines **199** and **231**. The numbers are **3** and **2** and they match the frontmatter's `review_cycle: max_iterations: 3` and nested `testing_cycle: max_iterations: 2`.
- Step 2: frontmatter closes before line 26; both sentences are far below it. `eval-loop-bounds.py` strips frontmatter before searching *"so a cross-read never matches the very declaration it is meant to be checking."*
- Step 3: **`PASS	drift-review-cycle`** and **`PASS	drift-testing-cycle`**.
- Step 4: **0**.
- Step 5: row 18 records that the Pipeline control-flow sentence was deliberately phrased *"max 3 iterations total across review"* — with **`total`** inserted — precisely so it does **not** match `eval-loop-bounds.py:485`'s `Max (\d+) iterations across review` regex ahead of the Gate 3 sentence that check is meant to read. That is a real trap avoided on purpose; confirm the word `total` is still there: `grep -n 'iterations total across review' commands/implement-story.md`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — `commands/implement-story.md:199,231`; `scripts/eval-loop-bounds.py:485,488`

**Notes:**

---

### Scenario 12: The two forbidden literals did not reappear — in the command or in any skill

**Source:** `sub-specs/technical-spec.md` § *Pinned Literals* → the two `forbid_literal` strings. `eval.sh` scopes them to the command file only, so reintroducing them inside a skill would **not** trip the check and would still be a defect.

**Preconditions:**
- None.

**Steps:**
1. Check the command, which `eval.sh` covers:
   ```
   grep -cF 'Store parsed hints in `context_hints` map' commands/implement-story.md
   grep -cF 'For bracketed references: search source file for matching rows/entries by name' commands/implement-story.md
   ```
2. Check every skill, which `eval.sh` does **not** cover:
   ```
   grep -rF 'Store parsed hints in' skills/ | wc -l
   grep -rF 'For bracketed references: search source file' skills/ | wc -l
   ```
3. Confirm the replacement is intact — the delegation rule that made those strings retired prose:
   ```
   grep -n 'sole implementation\|do not interpret' commands/implement-story.md
   grep -n 'sole\|restate' skills/story-context-assembly/SKILL.md
   ```

**Expected Result:**
- Step 1: **0** and **0**.
- Step 2: **0** and **0**. This is the check `eval.sh` cannot make for you.
- Step 3: both clauses survive, split across the two files. `commands/implement-story.md:96` — *"Delegate hint parsing and fetching to `scripts/story-context.py`, the sole implementation — do not interpret `## Context for Agents` here."* `skills/story-context-assembly/SKILL.md:36,38` — the script is the **sole** implementation and the caller must *"never restate its parsing algorithm in prose — a second prose copy is how the two diverged."* A skill restating the algorithm would recreate exactly the divergence the context-hints work eliminated, and `eval.sh` would not catch it.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — `commands/implement-story.md`; `skills/story-context-assembly/SKILL.md`

**Notes:**

---

## E. Skills Are Well-Formed

### Scenario 13: Eight new skills, all born `status: candidate`, all lint-clean, manifest in sync

**Source:** ADR-014 skill lifecycle — an extracted skill is a **candidate** until it earns promotion; Stories 2, 3, 4 AC.

**Preconditions:**
- `bash` and `python3` available.

**Steps:**
1. Confirm the eight exist with their statuses and sizes:
   ```
   for d in story-context-assembly dependency-context-loading boundary-map-computation \
            change-surface-classification drift-triage what-was-built-authoring \
            project-context-snapshot story-commit-provenance; do
     printf '%-32s %-22s %s\n' "$d" "$(grep -m1 '^status:' skills/$d/SKILL.md)" "$(wc -c < skills/$d/SKILL.md)"
   done
   ```
2. Confirm they are new in this spec: `git ls-tree --name-only 9e76d1e skills/` and `git log --oneline 9e76d1e..1dfe92b -- skills/`
3. Lint every skill in the repo: `bash scripts/lint-skill.sh skills/*/SKILL.md`
4. Check the generated manifest is not stale: `bash scripts/gen-skill.sh --check; echo "EXIT=$?"`
5. Count the total skill surface: `ls -d skills/*/ | wc -l`

**Expected Result:**
- Step 1: all eight report `status: candidate`. Sizes: `story-context-assembly` **7,453**, `boundary-map-computation` **6,518**, `what-was-built-authoring` **5,859**, `dependency-context-loading` **4,858**, `drift-triage` **3,162**, `project-context-snapshot` **3,150**, `change-surface-classification` **2,761**, `story-commit-provenance` **2,244**. Total **36,005**.
- Step 2: `9e76d1e` holds **six** skills — `code-explanation`, `conventional-commits`, `error-rescue-mapping`, `gbrain-interop`, `safe-refactor-loop`, `tdd-cycle`. None of the eight exists there; they arrive across commits `7d2c927`, `0b66432`, `ba23c8b`.
- Step 3: **all 14 clean** (the eight new plus `code-explanation`, `conventional-commits`, `error-rescue-mapping`, `gbrain-interop`, `safe-refactor-loop`, `tdd-cycle`), exit **0**.
- Step 4: `EXIT=0`, no delta. `.writ/manifest.yaml`'s `skills:` block holds 14 alphabetical entries.
- Step 5: **14**. Note that `eval-leanness.py:71` sets `MAX_SKILLS = 12`; 14 exceeds it. `check_ceilings` emits a **warning**, never a finding, so nothing breaks — but the warning is real and raising the cap is a handoff to `2026-08-12-governor-enforcement`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 2–4 — `skills/*/SKILL.md`; commits `7d2c927`, `0b66432`, `ba23c8b`

**Notes:**
`candidate` is the honest status. Each of these has exactly one consumer and has never been exercised by a real run (Scenario 20). Promotion requires evidence none of them has yet.

---

### Scenario 14: No skill reads another skill

**Source:** `scripts/lint-skill.sh:52` — `Read skills/` is a **body-shape rejection** categorized *Skill chaining*, with the remediation *"Skills do not call other skills. Combine them into the consumer (agent/command) that uses both."* ADR-009 is the boundary this enforces.

**Preconditions:**
- None.

**Steps:**
1. Read the rule: `sed -n '48,56p' scripts/lint-skill.sh`
2. Search every skill body: `grep -RF 'Read skills/' skills/ | wc -l`
3. Search for the two adjacent prohibitions while you are there:
   ```
   grep -RF 'Read commands/' skills/ | wc -l
   grep -RnE '(^|[^A-Za-z_])Task\(' skills/ | wc -l
   ```
4. Confirm where the reads legitimately live instead: `grep -c 'Read skills/' commands/implement-story.md` and `grep -n 'Read skills/' agents/*.md`

**Expected Result:**
- Step 1: four `BODY_PATTERNS` rows — command invocation, **skill chaining**, subagent dispatch, slash command — each with a category and a remediation.
- Step 2: **0**. This is the check that keeps an extraction from turning into a hidden dependency graph, where a "conditional" read of one 3 KB skill silently pulls three more.
- Step 3: **0** and **0**.
- Step 4: **9** in the command. Separately, `agents/coding-agent.md:116,118` and `agents/testing-agent.md:99` carry inline reads of `tdd-cycle` and `conventional-commits` — those are **agent** files, which the linter's skill rules do not apply to and which `measure-invocation.py` does not measure at all. Remember that for Scenario 17.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 2–4 — `scripts/lint-skill.sh:52`; `skills/`

**Notes:**

---

## F. Graceful Degradation

### Scenario 15: An unreadable skill path warns and keeps going — it never hard-fails

**Source:** Verification 8; `load-report.md` § *Graceful-degradation probe*. `system-instructions.md` → *Schema* and `eval-leanness.py:1239` specify warn-never-fail for the declarative form; the inline form must degrade in the same spirit.

> **This scenario modifies a tracked file.** Follow the backup and restore steps exactly. The fixture-root alternative in Scenario 4's Notes works here too and touches nothing tracked.

**Preconditions:**
- `git status --porcelain commands/implement-story.md` prints **nothing**.

**Steps:**
1. Back up:
   ```
   cp commands/implement-story.md /tmp/implement-story.md.uat-bak
   ```
2. Insert a read of a skill that does not exist, at a **real step** — immediately above Step 4's item 7:
   ```
   awk 'NR==282{print "`Read skills/does-not-exist/SKILL.md`"; print ""}{print}' \
     /tmp/implement-story.md.uat-bak > commands/implement-story.md
   ```
3. Run in table form and check the exit code:
   ```
   python3 scripts/measure-invocation.py --root . --command implement-story --format table | grep WARNING
   echo "EXIT=${PIPESTATUS[0]}"
   ```
4. Read the structured fields:
   ```
   python3 scripts/measure-invocation.py --root . --command implement-story \
     | python3 -c 'import json,sys; d=json.load(sys.stdin); c=d["commands"]["implement-story"]; print(c["ceiling_bytes"], c["unresolved_skills"], len(c["conditional_skills"])); print(d["warnings"])'
   ```
5. **Restore, and verify:**
   ```
   cp /tmp/implement-story.md.uat-bak commands/implement-story.md
   git status --porcelain commands/implement-story.md
   rm /tmp/implement-story.md.uat-bak
   ```
6. Re-measure: `python3 scripts/measure-invocation.py --root . --command implement-story | python3 -c 'import json,sys; c=json.load(sys.stdin)["commands"]["implement-story"]; print(c["command_bytes"], c["unresolved_skills"])'`

**Expected Result:**
- Step 3: one warning, verbatim — *"commands/implement-story.md references skills that resolve to no file: does-not-exist. Their load is unmeasurable, so the figures below are a lower bound."* — and **`EXIT=0`**. Never a hard failure.
- Step 4: `ceiling_bytes` **91,942** (91,903 plus the 39 bytes of the inserted line — the unresolved name contributes **nothing** to the figure), `unresolved_skills` **`['does-not-exist']`**, `conditional_skills` still **9** resolvable names. The same warning string appears in the JSON `warnings` array.
- Step 5: `git status --porcelain` prints **nothing**.
- Step 6: `24837 []`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — `scripts/measure-invocation.py:249,284`, `:402–403`

**Notes:**
**Discrepancy.** `load-report.md` states the warning is *"printed to stderr in `--format table`"*. **It is not.** `render_table` appends `WARNING:` lines to the string that `main()` prints to **stdout** (`measure-invocation.py:402–403`, `:424`). Verified: `--format table 2>/dev/null` still shows the warning, and `--format table >/dev/null` hides it. This matters for anyone wiring the instrument into CI on the assumption that stdout is the report and stderr is the alarm — **the warning is inside the report**. The behavior is correct; the load report's description of it is wrong.

**This scenario tests the instrument, not the harness.** It establishes that `measure-invocation.py` degrades gracefully. Whether a real agent harness degrades gracefully on a failed `Read` is **unknown** and is part of Scenario 20. If a harness is found to hard-fail on an unreadable skill path, that is a finding for ADR-021's 2026-11-11 review trigger, not something to work around.

---

## G. Honesty — The Negative Result

> The six scenarios below are not confirmations. They exist because this spec's headline measure came back negative and the artifacts have to make that unmissable. If a reader can work through the previous fifteen scenarios and come away thinking progressive disclosure was validated here, this group has failed.

### Scenario 16: The full-path ceiling regressed by 9.7% — more than twice the projection

**Source:** `load-report.md` § *The verdict, in two sentences* and § *Did the full-path ceiling regress?*; ADR-021 amendment 2 → *Tracked exemption*; `spec.md:283`.

**Preconditions:**
- `python3` available.

**Steps:**
1. Get the measured ceiling:
   ```
   python3 scripts/measure-invocation.py --root . --command implement-story \
     | python3 -c 'import json,sys; print(json.load(sys.stdin)["commands"]["implement-story"]["ceiling_bytes"])'
   ```
2. Read the projection the spec made **before** implementing: `sed -n '283p' .writ/specs/2026-08-12-disclosure-implement-story/spec.md`
3. Compute the miss: measured − projected, and measured − baseline.
4. Read ADR-021's amendment 2 → the paragraph beginning **"Tracked exemption"**: `grep -n 'Tracked exemption' .writ/decision-records/adr-021-progressive-disclosure-token-budget.md`
5. Confirm the baseline being compared against is the corrected one:
   ```
   grep -n '77,669' .writ/specs/2026-08-12-disclosure-implement-story/load-report.md | head -3
   ```

**Expected Result:**
- Step 1: **91,903**.
- Step 2: the spec projected **~87,231 — +3,461 bytes, +4.1%** — and said in the same breath *"The full-path ceiling is still projected to regress, and that is the spec's real risk."* The risk was named up front. It then came in worse than named.
- Step 3: measured **+8,133 / +9.7%** against the 83,770 baseline; **+4,672 bytes over the projection**, or **2.35× the projected overage**. Component misses: `command_bytes` 24,837 against ~20,970 (**+3,867**), eight skills 36,005 against ~34,200 + ~1,000 connective (**+805**).
- Step 4: the ADR carries this as a **tracked exemption**, with the measured figures and the reason, attached to its **2026-11-11 review trigger**. It is recorded in the decision record, not only in the spec folder.
- Step 5: the baseline is **83,770**, not 77,669. The 77,669 figure was produced by an instrument blind to inline reads (pre-`e8f2a09`) and is the **floor** baseline only. Quoting it as the ceiling baseline would turn a +9.7% regression into an apparent +18% one, or — flipped — would let the −35.9% floor improvement be presented as a like-for-like ceiling win. **The two numbers describe different runs and neither offsets the other.**

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — `load-report.md`; `.writ/decision-records/adr-021-progressive-disclosure-token-budget.md` § Amendments

**Notes:**
Both results are true at once and both must be reported together: **the floor fell 35.9% on every single run; the all-gates path costs 9.7% more than the monolith did.** A command whose gates nearly always all fire realizes the ceiling and never the floor — which makes `implement-story`, the command chosen as the pilot precisely because it was the biggest, close to the worst possible extraction candidate.

---

### Scenario 17: `--quick` saved 1.8%, not 5.9% — and five skipped gates are not five saved skills

**Source:** `load-report.md` § *Report the `--quick` saving honestly*; `spec.md:285`, which projected the number and pre-emptively warned against exactly the misreading this scenario tests for.

**Preconditions:**
- None. This is arithmetic plus two greps.

**Steps:**
1. Read what `--quick` skips: `sed -n '316,320p' commands/implement-story.md`
2. For each skipped gate, find whether that gate carries an inline skill read:
   ```
   sed -n '126p;139p;148p;189p;201p;211p;252p' commands/implement-story.md
   grep -n 'Read skills/' commands/implement-story.md
   ```
3. Derive the `--quick` ceiling by hand — the instrument does not model paths, so you must subtract:
   ```
   echo $(( 91903 - 6518 - 3162 ))
   ```
   (`boundary-map-computation` at Gate 0.5, `drift-triage` at Gate 3.5 — the only two skipped gates carrying a skill.)
4. Compare with the projection: `sed -n '285p' .writ/specs/2026-08-12-disclosure-implement-story/spec.md`
5. Measure what the three *other* skipped gates actually cost, in the files the instrument never opens:
   ```
   wc -c agents/architecture-check-agent.md agents/review-agent.md agents/documentation-agent.md
   ```
6. Check whether Gate 2.5 is in the skip list: `grep -n 'Gate 2.5' commands/implement-story.md | head -2`

**Expected Result:**
- Step 1: `--quick` skips **five** gates — 0 (arch-check), 0.5 (boundary map), 3 (review), 3.5 (drift handling), 5 (docs).
- Step 2: of those five, **only two carry an extracted skill** — Gate 0.5 → `boundary-map-computation` (line 148), Gate 3.5 → `drift-triage` (line 211). Gates 0, 3 and 5 are **agent spawns**; their procedure lives in `agents/architecture-check-agent.md`, `agents/review-agent.md`, `agents/documentation-agent.md`.
- Step 3: **82,223**, against the **83,770** such a run pays today — **−1,547 / −1.8%**.
- Step 4: the spec projected **~78,861 / −5.9%**. The measured saving is **less than a third of the projection**. The spec's own sentence — *"Do not report 'five gates skipped' as though five skills were saved"* — was written before the measurement and is still the right instruction after it.
- Step 5: **35,373 bytes** of agent definitions sit behind the three skill-free skipped gates. That load is real, it is skipped on `--quick`, and **`measure-invocation.py` counts none of it** — the instrument measures commands and their inline reads only. So the true `--quick` saving is larger than 1,547 bytes; it is simply not a saving this spec produced or can claim. This spec did not touch `agents/*.md`.
- Step 6: **Gate 2.5 is not in the skip list.** `change-surface-classification` (2,761 B) is paid on every run, including `--quick`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — `load-report.md`; `commands/implement-story.md:148,211,316–318`; `agents/*.md`

**Notes:**
Two derived paths are worth recording because they are the mechanism's best case, and both are real: **`--quick` on a dependency-free story = 77,365 (−7.6%)**, because `dependency-context-loading`'s read (4,858 B) sits inside the has-dependencies branch; and **`--review-only` = 79,284 (−5.4%)**, which skips `boundary-map-computation` and `tdd-cycle`. Derive each by subtraction from 91,903 as in step 3. The largest single conditional win in the whole file is **mode-independent** — it is the dependency branch, not `--quick`.

---

### Scenario 18: The cause is per-file scaffolding — measure it yourself

**Source:** `load-report.md` § *Per-skill sizes and the measured scaffolding cost*; ADR-021 amendment 2 → *the residual is per-skill scaffolding*.

**Preconditions:**
- None.

**Steps:**
1. Compute the pure overhead:
   ```
   echo "removed:  27872"
   echo "added:    $(cat skills/story-context-assembly/SKILL.md skills/dependency-context-loading/SKILL.md skills/boundary-map-computation/SKILL.md skills/change-surface-classification/SKILL.md skills/drift-triage/SKILL.md skills/what-was-built-authoring/SKILL.md skills/project-context-snapshot/SKILL.md skills/story-commit-provenance/SKILL.md | wc -c)"
   echo "overhead: $(( 36005 - 27872 ))  over 8 files"
   ```
2. Divide: `python3 -c 'print(8133/8)'`
3. Compare against what the spec projected per file: `sed -n '107p' .writ/specs/2026-08-12-disclosure-implement-story/spec.md`
4. Look at the extreme case — measure the scaffolding fraction of the smallest skill:
   ```
   wc -c skills/change-surface-classification/SKILL.md
   sed -n '1,20p' skills/change-surface-classification/SKILL.md
   ```
5. Read the operational conclusion in `load-report.md` § *The operational conclusion*.

**Expected Result:**
- Step 1: **27,872** bytes left the command; **36,005** bytes arrived as eight files; **8,133 bytes of pure overhead** — which is, to within 0.1%, the entire ceiling regression from Scenario 16. The regression is not a rule that got fatter. It is eight sets of frontmatter, titles, `## Purpose`, `## When to Use` and `## How to Apply`.
- Step 2: **1,016.6 bytes per skill.**
- Step 3: the spec projected *"roughly 650 bytes per file … about 5,200 bytes of pure overhead."* Measured per-file overhead is **1.56× the projection**; the resulting ceiling overage is **2.35× the projection** (Scenario 16). Per-skill overhead was underestimated, and that single underestimate accounts for essentially the whole miss.
- Step 4: `change-surface-classification` is **2,761 bytes** built from a **1,896-byte** source block — roughly **34% scaffolding**. The smaller the extraction, the worse the ratio.
- Step 5: *"fewer, larger skills"* — the overhead is charged per **file**, not per byte, so a spec that splits one capability into three small skills pays it three times for the same content.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — `load-report.md`; `skills/*/SKILL.md`

**Notes:**
This spec created eight skills, three of them under 3.2 KB. Applying its own conclusion retroactively, `change-surface-classification`, `project-context-snapshot` and `story-commit-provenance` were probably the wrong granularity — together they cost roughly 3,000 bytes of scaffolding to carry 6,500 bytes of content. The spec did not go back and merge them, and it does not claim it should have; it records the number so the next extraction does not repeat it. There is no next extraction — see Scenario 19.

---

### Scenario 19: This spec's result is why the five sibling specs were closed unimplemented

**Source:** ADR-021 § Consequences — *"sequenced `implement-story` first since a failure there should stop the phase rather than surface after five easier wins"*; commit `5dbaf1a`.

**Preconditions:**
- None.

**Steps:**
1. List the six disclosure specs: `ls -d .writ/specs/2026-08-12-disclosure-*`
2. Read the status line of each sibling:
   ```
   for s in create-spec implement-phase release ship verify-spec; do
     printf '%-18s ' "$s"; sed -n '3p' .writ/specs/2026-08-12-disclosure-$s/spec.md
   done
   ```
3. Read the closure paragraph of any one of them: `sed -n '9,20p' .writ/specs/2026-08-12-disclosure-create-spec/spec.md`
4. Read the commit that closed them: `git show --stat 5dbaf1a | head -20`
5. Confirm this spec's own status is different: `sed -n '3p' .writ/specs/2026-08-12-disclosure-implement-story/user-stories/README.md`

**Expected Result:**
- Step 1: six — `create-spec`, `implement-phase`, `implement-story`, `release`, `ship`, `verify-spec`.
- Step 2: all five siblings read **`> **Status:** Closed — Not Implemented (measured evidence, 2026-08-12)`**.
- Step 3: the closure text names **the pilot** as the reason. Each of the five had named `2026-08-12-disclosure-implement-story` as its dependency and had been told to *"follow the extraction pattern established by the dependency spec, do not invent a second one."* The pattern they were to follow is the one that measured a 9.7% ceiling regression.
- Step 4: commit `5dbaf1a` — *"spec(phase-10b): close five disclosure specs on measured evidence, rescope enforcement."*
- Step 5: this spec reads **`Completed ✅ — 6/6 stories, 48/48 tasks.`** It shipped. Its five siblings did not, **because** it shipped and reported what it measured.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Commit `5dbaf1a`; `.writ/specs/2026-08-12-disclosure-*/spec.md`

**Notes:**
This is what a pilot is for and it is the only reason the negative result is not a loss. ADR-021 put the largest, hardest command first on the explicit theory that *"a failure there should stop the phase rather than surface after five easier wins."* The signal arrived on schedule, at extraction 1 of 6, and it stopped the phase. Five specs' worth of work was not done. **If any part of this UAT is worth carrying forward, it is that sequencing decision, not the extraction.**

---

### Scenario 20: Nobody has watched the reads fire — run `/implement-story` and find out (MANUAL, OPEN)

**Source:** `.writ/product/roadmap.md:335` — *"(manual) One real `/implement-story` run completes with progressive disclosure active and every gate firing"*; `load-report.md` § *Harness observation*, whose recorded answer is *"not determinable from this run."*

> **This is the single most valuable scenario in this plan and it has never been executed.** Everything in Scenarios 1–19 is structural: the reads point at real files, they sit below the first step, each appears exactly once, and the arithmetic is consistent. **None of that establishes that a harness actually defers the `Read` until execution reaches the line.** If loading is not lazy at runtime, the floor improvement in Scenario 2 is fictional and only the ceiling regression in Scenario 16 is real. This spec was implemented by an agent running `/implement-spec`; no `/implement-story` invocation of the rewritten command has occurred, so no transcript exists in which the nine reads either fired or did not.

**Preconditions:**
- A working AI coding harness with Writ installed and `/implement-story` available.
- A **small, real, low-risk story** in an active spec — one or two files, a clear acceptance criterion. Do not use a story you cannot afford to revert.
- A branch you are willing to throw away: `git switch -c uat/disclosure-harness-probe`
- A way to see the harness's tool calls: a transcript, a session log, or the tool-call panel in your client.

**Steps:**
1. Record the pre-state: `python3 scripts/measure-invocation.py --root . --command implement-story --format table`
2. Run the **full** path on your chosen story so every gate fires:
   ```
   /implement-story story-N
   ```
3. **While it runs, watch the tool-call stream** and record, for each of the nine skills, the answer to one question: *did a `Read` of `skills/<name>/SKILL.md` appear before the run reached that skill's step, at that step, or not at all?* Fill in this table:

   | Skill | Read at its step? | Read early? | Not read? |
   |---|---|---|---|
   | `story-context-assembly` (Step 2) | | | |
   | `dependency-context-loading` (Step 2, dependency branch) | | | |
   | `boundary-map-computation` (Gate 0.5) | | | |
   | `tdd-cycle` (Gate 1) | | | |
   | `change-surface-classification` (Gate 2.5) | | | |
   | `drift-triage` (Gate 3.5) | | | |
   | `project-context-snapshot` (Step 4 item 3) | | | |
   | `what-was-built-authoring` (Step 4 item 4) | | | |
   | `story-commit-provenance` (Step 4 item 7) | | | |

4. Note whether the story reached `Status: Completed` with a `> **Commit:**` SHA and a `## What Was Built` section, or was marked DEGRADED.
5. **Run it again with `--quick` on a second small story** — this is the run that matters most:
   ```
   /implement-story story-M --quick
   ```
   Record specifically whether `boundary-map-computation` and `drift-triage` were read. **Those two skills are the mechanism's entire claim.** If a `--quick` run reads them anyway, progressive disclosure delivers nothing on the skipped path and Scenario 17's −1.8% is zero.
6. If your story has no dependencies, record whether `dependency-context-loading` was read. It should not be.
7. Deliberately break one path: rename one skill directory (`mv skills/drift-triage /tmp/drift-triage`), run `/implement-story --quick` on a throwaway story, and record whether the harness **warns and continues** or **hard-fails**. Then restore: `mv /tmp/drift-triage skills/drift-triage` and confirm `git status --porcelain skills/` is empty.
8. Discard the branch: `git switch -` and `git branch -D uat/disclosure-harness-probe`.

**Expected Result:**
- Step 3: **each of the nine reads appears at or immediately before its own step, and nowhere earlier.** Any read that appears during Step 1, or as a batch at the start of the run, is **eager loading in practice regardless of what the file says** — and it means `hoisted_skills: []` in Scenario 3 measured the syntax rather than the behavior.
- Step 4: the story completes or is honestly marked DEGRADED. A DEGRADED outcome is a valid terminal state and is not a Fail of this scenario.
- Step 5: on `--quick`, **`boundary-map-computation` and `drift-triage` are never read.** This is the pass condition that the whole `--quick` saving rests on.
- Step 6: `dependency-context-loading` is not read for a dependency-free story.
- Step 7: the harness **warns and continues**. `system-instructions.md` → *Schema* and `eval-leanness.py:1239` specify warn-never-fail for the declarative form and the inline form is meant to degrade in the same spirit. Scenario 15 established that the *measuring instrument* does this; whether the *harness* does is unknown.

**Status:** [ ] Pass  [ ] Fail  **[ ] NOT YET RUN — this is the current state**

**Implementation Reference:** `.writ/product/roadmap.md:335`; `load-report.md` § Harness observation

**Notes:**
Record the outcome even if it is partial. *"Could not determine"* is the answer the load report already gives and it is the accurate one for zero runs; it stops being acceptable after one.

**If a harness pre-loads reads it has not reached, or hard-fails on an unreadable skill path, that is a finding for ADR-021's 2026-11-11 review trigger — not something to work around.** Either finding would change the reading of this entire UAT: a pre-loading harness makes the 35.9% floor improvement a paper result and leaves only the 9.7% ceiling regression standing, which would retroactively make the five sibling closures in Scenario 19 conservative rather than merely correct.

---

### Scenario 21: The mechanism change orphaned a convention, and nobody owns the correction

**Source:** `load-report.md` § *The ownerless correction*; ADR-021 amendment 2 → *A consequence with **no owner***; Story 6 AC.

**Preconditions:**
- None.

**Steps:**
1. Confirm the field has zero declarations and will keep having zero:
   ```
   grep -rc '^required_skills:' commands/*.md | grep -v ':0' | wc -l
   ```
2. Read the claim in the root behavioral contract: `sed -n '252p' system-instructions.md`
3. Read the second carrier: `sed -n '396p' adapters/claude-code.md`
4. Read the third: `sed -n '136p' .writ/docs/skills.md`
5. Check which of the three this spec touched at all:
   ```
   git diff --name-only 9e76d1e..1dfe92b | grep -E 'system-instructions|adapters/|docs/skills'
   git diff 9e76d1e..1dfe92b -- .writ/docs/skills.md | grep -c 'Status: adopted'
   ```
6. Read `load-report.md` § *The ownerless correction* in full.

**Expected Result:**
- Step 1: **0** command files declare `required_skills:`. `metrics.required_skills_declarations` reports **0** today and — now that the six disclosure specs use inline reads and five of them are closed — will report **0** permanently.
- Step 2: `system-instructions.md:252` states **`Status: adopted`** and names *"Phase 10 progressive disclosure (ADR-021)"* as the field's **first consumer**, which *"needs a declarative, harness-resolved, per-invocation load mechanism — the exact contract this convention already specifies."* It closes with *"Progressive disclosure's extraction work lands the first real declarations; no agent or command declares the field yet."* ADR-021 amendment 2 establishes that a static frontmatter array **cannot** be per-invocation. The stated justification is precisely the claim this pilot disproved, and the first half of the last sentence is now permanently false while the second half is permanently true.
- Step 3: `adapters/claude-code.md:396` carries the same claim.
- Step 4: `.writ/docs/skills.md:136` carries it a third time, in near-identical wording.
- Step 5: the first command prints **`.writ/docs/skills.md` only** — `system-instructions.md` and `adapters/claude-code.md` sit outside this spec's locked file set and were not edited at all. The second command prints **0**: `.writ/docs/skills.md` *is* inside the file set and was edited (new skill entries), but its `Status: adopted` paragraph was deliberately left untouched, on the reasoning that correcting one carrier of a three-carrier claim is worse than correcting none, and the adoption decision belongs to `system-instructions.md`.
- Step 6: the load report states plainly that this **needs a maintainer action this spec cannot take**, names `2026-08-12-governor-enforcement` as the nearest candidate owner while explaining why naming it would assign work outside that spec's own file set, and records the item as **unassigned**.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — `load-report.md`; `system-instructions.md`; `adapters/claude-code.md:396`; `.writ/docs/skills.md`

**Notes:**
Also unexercised as a result: `scripts/eval-leanness.py`'s `check_required_skills`. It reads **frontmatter only**, and no command declares anything, so it has nothing to resolve. Its pin to the `warnings` bucket (`eval-leanness.py:1239`), which exists so a later severity flip cannot make an unknown skill name blocking, is **untested in the product**. The load report reports it as **unexercised, not passed**, and no declaration was added to manufacture a pass. That distinction is the right one and it should survive any future cleanup of this item.

---

## Discrepancies Found While Writing This Plan

Each was verified by running the command, not by reading an assertion.

1. **The degradation warning goes to stdout, not stderr.** `load-report.md` § *Graceful-degradation probe* says the warning is *"printed to stderr in `--format table`"*. `measure-invocation.py:402–403` appends `WARNING:` lines to the table string, which `main()` prints to stdout at `:424`. Confirmed by redirection in both directions. Consequence: a CI wiring that watches stderr for alarms will never see it. Recorded in Scenario 15's Notes. **The behavior is fine; the documentation of it is wrong.**

2. **The hoist boundary is `## Command Process`, not `### Step 1`.** `FIRST_STEP` (`measure-invocation.py:141`) matches `Command Process|Phase N|Step N|Gate N` and takes the first hit — line **71**, two lines above `### Step 1` at line 73. `load-report.md` describes the check as *"none sits above `### Step 1`"*, which is true of the current file but understates the tripwire's actual span. An inline read inserted between lines 71 and 73 is eager in practice and reports `hoisted_skills: []`. Verified in both positions. Recorded in Scenario 4's Notes. Harmless today; worth knowing before someone reports the tripwire as broken.

3. **The load report's probe ceiling (91,964) is not reproducible as an absolute.** The figure depends on where in the file the probe line was inserted. Re-running the probe at Step 4 item 7 gives **91,942**. Scenario 15 therefore states the rule — the unresolved name contributes **zero** to `ceiling_bytes`, and the only delta is the inserted line's own bytes — rather than an absolute to match. Not a defect in either artifact.

4. **`spec.md`'s per-file overhead projection and its ceiling projection imply different miss factors**, and the difference is worth stating precisely rather than collapsing to one number. Per-file overhead: projected ~650 B, measured ~1,017 B — **1.56×**. Ceiling overage: projected +3,461 B, measured +8,133 B — **2.35×**. Both are in Scenarios 16 and 18 with their derivations. Anyone quoting a single "underestimated by N×" figure should say which of the two they mean.

5. **The 75 machine-verified literals are not enumerated as a re-runnable list.** They are described in the walk record and embedded across the 281 rows, so the full check cannot be mechanically repeated from what is written down. Scenario 6 samples twelve instead. This is a limitation of the evidence, not a failure of it — but a future no-drift walk should emit the literal list to a file.

## Sign-Off

| | |
|---|---|
| Scenarios passed | ___ of 21 |
| Scenarios failed | ___ |
| Scenario 20 status | ☐ Passed  ☐ Failed  ☐ **Not yet run** |
| Tester | |
| Date | |

**This UAT cannot be signed off as complete while Scenario 20 is unrun.** Twenty of the twenty-one scenarios verify that the artifacts say what they claim to say. Scenario 20 is the only one that verifies the mechanism works.

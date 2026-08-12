# UAT Plan: Retire Dead Prescription

> **Generated:** 2026-08-11
> **Spec:** `.writ/specs/2026-08-11-retire-dead-prescription/`
> **Stories Covered:** 6 of 6 completed
> **Total Scenarios:** 18

## How to Use This Plan

1. Work through scenarios in order (grouped by story).
2. Run the commands exactly as written, from the repository root, on a branch that contains this spec (`phase/10-component-contract` or later).
3. Mark Pass or Fail — add notes for anything that differs from the Expected Result.
4. A Fail is filed as an issue or fed back to the spec; it is not fixed inline.
5. The feature passes UAT when every scenario passes, or when a failure is explicitly accepted as a known limitation.

> **Note on this methodology repo:** the deliverables are markdown and shell. Every scenario below is a grep, a diff, a lint run, or a file read. **No scenario modifies a tracked file.** Scenarios 6, 8, 11 and 12 create throwaway fixtures under a scratch directory; each names the directory and the cleanup.
>
> **Use `grep -F` throughout.** Two of the retired literals — `Model tier (advisory only)` and `^(orchestration|capability|-[0-9]+)$` — contain regex metacharacters. Without `-F`, `grep` silently under-reports and a tester can conclude the surface is clean when it is not. The spec's own measurements were wrong once for exactly this reason.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|------------------|
| Story 1: Correct the false frontmatter claim | ✅ Covered | 4 | AC: 3, Recorded finding: 1 |
| Mirror parity (Stories 1–3, the spec's named silent failure) | ✅ Covered | 2 | Business Rule 2: 2 |
| Story 2: Deprecate the ordinal-offset reservation | ✅ Covered | 4 | AC: 3, Spec-vs-code discrepancy: 1 |
| Story 6: Retire the prose-note carrier in explainer + lint | ✅ Covered | 3 | AC: 3 |
| Story 4: Reconcile `.writ/manifest.yaml` | ✅ Covered | 1 | AC: 1 |
| Story 5: Formally deprecate `decisions.md` | ✅ Covered | 2 | AC: 2 |
| Story 3: Resolve `required_skills:` by adoption | ✅ Covered | 2 | AC: 1, Honesty check: 1 |

---

## Story 1: Correct the False Frontmatter Claim

### Scenario 1: The replacement number is reproducible

**Source:** Business Rule 1; Story 1 Task 1.1. The spec's own premise is that a false number may not be replaced by an unverified one. This scenario re-derives the number the root contract now states.

**Preconditions:**
- Clean checkout at the repository root.

**Steps:**
1. Run `ls commands/*.md | wc -l`.
2. Run `for f in commands/*.md; do head -1 "$f"; done | grep -c '^---$'`.
3. Open `system-instructions.md` and read the Commands bullet under § Model Tiers → **Carrier per file type** (line 275).

**Expected Result:**
- Step 1 prints **32**. Step 2 prints **32** — every file in `commands/` opens with `---`.
- Step 3 reads: commands carry `model_tier` in the same `---` YAML frontmatter that already holds `name:` and `description:`, "present in 32/32 files under `commands/` (31 commands plus `_preamble.md`). Advisory only."
- The bullet states 32/32 files, not 32 commands. `commands/_preamble.md` is the 32nd file and is deliberately absent from `.writ/manifest.yaml` (see Scenario 13).
- The Skills and Agents bullets directly above it are unchanged and still describe their own carriers.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `system-instructions.md:271-275`

**Notes:**

---

### Scenario 2: The false claim is gone from the active surface

**Source:** Story 1 AC 2; Story 6 AC 2; spec-lite AC 1

**Preconditions:**
- None. Read-only.

**Steps:**
1. Run:
   ```
   grep -rn -F -e "verified 0/31 files" -e "no frontmatter mechanism" \
     system-instructions.md cursor/ commands/ agents/ adapters/ scripts/ .writ/docs/ .writ/manifest.yaml
   echo "EXIT=$?"
   ```
2. Run the same grep with `-e "carry no frontmatter mechanism"` added.

**Expected Result:**
- No output. `EXIT=1` — grep's "no matches" exit code, which is the pass condition here.
- Both steps behave identically.
- This covers all six downstream artifacts the spec named: `system-instructions.md`, `cursor/writ.mdc`, `commands/new-command.md`, `.writ/docs/model-tiers.md`, `scripts/lint-skill.sh`, and the adapters.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 1 and 6

**Notes:**

---

### Scenario 3: History is intact, and the one active-surface file where the claim survives

**Source:** Business Rules 3 and 8; Story 1 AC 3. Two halves: history must be *unchanged*, and the ownership boundary must have been *held* rather than helpfully crossed.

**Preconditions:**
- Full git history available.

**Steps:**
1. Run:
   ```
   grep -rn -F "verified 0/31 files" .writ/decision-records/ .writ/specs/archive/ CHANGELOG.md | cut -d: -f1 | sort | uniq -c
   grep -rn -F "no frontmatter mechanism" .writ/decision-records/ .writ/specs/archive/ CHANGELOG.md | wc -l
   ```
2. Read `CHANGELOG.md:143` and `.writ/decision-records/adr-016-model-tier-delegation.md:76`.
3. Run `git diff --stat fe2af84 e23fbdc -- CHANGELOG.md .writ/decision-records/ .writ/specs/archive/ .writ/research/` (`fe2af84` is the last commit before this spec's first story; `e23fbdc` is this spec's merge commit).

   > **Corrected 2026-08-11 (UAT execution).** This step originally ended at `HEAD`. That was correct when written and wrong the moment a sibling lane merged: `HEAD` now includes four other Phase 10 specs, and `3ac178a` (component-contract) legitimately edits `adr-020-component-contract.md`, so the step reported `1 file changed, 18 insertions(+), 6 deletions(-)` and read as a failure. The property being asserted — *this spec* rewrote no history — holds exactly; the command had stopped measuring it. Pinning the endpoint to this spec's own merge restores the assertion.
4. Now run `grep -n -F "verified 0/31 files" .writ/product/roadmap.md`.

**Expected Result:**
- Step 1: `verified 0/31 files` → **4 hits** — 2 in `adr-020-component-contract.md`, 1 each in `.writ/specs/archive/2026-07-10-model-tier-delegation/user-stories/story-1-tier-contract-adr.md` and `story-4-authoring-lint-docs.md`. `no frontmatter mechanism` → **13 hits**, 12 in the archived `2026-07-10-model-tier-delegation` spec and 1 in `CHANGELOG.md`.
- Step 2: both lines still carry the old wording. `CHANGELOG.md:143` says `/new-command` documents a prose note "(commands have no frontmatter mechanism)"; ADR-016 line 76 says commands "have no frontmatter or config-block mechanism at all (verified 0/31 command files)". Both were accurate on 2026-07-10 and are correctly left alone. ADR-016 uses the *variant* literal `verified 0/31 command files`, which is why it does not appear in step 1's first count.
- Step 3: **empty output** — this spec changed no byte of `CHANGELOG.md`, `.writ/decision-records/`, `.writ/specs/archive/`, or `.writ/research/`.
- Step 4: **zero hits.** *(Updated 2026-08-11 — see the note below.)* When this plan was first written the answer was one hit at line 343, recorded as a genuine open item. The sibling spec `2026-08-11-component-contract` has since landed (`b8b96d5`) and cleared it, so the retired literal now survives nowhere on the active surface. Line 343 still exists and still describes this spec; only the stale `verified 0/31 files` wording is gone. If you get a non-zero count here, the sibling's roadmap edit was reverted.

> **Why this step changed.** Line 343 was genuinely unowned — no spec's acceptance criteria claimed it (see Discrepancy 1). It was cleared because `/implement-phase` added it as an explicit constraint in the sibling lane's brief, not because any spec required it. That is scope added through an orchestration instruction rather than a spec amendment, which is why this plan went stale between being written and being run. The fix was correct; the route to it was not, and the phase report records it.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 "Recorded finding (not edited)"; Business Rule 8

**Notes:**

---

### Scenario 4: The authoring path teaches frontmatter, not the workaround

**Source:** Story 1 AC 4; Task 1.4. This is the file the false claim was propagating through — every future command was being taught the workaround.

**Preconditions:**
- None.

**Steps:**
1. Read `commands/new-command.md:145-155` (the Model tier note in Step 2.1).
2. Read the last bullet of the "Quality bars for the generated command file" list (line 175).
3. Run `grep -n -F "Model tier (advisory only)" commands/new-command.md; echo "EXIT=$?"`.

**Expected Result:**
- Step 1: line 145 reads "Command files carry `---` YAML frontmatter, so weight intent ships as a `model_tier:` field alongside the existing `name:` and `description:` keys". Beneath it is a fenced `yaml` block showing `---` / `name:` / `description:` / `model_tier: <tier>` / `---`. The tier-selection guidance, the "advisory documentation only … never resolves at runtime" caveat, and the ADR-016 + `.writ/docs/model-tiers.md` links all survive.
- Step 2: "Declare the advisory `model_tier: <tier>` field in the generated command's `---` frontmatter (see Step 2.1's Model tier note above)".
- Step 3: no output, `EXIT=1`. The locked prose string is gone from the only file that ever produced it.
- **Note the label drift:** the spec and Story 1 both call this the "Step 2.2 checklist bullet (line 171)". It is actually the last bullet of Step 2.1's quality-bars list, and `#### Step 2.2: Validate Integration` begins two lines below it. The right bullet was edited; the name for it in the spec is wrong. Cosmetic.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `commands/new-command.md:145-155`, `:175`

**Notes:**

---

## Mirror Parity — The Constraint With No Gate

> `cursor/writ.mdc` is a full mirror of `system-instructions.md`, not a Prime-Directive-only mirror. The spec names unmirrored drift as its **likeliest silent failure**. Scenario 5 checks the mirror; Scenario 6 exists because a passing Scenario 5 is not evidence that anything would have caught a failing one.

### Scenario 5: The mirror is in sync

**Source:** Business Rule 2; Stories 1, 2, 3 AC "line for line identical"

**Preconditions:**
- None.

**Steps:**
1. Run `diff system-instructions.md cursor/writ.mdc`.
2. Run `wc -l system-instructions.md cursor/writ.mdc`.

**Expected Result:**
- Step 1 prints exactly one hunk: `289a290,299`, followed by ten `>` lines — a blank line, `## Self-Dogfooding (Writ Repo Only)`, and the eight lines of that section. Nothing else. Lines 1–289 are byte-identical across both files.
- Step 2: **289** and **299**. The 10-line delta is the appendix and nothing more.
- Both files open with the same three-line `---` / `alwaysApply: true` / `---` header, so the bodies align by absolute line number, not merely by content. (The technical spec claims this header is unique to `writ.mdc`; it is not — see Discrepancy 3.)

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 1–3, mirror tasks 1.3 / 2.3 / 3.3

**Notes:**

---

### Scenario 6: Make the gate's blind spot visible

**Source:** Business Rule 2; technical spec § "The mirror constraint". **Run this one even though Scenario 5 passed.** Scenario 5 shows the mirror is correct today. This shows that if it were not, `bash scripts/eval.sh` would still report `Findings: 0` — the correctness came from three manual diff tasks, not from the suite.

**Preconditions:**
- A scratch directory. Use `S=$(mktemp -d)`. Nothing under version control is touched.

**Steps:**
1. Confirm which lines the gate actually compares:
   `grep -n '^## ' system-instructions.md` — note that `## Prime Directive` starts at **34** and the next `## ` heading (`## File Organization`) at **132**. The gate's window is lines 34–131.
2. Note where this spec's entire edit surface lives: `## Skills` at **221** and `## Model Tiers` at **260**. Both are outside 34–131.
3. Simulate the drift on copies:
   ```
   S=$(mktemp -d)
   cp system-instructions.md $S/si.md; cp cursor/writ.mdc $S/wm.mdc
   # falsify the Commands carrier bullet in one copy only
   sed -i '' '275s|32/32|9/31|' $S/si.md      # GNU sed: drop the ''
   ```
4. Run the gate's own extractor over both copies and diff the extracts:
   ```
   ex() { awk '/^## Prime Directive[[:space:]]*$/ {c=1} c && /^## [^#]/ && $0 !~ /^## Prime Directive[[:space:]]*$/ {exit} c {print}' "$1"; }
   ex $S/si.md > $S/a; ex $S/wm.mdc > $S/b; diff $S/a $S/b && echo "GATE WOULD PASS"
   ```
5. Now run the check a human would actually need: `diff $S/si.md $S/wm.mdc`.
6. Clean up: `rm -rf $S`.

**Expected Result:**
- Step 4 prints `GATE WOULD PASS` — the two Prime Directive extracts are identical, so `check_prime_directive_sync` finds nothing. A falsified frontmatter count in the root contract would ship green.
- Step 5 shows the drift on line 275, plus the usual `289a290,299` appendix hunk.
- Conclusion to carry forward: `prime-directive-sync` covers **98 of 289 lines** and none of this spec's edit surface. The three mirror-diff tasks in Stories 1–3 are the only thing that made Scenario 5 pass, and nothing in the repository will keep it passing. This is a live gap, not a hypothetical — see Discrepancy 2.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `scripts/eval.sh:302` (`check_prime_directive_sync`) and `extract_prime_directive` above it

**Notes:**

---

## Story 2: Deprecate the Ordinal-Offset Reservation

### Scenario 7: The schema is two values, and the four retired constructs are gone

**Source:** Story 2 AC 1 and 3

**Preconditions:**
- None.

**Steps:**
1. Read `system-instructions.md:277-289` (§ Model Tiers → **Schema** and the behavior table).
2. Run:
   ```
   grep -rn -F -e "ordinal" -e "Clamp to floor" -e "2026-10-16" -e "|-N>" -e "-[0-9]+" \
     system-instructions.md cursor/ commands/ agents/ adapters/ scripts/ .writ/docs/ .writ/manifest.yaml
   echo "EXIT=$?"
   ```
3. Read `.writ/docs/model-tiers.md` § "Allowed Values" (line ~90) and confirm the manifest's skills schema comment: `grep -n 'model_tier: <' .writ/manifest.yaml`.

**Expected Result:**
- Step 1: **Allowed values:** `orchestration` or `capability` — regex `^(orchestration|capability)$`. No `-N` clause. The behavior table has four rows — unset, capability-unavailable, unrecognized-value, and `model:`-wins — with **no** "Reserved ordinal offset beyond available bands | Clamp to floor" row. No "Reserved ordinal offsets … are reserve-only" paragraph and no `> **Review trigger: 2026-10-16**` blockquote follow it.
- Step 2: no output, `EXIT=1`.
- Step 3: the explainer restates `^(orchestration|capability)$`; the manifest comment reads `model_tier: <orchestration|capability>`.
- What survives, and should: the unrecognized-value degradation row (line 288) still says warn and fall back to inherit. A `model_tier: -1` written tomorrow is simply an unknown value — the deprecation added no new failure path.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `system-instructions.md:277-289`, `cursor/writ.mdc`, `.writ/docs/model-tiers.md`, `.writ/manifest.yaml`

**Notes:**

---

### Scenario 8: The lint rejects an ordinal and still accepts both named tiers

**Source:** Story 2 AC 2; Task 2.6. Documentation saying a value is retired is not the same as a validator refusing it.

**Preconditions:**
- `bash` available. Uses a scratch directory only.

**Steps:**
1. Build three fixtures:
   ```
   S=$(mktemp -d)
   for v in -1 orchestration capability; do
     printf -- '---\nname: t\ndescription: "Do a thing well."\nmodel_tier: %s\n---\n\nBody.\n' "$v" > $S/$v.md
   done
   ```
2. Run `bash scripts/lint-skill.sh $S/-1.md 2>&1 | grep model_tier`.
3. Run `bash scripts/lint-skill.sh $S/orchestration.md 2>&1 | grep -c model_tier` and the same for `capability.md`.
4. Run `bash scripts/lint-skill.sh skills/*/SKILL.md; echo "EXIT=$?"`.
5. Clean up: `rm -rf $S`.

**Expected Result:**
- Step 2 prints, verbatim except the path:
  `❌ <path>:4: model_tier '-1' is invalid. Use 'orchestration' or 'capability'.`
  The message names only the two surviving tiers — the old "or a reserved negative offset (e.g. -1)" wording is gone.
- Step 3 prints `0` for both. Neither named tier regressed.
- Step 4 exits `0` — all six real skills still lint clean under the narrowed grammar.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `scripts/lint-skill.sh` (`lint_model_tier`, allow-list and message)

**Notes:**

---

### Scenario 9: The adapters really did carry ordinals — and were cleared

**Source:** Story 2 "Scope note"; Story 2 AC 3. **The technical spec asserted the opposite.** This scenario exists so a human confirms the implementer's correction rather than the spec's claim.

**Preconditions:**
- Full git history available.

**Steps:**
1. Read `sub-specs/technical-spec.md:119` — "no adapter table changes — `adapters/{cursor,claude-code,codex,openclaw}.md` map `orchestration`/`capability` only and never mention ordinals."
2. Run `git show b50fd7d -- adapters/`.
3. Run `grep -rn -F -e "ordinal" -e "-N" adapters/; echo "EXIT=$?"`.
4. Read the tier tables that remain: `adapters/cursor.md:157-162` and `adapters/openclaw.md:60-67`.

**Expected Result:**
- Step 2 shows **all four adapters changed**, contradicting step 1's claim: `cursor.md` and `openclaw.md` each lost a table row (`| reserved ordinal \`-N\` | reserve-only; clamps … |`); `claude-code.md` and `codex.md` each lost a trailing sentence ("Reserved negative ordinal offsets (`-N`) are not resolved beyond the 2-band clamp today…").
- Step 3: no output, `EXIT=1`.
- Step 4: each table now has exactly three rows — `orchestration`, `capability`, `unset`. The graceful-degradation paragraph beneath each is untouched, so an unrecognized value still warns and inherits on every platform.
- The commit message states the correction plainly: "The technical spec claimed no adapter mentioned ordinals; four did." Story 2's AC 3 named `adapters/` in its grep list, so clearing them was required by the acceptance criteria regardless of the spec's bad measurement.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 "Scope note — the adapters did carry ordinals"; commit `b50fd7d`

**Notes:**

---

### Scenario 10: ADR-016 and the rest of history keep the reservation

**Source:** Business Rules 3 and 6; Story 2 AC 4

**Preconditions:**
- None.

**Steps:**
1. Run `grep -rn -F "2026-10-16" .writ/decision-records/ .writ/specs/archive/ .writ/research/ CHANGELOG.md | wc -l`.
2. Run `grep -n -F "ordinal" .writ/decision-records/adr-016-model-tier-delegation.md | head`.
3. Confirm no superseding record was retrofitted into ADR-016: `git log --oneline -- .writ/decision-records/adr-016-model-tier-delegation.md`.

**Expected Result:**
- Step 1: **7 hits**, unchanged from the pre-story count Story 2 recorded.
- Step 2: ADR-016 still describes the reserved negative ordinal offsets as decided. It records what was decided on 2026-07-10; a superseding decision is recorded forward, not retrofitted.
- Step 3: no commit from this spec appears. Whether the deprecation warrants its own ADR is explicitly a maintainer call outside this spec's file set — if you disagree, that is an ADR to write, not a UAT failure.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Business Rule 3; spec.md → Out of Scope

**Notes:**

---

## Story 6: Retire the Prose-Note Carrier in the Explainer and the Lint

> Story 6 deleted a branch from `lint_model_tier()`. The risk in deleting a lint branch is not that it fails loudly — it is that it removes more coverage than intended and nothing notices. Scenarios 11 and 12 are the two halves of that question.

### Scenario 11: The removal is exactly one branch wide

**Source:** Story 6 AC 4; Task 6.7. **This is the scenario that distinguishes "the prose branch was removed" from "model_tier validation was weakened."**

**Preconditions:**
- Scratch directory only.

**Steps:**
1. Read `scripts/lint-skill.sh:265-285` (`lint_model_tier`). Confirm the loop body has one `if` (line 274) and one `else`/`continue` — no `elif`.
2. Build two fixtures that differ only in carrier:
   ```
   S=$(mktemp -d)
   printf -- '---\nname: t\ndescription: "Do a thing well."\n---\n\n> **Model tier (advisory only):** bogus — commands run at the session model.\n' > $S/prose.md
   printf -- '---\nname: t\ndescription: "Do a thing well."\nmodel_tier: bogus\n---\n\nBody.\n' > $S/fm.md
   ```
3. Run `bash scripts/lint-skill.sh $S/prose.md 2>&1 | grep -c model_tier` — expect the branch to be gone.
4. Run `bash scripts/lint-skill.sh $S/fm.md 2>&1 | grep -c model_tier` — expect branch 1 intact.
5. Prove agent config-block capture survives:
   ```
   cp agents/architecture-check-agent.md $S/ok.md
   sed 's/^model_tier: .*/model_tier: bogus/' agents/architecture-check-agent.md > $S/bad.md
   bash scripts/lint-skill.sh $S/ok.md 2>&1 | grep -c model_tier
   bash scripts/lint-skill.sh $S/bad.md 2>&1 | grep -c model_tier
   ```
6. Clean up: `rm -rf $S`.

**Expected Result:**
- Step 3: **0**. A prose note with a bogus value produces no `model_tier` finding — the `elif` is genuinely gone, not merely reworded.
- Step 4: **1**. `model_tier: bogus` in frontmatter is still caught. Branch 1 was not damaged.
- Step 5: **0** then **1**. The agent's fenced Agent Configuration value is still captured and still validated. This works because branch 1's regex is unanchored and the function scans every raw line of the file — not because a second branch handles it.
- Together these three results are the whole claim: one carrier shape lost validation, and it is the retired one.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — Files: `scripts/lint-skill.sh` (`lint_model_tier`, prose `elif` removed)

**Notes:** Removal beat retargeting because there is no second frontmatter shape to point an `elif` at — a command's `model_tier:` line is already matched by branch 1. Retargeting would have duplicated branch 1.

---

### Scenario 12: The lint's self-description matches what it does, and the check it feeds still passes

**Source:** Story 6 AC 5 and 6

**Preconditions:**
- None.

**Steps:**
1. Run `bash scripts/lint-skill.sh` with no arguments and read the `usage()` output.
2. Read the comment block above `lint_model_tier()` (`scripts/lint-skill.sh:253-262`).
3. Run `bash scripts/eval.sh --check=skill-lifecycle`, then open the report path it prints.
4. Run `grep -c -e 'candidate|proven|promoted' -e 'State is EARNED from evidence' -e 'Lifecycle-unearned' -e 'Lifecycle-evidence' scripts/lint-skill.sh`.

**Expected Result:**
- Step 1: "Any declared model_tier value (skill or command frontmatter, or an agent config block) must be 'orchestration' or 'capability'". No command prose note. No reserved negative offset.
- Step 2: the block says the check "recognizes one shape wherever it appears" and names the three sites — skill frontmatter, command frontmatter, agent Agent Configuration/Specification blocks. The old "it recognizes two shapes: … 2. Locked prose" enumeration is gone. Both the ordinal half (Story 2) and the prose half (Story 6) of this block are consistent with each other.
- Step 3: report shows `Findings: 0` and the `skill-lifecycle` check passing. The four `require_literal` assertions that check makes against this script all live in `lint_lifecycle()`, not `lint_model_tier()`, so the removal had no mechanical path to them. Step 4 prints **6** — the four literals across six lines, all still present.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — Files: `scripts/lint-skill.sh` (`usage()`, `lint_model_tier` comment block); `scripts/eval.sh:2476`

**Notes:**

---

### Scenario 13: The user-facing explainer describes the real carrier and the real lint

**Source:** Story 6 AC 1 and 3. `.writ/docs/` ships to installed projects through `install.sh`'s doc fan-out, so this is user documentation, not an internal note. **No eval check reads this file** — these acceptance criteria are the only verification it has.

**Preconditions:**
- None.

**Steps:**
1. Read `.writ/docs/model-tiers.md` § "Where `model_tier` Lives" — the three-row carrier table (lines 40–45).
2. Read line 84 (`/new-command` emission) and line 86 (the `lint-skill.sh` validation sentence).
3. Cross-check line 84 against the artifact it describes: re-read `commands/new-command.md:145-155` from Scenario 4.
4. Run `grep -n -F "Reserved Ordinal" .writ/docs/model-tiers.md; echo "EXIT=$?"`.

**Expected Result:**
- Step 1: the **Command** row's Carrier column reads "The existing `---` YAML frontmatter that already holds `name:` and `description:` — carried by 32/32 files under `commands/` (31 commands + `_preamble.md`)", and its Example column is `model_tier: orchestration   # advisory only` — the same shape as the Skill row directly above it. The Skill and Agent rows and the umbrella-term sentence beneath the table are unchanged.
- Step 2: line 84 says `/new-command` emits `model_tier: <tier>` into the generated command's `---` frontmatter alongside `name:` and `description:`. Line 86 says the lint validates a declared value "in skill frontmatter, in command frontmatter, or in an agent's Agent Configuration block" against `^(orchestration|capability)$` — no prose note, and the allow-list Story 2 narrowed is intact.
- Step 3: the two agree. This is the check that matters — line 84 was rewritten only after the file it describes was measured, and the ownership conflict over `commands/new-command.md` had been ruled in this spec's favor, so no divergence needed recording.
- Step 4: no output, `EXIT=1`. The whole `## Reserved Ordinal Offsets` section is gone, not just its trigger.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — Files: `.writ/docs/model-tiers.md:40-45`, `:84`, `:86`

**Notes:**

---

## Story 4: Reconcile `.writ/manifest.yaml`

### Scenario 14: Version matches, and parity holds in both directions

**Source:** Story 4 AC 1–4 and 6

**Preconditions:**
- `python3` available for the entry count.

**Steps:**
1. Run `cat VERSION` and `grep -n '^  version:' .writ/manifest.yaml`.
2. Count data entries per section:
   ```
   python3 - <<'EOF'
   import re
   sec=None; c={}
   for l in open('.writ/manifest.yaml'):
       m=re.match(r'^([a-z_]+):\s*$', l)
       if m: sec=m.group(1)
       if re.match(r'^\s*-?\s*file:', l): c[sec]=c.get(sec,0)+1
   print(c, 'total', sum(c.values()))
   EOF
   ```
3. Run `grep -c 'file:' .writ/manifest.yaml`, then `sed -n '225p' .writ/manifest.yaml`.
4. Reverse parity: `ls commands/*.md | grep -v '_' | wc -l`, `ls agents/*.md | wc -l`, `ls skills/*/SKILL.md | wc -l`.
5. Run `bash scripts/eval.sh --check=manifest` and `bash scripts/gen-skill.sh --check; echo "EXIT=$?"`.

**Expected Result:**
- Step 1: both print `0.28.0`. The stale `0.13.1` — fifteen minor releases behind — is gone.
- Step 2: `{'commands': 31, 'agents': 7, 'skills': 6} total 44`.
- Step 3: raw grep prints **45**; line 225 is `#     file: skills/<name>/SKILL.md     # required, must exist on disk` — a commented line inside the skills-schema documentation block, not a data entry. This is the contract's "45 `file:` entries" reconciled: 44 data + 1 comment. `.writ/product/roadmap.md:343` independently states 44.
- Step 4: **31**, **7**, **6** — set-identical to step 2 in both directions. `commands/_preamble.md` is the 32nd file in `commands/` and is deliberately unlisted; `check_manifest` skips `_*.md` by prefix.
- Step 5: manifest check PASS; `gen-skill.sh --check` exits `0`. The generated `SKILL.md` does not render `metadata.version`, so the bump did not stale the catalog.
- Only one line of data changed in this story. No `file:`, `purpose:`, or `tags:` entry was rewritten — the reconciliation deliverable was verification recorded as evidence, not manufactured drift.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — Files: `.writ/manifest.yaml:4`; `scripts/eval.sh:454-521`

**Notes:**

---

## Story 5: Formally Deprecate `decisions.md`

### Scenario 15: The precedence claim is gone and the eight decisions are byte-identical

**Source:** Story 5 AC 1–3. The substantive part of this story is the *removal*, not the header. A superseded file asserting the highest override priority in the repository is the consequential stale claim; a deprecation banner that leaves it in place fixes nothing.

**Preconditions:**
- Full git history available.

**Steps:**
1. Read `.writ/product/decisions.md:1-7`.
2. Run:
   ```
   grep -rn "Override Priority" .writ/product/; echo "EXIT=$?"
   grep -n -F "Instructions in this file override conflicting directives" .writ/product/decisions.md; echo "EXIT=$?"
   ```
3. Prove the bodies are untouched:
   ```
   awk '/^## 2026-02-27: Product Identity & Direction$/,0' .writ/product/decisions.md | md5
   git show fe2af84:.writ/product/decisions.md | awk '/^## 2026-02-27: Product Identity & Direction$/,0' | md5
   ```
4. Run `grep -c '^\*\*ID:\*\* DEC-' .writ/product/decisions.md`.

**Expected Result:**
- Step 1: a four-line blockquote — **DEPRECATED — superseded by `.writ/decision-records/`**; the supersession dated to 2026-03-19 (`2026-03-19-command-suite-evolution`, Story 8) with what changed (`/plan-product` stopped emitting the file and now writes ADR-000-series records); an explicit statement that the file "asserts no override priority over user memories, project settings, or any active directive"; and retention as the historical record of DEC-001–DEC-008 with no migration required or planned.
- Step 2: both greps return nothing, `EXIT=1` twice. The old `> Override Priority: Highest` blockquote and the bolded override sentence survive in no form.
- Step 3: both md5 values match — `c9230d180e251f8b047aac11e4c9038b`. Deprecation annotated the head; it rewrote no decision.
- Step 4: **8**. DEC-001 through DEC-008 are all present and unconverted.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `.writ/product/decisions.md:1-7`

**Notes:** What made this claim worth removing: it asserted precedence over user memories and project settings, from a document superseded on 2026-03-19 and last touched 2026-07-09. An agent reading the file top-down had no signal that any of it was stale.

---

### Scenario 16: The promise about *other people's* projects survives verbatim

**Source:** Story 5 AC 4; Task 5.6. The obvious objection to Story 5 is that `/plan-product` and `/create-adr` promise users their `decisions.md` is never modified. That promise governs user repositories; this file is a development-workspace artifact under `.writ/`.

**Preconditions:**
- Full git history available.

**Steps:**
1. Read `commands/plan-product.md:345` and `commands/create-adr.md:170`.
2. Run `git diff --stat fe2af84 e23fbdc -- commands/plan-product.md commands/create-adr.md` (`e23fbdc` is this spec's merge commit — see the note on Scenario 3 step 3).

   > **Corrected 2026-08-11 (UAT execution).** Originally ended at `HEAD`, which now reports `2 files changed, 12 insertions(+)` from `e691de6` (component-contract adding the `problem:`/`outcome:`/`exit_criteria:` frontmatter — 6 lines per file). Both promise sentences are byte-unchanged; only the surrounding file grew. Scoped to this spec's merge the diff is empty, which is the assertion.
3. Run `grep -rn -F ".writ/product/decisions.md" commands/ agents/ scripts/ system-instructions.md` to enumerate every live inbound reference.

**Expected Result:**
- Step 1: both still tell users their existing `.writ/product/decisions.md` is left alone — `plan-product.md` says it "is **not** modified or deleted — soft deprecation only"; `create-adr.md` says it "is **not** modified, migrated, or deleted by these instructions" and that migration is "entirely optional and unscripted." (The spec quotes the `create-adr` wording for both; only that file carries the word "migrated.")
- Step 2: **empty**. Neither command file was touched by this spec. What `/plan-product` and `/create-adr` do to a user's project is unchanged.
- Step 3: the references you find are descriptions of user projects, not of this repository's copy, and none of them now contradicts the deprecation header.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — `commands/plan-product.md:345`, `commands/create-adr.md:170` (both unchanged)

**Notes:**

---

## Story 3: Resolve `required_skills:` by Adoption

### Scenario 17: The fired trigger is closed on the record, in all five places

**Source:** Story 3 AC 1, 3, 4; Business Rule 7. The trigger fired 2026-08-03 and sat unactioned for 8 days. Deleting it without recording *which* of its two outcomes was chosen would turn a visible overdue signal into an invisible one — which is the failure mode ADR-020 names for the four ignored leanness warnings.

**Preconditions:**
- None.

**Steps:**
1. Read `system-instructions.md:252` and check it for all four required facts.
2. Confirm the schema above it is untouched: read lines 238–250 (the five schema bullets and the Harness contract paragraph).
3. Run `grep -rn -F "reserve-only" system-instructions.md cursor/ .writ/docs/skills.md adapters/ commands/ agents/ scripts/ skills/; echo "EXIT=$?"`.
4. Read `.writ/docs/skills.md:136`, `adapters/cursor.md:217`, `adapters/claude-code.md:396`, `adapters/openclaw.md:277`.
5. Run `grep -rn -F "2026-08-03" .writ/decision-records/ .writ/specs/archive/ CHANGELOG.md | wc -l` and compare against Story 3's recorded pre-story count.

**Expected Result:**
- Step 1: `**Status: adopted.**` followed by (1) the trigger fired **2026-08-03**, 90 days post-ship per `2026-05-03-skills-foundation`; (2) the outcome is **revisit → adopt**, not deprecate; (3) the first consumer is Phase 10 progressive disclosure with a link to ADR-021, and why — it needs the declarative, harness-resolved, per-invocation load mechanism this convention already specifies, graceful degradation included, so deprecating would have meant redesigning it under a new name inside the same phase; (4) the schema is adopted **unchanged**.
- Step 2: the five bullets (optional array, manifest-matching names, order preserved, duplicates deduplicated, unknown names warn) and the Harness contract are byte-unchanged. The convention was adopted as specified, not redesigned under cover of a status change.
- Step 3: `EXIT=1`, no output. (Two `reserve-only` hits survive at `.writ/product/roadmap.md:299` and `:368` — those describe ADR-018's third-party skill trust model, a different reservation entirely.)
- Step 4: the explainer carries the same resolution with an ADR-021 link relative to `.writ/docs/`; the three adapters carry one byte-identical adoption sentence applied three times, so they cannot drift, and each file's per-platform pre-load mechanism sentence is otherwise unchanged.
- Step 5: unchanged. `.writ/specs/archive/2026-05-03-skills-foundation/`, where "reserve-only" originated, still records what was true at ship time.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `system-instructions.md:252`, `cursor/writ.mdc:252`, `.writ/docs/skills.md:136`, three adapters

**Notes:**

---

### Scenario 18: Adoption is declared, not demonstrated — and the text says so

**Source:** Business Rule 1; Story 3 "Honesty about the consumer". **This is the scenario a reviewer should personally confirm.** The trigger asked whether anything had adopted `required_skills:` in 90 days. The answer was no, and it is still no. What changed is the recorded disposition, not the adoption.

**Preconditions:**
- None. Reading and grepping only.

**Steps:**
1. Run `grep -rn "required_skills" commands/ agents/ skills/ claude-code/ 2>/dev/null`.
2. Count actual declarations rather than mentions: look for a line that *declares* the field followed by array entries, in any command's or agent's frontmatter.
3. Run `ls .writ/specs/` and look for a progressive-disclosure spec.
4. Read `.writ/product/roadmap.md` Phase 10 → Features → the **Progressive disclosure** bullet and note its checkbox.
5. Re-read the final sentence of `system-instructions.md:252` and of `.writ/docs/skills.md:136`.

**Expected Result:**
- Step 1: **4 hits, all documentation.** `commands/new-skill.md:228`, `:242`, `:267` and `skills/gbrain-interop/SKILL.md:155` — the last two describe `required_skills:` as ADR-014's `promoted` bar, which adoption does not change.
- Step 2: **zero declarations.** No command, no agent, no skill declares the field.
- Step 3: five Phase 10 specs exist — `autonomy-gate-classes`, `component-contract`, `governor-instrumentation`, `loop-bounds`, `retire-dead-prescription`. **There is no progressive-disclosure spec.** The named first consumer has not been specced, let alone built.
- Step 4: the Progressive disclosure feature is `- [ ]` — unchecked, `Effort: L`, the largest item in the phase.
- Step 5: both files say it plainly — "Progressive disclosure's extraction work lands the first real declarations; no agent or command declares the field yet" / "no consumer declares the field yet."
- **Read this correctly.** The resolution is defensible: a convention with a committed consumer inside the same phase is worth keeping, and deprecating it would have meant redesigning the same mechanism under a new name. But `Status: adopted` on a field with zero declarations is a *commitment*, and the commitment's own first consumer is the phase's largest unbuilt item. If progressive disclosure slips or changes shape, this trigger is closed and nothing will fire again. The honesty of the final sentence is what makes that visible — verify it survives any future edit to this paragraph.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 "Honesty about the consumer (Business Rule 1)"; `.writ/product/roadmap.md` Phase 10 Features

**Notes:**

---

## Whole-Spec Gate

Run once, after all eighteen scenarios:

```
bash scripts/eval.sh                 # → Findings: 0, Run errors: 0
bash scripts/gen-skill.sh --check    # → exit 0
git status --porcelain               # → empty (no scenario should have dirtied the tree)
```

Measured on this branch: `Findings: 0`, `Run errors: 0`, `gen-skill.sh --check` exit `0`, clean tree. The spec's hardest constraint was that it could not buy truth with a red gate; it did not.

---

## Discrepancies Worth Recording

These are not scenario failures — the spec was implemented as written, and in two cases the implementer corrected the spec rather than following it off a cliff. They are recorded so a tester sees them stated rather than discovering them later.

1. **`.writ/product/roadmap.md:343` carried `verified 0/31 files` and no spec claimed it — RESOLVED 2026-08-11, but by an irregular route.** `.writ/product/` is on the active surface per Business Rule 3, so the retired literal survived on the active surface in exactly one place. Story 1 recorded this as a finding rather than repairing it, correctly — the roadmap belongs to the sibling spec `2026-08-11-component-contract`. But that sibling's Story 1 claimed only roadmap lines 316 and 330 and its Revision Log row; **line 343 appeared in no spec's acceptance criteria.** The analysis in this plan was right that waiting could not close it.

   It was closed anyway: `/implement-phase` added clearing line 343 as an explicit constraint in the sibling lane's brief, and that lane made a fourth roadmap edit its own spec's text says it would not make (*"No other roadmap line is touched"*). All the sibling's hard constraints still held — `wc -l` 424, `git diff --numstat` 4/4 equal, and the line references `:341`/`:343` that this spec cites still resolve. Verified 2026-08-11: `grep -c -F "verified 0/31 files" .writ/product/roadmap.md` → **0**.

   **The finding worth keeping is the process one, not the line.** An orchestrator adding scope through a lane brief gets the edit made but leaves no trace in any spec's acceptance criteria, and silently invalidates artifacts written against the prior state — this plan's Scenario 3 step 4 went stale the moment the sibling merged. The correct route was an `/edit-spec` amendment to the sibling before its lane opened. Recorded in the Phase 10 report.

2. **The mirror stayed correct by discipline, and nothing will keep it correct.** `check_prime_directive_sync` compares 98 of `system-instructions.md`'s 289 lines. Every line this spec touched — § Skills at 221, § Model Tiers at 260 — is outside that window (Scenario 6 demonstrates a falsified frontmatter count shipping green). Three stories each carried a manual mirror-diff task and all three were done, which is why Scenario 5 passes. The next person to edit either file gets no such reminder. A full-file diff check would be a small addition to `eval.sh`; the spec explicitly forbade adding one ("Any new eval check" is Out of Scope), so the gap is deliberate and still open.

3. **The technical spec's measurements were wrong in two places, and the implementer caught both.** (a) It stated that no adapter mentions ordinals; all four did, and Story 2's own AC 3 required clearing them (Scenario 9). (b) It stated that `cursor/writ.mdc` "additionally carries a 3-line Cursor `---\nalwaysApply: true\n---` header (which is why its body still aligns 1:1 by content, not by absolute line index)" — `system-instructions.md` carries the identical header, and the two files align 1:1 by absolute line index (289 vs 299 = exactly the 10-line appendix). Neither error changed a deliverable, but both were in the document an implementer is told to trust for line-level measurements. Business Rule 1 was aimed at the spec's replacement claims; it should have been aimed at the technical spec too.

4. **The prose-note carrier now has neither a producer nor a consumer — but nothing prevents a new producer.** Story 6 removed the only lint that validated `> **Model tier (advisory only):** <value>`. That was safe because Story 1 had already converted `/new-command`'s producer to frontmatter and zero shipped commands carried the note (Scenario 11 confirms both halves). The residual risk is narrow and real: a command file that hand-writes the old prose note tomorrow will pass every check in the repository, silently. The alternative — keeping a bespoke per-variant regex alive for a carrier the root contract has retired — is the exact cost ADR-020 cites against prose, so this was the right trade. It is a trade, not a free removal.

5. **Story 4's deliverable was verification, and it is worth understanding why that counted.** `check_manifest` already enforced both parity directions and passed before the story started, so there was no drift to reconcile — only a version fifteen minor releases stale. The story changed one line and recorded the counts as evidence rather than manufacturing edits to look substantial. That is the correct outcome, but it means Scenario 14's parity results prove the *gate* works, not that this story did anything to make them true.

6. **Two contract literals never matched the repository, and were documented instead of amended.** `.writt/product/decisions.md` (clause d) is a typo — no `.writt/` directory exists. "45 `file:` entries" (clause c) is a raw grep count against 44 data entries. Both were recorded in `spec.md` → "Contract reading notes" as reading notes rather than contract amendments, and both were implemented against the real repository (Scenarios 14, 15). This is the right handling of a locked contract with a factual error in it; noted so the pattern is visible rather than inferred.

---

## Sign-Off

| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | [ ] Pass [ ] Fail |
| Reviewer | | | [ ] Pass [ ] Fail |

**Overall UAT:** [ ] Pass  [ ] Fail

**Notes:**

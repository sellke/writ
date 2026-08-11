# UAT Plan: Component Contract

> **Generated:** 2026-08-11
> **Spec:** `.writ/specs/2026-08-11-component-contract/`
> **Stories Covered:** 7 of 7 completed
> **Total Scenarios:** 18

## How to Use This Plan

1. Work through scenarios in order (grouped by story).
2. Run the commands exactly as written, from the repository root, on a branch that contains this spec (`phase/10-component-contract` or later).
3. Mark Pass or Fail — add notes for anything that differs from the Expected Result.
4. A Fail is filed as an issue or fed back to the spec; it is not fixed inline.
5. The feature passes UAT when every scenario passes, or when a failure is explicitly accepted as a known limitation.

> **Note on this methodology repo:** the deliverables are markdown. Every scenario below is a grep, a diff, an `eval.sh` run, or a file read. **No scenario modifies a tracked file.** Nothing here needs a scratch directory.
>
> **The base commit is `e23fbdc`** — the last commit before this spec's first story. Every `git diff` below measures against it. `b8b96d5` is the merge that closed the spec and is `HEAD` at the time of writing; substitute `HEAD` if later work has landed.
>
> **Scenarios 9, 10 and 11 are the point of this spec.** Everything else confirms that fields are *present*. Only those three ask whether they carry information. Budget ten minutes for Scenario 9 and do it by hand — it does not have a command that answers it.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|------------------|
| Story 1: Contract schema, docs, authoring template, premise amendments | ✅ Covered | 6 | AC: 4, Scope addition: 1, Honesty check: 1 |
| Story 7: Agent config contracts, both carriers | ✅ Covered | 2 | AC: 2 |
| Stories 2–5: The 30 remaining command contracts | ✅ Covered | 4 | Success Criterion 6: 1, BR2: 1, BR3: 1, BR4: 1 |
| Story 6: The eighteen `## Completion` sections | ✅ Covered | 2 | AC: 1, BR7: 1 |
| Whole-spec: budget, regression, and the two honest limits | ✅ Covered | 4 | SC 7: 1, SC 8: 1, Honesty: 2 |

---

## Story 1: Contract Schema, Docs, Authoring Template, and the Two Premise Amendments

### Scenario 1: Full command coverage — 31/31, and `_preamble.md` gained nothing

**Source:** Success Criteria 1 and 3; Business Rule 8. This is the presence check. It proves nothing about quality — Scenarios 9–11 do that — but a gap here invalidates everything after it.

**Preconditions:**
- Clean checkout at the repository root.

**Steps:**
1. Run:
   ```
   ls commands/*.md | wc -l
   for k in problem outcome exit_criteria; do
     printf '%s: ' "$k"; grep -l "^$k:" commands/*.md | grep -v _preamble | wc -l
   done
   grep -l '^## Completion' commands/*.md | wc -l
   ```
2. Run `grep -c '^problem:\|^outcome:\|^exit_criteria:\|^## Completion' commands/_preamble.md`.
3. Run `git diff --numstat e23fbdc..b8b96d5 -- commands/_preamble.md`.
4. Run `for f in commands/*.md; do echo "$(basename $f) $(grep -c '^## Completion' $f)"; done | sort -k2 -n | head -3`.

**Expected Result:**
- Step 1: **32** files; **31** for each of `problem:`, `outcome:`, `exit_criteria:`; **31** carrying `## Completion`. Thirteen of those 31 sections pre-existed; eighteen were written by Story 6.
- Step 2: **0**. `commands/_preamble.md` is the 32nd file and is not a command — it carries `disable-model-invocation: true`, is never invoked, and has no completion state.
- Step 3: **empty output**. The file was not touched by any commit in this spec. This is the check that distinguishes "excluded by design" from "excluded by luck" — an editor globbing `commands/*.md` would have hit it.
- Step 4: `_preamble.md 0` is the only zero; every other file reports exactly `1`. No duplicate sections.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Stories 1–6; Business Rule 8

**Notes:**

---

### Scenario 2: The keys landed in the frontmatter, not in the body

**Source:** Technical spec § Error & Rescue Map, row 1. Appending to a `---` block is the one mechanical way this spec could have silently corrupted 31 files. **The check the technical spec prescribed for this does not work — see the Expected Result.**

**Preconditions:**
- None.

**Steps:**
1. Find each command's frontmatter terminator:
   ```
   for f in commands/*.md; do
     echo "$(basename $f) term=$(awk 'NR>1 && /^---$/{print NR; exit}' "$f")"
   done
   ```
2. Run the technical spec's own prescribed check and read what it returns:
   `for f in commands/*.md; do echo "$f $(grep -c '^---$' "$f")"; done | head -5`
3. Read `commands/review.md` lines 1–11 and confirm the block opens at line 1 with `---`, carries `name`, `description`, `problem`, `outcome`, `exit_criteria` in that order, and closes at line 10.
4. Confirm the three keys were appended, never inserted: `grep -n '^name:\|^description:\|^problem:\|^outcome:\|^exit_criteria:' commands/plan-product.md`.

**Expected Result:**
- Step 1: **every command reports `term=10`** except `commands/implement-phase.md` at `term=11` (it carries four criteria, the only one that does) and `commands/_preamble.md` at `term=5` (unchanged — it has a third pre-existing key and no new ones). Thirty commands added exactly 6 frontmatter lines; `implement-phase` added 7. Both are inside the 7-line hard ceiling.
- Step 2: **counts from 3 to 18, not 2.** The technical spec's Error & Rescue Map says "`grep -c '^---$'` must stay at 2 for every command file." That was never true — command *bodies* use `---` as a horizontal rule, and always did. Run it, see it fail, and do not treat it as a finding. Step 1 is the check that actually answers the question. Recorded as Discrepancy 3.
- Step 3: field order is `name`, `description`, `problem`, `outcome`, `exit_criteria`, terminator at line 10.
- Step 4: line numbers ascend 2, 3, 4, 5, 6 — the three new keys sit after the last pre-existing key, never before `name` or `description`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Technical spec § Carrier Analysis → Command frontmatter

**Notes:**

---

### Scenario 3: The reference doc exists, ships to installed projects, and states its own limit

**Source:** Success Criterion 5; technical spec § `.writ/docs/component-contract.md`. `.writ/docs/*.md` fans out through `install.sh`, so this is user documentation for anyone authoring their own commands — not an internal note.

**Preconditions:**
- None.

**Steps:**
1. Run `ls .writ/docs/component-contract.md && wc -l .writ/docs/component-contract.md`.
2. Confirm the fan-out is real rather than asserted: `grep -n '\.writ/docs' scripts/install.sh`.
3. Read the file's six sections: The Three Fields · Where the Contract Lives · Writing `exit_criteria` · `## Completion` and How It Differs · Line Budget · References.
4. Read the **Honest limit** paragraph at line 86 and quote it into your notes.
5. Confirm `commands/new-command.md` points at this doc rather than restating it: `grep -n 'component-contract.md' commands/new-command.md`.

**Expected Result:**
- Step 1: the file exists, **128 lines** — the density of `.writ/docs/model-tiers.md`, not a second spec.
- Step 2: `overlay_scan_flat_dir "$WRIT_SRC/.writ/docs" ".writ/docs" ".writ/docs"` appears twice (preview at ~938, apply at ~1029), plus `for f in .writ/docs/*.md` manifest loops at ~809 and ~991 and a `git add .writ/docs/*.md` at ~1128. The doc reaches installed projects.
- Step 3: both agent carriers are documented, including the explicit warning that "an editor matching `^## Agent Configuration$` alone silently skips the seventh file and reports 6/7 as success."
- Step 4: the paragraph reads, in part: *"`exit_criteria` is only **nominally** machine-checkable. A lint can verify the field exists and is non-empty; it cannot verify the assertion is true."* It goes on to argue the field earns its lines because it forces the author to name a falsifiable condition, and cites ADR-020's 2026-11-11 review trigger. **This sentence is the honest boundary of this whole spec. Scenario 18 is built on it.**
- Step 5: one hit, in the Component-contract note in Step 2.1.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `.writ/docs/component-contract.md`; `scripts/install.sh`

**Notes:**

---

### Scenario 4: `new-command.md` acquired the mandate — and left the Model tier note alone

**Source:** Success Criterion 4; technical spec § `commands/new-command.md` — Exact Edit Set. Two halves: the mandate that ADR-020 wrongly assumed existed must now exist, **and** the ownership boundary with `2026-08-11-retire-dead-prescription` must have held.

**Preconditions:**
- Full git history available.

**Steps:**
1. Run `git diff e23fbdc..b8b96d5 -- commands/new-command.md`.
2. In the generated-command structure table (Step 2.1), count the rows and find the Completion row's position.
3. Read the **Component contract (every generated command)** block and the **Authoring `exit_criteria`** block beneath it.
4. Read the last bullet added to the "Quality bars for the generated command file" list.
5. Confirm the Model tier note is absent from the diff: `git diff e23fbdc..b8b96d5 -- commands/new-command.md | grep -c 'Model tier'`.

**Expected Result:**
- Step 1: **25 insertions, 0 deletions**, in four hunks — the file's own frontmatter (6 lines), the table row, the contract + coaching block, and one quality-bar bullet.
- Step 2: **seven rows**, with `**Completion**` between "Integration with Writ" and "References" — the same placement the 31 command files use. This row is the mandate. It did not exist before this spec; see Scenario 5.
- Step 3: the contract block names the three fields, the fixed append-after-last-key order, the 7-line ceiling, "2–4 criteria entries; three is the expected shape", and links to `.writ/docs/component-contract.md`. The coaching block states the **swap test** and the **restatement test** in one line each, followed by the contrasting pair `✗ "the release completes successfully"` / `✓ "a git tag matching v<VERSION> exists"`.
- Step 4: "Declare `problem:`, `outcome:`, and `exit_criteria:` in the `---` frontmatter, appended after the last existing key in that order, within 7 lines — and carry a `## Completion` section immediately before `## References` that does not contradict them."
- Step 5: **0**. Not one line of Step 2.1's Model tier note or the Step 2.2 checklist bullet appears in the diff. Those lines belong to `2026-08-11-retire-dead-prescription`, which landed first and converted them to frontmatter. Read them in the current file: they now prescribe `model_tier:` in the `---` block. If they still prescribed a prose note, the technical spec's instruction was to escalate, not repair — that path was not needed.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `commands/new-command.md`; ownership ruling 2026-08-11

**Notes:**

---

### Scenario 5: ADR-020's amendment is faithful — the premise is corrected, the decision is not reopened

**Source:** Success Criterion 9; technical spec § ADR-020 Exact Edit Surface. **The failure mode this guards is a re-decision wearing an amendment's clothes.** An ADR whose premise was wrong is easy to over-edit into an ADR that decided something else.

**Preconditions:**
- Full git history available.

**Steps:**
1. Run `git diff e23fbdc..b8b96d5 -- .writ/decision-records/adr-020-component-contract.md` and read every hunk.
2. Confirm placement: `grep -n '^## Amendments\|^## References' .writ/decision-records/adr-020-component-contract.md`.
3. Confirm the measurement row survived byte-for-byte: `grep -n '| Commands with a `## Completion` section | \*\*13 of 32\*\* |' .writ/decision-records/adr-020-component-contract.md`.
4. Confirm the Decision's three numbered carriers are absent from the diff — check the diff's hunk headers against lines 13–29.
5. Run the technical spec's own verification grep and read what it returns:
   `grep -n 'already mandates\|template violation\|it is \*\*unenforced\*\*' .writ/decision-records/adr-020-component-contract.md`
6. Read the `## Amendments` entry's four labelled parts.

**Expected Result:**
- Step 1: **18 insertions, 6 deletions**, in four hunks — the Date line, the post-carriers sentence at line 31, the `### The finding` subsection, and the Consequences → Positive bullet. Plus the inserted `## Amendments` section.
- Step 2: `## Amendments` at **104**, `## References` at **116**. The section is inserted immediately before References, per the ADR-009 convention.
- Step 3: **line 44**, matched exactly. It appears in the diff only as an unchanged context line. `13 of 32` is a verified number and was not "corrected" to this spec's `13 of 31` — both are true against different populations (raw file list vs. commands), and `2026-08-11-governor-instrumentation` `story-3:37` instructs that neither be touched.
- Step 4: no hunk falls inside lines 13–29. Decision items 1 (commands), 2 (agents), and 3 (skills) are byte-for-byte unchanged, as is the 2026-11-11 review trigger.
- Step 5: **two hits, both at lines 108 and 110 — inside the Amendments section, quoting the false claim in order to correct it.** The technical spec's verification block says "expect 0". Zero is not reachable: an amendment that corrects a false phrase must be able to name it. Do not read the 2 as a failure; read the two line numbers and confirm they are both inside `## Amendments`. Recorded as Discrepancy 2.
- Step 6: **Correction:** names the false claim, the measurement that refutes it, and the six structure-table rows. **Rationale:** states the Decision is unaffected and retires the three banned phrases from downstream use. **Measured:** dates it 2026-08-11, credits @AdamSellke's independent re-verification, and *deliberately omits the line number* — explaining that the sole `Completion` occurrence sat at line 202 when first measured and at line 206 by implementation time, after the dependency landed four lines above it, so "the count, not the offset, is the finding." **Originating work:** links Story 1 and names the roadmap as the same story's second target.
- Now read the three corrected inline sites and confirm the false premise is gone from each: line 3 (Date, now `(amended 2026-08-11 — see Amendments)`), line 31 (the post-carriers sentence, which no longer says "**already mandates**"), and the `### The finding: nothing checks the components themselves` subsection — whose tooling-inventory sentence and "guardian measures its own byte count" sentence survive verbatim, moved but not reworded.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `.writ/decision-records/adr-020-component-contract.md`

**Notes:**

---

### Scenario 6: The roadmap edits were line-count neutral — and there is a fourth edit the spec did not authorize

**Source:** Success Criterion 9; technical spec § `.writ/product/roadmap.md`. Line-count neutrality is a hard constraint, not tidiness: a sibling spec cites roadmap lines by number and a shift would silently invalidate the citations.

**Preconditions:**
- Full git history available.

**Steps:**
1. Run:
   ```
   wc -l .writ/product/roadmap.md
   git diff --numstat e23fbdc..b8b96d5 -- .writ/product/roadmap.md
   ```
2. Run `grep -n 'template violation\|19 file\|already mandating\|verified 0/31' .writ/product/roadmap.md; echo "EXIT=$?"`.
3. Run `git diff e23fbdc..b8b96d5 -- .writ/product/roadmap.md` and **count the hunks**.
4. Confirm the sibling's citations still resolve:
   ```
   sed -n '341p;343p' .writ/product/roadmap.md
   git show e23fbdc:.writ/product/roadmap.md | sed -n '341p;343p'
   ```
5. Confirm the verified numbers survived: `grep -c '13 of 32\|2 of 32\|0 of 5\|516,589' .writ/product/roadmap.md`.

**Expected Result:**
- Step 1: `wc -l` prints **424**, unchanged. `--numstat` prints `4	4	.writ/product/roadmap.md` — **equal added and deleted**. Every edit was a one-for-one line replacement; the Revision Log correction was appended to the existing 2026-08-11 row rather than added as a new row, precisely to hold this number.
- Step 2: **no output, `EXIT=1`.** All four banned strings are gone from Phase 10.
- Step 3: **four hunks, not three.** The spec specified three edits and stated "No other roadmap line is touched." A fourth landed at **line 343**, rewriting *"correct the false `no frontmatter … (verified 0/31 files)` claim"* to *"correct the stale no-frontmatter claim … (32/32 commands carry it)"*. This is a genuine scope addition — see Discrepancy 1 before deciding how to mark this scenario. It is line-count neutral and it closes a real open item, but it was not authorized by the contract and it invalidates a scenario in a sibling spec's UAT plan.
- Step 4: line 341 is **byte-identical** before and after (the Progressive disclosure bullet). Line 343 is the Retire dead prescription bullet in both, and still carries the `44 entries → 31 commands` manifest figure the sibling cites. Both citations resolve.
- Step 5: **4 or more** — `13 of 32`, `2 of 32`, `0 of 5`, and `516,589` all survive. No verified number was disturbed while a false clause next to it was replaced.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `.writ/product/roadmap.md`; Discrepancy 1

**Notes:**

---

## Story 7: Agent Config Contracts Across Both Carriers

### Scenario 7: 7/7 agents — the seventh-file trap did not fire

**Source:** Success Criterion 2; technical spec § Agent config blocks — two carriers. **`agents/visual-qa-agent.md` is the whole scenario.** An editor matching `^## Agent Configuration$` alone reaches six files, reports success, and leaves the seventh silently unconverted. Counting to six and stopping is the documented failure.

**Preconditions:**
- None.

**Steps:**
1. Run:
   ```
   ls agents/*.md | wc -l
   for k in problem outcome exit_criteria; do printf '%s: ' "$k"; grep -l "^$k:" agents/*.md | wc -l; done
   ```
2. Name the files rather than trusting the count: `grep -l '^problem:' agents/*.md`.
3. Read `agents/visual-qa-agent.md` lines 18–37 in full.
4. Confirm the keys are **inside** the fence, not after it, for the seventh file specifically — check that the closing ``` sits below `exit_criteria`.
5. Run `git diff --numstat e23fbdc..b8b96d5 -- agents/`.

**Expected Result:**
- Step 1: **7** files; **7** for each of the three keys.
- Step 2: all seven named, `visual-qa-agent.md` among them. Read the list — do not read the number.
- Step 3: the `## Agent Specification` block still opens with ` ```yaml `, still carries `name`, `description`, `tools`, `disallowedTools`, `model`, `model_tier`, `readonly`, `maxTurns` in their original order, and then `problem:`, `outcome:`, `exit_criteria:` appended after `maxTurns`. Its first criterion is worth reading on its own: *"activation was warranted: the story carries a Visual References section or the spec carries a non-empty `mockups/` directory — a skipped gate satisfies nothing here."* That is an assertion about an *optional* gate, and it could not have been templated from any other agent.
- Step 4: the fence closes after the last criterion. No second fence, no new heading.
- Step 5: **all seven files show `6	0`** — six added lines each (1 + 1 + 1 + 3 criteria), zero deleted, well inside the 7-line ceiling. Total 42 lines against a 49-line agent ceiling.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 7 — Files: all seven under `agents/`

**Notes:**

---

### Scenario 8: Neither carrier was normalized into the other

**Source:** Business Rule 6; Success Criterion 2. Carrier normalization is a separate decision and is explicitly out of scope. The temptation to "tidy" six-versus-one asymmetry while already editing all seven files is the thing being tested.

**Preconditions:**
- None.

**Steps:**
1. Run `grep -n '^## Agent \(Configuration\|Specification\)$' agents/*.md`.
2. Run `grep -n '^```yaml$' agents/*.md`.
3. Run `grep -n '^## Purpose$\|^## Role$' agents/*.md`.
4. Confirm the six unlabeled blocks are still not-quite-YAML: `grep -n 'model: default (inherits from parent)' agents/*.md | wc -l`.

**Expected Result:**
- Step 1: **six `## Agent Configuration` at line 7** (`architecture-check-agent`, `coding-agent`, `documentation-agent`, `review-agent`, `testing-agent`, `user-story-generator`) and **one `## Agent Specification` at line 18** (`visual-qa-agent`). Both the heading text and the heading *position* are unchanged — the seventh file's block still sits after `## Role` and `## Activation`, not after `## Purpose`.
- Step 2: exactly one hit, in `visual-qa-agent.md`. The other six fences are still unlabeled.
- Step 3: six `## Purpose`, one `## Role`. The prose heading asymmetry survives too — the contract lives in the fenced block, not the heading, and renaming was explicitly forbidden.
- Step 4: **6**. The six plain-fence blocks are still not strictly valid YAML. Appending a block sequence neither improved nor worsened that, which is exactly what the spec said would happen.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 7; Business Rule 6

**Notes:**

---

## Stories 2–5: The Thirty Remaining Command Contracts

> These four stories are where the spec either worked or produced 31 files of well-formed filler. Presence is already proven by Scenario 1. The next three scenarios ask the only question that matters: **does any of it say anything?**

### Scenario 9: The swap test — run it yourself, on these four pairs

**Source:** Business Rule 1; Success Criterion 6. **This is the central scenario of the plan.** The spec's entire justification is that these fields are derived assertions rather than boilerplate. Nothing in the repository checks that. A human reading four pairs is the check. Budget ten minutes.

**How to run a pair:** open command A's frontmatter, take the named criterion, and read it as if it sat in command B's frontmatter. It passes if it is **false or nonsensical** there. It fails if it is merely *vaguer* — plausible-in-both is the failure state.

**Preconditions:**
- None. Four files open side by side.

**Steps:**
1. **Pair A — direct contradiction.** Take `commands/revert.md`'s second criterion:
   > `"each affected story reads Status: Not Started with all task and acceptance-criteria boxes cleared, and its ## What Was Built record is retained under a Reverted banner rather than deleted"`

   Read it against `commands/implement-story.md`. Then read `implement-story`'s own first criterion.
2. **Pair B — nonsensical.** Take `commands/release.md`'s third criterion:
   > `"an annotated git tag v<VERSION> exists on the release commit, unless --no-tag or the bump-only choice was taken"`

   Read it against `commands/review.md`. Then read `review`'s own criteria.
3. **Pair C — the near-neighbour, and the one worth your attention.** Take `commands/research.md`'s second criterion:
   > `"every finding carries a source URL rather than an unattributed assertion"`

   Read it against `commands/security-audit.md` — a command that also produces a dated document full of things called findings. Then read `security-audit`'s own second criterion.
4. **Pair D — inverted polarity.** Take `commands/prototype.md`'s first criterion:
   > `"no spec folder, story file, or task list was created under .writ/specs/ for this change"`

   Read it against `commands/create-spec.md`. Then read `create-spec`'s `outcome:`.
5. Now pick any two entries yourself, from commands you have not read, and swap them against neighbours in the same batch (the four batches are in `spec.md` § Command batching). Same-batch neighbours are the hard case — cross-batch swaps are easy.

**Expected Result:**
- **Pair A: contradictory.** `/implement-story`'s own first criterion asserts *"the story file header reads Status: Completed."* `/revert`'s criterion asserts the same header reads `Not Started`. The two commands are inverses and their criteria say so. Pasting either into the other produces a file that asserts both states at once.
- **Pair B: nonsensical.** `/review` writes `.writ/state/review-<branch>.md` and touches no version file, no changelog, and no tag. Its own three criteria name a Failure Modes Registry, a Recommendation with three permitted values, and per-entry code locations. There is no VERSION in `/review` for `v<VERSION>` to refer to.
- **Pair C: plausible for about four seconds, then false.** Both commands produce dated documents with findings, so the sentence parses. But `/security-audit`'s own second criterion requires each finding carry *"an ID, a severity, a file-and-line location, and a remediation step"* — a source URL is the wrong evidence type for a finding about this codebase, and demanding one would make the command's real output non-compliant. **This is the pair that shows the fields were derived rather than distinguished.** A boilerplate author would have written "every finding is documented" for both and it would have been true in both.
- **Pair D: inverted.** `/create-spec`'s `outcome:` is *"A new `.writ/specs/<date>-<name>/` package exists — spec, spec-lite, per-story files, and sub-specs."* `/prototype`'s criterion asserts the exact absence of that package. It is `/prototype`'s whole reason to exist and it is false in `/create-spec` by construction.
- **Step 5: your two swaps behave the same way.** If you find one that stays plausible in a same-batch neighbour, that entry is the finding — record it in Notes with both command names. One soft entry does not fail the spec; a pattern of them does.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Business Rule 1; Success Criterion 6; `.writ/docs/component-contract.md` § "Writing `exit_criteria`"

**Notes:**

---

### Scenario 10: The restatement test — nothing is a paraphrase of `description:`

**Source:** Business Rule 2. The swap test catches criteria that fit everywhere. This catches criteria that fit *this* command and still say nothing, because they only repeat what `description:` already said.

**How to run it:** read a command's `description:`, cover the criterion, and try to re-derive it from the description alone. If you can, the criterion carries no information.

**Preconditions:**
- None.

**Steps:**
1. `commands/knowledge.md` — description: *"Capture a small durable fact … in under 2 minutes."* Now read its second criterion.
2. `commands/verify-spec.md` — description: *"Metadata linter for a spec … Auto-fixes what it safely can."* Now read its third criterion.
3. `commands/create-issue.md` — description: *"Fast-capture a bug, feature, or improvement mid-development in under 2 minutes. Speed over completeness."* Now read its third criterion.
4. Run the banned-construction sweep, scoped to frontmatter only:
   ```
   for f in commands/*.md agents/*.md; do
     awk 'NR<=20' "$f" | grep -n -F -e "completes successfully" -e "the report is generated" \
       -e "the user is informed" -e "the output is correct" | sed "s|^|$f:|"
   done
   ```
5. **The one to check hardest.** Read `commands/research.md`'s first criterion against its own description and decide whether it survives.

**Expected Result:**
- Step 1: `"--list and --read change no file on disk"`. The description never mentions the flags, let alone that two of them are read-only. Not re-derivable.
- Step 2: `"any regenerated spec-lite.md is a whole-file replacement carrying its regeneration date marker, and spec.md is byte-identical to its pre-run state"`. "Metadata linter … auto-fixes what it safely can" does not tell you that `spec.md` is off-limits. That is the criterion's whole content.
- Step 3: `"at most three clarifying questions were asked and at most three files are referenced"`. "Under 2 minutes" implies speed; it does not yield the numbers 3 and 3. Not re-derivable.
- Step 4: **no output.** The only occurrences of "completes successfully" anywhere under `commands/` are `new-command.md:178` (the `✗` example in the authoring coaching — it is *supposed* to be there) and `release.md:234` (ordinary prose in a phase-ordering note). Neither is an `exit_criteria` entry, and the `awk NR<=20` window excludes both.
- Step 5: `"a file matching .writ/research/<YYYY-MM-DD>-<topic>-research.md exists"` against a description that says the command produces "an evidence-backed research document." **This is the closest call in the set.** It survives on the path shape and date convention, which the description does not carry — but it is the one entry where a reviewer could reasonably argue the other way. Record your own judgment in Notes; do not fail the scenario on it alone. Its two sibling criteria (source URL per finding, exactly one primary recommendation with named alternatives) are clearly derived.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Business Rule 2; `.writ/docs/component-contract.md` § restatement test

**Notes:**

---

### Scenario 11: Every criterion names something a script could check

**Source:** Business Rule 3. The anti-pattern this catches is a criterion that names a path but asserts nothing about it — `".writ/state/review-<branch>.md"` is a path; the same string plus "exists and contains a Recommendation section" is a criterion.

**Preconditions:**
- None.

**Steps:**
1. Dump every criterion in the repository and read them:
   ```
   for f in commands/*.md; do
     t=$(awk 'NR>1 && /^---$/{print NR; exit}' "$f")
     sed -n "1,${t}p" "$f" | grep '^  - ' | sed "s|^|$(basename $f) |"
   done
   ```
2. For each, identify which of Business Rule 3's five checkable kinds it names: a **path**, a **field value**, a **count or comparison**, a **process outcome**, or a **command-observable state**.
3. Spot-check the three shapes that are easiest to fake:
   - `commands/create-spec.md` third criterion — a bare numeric bound.
   - `commands/implement-spec.md` first criterion — a named script and its expected return.
   - `commands/migrate.md` third criterion — a grep and its expected result.
4. Confirm criteria are written as present-tense assertions about post-run state, not as instructions.

**Expected Result:**
- Step 1 prints **94 entries** — 30 commands × 3 plus `implement-phase`'s 4.
- Step 2: every entry names at least one of the five. Angle-bracket placeholders (`<VERSION>`, `<slug>`, `<branch>`) appear throughout and are expected — the assertion must be *shaped* like something checkable, since nothing in this spec executes it.
- Step 3: `"spec-lite.md is under 100 lines"` — a comparison, and one `eval.sh check_length` already enforces independently. `"scripts/story-deps.py validate returned status ok for the full story graph before the first story ran"` — names the script, the subcommand, and the expected return. `"a recursive grep for .code-captain across .writ/ and README.md, CLAUDE.md, CONTRIBUTING.md returns zero hits"` — names the command and its expected output.
- Step 4: no entry begins with an imperative verb. They read as things that are true afterward, not as steps to perform.
- No entry is a bare path with nothing asserted about it.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Business Rule 3; technical spec § "Anti-pattern to reject in review"

**Notes:**

---

### Scenario 12: Entry counts sit inside the per-file budget

**Source:** Business Rule 4; Success Criterion 7 (per-file half).

**Preconditions:**
- None.

**Steps:**
1. Count entries per command:
   ```
   for f in commands/*.md; do
     t=$(awk 'NR>1 && /^---$/{print NR; exit}' "$f"); [ -z "$t" ] && continue
     echo "$(basename $f) $(sed -n "1,${t}p" "$f" | grep -c '^  - ')"
   done | sort -k2 -n | uniq -c -f1
   ```
2. Count entries per agent, scoped inside the fence:
   ```
   for f in agents/*.md; do
     echo "$(basename $f) $(awk '/^## Agent (Configuration|Specification)$/{f=1} f&&/^```/{c++} f&&c==1{print} c==2{exit}' "$f" | grep -c '^  - ')"
   done
   ```
3. Run `git diff --numstat e23fbdc..b8b96d5 -- commands/ | sort -n | uniq -c -f0 | head`.

**Expected Result:**
- Step 1: **thirty commands at 3 entries, one at 4** (`implement-phase.md`), `_preamble.md` at 0. The floor is 2 and the ceiling is 4; nothing is at either extreme except `implement-phase`, which is the command that resolves specs, tracks quarantine branches, checks roadmap criteria, and emits a terminal status — four distinct terminal facts, and the one place the fourth slot earns itself.
- Step 2: **3 for all seven agents.**
- Step 3: the per-file added-line counts are **6** (frontmatter only), **7** (`implement-phase`), **14** (frontmatter + a new `## Completion`), and **25** (`new-command.md`, which also carries the authoring coaching). No command exceeds 7 frontmatter lines.
- Nothing sits at the ceiling on every file. Uniform maximums would be evidence the swap test was not applied; uniform *middles* — three entries almost everywhere — is the expected shape the spec named in advance.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Business Rule 4; technical spec § Line Budget Arithmetic

**Notes:**

---

## Story 6: The Eighteen `## Completion` Sections

### Scenario 13: Eighteen written, placed correctly, one per file

**Source:** Success Criterion 3; technical spec § Placement Rules.

**Preconditions:**
- None.

**Steps:**
1. Confirm placement is below the file's last `## References` heading — that is, the section precedes it:
   ```
   for f in commands/*.md; do
     case "$f" in */_preamble.md) continue;; esac
     c=$(grep -n '^## Completion' "$f" | head -1 | cut -d: -f1)
     r=$(grep -n '^## References' "$f" | tail -1 | cut -d: -f1)
     [ -n "$c" ] && [ "$c" -lt "$r" ] || echo "MISPLACED $f"
   done; echo "checked"
   ```
   (Drop the `case` line and `_preamble.md` reports MISPLACED — correctly, it has no section. Scenario 1 already covers that.)
2. Measure the new sections' length:
   ```
   for f in assess-spec implement-spec implement-story initialize migrate prototype refactor \
     refresh-command reinstall-writ release retro revert security-audit ship status \
     uninstall-writ update-writ verify-spec; do
     echo "$f $(awk '/^## Completion/{f=1} f{c++} f&&/^## References/{print c-1; exit}' commands/$f.md)"
   done
   ```
3. Read three sections in full: `commands/status.md`, `commands/ship.md`, `commands/retro.md`.
4. Confirm the highest-value line was actually written, and find the exception:
   ```
   grep -c '\*\*Terminal constraint:\*\*' commands/*.md | grep -v ':0' | wc -l
   grep -c '\*\*Terminal constraint:\*\*' commands/*.md | grep ':0'
   ```

**Expected Result:**
- Step 1: only `checked` — no `MISPLACED` line. Every section sits above the file's final `## References`, and above the `---` rule that precedes it where one exists.
- Step 2: **10 for all eighteen**, well inside the 14-line hard ceiling and below the 15–16 median of the thirteen incumbents. Combined with the 6 frontmatter lines, this is the `14	0` per-file numstat from Scenario 12.
- Step 3: each carries the three-part shape — a one-sentence success condition naming the artifact, one sentence declaring a zero/failure result valid rather than an error, and a **Terminal constraint** line. `/status`: *"No active spec is a valid outcome. The report says so plainly rather than searching harder for one."* `/ship`: *"Failing tests or unresolved drift do not stop the run — they make the pull request a draft. That is the honest outcome, not a degraded one."* `/retro`: *"A first run has no prior snapshot to compare against. Metrics marked as having no baseline are correct output, not missing data."*
- Step 4: **30**, and the two zeros are `commands/_preamble.md` (not a command, no section) and `commands/review.md`. So **30 of 31 commands** carry it; the single exception is an *incumbent* section that pre-dates the contract, not one of the eighteen written by Story 6 — all eighteen have it. Business Rule 10 forbade rewriting substance, so `review.md`'s existing section was left as it stood. This is the line the spec called "the highest-value line and the least likely to be written unprompted"; it is the only part of a `## Completion` section that constrains an agent's *next* action rather than describing the current one, and it is worth reading closely wherever it appears.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 6 — the eighteen files listed in `spec.md` § The 18 commands missing `## Completion`

**Notes:**

---

### Scenario 14: `## Completion` and `exit_criteria` agree

**Source:** Business Rule 7. Two declarations of the same terminal state in one file is a contradiction waiting to happen. Every `exit_criteria` entry must be traceable to something the section also asserts.

**Preconditions:**
- None.

**Steps:**
1. For `commands/status.md`, read the three `exit_criteria` entries and the `## Completion` section, and match each entry to a sentence in the section.
2. Do the same for `commands/ship.md`.
3. Do the same for `commands/assess-spec.md`.
4. Now check a command whose section **pre-existed** the contract, where the criteria were derived *from* the section rather than written alongside it: `commands/review.md`.

**Expected Result:**
- Step 1: `.writ/context.md` rewritten with Active Spec + Artifact Map + timestamp → first sentence. Two to four suggested next actions → same sentence. Read-without-writing and no git-mutating command → the Terminal constraint line. Three for three.
- Step 2: origin upstream, default-branch ancestry, and the four PR body sections all appear in the first sentence; the draft-on-failure criterion maps to the second.
- Step 3: six checks with recorded results and exactly one of three ratings → first sentence. The "Ready to implement is a finding, not a wasted run" sentence covers the zero-flag case. The per-flag decomposition criterion is the one the section does not restate — that is acceptable in this direction: the section may be leaner than the criteria, it may not contradict them.
- Step 4: `/review`'s criteria name `.writ/state/review-<branch>.md`, a Failure Modes Registry, a Recommendation with exactly three permitted values, and per-entry code locations. Its incumbent section states the same terminal condition. Nothing in the file asserts two different completion states.
- **No contradiction in any of the four.** If you find one, the fix under Business Rule 7 is to correct the section — the frontmatter carries the machine-checkable assertion.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Business Rule 7; `.writ/docs/component-contract.md` § "`## Completion` and How It Differs"

**Notes:**

---

## Whole-Spec: Budget, Regression, and the Two Honest Limits

### Scenario 15: The line budget held — 392 against a 518 ceiling

**Source:** Business Rule 4; Success Criterion 7. **This is the number the spec asked a human to read rather than a check to enforce.** Reproduce it rather than taking the story's evidence on trust.

**Preconditions:**
- Full git history available.

**Steps:**
1. Run the exact command:
   ```
   git diff --shortstat e23fbdc..b8b96d5 -- commands/ agents/
   ```
2. Split it by surface:
   ```
   git diff --shortstat e23fbdc..b8b96d5 -- commands/
   git diff --shortstat e23fbdc..b8b96d5 -- agents/
   ```
3. Reconstruct the ceiling from `spec.md` Business Rule 4: 31×7 + 7×7 + 18×14.
4. Check the deletion count.

**Expected Result:**
- Step 1: **`38 files changed, 392 insertions(+)`** — no deletions. Against the **518** aggregate ceiling, that is 126 lines of headroom, 76% of budget spent.
- Step 2: `31 files changed, 350 insertions(+)` for `commands/`; `7 files changed, 42 insertions(+)` for `agents/`. The agent surface used 42 of its 49-line ceiling; commands used 350 against 217 + 252 = 469.
- Step 3: 217 + 49 + 252 = **518**. The arithmetic is reconstructable from the spec without reading the diff, which is the test the spec set for itself.
- Step 4: **zero deletions across all 38 files.** Every line is additive. Business Rule 10 said substance would not be rewritten; a zero in the deletions column is what that looks like.
- Note that `commands/new-command.md`'s 25 lines include 19 lines of authoring guidance that the 518 arithmetic never budgeted for — the ceiling covers 31×7 frontmatter + 7×7 agent + 18×14 sections and nothing else. It comes in under the ceiling regardless. Recorded as Discrepancy 4.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Business Rule 4; Success Criterion 7; commits `3ac178a`, `e691de6`, `79dcc60`

**Notes:**

---

### Scenario 16: The gates are green — and they emitted four warnings that are not

**Source:** Success Criterion 8; Business Rule 9.

**Preconditions:**
- `bash`, `python3`, and `git` available. `eval.sh` takes several minutes — it builds sandbox fixtures.

**Steps:**
1. Run `bash scripts/eval.sh` and open the report path it prints.
2. Read the report's `## Summary`.
3. Read the report's `## leanness` section — specifically the `Notes (non-blocking)` block.
4. Run `bash scripts/check-agent-parity.sh; echo "EXIT=$?"`.
5. Confirm this spec added no check of its own: `git diff --stat e23fbdc..b8b96d5 -- scripts/`.

**Expected Result:**
- Step 2: **`Findings: 0`, `Run errors: 0`.** `prime-directive-sync`, `artifact-integrity` (19/19), and `recommended-spec-impl` (23/23) all pass.
- Step 3: **four non-blocking WARNINGs attributable to this spec** — `commands` lines `10974 → 11364 (+390)`, `commands` chars `514594 → 552568 (+37974)`, `agents` lines `1768 → 1810 (+42)`, `agents` chars `67012 → 72473 (+5461)`, each reading "with no justification." They do not fail the run; `eval.sh` exits 0. **Read them anyway** — Scenario 17 is about what they mean. (The two `scripts` warnings are not this spec's; nothing under `scripts/` was touched.)
- Step 4: `parity OK — agents/, claude-code/agents/, and codex/agents/ aligned (subject to documented exclusions)`, `EXIT=0`. `check-agent-parity.sh` checks file existence, not field parity, so the `claude-code/agents/` and `codex/agents/` mirrors do **not** carry the three fields and do not need to — extending the contract to them is a later decision.
- Step 5: **empty**. No line of `scripts/eval.sh`, `scripts/eval-leanness.py`, or any `eval-*.py` changed. Business Rule 9 held: this spec produces the compliant surface, `2026-08-11-governor-instrumentation` asserts it.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Success Criterion 8; Business Rule 9

**Notes:**

---

### Scenario 17: The command surface got bigger, and Phase 10 says it must get smaller

**Source:** `.writ/product/roadmap.md` Phase 10 Success Criteria; `spec.md` § "Why this is not another token tax". **State this plainly or the plan is dishonest.** This spec was justified on the argument that a later spec removes an order of magnitude more than it adds. That later spec does not exist yet.

**Preconditions:**
- Full git history available.

**Steps:**
1. Measure the current surface:
   ```
   cat commands/*.md | wc -c; cat commands/*.md | wc -l
   ```
2. Measure the base:
   ```
   for f in $(git ls-tree -r --name-only e23fbdc commands/); do git show e23fbdc:$f; done | wc -c
   for f in $(git ls-tree -r --name-only e23fbdc commands/); do git show e23fbdc:$f; done | wc -l
   ```
3. Read the roadmap's phase-start figure: `grep -n '516,589' .writ/product/roadmap.md`.
4. Read Phase 10's Success Criteria at `.writ/product/roadmap.md:325-336` and find the three that bear on surface size — including line 334.
5. Run `ls .writ/specs/ | grep -i 'progressive\|disclosure'; echo "EXIT=$?"` and check the roadmap's Progressive disclosure checkbox at line 341.

**Expected Result:**
- Step 1: **552,568 chars, 11,364 lines.**
- Step 2: **517,444 chars, 11,014 lines** at the base commit. This spec added **+35,124 chars (+6.8%)** and **+350 lines (+3.2%)** to `commands/`, plus 42 lines and ~5,461 chars to `agents/`.
- Step 3: the roadmap's phase-start figure is **516,589** chars, measured before `2026-08-11-retire-dead-prescription` and `2026-08-11-autonomy-gate-classes` landed. Against *that* baseline the growth is **+35,979 chars, +7.0%**. Both baselines are real; the difference is which sibling specs had already landed. `eval-leanness.py` uses a third (`514,594`, from `.writ/leanness-baseline.json`). Cite which one you mean.
- Step 4: three criteria bear on size. `eval.sh` must exit 0 with **0 findings and 0 unjustified growth warnings** — this spec satisfies the findings half and **violates the warnings half**, having produced four (Scenario 16, step 3). No command file may exceed **400 lines** without an exemption — not yet enforced, since `check_length`'s command limit is still 2000. And line 334: **"`per_surface.commands.chars` drops materially from 516,589."** It did not drop. It rose to 552,568.
- Step 5: **no progressive-disclosure spec exists**, and the roadmap's Progressive disclosure feature is `- [ ]`, `Effort: L` — the largest unbuilt item in the phase.
- **The honest reading.** This spec makes Writ heavier. That is by design and the spec says so: it is "only defensible because ADR-021 removes an order of magnitude more than this adds," and landing it alone "would make Writ heavier while calling it streamlined — the explicit failure mode identified at plan time." As of today it *has* landed alone. Phase 10 is not falsified by this — it is unfinished. But a reviewer signing this UAT is signing off on a surface that grew 7% against a phase whose stated purpose is shrinking it, and the reversal is owed entirely by an unbuilt `Effort: L` item. Do not mark this scenario Pass on the basis that the growth was expected. Mark it Pass if the numbers above reproduce and the dependency is understood; record in Notes that the debt is outstanding.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `spec.md` § "Why this is not another token tax"; ADR-021; `.writ/product/roadmap.md` Phase 10

**Notes:**

---

### Scenario 18: Declared is not enforced — nothing checks a single one of these 94 assertions

**Source:** `.writ/docs/component-contract.md` § "Honest limit"; `spec.md` § Technical Concerns; Business Rule 9. **This is the scenario a reviewer should personally confirm before signing.** A passing UAT on scenarios 1–14 is easy to misread as "the exit criteria are verified." They are not verified. They are *written down*.

**Preconditions:**
- None. Reading and grepping only.

**Steps:**
1. Re-read the Honest limit paragraph at `.writ/docs/component-contract.md:86` and quote it in your notes.
2. Look for any check that reads the field:
   ```
   grep -rn 'exit_criteria' scripts/ ; echo "EXIT=$?"
   ```
3. Look for one that reads the section: `grep -rn "'## Completion'\|\"## Completion\"\|## Completion" scripts/ ; echo "EXIT=$?"`.
4. Run `ls .writ/specs/2026-08-11-governor-instrumentation/` and read its `spec.md` § Contract.
5. Check whether that spec has been built:
   ```
   grep -n 'Status' .writ/specs/2026-08-11-governor-instrumentation/spec.md | head -3
   grep -c 'Complete' .writ/specs/2026-08-11-governor-instrumentation/user-stories/README.md
   ```
6. Now pick any command and falsify its criteria **on paper**: read `commands/knowledge.md`'s three entries and ask what in this repository would notice if all three were untrue.

**Expected Result:**
- Step 1: *"`exit_criteria` is only **nominally** machine-checkable. A lint can verify the field exists and is non-empty; it cannot verify the assertion is true."* The doc argues the field still earns its lines because it forces the author to name a falsifiable condition — and cites ADR-020's **2026-11-11 review trigger**, which exists precisely because that argument might turn out to be insufficient.
- Step 2: **exactly one hit, and it is not a check** — `scripts/phase-state.py:47` defines `CHALLENGE_TRIGGERS = {"scope_degradation", "exit_criteria_degradation"}`, a phase-state trigger *name* that predates this spec and refers to a roadmap phase's exit criteria, not a command's frontmatter field. Read the line and confirm it. Nothing reads the field.
- Step 3: **no output, `EXIT=1`.** Nothing under `scripts/` reads `## Completion` either. There is no presence check, no emptiness check, and certainly no truth check. Business Rule 9 forbade adding one in this spec, deliberately.
- Step 4: `2026-08-11-governor-instrumentation` owns enforcement and depends on this spec. Its Story 3 is the `## Completion` presence check.
- Step 5: `> **Status:** Not Started`, and **zero** completed stories. Enforcement is a future spec's deliverable and no part of it exists.
- Step 6: **nothing.** If `/knowledge` stopped writing to `.writ/knowledge/`, if `--list` started mutating files, if `--consolidate` wrote `superseded_by` in only one direction — every check in this repository would still pass, and the frontmatter would still declare the opposite. The same is true of all 94 entries and all 31 sections.
- **What this scenario is asserting, exactly.** The gap between *declared* and *enforced* is total today. This spec's deliverable is a surface that *can* be checked; nothing checks it. That is not a defect — it is the documented design, sequenced deliberately so the surface is compliant before a blocking check is switched on. But two things follow, and both should be written into the sign-off: (a) the value delivered so far is entirely **authorial** — the discipline of naming a falsifiable condition, verified only by Scenarios 9–11 and only by a human; and (b) if `2026-08-11-governor-instrumentation` slips, the fields decay silently, because a field nothing reads cannot rot loudly. ADR-020's 2026-11-11 trigger is the only thing scheduled to notice.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `.writ/docs/component-contract.md:86`; ADR-020 Consequences and its 2026-11-11 review trigger; `2026-08-11-governor-instrumentation`

**Notes:**

---

## Whole-Spec Gate

Run once, after all eighteen scenarios:

```
bash scripts/eval.sh                 # → Findings: 0, Run errors: 0 (plus 4 non-blocking growth warnings)
bash scripts/check-agent-parity.sh   # → parity OK, exit 0
python3 scripts/spec-deps.py validate --specs-dir .writ/specs
git status --porcelain               # → empty (no scenario should have dirtied the tree)
```

Measured on this branch: `Findings: 0`, `Run errors: 0`, parity OK, clean tree. The four leanness warnings are real and are the subject of Scenario 17 — they are reported here rather than filtered out.

---

## Discrepancies Worth Recording

These are not scenario failures. In three cases the implementer corrected a spec instruction that could not be followed as written. They are recorded so a tester sees them stated rather than discovering them mid-run.

1. **The roadmap got a fourth edit the spec forbade, and it silently invalidates a sibling spec's UAT plan.** `spec.md` specifies three roadmap edits and states "No other roadmap line is touched." Four landed — the fourth rewrote line 343's *"correct the false `no frontmatter … (verified 0/31 files)` claim"* into *"correct the stale no-frontmatter claim … (32/32 commands carry it)."* Every constraint that mattered held: `wc -l` is still 424, `--numstat` is 4/4, and lines 341 and 343 still resolve for `2026-08-11-retire-dead-prescription`. And the edit closes a genuine open item — that sibling's UAT plan filed exactly this line as its **Discrepancy 1**, "the line is unowned," noting no spec claimed it. But two things follow. First, this spec claimed it without saying so, which is the pattern its own Business Rule 10 exists to prevent. Second, **`.writ/specs/2026-08-11-retire-dead-prescription/uat-plan.md` Scenario 3, step 4 now fails as written** — it instructs the tester to expect "one hit — line 343" and to treat that as a genuine open item. It is zero hits. That plan's Scenario 3 and Discrepancy 1 both need updating; neither is this spec's to edit.

2. **ADR-020's prescribed verification asks for a count that cannot be achieved.** The technical spec's verification block runs `grep -c 'already mandates|template violation|it is **unenforced**'` against ADR-020 and says "expect 0." The actual count is **2**, both inside the `## Amendments` section, where the amendment quotes the false phrases in order to name and retire them. An amendment that corrects a claim must be able to state the claim. The check as written would have forced either a vaguer amendment or a failing verification. Scenario 5 replaces it with the check that answers the real question: confirm both hits are inside `## Amendments`.

3. **The frontmatter-integrity check in the Error & Rescue Map was never valid.** It says `grep -c '^---$'` "must stay at 2 for every command file." Real counts run from 3 to 18, because command bodies use `---` as a horizontal rule and always have. Anyone running it as a gate would report 31 corrupted files. Scenario 2 substitutes an awk that finds the *first* `---` after line 1, which is the terminator, and confirms it sits at line 10 (11 for `implement-phase`).

4. **The 518-line ceiling does not account for `new-command.md`'s authoring guidance.** The arithmetic is 31×7 + 7×7 + 18×14, all of it frontmatter and sections. `new-command.md` added 25 lines, 19 of which are the structure-table row, the contract block, and the swap/restatement coaching — real deliverables of Story 1 that the budget never named. Measured total is 392 against 518, so nothing was hidden by the omission. Worth stating because the budget is the artifact that survives this spec, and the next person to reuse it should know it covers contract lines only.

5. **The "authoritative, paste it" text was improved rather than pasted, in two places.** `spec.md` says its before/after blocks are authoritative and "the implementer pastes it, not a paraphrase of it." Two deviations: (a) the roadmap Revision Log sentence dropped the phrase `"template violation"` that the authoritative text contained — necessary, because `spec.md` line 54 bans that phrase from downstream references and Success Criterion 9 requires the roadmap assert no template violation anywhere in Phase 10. The prescribed text contradicted the prescribed check. (b) The ADR Amendment's **Measured:** line gained a paragraph explaining that the line number moved from 202 to 206 between spec authoring and implementation, and that "the count, not the offset, is the finding." Both changes are better than what they replaced. Both are still departures from an instruction that said not to depart.

6. **Three different `commands/` baselines are in circulation and they disagree.** The roadmap says 516,589 chars / 10,996 lines (phase start). `.writ/leanness-baseline.json` says 514,594 / 10,974. The spec's base commit `e23fbdc` measures 517,444 / 11,014. All three are correct against different points in the phase; none is wrong. Any future claim about surface growth needs to name which one it is measured against, or it is unfalsifiable. Scenario 17 gives the figure against all three.

7. **`implement-phase` is the only command with four `exit_criteria`, and this is fine.** Business Rule 4 permits 2–4 and calls three "the expected shape." Thirty commands took three; one took four. Flagged only because a uniform distribution across 31 files would be evidence of templating — a single justified outlier is the opposite signal, and the four facts it asserts (per-spec terminal state, per-spec UAT plan, per-criterion roadmap evidence, one of three report verdicts) are genuinely distinct.

---

## Sign-Off

| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | [ ] Pass [ ] Fail |
| Reviewer | | | [ ] Pass [ ] Fail |

**Overall UAT:** [ ] Pass  [ ] Fail

**Notes:**

# Story 2: Move Documentation Out — Five Base Sections Relocated to .writ/docs/ With Ledger Rows and a Measured Byte Count

> **Status:** Completed ✅ (2026-09-07)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer pruning the shared base
**I want to** move the five documentation-class sections out of `system-instructions.md` into `.writ/docs/`, each behind at most one pointer line, one commit per section with its ledger rows
**So that** the base shrinks toward the 10,000-byte cap without losing any content, and Story 3 starts its cut from a measured, recorded byte count

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given the base at the start of Story 2 (`## Model Tiers` + `### entry_level`, `### required_skills: frontmatter convention`, `### Skill authoring`, `## Startup Update Awareness`, and the tutorial portion of `### Recommendation Semantics` all present in `system-instructions.md`), when all five move commits have landed, then none of those five sections' body text remains in `system-instructions.md` or `commands/_preamble.md`, each is present in a `.writ/docs/` file (new or merged into an existing doc already covering the topic), and each leaves behind at most one pointer line of the form `See .writ/docs/<file> for <topic>.` `[AC-2.1]`
- [x] Given each of the five move commits in turn, when `python3 scripts/prune-ledger.py check --repo .` runs against that commit, then it exits 0, every removed line from that commit has a ledger row in `.writ/decision-records/pruned-instructions-ledger.md` dated that commit's date with class `moved` and a reason naming the destination `.writ/docs/` path, and the ledger row lands in the same commit as the removal `[AC-2.2]`
- [x] Given the base after all five sections have moved, when `bash scripts/eval.sh` runs, then `check_referenced_paths` resolves every new `.writ/docs/` pointer link and `check_prime_directive_sync` reports `cursor/writ.mdc` still byte-identical to `system-instructions.md`'s Prime Directive block `[AC-2.3]`
- [x] Given `python3 scripts/prune-ledger.py measure --repo .` run after the fifth commit, when its byte total is compared to the pre-Story-2 measurement taken in task 2.1, then the post-move total is recorded in Story 2's What Was Built and in a `{date} stage-2: ...` decision-log line, and it is at most 16,000 bytes `[AC-2.4]`
- [x] Given the pinned Stage 1 closeout commit `cf84742`, when every line still present in `system-instructions.md` and `commands/_preamble.md` after Story 2 is diffed against that commit, then the diff of kept lines is empty — no kept line was reflowed, rewrapped, or reworded during the move `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Run `python3 scripts/prune-ledger.py measure --repo .` and record the before-move byte total for `system-instructions.md` + `commands/_preamble.md`; list the current contents of `.writ/docs/` and, for each of the five sections, decide new-file vs. merge-into-existing-doc (checking `model-tiers.md` and `skills.md` in particular, both of which already exist and already cover adjacent ground) `[AC-2.1, AC-2.4]`
- [x] 2.2 Move `## Model Tiers` + `### entry_level` (4,519 bytes) into `.writ/docs/model-tiers.md` (existing file — merge rather than create; it already states the normative text lives in `system-instructions.md` → Model Tiers, so that claim moves with the content), leave one pointer line in the base, add the ledger row(s) with class `moved`, and land it as one commit `[AC-2.1, AC-2.2, AC-2.5]`
- [x] 2.3 Move `### required_skills: frontmatter convention` (2,809 bytes) and `### Skill authoring` (458 bytes) into `.writ/docs/skills.md` (existing file — it already documents the `required_skills:` convention and skill authoring in detail; reconcile rather than duplicate), leave one pointer line in the base for the `## Skills` section, add the ledger rows with class `moved`, and land it as one commit `[AC-2.1, AC-2.2, AC-2.5]`
- [x] 2.4 Move `## Startup Update Awareness` (3,784 bytes) into `.writ/docs/startup-update-awareness.md` (new file), leave one pointer line in the base that preserves the one-line trigger `update.sh` may read, add the ledger row with class `moved`, and land it as one commit `[AC-2.1, AC-2.2, AC-2.5]`
- [x] 2.5 Move the tutorial portion of `### Recommendation Semantics` (~1,875 bytes) into `.writ/docs/recommendation-semantics.md` (new file), leaving the rule sentence itself in the base plus one pointer line to the tutorial, add the ledger row with class `moved`, and land it as one commit `[AC-2.1, AC-2.2, AC-2.5]`
- [x] 2.6 Verify: `python3 scripts/prune-ledger.py check --repo .` exits 0 at HEAD; `bash scripts/eval.sh` reports `Findings: 0` with `check_referenced_paths` and `check_prime_directive_sync` both green; `python3 scripts/prune-ledger.py measure --repo .` run again for the after total, recorded in What Was Built and in a `{date} stage-2: ...` decision-log line naming the before/after byte counts so Story 3 knows its depth `[AC-2.3, AC-2.4]`

## Notes

**Byte-identical kept lines.** Business Rule 5 diffs every kept line against `cf84742`. A section move must delete the section's lines wholesale and add a single pointer line — never reflow the paragraph above or below the cut to "read better." If a neighboring line looks awkward after the cut, leave it; smoothing it is Story 3's job at best, and doing it here would fail `prune-ledger.py check`'s removal detection (a reflowed kept line reads as a removal with no ledger row).

**Pointer line wording.** `See .writ/docs/<file> for <topic>.` — one line, no elaboration. `check_referenced_paths` in `scripts/eval.sh` resolves `.md` paths named in the base, so the path must be exact and relative-correct from the base file's location.

**Startup Update Awareness may be read by `update.sh`.** The technical spec (§3) flags this section as possibly consumed at runtime by the install/update path, not just by a human reading the base. Confirm whether `scripts/update.sh` (or `scripts/install.sh`) greps or references any text inside this section before cutting it down to a pointer; if it does, the one-line trigger it depends on stays in the base verbatim rather than moving, and only the surrounding explanation moves.

**Merge before create.** `.writ/docs/model-tiers.md` and `.writ/docs/skills.md` already exist and already cover much of what `## Model Tiers` and `## Skills` describe (confirmed by reading both files during story generation: `model-tiers.md` states the normative contract lives in the base, and `skills.md` already documents `required_skills:` frontmatter and skill authoring in full). Task 2.2 and 2.3 reconcile the moved base text into these existing docs rather than creating near-duplicate new files — check for overlap and fold in, don't append redundantly.

**One commit per section (Business Rule 4, Recommendation).** Each of tasks 2.2–2.5 is its own commit carrying both the base-file edit and the matching ledger rows, so a single bad move is a single revertable commit and `prune-ledger.py check` stays green at every commit on the branch, not only at story close.

**Integration with Story 3.** Story 3 classifies and cuts everything that remains after this story, starting from the byte count this story records — Business Rule 6 requires the measurement to happen between the move and the cut, not be estimated. Integration with Story 5: the revert path (spec.md §"Revert path") resolves this story's completion commits as a contiguous range if Stage 5's baseline re-run comes up short, so keeping each move as a clean, self-contained commit (task 2.2–2.5) keeps that range resolvable.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** spec.md → `## 🎯 Experience Design` → Error experience → "A removal without a ledger line: `eval.sh` blocks naming the file and the missing text"; "A kept line accidentally reflowed: it shows as a removal without a ledger line, which is the intended behavior"
- **Shadow paths:** spec.md → `## 🎯 Experience Design` → State catalog → "moves in progress (bytes falling, every commit green)"; technical-spec.md → `## 3. Move targets (Story 2)` → the merge-vs-new-file decision per section
- **Business rules:** spec.md → `## 📋 Business Rules` → 2 (ledger append-only), 3 (removed includes moved — reason class `moved`), 4 (ledger entries land in the same commit as the removal), 5 (kept lines stay byte-identical, diffed against `cf84742`), 6 (moves before cuts, measured between), 8 (Prime Directive mirror stays byte-identical), 12 (decision-log line format)
- **Experience:** spec.md → `## 🎯 Experience Design` → Happy path step (2) ("Story 2 moves five documentation sections out, one commit per section, each commit carrying its ledger lines; the check reports bytes after each")
- **Requirements:** spec.md → `## Detailed Requirements` → `### Story 2 — Move documentation out`; technical-spec.md → `## 3. Move targets (Story 2)` (byte counts per section, target files, pointer-line format, expected ~15,000-byte total)
- **Codebase:** `/Users/asellke/Projects/writ/system-instructions.md` (section line ranges: `## Model Tiers` at line 269, `### entry_level` at 302, `### required_skills: frontmatter convention` at 228, `### Skill authoring` at 263, `## Startup Update Awareness` at 175, `### Recommendation Semantics` at 83); `/Users/asellke/Projects/writ/.writ/docs/model-tiers.md` and `/Users/asellke/Projects/writ/.writ/docs/skills.md` (existing docs to merge into); `scripts/prune-ledger.py` (Story 1) `check` and `measure` subcommands; `scripts/eval.sh` → `check_referenced_paths`, `check_prime_directive_sync`

---

## What Was Built

**Implementation Date:** 2026-09-07

### Per-section move table

Bytes are `prune-ledger.py measure` section figures at `272da3d` (before) and at `724e86a` (after). Every removed line is a ledger row of class `moved` whose reason is the destination path; blank lines need no row (DEV-002).

| Section | Bytes before | Bytes after (what stays) | Destination | Pointer line in the base | Ledger rows | Commit |
|---|---|---|---|---|---|---|
| `## Model Tiers` + `### entry_level` | 3,290 + 1,229 = 4,519 | 176 (heading + pointer) | `.writ/docs/model-tiers.md` (existing — merged) | ``See `.writ/docs/model-tiers.md` for the model-tier contract: `model_tier` (anchor/floor), origin, floor resolution, escalation, degradation, and `entry_level`.`` | 30 | `25518d0da71c48b888bca23ae5cdc48a7cdddb8e` |
| `### required_skills:` frontmatter convention + `### Skill authoring` | 2,809 + 458 = 3,267 | 0 (the `## Skills` intro paragraph stays; section now 550 with the pointer) | `.writ/docs/skills.md` (existing — merged) | ``See `.writ/docs/skills.md` for the `required_skills:` frontmatter convention (schema, harness contract, status and review trigger) and skill authoring.`` | 26 | `2b11f7d6d9ad079cffe1fc5022b66f56536b5a9f` |
| `## Startup Update Awareness` | 3,784 | 417 (heading + the one-sentence trigger, byte-identical + pointer) | `.writ/docs/startup-update-awareness.md` (new, 42 lines) | ``See `.writ/docs/startup-update-awareness.md` for the startup sequence, cache contract, detection rules, and notification text.`` | 26 | `30e987ef0d2fb5275154645c2fe9fec333b2d645` |
| `### Recommendation Semantics` (bullets 2–5) | 2,275 | 655 (heading + labeling-rule bullet, byte-identical + pointer) | `.writ/docs/recommendation-semantics.md` (new, 31 lines) | ``See `.writ/docs/recommendation-semantics.md` for the evidence precedence, select-or-pause classification, audit rationale fields, and resume rule behind `--recommend`.`` | 20 | `724e86a703f5405ee777dab498a2222145b6a13a` |

**Totals (`prune-ledger.py measure --repo .`):** before 28,157 bytes (`system-instructions.md` 22,505 + `commands/_preamble.md` 5,652); after **15,713 bytes** (`system-instructions.md` 10,061 + `commands/_preamble.md` 5,652, untouched). Removed 12,444 bytes across 102 ledger rows; the only additions to the base are the four pointer lines and one blank line (`git diff -U0 cf84742 -- system-instructions.md commands/_preamble.md | grep '^+'`). Story 3's cut starts from 15,713 and needs about 5,700 bytes to reach the 10,000 cap.

### Files Created

1. **`.writ/docs/startup-update-awareness.md`** (42 lines)
   - Status header (normative; moved 2026-09-07 under ADR-026; shipped by `install.sh`), the trigger sentence, then the startup sequence, cache contract, detection rules, notification text, and read-only rule verbatim.
2. **`.writ/docs/recommendation-semantics.md`** (31 lines)
   - Status header naming ADR-013 and the `_preamble.md` boundary, the labeling rule repeated for readability, then bullets 2–5 verbatim (evidence precedence, select-or-pause, audit rationale, resume).

### Files Modified

- **`system-instructions.md`** (four sections)
  - 141 lines removed, 5 added (four pointer lines, one blank). `## Model Tiers`, `## Startup Update Awareness`, `## Skills`, and `### Recommendation Semantics` headings kept; `### entry_level`, `### required_skills:`, `### Skill authoring` headings removed with their bodies (rows in the ledger). Every kept line is byte-identical to `cf84742`.
- **`.writ/decision-records/pruned-instructions-ledger.md`** (rows)
  - 102 rows appended across the four move commits, dated 2026-09-07, file `system-instructions.md`, class `moved`, reason = destination path, text verbatim with `|` escaped as `\|` (table rows and separators included). Header untouched; no `<!-- cap: blocking -->` marker.
- **`.writ/docs/model-tiers.md`** (lines 6, 87, 179)
  - Already carried every table the base had (tiers, Q1/Q2, applied assignment, `entry_level` Q1/Q2, entry notice, origin, floor resolution, escalation, degradation, alias window). Merge = the three claims that "the normative text lives in `system-instructions.md` → Model Tiers" now say this document is the normative home since 2026-09-07 (ADR-026, ledger), plus the notice's once-per-session / never-ask / skip-on-unknown sentence folded into *The entry check*.
- **`.writ/docs/skills.md`** (`### required_skills:` frontmatter convention; *Authoring a Skill*; *References*)
  - The doc's paraphrased subsection replaced by the base's normative text (schema with the four pinned clauses, harness contract, status, eager-pre-load paragraph, review trigger) with the doc's own two sentences folded in (eval `inline_skill_reads` metric; the 2026-08-12 fourth-carrier correction). *Authoring a Skill* gains the role-convention and `/refresh-command` boundary-check sentence from `### Skill authoring`; the `disable-model-invocation` sentence was already in *Invocation*. The References row names this document as the convention's source.
- **`cursor/writ.mdc`** (`### Recommendation Semantics`)
  - The section is inside `## Prime Directive`, so the identical cut landed in the same commit (Business Rule 8); `check_prime_directive_sync` green. Other sections untouched (DEV-007).
- **`scripts/eval.sh`** (`check_recommendation_semantics`)
  - 13 `require_literal` pins for the moved bullets read `.writ/docs/recommendation-semantics.md`; the 3 labeling-rule pins still read the base; the `cursor/writ.mdc` pin requires the pointer line. Dated comment above the function (DEV-006).
- **`scripts/tests/test_governor_enforcement.py`** (`MechanismRecordTests`)
  - `CLAIM_FILES[0]` and the clause test read `.writ/docs/skills.md`; docstring records the move (DEV-005).
- **`.writ/specs/2026-09-07-phase11-stage2-prune-the-base/spec-lite.md`** (For Coding Agents → Files in Scope, Integration Points)
  - Three amendments recording DEV-005..DEV-008 (Small-drift auto-amend; pre-edit SHA-256 `ce64962f1bbf4e333deac3893740bdbb02453f299905c2e27020673117518974`).
- **`.writ/specs/2026-09-07-phase11-stage2-prune-the-base/drift-log.md`** — DEV-005..DEV-008.
- **`.writ/decision-log.md`** — one `2026-09-07 stage-2:` line naming 28,157 → 15,713 (Business Rules 6 and 12).
- **`user-stories/README.md`** — Story 2 row and totals.

### Implementation Decisions

1. **Section headings stay, sub-headings go.** `## Model Tiers`, `## Startup Update Awareness`, `## Skills`, and `### Recommendation Semantics` remain as byte-identical anchors so each pointer sits under the heading readers and `eval.sh` notes (`system-instructions.md § Model Tiers`) already name; `### entry_level`, `### required_skills:`, and `### Skill authoring` leave with their bodies because the surviving pointer covers them. Technical-spec §2's example row (`## Model Tiers` as a moved line) was read as illustrative; Story 3 may cut the headings under the constraint test.
2. **The Startup Update Awareness trigger stays verbatim.** Nothing in `scripts/update.sh` or `scripts/install.sh` greps the section (`commands/update-writ.md` only restates the cache path and notice text), so no script needs the body — but without the one-sentence trigger no session would run the check at all, and a rewritten trigger would read as a removal. The heading plus that sentence plus the pointer is 417 bytes.
3. **The labeling rule is bullet 1 whole.** The "rule sentence" cannot be split from its bullet without reflowing kept lines, so lines 85–89 (the `(Recommended)` suffix, the equivalence disclosure, advisory-label and Plan-Mode sentences, 655 bytes with heading and pointer) stay; bullets 2–5 (1,789 bytes) moved — within the spec's ~1,875 estimate.
4. **Merge, not append, for the two existing docs.** `model-tiers.md` already paraphrased every base paragraph, so only its three source-of-truth claims changed; `skills.md`'s subsection was replaced with the normative text because the test pins name exact clauses the paraphrase lacked, and the doc's unique sentences were kept.
5. **Governor pins follow the text.** Two governors (`check_recommendation_semantics`, `MechanismRecordTests`) pinned moved lines in the base; retargeting them to the destination docs keeps the guarantee that the text exists and is unchanged. Dropping the pins was rejected; mutation-tested (a changed literal in the doc yields one finding).
6. **Pointer paths are backticked** so `check_referenced_paths`' token grammar would resolve them if the check ever scans the base (it does not today — DEV-008).

### Test Results

**Verification:** `python3 scripts/prune-ledger.py check --repo .` exits 0 at each of the four move commits (`25518d0` 30 rows, `2b11f7d` 56, `30e987e` 82, `724e86a` 102; `removed: n, re-added: 0` at every one, verified in a detached worktree); `uv run --python 3.9 pytest -q` — 1075 passed, 1 skipped; all 13 `scripts/tests/test_*.sh` green (`test_eval_entry_level_note.sh` 8/8, `test_update_claude_md.sh` OK); `bash scripts/eval.sh` (sandbox off, all checks) → `Findings: 0`, `Run errors: 0`, exit 0, `pruned-base` notes `over_cap: 15713 bytes > cap 10000` and `base: 15713 bytes (cap 10000), ledger: 102 rows, removed: 102, re-added: 0`.
- ✅ `--check=prime-directive-sync`, `--check=referenced-paths`, `--check=broken-refs`, `--check=length`, `--check=leanness`, `--check=recommendation-semantics`, `--check=required-skills`, `--check=anti-sycophancy`, `--check=required-sections` — each `Findings: 0` after every move commit
- ✅ AC-2.5: `git diff -U0 cf84742 -- system-instructions.md commands/_preamble.md` adds exactly four pointer lines and one blank line; `commands/_preamble.md` diff is empty; 100 non-`---` removed lines + 2 removed `---` fence lines = 102 rows
- ✅ Mutation: altering `Hard platform blockers remain blockers.` in `.writ/docs/recommendation-semantics.md` → `recommendation-semantics` reports 1 finding naming the doc; restored
- ✅ `--check=leanness`: all warnings pre-existing (commands/skills/scripts/adapters ceilings, six over-budget commands); `COMMAND_BYTE_BUDGET` note now reports the live base at −9,247 against the 24,960 pin — a report, not a finding
- ✅ Startup Update Awareness: `grep -rn "writ-update-check\|Startup Update\|update_available" scripts/update.sh scripts/install.sh` → no hits
- ✅ No new scripts; no coverage claim (documentation-only story)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Medium (DEV-005, DEV-006); Small (DEV-007, DEV-008)
- **Security:** None — markdown moves; `eval.sh` edits only change which file a literal is required in
- **Boundary Compliance:** owned set (`system-instructions.md`, four `.writ/docs/` files, ledger, spec bookkeeping); two flagged cross-boundary edits (`scripts/eval.sh` pins, `scripts/tests/test_governor_enforcement.py` pins) and one spec-mandated mirror edit (`cursor/writ.mdc`, Business Rule 8); `commands/_preamble.md` untouched

### Deviations from Spec

- **[DEV-005] `MechanismRecordTests` pins follow the text to `.writ/docs/skills.md`** — Severity: Medium
  - Spec said: the story edits the base, the docs, and the ledger
  - Reality: `scripts/tests/test_governor_enforcement.py` pinned the schema clauses and review trigger in `system-instructions.md`; `CLAIM_FILES` and the clause test now read `.writ/docs/skills.md`
  - Resolution: ⚠️ flagged; pipeline PASS; `spec.md` unchanged
- **[DEV-006] `check_recommendation_semantics` pins retargeted** — Severity: Medium
  - Spec said: move the tutorial, keep the rule sentence
  - Reality: `eval.sh` required every bullet's text in the base; 13 pins now read `.writ/docs/recommendation-semantics.md`, the `writ.mdc` pin requires the pointer line, the 3 rule pins still read the base
  - Resolution: ⚠️ flagged; pipeline PASS; `spec.md` unchanged
- **[DEV-007] `cursor/writ.mdc` mirrors only the Prime Directive cut** — Severity: Small
  - Spec said: `writ.mdc` is the Prime Directive mirror
  - Reality: the Cursor rule still carries Model Tiers, Skills, and Startup Update Awareness in full (~21,400 bytes)
  - Resolution: logged; `spec-lite.md` amended; whole-file re-sync left to Story 3 or the maintainer
- **[DEV-008] `check_referenced_paths` does not scan the base** — Severity: Small
  - Spec said: the check resolves the new pointer links
  - Reality: it iterates `commands/*.md` only; the four paths were verified on disk and `check_broken_refs` is green
  - Resolution: logged; `spec-lite.md` amended

### For Story 3

- Start from **15,713 bytes** (`system-instructions.md` 10,061; `commands/_preamble.md` 5,652); the cap needs about 5,700 more. Per-section figures are in the measure table above.
- The four pointer lines and the Startup Update Awareness trigger sentence are new or kept environment facts under ADR-026; the four section headings that stayed are fair game under the constraint test.
- Append the ledger the same way (`| 2026-09-0N | file | behavior-request | why | text |`); rows 1–102 are `moved`. The `<!-- cap: blocking -->` marker is still absent.
- `cursor/writ.mdc` needs the same commit-lockstep edit only for lines inside `## Prime Directive` (Hard Constraints, Recommended Delivery Exception, Recommendation Semantics, Judgment Principles, Prose). Decide whether to re-sync its other sections (DEV-007).
- `check_recommendation_semantics` still pins the three labeling-rule lines in the base and the pointer line in `writ.mdc`; `check_autonomy_governance` (eval.sh, `require_literal "$system"`) pins six literals of `### Recommended Delivery Exception` in the base and one in `writ.mdc` — retarget before cutting those, as DEV-006 did.

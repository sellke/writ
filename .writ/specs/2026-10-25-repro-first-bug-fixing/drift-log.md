# Drift Log

> Spec: .writ/specs/2026-10-25-repro-first-bug-fixing/
> Created: 2026-10-29
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Repro-Order Check Script — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-001] Switch-line regex follows the existing switch readers, not the technical spec
- **Severity:** Small
- **Spec said:** technical-spec § Order of work step 1 gives `^\s*-\s*\*\*Repro First:\*\*\s*(\S+)\s*$`; story task 1.2 says to use the `scripts/review-panel.py` `config_value` pattern.
- **Implementation did:** `^- \*\*Repro First:\*\*[ \t]*(.*)$`, first match, value stripped, with the semantics of `scripts/review-override.py` `_resolve_switch`: absent, empty, or `on` (any case) → on; `off` (any case) → `unverifiable` / `reason: repro-first off` before any git call; another value → on plus `reason: repro-first value <v> read as on`. An indented line is not read, and `off # note` reads as on with the value reason line.
- **Reason:** The story task is the more specific instruction, and it keeps all four Phase 15 config switches on one line shape.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Order of work step 1 reads `^- \*\*Repro First:\*\*[ \t]*(.*)$` (first match, value stripped; empty reads as on). None needed in spec-lite.md; it does not give the pattern.

#### [DEV-002] Rule 6 freezes only the repro's test-classified, written paths
- **Severity:** Small
- **Spec said:** Check Rule 6 covers "a path the repro commit added or modified"; Business Rule 5 says "any file the repro commit added or changed".
- **Implementation did:** Freezes paths the repro commit added, modified, type-changed, or renamed/copied to that classify as test files. `.writ/` paths and paths the repro deleted are not frozen; a source path in a repro already fails Rule 3.
- **Reason:** Freezing `.writ/` would fail every story completion commit, and reporting a fix's edit to a source file as `repro_test_modified` would misname the problem.
- **Resolution:** Auto-amended
- **Spec amendment:** Check Rule 6 reads "No later non-repro commit modifies, renames, or deletes a test file the repro commit added or modified (`.writ/` paths are never frozen)." None needed in spec-lite.md.

#### [DEV-003] Which commit the `<sha>` in a reason line names
- **Severity:** Small
- **Spec said:** Reason codes carry `<sha>` without saying which commit.
- **Implementation did:** Rules 4 (`source_before_repro`) and 6 (`repro_test_modified`) name the offending commit; Rules 2, 3, and 5 name the repro commit. Documented in the script docstring and the contract Notes.
- **Reason:** Fills a gap; Story 4's consumers print these lines.
- **Resolution:** Auto-amended
- **Spec amendment:** Under the Check Rules table: "In rules 4 and 6, `<sha>` is the offending commit; in rules 2, 3, and 5 it is the repro commit." None needed in spec-lite.md.

#### [DEV-004] Printed paths and subjects escape control characters; an unsearchable `.writ/` exits 2
- **Severity:** Small
- **Spec said:** Error & Rescue Map: an unreadable config exits 2. Nothing on control characters in output.
- **Implementation did:** The existence check and the read share one `OSError`/`UnicodeDecodeError` handler, so a `.writ/` that cannot be searched exits 2 instead of a traceback. Every `reason:` line passes through `printable()`, which escapes C0, DEL, C1, U+2028, and U+2029, so a filename holding a newline cannot add a `reason:` line. Both came from Gate 3 recommendations, each with a test.
- **Reason:** Keeps the exit-2 contract and the one-finding-per-line output shape that consumers parse.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § CLI adds "Control characters in printed paths and subjects are escaped." None needed in spec-lite.md.

---

## Story 2: The tdd-cycle Bug Path — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-005] `## Repro First` sits after `## Reviewer Filters`, not after `## Review Panel`
- **Severity:** Small
- **Spec said:** Task 2.4: add a `## Repro First` section "after `## Review Panel`" that follows that section's pattern.
- **Implementation did:** The row is last in Supported Keys and the section follows `## Reviewer Filters`, the last of the three switch sections (Gate 0 Divergence, Safety Fact, Reviewer Filters) that sibling Phase 15 specs added after Review Panel. It uses their pattern: fenced `off` example, then one paragraph.
- **Reason:** Placing it directly after Review Panel would split the switch sections, and Review Panel is a slug list, not an on/off switch. The contract and technical spec set no placement.
- **Resolution:** Auto-amended
- **Spec amendment:** Task 2.4 reads "add a `## Repro First` section after `## Reviewer Filters` that follows the switch sections' pattern". None needed in spec-lite.md.

#### [DEV-006] Step 3 says the `Repro:` trailer shares the last paragraph with other trailers; the example shows it on its own line
- **Severity:** Small
- **Spec said:** technical-spec § Skill Section Draft step 3: "a trailer `Repro: <issue path or one-line bug>` in the message's last paragraph"; the Examples block shows `Repro:` on the subject line.
- **Implementation did:** Step 3 adds "with any other trailers and no blank line between them". The example puts `Repro: login fails for plus-sign emails` on an indented line under the repro `commit:` line.
- **Reason:** `scripts/repro-order.py` reads only the final paragraph (Story 1); a separate `Repro:` paragraph followed by a `Co-Authored-By:` or `Ref:` paragraph is not detected, and a one-line message with `Repro:` on the subject fails `no_repro_commit`.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Skill Section Draft step 3 and Examples block as built. None needed in spec-lite.md.

#### [DEV-007] Removal Inventory row 1 omits the When to Use bullet this story changes
- **Severity:** Small
- **Spec said:** Removal Inventory, `skills/tdd-cycle/SKILL.md` row: "`### Bug fixes: repro first` section and its example; restore the original two-line bug example".
- **Implementation did:** Per AC-2.3, the When to Use bug bullet also changed to point at the section. The removed example was three lines (red / green / refactor), not two.
- **Reason:** Followed literally, the row would leave a bullet pointing at a deleted heading. `2026-10-25-gate-upgrade-removal-measurement` consumes this inventory.
- **Resolution:** Auto-amended
- **Spec amendment:** Removal Inventory row reads "`### Bug fixes: repro first` section; the bug example under `## Examples` (restore the three-line `parseDate('')` example); the When to Use bug bullet (restore the 'reproduce it with a failing test first' bullet)". Recorded here because the pipeline never auto-modifies `spec.md`. None needed in spec-lite.md.

---

## Story 3: The Coding Agent's Repro Report — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-008] Requirement 3 sentence is longer than the technical-spec draft
- **Severity:** Small
- **Spec said:** technical-spec § Report Block: "Implementation Requirement 3 gains: under `/implement-story`, the repro and fix commits each end with `Ref: .writ/specs/<spec-id>/user-stories/<story-file>.md`."
- **Implementation did:** The sentence adds that the footer sits in the message's last paragraph with any other trailers (and, on the repro commit, its `Repro:` trailer), and that `/prototype` commits carry no `Ref:` footer.
- **Reason:** AC-3.1 and Business Rule 6 require the `/prototype` clause. `scripts/repro-order.py` reads `Repro:` only from the last paragraph, so a separate `Ref:` paragraph after it would hide the repro (see DEV-006). The repro-commit qualifier came from a Gate 3 recommendation so a fix commit is never read as needing `Repro:`.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Report Block's last line reads as built in `agents/coding-agent.md` Requirement 3. None needed in spec-lite.md.

#### [DEV-009] Report block presentation differs from the draft; labels, order and `Commits` shape do not
- **Severity:** Small
- **Spec said:** technical-spec § Report Block shows the bug form in its own fence and the three short forms as bold-labelled prose; placeholders `[at most 10 lines]` and `[line 1, any reason: lines, and the summary of repro-order.py check]`. spec.md § Detailed Requirements → Story 3 says "three forms".
- **Implementation did:** All four forms sit in one block under italic label lines, with an intro line ("Every report has this section, in exactly one of these four forms. List commits oldest first."). Placeholders read `[at most 10 lines from the same command]` and name `reason:` lines and the summary line. Field labels, field order, and the `Commits: repro [sha] → fix [sha][, [sha]]` shape match the technical spec. Four forms, per AC-3.2/3.3 and the technical spec.
- **Reason:** Gate 0 divergence chose sketch A (fields per form, one arrow `Commits` line) with the technical-spec order kept; "same command" is Business Rule 7.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Report Block shows the as-built block; spec.md Story 3 "three forms" reads "four forms" (recorded here; the pipeline never edits spec.md). None needed in spec-lite.md.

---

## Story 4: Consumer Wiring and Ordered-Commit Integration — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-010] Two out-of-boundary byte caps raised by this story's growth
- **Severity:** Small
- **Spec said:** Task 4.7: the only edits are `commands/prototype.md` Step 3, `commands/implement-story.md` Gate 1, the integration skill's step 3 paragraph, the wiring module, and generated trees. Technical Concerns expected byte-budget warnings.
- **Implementation did:** `KNOWN_OVER_BUDGET["commands/implement-story.md"]` in `scripts/tests/test_governor_enforcement.py` 15269 → 15717 and `IMPLEMENT_STORY_CAP` in `scripts/tests/test_review_route_rigor.py` 40234 → 40682, each with a dated comment. The file grew 40,229 → 40,677 bytes (+448); the cap keeps its 5-byte slack.
- **Reason:** Both are whole-file caps, so any growth in `implement-story.md` breaks them, and AC-4.5 needs a green suite. The sibling spec's Gate 2.5/3 allowance is unchanged.
- **Resolution:** Auto-amended
- **Spec amendment:** Task 4.7 adds "plus the dated bumps of both whole-file byte caps by this story's measured growth". None needed in spec-lite.md.

#### [DEV-011] AC-3.5 and AC-4.5 traced by citations in the wiring module
- **Severity:** Small
- **Spec said:** No task names ac-trace citations; AC-3.5 and AC-4.5 are verification-run criteria.
- **Implementation did:** Cited both in the `test_repro_first_wiring.py` docstring and in `test_generated_trees_current`, as the module already does for AC-2.5.
- **Reason:** `ac-trace.py` reported `untested_criterion AC-3.5` once Story 3 was marked Completed, which would have failed AC-4.5's zero-findings `eval.sh`.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Tests → `test_repro_first_wiring.py` adds "The module cites AC-3.5 and AC-4.5; their evidence is the full pytest run, the bash loop, and `bash scripts/eval.sh`." None needed in spec-lite.md.

#### [DEV-012] The `/prototype` Bug path line integrates named commits by cherry-pick
- **Severity:** Small
- **Spec said:** technical-spec § Consumer Lines: "When the agent's `### Repro` block names commits, run `python3 scripts/repro-order.py check --repo . --base <that SHA>` after integration and put its output …".
- **Implementation did:** "When the agent's `### Repro` block names commits, bring them into this checkout with `git cherry-pick`, oldest first, as the integration skill's Ordered commits paragraph says, not through `git apply`. Then run `python3 scripts/repro-order.py check --repo . --base <that SHA>` …".
- **Reason:** Gate 3 cycle 1 (FAIL, Major): Step 3's integration sentence prescribes `git apply`, which drops commits, so every worktree-isolated bug run would fail `no_repro_commit`. Reproduced in a scratch repo. The fix stays inside the one Removal Inventory line; the integration sentence (pinned by `test_prototype_worktree_integration.py`) is unchanged.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Consumer Lines `/prototype` Bug path line reads as built in `commands/prototype.md` Step 3; § Error & Rescue Map → Integration adds "/prototype: the line overrides Step 3's `git apply` for named commits". None needed in spec-lite.md.

#### [DEV-013] The `/implement-story` Bug path line keeps the base across recodes and routes exit 2
- **Severity:** Small
- **Spec said:** technical-spec § Consumer Lines: "record `git rev-parse HEAD` before the spawn … `unverifiable` prints and continues."
- **Implementation did:** "record `git rev-parse HEAD` before the story's first Gate 1 spawn and reuse it on recodes … `unverifiable`, or exit 2 with its stderr cause, prints and continues."
- **Reason:** Gate 3 cycle 1 (FAIL, Major): a per-spawn base moves past the first pass's repro on a recode, so the check fails `no_repro_commit` and the story is falsely `⚠️ DEGRADED`. Exit 2 left stdout empty and unrouted. No loop or increment is added; only `fail` maps to DEGRADED (Business Rule 10).
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Consumer Lines `/implement-story` Bug path line reads as built in `commands/implement-story.md` Gate 1. None needed in spec-lite.md.

---

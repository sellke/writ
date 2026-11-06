# Drift Log

> Spec: .writ/specs/2026-10-25-review-route-rigor/
> Created: 2026-10-29
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Upgrade switches — Drift Report

> Run: 2026-10-29
> Overall Drift: Medium

### Deviations

#### [DEV-001] `switch` prints a state word on line 1, an exception to the agent CLI check shape
- **Severity:** Medium
- **Spec said:** technical-spec § Resolver calls the output "check shape" with line 1 `on` or `off`; AC-1.1–1.3 pin line 1 to `on`/`off`.
- **Implementation did:** Line 1 is `on` or `off`, as the ACs require. `.writ/docs/agent-cli-contract.md` gained a Notes bullet recording `review-override.py switch` as a documented exception to the Check shape (line 1 is `pass`/`fail`/`unverifiable` everywhere else; `review-panel.py status` and `jev-judge.py status` print `pass` and carry state in `reason:` lines).
- **Reason:** The ACs and the Check-shape rule cannot both hold. The locked spec answers the question, and Stories 2–4 branch on line 1, so the shape is frozen here. `test_agent_cli_contract.py` has no smoke row for `switch`.
- **Resolution:** Flagged for review
- **Spec amendment:** N/A — flagged for post-implementation review. If the contract should stay uniform, a later spec can move the state to a `reason:` line and print `pass` on line 1.

#### [DEV-002] `on` is matched in any case
- **Severity:** Small
- **Spec said:** "value `on` or empty → `config_on`"; only `off` is described as "any case".
- **Implementation did:** `ON` and `On` resolve to `config_on`, not `malformed_value ON`.
- **Reason:** Line 1 and the exit code are the same either way; only the reason text differs. Matches the rule that only `off` turns a switch off.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Resolver row "value `on` or empty" reads as "value `on` (any case) or empty". None needed in spec-lite.md; it says only `off` turns a switch off.

#### [DEV-003] A script edit regenerates the plugin tree
- **Severity:** Small
- **Spec said:** task 1.4: "confirm no generated tree changes are needed for a script-only edit"; technical-spec regenerates trees after stories that edit `agents/`, `commands/`, or `skills/`.
- **Implementation did:** Ran `python3 scripts/gen-platform-trees.py`, which rewrote `plugins/writ/scripts/review-override.py`; `--check` fails without it.
- **Reason:** `scripts/` is mirrored into `plugins/writ/scripts/`, so the task's premise was wrong. The change matches Must Include 7.
- **Resolution:** Auto-amended
- **Spec amendment:** Task 1.4 reads "run `python3 scripts/gen-platform-trees.py`; `scripts/` is mirrored into `plugins/writ/scripts/`". None needed in spec-lite.md; it already says to regenerate trees.

---

## Story 2: Reviewer lead-judgment filters — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-004] Governor budget pin raised for the Gate 3 paragraph
- **Severity:** Small
- **Spec said:** technical-spec § Gate 3 Change permits up to 1,800 bytes of net growth in Gate 2.5 and Gate 3; it names no test edit.
- **Implementation did:** `KNOWN_OVER_BUDGET["commands/implement-story.md"]` in `scripts/tests/test_governor_enforcement.py` moved 13474 → 13769 (file 38434 → 38729, +295) with a dated comment.
- **Reason:** The over-budget test fails on any growth unless the pin moves. The growth is inside the spec's allowance.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Gate 3 Change, Byte budget: raise the `KNOWN_OVER_BUDGET` pin by the same net growth, with a dated comment naming the story. None needed in spec-lite.md.

#### [DEV-005] Agent CLI contract Callers cell names `commands/review.md`
- **Severity:** Small
- **Spec said:** technical-spec § Agent and Command Changes does not list `.writ/docs/agent-cli-contract.md`.
- **Implementation did:** Added `commands/review.md` to the `review-override.py` Callers cell.
- **Reason:** `/review` now calls `review-override.py switch`; the doc stays accurate.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Clean Removal → Remove `reviewer-filters` step 3 also removes `commands/review.md` from that Callers cell. None needed in spec-lite.md.

#### [DEV-006] README live-skill count corrected from a stale value
- **Severity:** Small
- **Spec said:** task 2.2: update the live-skill count.
- **Implementation did:** "16 skills are live today" became 18. The line was already stale (17 rows before this story); `test_readme_row_and_live_count` now pins the count to the row count.
- **Reason:** The count is a fact about the table; Story 4 must bump it again.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed in spec-lite.md.

#### [DEV-007] Manifest entry inserted in alphabetical position
- **Severity:** Small
- **Spec said:** "Append the `review-judgment-filters` entry to `.writ/manifest.yaml` `skills:` (append only)."
- **Implementation did:** Inserted between `project-context-snapshot` and `safe-refactor-loop`; no other entry changed.
- **Reason:** The `skills:` list is alphabetical, as the `design-divergence` precedent shows. "Append only" holds in the sense that matters: no existing entry is edited.
- **Resolution:** Auto-amended
- **Spec amendment:** task 2.2 reads "add the entry in alphabetical order without editing other entries". None needed in spec-lite.md.

---

## Story 3: Blast radius at Gate 2.5 — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-008] Repo-root extensionless path token dropped for generic or short stems
- **Severity:** Small
- **Spec said:** technical-spec § Blast Radius step 1: tokens are the path with and without its extension, plus the stem unless it is generic or short.
- **Implementation did:** `search_tokens` leaves out the extensionless path when it equals a generic or short bare stem, which happens only for repo-root files such as `setup.py` (`setup`).
- **Reason:** Read literally, step 1 makes `setup` a token and breaks AC-3.2 ("a file that contains only the bare stem is not listed"). The implementation follows the AC.
- **Resolution:** Auto-amended
- **Spec amendment:** § Blast Radius step 1: "When the path has no directory part and its stem is generic or shorter than 4 characters, the path without its extension is not a token." spec-lite.md "path or non-generic stem" already covers it.

#### [DEV-009] `.writ/` skipped at any depth
- **Severity:** Small
- **Spec said:** "Always skip `.writ/`."
- **Implementation did:** Skips any path with a `.writ` directory segment, including nested ones.
- **Reason:** Same intent: specs and state mention files but do not call them.
- **Resolution:** Auto-amended
- **Spec amendment:** § Blast Radius step 2: "Always skip any `.writ/` directory, at any depth." None needed in spec-lite.md.

#### [DEV-010] Non-regular and unreadable candidates skipped
- **Severity:** Small
- **Spec said:** Skip files over 1 MB and files that are not valid UTF-8.
- **Implementation did:** Also skips directories (including tracked symlinked directories), FIFOs, devices, permission-denied files, and tracked files deleted from the working tree, checked with `stat` before `open`.
- **Reason:** A FIFO would otherwise hang `open`, which the agent CLI contract's "never wait unbounded" rule forbids.
- **Resolution:** Auto-amended
- **Spec amendment:** § Blast Radius step 2: add "and any path that is not a readable regular file". None needed in spec-lite.md.

#### [DEV-011] `--pretty` counts are taken before the cap and cover non-test changed files
- **Severity:** Small
- **Spec said:** "one `<changed>: <n> consumer(s), <m> test(s)` line per changed file"; summary `(<n> changed, <k> consumers)`; silent on the cap.
- **Implementation did:** Per-file lines and `<n>` cover non-test changed files; the counts and `<k>` (distinct consumers) are taken before `--limit`, so they can exceed the JSON list lengths when `truncated` is non-empty.
- **Reason:** The human view reports the true size. Story 4 reads the JSON, so the integration point is unaffected.
- **Resolution:** Auto-amended
- **Spec amendment:** § Blast Radius `--pretty` bullet: "one line per non-test changed file, counted before the `--limit` cap; `<k>` counts distinct consumers before the cap." None needed in spec-lite.md.

---

## Story 4: Safety fact at Gate 3 — Drift Report

> Run: 2026-10-29
> Overall Drift: Medium

### Deviations

#### [DEV-012] Story report line leaves out the State Catalog outcome suffixes
- **Severity:** Medium
- **Spec said:** spec.md → Experience Design → State Catalog shows `— does not hold`, `— contradicts verdict`, `— below floor`, `safety-fact: missing`, and `safety-fact: unverifiable (<reason>)`.
- **Implementation did:** Gate 3 prints `safety-fact: <measured> (claimed <claimed>) — <fact>`, `safety-fact: off`, or `safety-fact: not on route`, and "print the reason" for `unverifiable` — the technical-spec § Gate 3 Change draft.
- **Reason:** The technical-spec draft and the State Catalog disagree. The 1,800-byte cap leaves 5 bytes, which does not fit the suffixes. The verifier's line 1 and `reason:` lines still carry the outcome, and the removal-measurement spec reads those.
- **Resolution:** Flagged for review
- **Spec amendment:** N/A — flagged for post-implementation review. Either amend the State Catalog to the shipped form or add "plus ` — <reason>` on a fail" and trim elsewhere in Gate 3.

#### [DEV-013] `Holds: no` with no verdict line is a contradiction
- **Severity:** Small
- **Spec said:** `safety_fact_contradicts_verdict` fires on `Holds: no` with verdict PASS.
- **Implementation did:** It also fires when no `REVIEW_RESULT` or `EVALUATION_RESULT` line is found.
- **Reason:** The table does not cover a missing verdict; without this the case would pass or fail with no reason. Failing closed is the safer reading.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Verifier table, `contradicts` row: "`Holds: no` with verdict PASS, or with no verdict line". None needed in spec-lite.md.

#### [DEV-014] No section prints `missing section` and `below_floor none`
- **Severity:** Small
- **Spec said:** No section → `safety_fact_missing`; "when more than one fail reason applies, all are printed in the table's order".
- **Implementation did:** Prints `reason: safety_fact_missing section` then `reason: safety_fact_below_floor none`.
- **Reason:** Both conditions are true. Gate 3 checks "still missing" before "still below floor", so routing is unchanged.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Verifier: "With no section, the measured rung is `none` and `below_floor none` follows `missing section`." None needed in spec-lite.md.

#### [DEV-015] Every evidence line of a rung must be accepted, for every rung
- **Severity:** Small
- **Spec said:** "Every cited `path:line` is valid" is stated for `traced` only.
- **Implementation did:** One bad `read`, `tested`, or `reproduced` line also rejects that rung; the skill says the same.
- **Reason:** Consistent with `traced`; stops a reviewer padding a rung with unchecked citations.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Evidence Ladder: "A rung counts only when it has at least one evidence line and every line for that rung is accepted." None needed in spec-lite.md.

#### [DEV-016] Absolute cited paths are rejected even inside `--repo`
- **Severity:** Small
- **Spec said:** "A path that resolves outside `--repo` is rejected."
- **Implementation did:** Every absolute path is rejected; the skill tells reviewers to cite repo-relative paths.
- **Reason:** Stricter, simpler rule with the same intent.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Verifier → Parsing: "Cited paths are repo-relative; an absolute path, or one that resolves outside `--repo`, is rejected." spec-lite.md "Cited path outside `--repo` or missing → evidence rejected" still holds.

#### [DEV-017] `tested` accepts pytest node IDs
- **Severity:** Small
- **Spec said:** `- tested: path::test_name`, accepted when `test_name` occurs in the file's text.
- **Implementation did:** Also accepts `path::Class::name` and strips a trailing `[param]`; every `::` segment must occur in the file.
- **Reason:** Reviewers copy pytest node IDs.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Evidence Ladder `tested` row: "`path::name` or a pytest node ID; each `::` segment, `[param]` removed, occurs in the file's text". None needed in spec-lite.md.

#### [DEV-018] `review-agent` gains a `## Recorded Test Results` prompt block
- **Severity:** Small
- **Spec said:** review-agent gets input rows, one conditional line, and one output slot; Clean Removal step 5 lists those.
- **Implementation did:** Also adds a `{recorded_test_results}` block to the prompt template so the new input reaches the agent.
- **Reason:** Required plumbing for the `tested` rung.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Agent and Command Changes and § Clean Removal → Remove `safety-fact` step 5 also name the `## Recorded Test Results` prompt block. None needed in spec-lite.md.

#### [DEV-019] Routing precedence when reasons co-occur
- **Severity:** Small
- **Spec said:** Each reason has its own outcome; the re-spawn carries "the `reason:` lines".
- **Implementation did:** Gate 3 routes "first match wins" with `safety_fact_contradicts_verdict` first (recode, no re-review); the re-spawn carries the `rung:` and `reason:` lines (Gate 0 divergence sketch A).
- **Reason:** A reviewer that found the fact does not hold is past the point a re-review helps; the skill's re-review guidance reads the `rung:` line.
- **Resolution:** Auto-amended
- **Spec amendment:** spec.md → Verifier outcomes is never auto-modified; proposed text: "When `safety_fact_contradicts_verdict` is among the reasons, it decides the outcome. The re-review receives the `rung:` and `reason:` lines." None needed in spec-lite.md.

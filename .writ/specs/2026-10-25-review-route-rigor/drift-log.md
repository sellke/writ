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

# Drift Log

> Spec: .writ/specs/2026-11-06-ship-watch-and-merge/
> Created: 2026-11-06
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: The merge rule re-derives readiness — Drift Report

> Run: 2026-11-06
> Overall Drift: Small

### Deviations

#### [DEV-001] The merge rule validates a little more than the technical spec, and resolves `--repo` first
- **Severity:** Small
- **Spec said:** technical-spec § `jev-judge.py` Merge Rule: step 7 builds `"pr_ready_" + <first blocker class, else first unknown code, else verdict>`; `head_sha` must match `^[0-9a-fA-F]{40}$`; `snapshot` must be a non-empty string; step 3 resolves a relative snapshot against `repo` and step 4 runs the child with `cwd=repo`.
- **Implementation did:** `_merge_token` lowercases the class or code, maps other characters to `_`, and caps it at 40 characters. A `head_sha` with surrounding whitespace and a whitespace-only `snapshot` are usage errors. `merge_rule` resolves `repo` before building the child's paths.
- **Reason:** For every token the real `pr-ready.py` prints the output is the same. The regex's `$` matches before a trailing newline, so `"<40 hex>\n"` would otherwise pass. The Gate 3 review reproduced a relative `--repo sub` doubling the child's paths (the child runs in `repo`), which asked with `pr_ready_exit_2`; resolving first fixes it.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach names the normalized token, the strict field checks, and the resolved repo.

## Story 2: `/ship` opens the PR without asking and records the ledger — Drift Report

> Run: 2026-11-06
> Overall Drift: Small

### Deviations

#### [DEV-002] The PR-agent Overview paragraph cut moves to Story 4
- **Severity:** Small
- **Spec said:** technical-spec § `ship.md` Changes by Story → Story 2 and § Byte Budget list the "How `/ship` absorbs the PR agent concept" paragraph (−369 bytes) as a Story 2 cut.
- **Implementation did:** Kept the paragraph in Story 2. Story 4, which rewrites the Overview, cuts it.
- **Reason:** With every Story 2 cut, `commands/ship.md` measured 24,767 bytes, below the 24,960 floor that § Byte Budget forbids ("If a story's cuts would cross the floor, leave the remaining cuts to Story 4").
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Line Budget Constraints names the deferred cut.

#### [DEV-003] The Doubt Rule call is stated once, in a `### Decisions` subsection
- **Severity:** Small
- **Spec said:** AC-2.2: each decision names its record and `scripts/jev-judge.py doubt --record` and says an asked answer is labeled with `doubt-label`; technical-spec names the files `decision-<step>.json`.
- **Implementation did:** `### Decisions` (before Step 1) states the record fields, the `doubt --record` and `doubt-label` calls, and the temp-file write once. Each site names its file (`decision-tests.json`, `decision-plan.json`, `decision-branch.json`, `decision-commit.json`), site, options, and recommended option.
- **Reason:** One rule stated once and cited keeps the four sites short and identical in mechanics; the byte budget had no room for four copies.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach names the `### Decisions` subsection.

## Story 3: A watch pass works a PR to merge-ready — Drift Report

> Run: 2026-11-06
> Overall Drift: Small

### Deviations

#### [DEV-004] The `loop:` block cites the watch file as a glob
- **Severity:** Small
- **Spec said:** technical-spec § Story 3 `loop:` block, exact: "The halt record goes to .writ/state/ship/watch-pr-<n>.json with the resume command /ship --watch."
- **Implementation did:** `.writ/state/ship/watch-pr-*.json`.
- **Reason:** `scripts/eval-shipped-refs.py` flags a `.writ/state/` path on a `calibrated_against:` line as `calibration-state` unless it is a glob over the user's own records. The exact text would fail `eval.sh check_shipped_refs`.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Line Budget Constraints notes the glob.

#### [DEV-005] `gh api graphql --input` checked from gh's help text, not a live call
- **Severity:** Small
- **Spec said:** Task 3.1: before anything else, run `gh api graphql --input` once with `{"query":"query{viewer{login}}"}` and record the gh version.
- **Implementation did:** Read `gh api --help` for gh 2.96.0 (2026-07-02): `--input file` is "The file to use as body for the HTTP request", and with `--input` any field flags go to the query string, so the file carries `query` and `variables` whole. No call was made.
- **Reason:** The Phase 16 lane may not run `gh` against GitHub. The live check belongs to the Human UAT run (spec.md → Human UAT).
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Testing Agents → Test Strategy names the help-text check and leaves the live call to UAT.

#### [DEV-006] Step 7 is about twice the Story 3 byte estimate, and test fixtures learn the sixth loop command and `re-enter`
- **Severity:** Small
- **Spec said:** technical-spec § Byte Budget, Story 3: Step 7 about +3,200 bytes, story net ≤ +3,000; task 3.2 renames one test in `test_eval_leanness_contract.py`.
- **Implementation did:** Step 7 measures 7,319 bytes after the Gate 3 recode and the story nets +7,593 (`commands/ship.md` 32,974 bytes). Projected residual after Story 4: about +3.5 KB over 28,907; disclosed, not closed. Beyond the rename, `test_all_five_declared_emits_nothing` becomes `..._six_...`, `scripts/tests/test_eval_leanness.sh`'s fixture gains `ship` (commands metric 9 → 10), `scripts/tests/test_gen_platform_trees.py`'s `GOLDEN` gains `re-enter`, and the `parity-no-file-search/codex.md` fixture gains a `re-enter` row.
- **Reason:** The 7.6 table, the fixed comments query, and the two request templates the tests pin are about 2,800 bytes before any prose. The fixtures stand in for the product population (loop-bearing commands, neutral names); without them those suites fail on the new command and row. The cap is not a gate (ADR-023); Story 4 applies the reserve cuts and discloses the residual.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Files in Scope names the three test fixtures.

#### [DEV-007] The Gate 3 halt repro ships as its own test file, which `test-integrity.py` cannot attribute to `ship.md`
- **Severity:** Small
- **Spec said:** spec-lite.md → Files in Scope names `scripts/tests/test_ship_watch.py` as the Story 3 test file; implement-story Gate 4 runs `test-integrity.py authenticity` over the story's test files.
- **Implementation did:** Story 3 also adds `scripts/tests/test_ship_watch_halt_repro.py`, the Gate 3 reviewer's confirmed repro (a halted watch could never resume), kept byte for byte. `test-integrity.py authenticity` flags it `test_imports_no_source`: it reads `commands/ship.md` and runs nothing, and the checker counts only imports and executed script paths. Authenticity runs over `test_ship_watch.py`, which carries the same assertion and passes.
- **Reason:** The evidence gate pins the repro by sha256 and fails `repro_removed` or `repro_modified` if it changes. The subject is a markdown command, so a prose test is the only kind there is; the repro did fail before the 7.2 fix and passes after it.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Files in Scope names the repro file.

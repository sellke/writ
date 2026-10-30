# Drift Log

> Spec: .writ/specs/2026-10-25-gate-upgrade-removal-measurement/
> Created: 2026-10-29
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Trial Harness: init and prepare — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-001] `init` takes an optional `--yuss` and records the before-snapshot
- **Severity:** Small
- **Spec said:** technical-spec § Subcommands: `init --baseline FILE --out FILE [--repo .] [--force]`. Business Rule 2 and AC-3.2 require a yuss `before` snapshot in the trial file, but no subcommand records it.
- **Implementation did:** `init` accepts `[--yuss PATH]` and stores `yuss_snapshot.before` as `{head, refs_sha256, status_sha256}` (hashes only, read-only git calls with `GIT_OPTIONAL_LOCKS=0`). New refusals: `yuss_missing` (path missing or not a work-tree top) and `repo_missing` (`--repo` not a directory, which would otherwise store four silent `present: false` probes).
- **Reason:** Fills the gap so Rule 2 and AC-3.2 can be met without hand-editing the trial file. Story 2 adds the matching `snapshot` subcommand for `after`.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Subcommands `init` row adds `[--yuss PATH]` and the refusals `repo_missing` and `yuss_missing`. None needed in spec-lite.md.

#### [DEV-002] `prepare` re-validates identity fields and requires yuss to be a work-tree top
- **Severity:** Small
- **Spec said:** `prepare` refuses when the yuss path is missing, a SHA is unreachable, or `_prepare_run` fails.
- **Implementation did:** Also refuses `trial_invalid`, `story_unknown`, `bad_sha`, `unsafe_path` (fields re-checked from the trial file before any git call), and `yuss_missing` when yuss is not the top of a git work tree. Pre-flight uses local git helpers; `_prepare_run` and `PrepareError` are still loaded from `scripts/review-panel.py` by path, and `PrepareError` is checked at load time with the four reused names.
- **Reason:** Stricter input checks; valid input behaves the same. `init` must not load review-panel.py, so it cannot share review-panel's `_git`.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Subcommands `prepare` refusals add `trial_invalid`, `story_unknown`, `bad_sha`, `unsafe_path`, and `yuss_missing` (not a work-tree top). None needed in spec-lite.md.

#### [DEV-003] Extra `prepare` output lines, `tests.txt` written by `prepare`, and the compute-blocker reason
- **Severity:** Small
- **Spec said:** `prepare` "prints every path"; a skip stores `gate0_route: "skip"` with the reason. § Arms names `<run>/tests.txt` but no step writes it.
- **Implementation did:** `prepare` writes `<run>/tests.txt` (line 1 `historical, not re-run`, then the story's `### Test Results` subsection of `## What Was Built`, with any `exit code:` line dropped) and `<run>/routes.json`, and prints `tests:`, `boundary:`, `routes-json:`, and, on a skip, `gate0_reason:` lines. A `boundary-map.py compute` blocker stores `gate0_reason: "unverifiable: no planned files"`; the route value is still `skip`.
- **Reason:** The arm procedures need `tests.txt`; keeping it free of `exit code:` lines preserves the spec's "`tested` rung out of reach" property.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Subcommands `prepare` effect adds "writes `tests.txt` and `routes.json`"; § Routes: a compute blocker stores `gate0_reason: "unverifiable: no planned files"`. None needed in spec-lite.md.

---

## Story 2: Trial Harness: record, sheet, label, and report — Drift Report

> Run: 2026-10-29
> Overall Drift: Small

### Deviations

#### [DEV-004] `snapshot` subcommand records the yuss after-snapshot
- **Severity:** Small
- **Spec said:** Contract Must Include 1 lists `init`, `prepare`, `record`, `sheet`, `label`, `report`. Business Rule 2 requires before and after yuss snapshots with recorded equality, and the report prints `yuss:`, but no subcommand records `after`.
- **Implementation did:** `snapshot --trial FILE --yuss PATH` computes `after` the way `init --yuss` computes `before` (HEAD plus hashes, read-only) and stores `unchanged`. A null `before` is refused `no_before_snapshot`. Line 1 is `unverifiable` with `reason: yuss_changed` when yuss changed. `report` prints `yuss: unchanged|changed|not checked`.
- **Reason:** Fills the gap DEV-001 named. Additive; no named interface changed.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Subcommands adds `snapshot --trial FILE --yuss PATH` (records `yuss_snapshot.after` and `unchanged`; refusals `no_before_snapshot`, `yuss_missing`); § Verdict output's `yuss:` line reads `unchanged`, `changed`, or `not checked`. None needed in spec-lite.md.

#### [DEV-005] Extra refusals in `record`, `sheet`, and `label`
- **Severity:** Small
- **Spec said:** `record` refuses an inapplicable arm, an evidence mismatch, an origin mismatch, or unreadable output; `sheet` a missing arm or a recorded sheet; `label` a hash mismatch, a bad field, or an agent-like name.
- **Implementation did:** Adds `not_prepared`, `no_verdict`, `bad_state`, `verifier_missing`, `state_dir_unresolved`, `state_dir_unwritable`, `unsafe_path` (identity re-check), `raw_missing` (raw output gone or its sha256 changed), `sheet_stale` (a `record` after `sheet` changed the finding IDs or the never-exercised set), `no_sheet`, and `sheet_unreadable`. `--labeled-by` is also refused when it holds a newline, CR, or backtick. Every arm uses one state rule: its own switch `on`, every other given switch `off`.
- **Reason:** Each is stricter; valid input behaves as specified. `sheet_stale` (Gate 0 sketch A) stops labels landing on a finding set the sheet does not show.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Subcommands refusal cells add the codes above; the `label` row adds "`sheet_stale` when the trial's finding IDs or never-exercised upgrades differ from the sheet". None needed in spec-lite.md.

#### [DEV-006] `blinding:` report line, per-arm evidence fields, and excerpt rules
- **Severity:** Small
- **Spec said:** § Verdict output has no `blinding:` line, though Story 3 Notes require `trial-report.md` to repeat the honor-system caveat. § Schema's example arm entry is `{verdict, keys, states, raw, raw_sha256}`. Sheet excerpts are "the issue block or AC line from the raw output; for Gate 0 also the cited sketch line".
- **Implementation did:** `report` prints `blinding: honor system — …` before `yuss:`; `--json` carries `sample`, `proxy`, and `blinding` without their prefixes. Arm entries add `exercised`, plus `verifier` (safety-fact line 1), `report` (`chose`/`skip`, never the line text), and `kind`/`repro_ac`/`at_parent`/`at_commit`/`repro_result` (repro). `sheet` stores `{path, body_sha256, seed, findings}`. Category-key excerpts include only blocks `parse_output` would key; the Gate 0 excerpt is the issue with its `**Avoided by:**` line, which is the sketch citation as the comparison reviewer wrote it; a no-match excerpt reads `(no matching block found in the raw output)`.
- **Reason:** The report is committed verbatim as `trial-report.md`, so the caveat has to be a report line. The added fields hold words and validated IDs only (AC-2.5).
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Verdict output adds the `blinding:` line; § Schema notes the per-arm evidence fields and the `sheet` object; § Subcommands `sheet` row: "for Gate 0, the issue's `**Avoided by:**` line, which cites the sketch line". None needed in spec-lite.md.

---

## Story 3: Run the Arms and Hand Off for Labeling — Drift Report

> Run: 2026-10-29
> Overall Drift: Medium

### Deviations

#### [DEV-007] Story 3 ran before `2026-10-25-design-divergence` was Complete ⚠️
- **Severity:** Medium
- **Spec said:** Experience Design entry point: "after its three dependencies are complete". Task 3.2: if any dependency is not complete, stop before `init` and report which. AC-3.2 is conditioned on all three passing `is-complete`.
- **Implementation did:** `spec-status.py is-complete` returned `complete: false` for `2026-10-25-design-divergence` (status "In Progress — awaiting blind rating (rating-handoff.md)"; Stories 1-5 done, Story 6 human-gated) and `complete: true` for the other two. The lane ran `init`, every arm, and `sheet` because the Phase 15 orchestrator's lane payload instructed it to: the Gate 0 switch and wiring exist, Gate 0 is not removed, run its arm normally. Gate 0 was measured as shipped. `rating-handoff.md` names the open blind trial and Business Rule 12.
- **Reason:** The precondition exists so the switches are present when the arms run (Cross-Spec Overlap); they were. The ordering is covered by technical-spec § Interaction Edge Cases ("removes Gate 0 after `init` but before Story 4") and Business Rule 12. An explicit stop rule was still overridden, on the orchestrator's instruction rather than a human's.
- **Resolution:** Flagged for review (Medium); PASS.
- **Spec amendment:** None to spec-lite.md. For the owner: task 3.2 could read "stop unless the incomplete dependency's only open story is its own human-gated trial and its switch exists".

#### [DEV-008] Gate 0 comparison `criterion` entries carry `- [ ] Unmet: [AC-N.M]`
- **Severity:** Small
- **Spec said:** The comparison prompt uses the Gate 3 issue format plus `**Avoided by:**`, with no AC checklist.
- **Implementation did:** Each `criterion` entry in `prompts/gate0-comparison.md` ends with one `- [ ] Unmet: [AC-N.M]` line. `parse_output` keys `ac:` findings only from unchecked checklist lines, and keys issues only for the `security` and `architecture` categories, so without it no Gate 0 unmet-criterion finding could key.
- **Reason:** Keeps Gate 0 `ac:` keys reachable with the reused parser (Business Rule 6 counts an unmet criterion as `valid`). There is still no checklist.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Trial Inputs, `gate0-comparison.md` row: append "; a `criterion` entry ends with `- [ ] Unmet: [AC-N.M]` so `parse_output` keys it". None needed in spec-lite.md.

#### [DEV-009] `repro-stop.md` adds `Targets:` and a `Repro: none` form; failing output is indented
- **Severity:** Small
- **Spec said:** `### Repro` reports `Kind:`, `Surface:`, `Command:`, the repro commit, and the failing output.
- **Implementation did:** Adds `Targets: AC-N.M` (feeds `record --repro-ac`) and the skill's `Repro: none: <reason>` form; the failing output is indented four spaces instead of fenced so a `#` line cannot end the section.
- **Reason:** These are the fields `record` needs plus the skill's own no-repro state. No story was a bug fix, so this run used neither.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Trial Inputs, `repro-stop.md` row adds "`Targets:` and a `Repro: none: <reason>` form; failing output indented". None needed in spec-lite.md.

#### [DEV-010] `tests.txt` written by hand for two stories
- **Severity:** Small
- **Spec said:** `tests.txt` holds the story's historical What Was Built test results under `historical, not re-run`; DEV-003 has `prepare` extract the `### Test Results` subsection.
- **Implementation did:** Quick-split story-3 and story-4 record their results under `### Verification` and a "Gate 4 (Testing/Coverage)" paragraph, so `prepare` wrote the placeholder line. The orchestrator replaced those two files (in `$TMPDIR`, never committed) with that text under the same header line, with no `exit code:` line, before any arm ran.
- **Reason:** Business Rule 3 holds: every arm of a story read the same file.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Arms: "When `prepare` finds no `### Test Results` subsection, the lane writes `tests.txt` from the story's What Was Built verification text under the same header line, with no `exit code:` line." None needed in spec-lite.md.

#### [DEV-011] Removal-inventory corrections for Story 4, from the dependency specs' drift logs
- **Severity:** Small
- **Spec said:** technical-spec § Verdict Execution → Removal inventories cites each sibling spec's inventory as written in its spec.md or technical-spec.md, and sets the `implement-story.md` re-pin as the only pin step.
- **Implementation did:** Nothing removed (Story 4 is human-gated). Recorded the amendments the siblings' drift logs make to those inventories, so Story 4 applies the as-built version:
  - `repro-first` (repro-first-bug-fixing DEV-007): the `skills/tdd-cycle/SKILL.md` row also restores the When to Use bug bullet ("reproduce it with a failing test first") that now points at the section, and restores the three-line `parseDate('')` example, not a two-line one.
  - `repro-first` (DEV-012, DEV-013): the `commands/prototype.md` Step 3 and `commands/implement-story.md` Gate 1 `**Bug path:**` lines are longer than the drafts (cherry-pick sentence; base kept across recodes; exit-2 routing); delete them as built.
  - `repro-first` (DEV-010): its growth raised both whole-file caps by 448 bytes: `KNOWN_OVER_BUDGET["commands/implement-story.md"]` in `scripts/tests/test_governor_enforcement.py` and `IMPLEMENT_STORY_CAP` in `scripts/tests/test_review_route_rigor.py`. Any removal re-pins both downward from the values present at Story 4 time (measured at this run: 15717 and 40682; `commands/implement-story.md` is 40,677 bytes), unless both review-route upgrades are removed, which deletes `test_review_route_rigor.py`.
  - `reviewer-filters` (review-route-rigor DEV-005): Clean Removal step 3 also removes `commands/review.md` from the `review-override.py` Callers cell in `.writ/docs/agent-cli-contract.md`.
  - `safety-fact` (review-route-rigor DEV-018): Clean Removal step 5 also deletes the `## Recorded Test Results` prompt block in `agents/review-agent.md`.
  - `safety-fact`, `reviewer-filters` (review-route-rigor DEV-006): each removed skill also decrements the README's "N skills are live today" count (19 at this run); a test pins the count to the Skills table rows.
  - `gate0-divergence` (design-divergence DEV-009): the Gate 0 block is five bold-led paragraphs (`**Design divergence (boundary-crossing route).**`, `**Switch.**`, `**Route.**` with its code block, `**Sketches.**`, `**Choice.**`); the inventory's "block" means all five. `scripts/tests/test_review_override.py` names `gate0-divergence` only as a value `switch` refuses; it is not Gate 0 wiring.
  - Byte measures at this run, for reference only: `commands/retro.md` 19,986 bytes and `commands/refresh-command.md` 23,187 bytes; neither is touched by any removal.
- **Reason:** The pipeline never edits a sibling's spec.md, so the corrections live in drift logs; Story 4 must read them to avoid a partial removal that a wiring test catches or a bullet that points at a deleted heading.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Verdict Execution → Removal inventories: "Apply each inventory as amended by its spec's drift log (see this spec's DEV-011)." None needed in spec-lite.md.

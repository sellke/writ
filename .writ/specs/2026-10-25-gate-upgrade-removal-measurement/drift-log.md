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

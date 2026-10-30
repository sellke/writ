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

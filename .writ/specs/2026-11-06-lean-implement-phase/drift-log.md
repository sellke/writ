# Drift Log

> Spec: .writ/specs/2026-11-06-lean-implement-phase/
> Created: 2026-11-07
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: UAT plans on request — Drift Report

> Run: 2026-11-07
> Overall Drift: Small

### Deviations

#### [DEV-001] c2 skips only on an explicit `false`, not on any falsy value
- **Severity:** Small
- **Spec said:** technical-spec.md § c2 predicate: `uat_requested = state.get("uatRequested", True); if not uat_requested: return met`.
- **Implementation did:** `if state.get("uatRequested", True) is False`; `null`, `0`, `""` or `"false"` check plans.
- **Reason:** The stricter direction: an odd value never turns a promised plan into `met`. `init` writes only a bool.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: c2 skips plan checks only on an explicit `false`.

#### [DEV-002] Handoff lines are printed per merged spec, not per spec that needs a person
- **Severity:** Small
- **Spec said:** Contract Experience Design, happy path: "one `/create-uat-plan {spec}` line for each spec that needs a person to validate it."
- **Implementation did:** The Invocation row, the Step 4.2 example and Completion item 2 print one line per merged spec.
- **Reason:** The orchestrator has no per-spec "needs a person" signal; a superset leaves no spec out.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Review Agents → Experience Design: one `/create-uat-plan {spec}` line per merged spec.

---

## Story 2: Health counts given sources; Goal emit leaves the phase — Drift Report

> Run: 2026-11-07
> Overall Drift: Small

### Deviations

#### [DEV-003] `--drift` repeatable with an unstated aggregation rule
- **Severity:** Small
- **Spec said:** technical-spec.md `health` sources table: one row per flag state; Step 4.1c passes `--drift` for each merged spec's drift log. It does not say how several logs combine.
- **Implementation did:** `--drift` is `action="append"`. The source is `material` if any log is material, else `missing` if any passed log is absent, else `none`; each missing log adds `drift log` to `unavailable`.
- **Reason:** Step 4.1c needs one flag per merged spec; the old CLI kept only the last. Single-flag callers are unaffected.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: `--drift` repeats, with the aggregation rule.

---

## Story 3: Lane result file and shipped brief template — Drift Report

> Run: 2026-11-07
> Overall Drift: Medium

### Deviations

#### [DEV-004] ⚠️ `commands` leanness metric counts invocable commands only
- **Severity:** Medium
- **Spec said:** Nothing; the spec does not mention `scripts/eval-leanness.py` or `MAX_COMMANDS`.
- **Implementation did:** `compute_metrics` counts non-underscore command files, so `_preamble.md` and `_lane-brief.md` no longer count against `MAX_COMMANDS = 35` (count 34); their bytes still count in `per_surface`. `test_eval_leanness.sh` pins the new rule.
- **Reason:** The spec-mandated `commands/_lane-brief.md` took the count to 36 and failed `test_the_real_roster_is_under_the_cap_with_headroom`. The maintainer chose this option over moving the template or raising the cap (AskQuestion, 2026-11-07).
- **Resolution:** ⚠️ Logged (Medium), PASS. Maintainer-approved.
- **Spec amendment:** None.

#### [DEV-005] Plugin generator excludes every underscore partial, not a listed one
- **Severity:** Small
- **Spec said:** technical-spec.md → Lane result file: "If either skips underscore files other than `_preamble.md`, add it to their lists in this story."
- **Implementation did:** `gen-platform-trees.py` uses `is_partial(stem)` (any `_` prefix) for the plugin manifest filter and the link rewrite; `test_plugin_distribution.py` helpers match.
- **Reason:** Same intent as a list entry, as a rule; a future partial needs no generator edit.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: every underscore file in `commands/` is a partial.

#### [DEV-006] `validate-result` gains `result_missing` and `invalid_result` blocker codes
- **Severity:** Small
- **Spec said:** "`validate-result --input` already takes a path; no new subcommand." No blocker named for a missing file.
- **Implementation did:** No new subcommand. A missing file returns blocker `result_missing`; non-JSON or a non-object returns `invalid_result` (previously a traceback).
- **Reason:** Makes Step 3.2's resume-once branch detectable by code.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: the two blocker codes.

---

## Story 3: Post-review supervisor input and adapter wording — Drift Report

> Run: 2026-11-07
> Overall Drift: Small

### Deviations

#### [DEV-007] The supervisor gets the result file's contents, not its path
- **Severity:** Small
- **Spec said:** technical-spec.md → Lane result file: "The supervisor gets the file path in place of the verbatim report"; task 3.4: "supervisor gets the file path".
- **Implementation did:** Step 3.2 item 3 passes `report` = the contents of `{result_path}` (the lane's whole report, verbatim). Applied by the orchestrator after Gate 3, from reviewer recommendation 1.
- **Reason:** `agents/supervisor-agent.md` defines `report` as the verbatim report; passing the contents keeps that input and the agent file unchanged (Business Rule 8), while passing a path would change the supervisor's input. The supervisor escalated the unlogged change; the maintainer accepted it (AskQuestion, 2026-11-07).
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: the supervisor gets the result file's contents.

#### [DEV-008] Adapters updated to describe the lane result file
- **Severity:** Small
- **Spec said:** Story 3's tasks name no adapter file; the reviewer suggested updating the adapters in Story 4 or a follow-up.
- **Implementation did:** `adapters/claude-code.md`, `adapters/codex.md`, `adapters/cursor.md` now say the lane writes its `phase-spec-result-v1` to the brief's result file and the parent validates it with `validate-result --input`; `claude-code.md` notes the result file as the one write outside the lane worktree. Applied by the orchestrator after Gate 3; no Gate 3 re-review.
- **Reason:** Without it the adapters contradict Step 3.2. Wording only. The supervisor escalated the unlogged change; the maintainer accepted it (AskQuestion, 2026-11-07).
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: the adapters' lane-result wording.

---

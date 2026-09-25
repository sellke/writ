# Drift Log

> Spec: .writ/specs/2026-09-24-flagged-harness-cuts/
> Created: 2026-09-25
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Flag substrate — Drift Report

> Run: 2026-09-25
> Overall Drift: Small

### Deviations

#### [DEV-001] Existing loader warnings name the file actually loaded
- **Severity:** Small
- **Spec said:** Nothing about the hoisted, unresolved, and double-load warning text.
- **Implementation did:** Those warnings use the resolved path instead of a hard-coded `commands/<stem>.md`. Flag off, the text is identical (floor hash unchanged).
- **Reason:** Flag-on warnings should point at the lean file that was parsed.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach says loader warnings name the file actually loaded.

#### [DEV-002] Missing-sibling warnings limited to the five in-scope siblings
- **Severity:** Small
- **Spec said:** AC-1.4 warns when a "required lean sibling" is missing.
- **Implementation did:** `LEAN_SIBLINGS` names `_preamble`, `create-spec`, `verify-spec`, `implement-phase`, `implement-story`. Other commands fall back to their default without a warning.
- **Reason:** Matches the spec's scope list. Adding a sibling later means updating the constant.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach lists the five siblings that warn.

Prior spec-lite SHA-256: `3601348474ec4c70b22faebac2dc71c60cd47a55846a3c74570036b708bd8b87`

---

## Story 2: Lean preamble — Drift Report

> Run: 2026-09-25
> Overall Drift: Small

### Deviations

#### [DEV-003] One dropped rule is a product rule, not a restatement
- **Severity:** Small
- **Spec said:** The lean preamble drops sentences that restate `system-instructions.md` on Plan Mode / `--recommend`.
- **Implementation did:** Dropped the whole section, including "validates its invocation matrix before mutation", which `system-instructions.md` does not carry and `implement-phase.md` does not state.
- **Reason:** Not a protected class (exit criteria, gates, production boundary, User Challenge, stakes triage). Routed to Story 4: `implement-phase.lean.md` states the rule.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach names where the generalized rules live under the flag.

#### [DEV-004] "Never offer to code" relies on per-command Terminal constraints
- **Severity:** Small
- **Spec said:** Drop only restatements of `system-instructions.md`.
- **Implementation did:** The sentence is not in `system-instructions.md`; every planning command's Terminal constraint says it.
- **Reason:** Covered while lean command bodies keep their Terminal constraint lines (Story 4 asserts it).
- **Resolution:** Auto-amended
- **Spec amendment:** Same spec-lite line as DEV-003.

Prior spec-lite SHA-256: `a52cc84aad807358699f81b5492e697a88a66435547d9d0ae1280bb1ef78a80e`

---

## Story 3: Spill to file — Drift Report

> Run: 2026-09-25
> Overall Drift: Small

### Deviations

#### [DEV-005] Spill filename uses the story file stem
- **Severity:** Small
- **Spec said:** `.writ/state/story-context-spill-<story-id>.md`
- **Implementation did:** `story-context-spill-<story-file-stem>.md`, e.g. `story-context-spill-story-3-spill-to-file.md`.
- **Reason:** Unique per story within a spec; two specs sharing a stem would overwrite ephemeral state only.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach names the stem.

#### [DEV-006] Inline total can exceed the budget by up to 500 bytes under spill
- **Severity:** Small
- **Spec said:** The cut category carries a tail of at most 500 bytes.
- **Implementation did:** The tail replaces the budget-fitted prefix, so `bytes.total` can exceed `budget_bytes` by at most 500, only with the flag on.
- **Reason:** The tail ceiling stays hard; the overshoot is bounded and documented.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach states the bound.

#### [DEV-007] `--state-dir` CLI flag and `state_dir` parameter
- **Severity:** Small
- **Spec said:** Spill goes under `.writ/state/`.
- **Implementation did:** Default `<repo>/.writ/state`, anchored at the script's location; overridable for hermetic tests.
- **Reason:** Additive; default behavior matches the spec.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach mentions the override.

Prior spec-lite SHA-256: `795d090336f31bf3b9cf1a391a06e42f5d09cc70fe4dd99a26255b51ca3dcd54`

---

## Story 4: Lean command bodies — Drift Report

> Run: 2026-09-25
> Overall Drift: Small

### Deviations

#### [DEV-008] What Was Built spill lives in the lean command, not a lean skill branch
- **Severity:** Small
- **Spec said:** The dependency-context skill's 1,000-line rule gets the same spill branch in its lean text.
- **Implementation did:** `skills/dependency-context-loading/SKILL.md` is byte-identical; `commands/implement-story.lean.md` Step 2 writes `.writ/state/wwb-spill-<story>-<dep>.md` and passes path, size, and a ~20-line tail, with a truncate fallback.
- **Reason:** Story 3's AC-3.4 already named the lean command as the surface. No lean skill sibling is needed.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Files in Scope names the lean command as the spill surface.

#### [DEV-009] eval.sh and eval-leanness.py edited outside the story's listed files
- **Severity:** Small
- **Spec said:** Story 4 authors the four lean bodies plus tests.
- **Implementation did:** `check_manifest`, `all_command_files`, and the MAX_COMMANDS count skip a `*.lean.md` when its default exists. Orphan lean files are still reported.
- **Reason:** Without it the siblings fail the manifest and README checks and push the command count past 35. Default-path reporting is unchanged.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Files in Scope lists the two eval scripts.

Prior spec-lite SHA-256: `197a465504cd15c2dd67db98ac38072dcf91aee6c3573db4fb3628406bcc67f5`

---

## Story 5: Keep or revert — Drift Report

> Run: 2026-09-25
> Overall Drift: Large (user-approved)

### Deviations

#### [DEV-010] Story 5 sample reduced to one story × 2 per arm
- **Severity:** Large
- **Spec said:** Four stories × 2, flag on and flag off, on one current default frontier.
- **Implementation did:** One story × 2 per arm. The decision check can report only null or quality miss on this sample; keep still needs the full sample. Null also stops `install.sh` / `update.sh` from shipping `*.lean.md`.
- **Reason:** Static bound — the prefix cut is under 1% of a run's cache reads against a 59% spread, so the full run cannot show a prefix-driven keep. The reduced run tests the real risk (lean text still completing a story) at a quarter of the cost.
- **Resolution:** Pipeline paused — spec modified by user
- **Spec amendment:** User approved in the `/implement-spec` session on 2026-09-25 ("Do what you think is best"). `spec.md` carries an Amendment section; Story 5 ACs and tasks rewritten, AC IDs unchanged.

#### [DEV-011] Story 5 scripts not listed in spec-lite Files in Scope
- **Severity:** Small
- **Spec said:** spec-lite Files in Scope did not name the baseline and install scripts.
- **Implementation did:** Added `scripts/lean-decision.py`; changed `scripts/pipeline-baseline.py`, `scripts/install.sh`, `scripts/update.sh`.
- **Reason:** Story 5's ACs and tasks name them.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Files in Scope lists them.

#### [DEV-012] install/update skip lean siblings before the decision exists
- **Severity:** Small
- **Spec said:** AC-5.2 ties "not shipped" to a null outcome.
- **Implementation did:** The skip lands before the runs.
- **Reason:** The reduced sample can end only in null or quality miss; both leave the default unflipped. A future full-sample keep revisits it.
- **Resolution:** Auto-amended
- **Spec amendment:** Covered by the same spec-lite Files in Scope line.

#### [DEV-013] Control arm strips an inherited WRIT_HARNESS_LEAN
- **Severity:** Small
- **Spec said:** Task 5.2: the control arm is unchanged.
- **Implementation did:** `driver_env` removes `WRIT_HARNESS_LEAN` from the control driver's env.
- **Reason:** Keeps an operator's exported flag from turning the control into a lean arm.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed beyond the task wording.

Prior spec-lite SHA-256: `8af542aa92f7d673c25d8c9a524048049ad7ceec877d0efee203ec1bb2519614`

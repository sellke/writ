# Governor Instrumentation (Lite)

> Source: .writ/specs/2026-08-11-governor-instrumentation/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Four new checks in `scripts/eval-leanness.py` — contract presence, `## Completion` presence, loop bounds, `required_skills:` resolution — emitting into `warnings` (exit 0), plus the delta-bound `justification` fix and resolution of the four live growth warnings.

**Implementation Approach:**
- Fix the silencer FIRST (Story 1). Today `justification` is read once per *surface* at `eval-leanness.py:527`, outside the per-metric loop, and line 533 (`if current_value <= base_value or justification: continue`) makes any non-empty string skip both `lines` and `chars` forever, at any magnitude. Replace it with `surfaces.<name>.justifications.<metric> = {value, date, text}`: silent only while `current <= value`, warns past it, per metric. Evaluate `current <= base` first and unconditionally — down stays free. `subject` becomes `<surface>.<metric>`. Legacy unbounded `"justification"` strings carry no bound and silence nothing (all six committed ones are `""`, so behavior is unchanged for them). Writer emits `"schema": 3`; reader accepts 2 and 3 — reader first, or the commit fails its own `eval.sh` run at `eval-leanness.py:510`. `--update-baseline` keeps resetting (`"justifications": {}`) — that reset was never the bug.
- Then clear the four live growth warnings (Story 2 gates Stories 3–6): record bound justifications naming `a5c5a66` / PR #34 / v0.28.0 at the post-Story-1 measurements. Do not move the floor, do not run `--update-baseline`, do not add an `absorbed` array — it is dropped as redundant with `justifications`.
- Add ONE constant `CONTRACT_CHECK_SEVERITY = "warnings"` and ONE router `emit_contract_findings()`. Every check is a pure function returning `list[dict]` of `{subject, what, fix}`; no check appends to `structural`/`warnings` itself.
- Reuse `is_infra()` / `command_names()` for the 31-vs-32 command split (`_preamble.md` is infra).
- Agent config carrier is dual: `## Agent Configuration` (plain fence, 6 agents) or `## Agent Specification` (```yaml fence, `visual-qa-agent.md` only).
- `check_parity`, `check_coverage`, and `check_ceilings` are untouched. `check_baseline` changes only as Story 1 specifies.

**Files in Scope:**
- `scripts/eval-leanness.py` — Story 1's `justified_ceiling()` + rewritten `check_baseline()` loop, schema 2/3 reader, schema-3 writer, corrected remediation string; then 4 new `check_*` functions, the severity constant, the router, `contract_compliance` + `required_skills_declarations` metrics.
- `.writ/leanness-baseline.json` — `schema: 3`, legacy `justification` keys removed, bound `justifications` on `commands` and `scripts`; baseline `lines`/`chars` unchanged.
- `scripts/tests/test_eval_leanness.sh` and a new `scripts/tests/test_eval_leanness_contract.py` (importlib-by-path recipe, same as `test_archive_sweep.py`).

**Error Handling:**
- Unparseable frontmatter / missing config block → a finding naming that file, never an exception.
- Missing `commands/` or `agents/` directory → zero findings (existing `surface_files()` behavior), never a crash.
- `required_skills:` unresolved names → `warnings` always, even post-flip (`system-instructions.md` graceful degradation).
- Script always exits 0; `eval.sh` decides FAIL from `structural` only.

**Integration Points:** `scripts/eval.sh check_leanness` (consumes `structural` → FAIL, `warnings` → note); `.writ/leanness-baseline.json`; the later `governor-enforcement` spec, which flips one string.

---

## For Review Agents

**Acceptance Criteria:**
0. After Story 1: grow → warns; justify to X → silent; grow past X → warns naming X; shrink → silent regardless. A justification for `lines` never silences `chars`. Story 1 clears nothing — the same four `(surface, metric)` pairs still warn.
1. After Story 2, `python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json` returns `warnings: []` and `structural: []`.
2. Each new check's findings name an exact file + field (`commands/status.md → problem:`), never an aggregate surface.
3. Flipping `CONTRACT_CHECK_SEVERITY` to `"structural"` moves the identical findings into `structural` and makes `eval.sh` FAIL — with no edit to any check function.
4. `required_skills:` findings stay in `warnings` after the flip.
5. Zero command or agent files are modified — this spec builds the instrument, not the migration.

**Business Rules:**
- No new warning emitted while any of the four existing growth warnings is live (Rule 1).
- Every finding names the exact file + field it asserts (Rule 2).
- Flip is one named constant + one router, verified by a test that throws it (Rule 3).
- Checks read the surface, never modify it — no `--fix` (Rule 4).
- Both agent config-block carriers handled; a false finding against `visual-qa-agent.md` is a failure (Rule 5).
- `required_skills:` warns, never hard-fails, even post-flip (Rule 6).
- `_preamble.md` excluded via existing `is_infra()`, not a new skip list — 31 commands (Rule 7).
- A vacuous check reports its declaration count so "0 findings" ≠ "0 checked" (Rule 8).
- A justification is bound to a recorded value, per metric, or it silences nothing; each story raises its own ceiling, dated (Rule 9).

**Expected day-one output (the true measurement, not a defect):** 114 contract findings (31 commands × 3 + 7 agents × 3), 18 `## Completion` findings, 10 loop-bound findings, 0 `required_skills:` findings.

---

## For Testing Agents

**Success Criteria:**
1. The silencer is delta-bound and per-metric before anything else lands; then the four live growth warnings are cleared and provably attributable (commit `a5c5a66` / PR #34 / v0.28.0) before any new check lands.
2. All four checks emit into `warnings`; `eval.sh` still exits 0 on the current surface.
3. The flip test proves the seam: one constant changed in-process → findings become blocking.
4. Every finding is individually addressable; no aggregate findings exist.
5. Metrics expose `contract_compliance` counts and `required_skills_declarations`.

**Shadow Paths to Verify:**
- **Happy path:** compliant fixture command/agent → zero findings.
- **Nil input:** `commands/`, `agents/`, or `skills/` absent → zero findings, no exception.
- **Empty input:** frontmatter present but `exit_criteria:` empty/`[]` → finding, not a silent pass.
- **Upstream error:** malformed YAML frontmatter → finding naming the file, never a traceback.

**Edge Cases:**
- `commands/_preamble.md` → never checked (infra prefix).
- `agents/visual-qa-agent.md` → `## Agent Specification` + ```yaml fence recognized; no false finding.
- `## Completion Criteria` / `### Completion` → do not satisfy Check 2; finding text names the exact required heading.
- `required_skills:` declaring a real skill → resolves silently; declaring `no-such-skill` → warning, exit 0.
- Duplicate `required_skills:` entries → deduplicated per `system-instructions.md`, one finding max.
- Justification `value` non-numeric, `text` blank, `value` ≤ baseline, or `justifications` not a dict → warns, never silences, never raises.
- Legacy non-empty `"justification"` string → warns, `fix` names the bound replacement. Legacy `""` → identical behavior to today.
- Schema 2 baseline read after Story 1 → accepted, `structural: []`; schema 1 / no `surfaces` → still structural.

**Coverage Requirements:**
- New code: ≥80%
- Emission seam and severity routing: 100%
- Error paths (malformed frontmatter, missing carrier, missing directory): 100%

**Test Strategy:**
- New `scripts/tests/test_eval_leanness_contract.py` — importlib-by-path load of `eval-leanness.py`, fixture command/agent/skill trees per check, plus the constant-flip test.
- Extend `scripts/tests/test_eval_leanness.sh` with a CLI-boundary scenario asserting `structural == []` and exit 0 against the real repo.
- Story 1's bound-justification matrix (16 rows) is the first thing written; it is the regression guard against reintroducing the per-surface mute.
- Story 2 verification is a real run against this repo, not a fixture: `warnings` must be `[]`.

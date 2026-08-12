# Governor Enforcement (Lite)

> Source: .writ/specs/2026-08-12-governor-enforcement/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Flip the four component-contract checks from `warnings` to `structural`, land an absolute per-invocation byte cap as **blocking**, retire the `check_length` command limit that never could bind.

**SCOPE ADDED 2026-08-12 (mechanism ruling).** `2026-08-12-disclosure-implement-phase` escalated that `required_skills:` is an **eager** pre-load — the harness loads every declared skill *"before any phase work begins"* (`system-instructions.md` § Harness contract; `adapters/claude-code.md:396`), so extraction under it makes a command cost **more** than the monolith. Verified and accepted: all six disclosure specs switch to inline `Read skills/<name>/SKILL.md`; `required_skills:` is **retired for this phase**. `measure-invocation.py` was fixed in `e8f2a09` (`floor = base + command + eager`, `ceiling = floor + inline`). Three consequences land here: **(1)** Story 4's gate gains a second condition — *no command declares `required_skills:`*; a stray declaration converts a conditional load into an eager one **without changing any command's byte count**, so assertion 1 cannot catch it, and it invalidates every ceiling the six disclosure specs certified. **(2)** `MAX_SKILLS` is now owned here (new Story 7) — five sibling specs flagged it and none could take it, because every disclosure spec bars itself from `scripts/`. **(3)** `system-instructions.md:252`'s `Status: adopted` claim is now false and is corrected here (Story 7); no other spec owns that file. Full record: spec.md → ## Approved Scope Changes. **Everything else is unchanged** — METRIC bridge first, cap appended to `structural` directly, budget pinned not derived, no exemption reader, mutation proof, and the two-tests-pass-for-the-wrong-reason finding.

**Budget:** `COMMAND_BYTE_BUDGET = 24960` — the irreducible shared base (`system-instructions.md` 20,153 + `commands/_preamble.md` 4,807, measured 2026-08-12). A command may not cost more to load than the contract it runs inside. Selects exactly ADR-021's top-6; a 400-line cap selects 10 and misses `implement-phase` (321 lines / 29,136 bytes). Bytes-per-line varies 2.63x (34.5–90.8).

**Implementation Approach:**
- **Story 1 first — the METRIC bridge.** `contract_compliance` / `required_skills_declarations` reach `eval-leanness.py`'s JSON but never the report: `scripts/eval.sh:2828-2847` prints a fixed METRIC set with branches for `per_surface` and `story_context_bytes` only. Add a branch per key; leave the legacy first `METRIC` line byte-identical. Blocking a gate whose coverage number is unreadable is the reason this lands first.
- **Story 2 — the cap.** Pinned constant, not derived live (live derivation lets base growth raise every allowance = ADR-021 reason 3 rebuilt). Binds on `command_bytes` only. Appends to `structural` **directly** — never via `emit_contract_findings()` / `CONTRACT_CHECK_SEVERITY`, or a future un-flip disables the budget too. Reuse `measure-invocation.py`'s accounting (`base.bytes`, `command_bytes`, `floor_bytes`, `ceiling_bytes`); a test asserts the two agree. `is_infra()` excludes `_preamble.md`. Report `per_command_invocation` in metrics so ADR-021 caveat 2 is visible.
- **Story 3 — the line limit.** Only `scripts/eval.sh:423` (`-gt 2000`). Read the **landed** ADR-021 amendment (owned by `2026-08-12-disclosure-implement-story` Story 1) and enforce it; if absent, HALT. As specified it demotes 400 lines to a *"secondary, non-binding tripwire"* under the byte budget — expected shape `-gt 2000` → `-gt 400`, `add_finding` → `add_note`; verify against the landed text, not this paraphrase. Do **not** touch line 404 (`spec-lite`, `-gt 100`) or line 412 (`_preamble`, `-gt 95`) — 8 and 11 lines away, owned by `2026-08-11-autonomy-gate-classes`.
- **Story 4 — the gate.** A committed test against the **real repo**, **four** assertions: every non-infra command ≤ 24,960; `structural: []` under both shipped and in-process-`"structural"` severity; `contract_compliance` saturated; **`required_skills_declarations == 0`**, cross-checked by a direct frontmatter grep so a parser change cannot make it vacuous. Red → the spec halts and reports which files are over by how much. Story 5 never starts.
- **Story 5 — the flip.** One string at `scripts/eval-leanness.py:278`. Plus five inverted tests and two broken anchors (below). Rewrite the handoff comment; drop the `# -> "structural"` marker.
- **Story 6 — mutation proof.** Break each gated property on a scratch copy, assert red, revert, assert green.
- **Story 7 — `MAX_SKILLS` + the `required_skills:` record. LAST, deliberately.** `MAX_SKILLS = 12` → **45**, derived as `MAX_COMMANDS + MAX_AGENTS` (35 + 10) — *never* fitted to the post-phase count of 35, which is the "cap raised to fit content" failure `2026-08-11-autonomy-gate-classes` BR1 bans. **Stays warn-only** (a count is not a unit of load — ADR-021's own finding, and Story 3 retires a line limit for exactly that reason; bytes are already governed by ADR-019's ratchet). Also corrects `system-instructions.md:252` and restores its review trigger. **It is last because it edits `system-instructions.md` — 20,153 of the 24,960 budget derivation — so this spec trips its own `check_budget_derivation()` finding. `COMMAND_BYTE_BUDGET` is NOT re-derived**; Story 4's gate is re-run to confirm nothing certified moved.

**Files in Scope (widened 2026-08-12; this spec owns these and nothing else):**
- `scripts/eval.sh` — the METRIC bridge (~2828-2847) and the command limit at line 423.
- `scripts/eval-leanness.py` — `CONTRACT_CHECK_SEVERITY` (line 278), the new cap, `per_command_invocation` metrics, **and `MAX_SKILLS` (line 71) — added 2026-08-12**. `MAX_COMMANDS`, `MAX_AGENTS`, and `check_ceilings()`'s body stay byte-identical.
- **`system-instructions.md` — the `required_skills:` status paragraph only (line ~252), added 2026-08-12.** The schema itself is unchanged. **Not** `adapters/*` (same false claim in three files — recorded, not taken) and **not** `.writ/product/roadmap.md`.
- `.writ/leanness-baseline.json` — only if a story's own growth passes a recorded ceiling.
- `scripts/tests/test_eval_leanness_contract.py` and a new cap/gate test file.

**Error Handling:**
- Unreadable command file → a finding naming it, never an exception.
- Missing `commands/` → zero findings (existing `all_command_files()` behavior).
- `eval-leanness.py` always exits 0; `eval.sh` decides FAIL from `structural`.
- Base drift (`base.bytes != 24960`) → non-blocking finding, never a silent allowance change.

**Integration Points:** `eval.sh check_leanness`; `measure-invocation.py` (loads `eval-leanness.py` by path — dependency runs measure→leanness, never reversed); `eval-loop-bounds.py`'s `governor-boundary-intact` (`:539-555`, cross-reads `eval-leanness.py` for the literal `check_loop_bounds` — keep it passing and assert it).

---

## For Review Agents

**Acceptance Criteria:**
1. The eval report renders `contract_compliance` and `required_skills_declarations`; the legacy first `METRIC` line is unchanged.
2. A command over 24,960 bytes produces a `structural` finding naming the file, its bytes, the budget, and the overage — and `eval.sh` FAILs.
3. That finding survives a bound justification planted in `.writ/leanness-baseline.json` naming the same surface.
4. `scripts/eval.sh` lines 404 and 412 are byte-identical to their pre-spec state.
5. The pre-flip gate test asserts against the real repo, is green before Story 5, and stays in the suite after.
6. `CONTRACT_CHECK_SEVERITY == "structural"` as committed, asserted by a test.
6b. `MAX_SKILLS == 45` as committed with its derivation recorded at the constant, a test asserting the count is below it, and `MAX_COMMANDS` / `MAX_AGENTS` / `check_ceilings()` byte-identical; `system-instructions.md` no longer claims Phase 10 as `required_skills:`'s first consumer, the schema unchanged, the review trigger restored with a date and terms; `COMMAND_BYTE_BUDGET` unchanged after Story 7's base edit, `check_budget_derivation()`'s finding quoted as observed, and Story 4's gate re-run green.
7. `bash scripts/eval.sh` exits 0 on a clean tree and non-zero on each mutated property.
8. No `eval-exempt:` marker appears anywhere in this spec's diff.

**Business Rules:**
1. No exemption to make the flip possible — `eval-leanness.py` gains no exemption reader at all.
2. The flip is gated on measured compliance, and the gate is a committed assertion, not a pre-flight ritual.
3. An absolute cap is not silenceable by a justification — a justification explains growth against a *baseline*, never against an *absolute budget*.
4. Every new blocking finding names the exact file and field, so a red gate is a work queue rather than a wall.
5. The budget is a pinned absolute whose derivation is itself checked — base drift is a finding, not a raise.
6. A tripwire that fires on a compliant surface is not a tripwire; land the amendment's value, record the firing, escalate.
7. The `_preamble` (95) and `spec-lite` (100) limits are untouched.
8. `MAX_SKILLS` is re-derived from a rule, never fitted to a count. Three tests: computed from constants that exist for other reasons; **can still fire** (35 against 45 leaves 10 headroom); moves only when its inputs move. The counterfactual is the proof — had the roster landed at 50, the cap would fire and the answer would be a Tier B escalation, not a bigger number.

**Verified pre-state (2026-08-12, re-measure before trusting):** `eval-leanness.py` returns `structural: []`, `warnings: []`; `contract_compliance` saturated at 31/31 commands, 31/31 completion, 5/5 loops, 7/7 agents; `required_skills_declarations: 0` — **and after the mechanism ruling that 0 is permanent by design, not transient**. `metrics.skills` 6 today; post-phase 35 (implement-story 8, create-spec 5, release 5, verify-spec 4, ship 4, implement-phase 3 = 29 new). Note `2026-08-12-disclosure-ship` states *"at least 29"* as a **total** — it undercounts two specs and omits `verify-spec`; the total is **35**. Six commands over budget by 67,578 bytes total. Largest command is 989 lines against a 2000-line limit — 2.02x out of reach.

---

## For Testing Agents

**Success Criteria:**
1. Compliance is *measured* before the flip, by a committed test against the real repo — **all four assertions**, including `required_skills_declarations == 0`.
2. The cap fails; it does not warn, and nothing silences it.
3. The gate is proven red-on-regression by mutation, not by fixture inference.
4. `governor-boundary-intact` still passes, asserted rather than assumed.
5. `MAX_SKILLS` is raised by a **derivation** that can still fire — a test names the committed value and asserts the count is below it.

**Five tests break on the flip (verified by mutation 2026-08-12 — 81 tests, 5 failures). Invert, do not delete:**
`FlipSeamTests.test_shipped_default_is_warnings`, `.test_default_routes_everything_non_blocking`, `.test_flip_moves_the_identical_dicts_to_structural`, `.test_main_exits_zero_and_stays_non_blocking_on_a_noncompliant_root`, `EvalShBoundaryTests.test_shipped_severity_passes_the_gate_on_the_same_tree`.

**Two tests pass for the WRONG reason after the flip — the more dangerous finding.** `test_the_constant_carries_its_handoff_comment` partitions on the literal `CONTRACT_CHECK_SEVERITY = "warnings"`, which survives the flip inside the handoff comment's diff preview at `eval-leanness.py:276`, so it matches the documentation instead of the statement. `EvalShBoundaryTests._run_leanness_check` shares the anchor: its `replace()` becomes a no-op and its `assertIn` passes trivially. Instrumentation Story 7 recorded this trap and defended one direction only. Re-anchor both; verify each still fails when its property is broken.

**Shadow Paths to Verify:**
- **Happy path:** compliant tree → `structural: []`, exit 0.
- **Nil input:** `commands/` absent → zero findings, no exception.
- **Empty input:** zero-byte command file → under budget, no finding, no divide-by-zero.
- **Upstream error:** unreadable command file → a finding naming it, never a traceback.

**Edge Cases:**
- **`required_skills_declarations` is permanently 0** post-ruling — nothing to resolve indefinitely, not transiently. Story 1 reports it, Story 4 asserts it, Story 7 corrects the sentence that predicted otherwise. Not a defect; do not "fix" it by removing the metric. Relatedly, **an inline `Read skills/<n>/SKILL.md` naming a missing skill produces NO finding** — `check_required_skills()` resolves frontmatter only (`eval-leanness.py:712`); `measure-invocation.py` catches it but always exits 0. Out of scope here, and the most consequential gap the ruling opened.
- **`MAX_SKILLS` crossed → warning, never blocking**, by decision and not omission (bytes are the blocking instrument for the skills surface: ADR-019 ratchet + bound justifications). **Story 7 trips this spec's own `check_budget_derivation()`** by editing `system-instructions.md` (20,153 of the 24,960 derivation) — expected, recorded, and **`COMMAND_BYTE_BUDGET` stays 24,960**.
- `plan-product.md` at 24,753 bytes — 207 under budget, the likeliest near-miss; must not fire.
- Exactly 24,960 bytes → compliant (`>` not `>=`), asserted explicitly.
- `_preamble.md` → never checked, via `is_infra()`, no hardcoded filename.
- Justification planted against an over-budget surface → cap still fails.
- `base.bytes != COMMAND_BYTE_BUDGET` → non-blocking drift finding, budget unchanged.
- Unrecognised `CONTRACT_CHECK_SEVERITY` → still falls back to `warnings`; the cap stays blocking regardless.

**Coverage Requirements:** new code ≥80%; the cap's severity path and the pre-flip gate 100%; error paths (unreadable file, missing directory, base drift) 100%.

**Test Strategy:** extend `scripts/tests/test_eval_leanness_contract.py` for the inverted seam tests; new test file for the cap, the base-drift check, and the real-repo pre-flip gate (importlib-by-path recipe, as `test_archive_sweep.py`). Story 6's mutations run on a scratch copy or fixture root — never the committed tree — and exit on a clean `git status`.

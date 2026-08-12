# Autonomy Gate Classes (Lite)

> Source: .writ/specs/2026-08-11-autonomy-gate-classes/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** ADR-022's five-row gate-class table plus the reversibility precondition, recorded in `commands/_preamble.md`, and the `check_length` `_preamble` cap raised 80 → 95.

**Implementation Approach:**
- Story 1: `scripts/eval.sh:411-412` — `-gt 80` → `-gt 95` and the finding message `limit 80` → `limit 95`. Add a regression test proving a 96-line `_preamble.md` still fails.
- Story 2: author `## Autonomy Gate Classes` into `commands/_preamble.md` within a **14-line budget** (79 + 14 + 2 reserve = 95). Place it adjacent to the `User Challenge` section, where ADR-013's boundary already lives.
- Story 3: read-only applicability pass over `/revert`, `/refactor`, `/uninstall-writ`, `/reinstall-writ` — record whether an agent can actually evaluate both precondition conditions. No edits.

**Files in Scope:**
- `scripts/eval.sh` — lines 411-412 **only**. The `-gt 2000` command limit (line 422) and `-gt 100` spec-lite limit (line 403) are out of bounds.
- `commands/_preamble.md` — one new section, ≤14 lines added, final file ≤95 lines, no `eval-exempt:` marker.
- New test file for the cap regression (shell, following `scripts/tests/test_eval_leanness.sh`'s shape).

**Test harness note:** `scripts/eval.sh` derives `PROJECT_ROOT` from its own location (line 13). Copy it into a temp `scripts/` dir beside a synthetic `commands/_preamble.md` and run `--check=length`. Verified pre-change: 96 lines → exit 1, 80 lines → exit 0.

**Error Handling:** none — this is a constant change plus markdown content. The failure mode is silent non-enforcement, which Story 1's test exists to prevent.

**Integration Points:** `scripts/eval.sh check_length` (CI Tier 1 gate); `commands/_preamble.md` (loaded by all 31 commands); ADR-013's select-or-pause boundary already stated in the preamble's `User Challenge` section.

---

## For Review Agents

**Acceptance Criteria:**
1. `bash scripts/eval.sh --check=length` exits 0 with `_preamble.md` ≤95 lines.
2. A 96-line fixture `_preamble.md` yields a blocking finding `96 lines (limit 95).` and non-zero exit; 95 lines exits 0.
3. `git diff scripts/eval.sh` touches only the two `_preamble` lines — `-gt 2000` and `-gt 100` byte-identical.
4. `_preamble.md` carries all five ADR-022 class rows and both precondition conditions in normative wording; no `eval-exempt:` marker.

**Business Rules:**
- Cap comes from a stated budget (79 + 14 + 2 = 95), never from what the content measures. Over budget → cut prose, don't raise again (Rule 1).
- The cap must still bind, proven by test (Rule 2).
- One constant only; the adjacent command limit belongs to `governor-enforcement` (Rule 3).
- No length exemption on `_preamble.md` — it removes the cap rather than resizing it (Rule 4).
- Precondition is normative: "only when both hold", "pauses". Never "should"/"consider" (Rule 5).
- Extends ADR-013, never weakens it — no autonomous merge/PR/release/tag, audit rationale retained (Rule 6).
- The recorded dissent stays recorded; no artifact may present the destructive-class decision as uncontested (Rule 7).
- Table faithful to ADR-022: five rows, same names, same behaviors; compression yes, meaning change no (Rule 8).
- No command file edits — Story 3 is read-only (Rule 9).

**The one thing to catch in review:** raising a cap to fit content is how caps stop binding. Phase 10's roadmap already documents the end state — a 2000-line command limit against a 961-line worst offender that can never fire. Verify the budget was set *before* the content was written, and that the test proves 96 still fails.

---

## For Testing Agents

**Success Criteria:**
1. 95-line `_preamble.md` fixture → `--check=length` exits 0.
2. 96-line fixture → exit 1 with `limit 95` in the finding.
3. Real `commands/_preamble.md` post-Story-2 → full `bash scripts/eval.sh` produces no new findings vs. baseline.
4. `scripts/eval.sh` diff confined to lines 411-412.

**Shadow Paths to Verify:**
- **Happy path:** preamble at 93-95 lines, check passes.
- **Boundary:** exactly 95 passes, exactly 96 fails (the check is `-gt`, so 95 is legal).
- **Exemption path:** a fixture `_preamble.md` carrying `eval-exempt: length` skips the check entirely — assert the real file does *not* carry one.
- **Adjacent-limit regression:** a fixture command file of 2001 lines still fails at `limit 2000`; a 101-line `spec-lite.md` still fails at `limit 100`.

**Edge Cases:**
- Missing `commands/_preamble.md` → check silently skips (`[ -f "$file" ]` guard). Not a regression; note it, don't fix it here.
- Trailing-newline handling: `line_count` must agree with `wc -l` for the boundary tests to mean anything.

**Coverage Requirements:** the cap constant is one branch — 100% (both sides: ≤95 pass, >95 fail). No other new code paths.

**Test Strategy:** shell test following `scripts/tests/test_eval_leanness.sh`'s shape — build a temp project root (`scripts/eval.sh` copy + synthetic `commands/_preamble.md`), run `--check=length`, assert exit code and finding text. No mocking, no fixtures committed beyond the generator.

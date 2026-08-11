# Loop Bounds (Lite)

> Source: .writ/specs/2026-08-11-loop-bounds/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `loop.max_iterations` + `loop.on_exhaustion` in the YAML frontmatter of the five verified-unbounded loop-bearing commands: `implement-phase`, `implement-spec`, `implement-story`, `refactor`, `verify-spec`. Plus one eval check verifying **correctness** — legal values, honest citation, non-regression against recorded runs, transcription drift. **Presence** is owned by `2026-08-11-governor-instrumentation` Check 3; this check skips a file with no `loop:` block and reports `deferred_to_check3` rather than duplicating that finding.

**Block shape** (appended to the same `---` block `2026-08-11-component-contract` adds `problem:`/`outcome:`/`exit_criteria:` to):

```yaml
loop:
  unit: "spec"                  # what one iteration counts
  max_iterations: 12            # positive integer literal
  on_exhaustion: halt_reported  # quarantine | escalate | halt_reported
  calibrated_against: "..."     # evidence path + evidence quality
  nested: [...]                 # optional; same 4 keys; one level only
```

**`on_exhaustion` vocabulary — exactly three values:**
- `quarantine` → calls `scripts/phase-state.py quarantine` (existing verb). Legal only where a `phase-execution-*.json` record exists.
- `escalate` → one bounded `AskQuestion` naming loop/bound/count/partial state. Mandatory where continuing would change scope.
- `halt_reported` → stop + write a named record (unit, bound, count, last completed unit, resume command).
- `retry` is **illegal**. Retry is pre-exhaustion, already enforced by `phase-state.py` (`attempts < 2`).

**The five bounds:**

| Command | unit | max | on_exhaustion | Evidence quality |
|---|---|---|---|---|
| `implement-phase` | `spec` | 12 | `halt_reported` | Thin — Phase 9 = 3 specs, Phase 10 = 5 (both state files), Phase 7 = 4 (roadmap only). Max observed 5 |
| ↳ nested | `spec_attempt` | 2 | `quarantine` | Strong — transcribes `phase-state.py` `attempts < 2` |
| `implement-spec` | `story` | 12 | `halt_reported` | Strongest — max of 41 archived specs = 9; 6 recorded runs ≤ 4 |
| `implement-story` | `review_cycle` | 3 | `escalate` | Strong — 42 records: 39×1, 3×2; max observed 2 |
| ↳ nested | `testing_cycle` | 2 | `escalate` | Adequate — transcribes the '2 fix iterations max' prose cap |
| ↳ nested | `agent_self_fix` | 3 | `escalate` | Strong — transcribes `MAX_SELF_FIX_ITERATIONS = 3` |
| `refactor` | `change` | 10 | `halt_reported` | **Weak — zero recorded runs.** Anchor: `refactor.md`'s "7+ changes" advisory |
| `verify-spec` | `autofix_pass` | 1 | `halt_reported` | Strong by construction — single-pass today, no re-check step exists |

**Files in Scope:** `commands/implement-phase.md`, `commands/implement-spec.md`, `commands/implement-story.md`, `commands/refactor.md`, `commands/verify-spec.md` (frontmatter + one prose sentence each); new `scripts/eval-loop-bounds.py`; `scripts/eval.sh` (`--check=loop-bounds` wiring).

**Error Handling:** Malformed/missing `loop:` key → blocking finding naming file + key, never default-and-continue. Declared bound below a recorded run → finding naming the state file and value. `.writ/state/` empty (CI) → explicit `skipped` with reason, never a silent pass. `quarantine` on a command with no phase-state integration → rejected by schema; at runtime fall back to `escalate` and say why.

**Integration Points:** `scripts/phase-state.py` `classify`/`retry`/`quarantine` (reused, never reimplemented); the ADR-020 frontmatter block owned by `2026-08-11-component-contract` (append-only); `scripts/eval.sh` check registry.

---

## For Review Agents

**Acceptance Criteria:**
1. All five commands declare `loop.max_iterations` + `loop.on_exhaustion` + `unit` + `calibrated_against`; `eval.sh --check=loop-bounds` exits 0 with 0 findings and never duplicates a governor Check 3 presence finding.
2. No declared bound is below any value recorded in `.writ/state/` or in any archived story's `Iteration count`.
3. `implement-phase`'s nested `spec_attempt` bound equals `phase-state.py`'s `attempts < 2` guard, read from the script rather than hardcoded.
4. Every `on_exhaustion` path emits unit, bound, count reached, last completed unit, and a literal resume command.

**Business Rules:**
- Every bound cites the run it was calibrated against; `calibrated_against:` is required (Rule 1).
- No bound below the highest observed historical value — rejected, not exempted (Rule 2).
- `on_exhaustion` always yields a named, resumable state; silence is a defect (Rule 3).
- Composes with `phase-state.py`'s retry rule, never widens it; `retry` is not a legal value (Rule 4).
- Exhaustion never degrades scope or self-certifies — ADR-013/ADR-022; `escalate` is the only legal value where continuing changes scope (Rule 5).
- `loop:` is a reserved sibling key in the ADR-020 block and restructures nothing (Rule 6).
- Existing enforced numbers (3, 2, `MAX_SELF_FIX_ITERATIONS = 3`, `attempts < 2`) are transcribed, not re-derived (Rule 7).
- Thin evidence is stated in-file; `refactor` must carry the literal `no recorded run` (Rule 8).

---

## For Testing Agents

**Success Criteria:**
1. Five commands parse with a complete, valid `loop:` block.
2. Historical-run assertion catches a deliberately lowered bound against a fixture `.writ/state/`.
3. `retry` as an `on_exhaustion` value is rejected by name with a reason.
4. Empty `.writ/state/` reports `skipped` with reason, not a pass.
5. `loop:` landing before or after the component-contract keys both validate.

**Shadow Paths to Verify:**
- **Happy:** all five valid → 0 findings.
- **Nil:** a named command file absent → finding naming it, not a crash.
- **Empty:** no state files → assertion 7 skips with a stated reason.
- **Upstream error:** unparseable frontmatter → finding with the parse error.

**Edge Cases:**
- `--all` chains phases: the `spec` counter resets per phase, not across the chain.
- A transient retry must not consume an outer `spec` iteration — nested bound covers it.
- `--quick` skips gates: no separate bound; skipped gates never increment.
- `implement-story` run standalone: all three bounds are `escalate`, need no phase state.
- Progressive disclosure restructures `implement-story`: check reads frontmatter only, never body line numbers.

**Coverage Requirements:** New code ≥80%. Historical-run assertion and the `.writ/state/`-empty skip path: 100%. Every illegal-value rejection: 100%.

**Test Strategy:** Fixture frontmatter blocks per malformation. Fixture `.writ/state/` with a run larger than a declared bound. Cross-read assertions binding `spec_attempt` to `phase-state.py` and the three `implement-story` numbers to their prose/agent sources, so drift on either side fails. Grep guard asserting `commands/verify-spec.md` still has no re-check step.

# UAT Plan: Artifact Integrity + Handshake

> **Generated:** 2026-07-19
> **Spec:** `.writ/specs/2026-07-18-artifact-integrity-handshake/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 16

## How to Use This Plan

1. Work through scenarios in order (grouped by story, ordered by priority).
2. For each scenario, follow the steps exactly as written.
3. Mark Pass or Fail — add notes for any unexpected behavior.
4. Scenarios marked Fail should be filed as issues or fed back to the spec.
5. The feature passes UAT when all scenarios pass (or failures are accepted as known limitations).

> **Note on this methodology repo:** Deliverables are markdown/scripts. Several scenarios are validated by reading command files or running `scripts/eval.sh` rather than exercising a live UI. Where a scenario temporarily renames a required artifact, use a scratch clone or restore immediately afterward.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|------------------|
| Story 1: Artifact Integrity in `_preamble.md` | ✅ Covered | 4 | AC: 3, Edge: 1 |
| Story 2: `context.md` Artifact Map schema | ✅ Covered | 5 | AC: 4, Edge: 1 |
| Story 3: Command declarations + eval | ✅ Covered | 7 | AC: 3, Shadow: 3, Edge: 1 |

---

## Story 1: Artifact Integrity Convention in `_preamble.md`

### Scenario 1: Preamble defines Artifact Integrity convention

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repo checked out on the phase branch (or a branch that includes this spec).

**Steps:**
1. Open `commands/_preamble.md`.
2. Locate the `## Artifact Integrity` section (after File Organization).
3. Confirm it defines the Required Artifacts convention (*required* vs *optional*), check-then-HALT behavior, and bounded repair (name the creating command; no auto-mutation).

**Expected Result:**
- The section is present and covers convention + HALT + bounded repair in plain language.
- Tone matches the rest of the preamble (standing rule, not a manual).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `commands/_preamble.md`

**Notes:**

---

### Scenario 2: Required vs optional behaviors are explicit

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- None.

**Steps:**
1. Read the Artifact Integrity section in `commands/_preamble.md`.
2. Confirm required absence → HALT + repair offer.
3. Confirm optional absence → warn and continue degraded.

**Expected Result:**
- Both behaviors are stated distinctly; only *required* absence halts.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `commands/_preamble.md`

**Notes:**

---

### Scenario 3: Rule is adapter-neutral

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- None.

**Steps:**
1. Read the Artifact Integrity section end-to-end.
2. Confirm it describes pure existence checks with no Cursor/Claude/Codex/OpenClaw-specific hooks.

**Expected Result:**
- Adapter neutrality is explicit; no platform runtime APIs are required.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `commands/_preamble.md`

**Notes:**

---

### Scenario 4: Common artifact → creating-command map is present

**Source:** Edge Case — Story 1

**Preconditions:**
- None.

**Steps:**
1. In `commands/_preamble.md`, find the common artifact → creating-command mapping.
2. Confirm it names at least: product/roadmap → `/plan-product`, foundation docs → `/initialize`, a spec → `/create-spec`.

**Expected Result:**
- Repair offers can name a concrete creating command from this map.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `commands/_preamble.md`

**Notes:**

---

## Story 2: `context.md` Artifact Map Schema

### Scenario 5: Canonical schema includes Artifact Map + Integrity line

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- None.

**Steps:**
1. Open `commands/implement-story.md` and find the Step 2 `context.md` schema.
2. Confirm an `## Artifact Map` section lists Product, Active spec, Knowledge, Docs, and an Integrity line.

**Expected Result:**
- Artifact Map is part of the canonical schema (not a separate file).
- Integrity line template covers ✅ all-present and ⚠️ missing-required forms.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/implement-story.md` (Step 2)

**Notes:**

---

### Scenario 6: Integrity line reports missing required artifacts

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Understanding of the Integrity line wording in the schema.

**Steps:**
1. Read the Integrity line rules in the canonical Artifact Map schema.
2. Confirm missing required artifacts produce `⚠️ missing required: <list>` and all-present produces ✅.

**Expected Result:**
- Both outcomes are specified; the Integrity line always renders.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/implement-story.md`

**Notes:**

---

### Scenario 7: implement-spec and status emit the Map via the canonical schema

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- None.

**Steps:**
1. Open `commands/implement-spec.md` regeneration guidance; confirm it points at the canonical schema including Artifact Map + Integrity (not a divergent copy).
2. Open `commands/status.md` regeneration sources; confirm Artifact Map is listed and references the same canonical schema.

**Expected Result:**
- One canonical definition; two regenerators reference it without duplicating the Map prose.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/implement-spec.md`, `commands/status.md`

**Notes:**

---

### Scenario 8: Graceful degradation for absent optional sources

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- None.

**Steps:**
1. Read the present-conditional / graceful-degradation rules on the Artifact Map schema.
2. Confirm absent optional sub-items are omitted while the Integrity line still renders.

**Expected Result:**
- Map never invents missing optional files; Integrity remains visible.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `commands/implement-story.md`

**Notes:**

---

### Scenario 9: Regenerated context.md contains Artifact Map (live)

**Source:** Edge Case / Experience Design — Story 2

**Preconditions:**
- This repo has a full `.writ/` tree.
- `.writ/context.md` exists (regenerate via `/status` or after a story completion if stale).

**Steps:**
1. Open `.writ/context.md`.
2. Confirm `## Artifact Map` is present with Product / Active spec / Knowledge / Docs / Integrity lines.
3. Confirm there is no `.writ/index.md`.

**Expected Result:**
- Artifact Map is current in the committed snapshot.
- No separate index/pointer file exists.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `.writ/context.md` (regenerated); rejected: `.writ/index.md`

**Notes:**

---

## Story 3: Per-Command Required Artifacts Declarations + Eval

### Scenario 10: All seven high-traffic commands declare Required Artifacts

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- None.

**Steps:**
1. Open each of: `commands/create-spec.md`, `implement-story.md`, `implement-spec.md`, `implement-phase.md`, `ship.md`, `release.md`, `status.md`.
2. Confirm each has a `## Required Artifacts` block marking required vs optional.
3. Confirm each defers HALT/repair behavior to the preamble (does not re-explain it).

**Expected Result:**
- All seven blocks are present and match technical-spec §3 intent (e.g. `implement-phase` requires roadmap; `create-spec`/`status` may require none).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: the seven command files above

**Notes:**

---

### Scenario 11: Eval asserts preamble, declarations, and no index.md

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Shell available at repo root.

**Steps:**
1. Run `bash scripts/eval.sh --check=artifact-integrity`.
2. Confirm exit code 0 and all scenarios passed.
3. Optionally run `python3 scripts/eval-artifact-integrity.py` and confirm 19/19 PASS.

**Expected Result:**
- Check PASS with Findings: 0 for this check.
- Guard confirms `.writ/index.md` is absent.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `scripts/eval.sh`, `scripts/eval-artifact-integrity.py`

**Notes:**

---

### Scenario 12: Happy path — required artifacts present → proceed

**Source:** Shadow Path — Story 3

**Preconditions:**
- This Writ repo has `.writ/product/roadmap.md` and at least one complete spec.

**Steps:**
1. Mentally (or actually) start `/status` or `/implement-phase` against this repo.
2. Confirm Required Artifacts for those commands are present on disk.

**Expected Result:**
- Command proceeds without an integrity HALT (normal Writ behavior on a healthy repo).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: Nil path — required artifact missing → HALT + repair offer

**Source:** Shadow Path — Story 3

**Preconditions:**
- Prefer a scratch clone. Do not leave this repo in a broken state.

**Steps:**
1. Temporarily move aside a *required* artifact for a declaring command (e.g. rename `.writ/product/roadmap.md` before invoking `/implement-phase`).
2. Invoke the command.
3. Observe the early HALT message and repair offer naming the creating command.
4. Restore the artifact immediately.

**Expected Result:**
- HALT is specific (names the missing artifact).
- Repair offer is bounded (names `/plan-product` or equivalent) and does not auto-mutate without confirmation.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Behavior: preamble Artifact Integrity + `commands/implement-phase.md` Required Artifacts

**Notes:**

---

### Scenario 14: Empty/optional path — optional missing → warn + continue

**Source:** Shadow Path — Story 3

**Preconditions:**
- Prefer a scratch clone or a context where `.writ/knowledge/` (or another optional) can be absent safely.

**Steps:**
1. Ensure an *optional* artifact listed by a command is missing (e.g. no `spec-lite.md` for `/implement-story` on a stub).
2. Invoke the command (or read its Required Artifacts + preamble rule and confirm the documented behavior).

**Expected Result:**
- Documented/observed behavior is warn + degraded continue — not HALT.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 15: Repair declined → clean HALT, no mutation

**Source:** Shadow Path / Experience Design — Story 3

**Preconditions:**
- Scenario 13 setup available, or read-only confirmation of the documented rule.

**Steps:**
1. Trigger (or simulate) a required-missing HALT with a repair AskQuestion.
2. Decline the repair.

**Expected Result:**
- Command stops cleanly.
- No mutating repair was applied without confirmation.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1/3 — Files: `commands/_preamble.md` (bounded repair rule)

**Notes:**

---

### Scenario 16: Legacy commands without declarations remain unaffected

**Source:** Edge Case — Story 3

**Preconditions:**
- None.

**Steps:**
1. Pick a command outside the seven (e.g. `commands/verify-spec.md` or `commands/retro.md`).
2. Confirm it has no `## Required Artifacts` block (or is not required to by this spec).
3. Confirm the preamble still applies as standing guidance when authors add declarations later.

**Expected Result:**
- Only the seven high-traffic commands gained declarations; no grab-bag of all ~30 commands.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Sign-Off

| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | [ ] Pass [ ] Fail |
| Reviewer | | | [ ] Pass [ ] Fail |

**Overall UAT:** [ ] Pass  [ ] Fail

**Notes:**

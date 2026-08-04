# UAT Plan: Evidence-Bound /refresh-command

> **Generated:** 2026-07-10
> **Spec:** `.writ/specs/2026-07-10-evidence-bound-refresh-command/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 18

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

All commands assume the repository root `/Users/Adam/Projects/writ` as the working directory. The eval convention is exit `0` = clean, non-zero = findings/run error. Read exit codes with `echo $?`. Several scenarios inspect command/doc prose because `/refresh-command` is a human-driven markdown command, not an automated pipeline.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Evidence-Citation Contract and Drift Reconciliation | ✅ Covered | 6 | AC: 5, Errors: 1 |
| Story 2: Refresh-Evidence Eval Check | ✅ Covered | 6 | AC: 5, Shadow: 1 |
| Story 3: Lightweight Tier 2 and Merge Gate | ✅ Covered | 6 | AC: 5, Errors: 1 |

---

## Story 1: Evidence-Citation Contract and Drift Reconciliation

### Scenario 1: Phase 3 mandates a structured Evidence block per proposal

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/refresh-command.md` and read Phase 3.
2. Confirm every proposal template requires five fields: **Title**, **Rationale**, **Confidence** (H/M/L), **Evidence**, and **Diff**.
3. Confirm the **Evidence** block has three parts: a transcript ID or path, a short observable signal quoted from that transcript, and the affected command file line/section.

**Expected Result:**
- Phase 3 requires a structured Evidence block (transcript ID/path + observable signal + affected section) alongside Title, Rationale, Confidence, and Diff.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `commands/refresh-command.md` (Phase 3)

**Notes:**

---

### Scenario 2: Unevidenced proposals are rejected before write and logged

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/refresh-command.md` and read Phase 4.
2. Confirm a proposal that cannot cite transcript evidence is rejected before any file write.
3. Confirm the rejection is recorded in `.writ/refresh-log.md` under a `**Rejected:**` section with reason `no evidence`.

**Expected Result:**
- Phase 4 refuses to apply (or log as applied) any amendment lacking evidence, and records the rejection with reason `no evidence`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `commands/refresh-command.md` (Phase 4)

**Notes:**

---

### Scenario 3: Evidence citations never store private content

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/refresh-command.md` (Phases 2–4) and the example Evidence blocks.
2. Confirm the privacy guard: only a transcript ID/path and a short observable signal are stored.
3. Confirm the command explicitly forbids chain-of-thought, prompts, and verbatim private transcript bodies in stored artifacts.

**Expected Result:**
- The command instructs that citations carry IDs + short observable signals only, never private bodies or reasoning.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `commands/refresh-command.md` (Prime Directive privacy guard)

**Notes:**

---

### Scenario 4: Drift is reconciled across command and docs

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Search `commands/status.md` for `Phase 2.2` — confirm it is absent.
2. Search `commands/status.md` for `.writ/state/refresh-log.md` — confirm it is absent, and that only the canonical `.writ/refresh-log.md` path is used.
3. Search `README.md` for "scans agent transcripts" / "Scans agent transcripts" — confirm the phrasing is replaced with accurate human-driven cited-evidence wording.
4. Open `.writ/docs/refresh-log-format.md` and confirm the schema documents the mandatory structured Evidence block (no loose `**Source transcript:**`) and `LEARNING_CONTRACT_SINCE` grandfathering.

**Expected Result:**
- No `Phase 2.2` reference; a single canonical `.writ/refresh-log.md` path; accurate README phrasing; the log-format doc describes the enforced Evidence block and grandfathering.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `commands/status.md`, `README.md`, `.writ/docs/refresh-log-format.md`

**Notes:**

---

### Scenario 5: Reviewed-with-no-amendments is a valid, evidence-exempt outcome

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/refresh-command.md` Phase 4.
2. Confirm that a run that reviews a command and applies zero amendments is recorded as a valid no-op.
3. Confirm this no-op outcome is exempt from the evidence requirement (there is nothing to justify).

**Expected Result:**
- A "reviewed, no changes" run is a valid, logged outcome exempt from the evidence requirement.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `commands/refresh-command.md` (Phase 4 no-op path)

**Notes:**

---

### Scenario 6: Malformed and citation-absent entries are handled without guessing

**Source:** Error & Rescue Map (Parse refresh-log entry / Missing transcript citation) — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/refresh-command.md` and `.writ/docs/refresh-log-format.md`.
2. Confirm the documented handling for a malformed/missing-field entry: report the missing field and treat the amendment as unevidenced, never fabricate the missing content.
3. Confirm the documented handling for a proposal with no transcript ID/path: reject before Apply with reason `no evidence`, and do not write the diff.

**Expected Result:**
- A malformed entry surfaces the missing field and is treated as unevidenced; a citation-absent proposal is rejected pre-write with `no evidence`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `commands/refresh-command.md`, `.writ/docs/refresh-log-format.md`

**Notes:**

---

## Story 2: Refresh-Evidence Eval Check

### Scenario 7: The validator passes well-formed evidence and fails a missing citation

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Python 3 available on PATH

**Steps:**
1. Run: `python3 scripts/eval-refresh-evidence.py` and read the PASS/FAIL TSV output and `echo $?`.
2. In the output, locate the well-formed evidenced scenario and the missing-transcript-citation scenario.

**Expected Result:**
- The well-formed evidenced entry emits `PASS`.
- The otherwise-identical entry with no transcript citation emits `FAIL`.
- The overall run exits `0` (all expected outcomes met).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/eval-refresh-evidence.py` (new)

**Notes:**

---

### Scenario 8: The privacy guard fails embedded private content

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `python3 scripts/eval-refresh-evidence.py`.
2. Locate the scenario that embeds a verbatim private transcript body or chain-of-thought.

**Expected Result:**
- The privacy-guard scenario emits `FAIL` (an entry embedding a fenced transcript body / reasoning block is rejected).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/eval-refresh-evidence.py` (privacy guard, D3)

**Notes:**

---

### Scenario 9: No-op review and valid rejection records both pass

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `python3 scripts/eval-refresh-evidence.py`.
2. Locate the reviewed-with-zero-amendments scenario and the rejected-for-lacking-evidence scenario.

**Expected Result:**
- The reviewed-no-amendments entry emits `PASS` (exempt).
- The rejected-for-lacking-evidence entry emits `PASS` (a valid rejection record).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/eval-refresh-evidence.py`

**Notes:**

---

### Scenario 10: Legacy entries before the contract date are grandfathered

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `python3 scripts/eval-refresh-evidence.py`.
2. Locate the scenario for an entry dated before `LEARNING_CONTRACT_SINCE` (`2026-07-11`).

**Expected Result:**
- The pre-contract entry is grandfathered and emits `PASS` (it is not retroactively failed).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/eval-refresh-evidence.py` (D6 grandfathering)

**Notes:**

---

### Scenario 11: The check is registered by a single append and runs by name

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `scripts/eval.sh` and confirm exactly one `check_refresh_evidence()` function is added and exactly one `refresh-evidence` line is appended to the `CHECKS` array (no reordering of existing entries).
2. Run: `bash scripts/eval.sh --check=refresh-evidence` and read `echo $?`.

**Expected Result:**
- The registry gains one function and one `CHECKS` entry, dispatched via the `check_${check//-/_}` convention.
- `--check=refresh-evidence` resolves and passes (exit `0`).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/eval.sh` (`check_refresh_evidence` + `CHECKS` entry)

**Notes:**

---

### Scenario 12: CI runs the new check with no workflow change

**Source:** Acceptance Criteria + Shadow Paths (Refresh-evidence check) — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `.github/workflows/eval.yml` and confirm its step runs `bash scripts/eval.sh` (iterating the full `CHECKS` array).
2. Confirm no `refresh-evidence`-specific wiring was added to the workflow file.
3. Confirm the check is included because it is registered in `CHECKS` and auto-dispatched.

**Expected Result:**
- `refresh-evidence` runs in CI automatically via the registry; `.github/workflows/eval.yml` is unmodified.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `.github/workflows/eval.yml` (verified no-change)

**Notes:**

---

## Story 3: Lightweight Tier 2 and Merge Gate

### Scenario 13: The pre-merge gate blocks unevidenced or eval-failing amendments

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/refresh-command.md` Phase 4 (Apply).
2. Confirm it runs `bash scripts/eval.sh --check=refresh-evidence` before writing any amendment.
3. Confirm an unevidenced or eval-failing amendment is rejected before any file write and recorded with reason `no evidence` or `eval failed`.

**Expected Result:**
- The Apply phase runs the pre-merge gate and only evidenced, eval-passing amendments merge; rejections are logged with the correct reason.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `commands/refresh-command.md` (Phase 4 gate)

**Notes:**

---

### Scenario 14: High-traffic targets get a structural (not LLM) Tier 2 check

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/refresh-command.md` and confirm the high-traffic allowlist is `create-spec`, `implement-story`, `ship`, `refactor`.
2. Confirm that, for an allowlisted target, the gate additionally runs a lightweight structural check reusing existing Tier 1 primitives (required-sections, broken-refs, length, preamble reference, diff-anchor).
3. Confirm the text explicitly defers the LLM-as-judge variant (no LLM judge is introduced).

**Expected Result:**
- Allowlisted targets trigger a structural Tier 2 check; the LLM-judge variant is documented as deferred.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `commands/refresh-command.md`, `scripts/eval-refresh-evidence.py` (Tier 2 scenarios)

**Notes:**

---

### Scenario 15: Non-allowlisted targets use the base check only

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `python3 scripts/eval-refresh-evidence.py` and locate the Tier 2 scope scenarios.
2. Confirm a non-allowlisted target uses only the base evidence check (no structural Tier 2), and an allowlisted target additionally runs the structural check.

**Expected Result:**
- The scenarios confirm allowlisted → base + structural, non-allowlisted → base only.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `scripts/eval-refresh-evidence.py` (Tier 2 allowlist scenarios)

**Notes:**

---

### Scenario 16: The log holds one merged-with-evidence entry and one rejected entry

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `.writ/refresh-log.md`.
2. Confirm one real entry records a refinement merged with cited transcript evidence and a passing eval gate.
3. Confirm one real entry records a proposal rejected for lacking evidence.
4. Confirm both entries conform to the schema in `.writ/docs/refresh-log-format.md`.

**Expected Result:**
- Two real acceptance entries exist (one merged-with-evidence, one rejected-for-lacking-evidence), both schema-conformant.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `.writ/refresh-log.md` (two acceptance entries)

**Notes:**

---

### Scenario 17: Full eval suite and catalog check remain clean

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `bash scripts/eval.sh` and read `echo $?`.
2. Run: `bash scripts/gen-skill.sh --check` and read `echo $?`.

**Expected Result:**
- Both commands exit `0`; the full suite (including `refresh-evidence`) is clean and the catalog is in sync.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `scripts/eval.sh`, `scripts/gen-skill.sh`

**Notes:**

---

### Scenario 18: The eval check tolerates missing transcripts and eval crashes safely

**Source:** Error & Rescue Map (Transcript file absent / Eval check crash / Tier 2 scope miss) — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `python3 scripts/eval-refresh-evidence.py` and locate the transcript-absent scenario.
2. Confirm an entry citing a `.jsonl` path that is not present on this machine still passes on the ID citation (the validator never requires the transcript body to exist).
3. Review the documented handling in `sub-specs/technical-spec.md` (Error & Rescue Map) for an eval-check crash (run error / exit-2 semantics; amendment not written) and a Tier 2 scope miss (explicit allowlist).

**Expected Result:**
- A cited-but-absent transcript passes on its ID; a validator crash is surfaced as a run error rather than a false pass; the allowlist prevents scope misses.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `scripts/eval-refresh-evidence.py`, `sub-specs/technical-spec.md` (Error & Rescue Map)

**Notes:**

---

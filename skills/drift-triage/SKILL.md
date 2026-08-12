---
name: drift-triage
description: "Triage implementation deviations by severity and route each to amend, warn, or pause."
disable-model-invocation: true
status: candidate
---

# Drift Triage

## Purpose

Decide what happens when what was built differs from what the contract said.
Every deviation gets one of three severities, and the severity decides the
route: auto-amend the lightweight artifact, warn and carry on, or stop and ask a
human. The decision comes from a stated rule, not from whoever noticed.

> **Format reference:** `.writ/docs/drift-report-format.md` is the authority on
> the drift-log entry's shape. This capability decides severity and routing; it
> does not re-specify the entry format.

## When to Use

- After a review that produces a `### Drift Analysis` section listing deviations
  between contract and implementation.
- When a deviation could be absorbed by amending a derived artifact, and the
  alternative is silently diverging documentation.
- When a deviation might be serious enough that continuing would compound it.

## How to Apply

Inspect the `### Drift Analysis` section and handle each deviation by severity.

### Small — naming, cosmetic; contract intent preserved

- Capture the exact **pre-edit SHA-256**, auto-amend **only** `spec-lite.md`,
  and append **one unique `DEV-NNN` entry** to `drift-log.md`.
- In recommended mode, return a canonical `recommend-spec-lite-review-v1` result
  bound to the execution ID, the story ID, `outcome: passed`,
  `drift_severity: small`, the DEV-ID list, and a **non-empty** summary.
- The parent must **durably** call
  `scripts/recommend-state.py record-spec-lite-amendment` with the state,
  repository, story ID, DEV ID, prior SHA-256 and review-result file before
  continuing. **A missing acknowledgment blocks.**
- Continue **PASS**.
- **Always** include the spec-lite changes in the run summary.

### Medium — scope or integration impact; contract intent met with notable changes

- Flag with a ⚠️ warning in the run output.
- Log to `drift-log.md`.
- Continue **PASS**.

### Large — fundamental deviation; contract intent NOT met, or constraints violated

- **PAUSE.**
- Present to the human with options: accept the deviation, reject it (send the
  work back), or modify the contract.
- **Wait for the decision** before continuing.

### Principles

- **Overall drift = the highest severity present.** A mixed run **pauses for the
  Large deviation while still auto-amending the Small ones.** Pausing does not
  suspend the Small-drift procedure; the two run together.
- Only `spec-lite.md` is auto-modified. The full `spec.md` is **never**
  auto-modified — it remains the human-approved contract.
- Log all drift to `.writ/specs/[spec-folder]/drift-log.md` — **append-only,
  never modify existing entries.** Continue DEV-ID numbering from the highest
  existing entry.
- In recommended mode, **never batch** multiple spec-lite byte revisions into
  one amendment record: each record must form a **contiguous prior/resulting
  digest link**. Duplicate or missing DEV IDs, a broken chain, or another
  locked-artifact mutation **blocks reconciliation**.

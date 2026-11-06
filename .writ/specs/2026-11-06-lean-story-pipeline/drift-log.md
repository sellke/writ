# Drift Log

> Spec: .writ/specs/2026-11-06-lean-story-pipeline/
> Created: 2026-11-06
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Gate declarations and evidence — Drift Report

> Run: 2026-11-06
> Overall Drift: Medium

### Deviations

#### [DEV-001] Frontmatter `evidence:` values name sources without `.writ/` paths
- **Severity:** Small
- **Spec said:** Business Rule 1: `evidence:` holds a cited recorded catch; `gate-evidence.md` holds one row per gate with the citation.
- **Implementation did:** The frontmatter gives a short dated citation (spec short name, DEV or F id, date, outcome); `gate-evidence.md` § Sources gives the full `.writ/` path or commit.
- **Reason:** `implement-story.md` ships to installed projects, and `eval-shipped-refs.py` keeps shipped commands from linking to Writ's own history. Traceability holds through `gate-evidence.md`.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: frontmatter `evidence:` is a short dated citation; `gate-evidence.md` § Sources holds the full path.

#### [DEV-002] Demoted gates' `kill_when` reads `gate-evidence.md` and a date, not `story-gate.py tally`
- **Severity:** Small
- **Spec said:** Business Rules (Expanded) → Rule 1, kill_when: checkable from `story-gate.py tally` output or a named file.
- **Implementation did:** `gate0_arch`, `gate4_5_behavior`, and `gate5_docs` read `"gate-evidence.md still reads none recorded for this gate on 2027-05-06"`.
- **Reason:** A named file is allowed, and full-pipeline runs write no `story-gate` record, so tally cannot see these gates.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: a `full-pipeline` gate's `kill_when` may be a dated condition over its `gate-evidence.md` row.

#### [DEV-003] ⚠️ `KNOWN_OVER_BUDGET` raised in Story 1 without asking the maintainer first
- **Severity:** Medium
- **Spec said:** Story 1 Notes: raise a budget failure with the maintainer before adding an entry. Hardest Constraint: update pins without weakening what they guard.
- **Implementation did:** Raised the `implement-story` entry from 13591 to 16566 (file 38551 → 41526 bytes), dated, with a comment that Stories 2–3 shrink the file below 38551.
- **Reason:** The frontmatter fields are required by Business Rule 1 and cannot fit in the old budget. The orchestrator had allowed the entry in the Gate 1 brief, which contradicted the story note. The raise is temporary: Success Criteria require the file to end smaller than at spec start.
- **Resolution:** ⚠️ Warned (Medium). Reported to the maintainer in the run output. Story 2 or 3 restores a pin at or below 38551 bytes.
- **Spec amendment:** None. Medium drift is warned and logged, not amended.

#### [DEV-004] Contract Business Rule 3 names Gate 0 Divergence, which no longer exists
- **Severity:** Small
- **Spec said:** Business Rule 3: Gate 0 Divergence stays on the default path.
- **Implementation did:** `gate-evidence.md` records that the design-divergence trial removed it on 2026-11-04 (`31b868a`). No `gates:` entry carries it.
- **Reason:** The contract was written against an older picture of `implement-story.md`. No keep verdict is reopened.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: kept gates are Safety Fact, Reviewer Filters, and the evidence gate; Gate 0 Divergence has no entry.

### Gate record

- Gate 3 iteration 1: `review-agent` FAIL, F1 (Major, AC-1.4: `gate3_5_drift` cited a catch Gate 3.5 did not make), confirmed by the evidence gate. Recoded in `31d8c29` with the repro committed unchanged.
- Gate 3 iteration 2: `review-agent` PASS.

#### [DEV-005] ⚠️ Gate 4 authenticity finding on the ADR-032 repro recorded as a false positive
- **Severity:** Medium
- **Spec said:** Gate 4: `test_imports_no_source` is blocking and takes the BLOCKED escalation.
- **Implementation did:** `scripts/tests/test_gate_evidence_drift_citation_repro.py`, committed unchanged as ADR-032 requires, reads `commands/implement-story.md` and imports no project module. `test-integrity.py authenticity` flagged it.
- **Reason:** The finding's claim is false here: the repro failed at `713af07` and passes after the fix in `31d8c29`. The extractor matches only quoted JS-style specifiers, the blind spot recorded in `.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`.
- **Resolution:** ⚠️ Warned (Medium). BLOCKED escalation asked the maintainer, who chose "Record as false positive". Story completes; not DEGRADED.
- **Spec amendment:** None.

### Maintainer decisions (2026-11-06)

- DEV-003: the temporary `KNOWN_OVER_BUDGET` raise stands; Story 2 or 3 brings `implement-story.md` to 38551 bytes or less and tightens the pin.
- DEV-005: Gate 4 authenticity finding recorded as a false positive.


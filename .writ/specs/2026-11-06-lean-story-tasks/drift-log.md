# Drift Log

> Spec: .writ/specs/2026-11-06-lean-story-tasks/
> Created: 2026-11-06
> ⚠️ Append-only — do not modify existing entries.

---

## Story 2: Lean task rules in the story generator and Step 2.6a — Drift Report

> Run: 2026-11-06
> Overall Drift: Small

### Deviations

#### [DEV-001] Generator states the rule content instead of citing Business Rules 1, 2, 3, 6 by number
- **Severity:** Small
- **Spec said:** Story 2 task 2.2: "Cite Business Rules 1, 2, 3, and 6 by number".
- **Implementation did:** `agents/user-story-generator.md` states each rule's content and cites no numbers.
- **Reason:** The generator ships to every Writ user; "Business Rule 1" there would point at this spec, which does not exist in a user's project. Business Rule 4 governs a generated spec's own files, not Writ's shipped prose.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: the shipped generator states rule content, not this spec's rule numbers.

#### [DEV-002] Byte-offset trims in Step 2.6a item 1, the iteration paragraph, and Step 2.9
- **Severity:** Small
- **Spec said:** Target net-zero bytes for `commands/create-spec.md`; the contract names no sentences to cut.
- **Implementation did:** Shortened item 1's `--repo` rationale, removed "This command declares no loop bound; the single re-run is the whole budget.", and reworded Step 2.9's count line. File stays at 39129 bytes.
- **Reason:** No consumer or pin reads the removed text; `eval.sh` `check_model_escalation` still finds its pinned sentence and the one-regeneration budget is stated twice.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach: `create-spec.md` edits are offset to stay net-zero in bytes.

---

## Story 3: Drop the generic Definition of Done — Drift Report

> Run: 2026-11-06
> Overall Drift: Small

### Deviations

#### [DEV-003] `--from-prototype` Step 3 no longer names a Definition of Done
- **Severity:** Small
- **Spec said:** The contract's Included list names `commands/create-spec.md` Steps 2.4, 2.6, 2.6a, 2.8, and Completion; Business Rule 5 says new stories have no Definition of Done.
- **Implementation did:** Removed "and Definition of Done item" from `--from-prototype` Step 3, so the completed Story 1 has only its Implementation Tasks checked.
- **Reason:** That Story 1 comes from the template that no longer has a DoD; leaving the line would contradict the template.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Files in Scope: `create-spec.md` adds Step 2.9 and `--from-prototype` Step 3.

#### [DEV-004] `/verify-spec` report example shows "—" for a story with no DoD
- **Severity:** Small
- **Spec said:** The contract scopes `commands/verify-spec.md` to Checks 1d and 3b.
- **Implementation did:** Changed the DoD cell of row 2 in the Phase 5 report example from `5/5` to `—` (byte-neutral).
- **Reason:** The example now shows the new 3b behavior; no behavior change.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents → Files in Scope: `verify-spec.md` adds the Phase 5 report example.

---

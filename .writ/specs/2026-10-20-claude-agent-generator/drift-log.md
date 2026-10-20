# Drift Log

> Spec: .writ/specs/2026-10-20-claude-agent-generator/
> Created: 2026-10-20
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Generator and Overlay — Drift Report

> Run: 2026-10-20
> Overall Drift: Small

### Deviations

#### [DEV-001] Orphan means no current canonical stem generates the file
- **Severity:** Small
- **Spec said:** technical-spec.md CLI Contract: an orphan is a `writ-*.md` in `--out-dir` that no overlay `file` maps to.
- **Implementation did:** An orphan is any `writ-*.md` that no current canonical stem generates. This also catches an overlay-mapped file whose `agents/<stem>.md` was deleted.
- **Reason:** Matches `gen-codex-agent-tomls.py`, which keys orphans on canonical stems. The spec's definition would let a file pass `--check` after its source was removed, which breaks Business Rule 1.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "For Coding Agents" → Error Handling orphan line (pre-edit SHA-256 1cc48592fc9114109519b3cbad4cd08f47571f36fd28b19ac1eb27bdda01b37b).

#### [DEV-002] Reasons sorted by reported name
- **Severity:** Small
- **Spec said:** `reason:` lines sorted by stem.
- **Implementation did:** Sorts on the printed token; an orphan sorts by its filename stem `writ-<x>`.
- **Reason:** The spec reports orphans by filename stem, so this is the literal reading. Deterministic.
- **Resolution:** Auto-amended
- **Spec amendment:** Same spec-lite line as DEV-001.

#### [DEV-003] Suffixes hold memory lines only
- **Severity:** Small
- **Spec said:** Suffix = trailing memory lines (Business Rule 3).
- **Implementation did:** Suffixes on architect, coder, evaluator, reviewer only. Story 2's regeneration drops hand-written tail lines that are not memory lines, e.g. "Report PASS only with a 100% pass rate." from `writ-tester.md`.
- **Reason:** Follows the contract. The canonical bodies carry the same rules (`agents/testing-agent.md:154`).
- **Resolution:** Auto-amended (no change needed)
- **Spec amendment:** None.

---

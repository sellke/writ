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

## Story 3: Parity Check, Eval Check, and Docs — Drift Report

> Run: 2026-10-20
> Overall Drift: Small

### Deviations

#### [DEV-004] Fail summary splits presence and content counts
- **Severity:** Small
- **Spec said:** Business Rule 6: output shape and exit codes stay the same. Old summary: `fail (<n> missing counterpart(s) across <a> agents)`.
- **Implementation did:** `fail (<m> missing counterpart(s), <c> content drift reason(s) across <a> agents[; content not checked: <gens>])`.
- **Reason:** The old wording would count content drift as missing counterparts. Shape is unchanged; no caller quotes the summary text.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "For Review Agents" criterion 5 (pre-edit SHA-256 5164c8767a293157c2cb2cbbe71d7b45fbda670049773fa741d1681d3895f240).

#### [DEV-005] eval stale and missing findings point at the canonical file
- **Severity:** Small
- **Spec said:** `check_claude_agents` structured like `check_codex_tomls`, which points findings at the generated file.
- **Implementation did:** Stale and missing findings point at `agents/<stem>.md`; orphan findings point at `claude-code/agents/writ-<x>.md`.
- **Reason:** The generator reports stale and missing by stem; naming the `writ-*.md` file would need a third copy of the stem map. The remedy names the regenerate command.
- **Resolution:** Auto-amended (no change needed)
- **Spec amendment:** None. technical-spec.md is not auto-modified.

#### [DEV-006] Generator exits 1 with no `reason:` line
- **Severity:** Small
- **Spec said:** rc 1 folds reasons; rc ≥ 2 becomes `<gen> --check exited <rc>`.
- **Implementation did:** rc 1 with no reason line adds `reason: <gen> --check failed without a reason line`.
- **Reason:** Prevents a broken generator from exiting 1 and still yielding `pass`. Matches `eval.sh` handling.
- **Resolution:** Auto-amended (no change needed)
- **Spec amendment:** None. technical-spec.md is not auto-modified.

---

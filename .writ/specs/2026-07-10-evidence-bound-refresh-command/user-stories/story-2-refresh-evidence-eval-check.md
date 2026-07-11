# Story 2: Refresh-Evidence Eval Check

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer relying on CI to keep the learning loop honest
**I want to** a deterministic, fixture-driven eval check that validates refresh refinements carry evidence
**So that** the evidence contract is machine-enforced on every PR and push, without depending on the contents of the live refresh log

## Acceptance Criteria

- [ ] Given a well-formed evidenced refresh-log entry, when `scripts/eval-refresh-evidence.py` validates it, then it emits `PASS`; given an otherwise-identical entry with no transcript citation, then it emits `FAIL`.
- [ ] Given an entry embedding a verbatim private transcript body or chain-of-thought, when the validator runs, then the privacy guard emits `FAIL`; given a reviewed-with-zero-amendments entry, then it emits `PASS` (exempt); given a rejected-for-lacking-evidence entry, then it emits `PASS` (valid rejection record).
- [ ] Given a live entry dated before `LEARNING_CONTRACT_SINCE`, when it is evaluated, then it is grandfathered and does not fail.
- [ ] Given `scripts/eval.sh`, when the new check is registered, then exactly one `check_refresh_evidence()` function and one `refresh-evidence` registry-array entry are appended, dispatched via the existing `check_${check//-/_}` convention.
- [ ] Given `.github/workflows/eval.yml`, when the check is registered, then it runs in CI with no file change (auto-run from the registry) and this is verified and noted.

## Implementation Tasks

- [ ] 2.1 Write `scripts/eval-refresh-evidence.py` with FAILING fixtures first (modeled on `scripts/eval-phase-knowledge.py`, PASS/FAIL TSV over `tempfile.TemporaryDirectory()` entries): evidenced entry passes; missing-citation fails; missing-signal fails; embedded private body/CoT fails; reviewed-no-amendments is exempt; rejected-for-lacking-evidence is a valid record; pre-`LEARNING_CONTRACT_SINCE` entry is grandfathered.
- [ ] 2.2 Implement the parser/validator the fixtures exercise: parse a refresh-log entry, detect the transcript citation, observable signal, and affected section, enforce the privacy guard, honor the no-op exemption, and apply date grandfathering.
- [ ] 2.3 Add `check_refresh_evidence()` to `scripts/eval.sh` that runs the fixture script, counts scenarios into `CURRENT_SCENARIOS`/`CURRENT_SCENARIOS_PASSED`, calls `add_finding` on FAIL, and adds `require_literal` static assertions that `commands/refresh-command.md` and `.writ/docs/refresh-log-format.md` mandate evidence and the rejection path.
- [ ] 2.4 Register the check by appending exactly one `refresh-evidence` line to the `CHECKS` array in `scripts/eval.sh` (append-only; do not reorder; a sibling Phase 7 spec appends later).
- [ ] 2.5 Verify `.github/workflows/eval.yml` needs no change — the check auto-runs via the existing `bash scripts/eval.sh` step — and note this explicitly in the story and spec.
- [ ] 2.6 Run `python3 scripts/eval-refresh-evidence.py` and `bash scripts/eval.sh --check=refresh-evidence`; confirm every fixture and static assertion passes.
- [ ] 2.7 Run full `bash scripts/eval.sh` and `bash scripts/gen-skill.sh --check`; confirm the other registered checks are unaffected.

## Notes

- Follow the established pattern in `scripts/eval-phase-knowledge.py` exactly: `emit(name, ok, detail)`, `PASS\t<name>` / `FAIL\t<name>\t<reason>`, temp-dir synthetic inputs, `return 0 if failed == 0 else 1`.
- The check must be deterministic and must NOT read `.writ/refresh-log.md` for pass/fail — the two existing legacy entries must never break CI.
- `require_literal` assertions target the reconciled Story 1 text; that is why this story depends on Story 1.
- Keep the transcript-absent case passing on the ID citation — the validator never requires a transcript body to exist on disk.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `eval-refresh-evidence.py` and `--check=refresh-evidence` pass
- [ ] Full `eval.sh` and `gen-skill.sh --check` clean
- [ ] Registry edit is a single append; no reordering

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Parse refresh-log entry`, `Eval check crash`, `Transcript file absent`, `Private-content guard`, `Grandfathered legacy entry`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Refresh-evidence check`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rules 8, 10, 11]
- **Decisions:** [`technical-spec.md` → `### D5 — Fixture-Driven Eval Check`, `### D6 — Grandfathering via LEARNING_CONTRACT_SINCE`, `### D7 — Two Enforcement Points, No New CI Wiring`]
- **Reference implementation:** [`scripts/eval-phase-knowledge.py` (the proven fixture-script pattern), `scripts/eval.sh` → `check_phase_knowledge()` and the `CHECKS` array (lines ~19–39)]

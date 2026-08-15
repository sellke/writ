# Writ Project Context

> Last Updated: 2026-08-15T01:58:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** 2026-08-14-script-backed-quality-gates — Script-Backed Quality Gates
- **Status:** Complete (2026-08-14)
- **Story:** 6 of 6 complete — Stories 1–6 all Completed ✅
- **Progress:** 42/42 tasks complete (100%); 30/30 acceptance criteria met

Four quality guarantees Writ stated as instructions to a language model now have
read-only scripts behind them, each validated against a real application codebase
before shipping: `scripts/quality-config-audit.py`, `scripts/test-integrity.py`,
`scripts/build-smoke.py`, plus `.writ/docs/quality-signal-classification.md` as
the specification they implement against. Wired into Gate 2 and Gate 4 of
`/implement-story` with no new gate number, and into `/initialize` (baseline +
coverage floor) and `/status` (health line).

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md present
- **Active spec:** .writ/specs/2026-08-14-script-backed-quality-gates/ — spec.md, spec-lite.md, user-stories/, sub-specs/, drift-log.md, recommendation-log.md
- **Knowledge:** .writ/knowledge/ (22 entries)
- **Docs:** .writ/docs/ (23 files)
- **Integrity:** ✅ all required present

## Recent Drift

- [DEV-006] `ac-trace` cannot tell a fixture literal from a citation — Small; seven `dangling_reference` findings originate in the *previous* spec's test fixtures, not this one. Diagnosis recorded rather than worked around; the fix belongs to `2026-08-13-acceptance-criteria-traceability-ids`.
- [DEV-005] The per-command byte ratchet needed a disclosed increment — Small; `implement-story.md` 735 → 2730 bytes over budget from the Gate 2/4 wiring. Acknowledged, not exempted. That ratchet is not wired into `eval.sh` and fired only because the full unit suite was run by hand.
- [DEV-004] `coverage` with nothing to judge is `unverifiable`, not `pass` — Small; the first real run returned `pass` while measuring 57.2% against an 80% bar, which is the clean-report failure mode the spec exists to end.

## Open Issues

4 files under `.writ/issues/`.

## Verification State

- `bash scripts/eval.sh` — 0 findings, 0 run errors (45 checks, including three new: `quality-config-audit`, `test-integrity`, `build-smoke`)
- `python3 -m unittest discover -s scripts/tests` — 697 tests, OK (1 skipped)
- `scripts/check-agent-parity.sh` — clean; `scripts/gen-skill.sh --check` — clean
- Fixture validation against a real `yuss.app` checkout (`ff3ad2e`) reproduced all four pinned findings: 57.2256% statements re-derived, exactly 4 inauthentic test files of 147, both `build_gate_disabled` line numbers, and an environment-versus-source build split measured on real toolchain output.

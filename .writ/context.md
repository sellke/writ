# Writ Project Context

> Last Updated: 2026-09-03T21:05:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** 2026-09-03-model-delegation — Model Delegation: Anchor, Floor, Origin, Escalation
- **Status:** In Progress
- **Story:** 1 of 5 — The Contract (Completed ✅); next: Story 2 (agents, manifest, scaffolders)
- **Progress:** 6/33 tasks complete (18%); 5/25 acceptance criteria met

Story 1 landed the ADR-024 contract: `system-instructions.md` § Model Tiers (anchor/floor,
two-question derivation, origin, ceiling, resolution order, escalate-once, `entry_level`
subsection with the normative notice), `cursor/writ.mdc` regenerated as its mirror,
`.writ/docs/model-tiers.md` rewritten, and `scripts/lint-skill.sh` accepting `anchor|floor`
with `orchestration`/`capability` as warned aliases until 0.35.0 plus `entry_level` validation.
Agents still carry the old values (lint warns, not fails) until Story 2.

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md present
- **Active spec:** .writ/specs/2026-09-03-model-delegation/ — spec.md, spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (23 files)
- **Integrity:** ✅ all required present

## Recent Drift

- [DEV-001] Entry notice rendered with inline code spans, not a code-span-escaped line — Small (Story 1)
- [DEV-002] `cursor/writ.mdc` regenerated whole-file, closing a pre-existing § Skills drift — Small (Story 1)
- [DEV-003] `.writ/leanness-baseline.json` gained dated `system_instructions` justifications — Small (Story 1)

## Open Issues

5 files under `.writ/issues/` (new: `test-integrity.py authenticity` flags every bash test as `test_imports_no_source`).

## Verification State

- `bash scripts/eval.sh` — Findings: 0, `prime-directive-sync` PASS (Story 1)
- `bash scripts/tests/test_lint_model_tier.sh` — OK (15 cases)
- `python3 -m unittest discover -s scripts/tests` — 703 ran; 7 pre-existing environmental errors (missing `pytest`, symlink-loop case)
- Mirror: `diff <(sed '/^## Self-Dogfooding/,$d' cursor/writ.mdc | sed '$d') system-instructions.md` → empty

# Writ Project Context

> Last Updated: 2026-09-03T21:40:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** 2026-09-03-model-delegation — Model Delegation: Anchor, Floor, Origin, Escalation
- **Status:** In Progress
- **Story:** 2 of 5 — Agents, Manifest, Scaffolders (Completed ✅); next: Story 3 (adapters + Cursor verification)
- **Progress:** 13/33 tasks complete (39%); 10/25 acceptance criteria met

Stories 1–2 landed the ADR-024 contract and migrated the carriers: `system-instructions.md`
§ Model Tiers (anchor/floor, two-question derivation, origin, ceiling, resolution order,
escalate-once, `entry_level`), its `cursor/writ.mdc` mirror, `.writ/docs/model-tiers.md`, the
lint grammar (aliases warned until 0.35.0); all 7 agents now declare `anchor|floor`, `"fast"` is
gone from `agents/`, the manifest carries `model_tier` only, `gen-skill.sh` renders a `Tier`
column, and `/new-command` scaffolds `entry_level`. Still stale until Story 3: `adapters/*.md`,
`claude-code/agents/*.md`, `codex/agents/*.toml`, `scripts/gen-codex-agent-tomls.py`.

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md present
- **Active spec:** .writ/specs/2026-09-03-model-delegation/ — spec.md, spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (23 files)
- **Integrity:** ✅ all required present

## Recent Drift

- [DEV-006] Story 1 Gate-5 doc handoff (`README.md`, `AGENTS.md`, `component-contract.md`) edited in Story 2 — Small
- [DEV-005] Generator drops `model` entirely; `Tier` column replaces `Model` — Medium (technical-spec §1 amendment suggested)
- [DEV-004] Template comment uses `model_tier=floor`, not `model_tier: floor` — Small

## Open Issues

5 files under `.writ/issues/` (new: `test-integrity.py authenticity` flags every bash test as `test_imports_no_source`).

## Verification State

- `bash scripts/eval.sh` — Findings: 0 (after Story 2)
- `bash scripts/tests/test_lint_model_tier.sh` — OK (15 cases); `test_model_tier_migration.sh` — OK
- `bash scripts/gen-skill.sh --check` — exit 0 (pure-bash and yq parsers); `check-agent-parity.sh` — OK
- `python3 -m unittest discover -s scripts/tests` — 703 ran; 7 pre-existing environmental errors (missing `pytest`, symlink-loop case)
- Mirror: `diff <(sed '/^## Self-Dogfooding/,$d' cursor/writ.mdc | sed '$d') system-instructions.md` → empty

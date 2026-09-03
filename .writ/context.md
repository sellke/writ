# Writ Project Context

> Last Updated: 2026-09-03T23:50:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** 2026-09-03-model-delegation — Model Delegation: Anchor, Floor, Origin, Escalation
- **Status:** Complete (2026-09-03) — awaiting `/status --archive`
- **Story:** 5 of 5 complete; last landed: Story 4 (escalation at `create-spec` 2.6a and Gate 0)
- **Progress:** 33/33 tasks complete (100%); 25/25 acceptance criteria met

All five stories landed ADR-024 end to end. `system-instructions.md` § Model Tiers (anchor/floor,
two-question derivation, origin, ceiling, resolution order, escalate-once, `entry_level`), its
`cursor/writ.mdc` mirror, `.writ/docs/model-tiers.md`, lint aliases (warned until 0.35.0); all 7
agents declare `anchor|floor`, manifest carries `model_tier` only, `gen-skill.sh` renders `Tier`,
`/new-command` scaffolds `entry_level`; four adapters carry Origin source · `anchor` · `floor` ·
escalation tables (Cursor verified 2026-09-03 from a Fable 5.1/high origin; OpenClaw unverified),
Claude Code agents `inherit`/`haiku`, Codex floor is effort-only, `"fast"` is gone from every carrier;
all 31 commands declare `entry_level` (14/12/5), `lint-skill.sh` routes `commands/*.md` to value
checks only, `eval.sh` notes a missing field. Story 4: `/create-spec` Step 2.6a validates generated
stories (`ac-trace.py check`, folder-scoped `--repo`, inline count bounds) and regenerates a failing
story once at anchor; `/implement-story` Gate 0 confirms a floor ABORT at anchor before interrupting
the user; both emit `(no-op until ADR-025 Story 1) escalated(agent=…, site=…, origin=…)`; six
`require_literal` pins under `eval.sh --check=model-escalation`; live forced-invalid run observed
`origin=claude-fable-5.1/high@cursor`. Next: ADR-025 Story 1 makes the `escalated`/`degraded` lines
live (`signal.py append`) — must keep the `escalated(` tuple as `detail` or update the pins.

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md present
- **Active spec:** .writ/specs/2026-09-03-model-delegation/ — spec.md, spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (23 files)
- **Integrity:** ✅ all required present

## Recent Drift

- [DEV-014] Step 2.6a passes `--repo <spec folder>` to `ac-trace.py check` — repo-wide scan misattributes other specs' dangling references at authoring time — Small
- [DEV-015] `test_governor_enforcement.py` `KNOWN_OVER_BUDGET` re-pinned in-story with dated disclosure (was red at HEAD from Story 5's `entry_level:` lines) — Small
- [DEV-009] Entry notice's positive path is not observable on Cursor today — every listed slug self-assesses ≥ `high`; harness prompt states no effort — Medium ⚠️ (flagged for ADR-025 ledger; no ranking added)
- [DEV-010–013] Story 5 task-text corrections: frontmatter-scoped count/predicate, own `entry-level` CHECKS entry, fixtures stay in Story 1's test, lint routing for commands — Small
- [DEV-008] Opus-origin Cursor sessions emit `degraded(reason=no lower same-family slug listed)` rather than collapsing silently — Medium (resolved in Story 3; cited by Story 4 Notes)

## Open Issues

5 files under `.writ/issues/` (`test-integrity.py authenticity` flags bash tests and importlib-by-path Python tests as `test_imports_no_source` — two occurrences recorded).

## Verification State

Post-spec integration run (2026-09-03, after Story 4 commit `dd0af22`):

- `bash scripts/eval.sh` — Findings: 0, Run errors: 0 (`## model-escalation PASS`, `## entry-level PASS`; leanness warnings for the six over-budget commands remain notes)
- `scripts/tests/test_*.sh` — 10/10 OK
- `uv run --with pytest --python 3.12 python -m pytest scripts/tests` — 798 passed, 1 skipped, 1 failed: `test_ac_trace.py::CitationScanTests::test_symlink_loop_does_not_crash_the_scan` — **pre-existing** (fails at spec baseline `855ed42`; `ac-trace.py` and its test untouched since 2026-08-13; `pathlib.resolve` raises `RuntimeError: Symlink loop` on this macOS host). System Python 3.9 additionally lacks `pytest` (6 modules) — environmental.
- `bash scripts/gen-skill.sh --check` OK; `check-agent-parity.sh` OK; `lint-skill.sh commands/*.md skills/*/SKILL.md` 0 violations; `gen-codex-agent-tomls.py` byte-stable
- Mirror: `diff <(sed '/^## Self-Dogfooding/,$d' cursor/writ.mdc | sed '$d') system-instructions.md` → empty
- `rg "count as one attempt against" commands/` → 2; `rg 'escalated\(' commands/` → exactly two site literals; `rg '"fast"' adapters/ claude-code/ codex/ commands/` → 0

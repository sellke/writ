# Writ Project Context

> Last Updated: 2026-09-03T22:22:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** 2026-09-03-model-delegation — Model Delegation: Anchor, Floor, Origin, Escalation
- **Status:** In Progress
- **Story:** 3 of 5 — Adapters + Cursor Verification (Completed ✅); next: Story 5 (`entry_level` on 31 commands), then Story 4 (escalation)
- **Progress:** 20/33 tasks complete (61%); 15/25 acceptance criteria met

Stories 1–3 landed the ADR-024 contract, migrated the carriers, and verified the platforms:
`system-instructions.md` § Model Tiers (anchor/floor, two-question derivation, origin, ceiling,
resolution order, escalate-once, `entry_level`), its `cursor/writ.mdc` mirror,
`.writ/docs/model-tiers.md`, lint aliases (warned until 0.35.0); all 7 agents declare
`anchor|floor`, manifest carries `model_tier` only, `gen-skill.sh` renders `Tier`, `/new-command`
scaffolds `entry_level`; four adapters carry Origin source · `anchor` · `floor` · escalation tables
(Cursor verified 2026-09-03 from a Fable 5.1/high origin: `"fast"` accepted but self-reports the
anchor, `inherit[effort=low]` rejected, `claude-opus-5-thinking-high` resolves below; OpenClaw
unverified), Claude Code agents `inherit`/`haiku`, Codex floor is effort-only
(`model_reasoning_effort = "low"`), `"fast"` is gone from every carrier. Remaining: Story 5
(`entry_level` on every command + lint test), Story 4 (escalate-once at `create-spec` 2.6a and
Gate 0 — must cite DEV-008: Opus-origin Cursor emits `degraded`, not a silent collapse).

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md present
- **Active spec:** .writ/specs/2026-09-03-model-delegation/ — spec.md, spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (23 files)
- **Integrity:** ✅ all required present

## Recent Drift

- [DEV-008] Opus-origin Cursor sessions emit `degraded(reason=no lower same-family slug listed)` rather than collapsing silently; "family floor" = vendor's bottom tier — Medium (resolved in Story 3; Story 4 must cite)
- [DEV-007] Cursor `floor` cell states rule (a); the dated verification record names the observed slug — Small
- [DEV-005] Generator drops `model` entirely; `Tier` column replaces `Model` — Medium (technical-spec §1 amendment suggested)

## Open Issues

5 files under `.writ/issues/` (`test-integrity.py authenticity` flags bash tests and importlib-by-path Python tests as `test_imports_no_source` — two occurrences recorded).

## Verification State

- `bash scripts/eval.sh` — Findings: 0 (after Story 3; pre-existing leanness warning set unchanged)
- `python3 -m unittest discover -s scripts/tests -p 'test_gen_codex*'` — 5/5 OK; `python3 scripts/gen-codex-agent-tomls.py` byte-stable
- `bash scripts/tests/test_lint_model_tier.sh` — OK (15 cases); `test_model_tier_migration.sh` — OK
- `bash scripts/gen-skill.sh --check` — exit 0 (pure-bash and yq parsers); `check-agent-parity.sh` — OK
- `rg '"fast"' adapters/ claude-code/ codex/` → 0; `rg -n 'Origin source' adapters/*.md` → 4
- `python3 -m unittest discover -s scripts/tests` — 708 ran; 7 pre-existing environmental errors (missing `pytest`, symlink-loop case)
- Mirror: `diff <(sed '/^## Self-Dogfooding/,$d' cursor/writ.mdc | sed '$d') system-instructions.md` → empty

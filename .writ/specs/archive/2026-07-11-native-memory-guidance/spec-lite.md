# Phase 8: Native-Memory Guidance Per Adapter (Lite)

> Source: `.writ/specs/2026-07-11-native-memory-guidance/spec.md`
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Add a consistent "Native Memory & the Writ Ledger" section to all four adapters, fold in the mission-language verification sweep, and ship one `memory-interop` eval check. One rule everywhere: **session prefs/trivia → native memory; negotiated decisions/conventions/lessons → the Writ ledger (canonical, reviewable, feeds the rest); external brain → disposable index over the ledger.**

**Implementation Approach:**
- Add the section to `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`, `adapters/openclaw.md`. Each: canonical two-place rule + platform-mechanics paragraph + named anti-pattern + one-line cross-link to `gbrain-interop` skill / `.writ/docs/gbrain-recipe.md`.
- Platform surfaces (name accurately): Cursor Memories + semantic index; Claude Code `CLAUDE.md` + `.claude/agent-memory/`; Codex `AGENTS.md`; OpenClaw session state.
- Verify active surfaces (mission, mission-lite, README, docs) have no stale "persistent-database knowledge layer" framing; active mission reads "not a memory database or retrieval engine." Fix any stale active ref (expected: none).
- Add `check_memory_interop` to `scripts/eval.sh` (model on `check_ralph_retirement` — file-scoped `require_literal`/`forbid_literal`, no Python fixture) + one `CHECKS` line.

**Files in Scope:**
- `adapters/{cursor,claude-code,codex,openclaw}.md`, `scripts/eval.sh` (single-writer for Phase 8)
- Do NOT edit `skills/gbrain-interop/SKILL.md`, `.writ/docs/gbrain-recipe.md`, `.writ/manifest.yaml`, or root `SKILL.md` — sibling spec owns them; only reference/assert.

**Consistency:** write the two-place rule once as a canonical sentence; the eval check asserts its key phrases across all four adapters so drift fails CI.

---

## For Review Agents

**Acceptance Criteria:**
1. All four adapters have the section, identical two-place rule, accurate per-platform mechanics.
2. Each section cross-links the `gbrain-interop` skill / recipe.
3. No stale "persistent-database knowledge layer" on active surfaces; active mission language verified.
4. `check_memory_interop` added additively + one `CHECKS` entry; no existing check altered.
5. `scripts/eval.sh --check=memory-interop` passes (adapters + sibling GBrain artifacts + no stale framing).
6. Full `scripts/eval.sh` green.

**Business Rules / Drift Anchors:**
- Markdown ledger canonical + reviewable; native memory is a consumer (ADR-011). Inverting the rule ("decisions → native memory") is drift.
- Never imply native memory is reviewable like markdown-in-git.
- `scripts/eval.sh` single-writer for Phase 8 = this spec; additive only, never a rewrite.
- Editing the sibling's skill/recipe/manifest/catalog here is scope drift.

---

## For Testing Agents

**Verification (script/static, no app test suite):**
- `bash scripts/eval.sh --check=memory-interop`
- full `bash scripts/eval.sh` (0 findings, 0 run errors)
- read-through: each platform's native-memory surface described accurately

**Shadow Paths:**
- Sibling artifacts missing (wrong order) → check fails loudly (this spec must run after `gbrain-compatibility-recipe`).
- A stale "persistent-database" active reference → `forbid_literal` fails.
- One adapter missing the section → `require_literal` fails for that file.

**Edge Cases:**
- Historical ADRs/specs describing the mission change must NOT be swept (only active surfaces).
- The two-place rule must read identically across adapters (consistency assertion).

# Phase 8: Native-Memory Guidance Per Adapter

> **Status:** Not Started
> **Created:** 2026-07-11
> **Owner:** @AdamSellke
> **Phase:** 8 — Memory Interop
> **Dependencies:** [2026-07-11-gbrain-compatibility-recipe]
> **Source:** `.writ/product/roadmap.md` Phase 8 — features "Native-memory guidance per adapter" and "Mission language update"
> **Governing ADRs:** `adr-011-memory-interop-markdown-canonical.md` (markdown canonical; native/external layers are consumers), `adr-005-knowledge-substrate-markdown-over-database.md` (reviewability), `adr-009-command-agent-skill-boundary.md`

---

## Specification Contract

**Deliverable:** Add a consistent **"Native Memory & the Writ Ledger"** section to each of the four platform adapters (`cursor.md`, `claude-code.md`, `codex.md`, `openclaw.md`) that draws one clear line: **session preferences and trivia belong in the platform's native memory; negotiated decisions, conventions, and lessons belong in the Writ ledger** — the reviewable markdown layer that feeds everything else. Fold in the roadmap's XS **"Mission language update"** feature: verify no stale "persistent-database knowledge layer" framing survives on active surfaces (README/docs/mission). Ship the phase's single machine-checkable proof as one `memory-interop` eval check.

**Origin:** Phase 8 — Memory Interop in `.writ/product/roadmap.md`. Two roadmap features land here: "Native-memory guidance per adapter" (S) and "Mission language update" (XS, already substantially done in the 2026-07-09 mission refresh — this spec verifies and closes it). Governed by ADR-011, which assigns native memory the role of *consumer* and the ledger the role of *system of record*.

**Must Include:** A per-adapter section grounded in each platform's *actual* native-memory surface — Cursor Memories + semantic index; Claude Code `CLAUDE.md` + `.claude/agent-memory/`; Codex `AGENTS.md`; OpenClaw session state — expressing one consistent two-place rule. Each section cross-links the `gbrain-interop` skill for the external-brain case. The mission-language verification confirms the active surfaces already read "not a memory database or retrieval engine" and carry no stale contradiction. One `memory-interop` eval check machine-verifies the adapter sections and the sibling spec's GBrain artifacts.

**Hardest Constraint:** One consistent memory posture across every adapter and the GBrain recipe — no per-platform contradiction. **Native memory = session preferences/trivia; the ledger = negotiated decisions/conventions/lessons (canonical, reviewable, feeds the rest); external brain = disposable index over the ledger.** The guidance must never invert this (never "put decisions in native memory") and must never imply native memory is reviewable the way markdown-in-git is.

### Experience Design

- **Entry point:** A user setting up Writ on their platform reads that platform's adapter and reaches the "Native Memory & the Writ Ledger" section.
- **Happy path:** They learn what to let their platform remember natively (their name, preferred tone, editor trivia, ephemeral session context) versus what to write to the ledger (why a decision was made, a convention the team follows, a lesson learned) — and that the ledger is the layer a teammate or a future self can review in a PR.
- **Moment of truth:** Six months later, the *why* behind a decision is in a reviewable markdown file, not trapped in one machine's native-memory store that no one else can read.
- **Feedback model:** The rule is one sentence, repeated consistently across adapters, with platform-specific mechanics beneath it. A reader on any platform gets the same posture.
- **Error experience (anti-pattern called out):** Each section names the failure mode — letting negotiated decisions live only in native memory, where they are unreviewable and evaporate on platform churn — and points to the ledger instead.

### Business Rules

1. Markdown in git is the canonical, reviewable system of record; native memory is a convenience consumer, never the source of truth (ADR-011).
2. The two-place rule is identical across all four adapters: session preferences/trivia → native memory; negotiated decisions/conventions/lessons → the ledger.
3. Each adapter section is grounded in that platform's real native-memory surface; it does not invent a memory feature the platform lacks.
4. Each adapter section cross-links the `gbrain-interop` skill / `.writ/docs/gbrain-recipe.md` for the external-brain (disposable index) case, keeping the three layers (native / ledger / external index) consistent.
5. The mission-language surfaces (mission, README, docs) carry no stale "persistent-database knowledge layer" framing on any active surface; historical ADRs and specs that *describe* the change are left untouched.
6. Exactly one spec owns `scripts/eval.sh` for Phase 8 (single-writer): this one. The `memory-interop` check is additive — one `check_*` function plus one `CHECKS` entry — never a rewrite of existing checks.
7. The eval check asserts both this spec's adapter sections and the sibling `gbrain-compatibility-recipe` artifacts, so Phase 8's machine-checkable exit criterion is one green check.
8. Guidance is documentation only; it introduces no runtime hook, no new command, and no native-memory automation.

### Success Criteria

1. All four adapters (`cursor.md`, `claude-code.md`, `codex.md`, `openclaw.md`) contain a "Native Memory & the Writ Ledger" section expressing the identical two-place rule, each grounded in that platform's real native-memory surface.
2. Each adapter section cross-links the `gbrain-interop` skill or `.writ/docs/gbrain-recipe.md` for the external-index case.
3. No active surface (mission, README, docs) contains stale "persistent-database knowledge layer" framing; the active mission language reads "not a memory database or retrieval engine" (verified).
4. `scripts/eval.sh` gains one `check_memory_interop` function and one `memory-interop` entry in `CHECKS`, additively (no existing check altered).
5. `bash scripts/eval.sh --check=memory-interop` passes: it asserts (a) each adapter's native-memory section + the two-place distinction, (b) the `gbrain-interop` skill exists and is registered, (c) `.writ/docs/gbrain-recipe.md` exists with the round-trip guarantee, and (d) no stale "persistent-database" framing on active surfaces.
6. Full `bash scripts/eval.sh` is green (0 findings, 0 run errors) on the merged phase branch.

### Scope Boundaries

**Included:**
- A "Native Memory & the Writ Ledger" section in each of `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`, `adapters/openclaw.md`.
- Cross-links from each adapter section to the `gbrain-interop` skill / recipe doc.
- Mission-language verification sweep across active surfaces (mission, README, docs); fix any stale framing found.
- One additive `check_memory_interop` in `scripts/eval.sh` + one `CHECKS` entry (single-writer for Phase 8).

**Excluded:**
- The GBrain skill and recipe doc themselves (sibling `gbrain-compatibility-recipe` spec — this spec only *references* and *asserts* them).
- Any native-memory automation, runtime hook, or new command.
- Rewriting historical ADRs/specs that describe the mission-language change (only active surfaces are swept).
- Editing `.writ/manifest.yaml`, `SKILL.md`, or the skill/recipe files (owned by the sibling spec — single-writer).

### Technical Concerns

- **Consistency risk.** Four separately-edited files must express one rule. Mitigation: a shared canonical sentence, asserted verbatim (or near-verbatim) by the eval check across all four adapters.
- **Platform accuracy.** Each platform's native-memory surface differs; the section must reflect reality (Cursor Memories, Claude `CLAUDE.md`/`.claude/agent-memory/`, Codex `AGENTS.md`, OpenClaw sessions), not a generic placeholder.
- **Cross-spec ordering.** The eval check asserts sibling artifacts; this spec must run *after* `gbrain-compatibility-recipe` so those artifacts exist. Guaranteed by the declared dependency and sequential phase execution.
- **Mission sweep is mostly verification.** The 2026-07-09 refresh already softened the language; the risk is a missed stale reference, not a large rewrite. The eval check's `forbid_literal` on active surfaces makes "clean" machine-checkable.

### Recommendations

- Write the two-place rule once as a canonical sentence, then adapt only the platform-mechanics paragraph beneath it per adapter. This keeps consistency cheap and the eval assertion simple.
- Model the section placement on each adapter's existing structure (e.g., near "Knowledge Loading" / "Customization" in `cursor.md`; near the memory features in `claude-code.md`).
- Model `check_memory_interop` on `check_ralph_retirement` (file-scoped `require_literal` / `forbid_literal_ci`), not on a Python fixture harness — this is a documentation check.
- Keep the external-index cross-link a one-liner pointing to the recipe/skill, so the three-layer model (native / ledger / external) reads consistently without duplicating the recipe.

### Cross-Spec Review

This spec depends on `gbrain-compatibility-recipe` (declared). It owns the four adapter files, `scripts/eval.sh`, and the mission-language sweep; the sibling spec owns the skill, recipe doc, `manifest.yaml`, and root `SKILL.md`. There is **no shared-writer file** — the dependency is one of *reference* (adapter cross-links, eval assertions), not co-editing. Sequential phase execution (sibling first) guarantees the referenced artifacts exist when this spec's eval check runs.

---

## Detailed Requirements

### R1 — Per-Adapter "Native Memory & the Writ Ledger" Section

- Add the section to all four adapters. Each contains: (a) the canonical two-place rule (session prefs/trivia → native memory; decisions/conventions/lessons → the ledger); (b) a short platform-mechanics paragraph naming that platform's real native-memory surface; (c) the named anti-pattern (decisions living only in native memory are unreviewable and evaporate on churn); (d) a one-line cross-link to the `gbrain-interop` skill / recipe for the external-index layer.
- Platform surfaces to name accurately:
  - **Cursor** — Cursor Memories + semantic codebase indexing.
  - **Claude Code** — `CLAUDE.md` (auto-loaded) + `.claude/agent-memory/` (persistent agent memory).
  - **Codex** — `AGENTS.md` (primary instruction surface; Writ-owned block + user region).
  - **OpenClaw** — session state / file-based context.

### R2 — Mission-Language Verification Sweep

- Confirm active surfaces (`.writ/product/mission.md`, `.writ/product/mission-lite.md`, `README.md`, `.writ/docs/*`) carry no stale "persistent-database knowledge layer" framing and that the active mission language reads "not a memory database or retrieval engine."
- Fix any stale active reference found; leave historical ADRs/specs that describe the change untouched.
- Record the verification result as evidence (the feature is "done" when the sweep is clean and asserted by the eval check).

### R3 — `memory-interop` Eval Check (single-writer for `scripts/eval.sh`)

- Add `check_memory_interop` (modeled on `check_ralph_retirement`): file-scoped static assertions, no Python fixture.
- Assertions:
  - each adapter file contains the native-memory section heading and the two-place distinction;
  - `skills/gbrain-interop/SKILL.md` exists and `gbrain-interop` is registered in `.writ/manifest.yaml` and root `SKILL.md`;
  - `.writ/docs/gbrain-recipe.md` exists and contains the round-trip guarantee and graceful-absence language;
  - `forbid_literal` "persistent-database knowledge layer" on active surfaces (mission, README).
- Register with exactly one `memory-interop` line appended to the `CHECKS` array.

---

## Implementation Approach

### Architecture

Documentation + one eval check; no runtime:

```
adapters/{cursor,claude-code,codex,openclaw}.md  → "Native Memory & the Writ Ledger" (one rule, per-platform mechanics)
mission/README/docs                              → verified free of stale framing
scripts/eval.sh                                  → check_memory_interop (asserts adapters + sibling GBrain artifacts)
```

### Consistency Mechanism

One canonical two-place sentence is written into all four adapters; `check_memory_interop` asserts it (or its stable key phrases) in each, making drift a failing check rather than a silent inconsistency.

### Validation Strategy

Script/static (no app test suite):

- `bash scripts/eval.sh --check=memory-interop`
- full `bash scripts/eval.sh` (0 findings, 0 run errors)
- manual read-through confirming each platform's native-memory surface is described accurately

---

## Files in Scope

### Primary (single-writer for this spec)

- `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`, `adapters/openclaw.md` — add the native-memory section
- `scripts/eval.sh` — add `check_memory_interop` + one `CHECKS` entry (Phase 8 single-writer)
- Any active surface found carrying stale mission framing (expected: none to fix)

### Reference (read-only, not edited)

- `skills/gbrain-interop/SKILL.md`, `.writ/docs/gbrain-recipe.md`, `.writ/manifest.yaml`, `SKILL.md` — asserted, not edited (sibling spec owns them)
- `scripts/eval.sh` → `check_ralph_retirement` — model for the new check
- `.writ/product/mission.md` line ~89 — the active "not a memory database or retrieval engine" language

---

## Story Plan

1. **Per-adapter native-memory guidance + mission sweep** — Dependencies: None (within this spec)
2. **`memory-interop` eval check + registration** — Dependencies: Story 1 (asserts the adapter sections) + sibling spec artifacts

---

## Deliverables

- [ ] "Native Memory & the Writ Ledger" section in all four adapters, one consistent two-place rule, per-platform mechanics accurate
- [ ] Each adapter section cross-links the `gbrain-interop` skill / recipe for the external-index layer
- [ ] Active surfaces verified free of stale "persistent-database knowledge layer" framing
- [ ] `check_memory_interop` added to `scripts/eval.sh` + one `CHECKS` entry (additive)
- [ ] `bash scripts/eval.sh --check=memory-interop` passes; full `bash scripts/eval.sh` green

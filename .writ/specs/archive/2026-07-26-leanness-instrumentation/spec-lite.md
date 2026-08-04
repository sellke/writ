# Leanness Instrumentation Rewrite (Lite)

> Source: .writ/specs/2026-07-26-leanness-instrumentation/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Rewrite `scripts/eval-leanness.py` to (1) measure the whole product surface, (2) hard-FAIL on any unmeasured top-level path, (3) report a static `story_context_bytes` proxy, (4) replace growth tolerance with a downward ratchet. Plus ADR-019 and a Tier B doc update.

**Implementation Approach:**
- Registry-driven measurement: each surface declares path, glob, gated flag.
- Preserve the JSON envelope (`structural`/`warnings`/`metrics`) and always-exit-0 contract so `eval.sh check_leanness` wiring changes minimally.
- Retain legacy metric keys (`commands`, `agents`, `skills`, `command_lines`, `command_chars`) so Tier B does not break on first run.
- Replace `GROWTH_TOLERANCE` with per-surface baseline entries carrying an optional `justification`.
- The guardian measures itself — no self-exemption for `eval-leanness.py`.

**Files in Scope:**
- `scripts/eval-leanness.py` — primary rewrite
- `scripts/eval.sh` — `check_leanness` wiring only
- `scripts/tests/test_eval_leanness.sh` — test-first anchor
- `.writ/leanness-baseline.json` — new per-surface schema, reseed
- `.writ/docs/leanness-audit-format.md` — Tier B consumes new metrics
- `.writ/decision-records/adr-019-*.md` — new

**Error Handling:**
- Unmeasured top-level path → structural finding (FAIL)
- Registry path missing on disk → structural finding
- Baseline missing/malformed → structural finding (existing behavior)
- Unjustified surface growth → warning, non-blocking
- `.writ/` growth → reported only, never a finding

**Integration Points:** eval Tier 1 PR gate; Tier B audit ritual reads the metrics block.

---

## For Review Agents

**Acceptance Criteria:**
1. Product coverage is 100%, asserted by the guard — not claimed in prose.
2. A new unmeasured top-level product dir hard-FAILs Tier 1.
3. `story_context_bytes` is byte-identical across runs on an unchanged tree.
4. Unjustified growth warns with surface + delta; a decrease is silent.
5. Full eval Tier 1 green; ADR-019 recorded; Tier B updated.

**Business Rules:**
- Product surface = `commands/`, `agents/`, `skills/`, `adapters/`, `scripts/`, `system-instructions.md`. Gated.
- `.writ/` is ceremony cost — reported, never gated.
- Down is free; up requires a `justification` string.
- Only unmeasured surface hard-fails; growth stays warn-only (ADR-015 Alternative B not reopened).
- Dogfooding-only: no `commands/*.md`, no `/status` behavior change.

**Experience Design:**
- Entry: `bash scripts/eval.sh --check=leanness`; existing PR gate. No new invocation surface.
- Happy path: every top-level path resolves to a rule, nothing grew unjustified, silent exit 0.
- Moment of truth: `scripts/` (18,260 lines) appears in guardian output for the first time.
- Error: unmeasured path names itself and the fix.

**Watch for:** scope creep into *deletion*. This spec builds the instrument only.

---

## For Testing Agents

**Success Criteria:**
1. Coverage guard fires on an undeclared top-level dir and only then.
2. Ratchet: decrease silent, unjustified increase warns, justified increase silent.
3. `story_context_bytes` deterministic across repeated runs.
4. Legacy metric keys still present and correct.
5. `scripts/eval.sh --check=leanness` exits 0 on the clean repo.

**Shadow Paths to Verify:**
- **Happy:** clean repo → `structural: []`, `warnings: []`, full metrics.
- **Nil:** baseline file absent → structural finding, no crash.
- **Empty:** a registry surface exists but is an empty dir → 0 lines, not an error.
- **Upstream error:** malformed baseline JSON → structural finding, exit 0.

**Edge Cases:**
- New top-level dir added → FAIL until declared in registry or out-of-scope list.
- Registry names a path that no longer exists → structural finding.
- `.writ/` grows sharply → reported, never a finding.
- Unreadable file under a measured surface → skip with warning, never crash the run.

**Verification Strategy (methodology repo):** Python behavior is exercised through `scripts/tests/test_eval_leanness.sh` (test-first) plus real runs against this repo and temp fixtures. Shell-harness coverage over the JSON contract; no line-coverage target applies to markdown deliverables.

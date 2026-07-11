# Leanness Guardian (Lite)

> Source: .writ/specs/2026-07-11-leanness-guardian/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Dogfooding-only, two-tier leanness mechanism for Writ-the-framework.
Tier A = CI tripwire (eval check). Tier B = maintainer audit ritual (doc template).
Neither ships as a user-facing command.

**Implementation Approach:**
- Tier A: new `leanness` entry in `CHECKS=()` + `check_leanness` in `scripts/eval.sh`,
  backed by `scripts/eval-leanness.py` (JSON findings, matches existing `eval-*.py`).
- Wiring: check name maps to bash fn `check_${name//-/_}`; emit `add_finding` on breach.
- Tier B: `.writ/docs/leanness-audit-format.md` template + cadence in `self-dogfooding.md`.

**Files in Scope:**
- `scripts/eval-leanness.py` — new metric/parity helper
- `scripts/eval.sh` — register check + `check_leanness`
- `scripts/tests/` — fixture (clean passes, injected orphan fails)
- `.writ/leanness-baseline.json` — committed baseline (31/7/6; ~10,659 lines)
- `.writ/docs/leanness-audit-format.md` + first dated audit
- `.writ/decision-records/adr-015-leanness-self-governance.md`
- `.writ/product/roadmap.md`, `.writ/docs/self-dogfooding.md` — edits

**Non-Duplication (critical):**
- `check_manifest` already owns `commands`/`agents` ↔ manifest parity — DO NOT redo.
- `check_length` owns per-file ceilings — Tier A checks AGGREGATE only.
- `lint-skill`/`skill-lifecycle` own skill boundary/lifecycle — Tier A only counts.
- Tier A's NOVEL check = `commands/*.md` ↔ README table ↔ `/status` allowlist parity.

## For Review Agents

**Acceptance Criteria:**
1. `bash scripts/eval.sh --check=leanness` passes on clean repo.
2. Fixture with injected orphan (command missing from README or status allowlist) FAILS.
3. Zero new user-facing surface: no new `commands/*.md`; `/status` allowlist unchanged.

**Business Rules:**
- Dogfooding-only — never a distributable command.
- Hybrid: hard-FAIL on registry parity; WARN-only on count/weight growth.
- Ritual cadence: per-phase-close/quarterly, NEVER per-release.
- Recommend, never auto-delete surface.

## For Testing Agents

**Success Criteria:**
1. Check passes clean; fails on injected orphan/phantom fixture.
2. Baseline reflects real numbers (31 cmds, 7 agents, 6 skills, ~10,659 lines).
3. Any eval self-test asserting the check list includes `leanness` and passes.

**Shadow Paths to Verify:**
- Happy path: clean repo → PASS.
- Orphan: command not in README table → FAIL (structural).
- Phantom: allowlist names missing command → FAIL (structural).
- Growth: weight > baseline +10% → WARN, non-blocking (exit 0).

**Edge Cases:**
- `_preamble.md` and infra files excluded from parity.
- Missing baseline file → clear error, not silent pass.

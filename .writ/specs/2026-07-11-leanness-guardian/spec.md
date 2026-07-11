# Spec: Leanness Guardian

> **Status:** Complete
> **Created:** 2026-07-11
> **Owner:** @adam
> **Type:** Dogfooding (Writ-the-framework self-governance — does not ship to users)

## Contract Summary

A dogfooding-only, two-tier mechanism that keeps Writ-*the-framework* lean — a
mechanical CI **tripwire** (Tier A) and a cadence-bound judgment **audit ritual**
(Tier B). Neither ships as a user-facing command; both are scoped to this repo's
own surface (`commands/`, `agents/`, `skills/`, adapters).

**Deliverable:** Objective, per-PR bloat detection that stays silent until a real
threshold breaks, plus a repeatable maintainer ritual that re-applies Design
Principle #4 ("does the harness do this natively now?") on a cadence instead of
by chance.

**Hardest Constraint:** The guardian must not itself become bloat, and must never
leak into the distributable surface — users trust Writ as a partner, they do not
audit its internals.

## Why This, Why Now

Writ's core value proposition *is* leanness: "the thin, portable methodology
layer… delegate the mechanics" (`mission.md`). Bloat is therefore an existential
threat to the value prop, not cosmetic debt. Today that discipline is enforced
**only culturally** — Design Principles #1/#4, the maintainer's prune instinct
(which killed `/audit`, `/lessons`, Ralph, `/explain-code`), and ADR-009. Nothing
systematic re-applies it.

Concrete gaps at time of writing:

- **31 commands, 7 agents, 6 skills**; commands total **10,659 lines / ~485K
  chars**. No aggregate ceiling, no trend line. The existing `length` eval check
  is **per-file only** (spec-lite ≤100, `_preamble` ≤80, command files ≤2000) —
  every command is far under the per-file cap, so the real risk is aggregate
  creep, which is unmeasured.
- The **native-displacement test** (Principle #4) was applied once, manually, in
  the 2026 harness audit (→ ADR-010–013). Harnesses keep evolving; nothing
  schedules the next application. This is exactly how Ralph became deprecated —
  but only because the maintainer happened to notice.
- Command **registries drift independently**: `check_manifest` already validates
  `commands/*.md` ↔ `.writ/manifest.yaml`, but the **README command table** and
  the **`/status` allowlist** are separate registries with no parity check.

## Non-Duplication Mandate

This spec exists to *prevent* bloat; it must not *add* bloat. Explicit
boundaries against existing checks:

| Existing mechanism | What it owns | Leanness guardian does NOT redo it |
|---|---|---|
| `check_manifest` (eval.sh) | `commands/`·`agents/` ↔ `.writ/manifest.yaml` parity | Tier A defers manifest parity entirely to this check |
| `check_length` (eval.sh) | Per-file line ceilings | Tier A checks *aggregate* weight only |
| `lint-skill.sh` / `skill-lifecycle` | Skill boundary + lifecycle | Tier A counts skills; does not re-lint them |

Tier A's **novel** structural contribution is the registry parity that nothing
else covers: `commands/*.md` ↔ README command table ↔ `/status` allowlist.

## Scope Boundaries

**Included:**
- `scripts/eval.sh` — register a `leanness` check + `check_leanness`.
- `scripts/eval-leanness.py` — new metric/parity helper (matches existing
  `eval-*.py` pattern), emits findings as JSON.
- Fixture test under `scripts/tests/` — clean repo passes; injected orphan fails.
- `.writ/leanness-baseline.json` — committed baseline seeded with real numbers.
- `.writ/docs/leanness-audit-format.md` — Tier B ritual template.
- First dated audit `.writ/docs/leanness-audit-2026-07-11.md` (dogfood proof).
- `.writ/decision-records/adr-015-leanness-self-governance.md`.
- Edits: `.writ/product/roadmap.md` (entry), `.writ/docs/self-dogfooding.md`
  (cadence note).

**Excluded:**
- Any user-facing command or change to shipping surface (`commands/`,
  `/release`, `/status` behavior — the allowlist is *read*, not changed).
- Auto-pruning — the ritual recommends; a human decides.
- LLM-as-judge overlap detection — structural/heuristic only.
- Command overlap detection in Tier A v1 — deferred to Tier B human judgment.
- Generalizing the tripwire for *users'* own projects — possible future, out now.
- The **product-consistency check** (mission/roadmap drift) — a distinct,
  user-facing spec, deliberately separate.

## Business Rules

- **Dogfooding-only:** no artifact in this spec may be a distributable
  user-facing command. Verifiable: no new `commands/*.md`; `/status` allowlist
  unchanged.
- **Hybrid enforcement (Tier A):** hard-FAIL only on unambiguous structural bugs
  (registry parity); WARN-only (non-blocking) on count/weight growth.
- **Ritual cadence (Tier B):** per-phase-close or quarterly — **never
  per-release** (release cadence is too frequent; an audit there is friction).
- **Recommend, never delete:** the ritual produces prune *candidates* and
  decisions routed to ADR/roadmap; it never removes surface automatically.

## Success Criteria

1. `bash scripts/eval.sh --check=leanness` passes on the current clean repo.
2. A fixture with an injected orphan (command file missing from the README
   command table) or an injected phantom (README table or `/status` allowlist
   names a command with no file) makes the check FAIL. See DEV-001 in
   `drift-log.md`: parity is directional — README ↔ files is bidirectional, the
   `/status` allowlist is checked one-way (phantom-only) because it is a curated
   suggestion subset.
3. `.writ/leanness-baseline.json` reflects real current numbers (31/7/6;
   ~10,659 command lines).
4. `.writ/docs/leanness-audit-format.md` exists and the first dated audit
   (`leanness-audit-2026-07-11.md`) is produced from it.
5. `adr-015-leanness-self-governance.md` and the roadmap entry are committed.
6. **Zero new user-facing surface** — no new `commands/*.md`, `/status`
   allowlist unchanged, `.writ/manifest.yaml` command/agent lists unchanged.
7. Any eval self-test that asserts the check list is updated to include
   `leanness` and still passes.

## Detailed Requirements

### Tier A — Leanness tripwire (Story 1)

`check_leanness` wraps `scripts/eval-leanness.py`, which computes:

**Hard-FAIL (structural, exit non-zero → blocks CI):**
- **Registry parity (directional — see DEV-001):** the README command table is the
  authoritative full registry, so every non-infra `commands/*.md` (exclude
  `_preamble.md`) must appear in it **and** every command it names must have a file
  (bidirectional). The `/status` allowlist is a curated *suggestion* subset, so it
  is checked **one-way only**: every command it names must have a file (phantom),
  but a command is never flagged for being absent from it. Flag orphans (file
  missing from README) and phantoms (either registry names a missing file).
  (Manifest parity is *out* — owned by `check_manifest`.)

**WARN-only (reported, non-blocking):**
- **Count ceilings:** commands > 35, agents > 10, skills > 12 (headroom over
  today's 31/7/6).
- **Aggregate weight:** total command lines/chars vs `.writ/leanness-baseline.json`;
  warn if growth exceeds +10% since the baseline, or crosses an absolute soft
  ceiling. The warning names the baseline file and how to bump it deliberately.

### Tier B — Audit ritual (Story 2)

`.writ/docs/leanness-audit-format.md` defines a repeatable maintainer ritual:
- **Inputs:** latest Tier A metrics, `.writ/manifest.yaml`, adapters.
- **Judgment checklist:** native-capability displacement (Principle #4), command
  overlap, "should this still exist," prune candidates.
- **Output:** dated `.writ/docs/leanness-audit-YYYY-MM-DD.md` — findings →
  decisions → ADR/roadmap follow-ups.
- **Cadence:** per-phase-close or quarterly, documented in `self-dogfooding.md`.
- **Precedent:** `.writ/docs/swot-2026-03-01.md`; the harness audit → ADR-010–013.

## Deliverables Checklist

- [ ] `scripts/eval-leanness.py` created
- [ ] `scripts/eval.sh` — `leanness` registered + `check_leanness` added
- [ ] `scripts/tests/` fixture for leanness added
- [ ] `.writ/leanness-baseline.json` created with real numbers
- [ ] `.writ/decision-records/adr-015-leanness-self-governance.md` created
- [ ] `.writ/docs/leanness-audit-format.md` created
- [ ] `.writ/docs/leanness-audit-2026-07-11.md` (first audit) created
- [ ] `.writ/product/roadmap.md` — leanness guardian entry added
- [ ] `.writ/docs/self-dogfooding.md` — cadence note added

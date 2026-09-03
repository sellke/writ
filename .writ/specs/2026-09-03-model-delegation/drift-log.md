# Drift Log — Model Delegation

> Parent: [`spec.md`](spec.md)

Deviations recorded during implementation. Per-story detail lives in each
story's `## What Was Built` → *Deviations from Spec*; this file carries the
spec-level entries. Append-only; `spec.md` is never auto-modified.

| ID | Story | Severity | Title |
|---|---|---|---|
| DEV-001 | 1 | Small | Entry notice rendered with inline code spans, not a code-span-escaped line |
| DEV-002 | 1 | Small | `cursor/writ.mdc` regenerated whole-file, closing a pre-existing § Skills drift |
| DEV-003 | 1 | Small | `.writ/leanness-baseline.json` gained dated `system_instructions` justifications |
| DEV-004 | 2 | Small | Template comment uses `model_tier=floor`, not `model_tier: floor` |
| DEV-005 | 2 | Medium | Generator drops `model` entirely; `Tier` column replaces `Model` |
| DEV-006 | 2 | Small | Story 1 Gate-5 doc handoff (`README.md`, `AGENTS.md`, `component-contract.md`) edited in Story 2 |

---

## DEV-001 — Entry notice rendered with inline code spans

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-03, Gate 3 review

**Spec said:** technical-spec §5 shows the notice inside one markdown code span with
backslash-escaped backticks (`\`<level>\``). **Implementation did:** the blockquote in
`system-instructions.md` § Model Tiers renders the placeholders as inline code spans —
This command expects `<level>` entry; you're running `<model>/<effort>`. … — with no
backslashes. **Why:** the backslashes were code-span escaping, not content; `spec.md`'s
Feedback model already renders the line this way. **Consequence:** Story 5 pins and the
user-facing line follow the root contract's bytes, not the technical-spec's escaped form.
`spec-lite.md` amended.

## DEV-002 — Mirror regenerated whole-file

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-03, Gate 0 arch-check

**Spec said:** copy § Model Tiers into `cursor/writ.mdc` byte-for-byte. **Implementation
did:** regenerated the mirror as the full `system-instructions.md` body + blank line + the
untouched `## Self-Dogfooding` appendix. **Why:** AC-1.3 requires an empty whole-file diff
outside the appendix, and the mirror was already drifted at the § Skills status paragraph
(`cursor/writ.mdc:252` still carried "Status: adopted." from before commit `8ff2960`). A
section copy could not have met the AC. Appendix verified byte-identical to HEAD.
Verify form that works: `diff <(sed '/^## Self-Dogfooding/,$d' cursor/writ.mdc | sed '$d') system-instructions.md`
(the story's literal command reports one phantom blank-line diff).

## DEV-003 — Leanness baseline justifications

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-03, Gate 0 arch-check

**Spec said:** `eval.sh` → `Findings: 0`; the Story 1 surface omits `.writ/leanness-baseline.json`.
**Implementation did:** § Model Tiers grew 2,809 → 4,521 bytes (five things it never stated
plus the ~730-byte normative blockquote), so dated `lines` (309) and `chars` (22491)
justifications were added under `surfaces.system_instructions.justifications`.
`BASE_BYTE_CAP` in `scripts/eval-leanness.py` was not raised; its pre-existing non-blocking
warning grows from 837 to 2,549 bytes over. **Why:** the ratchet is the only path by which the
root contract can grow with `Findings: 0`, and a dated justification is the file's convention.

## DEV-004 — Template comment uses `model_tier=floor`

**Severity:** Small · **Story:** 2 · **Found:** 2026-09-03, Gate 1

**Spec said:** Task 2.3's example comment reads `…from model_tier: floor (ADR-024)…`.
**Implementation did:** `# model: adapter-resolved from model_tier=floor (ADR-024), never hardcoded` (×6).
**Why:** the colon form would make `grep -rn 'model_tier:' agents/` return 13, breaking AC-2.1's
"exactly 7", and would match the lint's unanchored `model_tier:` scan on prose. `spec-lite.md` amended.

## DEV-005 — Generator drops `model`; `Tier` column replaces `Model`

**Severity:** Medium · **Story:** 2 · **Found:** 2026-09-03, Gate 0

**Spec said:** technical-spec §1:20–24 — make `model` optional in `gen-skill.sh`, "render `model` only
when present as an override", read `model_tier` for the tier column. **Implementation did:**
`gen-skill.sh` reads only `.model_tier` (both parser paths), requires it non-empty, and renders a
single `Tier` column; `model` is neither parsed nor rendered. **Why:** Business Rule 6 removes every
manifest `model:` line, so an override column would be permanently empty — a dead column with no
reader. The story's own Task 2.4 already specified this shape; the tech spec and the story disagreed.
**Flagged for review:** technical-spec §1 should be amended to "drop `model` from the manifest
schema and generator; the agent-file `model:` remains the override". `spec.md` not modified.

## DEV-006 — Story 1's doc handoff edited in Story 2

**Severity:** Small · **Story:** 2 · **Found:** 2026-09-03, Gate 0

**Spec said:** Story 2 surface = `agents/*.md`, manifest, `gen-skill.sh`, `SKILL.md`, `new-command.md`,
`new-skill.md`. **Implementation did:** one-line edits to `README.md:159`, `AGENTS.md:63`,
`.writ/docs/component-contract.md:54` replacing `orchestration`/`capability` and the "commands and
skills carry the same field, but only advisory" clause. **Why:** deferred from Story 1's Gate 5 because
the sentences describe what agents declare, which changes here; leaving them would ship user-facing
docs contradicting the contract. `spec-lite.md` amended.

## DEV-007 — Cursor `floor` cell states the rule; the record names the slug

**Severity:** Small · **Story:** 3 · **Found:** 2026-09-03, Gate 3

**Spec said:** AC-3.1 — "the `floor` cell names whichever value was observed to resolve below the
anchor, listed first in the (a)/(b) order that actually worked." **Implementation did:** the cell
states rule (a) — same-prefix listed slug with effort suffix ≤ `anchor.effort` — in the order that
worked; the literal `claude-opus-5-thinking-high` lives in the dated verification record beneath it
and in `.writ/docs/model-tiers.md:123`. **Why:** Cursor's slug list is version-dependent; a rule plus
a dated observation stays true when the list changes, a literal does not. Intent (observe first,
(a) first) preserved. `spec-lite.md` amended.

## DEV-008 — Opus-origin Cursor sessions emit `degraded`, not a silent collapse

**Severity:** Medium · **Story:** 3 · **Found:** 2026-09-03, Gate 3 (review finding)

**Spec said:** technical-spec §8 — collapse without `degraded` when "origin at family floor (e.g.
`haiku`/low)"; `degraded` for platform rejection or an empty list. `system-instructions.md:286` —
"When the origin already sits at the family floor, `floor` collapses to `anchor` … Otherwise (c)
emits `degraded`." **Implementation did (first draft):** treated "no listed same-prefix slug below
the anchor" (an Opus origin on Cursor today) as the family floor → silent collapse. **Corrected
to:** silent collapse only when the origin is the vendor's bottom tier; when the vendor has lower
tiers Cursor's list does not expose, emit one `degraded(reason=no lower same-family slug listed)`.
**Why:** ADR-024 Decision 1 ("cheapest same-family configuration the platform exposes") supports
the first reading, but its success criterion — "resolves to something other than the anchor, **or a
`degraded` signal says why not**" — and ADR-025's ledger both need the signal; a silent collapse is
exactly the invisible case the ADR set out to surface. The limit is the platform's, which is the
category `degraded` already covers. `adapters/cursor.md` fixed; `spec-lite.md` amended to define
"family floor" as the vendor's bottom tier. Story 4's escalation prose should cite this.

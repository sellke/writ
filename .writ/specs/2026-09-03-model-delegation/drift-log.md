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

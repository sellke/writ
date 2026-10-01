# Product Check Direction: Verification Feeds Realignment

> **Status:** Not Started
> **Created:** 2026-10-01
> **Owner:** @unknown
> **Dependencies:** []
> **Origin:** Promoted from issue: [`2026-10-01-product-lint-misread-as-verify-spec`](../../issues/improvements/2026-10-01-product-lint-misread-as-verify-spec.md). The issue proposed moving the lint into `/plan-product`; discovery rejected that because `/plan-product` is the baseline and realignment step, not a post-implementation check. This contract keeps the lint in `/verify-spec` and fixes the direction instead.

## Specification Contract

**Deliverable:** Product-doc verification reads, everywhere it is mentioned, as a post-implementation check whose findings feed realignment. `/verify-spec --product` stays where it is. `/plan-product --reconcile` stops pointing at it as a confirmation step and hands back to delivery. `/implement-phase` and `/release`, the two moments product docs fall behind, each suggest it in one line.

**Must Include:** One direction of flow, stated the same way in every file that mentions both commands: verification surfaces drift, realignment acts on it. No planning step points to a verification step.

**Hardest Constraint:** `verify-spec.md`, `implement-phase.md`, and `release.md` are recorded byte-budget violators under a one-way ratchet in `scripts/tests/test_governor_enforcement.py`. Story 1's rewording must not grow `verify-spec.md`; Story 2's additions re-pin `implement-phase.md` and `release.md` with a disclosed comment.

**Lifecycle the spec must preserve:**

| Stage | Command | Role |
|---|---|---|
| Baseline | `/plan-product` | Establish strategy and roadmap, early or at a reset |
| Delivery | `/create-spec` → `/implement-spec` / `/implement-phase` | Build |
| Verification | `/verify-spec` (spec), `/verify-spec --product` (product docs) | After implementation: has anything drifted from what shipped? |
| Realignment | `/plan-product --reconcile` | Revise the baseline when verification shows drift |

**Stories:**
1. **Reframe the boundary.** Rewrite the before/after framing in `verify-spec.md`, `verify-spec.lean.md`, and `plan-product.md`; replace Step R4's closing suggestion with a hand-back to delivery; update `verify-spec`'s description and `--product` Modes row; add eval pins that keep the wrong-direction pointer from returning.
2. **Suggest the check where drift appears.** One line in `/implement-phase`'s Step 4.2 completion report and one in `/release`'s Phase 5 summary, each pointing to `/verify-spec --product`. The release summary's existing reconcile pointer is replaced, not duplicated. Re-pin both ratchet entries with disclosure. Depends on Story 1.

**Success Criteria:**
- `rg -n "verify-spec --product" commands/plan-product.md` matches only Step R2 lines that consume its findings, never Step R4.
- No file in `commands/` describes `--product` as running "before" a decision or `--reconcile` as running "after" `--product` in the same ceremony.
- The `/implement-phase` and `/release` completion templates each contain one `/verify-spec --product` line.
- `uv run pytest` passes and `bash scripts/eval.sh` reports Findings 0.

**Scope Boundaries:**
- **Included:** wording in the five command files above, the two completion lines, eval pins, ratchet re-pins, closing the source issue with a `## Resolution` line.
- **Excluded:** renaming or moving the lint; any change to checks P1–P4, their dispositions, or the report path; a new command; Phase 12 work; `CHANGELOG.md` and `.writ/product/verification-*.md` history.

**⚠️ Technical Concerns:**
- `verify-spec.md` byte ratchet: rewording only, net bytes at or below today's. If a sentence must grow, cut an equal amount elsewhere in the same section.
- `retro.md:170` already points in the right direction (verify, then reconcile) and stays unchanged; it is the model wording.

**💡 Recommendations:** Write the direction sentence once in `verify-spec.md`'s Product Consistency section, then reuse its exact wording in `plan-product.md` and the lean twin so an eval `require_literal` can pin all three.

---

## 🎯 Experience Design

**Entry point.** A maintainer finishes a phase or a release and reads its completion output; or reads `/plan-product --reconcile`'s closing step; or reads either command's Modes/Boundary text.

**Happy path.**
1. `/implement-phase` or `/release` completes and its summary says: product docs may now lag what shipped, run `/verify-spec --product`.
2. `/verify-spec --product` reports drift (P1, P2, P4) and regenerates stale derivatives (P3).
3. If drift needs a decision, the maintainer runs `/plan-product --reconcile`, which ends by pointing back to delivery (`/create-spec`).

**Moment of truth.** The maintainer never sees a verification step suggested immediately after a planning step.

**Feedback model.** Unchanged: the product report at `.writ/product/verification-YYYY-MM-DD.md`.

**Error experience.** No `.writ/product/`: `/verify-spec --product` skips silently as today, and the two new completion lines are omitted when `.writ/product/` is absent.

## 📋 Business Rules

1. **One direction.** Verification may point to realignment. Realignment points to delivery. Neither `/plan-product` mode points to a verification step as its next action.
2. **Consumption is allowed.** `/plan-product --reconcile` Step R2 may still read recent `/verify-spec --product` findings; reading verification output is not pointing to it.
3. **No behavior change to the lint.** P1–P4 logic, dispositions, auto-fix scope, `--product --check`, and the report path are byte-for-byte unchanged in substance.
4. **Conditional lines.** Each new completion line appears only when `.writ/product/` exists.
5. **Replace, don't stack.** `/release`'s existing "consider `/plan-product --reconcile`" summary pointer is replaced by the verification pointer; the summary gains no second product line.

## Detailed Requirements

### `commands/verify-spec.md`
- `description:` frontmatter mentions product docs as a second scope ("a spec, or with `--product` the product docs, after implementation").
- Modes row for `--product`: "after specs ship" framing.
- Line 37 callout and the Product Consistency "Boundary (critical)" paragraph (lines 625–631): replace "lint you run before deciding anything" and "(before)/(after)" with the direction sentence. Drop the `/assess-spec` analogy, which pairs a pre-implementation and a post-implementation command and does not describe this relationship.

### `commands/verify-spec.lean.md`
- Mirror the same edits at lines 33–35 and 295. Section headings stay identical so `test_lean_commands.py` parity is untouched.

### `commands/plan-product.md`
- Reconcile "Boundary (critical)" paragraph (lines 37–45): reconcile realigns the baseline after verification (or a direction change) shows drift; drop "(before)" and the `/assess-spec` analogy.
- Step R4 closing paragraph (line 106): replace the `/verify-spec --product` suggestion with the hand-back: "suggest `/create-spec` for the next roadmap item"; keep the roadmap-revision note.
- Step R2 references (lines 66, 74) stay: they consume findings.

### `commands/implement-phase.md`
- Step 4.2 report template: one line after `Phase status:`, shown only when `.writ/product/` exists: `Product docs may lag what shipped — run /verify-spec --product.`

### `commands/release.md`
- Phase 5 summary `Roadmap:` line: replace the reconcile pointer with `— run /verify-spec --product to check product docs against what shipped`.
- Line 397 boundary sentence: order the two as "`/verify-spec --product`'s P1/P4 checks, then `/plan-product --reconcile`".
- Line 399 derivative note: point to `/verify-spec --product`, which regenerates `mission-lite.md` (P3).

## Implementation Approach

Pure markdown edits plus eval and test pins. Story 1 writes the direction sentence and pins it with `require_literal` across `verify-spec.md`, `verify-spec.lean.md`, and `plan-product.md`, and adds a `forbid_literal` on `plan-product.md` for the R4 suggestion. Story 2 adds the two completion lines, pins each with `require_literal`, and re-pins the two ratchet entries with a dated, disclosed comment in `test_governor_enforcement.py`, following the file's existing comment convention. See `sub-specs/technical-spec.md`.

# Product Check Direction (Lite)

> Source: .writ/specs/2026-10-01-product-check-direction/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Product-doc verification reads as a post-implementation check whose findings feed realignment; `/plan-product --reconcile` hands back to delivery; `/implement-phase` and `/release` suggest `/verify-spec --product`.

**Implementation Approach:**
- Markdown edits only, plus eval pins and two ratchet re-pins
- One direction sentence, reused verbatim in three files: "Verification surfaces drift after implementation; `/plan-product --reconcile` realigns the baseline when it does."
- Lint behavior (P1–P4, dispositions, report path) unchanged
- Forbid pins on both verify-spec files: "a lint you run before deciding anything", "consistency lint (before)", "lints (before" (DEV-005)

**Files in Scope:**
- `commands/verify-spec.md` — description, `--product` Modes row, line 37 callout, Boundary paragraph (625–631), Integration row for `--reconcile` (DEV-001); net bytes ≤ 0
- `commands/verify-spec.lean.md` — mirror description, lines 33–35, 295; headings unchanged
- `scripts/tests/test_lean_commands.py` — re-pin `DEFAULT_SHA256` for each edited default command (DEV-003)
- `scripts/tests/test_product_check_direction.py` — spec-attributed tests for AC-1.1–AC-2.5, incl. pin mutations (DEV-006)
- `commands/plan-product.md` — Reconcile Boundary (37–45); Step R4 closing (106) → suggest `/create-spec`
- `commands/implement-phase.md` — one conditional line in Step 4.2 template
- `commands/release.md` — Phase 5 `Roadmap:` line (518), lines 397, 399
- `scripts/eval.sh` — `check_product_check_direction` pins, run as `--check=product-check-direction` (DEV-004)
- `scripts/tests/test_governor_enforcement.py` — re-pin implement-phase (10200) and release (7576) with dated disclosure

**Error Handling:**
- No `.writ/product/` → new completion lines omitted (implement-phase Step 4.2 line; release Phase 5 `Roadmap:` line, DEV-008); lint skips silently (unchanged)

**Integration Points:**
- `retro.md:170` already correct (verify then reconcile); unchanged, model wording
- `test_lean_commands.py:159` heading parity must stay green

---

## For Review Agents

**Acceptance Criteria:**
1. The direction sentence appears verbatim in `verify-spec.md`, `verify-spec.lean.md`, `plan-product.md` `[AC-1.1]`
2. No command file frames `--product` as "before" a decision or reconcile as its "after" `[AC-1.1, AC-1.2]`
3. Step R4 suggests `/create-spec`, not `/verify-spec --product`; Step R2 still consumes findings `[AC-1.3]`
4. `implement-phase` Step 4.2 and `release` Phase 5 each carry one conditional `/verify-spec --product` line; release's reconcile pointer replaced, not stacked `[AC-2.1, AC-2.2, AC-2.3]`
5. `verify-spec.md` does not grow (its ratchet entry re-pinned down if it shrinks, DEV-002); implement-phase and release ratchet entries re-pinned with disclosure `[AC-1.5, AC-2.4]`

**Business Rules:**
- One direction: verification → realignment → delivery
- Reading verification findings is not pointing to verification
- No change to P1–P4 substance
- New lines conditional on `.writ/product/` existing

**Experience Design:**
- Entry: phase or release completion output
- Happy path: completion → `/verify-spec --product` → `/plan-product --reconcile` if needed → `/create-spec`
- Moment of truth: no verification step suggested right after a planning step
- Feedback: unchanged product report
- Error: no product dir → lines omitted

---

## For Testing Agents

**Success Criteria:**
1. `uv run pytest` passes (lean parity, governor ratchet)
2. `bash scripts/eval.sh` Findings 0, new pins present
3. Mutation: restoring the old R4 sentence makes `eval.sh` report a finding

**Shadow Paths to Verify:**
- **Happy path:** completion → verify → reconcile → create-spec wording chain intact
- **Empty input:** no `.writ/product/` → lines omitted
- **Upstream error:** reconcile with no prior verification still derives drift (R2 unchanged)

**Edge Cases:**
- `verify-spec.lean.md` drifts from canonical → lean parity test fails
- Re-pin without dated comment → violates ratchet convention

**Coverage Requirements:**
- Every new pin proven to bite by one mutation

**Test Strategy:**
- Eval `require_literal`/`forbid_literal` plus existing pytest suites

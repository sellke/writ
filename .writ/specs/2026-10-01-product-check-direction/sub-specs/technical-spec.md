# Technical Spec: Product Check Direction

> Spec: [`../spec.md`](../spec.md)

## Files and Edits

| File | Story | Edit | Byte constraint |
|---|---|---|---|
| `commands/verify-spec.md` | 1 | `description:`, `--product` Modes row (line 35), callout (line 37), Product Consistency Boundary paragraph (lines 625–631) | Ratchet entry `10898`: net ≤ 0 |
| `commands/verify-spec.lean.md` | 1 | Lines 33–35 and 295, mirroring the canonical file | Headings unchanged (`test_lean_commands.py:159`) |
| `commands/plan-product.md` | 1 | Reconcile Boundary paragraph (lines 37–45), Step R4 closing (line 106) | Not a recorded violator; keep growth small |
| `scripts/eval.sh` | 1, 2 | `require_literal` / `forbid_literal` pins (new check function `check_product_check_direction`, registered with the other checks) | — |
| `commands/implement-phase.md` | 2 | One conditional line in the Step 4.2 template | Ratchet entry `10200`: re-pin with disclosure |
| `commands/release.md` | 2 | Phase 5 `Roadmap:` line (518), boundary sentence (397), derivative note (399) | Ratchet entry `7576`: re-pin with disclosure |
| `scripts/tests/test_governor_enforcement.py` | 2 | Updated values at lines 567–568 and a dated comment in the existing convention | — |
| `.writ/issues/improvements/2026-10-01-product-lint-misread-as-verify-spec.md` | 2 | Append `## Resolution` with date and commit | — |

## The Direction Sentence

Write once, reuse verbatim so one `require_literal` string pins all three files:

> Verification surfaces drift after implementation; `/plan-product --reconcile` realigns the baseline when it does.

## Eval Pins (Story 1)

- `require_literal` the direction sentence in `commands/verify-spec.md`, `commands/verify-spec.lean.md`, `commands/plan-product.md`.
- `forbid_literal` in `commands/plan-product.md`: `suggest \`/verify-spec --product\` to confirm`.
- `forbid_literal` in `commands/verify-spec.md` and `.lean.md`: `a lint you run before deciding anything` and `consistency lint (before)`.

## Eval Pins (Story 2)

- `require_literal` in `commands/implement-phase.md`: `run /verify-spec --product`.
- `require_literal` in `commands/release.md`: `run /verify-spec --product to check product docs against what shipped`.
- `forbid_literal` in `commands/release.md`: `consider \`/plan-product --reconcile\` if \`mission-lite.md\` needs a matching update`.

## Error & Rescue Map

Not applicable: no data flow, network, or runtime path changes. The only failure modes are test and eval failures, which are the verification for each story.

## Shadow Paths

| Path | Expected |
|---|---|
| Happy path | Phase or release completes, summary points to `/verify-spec --product`, findings feed `/plan-product --reconcile`, which hands back to `/create-spec` |
| No `.writ/product/` | Completion lines omitted; `/verify-spec --product` skips silently (unchanged) |
| Reconcile run with no prior verification | Step R2 derives drift itself (unchanged); R4 ends with the delivery hand-back |

## Verification

```bash
uv run pytest
bash scripts/eval.sh            # Findings 0
rg -n "verify-spec --product" commands/plan-product.md   # R2 lines only
```

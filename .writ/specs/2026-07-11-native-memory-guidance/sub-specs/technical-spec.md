# Technical Spec: Native-Memory Guidance Per Adapter

> Parent: [`../spec.md`](../spec.md)
> Scope: implementation-level design for the per-adapter sections and the `memory-interop` eval check

## Design Decisions

### D1 — One canonical sentence, four placements

The two-place rule is authored once and reused verbatim (or with only trivial platform substitution) in each adapter. Example canonical form:

> **Native memory holds session preferences and trivia; the Writ ledger holds negotiated decisions, conventions, and lessons — the reviewable markdown layer that feeds native memory and any external index.**

Consistency is then a *checkable property*: `check_memory_interop` asserts stable key phrases in each adapter, so a future edit that drifts one platform fails CI rather than silently diverging.

### D2 — Ground each section in the platform's real surface

| Adapter | Native-memory surface (real) | Section anchor |
|---|---|---|
| `cursor.md` | Cursor Memories + semantic codebase indexing | near "Knowledge Loading" / "Customization" |
| `claude-code.md` | `CLAUDE.md` (auto-loaded) + `.claude/agent-memory/` (persistent agent memory) | near the memory feature sections |
| `codex.md` | `AGENTS.md` (Writ-owned block + user region), `AGENTS.override.md` | near "AGENTS.md layering" |
| `openclaw.md` | session state / file-based context (no ambient persistent store) | near "Skills" / context handling |

Each section names what belongs where *on that platform* — e.g., "let Cursor Memories hold your preferred tone; write the decision to `.writ/decision-records/`."

### D3 — Three-layer model, stated consistently

Every adapter section closes the loop across three layers: **native memory** (session prefs/trivia, per platform) → **ledger** (canonical, reviewable markdown) → **external index** (GBrain, disposable — see `gbrain-interop` skill / `.writ/docs/gbrain-recipe.md`). The cross-link keeps this spec and the sibling recipe telling one story.

### D4 — `memory-interop` is a documentation check, not a fixture harness

Model on `check_ralph_retirement`: `require_literal` / `forbid_literal_ci` over named files, no Python scenario script. This keeps the check cheap, deterministic, and readable. It is the single additive edit this spec makes to `scripts/eval.sh`.

### D5 — Single-writer discipline on `scripts/eval.sh`

For Phase 8, only this spec edits `scripts/eval.sh`. The sibling spec deliberately does not, so the two isolated lanes never collide on the shared file. The edit is additive: one `check_memory_interop` function definition + one `memory-interop` line in `CHECKS`. Existing checks are untouched and unordered relative to the new one.

## Error & Rescue Map

| Condition | Detection | Rescue |
|---|---|---|
| Sibling GBrain artifacts absent | `check_memory_interop` `require_literal` on skill/recipe fails | Run order is wrong; the declared dependency + sequential execution prevents this — do not weaken the check to pass |
| One adapter missing the section | `require_literal` per-adapter fails | Add the section to the named adapter |
| Adapter sections drift apart | key-phrase assertion fails on the drifted file | Restore the canonical sentence |
| Stale mission framing survives | `forbid_literal` on active surface fails | Replace the stale active wording; leave historical ADRs/specs alone |
| Existing check accidentally altered | full `eval.sh` regressions elsewhere | Keep the edit strictly additive |

## Shadow Paths

- **Clean mission (expected):** the sweep finds nothing to fix; the value is the *asserted* guarantee, not a diff.
- **Wrong execution order:** the eval check fails loudly rather than silently passing — a feature, not a bug.
- **New adapter added later:** the check is the place to extend coverage; documented for future maintainers.

## Validation

- `bash scripts/eval.sh --check=memory-interop`
- full `bash scripts/eval.sh` (0 findings, 0 run errors) on the merged phase branch
- read-through of each adapter section for platform accuracy

## File × Story Matrix

| File | Story 1 | Story 2 |
|---|---|---|
| `adapters/cursor.md` | ✅ section | — |
| `adapters/claude-code.md` | ✅ section | — |
| `adapters/codex.md` | ✅ section | — |
| `adapters/openclaw.md` | ✅ section | — |
| mission/README/docs (sweep) | ✅ verify/fix | — |
| `scripts/eval.sh` | — | ✅ add check + register |

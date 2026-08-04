# Phase 1: Foundation — Spec Lite

> Source: spec.md
> Last Updated: 2026-03-14
> Purpose: Efficient AI context for implementation

## What We're Building

Four features that fix Writ's top pain points and elevate the quality of planning conversations:

1. **`/prototype`** — Top-level command for small-to-medium changes. No spec required. Quick 2-3 question contract → coding agent (TDD) → lint/typecheck → done. Escape hatch to escalate if complexity emerges.

2. **Tiered spec-healing** — Review agent extension that detects spec drift and responds proportionally. Small deviations auto-heal. Medium deviations get flagged. Large deviations pause the pipeline. Default to Medium when ambiguous. Drift logged in `drift-log.md` per spec; original spec never modified.

3. **`/refresh-command`** — Scans agent transcripts after command use, identifies friction patterns, proposes concrete diffs to command files. Local-first (project copy). Optional promotion review for upstreaming to Writ core.

4. **`/plan-product` gstack enhancement** — Aspirational framing and opinionated posture for product planning. Posture selection (EXPANSION / HOLD / REDUCTION), mandatory premise challenge, dream state mapping, failure surface analysis, mandatory architecture diagrams, opinionated "I recommend X because Y" format throughout. Research: gstack analysis. Decision: DEC-006.

## Key Design Decisions

- `/prototype` is separate from `--quick` mode. `--quick` operates within a spec; `/prototype` operates without one.
- Spec-healing lives inside the review agent, not as a separate gate. Less ceremony.
- `/refresh-command` works on agent transcript `.jsonl` files. It should be able to refresh itself.
- All outputs are markdown files. No runtime code, no CLI, no server.
- `/plan-product` enhancement is a posture shift, not just feature additions. Design Principle 6: "Opinionated by default — lead with the recommendation, explain why, then offer alternatives."

## Story Dependencies

Batch 1 (parallel): `/prototype` command, spec-healing agent extension, `/refresh-command` core
Batch 2 (parallel): Drift report format, promotion pipeline, command overlay system, `/plan-product` gstack enhancement
Batch 3 (sequential): Integration testing & dogfooding

## Success Criteria

- `/prototype` < 5 min human wall-clock for small changes
- Spec-healing catches real drift in ≥3/5 stories without false positives
- `/refresh-command` produces ≥1 actionable improvement per command analyzed
- `/plan-product` challenges premises and leads with opinionated recommendations

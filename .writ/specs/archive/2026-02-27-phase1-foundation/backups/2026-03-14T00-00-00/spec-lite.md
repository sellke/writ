# Phase 1: Foundation — Spec Lite

> Source: spec.md
> Purpose: Efficient AI context for implementation

## What We're Building

Three features that fix Writ's top three pain points:

1. **`/prototype`** — Top-level command for small-to-medium changes. No spec required. Quick 2-3 question contract → coding agent (TDD) → lint/typecheck → done. Escape hatch to escalate if complexity emerges.

2. **Tiered spec-healing** — Review agent extension that detects spec drift and responds proportionally. Small deviations auto-heal. Medium deviations get flagged. Large deviations pause the pipeline. Default to Medium when ambiguous. Drift logged in `drift-log.md` per spec; original spec never modified.

3. **`/refresh-command`** — Scans agent transcripts after command use, identifies friction patterns, proposes concrete diffs to command files. Local-first (project copy). Optional promotion review for upstreaming to Writ core.

## Key Design Decisions

- `/prototype` is separate from `--quick` mode. `--quick` operates within a spec; `/prototype` operates without one.
- Spec-healing lives inside the review agent, not as a separate gate. Less ceremony.
- `/refresh-command` works on agent transcript `.jsonl` files. It should be able to refresh itself.
- All outputs are markdown files. No runtime code, no CLI, no server.

## Story Dependencies

Batch 1 (parallel): `/prototype` command, spec-healing agent extension, `/refresh-command` core
Batch 2 (parallel): Drift report format, promotion pipeline, command overlay system
Batch 3 (sequential): Integration testing & dogfooding

## Success Criteria

- `/prototype` < 5 min human wall-clock for small changes
- Spec-healing catches real drift in ≥3/5 stories without false positives
- `/refresh-command` produces ≥1 actionable improvement per command analyzed

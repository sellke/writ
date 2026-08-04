# File Ownership Boundaries — Spec Lite

> Compact context for agents. Full spec: `spec.md`
> **Shipped:** Writ **0.8.0** (2026-03-20) — see `CHANGELOG.md`.

## What

Add structured file ownership boundaries (owned / readable / out-of-scope) to the per-story pipeline. Computed before coding, passed to the coding agent, verified by the review agent.

## Key Constraints

- Advisory, not enforced — flag violations, don't hard-block
- File-level with glob support
- Computed from story tasks, tech spec, and assess-spec Check 5 data
- No boundaries in `/prototype` mode (lightweight path unchanged)

## Files in Scope

- `commands/implement-story.md` — new Gate 0.5 boundary computation step
- `agents/coding-agent.md` — new `boundary_map` input parameter + deviation flagging
- `agents/review-agent.md` — boundary compliance verification
- `agents/architecture-check-agent.md` — minor: arch warnings override boundaries

## Pipeline Position

```
Gate 0 (Arch Check) → Gate 0.5 (Boundary Comp) [NEW] → Gate 1 (Coding) → ... → Gate 3 (Review)
```

## Success Criteria

- Coding agent receives `boundary_map` with three tiers
- Cross-boundary modifications flagged in agent output
- Review agent verifies boundary compliance
- assess-spec Check 5 data feeds into computation when available

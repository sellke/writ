# Spec: File Ownership Boundaries

> **Status:** Complete
> **Created:** 2026-03-20
> **Spec Type:** Pipeline Enhancement

## Contract

**Deliverable:** Add file ownership boundaries to the per-story pipeline — a structured "owns / must-not-touch" constraint passed to the coding agent at Gate 1, derived from story tasks, the technical spec, and (when available) `/assess-spec` Check 5 file overlap data.

**Must Include:** A boundary computation step that runs before the coding agent, and a structured input parameter the coding agent respects.

**Hardest Constraint:** Boundaries must not be so rigid they block legitimate cross-cutting changes. A story touching `src/auth/middleware.ts` to add a new auth check shouldn't be blocked from updating the route that uses it — but it should be flagged if it starts modifying unrelated billing code.

## Background

The orchestrator prompt pattern ("spawn a subagent with the files it owns, the files it must not touch") revealed a gap in Writ's pipeline. Currently:

- The coding agent gets `related_files` — an advisory list with no enforcement semantics
- Gate 0 (arch check) can produce ad-hoc "don't touch X" warnings, but only when it spots a risk
- `/assess-spec` Check 5 detects file overlap between stories, but that data doesn't flow downstream
- Gate 2.5 classifies change surface *after* coding — too late to prevent overreach

No agent receives an explicit "you own these files; flag if you touch these" constraint. When multiple stories touch overlapping areas, the only guard is sequencing — there's no boundary awareness within a story's execution.

## Design

### Three-Tier Boundary Model

| Tier | Semantics | Agent Behavior |
|------|-----------|----------------|
| **Owned** | Files the story should create or modify | Normal implementation — these are the story's deliverables |
| **Readable** | Files the story may import/reference but not modify | Read for context, import from, but do not edit |
| **Out-of-scope** | Everything else | Flag in output if touched; review agent verifies |

### Boundary Granularity

File-level with glob support. Examples:

```
owned:
  - src/auth/session.ts
  - src/auth/session.test.ts
  - src/routes/login.ts

readable:
  - src/auth/types.ts
  - src/middleware/auth.ts
  - src/config/auth.config.ts
```

Directory-level is too coarse (would own entire `src/auth/` when only modifying one file). Function-level is impractical (agents operate on files, not AST nodes).

### Advisory, Not Enforced

Boundaries are advisory — the coding agent flags boundary violations in its output rather than being hard-blocked from writing files. Hard-blocking would require wrapping file write operations, which is fragile and platform-dependent. The review agent (Gate 3) verifies boundary compliance as part of its check.

### Pipeline Integration

```
Gate 0   (Arch Check)     — unchanged, still produces ad-hoc warnings
Gate 0.5 (Boundary Comp)  — NEW: compute owned/readable/out-of-scope from story + tech spec
Gate 1   (Coding Agent)   — receives boundary_map as new structured input
Gate 2   (Lint/Typecheck)  — unchanged
Gate 2.5 (Change Surface)  — unchanged, but can cross-reference against boundaries
Gate 3   (Review Agent)    — NEW: verify boundary compliance, flag violations
```

### Boundary Computation Sources

1. **Story tasks** — file paths mentioned in task descriptions ("Modify `src/auth/session.ts`", "Create `src/auth/refresh.ts`")
2. **Technical spec** — file paths in the architecture section
3. **`/assess-spec` Check 5** — when available, the file overlap map provides "other stories touch these files" data, which feeds the readable/out-of-scope classification
4. **Gate 0 warnings** — arch-check "don't touch X" warnings override computed boundaries (promote a file from owned to readable or out-of-scope)
5. **Codebase import graph** — files imported by owned files are auto-classified as readable

### Edge Cases

| Scenario | Handling |
|----------|----------|
| Story task says "modify X" but X is in another story's overlap area | Classify as owned with a `⚠️ overlap` flag; review agent gets extra scrutiny signal |
| Coding agent needs to modify a readable file to complete the task | Flag in output as `BOUNDARY_DEVIATION: modified readable file [path] because [reason]`; review agent evaluates |
| No file paths extractable from story tasks | Fall back to directory-level inference from task descriptions; warn that boundaries are approximate |
| `/prototype` mode | No boundaries — lightweight path stays boundary-free |

## Success Criteria

1. The coding agent receives a `boundary_map` structured input with owned/readable/out-of-scope tiers
2. Boundaries are computed from story tasks + tech spec, not guessed
3. Cross-boundary modifications are flagged in coding agent output (not silently blocked)
4. Gate 3 (review agent) verifies boundary compliance and reports violations
5. `/assess-spec` Check 5 data feeds into boundary computation when available
6. Boundary computation adds < 10 seconds to the pre-coding phase

## Scope Boundaries

**Included:**
- New Gate 0.5 boundary computation step in `commands/implement-story.md`
- New `boundary_map` input parameter in `agents/coding-agent.md`
- Boundary compliance check in `agents/review-agent.md`
- Integration hook for `/assess-spec` Check 5 data
- Documentation in technical spec

**Excluded:**
- No changes to `/implement-spec` orchestration logic
- No runtime file locking or write-prevention
- No changes to `/prototype` (lightweight path stays boundary-free)
- No changes to `system-instructions.md` or `writ.mdc`
- No changes to `/assess-spec` itself (it already produces the data; we just consume it)

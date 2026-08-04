# Technical Spec: File Ownership Boundaries

## Architecture

This enhancement adds a boundary computation step to the per-story pipeline and structured boundary inputs to two agents. No new files are created in target projects — this is purely a methodology change to Writ's command and agent specifications.

### File Map

| File | Change Type | Story |
|------|-------------|-------|
| `commands/implement-story.md` | Add Gate 0.5 section + boundary_map schema | 1 |
| `agents/coding-agent.md` | Add boundary_map input + deviation output format | 2 |
| `agents/review-agent.md` | Add boundary compliance section | 2 |
| `agents/architecture-check-agent.md` | Minor: note boundary override semantics in warnings | 2 |
| `commands/implement-story.md` | Add assess-spec Check 5 data loading to Gate 0.5 | 3 |

### boundary_map Schema

```markdown
### File Ownership Boundaries

**Owned** (create or modify):
- `src/auth/session.ts`
- `src/auth/session.test.ts`
- `src/routes/login.ts`

**Readable** (import/reference, do not modify):
- `src/auth/types.ts` _(imported by owned files)_
- `src/middleware/auth.ts` _(arch-check: do not modify directly)_
- `src/billing/invoice.ts` _(⚠️ overlap: also touched by Story 4)_

**Out-of-scope** (flag if touched):
- Everything not listed above
```

The schema is markdown (not JSON) because agents process markdown natively, and the boundary_map is passed as part of the prompt context — not parsed programmatically.

### Gate 0.5 Computation Algorithm

```
1. EXTRACT file paths from story implementation tasks
   - Match patterns: "Modify `path`", "Create `path`", "Update `path`", "Add to `path`"
   - Match code blocks containing file paths
   → These become OWNED files

2. EXTRACT file paths from technical spec (architecture section, file map)
   - Cross-reference with current story: if the tech spec assigns a file to THIS story → OWNED
   - If the tech spec assigns a file to ANOTHER story → READABLE with overlap flag

3. COMPUTE import graph for OWNED files
   - For each owned file that exists in the codebase, scan its imports
   - Imported files that are not already OWNED → READABLE
   - Limit depth to 1 level (direct imports only — transitive imports are too broad)

4. APPLY Gate 0 overrides
   - For each "Warnings for Coding Agent" entry from arch-check:
     - If warning says "do not modify X" → reclassify X as READABLE (if owned) or OUT-OF-SCOPE
     - Preserve the warning text as annotation on the boundary entry

5. APPLY assess-spec Check 5 data (when available) [Story 3]
   - For each file area flagged as shared between stories:
     - If file is OWNED by current story but also touched by other stories → keep OWNED, add overlap flag
     - If file is NOT in current story's tasks but in shared area → READABLE with overlap flag

6. CLASSIFY remaining
   - Everything not OWNED or READABLE → OUT-OF-SCOPE (implicit, not enumerated)
```

### Pipeline Placement

```
implement-story Step 3: Run Pipeline

Gate 0:   Architecture Check (readonly, fast model)
          ↓ produces: verdict + warnings
Gate 0.5: Boundary Computation (inline, no agent)     ← NEW
          ↓ produces: boundary_map
Gate 1:   Coding Agent (receives boundary_map as input)
          ↓ produces: implementation + any BOUNDARY_DEVIATION/VIOLATION flags
Gate 2:   Lint & Typecheck
Gate 2.5: Change Surface Classification
Gate 3:   Review Agent (receives boundary_map + coding agent deviation flags)
          ↓ verifies: boundary compliance
```

### Coding Agent Changes

**New input parameter:**

| Parameter | Description |
|-----------|-------------|
| `boundary_map` | File ownership boundaries (owned/readable/out-of-scope). When absent, skip boundary checking. |

**New prompt section (added to coding agent prompt template):**

```
### File Ownership Boundaries

{boundary_map}

RULES:
- You may freely create/modify files listed as OWNED
- You may read/import files listed as READABLE but must not modify them
- If you need to modify a READABLE file, include a BOUNDARY_DEVIATION entry in your output
  explaining why — the review agent will evaluate
- If you modify any other file, include a BOUNDARY_VIOLATION entry
- Boundary deviations are not failures — they're signals for the review agent
```

**New output section:**

```markdown
### Boundary Compliance

BOUNDARY_DEVIATION: Modified readable file `src/auth/types.ts`
  Reason: Added `RefreshToken` type export needed by new session refresh function

BOUNDARY_VIOLATION: None
```

### Review Agent Changes

**New review section:**

The review agent receives the boundary_map and any deviations from the coding agent. It adds a "Boundary Compliance" section to its review:

```markdown
### Boundary Compliance

| File | Tier | Action | Justified? | Notes |
|------|------|--------|-----------|-------|
| src/auth/types.ts | Readable | Modified | ✅ Yes | Added necessary type export |
| src/billing/fees.ts | Out-of-scope | Modified | ❌ No | Unrelated to story scope |
```

Unjustified violations are flagged as Major findings. Justified deviations are noted but do not affect the PASS/FAIL verdict.

### Skip Conditions

| Condition | Gate 0.5 Behavior |
|-----------|-------------------|
| `--quick` flag | Skipped (consistent with Gate 0 skip) |
| `/prototype` mode | Skipped (lightweight path stays boundary-free) |
| `--review-only` flag | Skipped (no coding phase) |
| No file paths extractable | Runs with approximate directory-level boundaries + warning |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Boundaries too restrictive — agent wastes iterations fighting constraints | Medium | Medium | Advisory model: flag, don't block. Review agent evaluates justifications. |
| File path extraction misses relevant files | Medium | Low | Import graph analysis catches most missing readables. Fallback to directory inference. |
| assess-spec data stale or absent | High (many users skip assess-spec) | Low | Graceful degradation: baseline computation works without it. |
| Adds latency to pre-coding phase | Low | Low | Computation is string matching + 1-level import scan — under 10 seconds. |

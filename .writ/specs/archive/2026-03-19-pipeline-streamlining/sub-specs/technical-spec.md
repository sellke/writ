# Technical Spec: Pipeline Streamlining

## Architecture

### Before

```
implement-spec → verify-spec → verify-spec --pre-deploy → release
                                     ↑                        ↑
                               (test suite)            (no own gate)
                               (coverage)
                               (build check)
                               (changelog gen)
```

Release depends on external validation. verify-spec is both diagnostic and gate. Tests run redundantly in ship and verify-spec.

### After

```
implement-spec → ship → release
                  ↑        ↑
            (opt-in     (inline gate:
             tests)      conditional tests +
                         build check +
                         spec validation)

verify-spec ← standalone diagnostic (no pipeline position)
```

Release is self-sufficient. Ship is fast by default. Verify-spec is independent.

## Conditional Test Execution in /release

### Detection Logic

```bash
LAST_MERGED_SHA=$(gh pr list --state merged --limit 1 --json mergeCommit --jq '.[0].mergeCommit.oid' 2>/dev/null)
HEAD_SHA=$(git rev-parse HEAD)

if [ "$LAST_MERGED_SHA" = "$HEAD_SHA" ]; then
  echo "Tests skipped — HEAD matches last merged PR"
  SKIP_TESTS=true
else
  echo "Running tests — commits exist since last merged PR"
  SKIP_TESTS=false
fi
```

### Fallback Behavior

| Condition | Behavior |
|---|---|
| `gh` available, HEAD matches last merged PR | Skip test suite, run build checks only |
| `gh` available, HEAD differs from last merged PR | Run full test suite + build checks |
| `gh` unavailable or unauthenticated | Run full test suite + build checks (safe default) |
| `--skip-gate` flag set | Skip entire gate (tests + build + spec validation) |

### Build Verification (Always Runs)

Build checks run regardless of test skip status because they're fast and catch different issues:

```bash
# Detect and run (same detection chain as /ship Step 1)
npx tsc --noEmit 2>/dev/null        # typecheck (if tsconfig exists)
npx eslint . 2>/dev/null             # lint (if eslint config exists)
npx prettier --check . 2>/dev/null   # format (if prettier config exists)
```

Only run checks where config files exist. Don't fail on missing tooling.

## Ship's Opt-In Test Architecture

### Default Pipeline (no --test)

```
DETECT CONVENTIONS → MERGE DEFAULT BRANCH → COMMIT INTELLIGENCE → PR CREATION
```

### With --test Flag

```
DETECT CONVENTIONS → MERGE DEFAULT BRANCH → RUN TESTS → COMMIT INTELLIGENCE → PR CREATION
                                                ↓
                                           (on fail: fix/draft/abort)
```

The test step is structurally identical to the current Step 3. The only change is it doesn't execute unless `--test` is passed.

## Inline Spec Health Check in /ship

Runs silently during PR creation (Step 5). Subset of verify-spec checks:

| Check | What | Auto-fixable? |
|---|---|---|
| 1a | Orphan story files (files without README entries) | Yes — add to README |
| 1b | Phantom stories (README entries without files) | No — flag in PR body |
| 2a | README ↔ story file status sync | Yes — update README |
| 2b | Task count accuracy | Yes — update README |
| 3d | Premature status (tasks done but status not updated) | Yes — update status |

**Behavior:**
- Auto-fix what can be fixed (silently, no prompting)
- If unfixable issues found: add "Spec Health" subsection to PR body
- If everything clean: omit the subsection entirely (no noise)

## Verify-Spec Check Matrix (After Streamlining)

| # | Check | Default Mode | --check Mode |
|---|---|---|---|
| 1 | Story file integrity | Run + auto-fix | Run + report only |
| 2 | Status consistency | Run + auto-fix | Run + report only |
| 3 | Completion integrity | Run + auto-fix | Run + report only |
| 4 | Dependency validation | Run + report | Run + report only |
| 5 | Deliverables checklist | Run + auto-fix | Run + report only |
| 8 | Contract vs implementation | Run + report | Run + report only |

Checks 4 and 8 are report-only in both modes (can't auto-fix dependency violations or scope drift — these need human judgment).

## Error Mapping

### Release Gate Failures

| Operation | What Fails | Handling | User Sees |
|---|---|---|---|
| `gh pr list` for merge detection | gh not installed / not authenticated | Fall back to running tests | "gh CLI unavailable — running full test suite" |
| Test suite execution | Tests fail | Block release with clear report | "Release blocked: N test failures. Fix and retry, or --skip-gate" |
| Build verification | Typecheck/lint/format fails | Block release with clear report | "Release blocked: typecheck errors in N files. Fix and retry" |
| Spec metadata validation | Unfixable issues found | Warn but don't block | "Warning: N spec issues found (see details). Proceeding with release." |

### Ship Spec Check Failures

| Operation | What Fails | Handling | User Sees |
|---|---|---|---|
| Spec folder detection | No .writ/specs/ found | Skip silently | Nothing — no spec, no check |
| Story file parsing | Malformed story file | Skip that file, continue | Nothing unless all files malformed |
| README sync | README out of date | Auto-fix silently | Nothing — fixed before PR creation |
| Unfixable issues | Phantom stories, false completions | Add to PR body | "Spec Health" subsection in PR |

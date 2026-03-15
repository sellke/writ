# Phase 2a: Shipping & Review — Validation Checklist

> Created: 2026-03-15
> Status: Structural validation complete, dogfood scenarios pending

## Validation Scenarios

### Scenario 1: `/ship` — End-to-End Shipping

**Command:** `/ship` on a real Writ feature branch

**Measurement criteria:**
- [ ] Convention detection correctly identifies: default branch, test runner, merge strategy, PR tool
- [ ] User can verify and override detected conventions before workflow proceeds
- [ ] Merge step fetches origin and merges cleanly (or pauses on conflict with clear guidance)
- [ ] Test execution auto-detects and runs the correct test command
- [ ] On test pass: workflow continues silently (momentum over ceremony)
- [ ] On test fail: three-option menu presented (fix/ship-anyway/abort)
- [ ] Commit splitting correctly separates infrastructure/logic/test changes when beneficial
- [ ] Commit splitting skips for single-file or <50 line changes
- [ ] PR body includes all sections: Summary, Changes, Spec Reference, Test Results, Drift Report, Review Notes
- [ ] Auto-labels correctly applied based on file types changed
- [ ] Draft/ready status correctly determined from test results and drift status
- [ ] Completion output shows branch, commits, PR URL, and labels

**Pass criteria:** Full pipeline runs on a real branch with zero manual PR body writing.

### Scenario 2: `/review` — Standalone Code Review

**Command:** `/review` on a real diff before shipping

**Measurement criteria:**
- [ ] Review scope correctly detected and printed
- [ ] Error & rescue map produced for methods that can fail
- [ ] Critical gap detection flags `RESCUED=No + TEST=No` patterns
- [ ] Shadow path tracing covers happy, nil, empty, and upstream error paths
- [ ] Interaction edge cases evaluated for user-facing features (or correctly skipped for backend-only)
- [ ] Failure modes registry aggregates all findings with severity ratings
- [ ] Architecture diagram produced for non-trivial flows
- [ ] Recommendation section leads with the most important finding (not a neutral list)
- [ ] At least one failure mode found that the pipeline review would have missed

**Pass criteria:** `/review` catches ≥1 failure mode per review that pipeline review missed.

### Scenario 3: `/retro` — Git-Based Retrospective

**Command:** `/retro` on the Writ repo after Phase 2a implementation

**Measurement criteria:**
- [ ] Auto-detection correctly identifies timezone, default branch, and period
- [ ] Git metrics collected: commits, LOC, files touched, test ratio
- [ ] Session detection identifies distinct work sessions with gap-based clustering
- [ ] Streak tracking shows consecutive active days
- [ ] Writ context collected: specs completed, stories completed, drift incidents
- [ ] JSON snapshot saved to `.writ/retros/YYYY-MM-DD.json`
- [ ] Ship of the Week highlights the most impactful change
- [ ] Patterns section provides opinionated observations (not just raw metrics)
- [ ] Tweetable summary distills the period into one compelling sentence
- [ ] If previous snapshot exists: Δ vs Last column populated

**Pass criteria:** Trend comparison against previous period's snapshot produced.

### Scenario 4: Error Mapping — In `/create-spec`

**Command:** `/create-spec` for a feature with data flows

**Measurement criteria:**
- [ ] Technical sub-spec includes Error & Rescue Map section
- [ ] `[UNPLANNED]` markers appear for operations without planned handling
- [ ] Shadow Paths section traces critical data flows
- [ ] Interaction Edge Cases section covers standard scenarios plus feature-specific cases
- [ ] Table formats match `/review` output format (shared format verified)
- [ ] Scope detection correctly identifies when error mapping is required vs optional

**Pass criteria:** Error mapping surfaces rescue gaps in technical sub-specs before implementation.

### Scenario 5: Integration — `/review` → `/ship`

**Command:** `/review` followed by `/ship` on the same branch

**Measurement criteria:**
- [ ] `/review` saves report to `.writ/state/review-[branch-name].md`
- [ ] `/ship` detects the review report file
- [ ] Failure modes registry from `/review` appears in PR's "Review Notes" section
- [ ] Critical/High findings highlighted in PR description
- [ ] Cross-command format consistency: error mapping tables in `/create-spec`, `/review`, and specs use identical structures

**Pass criteria:** Review findings propagate to PR Review Notes; format consistency verified across commands.

### Scenario 6: Structural Validation

**Automated checks (no real command execution needed):**

- [x] `commands/ship.md` exists with all 5 pipeline steps
- [x] `commands/review.md` exists with all 5 review techniques
- [x] `commands/retro.md` exists with analysis, output, persistence, and trends
- [x] `commands/create-spec.md` updated with error mapping in Step 2.8
- [x] `commands/implement-story.md` updated with `/ship` suggestion
- [x] All new commands follow Design Principle 6 (opinionated by default)
- [x] Error mapping table formats consistent across `/create-spec` and `/review`
- [x] All story files updated with completion status and "What Was Built" records
- [x] README.md reflects current progress

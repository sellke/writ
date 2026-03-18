# Validation Report: Remaining Command Refinement

> Validated: 2026-03-18
> Spec: `.writ/specs/2026-03-18-remaining-command-refinement/spec.md`

## Task 1: Line Count Audit

| File | Before | After | Target | Range (±10%) | Status |
|------|--------|-------|--------|--------------|--------|
| commands/new-command.md | 438 | 184 | ~200 | 180–220 | ✅ Pass |
| commands/refactor.md | 416 | 198 | ~220 | 198–242 | ✅ Pass |
| .cursor/commands/review.md | 292 | 198 | ~200 | 180–220 | ✅ Pass |
| .cursor/commands/retro.md | 455 | 198 | ~220 | 198–242 | ✅ Pass |
| **Total** | **1,601** | **778** | **~840** | **756–924** | **✅ Pass** |

Reduction: 51.3% (target was ~47%). All files within their individual target ranges.

---

## Task 2: Section-by-Section Litmus Test

For each line: (1) teaches non-obvious? (2) sets quality bar? (3) prevents mistake? Must pass at least one.

### new-command.md — ✅ Pass

| Section | Lines | Litmus | Notes |
|---------|-------|--------|-------|
| Overview + when to use | 1–8 | ✅ | Sets context, prevents wrong usage |
| Invocation table | 9–15 | ✅ | Structured reference |
| Phase 1 mission statement | 18–22 | ✅ | Crown jewel — contract-first mandate |
| Context scan | 24–29 | ✅ | Guides behavior, prevents skipping patterns |
| Plan Mode switch + ADR-001 | 31–35 | ✅ | Non-obvious interaction model |
| Discovery conversation rules | 37–53 | ✅ | Quality bars — 95% confidence, one question at a time |
| Critical analysis responsibility | 55–68 | ✅ | Crown jewel — prevents yes-machine behavior |
| Topic areas | 70–77 | ✅ | Guides discovery, prevents shallow exploration |
| Contract proposal | 83–89 | ✅ | Principle-based, not template |
| AskQuestion contract decision | 91–119 | ✅ | Decision gate with all 5 options |
| Phase 2 creation + categories | 121–163 | ✅ | Principles about what good commands contain |
| Core rules | 167–174 | ✅ | All non-obvious constraints |
| Integration table | 177–184 | ✅ | Cross-references intact |

**Litmus failures found: 0**

### refactor.md — ✅ Pass

| Section | Lines | Litmus | Notes |
|---------|-------|--------|-------|
| Overview + core discipline + scope | 1–9 | ✅ | Non-obvious constraints: never batch, scope boundary |
| Mode table | 11–24 | ✅ | All 8 modes + unifying principle |
| Scope determination + hotspot | 28–44 | ✅ | AskQuestion gate, hotspot analysis concept |
| Baseline verification | 46–52 | ✅ | Crown jewel — hard stop on broken baseline |
| Deep analysis per mode | 54–71 | ✅ | Mode-specific detection targets as principles |
| Refactoring plan + approval | 73–109 | ✅ | Risk-ordered table, all AskQuestion options, ADR |
| Phase 3 execution | 111–137 | ✅ | Golden rule, commit discipline, failure handling |
| Phase 4 verification | 139–152 | ✅ | Quality bar: every metric equal or improved |
| Safety Guarantees | 155–165 | ✅ | All 7 invariants — genuinely non-obvious |
| Refactoring Discipline | 167–186 | ✅ | 7 non-obvious principles preventing real failures |
| Integration table | 189–198 | ✅ | Cross-references intact |

**Litmus failures found: 0**

Note: The "Refactoring Discipline" section (7 principles) is new content not in the original. Every line passes the litmus test — each prevents a specific mistake the AI would likely make (scope creep, refactoring untested code, refactoring doomed code, breaking backward compatibility, over-removing "dead" code, mixing concerns in commits, breaking public interfaces).

### review.md — ✅ Pass

| Section | Lines | Litmus | Notes |
|---------|-------|--------|-------|
| Overview | 1–9 | ✅ | Purpose, depth distinction, /ship integration |
| Invocation table | 11–18 | ✅ | All 4 invocation patterns |
| Step 1: Scope | 20–33 | ✅ | Compressed without losing --spec comparison |
| Step 2: Scan | 35–44 | ✅ | 4 categories as numbered list |
| Technique 1: Error & Rescue | 46–73 | ✅ | Table, severity patterns, I/O-first guidance |
| Technique 2: Shadow Paths | 75–95 | ✅ | 4-path table, trust boundaries, 5-flow limit |
| Technique 3: Interaction Edge | 97–117 | ✅ | Standard scenarios, feature-specific, backend skip |
| Technique 4: Failure Registry | 119–141 | ✅ | Aggregated table, severity classification |
| Technique 5: Architecture | 143–158 | ✅ | ASCII example, include/skip criteria |
| Step 4: Report | 160–192 | ✅ | Compressed template, "Recommendation is the soul" |
| Step 5: /ship integration | 194–198 | ✅ | Output-based coupling |

**Litmus failures found: 0**

All 5 techniques preserved intact with tables, examples, severity classifications, and all 3 "I recommend" judgment calls.

### retro.md — ✅ Pass

| Section | Lines | Litmus | Notes |
|---------|-------|--------|-------|
| Overview + design philosophy | 1–14 | ✅ | 4 non-obvious philosophy bullets |
| Invocation table | 16–24 | ✅ | All 5 invocation patterns |
| Step 1: Auto-detect | 26–40 | ✅ | Settings table, smart period suggestion |
| Step 2: Git metrics | 42–57 | ✅ | What to collect + test ratio benchmarks |
| Step 3: Sessions | 59–81 | ✅ | 2-hour gap, all 5 refinements, timeline example |
| Step 4: Streaks | 83–89 | ✅ | ≥5 days threshold, interrupt-driven caveat |
| Step 5: Writ context | 91–102 | ✅ | What to collect + graceful skip |
| Step 6: Spec scoping | 104–108 | ✅ | Mechanism compressed to essentials |
| Step 7: Output structure | 110–148 | ✅ | Report structure, Ship heuristic, pattern table |
| Steps 8–9: Persistence | 150–175 | ✅ | Field lists as principles, rolling averages |
| Step 10: Compare mode | 177–188 | ✅ | Previous period lookup, opinionated analysis |
| Integration table | 190–198 | ✅ | Cross-references intact |

**Litmus failures found: 0**

Session detection heuristics, pattern type table, Ship of the Week selection, and tweetable forcing function all preserved.

---

## Task 3: Cross-Reference Check

| Reference | File | Expected | Found | Status |
|-----------|------|----------|-------|--------|
| `.writ/state/review-[branch].md` | review.md | /ship integration | Line 196 | ✅ |
| `/create-spec` error mapping | review.md | Shared table format | Line 73 | ✅ |
| `/ship` | review.md | Output-based coupling | Lines 9, 196 | ✅ |
| `/create-adr` | refactor.md | ADR for major refactors | Lines 107, 165 | ✅ |
| `/implement-story` | refactor.md | Scope boundary redirect | Lines 9, 193 | ✅ |
| `/security-audit` | refactor.md | Scope boundary redirect | Lines 9, 196 | ✅ |
| `.writ/retros/YYYY-MM-DD.json` | retro.md | Snapshot persistence | Line 152 | ✅ |
| `.writ/retros/trends.json` | retro.md | Rolling trends | Line 167 | ✅ |
| `.writ/specs/` | retro.md | Spec context for --spec | Lines 97, 108 | ✅ |
| `.writ/refresh-log.md` | retro.md | Command refresh data | Line 100 | ✅ |
| `commands/` | new-command.md | Pattern reference | Lines 27, 159 | ✅ |
| `/create-spec` | new-command.md | Shared interaction model | Line 181 | ✅ |
| `/create-adr` | new-command.md | Design decision records | Line 183 | ✅ |

**All cross-references resolvable and intact.** No broken paths.

---

## Task 4: Capability Comparison

### new-command.md — Zero Capability Loss ✅

| Capability | Pre-Refinement | Post-Refinement | Status |
|-----------|----------------|-----------------|--------|
| Contract-first workflow (Phase 1) | ✅ Full | ✅ Full | Preserved |
| Context scan of existing commands | ✅ | ✅ | Preserved |
| Plan Mode switch + ADR-001 | ✅ | ✅ | Preserved |
| Discovery conversation rules | ✅ | ✅ | Preserved |
| Critical analysis responsibility (5 items) | ✅ | ✅ | Preserved verbatim |
| Pushback phrasing (4 examples) | ✅ | ✅ | Preserved verbatim |
| Topic area exploration | ✅ 9 items | ✅ 6 items | Compressed, no loss |
| Echo check / contract proposal | ✅ Template | ✅ Principle | Same capability |
| AskQuestion contract decision (5 options) | ✅ | ✅ | Preserved with handling |
| Phase 2 file creation | ✅ Template | ✅ Principles + category table | Same capability |
| Command categories (5 types) | ✅ Verbose | ✅ Table | Same capability |
| Validation / integration check | ✅ Verbose | ✅ Compressed | Same capability |
| Core rules | ❌ Generic | ✅ 5 specific rules | Improved |
| Integration table | ❌ Generic | ✅ 4-row table | Improved |

### refactor.md — Zero Capability Loss ✅

| Capability | Pre-Refinement | Post-Refinement | Status |
|-----------|----------------|-----------------|--------|
| All 8 modes | ✅ | ✅ | Preserved |
| AskQuestion scope selection | ✅ | ✅ | Preserved |
| Baseline verification (hard stop) | ✅ | ✅ | Preserved |
| Per-mode detection targets | ✅ Bash scripts | ✅ Principles table | Same capability |
| Analysis report format | ✅ Full template | ✅ Principle + quality bar | Same capability |
| Risk-ordered plan table | ✅ | ✅ | Preserved |
| AskQuestion plan approval (5 options) | ✅ | ✅ | Preserved |
| ADR creation for major changes | ✅ | ✅ | Preserved |
| Phase 3 execution cycle | ✅ 4 steps | ✅ 4 steps | Preserved |
| Commit per change discipline | ✅ | ✅ | Preserved |
| Import update requirement | ✅ Bash | ✅ Principle | Same capability |
| Rollback on failure | ✅ | ✅ | Preserved |
| Phase 4 verification report | ✅ Full template | ✅ Quality bar | Same capability |
| All 7 safety guarantees | ✅ | ✅ | Preserved verbatim |
| Mode-specific workflows (5 modes) | ✅ Repeated | ✅ Unified principle | Same capability |
| Hotspot analysis | ✅ Implicit | ✅ Explicit | Improved |
| Dry-run termination | ✅ | ✅ | Preserved |
| Refactoring discipline principles | ❌ Not present | ✅ 7 principles | Added value |

### review.md — Zero Capability Loss ✅

| Capability | Pre-Refinement | Post-Refinement | Status |
|-----------|----------------|-----------------|--------|
| All 5 techniques with tables | ✅ | ✅ | Preserved |
| Severity classification table | ✅ | ✅ | Preserved |
| "I recommend" — external I/O first | ✅ | ✅ | Preserved |
| "I recommend" — 5 flows max | ✅ | ✅ | Preserved |
| "I recommend" — Critical/High before ship | ✅ | ✅ | Preserved |
| Invocation table (4 patterns) | ✅ | ✅ | Preserved |
| --spec plan-vs-actual comparison | ✅ | ✅ | Preserved |
| Table format note (shared with /create-spec) | ✅ | ✅ | Preserved |
| Scope identification | ✅ 3 code blocks | ✅ Compressed | Same capability |
| Diff scanning (4 categories) | ✅ | ✅ | Preserved |
| Feature-specific edge cases | ✅ | ✅ | Preserved |
| Skip for backend-only | ✅ | ✅ | Preserved |
| Architecture diagram + include/skip | ✅ | ✅ | Preserved |
| Report generation | ✅ Full template | ✅ Compressed template | Same capability |
| "Recommendation is the soul" | ✅ | ✅ | Preserved |
| /ship integration via .writ/state/ | ✅ | ✅ | Preserved |

### retro.md — Zero Capability Loss ✅

| Capability | Pre-Refinement | Post-Refinement | Status |
|-----------|----------------|-----------------|--------|
| All 5 invocation modes | ✅ | ✅ | Preserved |
| Auto-detect (tz, branch, period) | ✅ Bash | ✅ Table | Same capability |
| Smart period suggestion | ✅ | ✅ | Preserved |
| Git metrics collection | ✅ Bash | ✅ Principles | Same capability |
| Test ratio benchmarks (3 tiers) | ✅ | ✅ | Preserved |
| Session detection (2-hour gap) | ✅ Pseudocode | ✅ Principles | Same capability |
| All 5 session refinements | ✅ | ✅ | Preserved |
| Session statistics | ✅ Table | ✅ Inline | Same capability |
| Time distribution buckets | ✅ | ✅ | Preserved |
| Streak tracking + ≥5 threshold | ✅ | ✅ | Preserved |
| Interrupt-driven work caveat | ✅ | ✅ | Preserved |
| Writ context (4 artifacts) | ✅ Step-by-step | ✅ Bullet list | Same capability |
| Graceful skip for non-Writ | ✅ | ✅ | Preserved |
| Spec scoping (--spec) | ✅ | ✅ | Preserved |
| Ship of the Week (5-level heuristic) | ✅ | ✅ | Preserved |
| "Effort not volume" quality bar | ✅ | ✅ | Preserved |
| Pattern type table (6 patterns) | ✅ | ✅ | Preserved |
| 2-3 patterns recommendation | ✅ | ✅ | Preserved |
| Tweetable forcing function | ✅ | ✅ | Preserved |
| Snapshot persistence (JSON fields) | ✅ Full schema | ✅ Field list | Same capability |
| Trends rolling averages | ✅ Full schema | ✅ Field list | Same capability |
| Compare mode | ✅ Full template | ✅ Principles | Same capability |

---

## Task 5: Voice & Density Comparison

**Benchmarks:** assess-spec.md (203 lines, A grade), edit-spec.md (118 lines, A grade)

| Dimension | Benchmark Pattern | new-command | refactor | review | retro |
|-----------|------------------|-------------|----------|--------|-------|
| Sentence length | Short (2-4 lines) | ✅ | ✅ | ✅ | ✅ |
| Table vs prose | Tables for structured data | ✅ | ✅ | ✅ | ✅ |
| Principle vs prescription | Principles over steps | ✅ | ✅ | ✅ | ✅ |
| Section structure | Overview → Invocation → Process → Integration | ✅ | ✅ | ✅ | ✅ |
| "You should" filler | None | ✅ None | ✅ None | ✅ None | ✅ None |
| Bash scripts | None | ✅ None | ✅ None | ✅ None | ✅ None |
| JSON/markdown templates | None | ✅ None | ✅ None | ✅ Minimal¹ | ✅ None |
| Information density | High — no line wasted | ✅ | ✅ | ✅ | ✅ |

¹ review.md retains a compressed report skeleton (lines 164-190) showing section order. This is appropriate — it defines the report structure that /ship integration depends on.

**Tone assessment:** All 4 files are direct, principle-driven, and read at the same density as the benchmark files. No file feels bloated or sparse. The "I recommend" voice in review.md and retro.md adds appropriate judgment without becoming chatty.

---

## Overall Assessment

| File | Line Count | Litmus | Cross-Refs | Capability | Voice | Grade |
|------|-----------|--------|------------|------------|-------|-------|
| new-command.md | ✅ 184 | ✅ 0 failures | ✅ All intact | ✅ Zero loss | ✅ Match | **A** |
| refactor.md | ✅ 198 | ✅ 0 failures | ✅ All intact | ✅ Zero loss + bonus | ✅ Match | **A** |
| review.md | ✅ 198 | ✅ 0 failures | ✅ All intact | ✅ Zero loss | ✅ Match | **A** |
| retro.md | ✅ 198 | ✅ 0 failures | ✅ All intact | ✅ Zero loss | ✅ Match | **A** |

**Overall: ✅ PASS — All 4 files confirmed at A grade.**

Total reduction: 1,601 → 778 lines (51.3%). Zero functional capability lost. Zero litmus test failures. All cross-references intact. Voice and density consistent with benchmark A-grade commands.

# Validation Report: Core A-Grade Refinement

> Validated: 2026-03-18
> Status: ✅ All checks passed

## 1. Line Count Audit

| File | Original | Refined | Target | Range (±15%) | Status |
|------|----------|---------|--------|--------------|--------|
| commands/plan-product.md | 623 | 272 | ~280 | 238–322 | ✅ |
| commands/create-spec.md | 805 | 458 | ~400 | 340–460 | ✅ |
| commands/implement-spec.md | 294 | 244 | ~250 | 213–288 | ✅ |
| commands/implement-story.md | 469 | 285 | ~320 | 272–368 | ✅ |
| agents/review-agent.md | 454 | 321 | ~280 | 238–322 | ✅ |
| agents/coding-agent.md | 269 | 204 | ~200 | 170–230 | ✅ |
| agents/documentation-agent.md | 299 | 182 | ~180 | 153–207 | ✅ |
| agents/architecture-check-agent.md | 206 | 190 | ~180 | 153–207 | ✅ |
| agents/testing-agent.md | 256 | 228 | ~220 | 187–253 | ✅ |
| **Total** | **3,675** | **2,384** | **~2,310** | **2,079–2,541** | ✅ |

**Reduction: 35%** (target ~37%). All files within individual range. Total within ±10%.

## 2. Litmus Test Results

Every section in every file was verified against the three-question litmus test:
1. Teaches something non-obvious?
2. Sets a quality bar the AI wouldn't reach alone?
3. Prevents a specific mistake?

### Key Sections Verified

| File | Section | Verdict | Rationale |
|------|---------|---------|-----------|
| plan-product.md | Phase 1 Discovery | ✅ Pass | Posture selection, premise challenge, dream state mapping — all non-obvious and unique to Writ |
| plan-product.md | Phase 2 Principles | ✅ Pass | Quality bars ("someone reading only this file understands the entire product direction") set standards AI wouldn't reach alone |
| plan-product.md | Contract Format | ✅ Pass | Failure surfaces concept, opinionated recommendations — prevents generic neutral menus |
| create-spec.md | Phase 1 Discovery | ✅ Pass | Experience-first ordering, pushback examples — crown jewel preserved intact |
| create-spec.md | Error Mapping | ✅ Pass | [UNPLANNED] marker concept, "what user sees not what system does" — prevents spec gaps |
| create-spec.md | Example 2 | ✅ Pass | Demonstrates discovery conversation feel — teaches the AI the interaction quality bar |
| implement-story.md | Gate 3.5 Drift | ✅ Pass | Three-tier model as principles, spec-lite mutation visibility — prevents silent corruption |
| implement-story.md | Gate 2.5 Surface | ✅ Pass | Change surface classification — non-obvious heuristic for review depth allocation |
| implement-spec.md | Pre-flight | ✅ Pass | Threshold principles without reimplementing assess-spec — prevents maintenance coupling |
| review-agent.md | Review Categories | ✅ Pass | "Security is never Minor", "no vacuous assertions" — prevents under-flagging |
| review-agent.md | Drift Analysis | ✅ Pass | Severity classification table, "when ambiguous → Medium" — prevents under-classification |
| coding-agent.md | Self-Verification | ✅ Pass | "Fix failures yourself with warm context" — prevents silently handing off broken code |
| documentation-agent.md | Default-First | ✅ Pass | No-framework path as primary — prevents wasting tokens on rare framework detection |
| testing-agent.md | Coverage Thresholds | ✅ Pass | "Don't chase 100%", "branch coverage matters" — non-obvious quality bars |

### Sections Cut (confirmed as appropriate)

| Cut | Why it failed the litmus test |
|-----|-------------------------------|
| SwitchMode code blocks | Cursor doesn't support programmatic mode switching |
| plan-product Key Improvements | Changelog comparing to previous version — not execution guidance |
| plan-product Tool Integration | AI already knows its tools |
| plan-product Best Practices | Repeated the command body |
| create-spec Key Improvements | Changelog — not execution guidance |
| create-spec User Stories Best Practices | Repeated the template content |
| implement-story Deprecation Note | Historical note — not execution guidance |
| All markdown file templates | AI can generate documents from principles — templates are token-expensive and constraining |
| Test runner detection recipes | AI already knows how to detect vitest vs jest vs pytest |
| 5 framework-specific doc sections | One conditional principle replaces 5 detailed sections |
| Review checklist (31 items) | 5 categorized principles cover the same ground with less noise |
| Gate 3.5 procedural steps | Principles replace step-by-step procedures while preserving the three-tier safety model |

## 3. Cross-Reference Audit

| Source | Reference | Target | Status |
|--------|-----------|--------|--------|
| implement-story.md Gate 0 | `agents/architecture-check-agent.md` | ✅ Exists |
| implement-story.md Gate 1 | `agents/coding-agent.md` | ✅ Exists |
| implement-story.md Gate 3 | `agents/review-agent.md` | ✅ Exists |
| implement-story.md Gate 4 | `agents/testing-agent.md` | ✅ Exists |
| implement-story.md Gate 5 | `agents/documentation-agent.md` | ✅ Exists |
| implement-story.md Gate 3.5 | `.writ/docs/drift-report-format.md` | ✅ Exists |
| implement-spec.md | `/implement-story` references | ✅ Command intact |
| create-spec.md Step 2.6 | `agents/user-story-generator.md` | ✅ Exists (unchanged) |
| review-agent.md | Drift severity tiers (Small/Medium/Large) | ✅ Consistent with Gate 3.5 |
| implement-story.md | Gate numbers (0, 1, 2, 2.5, 3, 3.5, 4, 4.5, 5) | ✅ All present |
| implement-spec.md | Orchestration contract table | ✅ Preserved (exception to "remove Integration" rule) |

**No broken cross-references found.**

## 4. Drift-Report-Format Consistency

The simplified Gate 3.5 references `.writ/docs/drift-report-format.md` as the canonical format. Verified:

- ✅ Three severity tiers match (Small/Medium/Large)
- ✅ Pipeline responses match (PASS/PASS+warning/PAUSE)
- ✅ DEV-ID continuation principle stated
- ✅ Append-only logging principle stated
- ✅ One example drift entry included (brief, defers to format doc for full spec)

**Pre-existing note:** `drift-report-format.md` line 10 states "spec.md and spec-lite.md are never changed by the pipeline" — but Gate 3.5 auto-amends spec-lite.md for Small drift. This inconsistency pre-dates this refinement and exists in the original files. Recommend resolving in a future spec by updating drift-report-format.md to note the spec-lite exception.

## 5. Context Cost Estimate

Approximate token weight per agent when fully expanded with typical story content:

| Agent | Instruction Lines | Est. Expanded Tokens | Reduction |
|-------|-------------------|---------------------|-----------|
| review-agent.md | 321 | ~2,500 | -29% |
| coding-agent.md | 204 | ~1,800 | -24% |
| documentation-agent.md | 182 | ~1,500 | -39% |
| architecture-check-agent.md | 190 | ~1,600 | -8% |
| testing-agent.md | 228 | ~1,900 | -11% |
| **Pipeline total (one story)** | — | **~9,300** | **~25%** |

Context savings are most significant for review-agent (checklist → principles) and documentation-agent (framework sections → conditional). Architecture-check and testing agents were already close to A-grade, so savings are modest.

## 6. Summary

| Check | Result |
|-------|--------|
| Line count within targets | ✅ All 10 files in range, total 2,384 (target ~2,310 ±10%) |
| Litmus test on all sections | ✅ Every remaining section passes |
| Cross-reference integrity | ✅ No broken references |
| Drift-report-format consistency | ✅ Consistent (one pre-existing note flagged) |
| Functional capability preserved | ✅ Same pipeline, same quality gates, same artifacts |
| Zero SwitchMode references | ✅ Removed from all in-scope files |

**Verdict: All 10 files confirmed A-grade.**

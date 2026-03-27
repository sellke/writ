# ADR-004: Context-First Phasing

> **Status:** Accepted
> **Date:** 2026-03-27
> **Deciders:** Product owner
> **Part of:** `/plan-product` discovery for Context Engine

## Context

Writ's evolution to incorporate intelligent context routing and autonomous execution could be delivered in multiple ways:

1. **Big bang** — ship context engine and autonomous execution together as "Writ v2"
2. **Context first** — ship context engine in Phase 3a, autonomous execution in Phase 3b
3. **Autonomous first** — ship Ralph loop orchestration in Phase 3a, context engine in Phase 3b or alongside

The question: Which capability should ship first, and why?

## Decision Drivers

1. **Autonomous execution quality depends on context quality** — agents looping autonomously without the right context will produce worse outcomes faster
2. **Context engine has immediate value** — improves code quality for human-supervised runs today
3. **Risk profile** — context engine is structural changes to artifacts; autonomous execution is architectural changes to orchestration
4. **Validation opportunity** — context engine usage reveals which context matters most, informing autonomous mode design
5. **User impact** — context improvements are invisible upgrades; autonomous mode changes workflow

## Considered Options

### Option 1: Big Bang (Both Together)

**Approach:** Design and ship context engine + autonomous execution as one coordinated release. Agents get better context *and* can run autonomously.

**Pros:**
- Users get the full vision at once
- No interim state where one capability exists without the other
- Marketing moment — "Writ v2" with two major features

**Cons:**
- High risk — two complex capabilities shipping simultaneously
- Long development cycle (5-7 weeks) before any value ships
- If either capability has issues, both are blocked
- No validation opportunity — can't learn from context engine usage before building autonomous mode
- Testing complexity — must validate both capabilities and their interaction

**Effort:** XL (5-7 weeks)

### Option 2: Context First, Autonomous Later (Phased)

**Approach:** Ship context engine in Phase 3a (2-3 weeks). Validate it on real specs. Use learnings to design autonomous execution for Phase 3b.

**Pros:**
- Lower risk — one capability at a time, incremental validation
- Context engine ships value faster (2-3 weeks vs 5-7 weeks)
- Autonomous mode benefits from real-world context engine usage data
- If context engine reveals gaps, Phase 3b design adapts
- Testing is simpler — validate one thing at a time
- Users get immediate code quality improvements without workflow changes

**Cons:**
- Two separate rollouts (though both are backward compatible)
- Marketing is less dramatic — no single "v2" moment
- Users experience the vision in stages, not all at once

**Effort:** M + M (2-3 weeks for Phase 3a, 3-4 weeks for Phase 3b)

### Option 3: Autonomous First, Context Later

**Approach:** Ship Ralph loop orchestration in Phase 3a. Add context engine improvements in Phase 3b.

**Pros:**
- Users get "walk away, come back to a PR" workflow quickly
- Autonomous execution is the more visible feature (bigger perceived impact)

**Cons:**
- **Critical flaw: Autonomous agents looping with poor context produce poor code faster.** If agents miss error cases or business rules today due to context delivery gaps, letting them loop autonomously compounds the problem.
- Context engine has higher ROI per unit effort — improves quality for every run, autonomous or not
- Autonomous mode design would be uninformed by real-world context delivery patterns
- Higher risk of user frustration — "it runs autonomously but the output is wrong" is worse than "it requires supervision but the output is good"

**Effort:** M + M (3-4 weeks for Phase 3a, 2-3 weeks for Phase 3b)

**Verdict:** Rejected — puts autonomy before quality

## Decision

**Chosen: Option 2 — Context First (Phase 3a), Autonomous Later (Phase 3b)**

### Rationale

**1. Autonomous execution quality depends on context quality.**

Ralph loop orchestration means agents iterate until success criteria are met. If agents are missing error maps, business rules, or cross-story context, they'll iterate *toward the wrong thing*. The loop will converge on code that passes tests but violates business rules or misses error cases.

Context engine ensures agents have the right inputs. Autonomous mode ensures they use those inputs without human supervision. You can't skip the first and expect the second to work well.

**2. Context engine ships value immediately.**

Every spec run after Phase 3a ships benefits:
- Coding agents handle error cases described in specs
- Review agents catch business rule violations
- Story 3 builds correctly on Stories 1-2

These improvements happen whether the run is human-supervised or autonomous. Context engine is a force multiplier for all execution modes.

**3. Real-world usage informs Phase 3b design.**

Phase 3a usage will reveal:
- Which context hints are most valuable (error maps? shadow paths? business rules?)
- Where context delivery still fails (agent prompt templates? orchestrator logic?)
- What agents do with cross-story continuity ("What Was Built" records)

These learnings directly inform autonomous mode design. For example, if "What Was Built" records prove critical, autonomous mode needs to checkpoint them after every story completion. If error maps are underutilized, autonomous mode shouldn't over-index on them.

**4. Lower risk, faster value.**

Phase 3a ships in 2-3 weeks. Phase 3b ships 3-4 weeks after that. Total time to full vision: 5-7 weeks, same as big bang — but value ships at the 2-3 week mark instead of waiting for 5-7.

If Phase 3a reveals context delivery gaps, Phase 3b design adapts. If big bang ships and both capabilities have issues, rollback is complex.

**5. Backward compatibility makes phasing seamless.**

Both phases are backward compatible. Users on Phase 3a get better context for supervised runs. When Phase 3b ships, they *opt into* autonomous mode. No forced migration, no breaking changes.

### Implementation Path

**Phase 3a: Context Engine (2-3 months after Phase 1 & 2 dogfooding)**

Stories:
1. Per-story context hints (story format + user-story-generator update)
2. "What Was Built" records (implement-story + review-agent integration)
3. Agent-specific spec views (spec-lite restructuring + orchestrator routing)
4. UAT plan generation (new command or ship integration)
5. Context routing improvements (all agent prompt templates)

Success criteria:
- Review agent catch rate for business rule violations improves >30%
- Coding agents handle error cases from specs without explicit prompting
- Story 3 implementations correctly build on Stories 1-2
- No prompt length increase

**Phase 3b: Autonomous Execution (After Phase 3a validation)**

Stories:
1. Ralph loop wrapper around implement-story pipeline
2. External state files (.writ/state/loop-N.json) for cross-context-window persistence
3. Progressive autonomy thresholds (3 soft iterations, meta-rethink, escalation to human)
4. "Come back to a PR" mode (full autonomous run, structured status report)
5. Autonomous mode configuration (.writ/config.md: autonomy level, stop conditions)

Success criteria:
- Autonomous runs produce PRs with same quality as supervised runs
- Escalation to human happens <10% of runs (most succeed autonomously)
- External state enables overnight runs that survive context window resets
- Users opt into autonomous mode; supervised mode remains default

## Consequences

**Positive:**
- Context engine ships value faster (2-3 weeks vs 5-7 weeks for big bang)
- Autonomous mode design informed by real-world context engine usage
- Lower risk — one capability at a time, incremental validation
- Users experience immediate quality improvements without workflow disruption
- Backward compatible phasing — no forced migrations

**Negative:**
- Two separate rollouts (more communication needed)
- No single "Writ v2" marketing moment
- Users experience the full vision in stages (but backward compatibility makes this seamless)

**Risks:**
- If Phase 3a reveals fundamental context delivery issues, Phase 3b timeline extends. Mitigation: Phase 3a has clear success criteria; if not met, pause before Phase 3b.
- If users expect autonomous mode immediately after hearing about context engine, phasing may disappoint. Mitigation: roadmap communication is explicit — Phase 3a is context, Phase 3b is autonomy.

**Review Triggers:**
- After Phase 3a ships, measure review agent catch rate and coding agent error handling. If improvements are <20%, reassess before starting Phase 3b.
- If Phase 3a dogfooding reveals that context hints or "What Was Built" records are rarely used by agents, simplify Phase 3b design accordingly.
- If user feedback strongly prefers autonomous mode over context improvements, consider accelerating Phase 3b or running both in parallel (higher risk, but demand-driven).

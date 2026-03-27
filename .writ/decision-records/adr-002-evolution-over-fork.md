# ADR-002: Evolution Over Fork

> **Status:** Accepted
> **Date:** 2026-03-27
> **Deciders:** Product owner
> **Part of:** `/plan-product` discovery for Context Engine

## Context

Writ's roadmap explicitly deferred "skill-based automation, self-improving agents, and advanced delegation" to a "separate product extension." When planning this work, three architectural approaches were considered:

1. **Fork Writ** — create a new repository, convert command files to skills, implement Ralph loop automation from scratch
2. **Evolve Writ** — layer context engine and autonomous execution on top of existing command infrastructure
3. **New product** — build a separate framework that uses Writ specs as input but has its own execution model

The core question: Should Writ's next evolution be a fork or an enhancement?

## Decision Drivers

1. **Maintenance burden** — forks create two codebases where every improvement must be ported manually
2. **Existing investment** — 24 commands, 7 agents, 11K lines of structured methodology represents significant working capital
3. **User migration friction** — forcing users to choose between "classic Writ" and "new Writ" fragments the user base
4. **Architectural compatibility** — the identified problems (context delivery, autonomous execution) don't require throwing away the existing system
5. **Risk profile** — evolution allows incremental rollout; fork requires big-bang adoption

## Considered Options

### Option 1: Fork into Skills-Based Framework

**Approach:** Create a new repository. Convert command files to composable skills. Replace human-in-the-loop gates with Ralph loop automation. Rewrite agent orchestration for autonomous execution.

**Pros:**
- Clean slate — no legacy constraints
- Could explore radically different architectures (pure skill composition, no markdown commands)
- Skills could be more composable and shareable

**Cons:**
- Throws away 24 working commands, 7 specialized agents, and all existing spec infrastructure
- Every future improvement to core Writ requires manual porting to the fork
- Users must choose: stay on classic Writ or migrate to the fork
- High migration friction — existing specs might not work without manual translation
- Fork author becomes sole maintainer unless community splits (fragmentation risk)

**Effort:** XL (3+ months to reach feature parity with current Writ)

### Option 2: Evolve Writ with Context Engine and Autonomous Mode

**Approach:** Keep all 24 commands and 7 agents. Add a context engine layer that intelligently routes spec context to agents. Introduce autonomous execution mode as an option, not a replacement for human-in-the-loop.

**Pros:**
- Preserves all existing investment — commands, agents, spec format, user knowledge
- Backward compatible — old specs work with new features, just less optimized
- Incremental rollout — ship context engine first, autonomous mode later
- Maintenance stays unified — one codebase, one improvement stream
- Users get new capabilities without migration friction

**Cons:**
- Must maintain backward compatibility (constrains architecture)
- Can't explore radically different paradigms without breaking existing users
- Context engine must work with existing command structure

**Effort:** M (Context Engine: 2-3 weeks, Autonomous Mode: 3-4 weeks)

### Option 3: New Product Using Writ Specs

**Approach:** Build a separate framework that consumes Writ specs as input but executes them differently. Writ remains the spec authoring tool, new framework is the autonomous executor.

**Pros:**
- Clear separation of concerns — Writ owns planning, new tool owns execution
- Can explore autonomous execution without constraints
- Users can use Writ specs with either executor

**Cons:**
- Two products to maintain (even if separate)
- Spec format becomes an API contract between two systems (versioning complexity)
- Unclear value proposition — why not just enhance Writ directly?
- Splits user attention and community across two tools

**Effort:** L (4-6 weeks to build + ongoing dual maintenance)

## Decision

**Chosen: Option 2 — Evolve Writ with Context Engine and Autonomous Mode**

### Rationale

The core problems identified — context delivery gaps and lack of autonomous execution — don't require architectural replacement. They require targeted enhancements:

1. **Context delivery** can be solved by restructuring how spec content flows to agents (per-story hints, agent-specific views, cross-story records). This is a data flow problem, not an architecture problem.

2. **Autonomous execution** can be layered on top of the existing pipeline. The 6-gate structure (arch-check → code → lint → review → test → docs) doesn't need replacement — it needs external state tracking, iteration management, and escalation thresholds instead of hard caps.

3. **Existing commands are working assets.** `/create-spec`, `/implement-story`, `/verify-spec`, and the full agent suite represent months of refinement. Throwing them away to start over would be waste.

4. **Backward compatibility enables incremental adoption.** Users get Context Engine improvements immediately without changing their workflow. Autonomous mode becomes an opt-in enhancement, not a forced migration.

5. **One codebase means one improvement stream.** Every bug fix, every refinement, benefits all users. Forks fragment effort and community.

### Implementation Path

- **Phase 3a (Context Engine):** Per-story context hints, "What Was Built" records, agent-specific spec views, UAT plan generation. Ships 2-3 months after Phase 1 and 2 dogfooding completes.
- **Phase 3b (Autonomous Execution):** Ralph loop wrapper, external state files, progressive autonomy thresholds, "come back to a PR" workflow. Ships after Context Engine proves value.

## Consequences

**Positive:**
- All 24 commands and 7 agents remain intact and improve
- Users get better context routing without migration friction
- Maintenance burden stays unified
- Spec format evolution benefits all execution modes
- Community stays unified around one methodology

**Negative:**
- Must maintain backward compatibility (constrains some design choices)
- Can't explore radically different execution paradigms without breaking existing users
- Context engine must integrate with existing command structure (can't redesign from scratch)

**Risks:**
- If autonomous execution truly requires replacing the pipeline (not just wrapping it), this decision delays the inevitable fork
- If context engine proves insufficient, the backward compatibility constraint will feel limiting

**Review Triggers:**
- If Context Engine ships and coding agents still produce poor error handling despite targeted context, reassess whether the problem is delivery or capture
- If autonomous mode implementation reveals fundamental incompatibility with the 6-gate pipeline structure, revisit Option 1 or 3
- If maintenance burden for backward compatibility exceeds 20% of development time, evaluate whether the constraint is worth it

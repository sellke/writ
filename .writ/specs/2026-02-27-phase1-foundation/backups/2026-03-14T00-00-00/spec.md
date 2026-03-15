# Phase 1: Foundation — Specification

> Created: 2026-02-27
> Status: Complete ✅
> Contract Locked: ✅

## Contract Summary

**Deliverable:** Three interconnected capabilities that address Writ's top pain points — adaptive ceremony (`/prototype`), self-correcting pipeline (tiered spec-healing), and compounding intelligence (`/refresh-command`).

**Must Include:**
- `/prototype` as a standalone top-level command — no spec required
- Tiered spec-healing integrated into the review agent
- `/refresh-command` that scans agent transcripts and proposes command improvements

**Hardest Constraint:** Spec-healing severity classification — determining whether a deviation is small (auto-heal), medium (flag), or large (pause) requires judgment that's difficult to encode reliably.

**Success Criteria:**
- `/prototype` completes a small change in under 5 minutes of human wall-clock time
- Spec-healing catches real drift in ≥3 of 5 story implementations without false positives
- `/refresh-command` produces at least one actionable improvement per command analyzed

**Scope Boundaries:**
- Included: `/prototype` command, spec-healing review agent extension, `/refresh-command` command, drift report format, command overlay system
- Excluded: Cross-project patterns (Phase 2), self-improving agents (Phase 3), CLI tooling, MCP integration, PR agent

---

## Detailed Requirements

### Feature 1: `/prototype` Command

#### Purpose

Lightweight execution mode for small-to-medium changes that don't warrant the full 6-gate SDLC pipeline. The biggest day-to-day friction reducer identified in the SWOT analysis.

#### Design Philosophy

`/prototype` is fundamentally different from `--quick` mode on `/implement-story`:
- `--quick` operates within an existing spec — it runs a specific story with fewer gates
- `/prototype` operates **without a spec** — describe the change, answer 2-3 fast questions, ship code

The distinction matters: `/prototype` is for when the overhead of creating a spec exceeds the value of the change. A bug fix, a small feature addition, a UI tweak, a refactor — work where the full ceremony costs more than the work itself.

#### Pipeline

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ QUICK        │──▶│ CODING       │──▶│ LINT &       │──▶│ DONE         │
│ CONTRACT     │   │ AGENT (TDD)  │   │ TYPECHECK    │   │              │
│ (2-3 Q's)   │   │              │   │              │   │ + summary    │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                          │                                     │
                          │ complexity detected?                │
                          ▼                                     │
                   ┌──────────────┐                             │
                   │ ESCALATE     │                             │
                   │ to full      │── suggest /create-spec ─────┘
                   │ pipeline     │
                   └──────────────┘
```

**Gates included:** Quick contract → Coding agent (TDD) → Lint/typecheck
**Gates excluded:** Architecture check, review agent, testing agent (separate), documentation agent, visual QA
**Escape hatch:** If the coding agent detects complexity exceeding the prototype scope, it can recommend escalation to `/create-spec` → `/implement-story`.

#### Quick Contract

The quick contract replaces the full spec creation process with 2-3 targeted questions:

1. **What's the change?** — Natural language description of the work
2. **What files are involved?** — Auto-detected from codebase scan with human confirmation
3. **Any constraints?** — Performance, compatibility, or patterns to follow (optional)

No formal spec file is created. The contract lives in the conversation context.

#### Invocation

| Invocation | Behavior |
|---|---|
| `/prototype` | Interactive — asks what you want to build |
| `/prototype "add dark mode toggle to settings"` | Pre-filled description, skips question 1 |

#### Output

On completion, `/prototype` produces:
- A brief summary of what was changed and why
- A list of files modified
- Lint/typecheck pass confirmation
- An optional recommendation: "This change grew beyond prototype scope — consider running `/create-spec` to formalize it"

#### Scope Detection Heuristic

The coding agent should flag escalation when:
- More than 5 files need modification
- New database schema changes are required
- The change touches core architecture or shared utilities
- Test coverage for the change area is already low
- The change has dependencies on incomplete work

---

### Feature 2: Tiered Spec-Healing

#### Purpose

When implementation reveals that a spec was wrong or incomplete, the pipeline should self-correct proportionally rather than hard-failing. This addresses the #1 pain point identified during product discovery: spec drift with no structured reconciliation.

#### Integration Point

Spec-healing extends the **review agent** (`agents/review-agent.md`). The reviewer already reads the spec and the implementation — it's the natural place to detect and classify drift. Adding a separate gate would increase ceremony, which contradicts the adaptive ceremony principle.

#### Severity Tiers

| Tier | Examples | Detection Signal | Response |
|------|----------|------------------|----------|
| **Small** | Different function/variable name, minor API shape change, implementation detail that doesn't affect behavior | Cosmetic diff between spec and implementation; behavior matches intent | Auto-amend spec. Log the change in `drift-log.md`. Continue pipeline. |
| **Medium** | Scope expansion (added a feature not in spec), new dependency introduced, approach variation that changes integration points | Functional addition or dependency change not anticipated by spec | Flag in drift report with ⚠️. Continue pipeline with warning. Review post-implementation. |
| **Large** | Wrong approach entirely, fundamental constraint violation, security model change, data model incompatible with spec | Core architectural deviation or constraint breach | **Pause pipeline.** Surface conflict to human. Present: what spec said, what implementation did, why. Wait for decision: amend spec, revert code, or accept deviation. |

#### Default Severity

When severity is ambiguous, **default to Medium** (flag). Better to surface something unnecessary than to silently auto-heal something important.

#### Drift Report Format

Each story run generates a drift analysis appended to `.writ/specs/[spec-folder]/drift-log.md`:

```markdown
## Story N: [Name] — Drift Report

> Run: [DATE]
> Overall Drift: None | Small | Medium | Large

### Deviations

#### [DEV-001] [Brief description]
- **Severity:** Small / Medium / Large
- **Spec said:** [What the spec expected]
- **Implementation did:** [What actually happened]
- **Reason:** [Why the deviation occurred]
- **Resolution:** Auto-amended / Flagged for review / Pipeline paused
- **Spec amendment:** [Diff or description of spec change, if applicable]
```

#### Review Agent Extension

The review agent prompt gains a new section:

```
### Drift Analysis (NEW)
Compare the implementation against the spec contract and story requirements:

1. For each acceptance criterion, check if the implementation satisfies it AS WRITTEN or if it satisfies the INTENT through a different approach
2. Classify any deviations using the severity tiers:
   - Small: cosmetic/naming differences, implementation details
   - Medium: scope additions, new dependencies, approach variations
   - Large: architectural changes, constraint violations, security model changes
3. When ambiguous, classify as Medium
4. For Small deviations: propose a spec amendment
5. For Medium deviations: flag with explanation, continue
6. For Large deviations: PAUSE and report — do not continue review

Output a structured drift report section in your review.
```

#### Spec Amendment Format

When the review agent auto-amends (Small severity), it appends to `drift-log.md` and notes the change. The original spec is NOT modified — drift-log serves as a living amendment record. This preserves the original contract while documenting how reality refined it.

---

### Feature 3: `/refresh-command` Command

#### Purpose

The learning loop. After using any Writ command, `/refresh-command` scans what happened, identifies what worked and what caused friction, and proposes concrete improvements to the command file. Commands get better through use.

#### How It Works

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ SELECT       │──▶│ SCAN         │──▶│ ANALYZE      │──▶│ PROPOSE      │
│ COMMAND +    │   │ TRANSCRIPT   │   │ FRICTION &   │   │ AMENDMENTS   │
│ TRANSCRIPT   │   │              │   │ PATTERNS     │   │              │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                                                                │
                                                         ┌──────┴──────┐
                                                         │  LOCAL      │
                                                         │  APPLY      │
                                                         │  + changelog│
                                                         └──────┬──────┘
                                                                │
                                                         ┌──────┴──────┐
                                                         │  PROMOTION  │
                                                         │  REVIEW     │
                                                         │  (optional) │
                                                         └─────────────┘
```

#### Invocation

| Invocation | Behavior |
|---|---|
| `/refresh-command` | Interactive — select command and transcript |
| `/refresh-command create-spec` | Refresh a specific command, select transcript |
| `/refresh-command create-spec --last` | Refresh using the most recent transcript that used that command |

#### Input: Transcript Scanning

The command reads agent transcript files (`.jsonl` format in `agent-transcripts/`). It scans for:

1. **Command identification** — Which Writ command was being executed
2. **Friction signals** — Points where the agent struggled, asked unnecessary questions, produced low-quality output, or required many iterations
3. **Skip signals** — Steps the user skipped or dismissed (like our AskQuestion skips during this session)
4. **Surprise signals** — Places where the agent's output was unexpectedly good or bad
5. **Duration signals** — Steps that took disproportionately long

#### Analysis: Pattern Extraction

For each signal, the analyzer determines:
- **Root cause** — Is this a command design issue, a prompt quality issue, or a context gap?
- **Impact** — How much time/quality did this cost?
- **Frequency** — Has this pattern appeared in other transcripts?
- **Fixability** — Can the command file be changed to address this?

#### Output: Proposed Amendments

The command produces:
1. **A diff** — Specific changes to the command markdown file
2. **Rationale** — Why each change improves the command
3. **Confidence** — High/Medium/Low confidence that the change is an improvement
4. **Scope assessment** — Is this project-specific or universally applicable?

#### Local-First Application

Amendments are applied to the project's local copy of the command:
- Cursor: `.cursor/commands/[command].md`
- Claude Code: `.claude/commands/[command].md`
- OpenClaw: `~/.openclaw/workspace/skills/writ/commands/[command].md`

If no local copy exists, one is created from the core Writ command as a base.

#### Promotion Review

After local application, the command optionally asks:

```
This improvement looks universally applicable:
- [Description of change]
- [Rationale]

Promote to Writ core? (This would create a PR against the writ repository)
- Yes — generate upstream PR
- No — keep local only
- Later — save for batch promotion review
```

Promotion generates a changelog entry in `.writ/refresh-log.md`:

```markdown
## [DATE] — /[command] refreshed

**Source transcript:** [transcript ID]
**Changes:**
- [Change 1 description]
- [Change 2 description]

**Scope:** Local only / Promoted to core
**Confidence:** High / Medium / Low
```

#### Bootstrap Property

`/refresh-command` should be designed to work on itself. The first command it refreshes after shipping should be `/refresh-command` itself — validating the learning loop by improving the learner.

---

## Implementation Approach

### Dependency Graph

```
Story 1: /prototype command ──────────────────── (independent)
Story 2: Spec-healing review agent extension ─── (independent)
Story 3: Drift report format & drift-log.md ──── depends on Story 2
Story 4: /refresh-command core ───────────────── (independent)
Story 5: /refresh-command promotion pipeline ─── depends on Story 4
Story 6: Command overlay system ──────────────── depends on Stories 1, 4
Story 7: Integration testing & dogfooding ────── depends on all above
```

### Parallel Execution Batches

```
Batch 1 (parallel): Story 1, Story 2, Story 4
Batch 2 (parallel): Story 3, Story 5, Story 6
Batch 3 (sequential): Story 7
```

### Technical Patterns

All three features are **command files** (markdown) and **agent extensions** (markdown) — no runtime code, no CLI, no server. This means:

- Changes are Git-diffable and reviewable
- No build step, no deployment, no infrastructure
- Testing = dogfooding (use the commands and verify they work)
- Distribution = file copy (existing install/update scripts)

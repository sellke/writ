# Phase 1: Foundation — Technical Specification

> Created: 2026-02-27
> Last Updated: 2026-03-14
> Spec: Phase 1 Foundation
> Status: In Progress — Dogfooding Pending

## Architecture Overview

All Phase 1 deliverables are **markdown files** — command definitions and agent prompt extensions. There is no runtime code, no CLI binary, no server, no database. The "implementation" is writing precise markdown instructions that AI agents follow.

```
commands/
├── prototype.md          ← NEW (Story 1)
├── refresh-command.md    ← NEW (Story 4)
├── plan-product.md       ← MODIFIED (Story 8 — gstack-inspired enhancements)
└── implement-story.md    ← MODIFIED (Stories 2, 3 — pass spec context to reviewer)

agents/
├── review-agent.md       ← MODIFIED (Story 2 — add drift analysis section)
└── coding-agent.md       ← UNCHANGED (shared by both /prototype and /implement-story)

scripts/
├── install.sh            ← MODIFIED (Story 6 — preserve local overlays)
└── update.sh             ← MODIFIED (Story 6 — warn on conflict)

.writ/
├── refresh-log.md        ← NEW (Story 5 — changelog for command refreshes)
├── product/              ← MODIFIED (Story 8 — mission, roadmap, decisions updated)
├── research/             ← NEW (Story 8 — gstack analysis research)
└── docs/
    └── drift-report-format.md  ← NEW (Story 3 — canonical format reference)
```

## Feature 1: /prototype Command

### File: `commands/prototype.md`

New command file defining the lightweight execution flow.

**Pipeline stages:**
1. **Quick contract** — 2-3 AskQuestion rounds (what, where, constraints)
2. **Coding agent** — Spawns `agents/coding-agent.md` with contract context instead of story file
3. **Lint/typecheck** — Same mechanism as implement-story Gate 2
4. **Summary** — Files changed, lint pass, optional escalation recommendation

**Coding agent integration:**
The coding agent receives a "prototype contract" instead of a story file. The prompt is parameterized:
- In `/implement-story`: receives story content, spec-lite, acceptance criteria
- In `/prototype`: receives description, file list, constraints, codebase patterns

No changes to `agents/coding-agent.md` are needed — the orchestrating command provides different context.

**Escalation heuristic:**
The coding agent prompt includes scope detection criteria. When triggered, the agent includes an escalation recommendation in its output. The prototype orchestrator surfaces this in the summary.

Escalation triggers:
- More than 5 files modified
- Database schema changes detected
- Core architecture / shared utility modifications
- Test coverage in affected area is below threshold
- Dependencies on incomplete work detected

### Adapter Considerations

The command file is platform-agnostic. For each platform:
- **Cursor:** Copy to `.cursor/commands/prototype.md`
- **Claude Code:** Copy to `.claude/commands/prototype.md`
- **OpenClaw:** Available via skill system

## Feature 2: Tiered Spec-Healing

### File: `agents/review-agent.md` (modification)

Add a new section to the review agent's prompt template:

**New input parameter:** `spec_lite_content` — the condensed spec for comparison

**New review section: Drift Analysis**

The reviewer compares implementation against spec contract and classifies deviations:

| Severity | Detection Criteria | Agent Action |
|----------|-------------------|--------------|
| Small | Naming differences, implementation details, cosmetic API shape changes that don't affect behavior | Include spec amendment recommendation in output |
| Medium | Scope additions not in spec, new dependencies introduced, approach that changes integration points | Flag with ⚠️ and explanation in output |
| Large | Architectural deviation, constraint violation, security model change, data model incompatibility | Report PAUSE with full context: what spec said, what happened, why |

**Ambiguity rule:** When severity is unclear, classify as Medium.

**Output format addition:**

```markdown
## Drift Analysis

**Overall Drift:** None | Small | Medium | Large

### Deviations (if any)

#### DEV-001: [Description]
- Severity: [Small/Medium/Large]
- Spec expected: [quote from spec]
- Implementation: [what was done]
- Reason: [inferred or stated reason]
- Recommendation: [amendment text for Small, explanation for Medium, full context for Large]
```

### File: `commands/implement-story.md` (modification)

Two changes to the implement-story orchestrator:

1. **Before Gate 3 (Review):** Load `spec-lite.md` and pass as `spec_lite_content` to the review agent
2. **After Gate 3 (Review):** Parse the drift analysis from review output and:
   - Small: Apply amendment to `drift-log.md`, continue
   - Medium: Log to `drift-log.md` with ⚠️, continue with warning message
   - Large: Log to `drift-log.md`, pause pipeline, present conflict via AskQuestion

### File: `.writ/docs/drift-report-format.md` (new)

Canonical reference for the drift report format. Used by both the review agent (to format output) and implement-story (to parse and write drift-log).

## Feature 3: /refresh-command

### File: `commands/refresh-command.md`

New command file defining the learning loop.

**Stage 1: Select**
- Interactive: AskQuestion to pick command + transcript
- Direct: `/refresh-command [command-name]` skips command selection
- `--last` flag: auto-selects most recent transcript containing the specified command

**Stage 2: Scan**
Read the agent transcript (.jsonl). Identify:
- Which Writ command was executed (search for command invocation patterns)
- Friction signals: repeated attempts, error recovery, low-quality output
- Skip signals: AskQuestion responses that were skipped
- Surprise signals: unexpectedly good or bad output quality
- Duration signals: steps that took disproportionate time

**Stage 3: Analyze**
For each signal, determine:
- Root cause: command design flaw, prompt quality issue, or context gap
- Impact: time cost or quality cost
- Fixability: can the command file be changed to address this
- Scope: project-specific concern or universal improvement

**Stage 4: Propose**
Generate output:
- Specific diff to the command markdown file
- Rationale for each change
- Confidence level (High/Medium/Low)
- Scope assessment (local-only vs. universally applicable)

**Stage 5: Apply (local)**
- If project-local copy exists: apply diff to local copy
- If no local copy: copy core command as base, apply diff
- Write changelog entry to `.writ/refresh-log.md`

**Stage 6: Promote (optional, Story 5)**
- If scope is universal and confidence is High: offer promotion
- AskQuestion: Yes (PR) / No (local only) / Later (batch)

### Transcript Identification

Agent transcripts are `.jsonl` files. To identify which Writ command was used:
- Search for command invocation patterns (e.g., `/create-spec`, `/implement-story`)
- Search for command-specific markers (e.g., "Contract Locked: ✅", "Gate 0: Architecture Check")
- Fall back to filename/metadata if available

### Bootstrap Design

`/refresh-command` must be able to analyze transcripts of its own use. This means:
- The command's own patterns (AskQuestion rounds, analysis output) should be scannable
- Improvements to `/refresh-command` itself follow the same local-first → promote flow

## Command Overlay System (Story 6)

### Precedence Rules

```
1. Check platform-local path (.cursor/commands/, .claude/commands/, etc.)
2. If local copy exists → use it
3. If no local copy → use core command (commands/)
```

This is a **documentation and script convention**, not a runtime system. AI agents follow instructions in whatever command file they're given. The overlay system ensures they're given the right one.

### Script Changes

**`scripts/install.sh`:**
- Before copying, check if local copy already exists
- If exists: skip (preserve local modifications)
- If not exists: copy from core
- New flag: `--force` to overwrite local copies (with warning)

**`scripts/update.sh`:**
- Check each core command against local copy
- If local copy is unmodified (matches previous core version): update to new core
- If local copy has modifications: warn and skip, show diff
- New flag: `--merge` to attempt automatic merge of core updates with local modifications

## Feature 4: /plan-product gstack Enhancement

### File: `commands/plan-product.md` (modification)

~100 lines added implementing six gstack-inspired techniques:

**New step: 1.1c Planning Posture Selection**
AskQuestion with three options: EXPANSION (dream big, 10-star product), HOLD (pressure-test the framing), REDUCTION (strip to minimum viable). Selected posture shapes all downstream discovery and recommendations.

**New opening move: Premise Challenge**
Before any information-gathering, challenge the premise: "Is this the right problem? What would happen if we did nothing? Who benefits most?" This is mandatory regardless of posture.

**New discovery technique: Dream State Mapping**
`CURRENT STATE → THIS PLAN → 12-MONTH IDEAL` progression. Required in EXPANSION mode, encouraged in HOLD. Forces long-horizon thinking and tests whether the MVP points toward the right future.

**Modified posture: Opinionated Recommendations**
All recommendations throughout discovery and contract phases use "I recommend X because Y" format instead of neutral option menus. Pushback phrasing leads with the recommendation, not the concern.

**New contract section: Failure Surface Analysis**
Mandatory table in product contracts for Moderate/Complex products: User Flow → What Can Break → User Impact → Mitigation. Identifies critical failure modes before code is written.

**New contract section: Architecture Diagrams**
Mandatory ASCII diagrams for Moderate/Complex products. Forces hidden assumptions into the open. Not optional.

### Files Modified (Product Layer)

| File | Changes |
|------|---------|
| `.writ/product/mission-lite.md` | Added opinionated guidance differentiator, design principle 6 |
| `.writ/product/mission.md` | Added last-updated date |
| `.writ/product/decisions.md` | Added DEC-006 (Opinionated & Aspirational Posture) |
| `.writ/product/roadmap.md` | Added `/plan-product` enhancement as Phase 1 feature, new Phase 2 items, design principle 6 |

### Adapter Considerations

Changes to `commands/plan-product.md` are platform-agnostic. The Cursor mirror (`.cursor/commands/plan-product.md`) should be synchronized after modification.

---

## Cross-Cutting Concerns

### Context Window Management

Phase 1 adds content to agent prompts:
- Review agent gains ~30 lines of drift analysis instructions
- Review agent receives spec-lite content (typically 30-50 lines)
- This is within acceptable bounds for current context windows

### Testing Strategy

All deliverables are markdown files. "Testing" means:
1. **Structural validation:** Verify files exist, follow expected format
2. **Dogfooding:** Run the commands on real tasks (Story 7)
3. **Cross-reference:** Verify agent prompts reference correct input parameters
4. **Scenario testing:** Walk through each severity tier manually

### Distribution

Phase 1 deliverables ship through existing mechanisms:
- `scripts/install.sh` copies new commands to local project
- `scripts/update.sh` handles updates with overlay awareness
- README updated with new command documentation

# Enhanced Edit Spec Command (edit-spec)

## Overview

Modify existing feature specifications using a contract-first approach that ensures complete alignment between developer and AI before updating any supporting files. This command prevents assumptions by establishing a clear "modification contract" through structured clarification rounds using `AskQuestion`.

## Command Process

### Phase 1: Specification Loading & Change Contract (No File Modifications)

**Mission Statement:**
> Your goal is to help me modify an existing specification safely and precisely. You will deliver the updated spec package only after we both agree on the modification contract. **Important: Challenge changes that could break existing functionality or create technical debt - it's better to surface concerns early than implement problematic modifications.**

#### Step 1.1: Specification Discovery & Selection

**If spec-identifier provided:**
1. **SEARCH** `.writ/specs/` for exact or partial folder name match
2. **IF** multiple matches, use AskQuestion for disambiguation

**If no spec-identifier provided:**

```
AskQuestion({
  title: "Edit Specification - Select Target",
  questions: [
    {
      id: "spec_target",
      prompt: "Which specification do you want to modify?",
      options: [
        // Dynamically populated from .writ/specs/
        { id: "spec_1", label: "[DATE] Feature Name (X stories, Y% complete)" },
        { id: "spec_2", label: "[DATE] Feature Name (X stories, Y% complete)" },
        { id: "spec_3", label: "[DATE] Feature Name (X stories, Y% complete)" }
      ]
    }
  ]
})
```

#### Step 1.2: Load Current State

1. **READ** primary specification file (`spec.md`)
2. **READ** user stories overview (`user-stories/README.md`)
3. **READ** all individual story files in `user-stories/` directory
4. **READ** all sub-specifications in `sub-specs/` directory
5. **SCAN** codebase for any implementation progress related to this spec

**Present current state summary** (no modifications yet):

```
## Current Specification: [Feature Name]

**Created:** [DATE]
**Stories:** X total (Y complete, Z in progress, W not started)
**Implementation Progress:** N/M tasks complete (X%)

### Story Status
| # | Title | Status | Tasks | Progress |
|---|-------|--------|-------|----------|
| 1 | [Name] | ✅ Complete | 6 | 6/6 |
| 2 | [Name] | 🔄 In Progress | 5 | 3/5 |
| 3 | [Name] | ⬜ Not Started | 7 | 0/7 |
```

#### Step 1.3: Change Type Classification

**If user described their change upfront**, analyze it and skip to Step 1.4.

**If change is vague or not provided:**

```
AskQuestion({
  title: "What kind of change?",
  questions: [
    {
      id: "change_type",
      prompt: "What type of modification are you making?",
      options: [
        { id: "add_feature", label: "Add new functionality (new stories)" },
        { id: "modify_existing", label: "Change existing stories or requirements" },
        { id: "remove_scope", label: "Remove or descope functionality" },
        { id: "refactor_stories", label: "Reorganize/split/combine stories" },
        { id: "update_technical", label: "Change technical approach (same features)" },
        { id: "multiple", label: "Multiple types of changes" }
      ]
    },
    {
      id: "change_scope",
      prompt: "How broad is this change?",
      options: [
        { id: "single_story", label: "Affects a single story" },
        { id: "few_stories", label: "Affects 2-3 stories" },
        { id: "broad", label: "Affects most or all stories" },
        { id: "unsure", label: "Not sure yet" }
      ]
    }
  ]
})
```

If `single_story` selected, follow up:

```
AskQuestion({
  title: "Which story?",
  questions: [
    {
      id: "target_story",
      prompt: "Which story needs changes?",
      options: [
        // Dynamically populated from story files
        { id: "story_1", label: "Story 1: [Title] (✅ Complete)" },
        { id: "story_2", label: "Story 2: [Title] (🔄 In Progress - 3/5)" },
        { id: "story_3", label: "Story 3: [Title] (⬜ Not Started)" }
      ]
    }
  ]
})
```

#### Step 1.4: Impact Analysis (Internal)

**Internal Process (not shown to user):**
- Analyze proposed changes against current specification
- Identify affected story files and task groups
- Note potential ripple effects on:
  - Existing implementation (completed work at risk)
  - Story dependencies and sequencing
  - Technical architecture and sub-specs
  - Acceptance criteria within affected stories
- Classify risks:
  - **Breaking Changes**: Will this invalidate completed work?
  - **Architecture Impact**: Does this conflict with existing patterns?
  - **Scope Creep**: Are we expanding beyond original boundaries?
  - **Dependency Chain**: Will this cascade to other stories?

#### Step 1.5: Structured Clarification Loop

**Use `AskQuestion` for structured clarification, batching related questions (max 5-7 per round).**

**Round 1 — Change Details & Impact Tolerance:**

```
AskQuestion({
  title: "Change Clarification - Round 1",
  questions: [
    {
      id: "completed_work",
      prompt: "Story 1 is already complete and would be affected. How should we handle it?",
      options: [
        { id: "preserve", label: "Preserve completed work, add changes on top" },
        { id: "rework", label: "Rework is acceptable if needed" },
        { id: "avoid", label: "Adjust the change to avoid touching completed stories" }
      ]
    },
    {
      id: "migration",
      prompt: "There's existing implementation. What's your migration preference?",
      options: [
        { id: "incremental", label: "Incremental - keep what works, modify in place" },
        { id: "clean", label: "Clean break - rewrite affected areas" },
        { id: "recommend", label: "Recommend the safest approach" }
      ]
    },
    {
      id: "timeline_impact",
      prompt: "This change adds ~2 stories worth of work. Is that acceptable?",
      options: [
        { id: "yes", label: "Yes, scope increase is fine" },
        { id: "trade", label: "Add this but remove something else to compensate" },
        { id: "minimal", label: "Find the minimal version of this change" }
      ]
    }
  ]
})
```

**Round 2+ — Technical & Scope Questions (as needed):**

Adapt questions based on Round 1 answers. Continue until 95% confidence on modification impact. Use free-text follow-up only when structured options can't capture the nuance.

**Critical Analysis Responsibility:**
- If proposed changes conflict with existing implementation, explain impact and suggest migration strategies
- If scope changes affect dependent specifications, identify and discuss dependencies
- If modifications introduce technical complexity, assess if benefits justify the cost
- If changes affect in-progress stories, surface timeline implications
- If proposed changes contradict original business value, question the rationale

**Pushback Phrasing Examples:**
- "This change would invalidate 3 completed tasks in Story 2. Is the rework worth the improvement?"
- "I see a simpler way to achieve this that only touches Story 4 instead of Stories 2-5. Want to explore that?"
- "This conflicts with your existing [pattern]. Should we update the pattern or adjust the change?"
- "Adding this would push Story 3 to 9 tasks — I'd recommend splitting it. Agree?"

#### Step 1.6: Modification Contract Proposal

When confident about changes, present the contract:

```
## Modification Contract

**Target Specification:** [Specification name and date]

**Proposed Changes:** [Clear description of what will be modified]

**Change Type:** [Addition/Removal/Modification/Refactor]

**Impact Assessment:**
- **Stories Modified:** [List of specific story files that change]
- **Stories Added:** [Any new story files to create]
- **Stories Removed/Archived:** [Any stories becoming obsolete]
- **Tasks Affected:** [Task groups needing modification]
- **Completed Work at Risk:** [What finished work gets touched, if any]

**Migration Strategy:**
- [How to handle existing implementation]
- [Steps to preserve completed work]
- [Rollback plan if needed]

**Updated Scope Boundaries:**
- **Still In Scope:** [Unchanged from original]
- **Now In Scope:** [Additions]
- **Removed From Scope:** [Removals]
- **Still Out of Scope:** [Unchanged exclusions]

**⚠️ Risks & Concerns:**
- [Specific risks from the changes]
- [Potential complications or dependencies]

**💡 Recommendations:**
- [Safer implementation approaches]
- [Ways to minimize disruption]

**Effort Estimate:** [Additional/changed work involved]
```

**Then IMMEDIATELY use AskQuestion for contract decision:**

```
AskQuestion({
  title: "Modification Contract Decision",
  questions: [
    {
      id: "contract_action",
      prompt: "How would you like to proceed?",
      options: [
        { id: "yes", label: "Lock contract and update the specification" },
        { id: "edit", label: "Edit the contract (I'll specify changes)" },
        { id: "compare", label: "Show detailed before/after comparison" },
        { id: "risks", label: "Explore implementation risks in detail" },
        { id: "rollback", label: "Understand how to undo these changes later" },
        { id: "questions", label: "I have more questions before deciding" }
      ]
    }
  ]
})
```

**Handling responses:**
- **yes**: Proceed to Phase 2
- **edit**: Ask free-text: "What changes would you like to make to the contract?"
- **compare**: Present side-by-side before/after for affected stories, then re-present AskQuestion
- **risks**: Present detailed risk analysis with mitigation strategies, then re-present AskQuestion
- **rollback**: Explain backup/restore process, then re-present AskQuestion
- **questions**: Ask "What would you like to clarify?" then return to clarification loop

### Phase 2: Specification Update (Post-Agreement Only)

**Triggered only after user confirms modification contract with 'yes'**

#### Step 2.1: Initialize Modification Tracking

```bash
# Use todo_write to track modification process
1. Create backup of original specification files
2. Update core specification document (spec.md, spec-lite.md)
3. Modify affected individual story files
4. Create/remove/archive story files as needed
5. Update user-stories/README.md with new progress tracking
6. Update technical sub-specifications
7. Adjust task groups (maintain 5-7 tasks max per story)
8. Create change log entry
9. Present updated package for validation
```

#### Step 2.2: Create Backup & Change Documentation

**Backup Process:**
1. **CREATE** backup folder: `.writ/specs/[spec-folder]/backups/[timestamp]/`
2. **COPY** all current files to backup
3. **CREATE** or **APPEND** to `CHANGELOG.md` within spec folder

**Change Log Format:**
```markdown
## [Date] - [Change Type]
**Modification Contract:** [Brief summary]

### Changes Made:
- [Specific change 1]
- [Specific change 2]

### Files Updated:
- spec.md - [what changed]
- user-stories/README.md - [progress tracking updates]
- user-stories/story-N-{name}.md - [specific story changes]

### Backup Location:
`backups/[timestamp]/`
```

#### Step 2.3: Update Core Specification

**spec.md Updates:**
- Modify contract summary to reflect new agreement
- Update detailed requirements
- Revise implementation approach if changed
- Add change log reference

**spec-lite.md Updates:**
- Regenerate condensed version reflecting all changes

#### Step 2.4: Update Story Files

**For modified stories:**
- Update tasks, acceptance criteria, and notes
- Preserve task completion status where work is still valid
- Annotate tasks needing rework:
  ```markdown
  - [x] 1.1 Write tests for user auth ✅ (Still valid)
  - [ ] 1.2 Implement OAuth provider ⚠️ (Needs modification per change contract)
  - [ ] 1.3 Create social login UI 🆕 (New task)
  ```

**For new stories:**
- Spawn parallel `Task` subagents (same pattern as `create-spec` Step 2.6)
- Use `agents/user-story-generator.md` agent reference
- Max 4 subagents at a time

**For removed/archived stories:**
- Move to `user-stories/archived/` with timestamp
- Do NOT delete — preserve for rollback

**Story management rules:**
- If modifications push a story beyond 7 tasks → split into multiple stories
- If modifications shrink a story below 3 tasks → consider combining with related story
- Update all dependency declarations across affected stories

#### Step 2.5: Update README & Sub-Specs

**user-stories/README.md:**
- Update story table (add/remove/modify rows)
- Update progress percentages
- Update dependency graph
- Add/remove quick links

**Sub-specifications:**
- Only update sub-specs affected by the changes
- Create new sub-specs if new technical areas introduced
- Archive sub-specs no longer relevant

#### Step 2.6: Final Validation

Present updated package and use AskQuestion for validation:

```
✅ Specification successfully updated!

📁 .writ/specs/[DATE]-feature-name/
├── 📋 spec.md - ⭐ Updated
├── 📝 spec-lite.md - ⭐ Updated
├── 👥 user-stories/
│   ├── 📊 README.md - ⭐ Updated progress & dependencies
│   ├── 📝 story-1-{name}.md - [status indicator]
│   ├── 📝 story-2-{name}.md - [status indicator]
│   ├── 📝 story-N-{name}.md - 🆕 New
│   └── 📂 archived/ - 🗃️ Removed stories preserved
├── 📂 sub-specs/ - [update indicators]
├── 💾 backups/[timestamp]/ - Original preserved
└── 📝 CHANGELOG.md - ⭐ Change documented

## Summary
- **Stories Modified:** X
- **Stories Added:** Y
- **Stories Archived:** Z
- **Tasks Affected:** N task groups reorganized
- **Completed Work Preserved:** X/Y completed tasks still valid
```

```
AskQuestion({
  title: "Validation",
  questions: [
    {
      id: "validation",
      prompt: "Does the updated specification look correct?",
      options: [
        { id: "approved", label: "Looks good — specification is updated" },
        { id: "adjustments", label: "Needs minor adjustments (I'll specify)" },
        { id: "rollback", label: "Rollback — restore from backup" }
      ]
    }
  ]
})
```

**Handling responses:**
- **approved**: Done. Spec is updated and ready for `/implement-spec` or `/implement-story`.
- **adjustments**: Ask free-text: "What needs adjusting?" Apply changes inline (no new contract needed for minor tweaks).
- **rollback**: Restore all files from `backups/[timestamp]/`, confirm restoration.

## Example Usage Flow

```
Developer: /edit-spec "user-auth" "add biometric authentication"

Agent: [Loads spec, scans codebase]

## Current Specification: User Authentication System

**Created:** 2026-02-15
**Stories:** 8 total (3 complete, 1 in progress, 4 not started)
**Implementation Progress:** 18/42 tasks (43%)

I found your user auth specification. You want to add biometric authentication.
Before I dig into questions — your current implementation is web-focused, but biometric
auth typically needs native apps or WebAuthn. I see no mobile components in your spec.

[Uses AskQuestion]

┌─────────────────────────────────────────────────────────────┐
│ Change Clarification - Round 1                              │
├─────────────────────────────────────────────────────────────┤
│ 1. What kind of biometric authentication?                   │
│    ○ WebAuthn (browser-based, fingerprint/face via OS)      │
│    ○ Native mobile biometrics (Face ID, Touch ID)           │
│    ○ Both web and mobile                                    │
│    ○ Let me recommend based on your current architecture    │
│                                                             │
│ 2. Should biometric auth be required or optional?           │
│    ○ Required for all users                                 │
│    ○ Optional enhancement for supported devices             │
│    ○ Required for sensitive actions only (payments, etc.)   │
│                                                             │
│ 3. Story 2 (Login Flow) is in progress (3/5 tasks done).   │
│    This change would affect it. How to handle?              │
│    ○ Preserve progress, add biometric as additional tasks   │
│    ○ It's fine to rework Story 2 if needed                  │
│    ○ Create a separate story for biometric login instead    │
└─────────────────────────────────────────────────────────────┘

Developer: [Selects: "WebAuthn", "Optional enhancement", "Create a separate story"]

Agent: Good call — separate story keeps the in-progress work clean. WebAuthn as
optional means no breaking changes to existing auth. One more round:

┌─────────────────────────────────────────────────────────────┐
│ Change Clarification - Round 2                              │
├─────────────────────────────────────────────────────────────┤
│ 1. Browser support strategy?                                │
│    ○ Modern only (Chrome 67+, Firefox 60+, Safari 14+)      │
│    ○ Progressive — offer when available, hide when not      │
│    ○ Show prompt to upgrade if browser doesn't support it   │
│                                                             │
│ 2. Where in the UX flow?                                    │
│    ○ Login page — "Sign in with fingerprint" button         │
│    ○ Settings — "Enable biometric login" toggle             │
│    ○ Both — setup in settings, use on login                 │
└─────────────────────────────────────────────────────────────┘

Developer: [Selects: "Progressive", "Both"]

Agent: Clear. Here's the modification contract:

## Modification Contract

**Target:** User Authentication System (2026-02-15)
**Change Type:** Addition (non-breaking)

**Proposed Changes:** Add WebAuthn biometric authentication as optional
progressive enhancement. New story for biometric setup + login.

**Impact Assessment:**
- **Stories Modified:** None (existing stories untouched)
- **Stories Added:** 1 new story (Story 9: Biometric Authentication)
- **Completed Work at Risk:** None

**Migration Strategy:**
- No changes to existing implementation
- New story is independent — can be implemented in any order

**⚠️ Risks:**
- WebAuthn requires HTTPS in production
- Credential storage needs secure server-side handling

**Effort Estimate:** 1 new story, ~6 tasks, modest complexity

┌─────────────────────────────────────────────────────────────┐
│ Modification Contract Decision                              │
├─────────────────────────────────────────────────────────────┤
│    ○ Lock contract and update the specification             │
│    ○ Edit the contract (I'll specify changes)               │
│    ○ Show detailed before/after comparison                  │
│    ○ Explore implementation risks in detail                 │
│    ○ Understand how to undo these changes later             │
│    ○ I have more questions before deciding                  │
└─────────────────────────────────────────────────────────────┘

Developer: [Selects: "Lock contract"]

Agent: ✅ Contract locked! Updating specification...

[Creates backup, spawns subagent for new story, updates README, logs change]

✅ Specification updated!

- Story 9: Biometric Authentication (6 tasks) — 🆕 Created
- README.md — ⭐ Updated with new story + dependencies
- CHANGELOG.md — ⭐ Change documented
- Backup at backups/2026-02-23T02-45-00/

┌─────────────────────────────────────────────────────────────┐
│ Validation                                                  │
├─────────────────────────────────────────────────────────────┤
│    ○ Looks good — specification is updated                  │
│    ○ Needs minor adjustments (I'll specify)                 │
│    ○ Rollback — restore from backup                         │
└─────────────────────────────────────────────────────────────┘

Developer: [Selects: "Looks good"]

Agent: Done! You can implement it with `/implement-story story-9` or include it
in your next `/implement-spec` run.
```

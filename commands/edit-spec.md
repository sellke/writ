# Enhanced Edit Spec Command (edit-spec)

## Overview

Modify existing feature specifications using a contract-first approach that ensures complete alignment between developer and AI before updating any supporting files. This command prevents assumptions by establishing a clear "modification contract" through structured clarification rounds.

## Command Process

### Phase 1: Specification Loading & Change Contract (No File Modifications)

**Mission Statement:**
> Your goal is to help me modify an existing specification safely and precisely. You will deliver the updated spec package only after we both agree on the modification contract. **Important: Challenge changes that could break existing functionality or create technical debt - it's better to surface concerns early than implement problematic modifications.**

#### Step 1.1: Specification Discovery & Loading

**Locate Target Specification:**
1. **SCAN** `.writ/specs/` directory for all existing specifications
2. **IF** spec-identifier provided:
   - **SEARCH** for exact folder name match: `[DATE]-{spec-identifier}`
   - **SEARCH** for partial name match in folder names
   - **SEARCH** for identifier in spec.md titles/content
3. **IF** spec-identifier is "latest":
   - **FIND** most recent folder by date prefix
4. **IF** no spec-identifier provided:
   - **LIST** all available specifications for user selection
5. **IF** multiple matches found:
   - **PRESENT** options for user disambiguation

**Load Current State:**
1. **READ** primary specification file (`spec.md`)
2. **READ** user stories overview (`user-stories/README.md`)
3. **READ** all individual story files in `user-stories/` directory
4. **READ** all sub-specifications in `sub-specs/` directory
5. **SCAN** codebase for any implementation progress related to this spec
6. **OUTPUT:** Current specification summary with story status (no modifications yet)

#### Step 1.2: Impact Analysis & Change Assessment

**Internal Process (not shown to user):**
- Analyze proposed changes against current specification
- Identify affected individual story files and task groups
- Note potential ripple effects on:
  - Existing implementation (if any)
  - Specific user story files in user-stories/ folder
  - Story dependencies and sequencing
  - Technical architecture
  - Acceptance criteria within affected stories
  - Project timelines and story priorities
- Catalog modification domains:
  - Scope changes (adding/removing/splitting stories)
  - Technical approach modifications
  - Individual story adjustments or combinations
  - Task group reorganization (keeping 5-7 tasks max)
  - Performance/security requirement changes
  - Integration point modifications
  - Success criteria updates within stories

#### Step 1.3: Change Clarification Loop

**Rules:**
- Ask ONE focused question at a time about the proposed changes
- After each answer, re-analyze the existing spec and codebase for new context
- Continue until reaching 95% confidence on modification impact
- Each question should target the highest-impact unknown or risk
- **Never declare "final question"** - let the conversation flow naturally
- **Challenge changes that could break existing functionality or create technical debt**

**Critical Analysis Responsibility:**
- If proposed changes conflict with existing implementation, explain impact and suggest migration strategies
- If scope changes affect other dependent specifications, identify and discuss dependencies
- If modifications introduce technical complexity, assess if benefits justify the cost
- If changes affect user stories that may already be in progress, surface timeline implications
- If proposed changes contradict original business value, question the modification rationale

**Risk Assessment Categories:**
- **Breaking Changes**: Will this break existing functionality?
- **Implementation Impact**: How much existing work needs to be modified/discarded?
- **Architecture Consistency**: Do changes align with existing patterns?
- **Scope Creep**: Are we expanding beyond the original contract boundaries?
- **Business Value**: Do changes improve or compromise original user value?

**Question Categories (examples):**
- "This change would affect [existing user story]. Should we modify that story or create a new one?"
- "I see this conflicts with [existing implementation]. Should we plan a migration strategy?"
- "This modification increases complexity in [area]. Is the added value worth the technical cost?"
- "The original spec was focused on [goal]. How does this change serve that same goal?"
- "This would require changes to [dependent system]. Have you considered the downstream impact?"

#### Step 1.4: Modification Contract Proposal

When confident about changes, present a modification contract:

**Format:**
```
## Modification Contract

**Target Specification:** [Specification name and date]

**Proposed Changes:** [Clear description of what will be modified]

**Change Type:** [Addition/Removal/Modification/Refactor]

**Impact Assessment:**
- **Story Files Affected:** [List of specific story-N-{name}.md files that need changes]
- **New Stories Required:** [Any additional story files to be created]
- **Stories to Remove/Combine:** [Any story files that become obsolete]
- **Task Groups Affected:** [Which task groups within stories need modification]
- **Technical Components Affected:** [Code/architecture areas needing updates]  
- **Implementation Status:** [How much existing work across stories is affected]

**Migration Strategy:**
- [How to handle existing implementation]
- [Steps to preserve completed work]
- [Rollback plan if needed]

**Updated Success Criteria:** [How success metrics change]

**Revised Scope Boundaries:**
- **Still In Scope:** [What remains from original]
- **Now In Scope:** [What gets added]
- **Removed From Scope:** [What gets removed]
- **Still Out of Scope:** [Unchanged exclusions]

**⚠️ Risks & Concerns:**
- [Specific technical or business risks from the changes]
- [Potential complications or dependencies]

**💡 Recommendations:**
- [Suggestions for safer implementation approaches]
- [Ways to minimize disruption to existing work]

**Effort Estimate:** [How much additional/changed work is involved]

---
Options:
- Type 'yes' to lock this modification contract and update the specification
- Type 'edit: [your changes]' to modify the contract
- Type 'compare' to see a detailed before/after comparison
- Type 'risks' to explore implementation risks in detail
- Type 'rollback' to understand how to undo these changes later
- Ask more questions if anything needs clarification
```

### Phase 2: Specification Update (Post-Agreement Only)

**Triggered only after user confirms modification contract with 'yes'**

#### Step 2.1: Initialize Modification Tracking
```bash
# Use todo_write to track modification process
1. Backup original specification files and user-stories folder
2. Update core specification document
3. Modify affected individual story files in user-stories/
4. Update user-stories/README.md with new progress tracking
5. Create/remove/combine story files as needed
6. Update technical sub-specifications
7. Adjust task groups within stories (maintain 5-7 tasks max)
8. Create change log entry
9. Present updated package for validation
```

#### Step 2.2: Create Backup & Change Documentation

**Backup Process:**
1. **CREATE** backup folder: `.writ/specs/[spec-folder]/backups/`
2. **COPY** all current files to `backups/[timestamp]/`
3. **CREATE** change log entry in `CHANGELOG.md` within spec folder

**Change Log Format:**
```markdown
# Specification Change Log

## [Date] - [Change Type]
**Modified by:** [User identifier or "Manual edit"]
**Modification Contract:** [Brief summary]

### Changes Made:
- [Specific change 1]
- [Specific change 2]

### Files Updated:
- spec.md - [what changed]
- user-stories/README.md - [progress tracking updates]
- user-stories/story-N-{name}.md - [specific story changes]
- sub-specs/[file] - [what changed]

### Backup Location:
`backups/[timestamp]/`

---
```

#### Step 2.3: Update Core Specification Files

**spec.md Updates:**
- Modify contract summary to reflect new agreement
- Update detailed requirements based on clarification
- Revise implementation approach if changed
- Add change log reference
- Update status if appropriate

**user-stories/ folder Updates:**
- **README.md**: Update progress tracking table and story dependencies
- **Individual story files**: Modify affected story-N-{name}.md files
- **Story additions**: Create new story files with focused task groups (5-7 tasks max)
- **Story combinations**: Merge related stories if they become too granular
- **Story removals**: Archive or delete story files no longer needed
- **Task reorganization**: Ensure task groups within stories remain manageable
- **Status updates**: Mark completed tasks that might need rework across all stories

#### Step 2.4: Update Technical Sub-Specifications

**Selective Updates:**
- Only update sub-specs affected by the changes
- Create new sub-specs if new technical areas introduced
- Archive sub-specs no longer relevant
- Update cross-references between documents

#### Step 2.5: Story-Based Task Reconciliation

**Task Status Assessment Across Stories:**
- **Review each story file** for task status and relevance
- **Identify completed tasks** within stories that remain valid
- **Flag tasks requiring rework** due to changes
- **Add new tasks** while maintaining 5-7 task limit per story
- **Split stories** if task count would exceed 7 tasks
- **Combine stories** if task counts become too small
- **Reorder stories** if dependencies changed

**Story-Level Task Annotations:**
```markdown
# In story-1-user-auth.md:
- [x] 1.1 Write tests for user authentication ✅ (Still valid)
- [ ] 1.2 Implement OAuth provider ⚠️ (Needs modification)
- [ ] 1.3 Create social login UI 🆕 (New task from scope change)
- [~~] 1.4 Implement mobile-specific auth ❌ (Moved to new story-4-mobile-auth.md)

# New story-4-mobile-auth.md created if mobile auth becomes separate feature
```

**Story Management:**
- **Split large stories**: If modifications would create >7 tasks, create additional story files
- **Archive obsolete stories**: Move removed stories to archived/ subfolder with timestamp
- **Update story dependencies**: Modify README.md to reflect new story relationships
- **Maintain story cohesion**: Ensure each story delivers standalone user value

#### Step 2.6: Final Update Review & Validation

Present updated package with change summary:
```
✅ Specification successfully updated!

📁 .writ/specs/[DATE]-feature-name/
├── 📋 spec.md - ⭐ Updated specification
├── 📝 spec-lite.md - ⭐ Updated AI context summary  
├── 👥 user-stories/ - ⭐ Updated story organization
│   ├── 📊 README.md - ⭐ Updated progress tracking and dependencies
│   ├── 📝 story-1-{name}.md - ⭐ Modified stories (5-7 tasks each)
│   ├── 📝 story-2-{name}.md - 🆕 New stories or combinations
│   ├── 📂 archived/ - 🗃️ Obsolete stories (if any)
│   └── 📝 story-N-{name}.md - ⭐ Focused task groups
├── 📂 sub-specs/
│   ├── 🔧 technical-spec.md - ⭐ Updated if affected
│   └── [other sub-specs...]
├── 💾 backups/[timestamp]/ - Original files and stories preserved
└── 📝 CHANGELOG.md - ⭐ Change documentation

## Summary of Changes:
- **Stories Modified:** [X] existing story files updated
- **Stories Added:** [Y] new story files created
- **Stories Removed/Archived:** [Z] story files no longer needed
- **Task Groups Affected:** [N] task groups reorganized
- **Modified Components:** [List of changed technical components]

## Impact on Implementation:
- **Stories Still Valid:** [X] out of [Y] stories remain unchanged  
- **Stories Requiring Rework:** [N] stories need modification
- **New Stories Added:** [N] new stories created (with focused task groups)
- **Stories Archived:** [N] stories no longer needed
- **Total Tasks:** [N] tasks across all stories (max 5-7 per story)

Please review the updated specification:
- Does this accurately reflect the agreed modifications?
- Are the user stories appropriately organized (5-7 tasks per story)?
- Should any stories be further split or combined?
- Are story dependencies correctly updated in the README?
- Should any additional changes be made?

The updated user-stories folder structure provides:
- **Focused development**: Work on one story at a time
- **Better organization**: Each story file is manageable and self-contained
- **Team collaboration**: Different stories can be assigned to different developers
- **Clear progress tracking**: README overview shows status across all stories
- **Flexible workflow**: Stories can be completed independently where possible

The original version is safely backed up in the backups folder. If you need to rollback any changes, I can help restore from backup.
```

## Key Features

### 1. Safe Modification Process
- **Backup creation** before any changes
- **Change tracking** with detailed logs
- **Rollback capability** to restore previous versions
- **Impact assessment** before making changes

### 2. Precise Change Control
- **Focused clarification** about specific modifications
- **Risk assessment** for breaking changes
- **Migration strategy** for existing implementation
- **Selective updates** only to affected components

### 3. Implementation Continuity
- **Task status preservation** for completed work
- **Clear annotation** of what needs rework
- **Priority reassessment** based on changes
- **Timeline impact** analysis

### 4. Change Documentation
- **Detailed change logs** for audit trail
- **Before/after comparison** capability
- **Modification rationale** capture
- **Rollback instructions** for safety

## Example Usage Flow

```
Developer: /edit-spec "user-auth" "add biometric authentication"

Agent: I found your user authentication specification from 2024-01-15. Let me load the current state...

[Loads spec.md, tasks.md, and sub-specs]

Current specification includes email/password auth with OAuth social login. I see there are 8 user stories, with 3 already implemented in your codebase.

I have a concern about adding biometric authentication: your current implementation is web-focused, but biometric auth typically requires native mobile or desktop apps. I see no mobile components in your existing specification.

First question: Are you planning to add mobile app development to this specification, or do you want to use WebAuthn for browser-based biometric authentication?

Developer: WebAuthn for browser-based

Agent: That makes more sense with your existing web architecture. However, WebAuthn requires HTTPS and has limited browser support. I see your current implementation supports users who may be on older browsers.

Should we make biometric authentication an optional enhancement for supported browsers, or do you want to require it for all users (which might break compatibility)?

Developer: Optional enhancement for supported browsers

Agent: [Continues with more questions about UX, fallback behavior, etc.]

## Modification Contract

**Target Specification:** User Authentication System (2024-01-15)

**Proposed Changes:** Add WebAuthn biometric authentication as optional enhancement

**Change Type:** Addition (with graceful degradation)

**Impact Assessment:**
- **User Stories Affected:** Story 2 (Login flow) needs biometric option
- **Technical Components Affected:** Frontend auth component, browser capability detection
- **Implementation Status:** 3/8 stories completed, none affected by this change

**Migration Strategy:**
- Existing auth flows remain unchanged
- Add biometric as progressive enhancement
- No breaking changes to current implementation

**Updated Success Criteria:** Users can log in with biometrics on supported browsers, fallback to existing methods

**⚠️ Risks & Concerns:**
- Browser support varies (Chrome 67+, Firefox 60+, Safari 14+)
- Requires HTTPS in production
- UX complexity for unsupported browsers

**💡 Recommendations:**
- Feature detection before offering biometric option
- Clear messaging when biometric unavailable
- Analytics to track adoption rates

**Effort Estimate:** ~2-3 additional days (1 story addition, modest technical complexity)

---
Options: [yes/edit/compare/risks/rollback]

Developer: yes

Agent: ✅ Modification contract locked! Updating specification...

[Updates files, creates backups, documents changes]
```

This approach ensures that specification modifications are as careful and controlled as the original creation process, while preserving existing work and providing safety mechanisms for complex changes.
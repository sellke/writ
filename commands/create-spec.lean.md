---
name: create-spec-lean
description: "Lean variant of /create-spec for WRIT_HARNESS_LEAN=1 baseline runs. Generate a full feature specification contract-first - discovery conversation, then user stories, sub-specs, and acceptance criteria. The entry point for any feature large enough to need a spec."
problem: "Implementation starts from a feature idea nobody wrote down, so scope, story boundaries, and acceptance criteria get invented mid-build and argued about afterwards."
outcome: "A new .writ/specs/<date>-<name>/ package exists — spec, spec-lite, per-story files, and sub-specs — matching a contract the user locked before any file was written."
entry_level: high
exit_criteria:
  - "spec.md carries a Status line and a Dependencies line listing exact spec-folder IDs, or [] when there are none"
  - "every user-stories/story-*.md file has 3-5 Given/When/Then acceptance criteria and no more than 7 implementation tasks"
  - "spec-lite.md is under 100 lines"
---

# Create Spec Command (create-spec, lean)

## Overview

Contract-first: developer and AI agree on a contract before any supporting file is created. Discovery runs in Plan Mode; bounded decisions use AskQuestion.

## Required Artifacts

Verify per the preamble's **Artifact Integrity** rule before starting.

- **Required:** none — `/create-spec` bootstraps a spec from scratch.
- **Optional:** `.writ/product/` docs (inform discovery), `.writ/context.md`.

## Invocation

- `/create-spec` — discover and create a full contract-first spec package
- `/create-spec --from-prototype` — formalize recent prototype work into a spec with Story 1 already complete
- `/create-spec --from-issue <path>` — promote a `.writ/issues/` issue or Goal Card into a spec, pre-populating discovery from it (see § `--from-issue` Mode)
- `/create-spec --recommend [idea]` — autonomously author and lock a complete spec package from evidence, then stop (does not implement)

## Recommended Mode (`--recommend`)

Parse `--recommend` exactly once at command entry. Store `recommend_mode` and
choose one branch before discovery or file creation.

**Normal branch (authoritative): when `--recommend` is absent, follow every
existing phase, prompt, terminal constraint, and next-step behavior below
verbatim.**

`--recommend` makes spec authoring autonomous: the command still runs
contract-first discovery, but it auto-adopts the evidence-backed contract and
its planning choices instead of stopping at each routine gate, and records the
rationale. It is invokable standalone and is also the mode
`/implement-phase --recommend` passes down when it authors missing specs.

**Terminal scope:** `--recommend` produces a locked, validated spec package and
**stops**. It never triggers `/implement-spec` or any implementation. Autonomous
implementation across a phase belongs to `/implement-phase --recommend`, which
calls `/implement-spec` per spec after the packages exist.

### Authoritative `--recommend` Invocation Matrix

Validate the complete invocation before creating files, updating an issue, or
launching discovery:

| Invocation | Result |
|---|---|
| `/create-spec --recommend [one-idea]` | Supported; source mode `standard` |
| `/create-spec --recommend --from-issue <one-path>` | Supported; source mode `from-issue` |
| `/create-spec --recommend --from-prototype` | Supported; source mode `from-prototype` |
| `/create-spec --recommend` with no idea | Supported only when exactly one unambiguous feature candidate resolves from context; otherwise pause with a bounded selection before discovery |
| `/create-spec --recommend --quick` | Reject: full spec package generation is mandatory |
| `/create-spec --recommend --force` | Reject: recommended authoring never overwrites ownership or completion evidence |
| `--recommend` with multiple source modes | Reject: select exactly one of standard, `--from-issue`, or `--from-prototype` |
| `--recommend` with multiple issue paths or multiple free-form source arguments | Reject: one invocation authors exactly one spec |

On rejection, print the supported forms above and stop before mutation.

### Autonomous Authoring Boundary

`--recommend` overrides the routine human gates of Phase 1 — not the
accountability floor (see [ADR-013](../.writ/decision-records/adr-013-recommended-autonomous-delivery.md)):

- **Auto-adopt** — record each material decision in `{spec}/recommendation-log.md`
  (decision, evidence, material alternatives, risk/reversibility, result; never
  private chain-of-thought or transcript content):
  - *Feature selection (Step 1.0):* use the provided `[idea]`; with no idea and
    exactly one unambiguous candidate from context, adopt it, otherwise pause.
  - *Contract lock (Step 1.4b):* auto-lock the evidence-backed contract. Do
    **not** present the lock/edit/risks/blueprint/questions choice. The lock is
    justified by discovery and codebase evidence and recorded. Silence is not
    justification.
  - *Story decomposition and sub-spec set:* choose from contract scope and
    codebase evidence (technical-spec always; database/api/ui sub-specs when the
    data-flow/UI heuristics apply).
  - *Visual references (Step 1.5):* auto-resolve without prompting — default to
    `none`, or `generate` when the spec is UI-bearing and no assets were supplied.
  - *Source pre-population:* `--from-issue`/`--from-prototype` context is adopted
    without re-litigating the shortened-discovery offers.
- **Pause (bounded question or actionable blocker):** no idea and no single
  unambiguous candidate; conflicting or technically infeasible requirements
  (core-contract ambiguity, not the lock itself); a cross-spec overlap that is
  a blocking conflict rather than an advisory note.

After the contract is auto-locked, run the ordinary Phase 2 generation steps and,
before finishing, write `{spec}/recommendation-log.md` capturing the autonomous
decisions above. When invoked with `--from-issue`, the ordinary `spec_ref`
writeback still applies. Then stop — the locked, validated package is the
deliverable.

## Command Process

### `--from-prototype` Mode

**Invocation:** `/create-spec --from-prototype`. Formalizes `/prototype` work (typically after scope-escalation signals) as Story 1, already complete, and plans Story 2+. **Replaces Phase 1 with a prototype-anchored flow:**

#### Step 0: Read Prototype Context

1. **Read the current git diff** — `git diff HEAD` (or `git diff --cached` if staged): files changed, lines added/removed, new dependencies.
2. **Read the coding agent implementation summary** from the conversation if available.
3. **Build a pre-populated contract draft:** Deliverable (from diff + summary), Files in Scope (every file created or modified), Implementation Approach (summary, else diff analysis), and `Story 1: [Prototype: description of what was built] — Status: Completed ✅`.

If no git diff exists (clean working tree), warn: *"No changes detected in working tree. `--from-prototype` requires an uncommitted or staged diff to read context from."* and offer: proceed with manual description, or cancel.

#### Step 1: Shortened Discovery Conversation (Plan Mode)

Switch to Plan Mode. The prototype is done; do not re-litigate what was built. Open with: *"The prototype built [summary from diff]. Story 1 is already complete. What should Story 2+ accomplish?"* Cover the gap to shippable, what Story 2 unlocks, skipped error/edge/production concerns, and integration points to productionize. Skip what the diff already answers. Expect 3–5 exchanges.

#### Step 2: Contract Proposal (Plan Mode)

Build on the Step 0 draft plus discovery answers; present in Plan Mode. The contract covers what is built (Story 1) and what comes next:

```
## Specification Contract

**Deliverable:** [inferred from diff + discovery]
**Origin:** Formalized from prototype (Story 1 already complete)

**Story 1 (Complete):** [description of prototype work — what was built]
**Story 2+:** [what the discovery conversation revealed comes next]

**Files in Scope:** [from git diff — already in the codebase]

[standard contract sections: Constraints, Success Criteria, Scope Boundaries]
```

#### Step 3: Phase 2 with Story 1 Pre-Marked Complete

When the user locks the contract, run Phase 2 with one change: **Story 1** is generated with `Status: Completed ✅` (never Not Started — the work exists and `/implement-spec` must not re-implement it), describes the prototype work, files touched, and that it was done via `/prototype`, and has every Implementation Task (`- [x] [task]`) and Definition of Done item checked. All later stories start at `Status: Not Started`. `user-stories/README.md` progress shows Story 1 complete.

---

### `--from-issue` Mode

**Invocation:** `/create-spec --from-issue [path]`. Promotes an issue or Goal Card under `.writ/issues/` into a spec. **Replaces Phase 1 with an issue-anchored flow:**

#### Step 0: Read Issue Context

1. **Validate the path** — the file must exist under `.writ/issues/{bugs,features,improvements,goals}/`. Otherwise:
   ```
   ⚠️ Issue file not found: [path]
   Expected under .writ/issues/{bugs,features,improvements,goals}/YYYY-MM-DD-{slug}.md
   Provide a valid path or cancel.
   ```
   Do not modify the issue file on error.

2. **Parse the issue file** — `Type` (`**Type:**`), `Priority` (`**Priority:**`), `Effort` (`**Effort:**`), and the `TL;DR`, `Current State`, `Expected Outcome`, and `Relevant Files` sections.

   **Goal Cards** (`**Type:** Goal`, written by `/create-goal`): if the header reads `**loop:** no`, stop with `⚠️ This Goal Card is marked loop: no; use its SINGLE PROMPT section instead.` and leave the file unchanged. Otherwise map OBJECTIVE → Deliverable, OUTPUT and CONTEXT → Files in Scope, DONE WHEN lines → Success Criteria verbatim, STAGES → story seed, STOP-CAPS → the spec's `loop` block, QUALITY and CONSTRAINTS → Constraints.

3. **Build a pre-populated contract draft:** Deliverable (from TL;DR and type), `Origin: Promoted from issue: [path]`, Files in Scope (Relevant Files), and Priority / Effort signals.

#### Step 1: Shortened Discovery Conversation (Plan Mode)

Switch to Plan Mode. Do not re-ask what the issue documents; shape the solution into stories. Open with: *"This issue captures [TL;DR from issue]. What does the fix/feature need to accomplish beyond what the issue describes?"* Cover story decomposition, uncaptured edge cases and error states, confirming acceptance criteria, unmentioned integration points, and omitted constraints. Expect 2–4 exchanges.

#### Step 2: Contract Proposal (Plan Mode)

Build on the Step 0 draft plus discovery answers; present for review:

```
## Specification Contract

**Deliverable:** [inferred from issue + discovery]
**Origin:** Promoted from issue: [path]

**Stories:** [decomposition revealed by discovery]

**Files in Scope:** [from issue Relevant Files + discovery additions]

[standard contract sections: Constraints, Success Criteria, Scope Boundaries]
```

#### Step 3: Phase 2 with `spec_ref` Writeback

When the user locks the contract, run Phase 2. **After `spec.md` is written**, update the source issue: replace its `spec_ref:` line (which reads `_(set automatically when promoted via ...)_`) with

```
> **spec_ref:** .writ/specs/[date]-[name]/spec.md
```

Only that line changes; the issue is never deleted or archived. **If the spec_ref line is absent** (an older issue), append it to the frontmatter block instead of failing.

---

### Phase 1: Contract Establishment (No File Creation)

**Mission:** turn the rough feature idea into a clear work specification, and deliver the spec package only after both sides agree on the requirements contract. Challenge ideas that don't make technical or business sense; surface concerns early.

#### Step 1.0: Feature Selection (if not provided)

**If the user didn't specify a feature idea, use AskQuestion immediately:**

```
AskQuestion({
  title: "Feature Specification - What would you like to build?",
  questions: [
    {
      id: "feature_idea",
      prompt: "What feature would you like to create a specification for?",
      options: [
        // Dynamically generate options based on codebase scan
        { id: "option_1", label: "[Feature suggestion based on codebase gaps]" },
        { id: "option_2", label: "[Another relevant feature suggestion]" },
        { id: "option_3", label: "[Third suggestion from TODO/roadmap]" },
        { id: "other", label: "Something else (I'll describe it)" }
      ]
    }
  ]
})
```

On "Something else", follow up with a free-text question.

#### Step 1.1: Initial Context Scan

Scan `.writ/specs/` for related specifications, analyze codebase architecture and patterns, and load `.writ/docs/tech-stack.md` and `.writ/docs/code-style.md` (written by `/initialize`; skip any that are absent). **Output:** a context summary; no files created.

#### Step 1.3: Discovery Conversation (Plan Mode)

After the context scan, run discovery in Plan Mode; the user controls when to switch. Before speaking, list what is missing across four areas:

- **Experience:** entry point, happy path, key interaction moments, feedback/confirmation, error/empty/loading states, responsive behavior
- **Business rules:** permissions and access control, validation rules and limits, state transitions and lifecycle, time-based rules, pricing/billing, domain edge cases, compliance
- **Technical:** integration points, performance, security, data persistence
- **Scope:** success criteria, in/out boundaries, implementation approach, timeline

**Conversation rules:** one focused question at a time, on the highest-impact unknown; re-scan the codebase after answers when relevant; continue until 95% confidence on the deliverable; **never declare "final question"**; let the user signal readiness for a contract. Explore experience first, then rules, then technical constraints.

**Critical analysis:** say so when requirements are infeasible with the current architecture (with alternatives), when scope is several features (recommend splitting), when requests conflict with codebase patterns, when business logic does not match stated user value, and when performance/security/scalability concerns arise. Ask about error/empty/loading experience if it has not come up; probe vague rules ("admins can do it") for who, under what conditions, and exceptions; suggest smoother paths when a flow has unnecessary friction.

When confidence is high, present the contract (still in Plan Mode) and leave room for more questions.

#### Step 1.3b: Cross-Spec Overlap Check (Automatic)

Before presenting the contract, scan for conflicts with in-progress specifications:

1. **List spec folders** with the single-level glob `.writ/specs/*/spec.md` (this excludes `.writ/specs/archive/**`; see `.writ/docs/spec-lifecycle.md`).
2. **Filter out completed specs** with the format-tolerant complete-family check (`python3 scripts/spec-status.py is-complete --file <path>`, or equivalent logic): bold or unbold `Status:` label; `Complete`, `Completed ✅`, or `Closed — Abandoned` are complete-family; trailing parenthetical/emoji text ignored. **Do not** match only the literal substring `Status: Complete` — it never matches the bold form `> **Status:** Complete`. A spec with no status header resolves not-complete (never skipped).
3. **Read each remaining `spec-lite.md`.**
4. **Extract domain keywords** from the new contract: models/entities, routes/endpoints, shared utilities, domain terms, files to be modified.
5. **Compare** for keyword overlap in the same domain areas.
6. **Overlap** → add a `⚠️ Cross-Spec Overlap` section to the contract. **None** → proceed silently.

Keyword matching, not semantic analysis; false positives are acceptable (the user can dismiss).

#### Step 1.4: Contract Proposal (Still in Plan Mode)

```
## Specification Contract

**Deliverable:** [One clear sentence describing what will be built]

**Must Include:** [Critical requirement that makes this valuable]

**Hardest Constraint:** [Biggest technical/business limitation to overcome]

**🎯 Experience Design:**
- **Entry point:** [How the user reaches this feature]
- **Happy path:** [The ideal flow in 2-3 steps]
- **Moment of truth:** [The instant the user gets the value]
- **Feedback model:** [How the user knows it worked — toast, redirect, animation, etc.]
- **Error experience:** [What failure looks like to the user — not the system]

**📋 Business Rules:**
- [Key rule 1 — e.g., "Only workspace admins can invite members"]
- [Key rule 2 — e.g., "Free tier limited to 3 projects"]
- [Edge cases or domain-specific constraints discovered during conversation]

**Success Criteria:** [How we'll know it's working correctly]

**Scope Boundaries:**
- Included: [2-3 key features]
- Excluded: [2-3 things we won't build]

**⚠️ Technical Concerns (if any):**
- [Specific concern about feasibility, performance, or architecture]
- [Suggested alternative or mitigation approach]

**💡 Recommendations:**
- [Suggestions for improving the approach based on codebase analysis]
- [Ways to reduce risk or complexity]

**⚠️ Cross-Spec Overlap (if detected):**
- [Spec name] ([status]) also touches [domain area] — [specific overlap details]
- Consider: sequencing these specs, declaring a dependency, or coordinating the shared area
```

Discuss refinements in Plan Mode. When the user approves and switches back to Agent Mode, confirm with AskQuestion.

#### Step 1.4b: Contract Decision (Agent Mode)

```
AskQuestion({
  title: "Contract Decision",
  questions: [
    {
      id: "contract_action",
      prompt: "How would you like to proceed with this contract?",
      options: [
        { id: "yes", label: "Lock contract and create spec package" },
        { id: "edit", label: "Edit the contract (I'll specify changes)" },
        { id: "risks", label: "Explore potential implementation risks first" },
        { id: "blueprint", label: "See the planned folder structure and documents" },
        { id: "questions", label: "I have more questions before deciding" }
      ]
    }
  ]
})
```

- **yes**: Proceed to Phase 2 (Spec Package Creation)
- **edit**: Ask free-text: "What changes would you like to make to the contract?"
- **risks**: Present detailed risk analysis, then re-present the contract with AskQuestion
- **blueprint**: Show planned folder structure, then re-present the contract with AskQuestion
- **questions**: Switch back to Plan Mode and return to discovery

#### Step 1.5: Visual References (Optional)

**After contract lock, before creating files**, if the spec involves any user-facing UI, ask:

```
AskQuestion({
  title: "Visual References",
  questions: [
    {
      id: "visuals",
      prompt: "Do you have any visual references for this feature?",
      options: [
        { id: "screenshots", label: "I have screenshots or mockups to share" },
        { id: "sketch", label: "I have an Excalidraw sketch" },
        { id: "generate", label: "Generate wireframes from the spec" },
        { id: "existing", label: "Match existing app patterns (capture current UI)" },
        { id: "none", label: "No visual references — text spec is enough" }
      ]
    }
  ]
})
```

- **screenshots**: Accept image uploads/paths. Store in `mockups/`. Extract layout structure, components, and design patterns. Generate `mockups/README.md` and `mockups/component-inventory.md`.
- **sketch**: Accept `.excalidraw` file. Store in `mockups/`. Parse JSON to extract component names and layout.
- **generate**: After creating `spec.md`, generate Excalidraw wireframes for each screen/view in the spec. Store in `mockups/`. Follow `/design` wireframe conventions.
- **existing**: Capture screenshots of the current app at relevant routes into `mockups/current/` (the "before" state).
- **none**: Create empty `mockups/` directory. Skip visual references in story files.

**When mockups are provided or generated:** add a `## Visual References` section to each relevant story file linking its mockups; generate `mockups/component-inventory.md` (components, states, owning stories); reference design tokens from `.writ/docs/design-system.md` if it exists, otherwise extract one from the mockups.

### Phase 2: Spec Package Creation (Post-Agreement Only)

**Triggered only after the user confirms the contract with 'yes'.**

#### Step 2.2: Determine Current Date

Use `npx @sellke/writ date` when available; otherwise the local system date in `YYYY-MM-DD`. Folder: `.writ/specs/[DATE]-[feature-name]/`.

Resolve the spec owner from git config before writing `spec.md`:

```bash
OWNER="@$(git config user.name 2>/dev/null | tr -d ' ' || echo 'unknown')"
if [ "$OWNER" = "@" ]; then
  OWNER="@unknown"
  echo "⚠️ No git user.name configured; writing owner: @unknown. Set it with: git config user.name 'Your Name'"
fi
```

Prefix `@`, strip spaces, and consult no external user directory. Unset or empty `git config user.name` → `owner: @unknown` with the warning above.

#### Step 2.3: Create Directory Structure

```
.writ/specs/[DATE]-{feature-name}/
├── spec.md
├── spec-lite.md
├── mockups/
├── user-stories/
│   ├── README.md
│   ├── story-1-{name}.md
│   └── story-N-{name}.md
└── sub-specs/
    └── technical-spec.md (+ database-schema.md, api-spec.md, ui-wireframes.md as needed)
```

#### Step 2.4: Generate Core Documents

**spec.md** — built from the locked contract. Must contain:

- **Frontmatter:**
  ```markdown
  > **Status:** Not Started
  > **Created:** [DATE]
  > **Owner:** [OWNER]
  > **Dependencies:** [spec-folder-id, ...]
  ```
  - Emit `> **Dependencies:**` for **every** new spec — never omit it. Use `[]` when there is no cross-spec dependency.
  - Values are **exact spec-folder IDs** under `.writ/specs/` (e.g. `2026-07-09-autonomy-ceiling`), in declared order. Titles and fuzzy matches are invalid.
  - This spec-level header is distinct from story-level `Dependencies:` metadata. Do not conflate the two graphs.
  - **Canonical complete-family spelling (forward-only):** a spec later marked done reads `> **Status:** Complete` — bold, unadorned. This is the only complete spelling `create-spec` writes. `scripts/spec-status.py` stays tolerant of legacy spellings (`Completed ✅`, unbold `Status: Complete`, `Closed — Abandoned`). Non-complete values (`Not Started`, `In Progress`, etc.) are unchanged.
  - **Supersession banners:** if the locked contract says this spec replaces or builds on prior spec work, add `> **Amends:**` (replaces/supersedes) or `> **Extends:**` (builds on) as a markdown link — link text the prior spec's folder name, target its relative `spec.md` path (e.g. `Amends:` → `2026-07-11-leanness-guardian` → `../2026-07-11-leanness-guardian/spec.md`). Step 2.4b writes the reverse pointer; convention in [`.writ/docs/spec-lifecycle.md`](../.writ/docs/spec-lifecycle.md#supersession-banners).
- **Contract summary** — the locked contract verbatim
- **Experience design** — the 🎯 section expanded: user journey, state catalog (empty/loading/populated/error/edge), interaction patterns, responsive behavior
- **Business rules** — the 📋 section expanded: permissions, validation, state transitions, domain edge cases, compliance
- **Detailed requirements** — from clarification responses
- **Implementation approach** — technical strategy based on codebase analysis

#### Step 2.4b: Supersession Write-back (`Amends:`/`Extends:`)

If the new spec's header has an `> **Amends:**` or `> **Extends:**` line, write a matching reverse pointer onto each referenced spec — in the standard flow, `--from-issue`, and `--from-prototype` alike. Use the reference implementation, not hand edits:

```bash
python3 scripts/supersession-writeback.py apply --new-spec-file .writ/specs/[date]-[name]/spec.md
```

It parses every link target on the line (there may be several, e.g. a spec **and** an ADR), resolves each against the new spec's folder, and writes or updates a `Superseded by:` line (link text the new folder name, target its relative `spec.md`) in each resolvable target's header, never duplicating it and leaving every other line — including the target's `> **Status:**` — untouched. Non-spec targets (e.g. an ADR) are reported under `skipped_other`; broken paths or missing targets under `broken`. **This step never blocks or fails spec package creation** — proceed to Step 2.5 regardless and surface any `broken` entries as an informational note.

**spec-lite.md** — condensed version for AI context with agent-specific sections. **Hard limit: under 100 lines.** Format:

```markdown
# [Feature Name] (Lite)

> Source: .writ/specs/[DATE]-[name]/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

[35 lines max]

**Deliverable:** [One-sentence summary]

**Implementation Approach:**
- [Key technical decisions, architecture patterns, integration strategy]

**Files in Scope:**
- `path/to/file.ext` — [what changes here]

**Error Handling:**
- [Error case] → [planned handling]

**Integration Points:**
- [Command/agent interactions]

**Line Budget Constraints:** [if relevant to this spec]

---

## For Review Agents

[35 lines max]

**Acceptance Criteria:**
1. [Measurable criterion with target]
2. [Business rule verification]
3. [Integration success condition]

**Business Rules:**
- [Permission/access control, validation, state transitions, domain edge cases]

**Experience Design:**
- Entry: [How user reaches this]
- Happy path: [Ideal flow]
- Moment of truth: [Value realization point]
- Feedback: [Success confirmation]
- Error: [Failure experience]

**[Domain-Specific Section if applicable]:**
- Error & Rescue Map structure
- Shadow Paths format
- Drift Analysis thresholds

---

## For Testing Agents

[30 lines max]

**Success Criteria:**
1. [Quantifiable metric with threshold]
2. [Coverage requirement]
3. [Performance/quality target]

**Shadow Paths to Verify:**
- **Happy path:** [Normal flow outcome]
- **Nil input:** [Missing data handling]
- **Empty input:** [Zero-state handling]
- **Upstream error:** [External failure handling]

**Edge Cases:**
- [Feature-specific edge case] → [expected behavior]

**Coverage Requirements:**
- New code: ≥80%
- Critical paths: 100%
- Error paths: 100%

**Test Strategy:**
- [Test types needed and key scenarios]
```

The "For Review Agents" acceptance-criteria bullets are written **untagged** here: story-level `AC-N.M` IDs do not exist until Step 2.6. Step 2.6b adds the tags.

Emphasis by feature type: data flow (APIs, auth, payments, integrations) → error handling, shadow paths, business rules; UI → experience design, interaction edge cases, responsive behavior; refactors → affected files, integration points, backward compatibility; docs/tooling → success criteria, verification approach.

**Line budget:** sections target 35/35/30 content lines; header and dividers take ~15, so the file stays under 100. When over, cut nice-to-haves first, keep error maps, business rules, and acceptance criteria, point to `spec.md` sections instead of duplicating, and reduce all three sections proportionally. Do not convert older single-block spec-lites unless asked.

#### Step 2.5: Plan User Stories

Break the contract into user stories that each deliver standalone value, identify dependencies between them, and keep each to 5-7 implementation tasks max. Output the plan:

```
Story Plan:
1. story-1-{name}: [Description] - Dependencies: None
2. story-2-{name}: [Description] - Dependencies: Story 1
```

#### Step 2.6: Generate User Stories in Parallel

Launch parallel Task subagents to create all story files. Agent spec and prompt template: `agents/user-story-generator.md`.

For each story, spawn a Task subagent (`generalPurpose`, at the `floor` tier resolved per the platform adapter — the tier `agents/user-story-generator.md` declares) in a single message. Provide: output path, story number, title, description, dependencies, priority, the locked contract, relevant codebase patterns, and full specification content for context hint generation:
- `spec_content` — full text of `spec.md`
- `technical_spec_content` — full text of `technical-spec.md` if it exists; otherwise `""`, and add to the prompt: "Technical spec not yet generated — scope hints to spec.md sections only (e.g., 'spec.md → ## 🎯 Experience Design → ### Error Experience')." (Step 2.8 may still be running in parallel.)

Each story file contains: status/priority/dependencies metadata, user story (As a / I want / So that), 3-5 acceptance criteria in Given/When/Then, 5-7 implementation tasks (tests first, verification last), technical notes, definition of done, and a `## Context for Agents` section with targeted hints to relevant error map rows, shadow paths, business rules, and experience elements.

**Criterion ID grammar (required):** every story carries the `> **AC IDs assigned through:** AC-N.M` marker directly beneath `## Acceptance Criteria`, a trailing `` `[AC-N.M]` `` tag on every criterion line, and a trailing `` `[AC-N.M, ...]` `` tag on every implementation task line citing the criterion IDs it satisfies. The literal template lives in `agents/user-story-generator.md`; the full grammar in `.writ/docs/acceptance-criteria-ids.md`.

Launch up to 4 subagents simultaneously; batch beyond that.

#### Step 2.6a: Validate Generated Stories

After **all** generators return, and before Step 2.6b:

1. Run `python3 scripts/ac-trace.py check --spec .writ/specs/{spec-folder} --repo .writ/specs/{spec-folder}` once; attribute each finding to its `story=`. `--repo` is the spec folder (no story is Completed yet, and a repo-wide scan would misattribute other specs' `dangling_reference`s); `/verify-spec` keeps `--repo .`.
2. Per file: 3–5 criteria (count `- [ ] Given` lines only), each ending in a `` `[AC-N.M]` `` tag; `> **AC IDs assigned through:**` equal to the highest criterion ID; 5–7 tasks (count `- [ ] N.M` lines only), each citing ≥1 ID; `**Status:** Not Started`.
3. For each **failing** story: spawn one regeneration with the identical prompt at `anchor` (`model` = platform `inherit`), overwrite the floor file with the anchor result whether or not it passes, re-check once. A second failure surfaces in Step 2.9. A passing story is never regenerated.
4. Per regeneration emit `(no-op until ADR-025 Story 1) escalated(agent=user-story-generator, site=create-spec.2.6, origin=<model>/<effort>@<platform>)` — origin is the one captured at command entry (`system-instructions.md` § Model Tiers); `origin=unknown/unknown@<platform>` is valid. The line is printed only; no recorder consumes it yet.

Escalation fires only on a *returned* file that fails the check — a Task error, timeout, or absent file follows the normal error path. The floor attempt and its anchor re-run count as one attempt; there is no second regeneration. This command declares no loop bound; the single re-run is the whole budget.

#### Step 2.6b: Tag spec-lite.md Review Criteria with IDs

1. Read every generated story's `## Acceptance Criteria`.
2. Match each bullet under `spec-lite.md` → `## For Review Agents` → `**Acceptance Criteria:**` by content to the story criterion (or criteria) it condenses.
3. Append the matching `` `[AC-N.M]` `` tag (comma-separated inside one tag for several) to the end of that bullet.
4. Change nothing else in `spec-lite.md`; only trailing tags are appended, so the <100-line budget holds.

If a bullet cannot be confidently matched, leave it untagged and note the gap in Step 2.9. Do not guess.

#### Step 2.6c: Spec analysis (advisory)

After Step 2.6a, run one analysis pass — **once** per `/create-spec`, no loop. It does not replace 2.6a (`ac-trace.py`).

1. **LLM pass (orchestrator, not the script).** Read the generated acceptance criteria and look for contradiction, gap, and ambiguity, grounded in exit-criteria grammar (observable, named outcomes). Write a JSON array of `{code, story, summary, ac_ids?}` objects (`code` is `contradiction`, `gap`, or `ambiguity`) to a per-run path under `.writ/state/`; write `[]` if you cannot judge. Do not add an API key to `scripts/spec-analyze.py`, create an agent file, or change how `/implement-story` spawns agents. If you skip the pass, omit `--findings` below.
2. **Verify the claim, don't trust it.**

```bash
python3 scripts/spec-analyze.py check --spec .writ/specs/<folder> [--findings .writ/state/spec-analyze-<run>.json]
```

3. **Surface as notes only.** Carry the verdict line and every `reason:` into Step 2.9 as notes (`add_note`). Use `add_finding` only when the helper is missing or exits 2. A script `fail` (including `malformed_findings`) or `unverifiable` does **not** fail package creation, does **not** mark the spec `DEGRADED`, and does **not** open an AskQuestion gate.

#### Step 2.7: Create User Stories README

After all subagents complete, create `user-stories/README.md`: stories summary table (status, task counts, progress), dependency descriptions, and links to each story file.

#### Step 2.8: Generate Technical Sub-Specs

May run in parallel with story generation. Create only the sub-specs the contract requires: `technical-spec.md` (always), plus `database-schema.md`, `api-spec.md`, `ui-wireframes.md` as needed, each referencing its user stories.

**Error Mapping (Required for Data Flow Features):** include when the spec touches API routes, auth flows, payments, file operations, or external integrations; skip for pure UI/CSS, docs, config, or internal refactors; when in doubt, include it. `Read skills/error-rescue-mapping/SKILL.md` for how to build the Error & Rescue Map, Shadow Paths, and Interaction Edge Case tables and the `[UNPLANNED]` → `[OUT OF SCOPE — reason]` resolution discipline.

#### Step 2.9: Final Package Review

Present the package: file tree, story count and total task count, items for the user to review (accuracy, story sizing, missing requirements), and suggested next steps. If Step 2.6c ran, include its `spec-analyze.py` verdict and `reason:` lines as **notes**; they never fail this review or block the package.

## Completion

This command succeeds when all of:

1. **Contract was locked** — the user explicitly approved the specification contract
2. **Spec package exists** — `spec.md`, `spec-lite.md`, all story files, and `user-stories/README.md` are written
3. **Stories are actionable** — each story has 3-5 acceptance criteria (Given/When/Then) and 5-7 implementation tasks
4. **Sub-specs generated** — `technical-spec.md` and any additional sub-specs the contract requires exist in `sub-specs/`
5. **Package reviewed** — the final package summary was presented to the user

If `--from-prototype`: Story 1 is marked `Completed ✅` with all tasks checked. If `--from-issue`: the source issue file's `spec_ref` line is updated with the spec path.

**Suggested next step:** `/implement-spec` to execute the full implementation pipeline, or `/implement-story` for individual stories.

**Production boundary:** this command writes the spec package, the `--from-issue` `spec_ref` line in the source issue, and the Step 2.4b `Superseded by:` reverse pointers, plus ephemeral `.writ/state/` files, nothing else. Do not commit, merge, open a PR, release, tag, or publish.

**Terminal constraint:** This command produces specification artifacts (`.writ/specs/{date}-{name}/`). Do not offer to implement, build, or execute what was specified. For implementation, the user should run `/implement-spec` or `/implement-story`. For quick prototyping, use `/prototype`.

---

## References

- Standing instructions: [`commands/_preamble.lean.md`](_preamble.lean.md) (the `WRIT_HARNESS_LEAN=1` sibling of `commands/_preamble.md`)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)

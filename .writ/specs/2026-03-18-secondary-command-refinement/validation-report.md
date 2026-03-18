# Validation Report: Secondary Command Refinement

> **Date:** 2026-03-18
> **Result:** ✅ PASS — All three files at A grade

## Task 1: Line Count Audit

| File | Before | After | Target Range | Status |
|------|--------|-------|-------------|--------|
| create-issue.md | 307 | 139 | 126–154 | ✅ |
| design.md | 377 | 209 | 180–220 | ✅ |
| prototype.md | 358 | 199 | 189–231 | ✅ |
| **Total** | **1,042** | **547** | **495–605** | ✅ |

Overall reduction: 47.5%

## Task 2: Litmus Test Results

Applied the three-question litmus test (teaches non-obvious? / sets quality bar? / prevents mistake?) section-by-section across all three files.

### create-issue.md — PASS

| Section | Lines | Verdict | Notes |
|---------|-------|---------|-------|
| Overview | 1–5 | ✅ | "Speed over completeness", "under 2 minutes", "good enough beats perfect" — all set quality bars |
| Invocation | 7–12 | ✅ | Functional — necessary for execution |
| Step 1: Context Capture | 14–21 | ✅ | Type hint parsing teaches what to extract |
| Step 2: Clarification | 23–38 | ✅ | Question trigger table + skip logic = non-obvious judgment calls |
| Step 3: Context Search | 40–54 | ✅ | Search/skip triggers encode when to search vs when it wastes time |
| Step 4: Related Issues | 56–63 | ✅ | Skip conditions prevent unnecessary slowdown |
| Step 5: Create Issue File | 65–109 | ✅ | Template is the output contract; section omission rules prevent over-documentation |
| Step 6: Confirm | 111–119 | ✅ | Sets the "Back to work!" bar |
| Example | 121–139 | ✅ | Demonstrates the hardest judgment: when to ask vs skip |

Failures: 0

### design.md — PASS

| Section | Lines | Verdict | Notes |
|---------|-------|---------|-------|
| Overview + Invocation | 1–17 | ✅ | Concise, shows all five modes |
| Phase 1: Context & Mode | 19–40 | ✅ | Mode table scannable; framework detection explained with rationale |
| Mode A: Wireframes | 42–82 | ✅ | Wireframe conventions are crown jewels; component inventory principles replace template |
| Mode B: Attach | 84–117 | ✅ | `## Visual References` format documented with pattern-matching rationale |
| Mode C: Capture | 119–138 | ✅ | `current/` vs `target/` split explained; browser MCP referenced |
| Mode D: Compare | 140–162 | ✅ | Comparison table preserved — key deliverable |
| Design System Extraction | 164–174 | ✅ | Four categories + "tag as auto-extracted" |
| Pipeline Integration | 176–201 | ✅ | Gate 1 loading sequence, visual-qa-agent reference — all non-obvious |
| Integration with Writ | 203–209 | ✅ | Matches standard table pattern |

Failures: 0

### prototype.md — PASS

| Section | Lines | Verdict | Notes |
|---------|-------|---------|-------|
| Overview + Comparison table | 1–16 | ✅ | Disambiguation table is high-value |
| Invocation | 18–26 | ✅ | "Single clarifying question" prevents menu-itis |
| Pipeline + Error recovery | 27–45 | ✅ | ASCII diagram intact; error recovery inlined as principles |
| Step 1: Extract Intent | 47–58 | ✅ | Four input sources, extraction targets |
| Step 2: Context Scan | 60–91 | ✅ | All 7 substeps including nearby rules sniffing; UI heuristic; context example |
| Step 2.5: Visual Preview | 93–125 | ✅ | Canvas guidelines and "what the canvas is NOT" — innovative, well-written |
| Step 3: Coding Agent | 127–157 | ✅ | Principles-based; six scope flags VERBATIM |
| Step 4: Lint & Typecheck | 159–163 | ✅ | Detection-and-retry logic compressed to essentials |
| Step 5: Output Summary | 165–184 | ✅ | Three outcomes in ~20 lines |
| When to Use | 186–199 | ✅ | Disambiguation table preserved |

Failures: 0

## Task 3: Cross-Reference Check

| Reference | File | Line | Target Exists | Status |
|-----------|------|------|---------------|--------|
| `agents/coding-agent.md` | prototype.md | 129 | ✅ `agents/coding-agent.md` | ✅ |
| `agents/visual-qa-agent.md` | design.md | 201 | ✅ `agents/visual-qa-agent.md` | ✅ |
| Gate 1 → coding agent | design.md | 60, 81, 193 | N/A (concept) | ✅ |
| Gate 4.5 → visual QA | design.md | 201, 208 | N/A (concept) | ✅ |

All cross-references intact and resolvable.

## Task 4: Capability Comparison

### create-issue.md

| Capability | Pre-Refinement | Post-Refinement | Status |
|-----------|----------------|-----------------|--------|
| Step 1: Context Capture | ✅ | ✅ | Preserved |
| Step 2: Light Clarification + triggers | ✅ | ✅ | Preserved (table format) |
| Step 3: Context Search + skip logic | ✅ | ✅ | Preserved |
| Step 4: Related Issues Check | ✅ | ✅ | Preserved |
| Step 5: File creation with template | ✅ | ✅ | Preserved |
| Step 6: Confirmation | ✅ | ✅ | Preserved |
| Core Rules (6 rules) | Standalone section | Merged into steps | Preserved — better integrated |
| Example (clarification case) | ✅ | ✅ | Preserved (only judgment-teaching example) |

Removed without capability loss: AI Implementation Prompt (restatement), 3 redundant examples, Integration Notes, Folder Structure, Future Enhancements.

### design.md

| Capability | Pre-Refinement | Post-Refinement | Status |
|-----------|----------------|-----------------|--------|
| Mode A: Wireframes + conventions | ✅ | ✅ | Preserved |
| Mode B: Attach Mockups | ✅ | ✅ | Preserved |
| Mode C: Capture Current UI | ✅ | ✅ | Preserved (browser MCP) |
| Mode D: Compare + table format | ✅ | ✅ | Preserved |
| Mode E: Review (in mode table) | ✅ | ✅ | Preserved |
| Component inventory generation | Full template | Principles | Preserved — AI can generate from principles |
| mockups/README generation | Full template | Principles | Preserved — AI can generate from principles |
| Design system extraction | Full template | Principles + categories | Preserved |
| Pipeline integration | ✅ | ✅ | Preserved |
| Visual References format | ✅ | ✅ | Preserved with rationale |

Removed without capability loss: Tool Integration table, Excalidraw JSON schema, component primitives, Playwright/bash code.

### prototype.md

| Capability | Pre-Refinement | Post-Refinement | Status |
|-----------|----------------|-----------------|--------|
| Extract Intent (4 sources) | ✅ | ✅ | Preserved |
| Context Scan (7 substeps) | ✅ | ✅ | Preserved |
| UI detection heuristic | ✅ | ✅ | Preserved |
| Figma MCP detection | ✅ | ✅ | Preserved |
| Visual Preview + canvas | ✅ | ✅ | Preserved |
| Coding agent spawn | 80-line template | 25-line principles | Preserved — same inputs, principles-based |
| Scope escalation (6 flags) | ✅ | ✅ | Preserved VERBATIM |
| Experience gaps | ✅ | ✅ | Preserved |
| Lint & Typecheck retry | ✅ | ✅ | Preserved |
| Output formats (3 cases) | 73 lines | 18 lines | Preserved — same branching logic |
| Error handling | Standalone section | Inlined as principles | Preserved |
| When to Use table | ✅ | ✅ | Preserved |

Removed without capability loss: language/tool matrix, exact output format headers, verbose error handling block.

**Zero capabilities lost across all three files.**

## Task 5: Voice & Density Comparison

Benchmarks: assess-spec.md (203 lines), edit-spec.md (118 lines)

| Pattern | Benchmark | create-issue | design | prototype |
|---------|-----------|-------------|--------|-----------|
| Short paragraphs (2-4 lines) | ✅ | ✅ | ✅ | ✅ |
| Tables for structured data | ✅ | ✅ | ✅ | ✅ |
| Bullets for lists | ✅ | ✅ | ✅ | ✅ |
| No "you should" filler | ✅ | ✅ | ✅ | ✅ |
| Principle-first | ✅ | ✅ | ✅ | ✅ |
| Consistent headers (Overview, Invocation, Process) | ✅ | ✅ | ✅ | ✅ |
| Direct, principle-driven tone | ✅ | ✅ | ✅ | ✅ |
| No section feels bloated/sparse | — | ✅ | ✅ | ✅ |

All three refined files read at the same density as the benchmark set. No tonal inconsistencies detected.

## Overall Verdict

| File | Grade | Litmus Test | Line Count | Cross-Refs | Capabilities | Voice |
|------|-------|-------------|------------|------------|-------------|-------|
| create-issue.md | A | ✅ 0 failures | ✅ 139 | N/A | ✅ Zero lost | ✅ Match |
| design.md | A | ✅ 0 failures | ✅ 209 | ✅ All intact | ✅ Zero lost | ✅ Match |
| prototype.md | A | ✅ 0 failures | ✅ 199 | ✅ All intact | ✅ Zero lost | ✅ Match |

**Result: ✅ ALL PASS — Ready for commit.**

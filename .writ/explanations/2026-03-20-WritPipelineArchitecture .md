# Code Explanation: Writ Pipeline Architecture

_Generated on 2026-03-20_

## Overview

Writ is a **prompt-driven software methodology** — not a runtime, not a framework, not a CLI. It's a suite of 22 markdown command specifications and 7 agent role definitions that turn an AI coding assistant into a disciplined development team. Every command is a contract: a set of instructions that the AI executes as a structured workflow with quality gates, handoffs, and feedback loops.

The entire "product" is markdown files. The entire "runtime" is an AI model following those files. This is simultaneously its greatest strength (zero dependencies, infinitely portable across Cursor, Claude Code, OpenClaw) and its most interesting constraint (quality depends entirely on specification clarity and model instruction-following fidelity).

## Execution Flow

### The Macro Pipeline

A feature flows through these stages, each a separate command invocation:

```mermaid
graph TD
    INIT["/initialize<br/>Detect stack, seed config"] --> PLAN["/plan-product<br/>Mission, roadmap, ADRs"]
    PLAN --> SPEC["/create-spec<br/>Feature → contract → spec package"]
    SPEC --> ASSESS["/assess-spec<br/>6-check risk analysis"]
    ASSESS --> IMPL["/implement-spec<br/>DAG-aware orchestrator"]
    IMPL --> REVIEW["/review<br/>Failure-mode code review"]
    REVIEW --> SHIP["/ship<br/>Merge, commits, PR"]
    SHIP --> RELEASE["/release<br/>Changelog, tag, publish"]
    RELEASE --> RETRO["/retro<br/>Git metrics & patterns"]
    RETRO --> REFRESH["/refresh-command<br/>Learning loop"]
    REFRESH -.->|improves| SPEC

    ISSUE["/create-issue"] -.->|--from-issue| SPEC
    PROTO["/prototype"] -.->|--from-prototype| SPEC
    DESIGN["/design"] -.->|mockups| SPEC
    RESEARCH["/research"] -.->|evidence| SPEC
    ADR["/create-adr"] -.->|decisions| SPEC
    EDIT["/edit-spec"] -.->|modifies| SPEC

    style SPEC fill:#e8c547,color:#000
    style IMPL fill:#e8c547,color:#000
    style REFRESH fill:#34d399,color:#000
```

### The Per-Story Pipeline (Inside /implement-story)

Each user story passes through up to 8 gates:

```mermaid
graph LR
    G0["Gate 0<br/>Arch Check<br/>PROCEED/CAUTION/ABORT"] --> G1["Gate 1<br/>Coding Agent<br/>TDD, max 3 self-fix"]
    G1 --> G2["Gate 2<br/>Lint & Typecheck"]
    G2 --> G25["Gate 2.5<br/>Change Surface<br/>Classification"]
    G25 --> G3["Gate 3<br/>Review Agent<br/>PASS/FAIL/PAUSE"]
    G3 --> G35["Gate 3.5<br/>Drift Response<br/>S/M/L"]
    G35 --> G4["Gate 4<br/>Testing Agent<br/>100% pass, ≥80% cov"]
    G4 --> G45["Gate 4.5<br/>Visual QA<br/>≥85% match"]
    G45 --> G5["Gate 5<br/>Documentation"]

    G3 -->|FAIL max 3x| G1
    G4 -->|FAIL max 2x| G1
    G45 -->|FAIL| G1
```

### Agents and Their Roles

| Agent | Gate | Mode | Iteration Cap | Pass Criteria |
|-------|------|------|---------------|---------------|
| Architecture Check | 0 | readonly, fast model | 1 | PROCEED / CAUTION / ABORT |
| Coding Agent | 1 | read-write | 3 self-fix | Tests pass, typecheck clean |
| Review Agent | 3 | readonly | 3 iterations | PASS / FAIL / PAUSE |
| Testing Agent | 4 | read-write | 2 fix iterations | 100% pass, ≥80% coverage |
| Visual QA | 4.5 | readonly | shared 3 cap | ≥85% mockup match |
| Documentation | 5 | read-write | 1 | DOCS_UPDATED: YES/NO |
| User Story Generator | create-spec | fast model | 1 per story | Parallel story generation |

## Detailed Breakdown

### Key Design Patterns

#### Contract-First Everywhere
No files created until a contract is locked. `/create-spec`, `/plan-product`, `/edit-spec`, `/new-command` all follow this. Discovery happens in Plan Mode (open-ended). Decisions happen via AskQuestion (bounded). Codified in **ADR-001**.

#### Adaptive Ceremony
`/prototype` for quick changes (no spec). `--quick` flag skips arch-check, review, docs. Full pipeline for serious features. Scope escalation auto-detects when a prototype outgrows its bounds (`--from-prototype`).

#### Self-Correction at Three Levels
- **Agent-level:** Coding/Testing agents self-fix up to 3 iterations before escalating
- **Spec-level:** Drift detection (Small/Medium/Large) with auto-amend for spec-lite, human decision for large drift
- **System-level:** `/refresh-command` mines transcripts for friction signals and proposes command improvements with a promotion pipeline

#### Context Management
`.writ/context.md` regenerated (never patched) after each story. `/assess-spec` estimates context accumulation cost. `spec-lite.md` exists specifically as a compact context payload for agents.

#### Separation of Concerns
`/verify-spec` owns metadata correctness. `/review` owns code quality. `/release` owns the gate. `/assess-spec` owns pre-build risk. No single command tries to do everything.

### Command Categories

**Planning (5):** `/initialize`, `/plan-product`, `/create-spec`, `/edit-spec`, `/design`

**Risk & Analysis (3):** `/assess-spec`, `/research`, `/create-adr`

**Implementation (4):** `/implement-spec`, `/implement-story` (internal), `/prototype`, `/refactor`

**Quality (2):** `/verify-spec`, `/review`

**Shipping (2):** `/ship`, `/release`

**Feedback (3):** `/retro`, `/refresh-command`, `/status`

**Utility (3):** `/create-issue`, `/new-command`, `/explain-code`

## Architecture Context

### File Organization

```
writ/
├── commands/           # Product source — 22 command specifications
├── agents/             # Product source — 7 agent role definitions
├── adapters/           # Platform adapters (Cursor, Claude Code, OpenClaw)
├── cursor/             # Cursor-specific rule (writ.mdc)
├── scripts/            # install.sh, update.sh, migrate.sh, unlink.sh
├── system-instructions.md  # Global agent personality & protocol
├── .writ/              # Development workspace (dogfooding)
│   ├── specs/          # 10 spec packages (stories, tech specs, AC)
│   ├── product/        # Mission, roadmap, decisions
│   ├── research/       # Technical research artifacts
│   ├── decision-records/ # ADRs
│   ├── docs/           # Operational documentation
│   ├── issues/         # Issue tracking
│   ├── retros/         # Retrospective snapshots
│   └── state/          # Ephemeral execution state (gitignored)
└── .cursor/            # Active installation (symlinked to product source)
    └── commands/       # Symlinks → commands/
```

### Self-Dogfooding Model

This repo uses Writ to build Writ. `.cursor/commands/` symlinks to `commands/` (product source). Edits to commands are edits to the product. `.writ/` is the development workspace — specs, research, and decisions for building Writ itself.

## Related Components

- [System Instructions](../../system-instructions.md) — Global agent identity and protocol
- [README](../../README.md) — Public documentation and quick start
- [ADR-001](../decision-records/adr-001-askquestion-vs-plan-mode.md) — AskQuestion vs Plan Mode
- [Mission](../product/mission.md) — Product positioning and phases
- [Roadmap](../product/roadmap.md) — Feature timeline

---

_Generated by Writ on 2026-03-20_

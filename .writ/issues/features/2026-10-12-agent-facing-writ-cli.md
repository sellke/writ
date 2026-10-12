# Agent-Facing Writ CLI

> **Type:** Feature
> **Priority:** Normal
> **Effort:** Large
> **Created:** 2026-10-12
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

Build a CLI that lets agents use and contribute to Writ anywhere it is available, so Writ speeds up product development and is more than a verification loop.

## Current State

- Agents reach Writ only by reading markdown command files and following them top to bottom.
- Deterministic behavior lives in ~40 loose `scripts/*.py` / `*.sh` files (`story-context.py`, `spec-status.py`, `phase-state.py`, `recommend-state.py`, ...). Commands call them by path, and each project carries its own copied version.
- `@sellke/writ` on npm is deliberately narrow: only `date` and `timestamp`.
- Agents have no single entry point to discover Writ state, run a stage, or send improvements (issues, command refinements) back upstream.
- In practice, Writ works mostly as the verification and gating loop around work an agent was already doing.

## Expected Outcome

- One CLI entry point (likely an extension of `@sellke/writ`) that agents can run in any project with Writ installed.
- Agents can query state (`status`, the active spec, the next recommended step) and get structured output back. No prose parsing.
- Agents can run deterministic stages (story context, spec deps, spec status, phase state) through stable subcommands instead of script paths.
- Agents can contribute upstream: file issues, propose command refinements, and report evidence from real runs back to the Writ source.
- The markdown commands remain the methodology. The CLI is the action surface agents use to carry it out.

## Relevant Files

- `scripts/writ-runtime-readme.md` - current `@sellke/writ` scope, which says it is "not the Writ methodology itself"
- `scripts/publish-writ-runtime.sh` - existing npm publish path
- `.writ/product/decisions.md` - decision that rejected a CLI tool

## Notes

- **Decision:** [ADR-029](../../decision-records/adr-029-agent-cli-contract.md) (Accepted) chooses a contract over per-workflow tools rather than a `writ` CLI product, and handles contribution through local changes that a person approves.
- **This conflicts with a recorded decision.** `.writ/product/decisions.md` lists "CLI Tool (npm install -g writ)" as a rejected alternative: "Platforms will always have better native tooling." Before writing a spec, write an ADR that either supersedes that decision or narrows this CLI to a runtime/action layer under the methodology. The second option is closer to the existing "tooling extends reach" rationale.
- Scope risk: "fully use and contribute to" covers a lot. Split it into (1) a read-only state/query surface, (2) wrappers around existing deterministic scripts, (3) the upstream contribution flow.
- Contributing upstream sends content to a public repo, so it needs an explicit consent and approval step.

# Replace bounded harness judgments with Jev typed judgments

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Large
> **Created:** 2026-09-25
> **spec_ref:** .writ/specs/2026-09-25-jev-judgment-pilot/spec.md

## TL;DR

Several Writ gates make small, bounded semantic judgments with a known answer set. Today each one costs an anchor-tier agent spawn, a round of orchestrator reasoning, a human interruption, or a brittle keyword list. TypeSafe's Jev model returns calibrated typed answers (Choice / Noul / Score, each with confidence), so it could make these calls faster and route only low-confidence cases to an agent or a person.

## Current State

Candidates, ranked by frequency × cost × how cleanly the answer set is defined:

- **Evaluator per-AC verdict** (`commands/implement-story.md` Gate 3, `agents/evaluator-agent.md`, anchor tier). One full agent spawn per story, and it is the largest recurring spawn on the default path. A wrong PASS is expensive.
- **Drift severity** (Gate 3.5, `skills/drift-triage/SKILL.md`). The evaluator assigns None/Small/Medium/Large inside its own spawn. Log to date: 84 Small, 20 Medium, 1 Large. Calling a Large "Small" silently auto-amends `spec-lite.md`.
- **Spec analysis** (`/create-spec` Step 2.6c). One orchestrator LLM pass per spec. The vague-Then check in `scripts/spec-analyze.py` is `VAGUE_THEN`, a frozenset of six literal strings. Findings are advisory. The `--findings <json>` seam and the gold fixtures in `scripts/tests/fixtures/spec-analyze/` already exist.
- **Roadmap feature → spec matching** (`implement-phase.md:76` title similarity; `scripts/resolve-spec-reference.py` substring match). A missed match under `/implement-phase --recommend` authors a spec that did not need writing.
- **Cross-spec overlap** (`/create-spec` Step 1.3b). Keyword matching; under `--recommend` a "blocking" result pauses the run.
- **Knowledge relevance and dedupe** (`skills/story-context-assembly`, the +3/+2/+1 hand scoring; `phase-state.py` `_is_duplicate` Jaccard ≥0.5 silently drops knowledge writeback).
- **`--recommend` auto-adopt calls** (UI-bearing?, which sub-specs apply, does error mapping apply?). Decided by orchestrator reasoning, with no calibrated number to record in `recommendation-log.md`.
- **Smaller calls:** lane failure transient vs terminal, `/create-issue` type and priority, `/knowledge` category, `/prototype` UI detection keyword list, `/release` commit categorization.

## Expected Outcome

- One optional, opt-in judgment provider, reachable two ways:
  - TypeSafe direct (`TYPESAFE_API_KEY`);
  - the Vercel AI Gateway's TypeSafe-compatible endpoint (`AI_GATEWAY_API_KEY`, model `typesafe-ai/jev`).
  It is off by default and uses Python 3.9 stdlib only. With no key, the harness behaves exactly as it does today. Users are prompted once to set it up, and are never asked to paste a key into chat.
- Callers emit the existing script contract: a `pass` / `fail` / `unverifiable` verdict, `reason:` lines, and exit codes 0/1/2. A low-confidence answer maps to `unverifiable`, so gates keep their current "continue, surface the reason" handling.
- Confidence thresholds are calibrated against labeled fixtures and pinned to a versioned model ID (`jev-1.13.0`, not `jev-latest`).
- Pilot on a site where errors are cheap (spec analysis). Run a high-stakes site (evaluator per-AC) in shadow mode, logging the typed judgment next to the agent's verdict, before any spawn is skipped.
- Savings are measured offline with the existing `scripts/pipeline-baseline.py` / `harness-cost.py` / `lean-decision.py`. The harness has no timing or token source of its own.

## Relevant Files

- `scripts/spec-analyze.py` - the `--findings` seam; the first pilot
- `commands/implement-story.md` - Gates 3 and 3.5, where most of the leverage sits
- `.writ/decision-records/adr-024-model-delegation.md` - the family-lock rule a vendor call has to reconcile with

## Related Issues

- [2026-09-03-test-integrity-authenticity-flags-every-bash-test](2026-09-03-test-integrity-authenticity-flags-every-bash-test.md) - fix deterministically first (`unsupported_stack` → `unverifiable`); a typed judgment helps only as a fallback there

## Notes

- **Needs an ADR.** An external paid API with a network call breaks three existing rules:
  - Writ's no-dependency / no-network posture.
  - Phase 11's "no API key inside verifier scripts." Put the call in a separate caller that writes JSON an existing script already accepts.
  - The spirit of ADR-024's no-vendor-crossing rule. Jev replaces a verdict, not an agent tier, but the ADR should say so explicitly.
- **Privacy:** state sent to Jev includes spec text and diffs. Users must opt in knowingly.
- **Wrong tool for:** generation (coding-agent, story generation, PR and changelog prose); the Large-drift accept/reject decision and User Challenges (human class under ADR-022); visual QA; the evaluator's open-ended security and taste scan.
- **Fix first:** Gate 2.5's `change-surface.py` output never reaches the evaluator on the default path. Wire it in or drop it before building on it.
- **Jev constraints** (jev-1.13 jaggedness doc): literal reading, poor counting and numeric comparison, and accuracy that degrades with large irrelevant state. Slice diffs per AC; keep arithmetic and counting in code.

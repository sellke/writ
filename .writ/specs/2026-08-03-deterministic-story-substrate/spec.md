# Spec: Deterministic Story Substrate

> **Status:** Not Started
> **Owner:** @Adam Sellke
> **Created:** 2026-08-03
> **Dependencies:** none
> **Origin:** [`2026-08-03-writ-vs-openspec-analysis`](../../research/2026-08-03-writ-vs-openspec-analysis.md) — P2 adopted as specified; the context-assembly half is a finding the research's recommendation table did not surface
> **Builds on:** [`2026-07-26-leanness-instrumentation`](../2026-07-26-leanness-instrumentation/spec.md) / [ADR-019](../../decision-records/adr-019-full-surface-leanness-measurement.md)

## Contract (Locked)

**Deliverable:** Move Writ's two highest-consequence agent-interpreted steps to program — validate the user-story dependency graph before `/implement-spec` batches parallel worktrees, and replace the orchestrator's prose context-hint parser with a deterministic, budget-enforced assembler that becomes the single implementation of a contract currently stated three times.

**Must include:** The `fetched_context` byte budget, empirically derived. Everything else in this spec consolidates logic that already works; the budget closes the one unbounded token path routed to all five gate agents. It is the only part that is genuinely absent rather than misplaced.

**Hardest constraint:** The prose being deleted is load-bearing. `commands/implement-story.md` lines 75–123 are not decoration — they are the running implementation. A script that is merely *approximately* equivalent silently degrades every downstream gate's context. Story 2 must prove fixture-level equivalence before Story 4 removes the prose, which is why they are separate stories with a dependency rather than one change.

## Why This Exists

Writ's quality and token story is enforced by program exactly where enforcement is cheap, and left to agent judgment exactly where the consequences and the volume are.

### The coarse graph is checked; the fine graph is not

`scripts/spec-deps.py` validates the cross-spec DAG, and `commands/implement-phase.md` (lines 126–135) runs it pre-execution as a blocking gate with unambiguous language: *"Invalid explicit metadata is blocking… Do not guess an order around invalid metadata."*

`commands/implement-spec.md` Step 2.1–2.2 (lines 62–82) builds the **story** DAG — the graph that actually determines which stories get spawned into parallel git worktrees — by agent interpretation, with no validation at all. Step 2.3b's pre-flight is explicitly *"advisory — never blocks execution."*

The asymmetry is inverted relative to blast radius. A bad cross-spec order runs specs in the wrong sequence. A bad story graph spawns concurrent worktrees against unsatisfied dependencies, and the failure surfaces as confusing mid-flight skip/retry prompts (`implement-spec.md` lines 164–166) rather than as a graph diagnostic.

The validation logic already exists. `scripts/recommend-state.py` `validate_dag()` (lines 376–394) does cycle and dangling-reference detection over story IDs, and its dependency regex (lines 363–366) is the proven parser. Both are dormant — reachable only through `--recommend` eval fixtures.

### One parsing contract, stated three times, and the copy that runs is prose

| Location | Form | Role |
|---|---|---|
| `.writ/docs/context-hint-format.md` | 433 lines of prose | Declares the format, the parsing algorithm, and an edge-case table |
| `commands/implement-story.md` lines 75–123 | ~50 lines of prose | **Actually executes**, by LLM judgment, every story |
| `scripts/eval-leanness.py` `resolve_context_hints()` lines 234–253 | working Python | Only measures |

Nothing keeps the three in agreement. This is precisely why `story_context_bytes` is honestly labeled a "declared-load proxy" (`eval-leanness.py` line 38, and Business Rule 7 of the leanness-instrumentation spec) — it cannot be anything more, because it is not the code doing the loading.

The docs copy also rests on a premise that is now false. Line 340: *"Since Writ is a markdown-based workflow system with no automated test suite, validation follows a documentation + golden file approach."* `scripts/eval.sh` runs 27 checks in CI. The manual golden-file strategy was a reasonable response to a constraint that no longer exists.

### The budget is on the wrong artifact

| Context source | Cap | Enforcement |
|---|---|---|
| `spec-lite.md` | 100 lines | **Hard, CI** — `eval.sh` `check_length` |
| `knowledge_context` | 2KB | Prose only |
| `fetched_context` | **none** | **none** |

`fetched_context` is routed to all five gate agents (`implement-story.md` lines 191–195), and it is the only one of the three that scales with both spec size and story count. It is the one nobody bounded.

## 🎯 Experience Design (CLI / CI — no user-facing UI)

### Entry Point

No new user-invokable surface. Two scripts invoked by existing commands, plus two new `eval.sh` checks:

- `/implement-spec` gains a blocking graph validation before it computes batches.
- `/implement-story` Step 2 calls the assembler instead of parsing hints itself.
- `bash scripts/eval.sh --check=story-deps` and `--check=story-context` run locally and in Tier 1 CI.

### Happy Path

1. Developer runs `/implement-spec`.
2. The story graph validates clean; deterministic batches are printed in the execution plan.
3. Per story, the assembler resolves context hints and returns a bounded payload with a byte report.
4. Gates run as they do today, on context that is now reproducible run to run.

### Moment of Truth

`story_context_bytes` stops being a proxy. The number in the leanness report becomes the number the pipeline actually loaded, because the same code produced both.

### Error Experience

| Situation | Behavior |
|---|---|
| Story graph has a cycle, self-reference, missing reference, duplicate, or malformed header | **Blocking.** Stop before the confirmation gate, name the affected story and the exact diagnostic (including the cycle path). Never guess a batch order around invalid metadata. |
| `## Context for Agents` section absent | Proceed on `spec-lite.md` alone; informational log. Legacy stories keep working. |
| Hint category malformed or misspelled | Skip that category, warn, continue. |
| Referenced content not found in source file | Skip that reference, warn, continue. |
| `spec.md` or `technical-spec.md` unreadable | Warn, fall back to `spec-lite.md` only. |
| `fetched_context` exceeds budget | Truncate by relevance, warn with actual and budget bytes, continue. |
| Assembler itself fails or is absent | Warn and fall back to `spec-lite.md` only — a broken assembler degrades context; it never halts a story. |

The distinction is deliberate and is the spec's central safety rule: **graph validity blocks, context assembly degrades.** A wrong graph corrupts execution order and must stop the run. Thin context produces a weaker story that the existing review and testing gates still judge.

### Feedback Model

Unchanged conventions. Graph failures render like `implement-phase`'s existing cross-spec diagnostics. Assembler warnings render through the existing `context_warnings` channel already documented at `implement-story.md` line 123. A clean run stays quiet.

## 📋 Business Rules

1. **Graph validity is blocking; context assembly is degrading.** No exceptions in either direction.
2. **One implementation per contract.** After this spec, story-dependency parsing exists once (`story-deps.py`, imported by `recommend-state.py`) and context-hint resolution exists once (`story-context.py`, imported by `eval-leanness.py`).
3. **Error classes match the cross-spec validator exactly** — `malformed_dependencies`, `missing_reference`, `self_reference`, `duplicate_reference`, `dependency_cycle`. A maintainer who has read one diagnostic can read the other.
4. **The budget is derived, never invented.** The threshold must come from measured `fetched_context` values across the specs in this repo, set above the observed distribution so it catches pathology and not normal work. The measurement and the chosen number are both recorded.
5. **Determinism is a testable property.** Both scripts return byte-identical output for an unchanged tree. This is what makes the leanness metric trustworthy and is asserted, not assumed.
6. **Legacy stories never break.** Stories with no `## Context for Agents` section, or with hints referencing content that no longer exists, degrade gracefully exactly as they do today.
7. **Orchestration policy stays in the command.** The per-gate routing table (`implement-story.md` lines 191–195) decides *which* categories reach *which* agent. That is policy and belongs in markdown. Only parsing and fetching move to code.
8. **Growth in `scripts/` is expected and must be justified in the baseline.** Moving a contract out of `.writ/docs/` (unmeasured) into `scripts/` (measured) registers as surface growth under ADR-019's ratchet. The justification is recorded rather than routed around.

## Detailed Requirements

### `scripts/story-deps.py`

CLI shape mirrors `spec-deps.py`: `validate --spec-dir <path> [--json]`. Parses `> **Dependencies:**` from every `user-stories/story-*.md`, accepting the documented value forms (`None`, `Story N`, comma-separated lists) via the regex proven in `recommend-state.py` lines 363–366.

On success it emits the topological batches that `implement-spec.md` Step 2.2 currently derives by inspection, with a deterministic tie-break by story number so the plan is reproducible. On failure it emits the offending story plus the specific diagnostic.

`recommend-state.py` `validate_dag()` is refactored to call the shared module. The duplicate implementation does not survive this story.

### `scripts/story-context.py`

Implements the contract in `.writ/docs/context-hint-format.md`: locate `## Context for Agents`, parse all four categories (`Error map rows`, `Shadow paths`, `Business rules`, `Experience`) in both the bracketed and the extended `file.md → ## Section → ### Subsection` forms, resolve against `technical-spec.md` with the documented `spec.md` fallbacks, and handle every branch of the edge-case table.

Output is JSON — the narrow, useful borrow from OpenSpec's `instructions --json`, scoped to one story rather than generalized into a schema engine:

```json
{
  "fetched_context": { "<category>": "<content>" },
  "warnings": ["..."],
  "bytes": { "<category>": 0, "total": 0 },
  "truncated": false
}
```

`resolve_context_hints()` is removed from `eval-leanness.py`, which imports the assembler instead.

### The budget

Story 3 opens by running the assembler across every spec in `.writ/specs/` and reporting the real distribution of `fetched_context` bytes. The cap is set above the observed high end, and the distribution plus the chosen threshold are recorded in the story's What Was Built record so a later reader can see the number was measured rather than picked.

Over-budget behavior mirrors the existing `knowledge_context` posture already documented at `implement-story.md` lines 165 and 174: retain higher-relevance content first, truncate the remainder, warn, never block.

### Consolidating the prose

`implement-story.md` lines 75–123 collapse to an invocation and its output contract. The routing table survives untouched. `.writ/docs/context-hint-format.md` is rewritten to point at the script as the executable contract instead of restating the algorithm, and its stale "no automated test suite" premise is removed.

## Implementation Approach

Test-first, following the established convention: Python 3 for logic, bash for harness, an `eval-*.py` scenario emitter plus a `check_*` entry in the `CHECKS` array (`scripts/eval.sh` lines 19–47), and unit tests under `scripts/tests/`. Both new scripts follow the `spec-deps.py` precedent of a stable JSON envelope with `eval.sh` deciding FAIL.

Story 1 is independent and can land first or in parallel. Stories 2 → 3 → 4 are strictly sequential: the assembler must exist before it can be measured against real specs, the budget must exist before the assembler becomes the delivery path, and the prose cannot be deleted until the replacement is proven equivalent on fixtures.

## Success Criteria

1. A story graph containing a cycle, self-reference, dangling reference, duplicate, or malformed header stops `/implement-spec` before the confirmation gate with a named diagnostic — verified against fixtures for all five classes.
2. Story-dependency parsing and context-hint resolution each exist in exactly one place; `recommend-state.py` and `eval-leanness.py` import rather than duplicate.
3. The assembler reproduces the prose parser's behavior on fixtures covering every row of the edge-case table, including all six degradation scenarios.
4. The `fetched_context` cap is documented alongside the measured distribution it was derived from.
5. `story_context_bytes` is produced by the same code path that delivers context, and is byte-identical across repeated runs on an unchanged tree.
6. `commands/` line count decreases; the `scripts/` increase carries a recorded baseline justification; full eval Tier 1 stays green with `Findings: 0`.

## Technical Concerns (surfaced at contract time)

- **Equivalence is the real risk.** An LLM following prose and a regex following a grammar will not agree on every ambiguous input, and the prose has no test suite to define correct behavior. Mitigation: fixtures are derived from the edge-case table in `.writ/docs/context-hint-format.md` — the closest thing to a written specification that exists — and Story 4 is gated on Story 3, so the script is exercised on real specs before the prose is removed.
- **A brittle assembler is worse than prose.** An LLM improvises around a malformed hint; a regex does not. This is why every assembler failure mode degrades to `spec-lite.md` rather than halting, and why the script's absence is itself a handled case.
- **The ratchet will fire.** `scripts/` grows while `commands/` shrinks, and only one of those two surfaces was measured before ADR-019. Expected, and Business Rule 8 requires the justification rather than an exemption.
- **`spec-deps.py` is documented but unhooked.** `implement-phase.md` line 132 instructs the agent to run it; no shell hook enforces the call. `story-deps.py` inherits the same weakness — a documented invocation an agent could skip. Accepted here as consistent with the existing pattern; a genuine enforcement hook is a separate concern spanning both validators and is not smuggled into this spec.
- **The 433-line docs file lives outside the measured surface.** Rewriting it is real leanness work that the instrument cannot see, so it will not appear in the reported delta. Noted so the Story 4 report does not read as a smaller win than it is.

## Scope Boundaries

**Included:** `story-deps.py` with a blocking pre-execution gate in `/implement-spec`; `story-context.py` as the single context-hint implementation; an empirically derived `fetched_context` budget; real `story_context_bytes`; consolidation of the orchestrator prose and the format doc; eval wiring and unit tests for both scripts.

**Excluded, deliberately:**

- **Research P5 (fluid-editing framing).** Prose added to every command file for zero mechanism — directly against ADR-019's reduction ratchet.
- **Research P4 (Stores / multi-repo).** ADR-007's trigger has not fired.
- **Research P3 (`skip_reason:` ceremony marker).** Real, but bookkeeping rather than quality. Filed under `.writ/issues/improvements/` instead of consuming a story slot.
- **OpenSpec's schema-fork generality and adapter-generation engine.** Those solve extensibility and distribution, not quality or token cost.
- **Any move toward a single-model default.** ADR-016's enforced tiering is the stronger bet on exactly the axes this work targets.
- **A shell-level enforcement hook for either validator.** Both stay documented invocations, matching `spec-deps.py`. Changing that is its own spec.
- **Live token metering.** `story_context_bytes` becomes a real measurement of delivered bytes, not consumed tokens. ADR-019's labeling discipline still applies.
- **Changing what any gate agent does with its context.** Only assembly and bounding change; routing and gate behavior do not.

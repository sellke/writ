# Drift and Architecture Guards (Lite)

> Source: .writ/specs/2026-09-26-drift-arch-guards/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Default `/implement-story` catches out-of-scope changes and architecture-class drift mechanically and routes Gate 3 to `review-agent` when either appears, still spawning two agents.

**Implementation Approach:**
- Extend `scripts/boundary-map.py` with a `crossings` subcommand; extend `scripts/drift-format.py` with `summary`. No new scripts.
- Command edits are prose lines inside existing gates; no new gate numbers.
- Python 3.9 stdlib only; helper-family output (verdict, `route:`/`reason:` lines, summary last).

**Files in Scope:**
- `scripts/boundary-map.py`, `scripts/tests/test_boundary_map.py` — `crossings`
- `commands/implement-story.md` — Gate 0.5 save map, Gate 2.5 run crossings, Gate 3 route, context routing
- `agents/evaluator-agent.md`, `agents/review-agent.md` + `claude-code/agents/writ-{evaluator,reviewer}.md` + `codex/agents/{evaluator,review}-agent.toml` — `contract_content`, severity
- `.writ/docs/drift-report-format.md`, `skills/drift-triage/SKILL.md` — severity
- `scripts/drift-format.py`, `scripts/tests/test_drift_format.py`, `commands/implement-spec.md` — roll-up
- `scripts/tests/test_governor_enforcement.py`, `scripts/tests/test_lean_commands.py` — disclosed re-pins

**Error Handling:**
- Map unreadable (including non-list entries) / helper missing → `unverifiable`, `route: review-agent`
- No `--changed` → exit 2 (usage)
- Drift log missing → `summary` passes with zero counts

**Integration Points:**
- `spawn-cap.py` must still pass on `implement-story.md` (swap, never add)
- Two-fail escalation unchanged; Jev shadow on routed stories reports `no_evaluator_ids`

---

## For Review Agents

**Acceptance Criteria:**
1. `crossings` lists outside/out-of-scope files, excludes pipeline outputs, and routes review-agent on crossings or `full-stack` `[AC-1.1, AC-1.2, AC-1.3]`
2. Unreadable map or missing input routes UP to review-agent `[AC-1.4]`
3. Gate 2.5 runs crossings; Gate 3 spawns the routed agent; story report prints `gate3-route:` `[AC-2.1, AC-2.2, AC-2.3]`
4. `spawn-cap.py` passes; ratchets re-pinned with disclosure; lean sibling byte-identical `[AC-2.4, AC-2.5]`
5. Both Gate 3 agents and peers take `contract_content` and treat it as the drift reference `[AC-3.1, AC-3.2]`
6. Architecture-class drift is Large across agents, peers, format doc, and skill `[AC-3.3, AC-3.4]`
7. `drift-format.py summary` counts by severity since a date and lists Medium/Large headlines `[AC-4.1, AC-4.2]`
8. `/implement-spec` Step 4.2 reports the roll-up as a note `[AC-4.3, AC-4.4]`

**Business Rules:**
- Swap, never add; route UP on doubt; triggers are exactly `full-stack` or ≥1 crossing
- Spec folder, `.writ/context.md`, `.writ/state/` are never crossings
- `spec.md` contract outranks `spec-lite.md` for drift; `spec.md` never auto-modified
- Roll-up is report-only; `implement-story.lean.md` untouched

**Experience Design:**
- Entry: `/implement-story story-N` or `/implement-spec`
- Happy path: clean story → `gate3-route: evaluator-agent`
- Moment of truth: out-of-boundary edit → review-agent with the files named
- Feedback: one `gate3-route:` line; one `Drift this run:` line at spec end
- Error: unverifiable crossings → review-agent, reason printed

---

## For Testing Agents

**Success Criteria:**
1. `uv run pytest` green, including 3.9 floor
2. `bash scripts/tests/test_*.sh` green
3. `bash scripts/eval.sh` Findings 0

**Shadow Paths to Verify:**
- **Happy path:** changed ⊆ owned, non-full-stack → `route: evaluator-agent`
- **Nil input:** no `--changed` → exit 2
- **Empty input:** empty map lists → every non-excluded file is a crossing
- **Upstream error:** unreadable map → `unverifiable`, `route: review-agent`

**Edge Cases:**
- Directory entries in `owned` cover nested files
- `./`-prefixed and absolute changed paths normalize to repo-relative
- Drift log with no `> Run:` date on a section → section counted only without `--since`

**Coverage Requirements:**
- New code: ≥80%; error paths: 100%

**Test Strategy:**
- Unit tests per subcommand in existing test files; wiring pins for command prose

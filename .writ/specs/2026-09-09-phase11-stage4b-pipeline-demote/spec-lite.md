# Phase 11 Stage 4b: Pipeline Demote (Lite)

> Source: .writ/specs/2026-09-09-phase11-stage4b-pipeline-demote/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Default `/implement-story` spawns coding-agent + evaluator-agent only; five-agent path is `--full-pipeline`.

**Implementation Approach:**
- New `agents/evaluator-agent.md` (anchor, readonly); rubric = AC + tests
- Platform counterparts + parity mapping + manifest; do not rewrite `review-agent`
- `implement-story.md` invocation + pipeline + two-fail escalate
- Default Gate 4 fail → coding-agent; scripts stay; no new gate numbers
- `spawn-cap.py` static scan; additive `eval.sh` check

**Files in Scope:**
- `agents/evaluator-agent.md` — new
- `claude-code/agents/writ-evaluator.md`, `codex/agents/evaluator-agent.toml`
- `scripts/check-agent-parity.sh`, `.writ/manifest.yaml`
- `commands/implement-story.md` — default spawn + flags
- `scripts/spawn-cap.py`, `scripts/eval.sh`
- `adapters/{cursor,claude-code,codex,openclaw}.md` — no-flag ≠ full SDLC

**Error Handling:**
- Evaluator FAIL → recode; second FAIL → `--full-pipeline` notice
- Script `unverifiable` → continue, no `DEGRADED`
- Helper missing / exit 2 → `add_finding`

**Integration Points:** `review-override.py` FAIL-only unchanged; Stage 2b scripts still run

---

## For Review Agents

**Acceptance Criteria:**
1. Evaluator agent exists; review-agent untouched; parity + manifest clean `[AC-1.1, AC-1.2, AC-1.3, AC-1.5]`
2. No-flag path names ≤2 spawn sites; flag matrix matches the contract `[AC-2.1, AC-2.2]`
3. Two-fail escalation; Gate 4 default fail recodes via coding-agent `[AC-2.3, AC-2.4]`
4. spawn-cap + eval.sh; adapters no longer imply no-flag is full SDLC `[AC-3.1, AC-3.2, AC-3.3, AC-3.5]`

**Business Rules:**
- No `--default` flag; no high-stakes classifier; no new gate numbers
- FAIL-only override stands; evaluator is read-only; no counterfactual apply
- No emit, eight-run, yuss, prompt-rewrite, background-await
- Decision log `{date} stage-4b:`

**Experience Design:**
- Entry: `/implement-story` (no flag)
- Happy path: scripts → coding-agent → evaluator → close
- Moment of truth: default spawn count is 2
- Feedback: rubric findings; Suggested Fix not applied
- Error: second evaluator FAIL → `--full-pipeline` notice

---

## For Testing Agents

**Success Criteria:**
1. Agent-contract pytest + parity mapping green
2. spawn-cap pass / over_cap / missing / exit 2 fixtures green
3. `eval.sh` exits 0; Story 3 WWB records default ≤2

**Shadow Paths:**
- **Happy path:** default scan names coding-agent + evaluator-agent only
- **Nil input:** missing command file → `unverifiable` `missing_command`
- **Empty input:** command with no Gate 1/3 spawn → fail or unverifiable per helper
- **Upstream error:** third default spawn site → `fail` `over_cap`

**Edge Cases:**
- `--full-pipeline` agents must not count against the cap
- `--quick` / `--review-only` rows exist; no `--default` token

**Coverage Requirements:** New script ≥80%; error paths 100%

**Test Strategy:** pytest on agent file + spawn-cap; eval-wiring bash

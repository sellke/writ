# Writ Agents Registered (Lite)

> Source: .writ/specs/2026-11-08-writ-agents-registered/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `.claude/agents` points at `claude-code/agents/` so Claude Code registers the nine `writ-*` agents in this repo; every spawn has a stated fallback; a check fails when `.claude/agents` exposes no frontmatter agents.

**Implementation Approach:**
- Story 1: replace the symlink (`../claude-code/agents`), update `.writ/docs/self-dogfooding.md`, extend `check_claude_agents` in `scripts/eval.sh`, add cases to `scripts/tests/test_eval_claude_agents.sh`, record a fresh-session agent list.
- Story 2: fallback rule in `adapters/claude-code.md` § Agent Paths; one Gate 1 sentence in `commands/implement-story.md` (offset or ledger); supervisor ESCALATE clause; regenerate trees; text pins.
- Bash 3.2 for eval.sh (no associative arrays, no `mapfile`); Python 3.9 floor for tests.

**Files in Scope:**
- `.claude/agents` (symlink), `.writ/docs/self-dogfooding.md`
- `scripts/eval.sh` (`check_claude_agents`), `scripts/tests/test_eval_claude_agents.sh`
- `adapters/claude-code.md`, `commands/implement-story.md`, `agents/supervisor-agent.md`
- Generated: `claude-code/agents/writ-supervisor.md`, plugin and cursor copies via `gen-platform-trees.py`
- `scripts/tests/test_governor_enforcement.py` (`KNOWN_OVER_BUDGET`, residual only)
- Never: `scripts/install.sh`, plugin manifests, `.cursor/agents`

**Error Handling:**
- Dangling or frontmatter-less link → eval finding, remedy `ln -sfn ../claude-code/agents .claude/agents`
- No `writ-*` type in session → general-purpose spawn briefed from `agents/<file>.md`
- No spawn possible → Gate 1 BLOCKED escalation; never inline coding

**Integration Points:**
- `adapters/claude-code.md` Agent Paths table maps canonical paths to `writ-*`
- `implement-story.md` presence probes pinned by `test_gate_upgrade_trial_outcome.py` must stay intact

---

## For Review Agents

**Acceptance Criteria:**
1. `.claude/agents` is a symlink to `../claude-code/agents` and exposes the nine `writ-*` names `[AC-1.1]`
2. `eval.sh --check=claude-agents` fails on a frontmatter-less link and passes on the real link and on no link `[AC-1.2, AC-1.3, AC-1.4]`
3. A fresh Claude Code session lists the nine `writ-*` types (recorded run) `[AC-1.5]`
4. The adapter states the general-purpose fallback and that the report names the agent type `[AC-2.1]`
5. Gate 1 routes a missing coding-agent type to the fallback or BLOCKED, never inline coding `[AC-2.2, AC-2.4]`
6. The supervisor ESCALATEs code with no coding-agent spawn `[AC-2.3]`

**Business Rules:**
- Symlinks to product source only; `.cursor/agents` unchanged
- `claude-code/agents/` stays generated; both generator `--check`s clean
- Installs unchanged; the link check runs only in the Writ source repo

**Experience Design:**
- Entry: `/implement-story` in this repo
- Happy path: Gate 1 spawns `writ-coder` by name
- Moment of truth: session agent list shows nine `writ-*` types
- Feedback: eval passes; report names the Gate 1 agent
- Error: fallback spawn, else BLOCKED

---

## For Testing Agents

**Success Criteria:**
1. New eval cases pass in `test_eval_claude_agents.sh`
2. pytest 3.9 and 3.14, bash tests, `eval.sh` all green
3. `gen-claude-agents.py --check` and `gen-platform-trees.py --check` clean

**Shadow Paths to Verify:**
- **Happy path:** real link → Findings 0
- **Nil input:** no `.claude/agents` → Findings 0
- **Empty input:** link to empty folder → nine missing-name findings
- **Upstream error:** generator drift → existing finding, link check still runs

**Edge Cases:**
- Dangling link → one "does not resolve" finding
- Mixed folder (some frontmatter) → findings only for the missing names and bare files

**Test Strategy:**
- Bash temp-copy eval cases; pytest readlink and text pins; byte-ledger tests unchanged or re-pinned

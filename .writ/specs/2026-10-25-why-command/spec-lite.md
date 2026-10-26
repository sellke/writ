# Why Command (Lite)

> Source: .writ/specs/2026-10-25-why-command/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `/why "<question>"` answers why something in the project is the way it is, from Writ's ledger first, then git history, then connected MCP servers. Every claim carries a confidence tier. When a change follows, it ends with a `## Preserve / Change / Avoid / Risk` section saved under `.writ/research/`, which `/create-spec` Step 1.2 reads.

**Implementation Approach:**
- `commands/why.md`, under 200 lines, six `### Step N:` headings: Anchor, Ledger, Git, MCP when needed, Answer, Hand off a change. No subagents, no helper script, read-only except the saved record.
- Ledger order: `refs/notes/writ` notes on anchor commits → specs (archive too), `drift-log.md`, What Was Built → ADRs → knowledge and issues → cited research. Git history always runs (stale-ledger check). MCP only when the strongest claim is below `Stated`.
- Tiers: `Recorded`, `Stated`, `Corroborated`, `Inferred`, `Unknown`. Code is not evidence of its own intent; conflicts take the lower tier.
- Saved record `.writ/research/<YYYY-MM-DD>-why-<slug>.md`: header (`Asked`, `Subject`, `Change`, `Question`), answer, handoff section last.
- `/writ` fifth row routes `/why`; `/research` stays for questions outside the project; six rows kept.
- Exact strings: technical-spec.md → `commands/why.md` Skeleton, Output Templates, `/create-spec` Step 1.2, `/writ` Route, Registration Edits.

**Files in Scope:**
- S1: `commands/why.md`, `scripts/tests/test_why_command.py`.
- S2: `.writ/manifest.yaml`, `SKILL.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `cursor/plugin/`, `plugins/writ/` (generated), `README.md`, `adapters/cursor.md`, `commands/status.md`, `.writ/docs/model-tiers.md`, `scripts/eval-command-structure.py`, `scripts/tests/test_front_door.py`, `scripts/tests/test_why_command.py`.
- S3: `commands/writ.md`, `.writ/docs/prompting-guide.md`, `scripts/tests/test_front_door.py`, `scripts/tests/test_prompting_guide.py`, regenerated trees.
- S4: `commands/create-spec.md`, `scripts/tests/test_governor_enforcement.py`, `scripts/eval-command-structure.py`, `scripts/tests/test_why_command.py`, regenerated trees.
- Never: `commands/prototype.md`, `commands/implement-story.md`, `agents/*`, `skills/tdd-cycle/`, `commands/retro.md`, `commands/refresh-command.md`.

**Error Handling:**
- Subject not found → what was searched, one natural-language question.
- No `.writ/` / not a git repo / no notes → say so, continue with the remaining sources.
- MCP failure or none connected → named under Sources searched; never prompt to connect.
- Saved path exists → `-2`, `-3`; never overwrite.

**Integration Points:**
- `/writ` routes here; `/create-spec` Step 1.2 reads the handoff; `/create-adr` finds records in `.writ/research/`.
- Every command edit regenerates trees: `python3 scripts/gen-platform-trees.py`; `SKILL.md` via `bash scripts/gen-skill.sh`.

**Line Budget Constraints:** `commands/why.md` < 200 lines and < 24,960 bytes. Step 1.2 < 700 bytes; re-pin `KNOWN_OVER_BUDGET` with a dated comment.

---

## For Review Agents

**Acceptance Criteria:**
1. `commands/why.md` frontmatter and section set, `entry_level: high`, three exit criteria `[AC-1.1]`
2. Five tiers in order; code-is-not-evidence and lower-tier-on-conflict rules `[AC-1.2]`
3. Six steps; ledger before git before MCP; MCP only below `Stated`, never prompts `[AC-1.3]`
4. Saved record path and the fixed handoff heading with four subsections in order `[AC-1.4]`
5. Dogfood questions 1–3 answer at `Recorded` with the expected source `[AC-1.5]`
6. Manifest entry sorted; `--check` passes for both generators `[AC-2.1, AC-2.2]`
7. README, cursor tree (34), both status allowlists, model-tiers `high` (17) `[AC-2.3]`
8. Structure rows, `CURSOR_COUNT`, full suite and eval clean `[AC-2.4]`
9. `/writ` fifth row and Step 2 route `/why`, `/research` for outside questions; no "when it ships" `[AC-3.1, AC-3.2]`
10. Prompting guide route names `/why` `[AC-3.3]`
11. Step 1.2 placed between 1.1 and 1.3 and searches three places `[AC-4.1]`
12. Seam: same heading literal; four mappings with tier and citation `[AC-4.2]`
13. `KNOWN_OVER_BUDGET` re-pinned, step under 700 bytes, dated comment `[AC-4.3]`
14. Question 4 end to end: record saved, Preserve and Risk carried, no spec files written `[AC-4.4]`

**Business Rules:**
- Read-only except the saved record; no git notes, refs, commits, or ledger edits.
- A change follows only when the request or the user names one; otherwise nothing is written.
- Generated files are regenerated, never hand-edited.

**Experience Design:**
- Entry: `/why "<question>"`, `/why <path>[:<line>]`, or `/writ` routing.
- Happy path: anchor → ledger → git → answer → handoff when a change follows.
- Moment of truth: the answer quotes the ADR, rule, or DEV entry with its path.
- Feedback: first line names the tier; Sources searched shows what held nothing.
- Error: one question when the subject is missing; absent sources named, never fatal.

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest` passes, run alone.
2. Bash test loop passes; `bash scripts/eval.sh` reports 0 findings.
3. Both generator `--check` commands print `pass`.
4. Dogfood fixture: questions 1–3 at `Recorded`; question 4 carried into a draft contract.

**Shadow Paths to Verify:**
- **Happy path:** `Recorded` answer with ledger path.
- **Nil input:** `/why` alone asks one question.
- **Empty input:** unknown subject → searched terms plus one question.
- **Upstream error:** MCP failure named; answer stands on ledger and git.

**Edge Cases:**
- Stale ledger → claim keeps tier, stale line added.
- Conflicting sources → both shown, lower tier.
- Same-day same-slug record → `-2` suffix.

**Coverage Requirements:**
- Every acceptance criterion cited by a test or a recorded fixture result.

**Test Strategy:**
- Structural pytest checks on markdown (Python 3.9 stdlib); fixture runs recorded in What Was Built.

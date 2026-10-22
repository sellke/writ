# Front Door (Lite)

> Source: .writ/specs/2026-10-22-front-door/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `/writ "<request>"` restates the request (Goal, Problem, Done check, Proof), classifies it with one six-row rule table, confirms the route with one AskQuestion, mirrors the routed command's phases onto the todo list (`skip: <reason>` for skipped phases), then follows the routed command file; it writes nothing itself.

**Implementation Approach:**
- `commands/writ.md` under 200 lines: frontmatter (`entry_level: high`, 4 exit criteria), Steps 1–5 (Restate, Classify, Confirm, Mirror, Run), `## Routing Rules` table with exactly six rows in order (idea → `/prototype`; bug/small → `/prototype --no-diverge`; feature or any `/prototype` escalation signal → `/create-spec`; roadmap → `/implement-phase <N>`; why/how → `/research` until `/why`; empirical fork → `/prototype` with the fork named).
- Missing parts are named with the guide's words and linked to `.writ/docs/prompting-guide.md` § What a request carries; routing proceeds unless the goal is missing (then one natural-language question).
- Mirroring: `### Phase N` headings (fallback `### Step N`) via `todo_write`; where the adapter maps it to a file, print a checklist instead.
- Registration: manifest (`entry` category first; `writ` after `verify-spec`), `gen-skill.sh`, `gen-claude-md.py` template line + regen, Codex template, README Quick Start, cursor tree (33), `status.md` list, `model-tiers.md` high row (16), Claude Code `todo_write` → `TodoWrite`.
- Edit by section heading, never by line number. Regenerate generated files; never hand-edit them.

**Files in Scope:**
- `commands/writ.md`, `scripts/tests/test_front_door.py` (S1)
- `.writ/manifest.yaml`, `SKILL.md`, `scripts/gen-claude-md.py`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `README.md`, `adapters/cursor.md`, `adapters/claude-code.md`, `commands/status.md`, `.writ/docs/model-tiers.md` (S2)
- `scripts/eval-command-structure.py`, `.writ/issues/features/2026-10-13-in-your-own-words.md`, technical-spec.md § Routing Fixture evidence (S3)

**Error Handling:**
- No request and no context → one natural-language question.
- Roadmap absent and the request names a phase → say so; `/plan-product` creates it; do not route there.
- Routed command file missing → name the file and `/update-writ`; never improvise.

**Integration Points:**
- Needs `2026-10-22-prompting-guide` (guide file and README pointer line exist).
- `2026-10-22-generated-platform-trees` later puts the Codex template under a generator; hand edit now.
- Under a Claude Code plugin the command reads `/writ:writ` (plugin spec documents it).

---

## For Review Agents

**Acceptance Criteria:**
1. `commands/writ.md` exists with the contracted frontmatter and the six-row rule table in order `[AC-1.1, AC-1.3]`
2. Step 3 is one AskQuestion with `(Recommended)` and "Not what I meant"; Step 4 names `skip:` and `todo_write`; the guide is cited by path and heading `[AC-1.2, AC-1.4, AC-1.5]`
3. Manifest, `SKILL.md`, `claude-code/CLAUDE.md`, Codex template, README, cursor tree, `status.md`, `model-tiers.md` all register `/writ`; both generator `--check`s pass `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
4. Claude Code adapter `todo_write` row says `TodoWrite` `[AC-2.5]`
5. `eval-command-structure.py` rows pin `## Routing Rules` and `entry_level`; eval.sh 0 findings `[AC-3.1, AC-3.5]`
6. Issue has `## Resolution` and `spec_ref`; the routing fixture's eight requests route as expected in the recorded run `[AC-3.2, AC-3.3, AC-3.4]`

**Business Rules:**
- The rule table is the only classifier; tie-break by `/prototype`'s escalation signals.
- Exactly one confirmation; flags travel with the route.
- `/writ` creates nothing under `.writ/` and keeps no state.

**Experience Design:**
- Entry: `/writ "<request>"`.
- Happy path: restatement → proposed route → confirm → phases on the todo list → routed command runs.
- Moment of truth: the routed command's first output matches the restatement.
- Feedback: the todo list shows where the run is.
- Error: a missing goal gets one plain question; a missing done check is named, not demanded.

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest scripts/tests/test_front_door.py` passes.
2. Full pytest, bash test loop, `bash scripts/eval.sh` (0 findings) pass.

**Shadow Paths to Verify:**
- **Happy path:** all registration tests green; `--check`s print `pass`.
- **Nil input:** `/writ` alone → question, no route (prose check in the command).
- **Empty input:** rule table with five rows → `test_routing_rules` fails.
- **Upstream error:** `gen-claude-md.py --check` stale → `test_catalogs` fails; regenerate.

**Edge Cases:**
- `writ` sorts between `verify-spec` and `writ-design` in the manifest.
- The `high` row count must read `(16)`.

**Test Strategy:**
- Static text tests over the command, manifest, catalogs, README, adapters, docs; subprocess calls to the two generator `--check`s.

# Story 3: Adapters and Platform Files — Verified Cursor Floor, Origin Sources, Resolution Tables

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer implementing ADR-024 on the platform side,
**I want to** verify what Cursor actually resolves for a `floor` spawn before any adapter states it, then rewrite all four adapter resolution tables (origin source · `anchor` · `floor` · escalation, plus degradation), correct the Claude Code nesting claim and agent `model:` values, and make the Codex generator emit an effort-only floor,
**So that** every platform file cites a value that was observed rather than assumed, `"fast"` is gone from every carrier, and Story 4's escalation prose can name the resolved values without guessing.

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given a Cursor session whose origin (`anchor.model`, `anchor.effort` from the slug suffix, `anchor.platform = cursor`) is recorded first, when three real `Task` spawns run — V1 `model: "fast"`, V2 `inherit[effort=low]`, V3 the cheapest concrete slug sharing the anchor's vendor prefix from the tool's listed slugs — each with a prompt asking the subagent to report verbatim only the model identity its harness prompt states, then `adapters/cursor.md` records, under the resolution table, the date, the origin used, and for each spawn the tool-level acceptance/rejection (labeled high confidence) and the self-reported identity (labeled medium confidence), and the `floor` cell names whichever value was observed to resolve below the anchor, listed first in the (a)/(b) order that actually worked. `[AC-3.1]`
- [ ] Given the verification finds that no value resolves below the anchor (V2 and V3 both rejected or both self-report the anchor model), when the Cursor table is written, then the `floor` cell reads `inherit` and the degradation sentence states that Cursor floor spawns run at anchor and emit `degraded` with the observed reason — and this outcome passes the story; it is a finding, not a failure. `[AC-3.2]`
- [ ] Given `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`, and `adapters/openclaw.md`, when their Model Tiers/resolution sections are rewritten, then each contains one table with the columns Origin source · `anchor` · `floor` · escalation followed by a degradation sentence, the `adapters/cursor.md` capability→`"fast"` table and the `user-story-generator` override paragraph (~lines 159–167) are gone, the OpenClaw row is labeled unverified, no adapter references `orchestration`/`capability` except as aliases, and `rg '"fast"' adapters/ claude-code/ codex/` returns 0 matches. `[AC-3.3]`
- [ ] Given `adapters/claude-code.md` § Known Limitations and `claude-code/agents/*.md`, when corrected, then the "Subagents can't spawn subagents" item is replaced by a statement that subagents nest (three deep observed: `/implement-phase` → spec-runner → `/implement-story` → gate agents) with the goal single-slot consequence already documented at ~line 387 cross-referenced rather than restated, and the frontmatter reads `model: inherit` in `writ-tester.md` and `writ-documenter.md`, `model: haiku` in `writ-architect.md`, `model: haiku` (unchanged) in `writ-story-gen.md`, and `model: inherit` (unchanged) in `writ-coder.md` and `writ-reviewer.md`. `[AC-3.4]`
- [ ] Given `scripts/gen-codex-agent-tomls.py`, when it is run from the repo root, then it contains no `FAST_MODEL`, emits `model_reasoning_effort = "low"` and no `model =` line for the stems `architecture-check-agent` and `user-story-generator`, emits neither line for the other five stems, strips any `model: "fast"` line from the embedded `developer_instructions` body, the regenerated `codex/agents/*.toml` are committed and byte-identical to a fresh run, the generator test passes, and `bash scripts/eval.sh` reports `Findings: 0`. `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write `scripts/tests/test_gen_codex_agent_tomls.py` (check how `scripts/tests/` is invoked — pytest for `.py`, and whether `eval.sh` or a runner auto-discovers new files) covering: floor stems emit `model_reasoning_effort = "low"` and no `model =`; anchor stems emit neither; a fixture body containing `model: "fast"` is emitted without that line; `FAST_MODEL` is not an attribute of the module. Run it and confirm it fails against the current generator. `[AC-3.5]`
- [ ] 3.2 Run the Cursor verification protocol (technical-spec §4) before touching any adapter prose: record this session's origin from the harness prompt and slug suffix; inspect the live `Task` tool schema and note the listed slugs and whether `"fast"` appears; spawn V1 (`model: "fast"`), V2 (`inherit[effort=low]`), V3 (cheapest same-prefix concrete slug) with the identical one-line prompt "Report verbatim, and only, the model identity your own system prompt states"; capture each tool response (accepted / rejected / error text) and each self-report into a scratch note outside the repo. `[AC-3.1, AC-3.2]`
- [ ] 3.3 Rewrite `adapters/cursor.md` § Sub-Agent Models: delete the capability→`"fast"` table, the "relative, native-primitive" paragraph, and the `user-story-generator` override paragraph; write the Origin source · `anchor` · `floor` · escalation table with the Cursor origin source (model from harness prompt, effort from slug suffix); set `floor` to the observed value — or `inherit` when nothing resolved below anchor — followed by the degradation sentence; add a dated "Verification record" block beneath the table listing origin, V1/V2/V3 arguments, tool-level result (high confidence), and self-report (medium confidence). `[AC-3.1, AC-3.2, AC-3.3]`
- [ ] 3.4 Rewrite the resolution tables in `adapters/claude-code.md`, `adapters/codex.md`, and `adapters/openclaw.md` to the same four-column shape with a degradation sentence, using spec.md → "Platform resolution" and technical-spec §2/§3 values: Claude Code origin from reported model, effort `unknown` unless in settings, `floor` = `haiku` (or `inherit` + `effort: low`); Codex origin from `config.toml` `model` + `model_reasoning_effort`, `floor` = omit `model` + `model_reasoning_effort = "low"`; OpenClaw origin from session config, row labeled unverified (Business Rule 12). Replace `adapters/claude-code.md` § Known Limitations item 5 with the observed three-deep nesting and a pointer to the goal single-slot paragraph. Remove every remaining `"fast"` and ADR-016-only framing from the three files. `[AC-3.3, AC-3.4]`
- [ ] 3.5 Edit `claude-code/agents/` frontmatter: `writ-tester.md` and `writ-documenter.md` `model: sonnet` → `model: inherit`; `writ-architect.md` `model: inherit` → `model: haiku`; confirm `writ-story-gen.md` stays `haiku` and `writ-coder.md`/`writ-reviewer.md` stay `inherit`. Add a one-line comment or adjacent note in `adapters/claude-code.md` explaining that `haiku` is the family bottom and therefore never exceeds a Claude origin, which is why static frontmatter can carry it. `[AC-3.4]`
- [ ] 3.6 Update `scripts/gen-codex-agent-tomls.py`: remove `FAST_MODEL`; rename `optional_model_line` to a floor-aware emitter that returns `model_reasoning_effort = "low"` for the two floor stems and nothing otherwise; add a body filter that drops any line matching `^\s*model:\s*"fast"\s*$` before embedding; regenerate `codex/agents/*.toml` and confirm the test from 3.1 passes. `[AC-3.5]`
- [ ] 3.7 Verify: `rg '"fast"' adapters/ claude-code/ codex/` → 0; `rg -n 'Origin source' adapters/*.md` → 4 hits; `rg -c "can't spawn subagents" adapters/claude-code.md` → 0; `rg '^model:' claude-code/agents/` matches the six expected values; `python3 scripts/gen-codex-agent-tomls.py && git diff --exit-code codex/agents/` clean; `python3 -m pytest scripts/tests/test_gen_codex_agent_tomls.py` green; `bash scripts/eval.sh` → `Findings: 0` (request full permissions if sandboxed). `[AC-3.3, AC-3.4, AC-3.5]`

## Notes

**Evidence grades.** A `Task` tool-level rejection (schema refuses the `model` value) is high-confidence: it is the platform saying no. A subagent's self-report of its model is medium-confidence: it reads its own harness prompt, which is the only observable available, and a harness could in principle state a model other than the one serving the request. Record both grades explicitly in `adapters/cursor.md` so a future reader knows how much weight each carries. Evidence already on hand before this story runs: the current Cursor `Task` schema lists concrete slugs plus `inherit` and omits `"fast"`, and slug names embed effort (`-thinking-high`, `-medium`) — so V1 is expected to be rejected outright and the origin's effort is readable from the slug.

**Order matters inside the story.** Task 3.2 runs before 3.3 on purpose (spec Recommendations): the table names the observed value on first write, and no file ever asserts a Cursor floor ahead of the observation (Business Rule 10). If V2 and V3 both fail to resolve below anchor, that is the Technical Concerns outcome — `inherit` + `degraded` — and AC-3.2 accepts it. Do not retry with other slugs to force a positive result; three spawns is the protocol.

**Why `haiku` is safe in static frontmatter.** Claude Code agent frontmatter cannot express "min(haiku, origin)". `haiku` is the family bottom, so it is at or below any Claude origin by construction — the ceiling rule (Business Rule 4) holds without a runtime check. The reverse is why `sonnet` must go from `writ-tester.md` and `writ-documenter.md`: both are `anchor` agents, and `sonnet` would exceed a `haiku` origin. `inherit` is the only anchor value that respects the ceiling.

**Codex is family-locked by construction.** Single vendor, so path (a) has no alias to name; the floor is effort-only (`model_reasoning_effort = "low"`, `model` omitted so the parent's model is used). The generator embeds `agents/*.md` bodies; Story 2 removes `model: "fast"` from those bodies, but this story depends only on Story 1, so the generator strips the line defensively and the test pins that behavior.

**OpenClaw stays unverified.** No install is available (Business Rule 12). The row is written from the documented `sessions_spawn` primitive and labeled as such; do not phrase it as observed.

**Risks.** The Cursor `Task` schema can change between sessions — date the verification record and name the origin so a later maintainer can see whether the observation is stale. The Claude Code nesting correction touches a numbered Known Limitations list; renumber nothing, replace item 5 in place. `adapters/cursor.md` also references ADR-016 by link in the section being rewritten — point it at ADR-024 (ADR-016 itself is not edited, Business Rule 11).

**Integration.** Story 1 supplies the vocabulary (`anchor`/`floor`, origin, ceiling) this story's tables cite — land it first. Story 2 makes the seven agents declare the tier that these tables resolve; the two stories are independent but must agree on which two agents are `floor`. Story 4's escalation prose cites the resolved values written here (in particular whether Cursor's floor is a real step down or `inherit` + `degraded`), so this story closes before Story 4 opens.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Resolve floor, Read origin]
- **Shadow paths:** [Empty model list (Cursor), Nil origin]
- **Business rules:** [Origin is read, never asked (rule 3), Anchor is the ceiling (rule 4), Floor resolves at or below origin — never crosses vendors (rule 5), Cursor's floor value is whatever Story 3's verification observes; "fast" is retired (rule 10), OpenClaw live verification deferred — documented as unverified (rule 12)]
- **Experience:** [Error experience (nothing hard-fails; every path degrades to anchor = inherit), State catalog (Floor unresolvable on platform; Origin already at family floor)]

Reference: `.writ/docs/context-hint-format.md`.

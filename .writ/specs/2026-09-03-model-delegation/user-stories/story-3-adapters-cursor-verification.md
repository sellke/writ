# Story 3: Adapters and Platform Files — Verified Cursor Floor, Origin Sources, Resolution Tables

> **Status:** Completed ✅ (2026-09-03)
> **Commit:** 172825394048ce4a45ebd28d9cdd38e3c63e1633
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer implementing ADR-024 on the platform side,
**I want to** verify what Cursor actually resolves for a `floor` spawn before any adapter states it, then rewrite all four adapter resolution tables (origin source · `anchor` · `floor` · escalation, plus degradation), correct the Claude Code nesting claim and agent `model:` values, and make the Codex generator emit an effort-only floor,
**So that** every platform file cites a value that was observed rather than assumed, `"fast"` is gone from every carrier, and Story 4's escalation prose can name the resolved values without guessing.

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given a Cursor session whose origin (`anchor.model`, `anchor.effort` from the slug suffix, `anchor.platform = cursor`) is recorded first, when three real `Task` spawns run — V1 `model: "fast"`, V2 `inherit[effort=low]`, V3 the cheapest concrete slug sharing the anchor's vendor prefix from the tool's listed slugs — each with a prompt asking the subagent to report verbatim only the model identity its harness prompt states, then `adapters/cursor.md` records, under the resolution table, the date, the origin used, and for each spawn the tool-level acceptance/rejection (labeled high confidence) and the self-reported identity (labeled medium confidence), and the `floor` cell names whichever value was observed to resolve below the anchor, listed first in the (a)/(b) order that actually worked. `[AC-3.1]`
- [x] Given the verification finds that no value resolves below the anchor (V2 and V3 both rejected or both self-report the anchor model), when the Cursor table is written, then the `floor` cell reads `inherit` and the degradation sentence states that Cursor floor spawns run at anchor and emit `degraded` with the observed reason — and this outcome passes the story; it is a finding, not a failure. `[AC-3.2]`
- [x] Given `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`, and `adapters/openclaw.md`, when their Model Tiers/resolution sections are rewritten, then each contains one table with the columns Origin source · `anchor` · `floor` · escalation followed by a degradation sentence, the `adapters/cursor.md` capability→`"fast"` table and the `user-story-generator` override paragraph (~lines 159–167) are gone, the OpenClaw row is labeled unverified, no adapter references `orchestration`/`capability` except as aliases, and `rg '"fast"' adapters/ claude-code/ codex/` returns 0 matches. `[AC-3.3]`
- [x] Given `adapters/claude-code.md` § Known Limitations and `claude-code/agents/*.md`, when corrected, then the "Subagents can't spawn subagents" item is replaced by a statement that subagents nest (three deep observed: `/implement-phase` → spec-runner → `/implement-story` → gate agents) with the goal single-slot consequence already documented at ~line 387 cross-referenced rather than restated, and the frontmatter reads `model: inherit` in `writ-tester.md` and `writ-documenter.md`, `model: haiku` in `writ-architect.md`, `model: haiku` (unchanged) in `writ-story-gen.md`, and `model: inherit` (unchanged) in `writ-coder.md` and `writ-reviewer.md`. `[AC-3.4]`
- [x] Given `scripts/gen-codex-agent-tomls.py`, when it is run from the repo root, then it contains no `FAST_MODEL`, emits `model_reasoning_effort = "low"` and no `model =` line for the stems `architecture-check-agent` and `user-story-generator`, emits neither line for the other five stems, strips any `model: "fast"` line from the embedded `developer_instructions` body, the regenerated `codex/agents/*.toml` are committed and byte-identical to a fresh run, the generator test passes, and `bash scripts/eval.sh` reports `Findings: 0`. `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write `scripts/tests/test_gen_codex_agent_tomls.py` (check how `scripts/tests/` is invoked — pytest for `.py`, and whether `eval.sh` or a runner auto-discovers new files) covering: floor stems emit `model_reasoning_effort = "low"` and no `model =`; anchor stems emit neither; a fixture body containing `model: "fast"` is emitted without that line; `FAST_MODEL` is not an attribute of the module. Run it and confirm it fails against the current generator. `[AC-3.5]`
- [x] 3.2 Run the Cursor verification protocol (technical-spec §4) before touching any adapter prose: record this session's origin from the harness prompt and slug suffix; inspect the live `Task` tool schema and note the listed slugs and whether `"fast"` appears; spawn V1 (`model: "fast"`), V2 (`inherit[effort=low]`), V3 (cheapest same-prefix concrete slug) with the identical one-line prompt "Report verbatim, and only, the model identity your own system prompt states"; capture each tool response (accepted / rejected / error text) and each self-report into a scratch note outside the repo. `[AC-3.1, AC-3.2]`
- [x] 3.3 Rewrite `adapters/cursor.md` § Sub-Agent Models: delete the capability→`"fast"` table, the "relative, native-primitive" paragraph, and the `user-story-generator` override paragraph; write the Origin source · `anchor` · `floor` · escalation table with the Cursor origin source (model from harness prompt, effort from slug suffix); set `floor` to the observed value — or `inherit` when nothing resolved below anchor — followed by the degradation sentence; add a dated "Verification record" block beneath the table listing origin, V1/V2/V3 arguments, tool-level result (high confidence), and self-report (medium confidence). `[AC-3.1, AC-3.2, AC-3.3]`
- [x] 3.4 Rewrite the resolution tables in `adapters/claude-code.md`, `adapters/codex.md`, and `adapters/openclaw.md` to the same four-column shape with a degradation sentence, using spec.md → "Platform resolution" and technical-spec §2/§3 values: Claude Code origin from reported model, effort `unknown` unless in settings, `floor` = `haiku` (or `inherit` + `effort: low`); Codex origin from `config.toml` `model` + `model_reasoning_effort`, `floor` = omit `model` + `model_reasoning_effort = "low"`; OpenClaw origin from session config, row labeled unverified (Business Rule 12). Replace `adapters/claude-code.md` § Known Limitations item 5 with the observed three-deep nesting and a pointer to the goal single-slot paragraph. Remove every remaining `"fast"` and ADR-016-only framing from the three files. `[AC-3.3, AC-3.4]`
- [x] 3.5 Edit `claude-code/agents/` frontmatter: `writ-tester.md` and `writ-documenter.md` `model: sonnet` → `model: inherit`; `writ-architect.md` `model: inherit` → `model: haiku`; confirm `writ-story-gen.md` stays `haiku` and `writ-coder.md`/`writ-reviewer.md` stay `inherit`. Add a one-line comment or adjacent note in `adapters/claude-code.md` explaining that `haiku` is the family bottom and therefore never exceeds a Claude origin, which is why static frontmatter can carry it. `[AC-3.4]`
- [x] 3.6 Update `scripts/gen-codex-agent-tomls.py`: remove `FAST_MODEL`; rename `optional_model_line` to a floor-aware emitter that returns `model_reasoning_effort = "low"` for the two floor stems and nothing otherwise; add a body filter that drops any line matching `^\s*model:\s*"fast"\s*$` before embedding; regenerate `codex/agents/*.toml` and confirm the test from 3.1 passes. `[AC-3.5]`
- [x] 3.7 Verify: `rg '"fast"' adapters/ claude-code/ codex/` → 0; `rg -n 'Origin source' adapters/*.md` → 4 hits; `rg -c "can't spawn subagents" adapters/claude-code.md` → 0; `rg '^model:' claude-code/agents/` matches the six expected values; `python3 scripts/gen-codex-agent-tomls.py && git diff --exit-code codex/agents/` clean; `python3 -m pytest scripts/tests/test_gen_codex_agent_tomls.py` green; `bash scripts/eval.sh` → `Findings: 0` (request full permissions if sandboxed). `[AC-3.3, AC-3.4, AC-3.5]`

## Notes

**Evidence grades.** A `Task` tool-level rejection (schema refuses the `model` value) is high-confidence: it is the platform saying no. A subagent's self-report of its model is medium-confidence: it reads its own harness prompt, which is the only observable available, and a harness could in principle state a model other than the one serving the request. Record both grades explicitly in `adapters/cursor.md` so a future reader knows how much weight each carries. Evidence already on hand before this story runs: the current Cursor `Task` schema lists concrete slugs plus `inherit` and omits `"fast"`, and slug names embed effort (`-thinking-high`, `-medium`) — so V1 is expected to be rejected outright and the origin's effort is readable from the slug.

**Order matters inside the story.** Task 3.2 runs before 3.3 on purpose (spec Recommendations): the table names the observed value on first write, and no file ever asserts a Cursor floor ahead of the observation (Business Rule 10). If V2 and V3 both fail to resolve below anchor, that is the Technical Concerns outcome — `inherit` + `degraded` — and AC-3.2 accepts it. Do not retry with other slugs to force a positive result; three spawns is the protocol.

**Why `haiku` is safe in static frontmatter.** Claude Code agent frontmatter cannot express "min(haiku, origin)". `haiku` is the family bottom, so it is at or below any Claude origin by construction — the ceiling rule (Business Rule 4) holds without a runtime check. The reverse is why `sonnet` must go from `writ-tester.md` and `writ-documenter.md`: both are `anchor` agents, and `sonnet` would exceed a `haiku` origin. `inherit` is the only anchor value that respects the ceiling.

**Codex is family-locked by construction.** Single vendor, so path (a) has no alias to name; the floor is effort-only (`model_reasoning_effort = "low"`, `model` omitted so the parent's model is used). The generator embeds `agents/*.md` bodies; Story 2 removes `model: "fast"` from those bodies, but this story depends only on Story 1, so the generator strips the line defensively and the test pins that behavior.

**OpenClaw stays unverified.** No install is available (Business Rule 12). The row is written from the documented `sessions_spawn` primitive and labeled as such; do not phrase it as observed.

**Risks.** The Cursor `Task` schema can change between sessions — date the verification record and name the origin so a later maintainer can see whether the observation is stale. The Claude Code nesting correction touches a numbered Known Limitations list; renumber nothing, replace item 5 in place. `adapters/cursor.md` also references ADR-016 by link in the section being rewritten — point it at ADR-024 (ADR-016 itself is not edited, Business Rule 11).

**Integration.** Story 1 supplies the vocabulary (`anchor`/`floor`, origin, ceiling) this story's tables cite — land it first. Story 2 makes the seven agents declare the tier that these tables resolve; the two stories are independent but must agree on which two agents are `floor`. Story 4's escalation prose cites the resolved values written here (in particular whether Cursor's floor is a real step down or `inherit` + `degraded`), so this story closes before Story 4 opens.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Resolve floor, Read origin]
- **Shadow paths:** [Empty model list (Cursor), Nil origin]
- **Business rules:** [Origin is read, never asked (rule 3), Anchor is the ceiling (rule 4), Floor resolves at or below origin — never crosses vendors (rule 5), Cursor's floor value is whatever Story 3's verification observes; "fast" is retired (rule 10), OpenClaw live verification deferred — documented as unverified (rule 12)]
- **Experience:** [Error experience (nothing hard-fails; every path degrades to anchor = inherit), State catalog (Floor unresolvable on platform; Origin already at family floor)]

Reference: `.writ/docs/context-hint-format.md`.

## What Was Built

**Implementation Date:** 2026-09-03

### Files Created

1. **`scripts/tests/test_gen_codex_agent_tomls.py`** (~120 lines, `unittest`)
   - Imports the hyphenated generator by path (the `test_ac_trace.py` recipe); asserts against the TOML *header* only (everything before `developer_instructions =`) so embedded body text can never satisfy or falsely violate a header expectation. Five tests: floor stems emit `model_reasoning_effort = "low"`; anchor stems emit **no** `model_reasoning_effort` key at all (tightened at review from "no `low`"); no stem emits `model =`; a fixture body carrying `model: "fast"` is emitted without that line; `FAST_MODEL` is not a module attribute. Red against `HEAD`'s generator (6 failures), green after.

### Files Modified

- **`adapters/cursor.md`** § Sub-Agent Models — capability→`"fast"` table, "relative, native-primitive" paragraph, and `user-story-generator` override paragraph deleted. New four-column table (Origin source · `anchor` · `floor` · escalation) with the operational `floor` rule: **(a)** listed slug sharing the anchor's vendor prefix with effort suffix ≤ `anchor.effort`; **(b)** `inherit[effort=…]` — rejected by the tool, skip; **(c)** `inherit` — silent collapse only when the origin is the vendor's bottom tier, otherwise one `degraded(reason=no lower same-family slug listed)` line. Dated **Verification record — 2026-09-03**: origin `Claude Fable 5.1 / high @ cursor`; V1 `model: "fast"` accepted at tool level (high), self-reported the anchor (medium); V2 `inherit[effort=low]` rejected at tool level (high); V3 `claude-opus-5-thinking-high` accepted (high), self-reported Opus 5 (medium). ADR-016 links → ADR-024.
- **`adapters/claude-code.md`** § Model Selection — same table; `floor` = `model: haiku` with the "family bottom ≤ any Claude origin, so static frontmatter is safe" note; fallback `inherit` + `effort: low` (verified against current Claude Code subagent docs: `effort` is a real frontmatter key, `low|medium|high|xhigh|max`). Known Limitations item 5 replaced in place: subagents nest three deep (`/implement-phase` → spec-runner → `/implement-story` → gate agents), `/goal` single-slot cross-referenced not restated. Stale `sonnet` mentions removed.
- **`adapters/codex.md`** § Model Selection — same table; origin from `config.toml` `model` + `model_reasoning_effort` (`unknown` when absent); `floor` = omit `model`, `model_reasoning_effort = "low"`; agent→tier table matches `agents/*.md`. "model IDs are concrete" / "fast model aliases" text removed.
- **`adapters/openclaw.md`** — same table, row labeled **unverified** (Business Rule 12); `model: "fast"` examples → ADR-024 comment form; Gotcha 6 reworded.
- **`claude-code/agents/writ-tester.md`, `writ-documenter.md`** — `model: sonnet` → `inherit` (anchor must not exceed a `haiku` origin). **`writ-architect.md`** — `inherit` → `haiku`. `writ-story-gen.md` (`haiku`), `writ-coder.md`/`writ-reviewer.md` (`inherit`) unchanged.
- **`claude-code/CLAUDE.md:45`** — "(fast model, worktree)" → "(haiku, worktree)".
- **`scripts/gen-codex-agent-tomls.py`** — `FAST_MODEL` removed; `optional_model_line` → `floor_effort_line` (effort-only for `FLOOR_STEMS`, nothing otherwise, never a `model =` key); `strip_retired_fast_lines` applied to embedded bodies (anchored regex, bare or comma-terminated).
- **`codex/agents/*.toml`** (7) — regenerated; byte-stable on re-run. The large `user-story-generator.toml` hunk is Story 2's body edits landing in Codex for the first time.
- **`.writ/docs/model-tiers.md:123`** — Cursor `floor` cell filled from the observation.
- **`.writ/leanness-baseline.json`** — `surfaces.adapters` dated justifications: `lines` 1709, `chars` 93415 (notes 32 lines / ~4.7k chars of pre-existing unattributed growth since 2026-08-12).
- **`.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`** — second occurrence appended (importlib-by-path Python tests).

### Implementation Decisions

1. **Verification ran before any adapter prose** (Business Rule 10). `"fast"` turned out to be *accepted* by Cursor's `Task` schema but self-reports the anchor — both floor agents had likely been running at anchor on Cursor. Path (b) is rejected outright, so Cursor's floor is (a)-only.
2. **The Cursor `floor` cell states the rule, not the literal slug** (DEV-007). Slug lists are version-dependent; the dated record beneath names the observed value.
3. **Opus-origin Cursor sessions emit `degraded`, not a silent collapse** (DEV-008, review finding). Silent collapse is reserved for the vendor's bottom tier; when the vendor has lower tiers Cursor simply doesn't list, the limit is the platform's and ADR-024's success criterion ("or a `degraded` signal says why not") plus the ADR-025 ledger both need the signal.
4. **Codex floor is effort-only.** Single vendor, no alias to name; omitting `model` inherits the parent's, which is the only value that respects the ceiling.
5. **Claude Code `floor` = `haiku` in static frontmatter** — family bottom, so `min(haiku, origin)` needs no runtime check.

### Test Results

**Verification:** `python3 -m unittest discover -s scripts/tests -p 'test_gen_codex*'` 5/5 OK; same file vs `git show HEAD:scripts/gen-codex-agent-tomls.py` → 6 failures (red-first confirmed by reviewer); `python3 scripts/gen-codex-agent-tomls.py` → md5 of all seven TOMLs identical before/after; `rg '"fast"' adapters/ claude-code/ codex/` → 0; `rg -n 'Origin source' adapters/*.md` → 4; `rg -c "can't spawn subagents" adapters/claude-code.md` → 0; `rg '^model:' claude-code/agents/` → six expected values; `eval.sh` → Findings: 0 (pre-existing warning set unchanged).
- ✅ Mutation (reviewer, conceptual): `"medium"` effort → `test_floor_stems_emit_low_effort` fails; `FAST_MODEL` reintroduced → `test_no_fast_model_attribute` fails; filter removed → fixture test fails.
- ⚠️ `test-integrity.py authenticity` → `fail` / `test_imports_no_source` — importlib-by-path is invisible to the specifier extractor; carried on the red-first evidence, issue appended.
- ✅ Gate 5: docs updated in-story (`model-tiers.md`, four adapters, `CLAUDE.md`); `CHANGELOG.md` is `/release`'s.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Medium (DEV-008, resolved in-story)
- **Findings applied:** confidence wording at `cursor.md` degradation sentence and leanness text; anchor-stem test asserts no effort key of any value; `CLAUDE.md` retired-vocabulary line; DEV-008 clause.
- **Deferred:** a test pinning committed TOMLs == fresh `emit_toml` (byte-stability is verified manually per run); phrasing the Anthropic ladder as "read from the vendor's published tier names" rather than listing it inline.

### Drift

- **[DEV-007] Cursor `floor` cell states the rule, record names the slug** — Severity: Small
  - Spec said: AC-3.1 — "the `floor` cell names whichever value was observed to resolve below the anchor"
  - Reality: cell states rule (a) in the order that worked; `claude-opus-5-thinking-high` appears in the dated record and `model-tiers.md:123`
  - Resolution: Auto-amended `spec-lite.md`; logged
- **[DEV-008] Opus-origin Cursor session emits `degraded` rather than collapsing silently** — Severity: Medium
  - Spec said: technical-spec §8 — collapse without `degraded` when "origin at family floor (e.g. `haiku`/low)"; `degraded` for platform rejection / empty list
  - Reality: first draft treated "no lower same-prefix slug listed" as family floor; corrected at review to `degraded(reason=no lower same-family slug listed)` unless the origin is the vendor's bottom tier
  - Resolution: Adapter fixed; `spec-lite.md` amended to define "family floor" as the vendor's bottom tier; Story 4's escalation prose should cite this

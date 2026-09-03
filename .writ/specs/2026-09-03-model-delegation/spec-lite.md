# Model Delegation — Anchor, Floor, Origin, Escalation (Lite)

> Source: .writ/specs/2026-09-03-model-delegation/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Implement ADR-024 (+ Amendments A1–A3): `model_tier: anchor|floor` on agents only, derived by two questions; origin (model/effort/platform) read at entry and treated as the ceiling; family-locked floor at or below origin with a verified Cursor value; `entry_level: high|standard|any` on all 31 commands with a one-line non-blocking entry notice; floor results re-run once at anchor when they fail their check.

**Implementation Approach:**
- Contract text lives in `system-instructions.md` § Model Tiers, mirrored byte-identically into `cursor/writ.mdc` — never in `_preamble.md` (95-line cap).
- Old values `orchestration`/`capability` are lint-warned aliases for one minor release, then rejected.
- No new state file: origin is stamped on ADR-017 audit records and `escalated`/`degraded` lines only.
- `escalated`/`degraded` calls are documented no-ops until ADR-025's spec ships.
- Every path degrades to `anchor` = `inherit` (today's behavior).
- *(DEV-001–003, Story 1)* The entry notice renders its placeholders as inline code spans (no backslashes); `cursor/writ.mdc` is regenerated whole-file from `system-instructions.md` + its `## Self-Dogfooding` appendix (verify with `diff <(sed '/^## Self-Dogfooding/,$d' cursor/writ.mdc | sed '$d') system-instructions.md`); root-contract growth is recorded as a dated justification in `.writ/leanness-baseline.json`, never by raising `BASE_BYTE_CAP`.
- *(DEV-004–006, Story 2)* Agent template comments write `model_tier=floor` (equals sign) so `model_tier:` literal counts stay exact; `gen-skill.sh` reads `model_tier` only and renders a single `Tier` column (no `model` override column — ⚠️ Medium, technical-spec §1 amendment suggested); `README.md`, `AGENTS.md`, `.writ/docs/component-contract.md` describe agents as declaring `anchor|floor`.
- *(DEV-007–008, Story 3)* The Cursor `floor` cell states resolution rule (a) in the order that worked and the dated verification record beneath it names the observed slug (`claude-opus-5-thinking-high` from a Fable 5.1/high origin); `"fast"` is accepted by the `Task` schema but self-reports the anchor. "Origin at family floor" means the **vendor's bottom tier** (Anthropic: haiku/low) — that case collapses silently; when the vendor has lower tiers the platform's list does not expose (Opus on Cursor today), path (c) emits `degraded(reason=no lower same-family slug listed)` — ⚠️ Medium, Story 4 must cite this.

**Files in Scope:**
- `system-instructions.md`, `cursor/writ.mdc`, `.writ/docs/model-tiers.md` — rewrite § Model Tiers
- `scripts/lint-skill.sh` — `^(anchor|floor)$` + alias warning; `entry_level` grammar
- `agents/*.md` (7), `.writ/manifest.yaml` — rename tiers; drop `model: "fast"` and manifest `model:`
- `scripts/gen-skill.sh`, `SKILL.md` — make manifest `model` optional (eval gates on `--dry-run`); regenerate catalog
- `commands/new-command.md`, `commands/new-skill.md` — emit `entry_level`, stop emitting `model_tier`
- `adapters/{cursor,claude-code,codex,openclaw}.md` — resolution tables with Origin source column
- `claude-code/agents/*.md`, `scripts/gen-codex-agent-tomls.py`, `codex/agents/*.toml` — platform values
- `commands/create-spec.md` Step 2.6, `commands/implement-story.md` Gate 0 — escalation sites
- `commands/*.md` (31) — `entry_level:` frontmatter; `scripts/eval.sh` — pins + presence note

**Error Handling:**
- Floor unresolvable → run at anchor, one `degraded` line
- Origin unknown → floor path (b) uses `low`; entry check skipped
- Origin already at family floor → floor collapses to anchor, one line, no `degraded`

**Integration Points:**
- `/create-spec` Step 2.6 → structural validation → regenerate at anchor once
- `/implement-story` Gate 0 ABORT → confirm at anchor before AskQuestion; pair = one iteration

---

## For Review Agents

**Acceptance Criteria:**
1. § Model Tiers in `system-instructions.md` states two tiers, Q1/Q2, origin capture, ceiling, floor order (a)(b)(c), collapse rule, escalation-once, degradation; `cursor/writ.mdc` copy byte-identical `[AC-1.1, AC-1.2, AC-1.3]`
2. `lint-skill.sh` accepts `anchor`/`floor`, warns on `orchestration`/`capability` naming the replacement, fails on anything else; validates `entry_level` values `[AC-1.4, AC-1.5]`
3. `rg "model_tier:" agents/` → 7 hits all `anchor`/`floor`, matching the derivation table; `rg "model_tier" commands/ skills/` → 0; `rg '"fast"' agents/ adapters/ claude-code/ codex/` → 0 `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-3.3]`
4. Every adapter table has Origin source, `anchor`, `floor`, escalation, degradation; Cursor's floor cell cites the observed spawn result; Claude Code nesting claim corrected; `writ-tester`/`writ-documenter` → `inherit`, `writ-architect`/`writ-story-gen` → `haiku` `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
5. `create-spec.md` Step 2.6 and `implement-story.md` Gate 0 each state the escalate-once rule, the origin stamp, and that the pair counts as one iteration; `require_literal` pins exist for both `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
6. All 31 `commands/*.md` carry `entry_level:` matching the derivation table; the one-line notice rule appears once, in the root contract; nothing blocks or asks `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

**Business Rules:**
- Anchor is the ceiling — never resolve above `anchor.model`/`anchor.effort`
- Origin is read, never asked; surfaced to the user only by the entry notice
- No agent changes tier; no model ranking is maintained anywhere
- ADR-016 untouched beyond its supersession header

**Experience Design:**
- Entry: agent/command author edits frontmatter; end user runs commands unchanged
- Moment of truth: malformed floor story silently regenerated at anchor
- Feedback: one lint warning per alias; one entry line per session when below level
- Error: nothing hard-fails

---

## For Testing Agents

**Success Criteria:**
1. `bash scripts/eval.sh` → `Findings: 0` after every story; `bash scripts/lint-skill.sh` clean
2. `diff` of § Model Tiers between `system-instructions.md` and `cursor/writ.mdc` → empty
3. Blind derivation of all 7 agent tiers and 31 entry levels from the two questions matches the files

**Shadow Paths to Verify:**
- **Happy path:** floor agent resolves below anchor; result passes check; no lines emitted
- **Check fails:** one anchor re-run; anchor result used; `escalated` recorded once; iteration count +1 not +2
- **Unresolvable floor:** anchor used; exactly one `degraded` line
- **Alias in file:** lint exits 0 with a warning naming `anchor`/`floor`
- **Below entry level:** exactly one notice line; command output otherwise identical

**Edge Cases:**
- Origin at family floor (e.g. `haiku`/low) → no `degraded`, one collapse line
- Cursor `Task` rejects `inherit[effort=low]` → falls to same-prefix ID → falls to `inherit`
- `--recommend` runs → origin appears in `recommendation-log.md` entries

**Coverage Requirements:**
- `scripts/tests/` for lint grammar (aliases, rejection, `entry_level`) and generator output
- One real `/create-spec` with a forced-invalid story; one real Cursor spawn per candidate floor value

**Test Strategy:**
- Script tests for lint/generator; eval pins for command text; live spawns for Cursor resolution

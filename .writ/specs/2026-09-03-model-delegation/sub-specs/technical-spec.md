# Technical Spec — Model Delegation

> Parent: [`../spec.md`](../spec.md) · Decision: [ADR-024](../../../decision-records/adr-024-model-delegation.md) incl. § Amendments

This is a documentation/tooling spec: the deliverables are markdown contract text, frontmatter
values, one bash lint, one Python generator, and eval pins. No application code. The error map
below is included because the runtime behavior (spawn resolution, escalation) has failure
paths a user can hit.

## 1. Vocabulary and grammar

| Field | Carrier | Values | Enforcement |
|---|---|---|---|
| `model_tier` | agents only — `## Agent Configuration` fenced block (`visual-qa-agent.md`: `## Agent Specification`, `yaml` fence) and `.writ/manifest.yaml` agent entries | `anchor` \| `floor` (aliases `orchestration`→`anchor`, `capability`→`floor`, warned) | lint fails on any other value; runtime warns and runs at `anchor` |
| `model` | agents only | platform-specific concrete value | wins over `model_tier` unconditionally |
| `entry_level` | commands only — existing `---` frontmatter, after `outcome:` | `high` \| `standard` \| `any` | lint fails on any other value; eval notes (non-blocking) a missing field |

Skills carry neither field. `_preamble.md` carries neither field.

**Manifest `model` removal has a consumer.** `scripts/gen-skill.sh` line ~485 raises
`missing required field 'model'` per agent entry, and `scripts/eval.sh` line ~496 runs
`gen-skill.sh --dry-run` as a blocking check. Story 2 makes `model` optional in the generator
(read `model_tier` for the catalog's tier column; render `model` only when present as an
override) and regenerates `SKILL.md`. Tested by a generator case in `scripts/tests/`.

**Lint regex (`scripts/lint-skill.sh`, replacing lines ~253–284):**
```bash
# ---------- model_tier / entry_level value validation (ADR-024) ----------
if [[ "$line" =~ model_tier:[[:space:]]*([A-Za-z0-9-]+) ]]; then
  value="${BASH_REMATCH[1]}"
  case "$value" in
    anchor|floor) ;;
    orchestration) echo "⚠️ $file:$line_num: model_tier 'orchestration' is a deprecated alias — use 'anchor' (rejected after the next minor release)." ;;
    capability)    echo "⚠️ $file:$line_num: model_tier 'capability' is a deprecated alias — use 'floor' (rejected after the next minor release)." ;;
    *) echo "❌ $file:$line_num: model_tier '$value' is invalid. Use 'anchor' or 'floor'."; MODEL_TIER_VIOLATIONS=$((MODEL_TIER_VIOLATIONS + 1)) ;;
  esac
elif [[ "$line" =~ ^entry_level:[[:space:]]*([A-Za-z0-9-]+) ]]; then
  value="${BASH_REMATCH[1]}"
  [[ "$value" =~ ^(high|standard|any)$ ]] || { echo "❌ $file:$line_num: entry_level '$value' is invalid. Use 'high', 'standard' or 'any'."; MODEL_TIER_VIOLATIONS=$((MODEL_TIER_VIOLATIONS + 1)); }
fi
```
Aliases exit 0 (warning). The header comment names the release in which aliases become errors;
that release flips the two alias branches to the `*` branch — a two-line change.

## 2. Origin capture

Captured once at command entry by every command that spawns agents — `/create-spec` (Step 2.6),
`/implement-story` (Gates 0, 1, 3, 4, 4.5), and `/implement-phase`'s spec-runner (which passes
it down rather than re-reading). Read, never asked.

| Field | Cursor | Claude Code | Codex CLI | OpenClaw |
|---|---|---|---|---|
| `anchor.model` | model name the harness states in its prompt (e.g. "powered by …") | reported model name | `~/.codex/config.toml` → `model` (or project `.codex/config.toml`) | session config; `unknown` if absent |
| `anchor.effort` | suffix of the running slug (`-thinking-high` → `high`, `-medium` → `medium`, none → `unknown`) | `unknown` unless an effort setting is present in `.claude/settings*.json` | `config.toml` → `model_reasoning_effort` | `unknown` |
| `anchor.platform` | `cursor` | `claude-code` | `codex` | `openclaw` |

**Where it goes:** stamped as `origin=<model>/<effort>@<platform>` on (a) ADR-017 git-note
audit records written by `/implement-story`, (b) `recommendation-log.md` entries in
`--recommend` runs, (c) every `escalated`/`degraded` line. Never a new file under
`.writ/state/`. Never shown to the user except through the entry-level notice (§ 5).

## 3. Resolution algorithm (contract text, normative)

```
resolve(agent):
  if agent.model is set:              return agent.model            # concrete override wins
  tier = alias(agent.model_tier) or anchor                          # unknown → anchor + warn
  if tier == anchor:                  return platform.inherit
  # floor — never above origin, never cross-vendor
  if platform exposes a same-family tier strictly below anchor.model:   return it        # (a)
  if platform exposes an effort strictly below anchor.effort (or 'low' when unknown):
                                      return platform.inherit @ that effort              # (b)
  if origin is already at family floor:  note once "floor collapses to anchor"; return platform.inherit
  emit degraded(origin, reason);      return platform.inherit                            # (c)
```

Per-platform values of "same-family tier below anchor":

| Platform | (a) family tier | (b) effort form | Notes |
|---|---|---|---|
| Cursor | *verify:* cheapest concrete slug sharing the anchor's vendor prefix from the runtime `Task` model list | *verify:* `inherit[effort=low]` | order of (a)/(b) may swap based on Story 3's observation; whichever resolves is documented first |
| Claude Code | `haiku` (family bottom — always ≤ any Claude origin, so no collapse check needed) | `effort: low` in agent frontmatter | agent frontmatter is static; `haiku` chosen for the two floor agents |
| Codex CLI | none exposed as an alias — skip (a) | `model_reasoning_effort = "low"` with `model` omitted | single vendor → family-locked by construction |
| OpenClaw | operator-configured on `sessions_spawn` | none | unverified — documented as such |

## 4. Cursor verification protocol (Story 3, run before editing adapter prose)

Three real `Task` spawns from one Cursor session whose origin is known (record it):

| # | `model` argument | Expected if honored | Observe |
|---|---|---|---|
| V1 | `"fast"` | rejected or silently anchor | tool response / subagent self-report |
| V2 | `inherit[effort=low]` | accepted, same model, lower effort | tool response accepts? subagent reports same model |
| V3 | cheapest concrete slug with the anchor's vendor prefix from the tool's listed slugs | accepted, that model | subagent reports the slug's model |

Each subagent's prompt asks it to report, verbatim, the model identity its own harness prompt
states, and nothing else. Self-report is the only observable available and is treated as
medium-confidence evidence; a tool-level rejection is high-confidence. Results are recorded in
`adapters/cursor.md` under the resolution table with the date and the origin used. Evidence on
hand before Story 3 runs: the current Cursor `Task` tool schema enumerates concrete slugs plus
`inherit` and does not list `"fast"`.

## 5. Entry-level check (contract text, normative)

Placed in `system-instructions.md` § Model Tiers; commands do not repeat it.

> At entry, compare the captured origin against this command's `entry_level`. If the origin
> is below it, print exactly one line and continue:
> `This command expects \`<level>\` entry; you're running \`<model>/<effort>\`. Floor-tier retries cannot escalate above this. Consider re-running at a higher thinking level.`
> Print it at most once per session. Never ask. If the origin is `unknown`, skip the check.
> "Below" is your own assessment against: `high` — a frontier-class model of its family at a
> non-minimal thinking level; `standard` — a non-smallest model, or medium-plus effort;
> `any` — nothing.

Derivation of the 31 values is the table in `spec.md` → *`entry_level` derivation applied*;
Story 5's first task is to confirm it with the maintainer before writing.

## 6. Escalation sites (Story 4)

**`/create-spec` Step 2.6 — story structural validation.** After the parallel generators
return, validate each `story-*.md`: 3–5 criteria each with a trailing `` `[AC-N.M]` `` tag,
`> **AC IDs assigned through:**` marker equal to the highest ID, 5–7 tasks each citing ≥1 ID,
`Status: Not Started`. The check is `python3 scripts/ac-trace.py check --spec <folder>` plus
the count bounds. A failing story is regenerated **once** at `anchor` (same prompt, `model`
= platform `inherit`); the anchor result replaces the floor result regardless of whether it
also fails (a second failure is reported to the user as today). Emit
`escalated(agent=user-story-generator, site=create-spec.2.6, origin=…)`.

**`/implement-story` Gate 0 — ABORT confirmation.** When `architecture-check-agent` returns
**ABORT**, re-run the check **once** at `anchor` with the identical prompt before presenting
findings. The anchor verdict stands: PROCEED/CAUTION → continue as that verdict, no user
interruption; ABORT → present findings and ask, as today. Emit
`escalated(agent=architecture-check-agent, site=implement-story.gate0, origin=…)`.

**Iteration accounting.** Both sites state: *the floor attempt and its anchor re-run count as
one attempt against `loop.max_iterations`.* `eval.sh` gains `require_literal` pins for that
sentence in both command files and for the two `escalated(` literals.

**Signal calls before ADR-025 ships:** written as the literal line the ADR-025 spec will
implement, prefixed *"(no-op until ADR-025 Story 1)"*. The ADR-025 spec removes the prefix.

## 7. Platform files (Story 3)

| File | Change |
|---|---|
| `claude-code/agents/writ-tester.md`, `writ-documenter.md` | `model: sonnet` → `model: inherit` (anchor tier; `sonnet` can exceed a `haiku` origin) |
| `claude-code/agents/writ-architect.md` | `model: inherit` → `model: haiku` (floor tier) |
| `claude-code/agents/writ-story-gen.md` | already `haiku` — unchanged |
| `claude-code/agents/writ-coder.md`, `writ-reviewer.md` | already `inherit` — unchanged |
| `scripts/gen-codex-agent-tomls.py` | drop `FAST_MODEL`; for the two floor stems emit `model_reasoning_effort = "low"` and no `model`; strip the `model: "fast"` line from the embedded agent body; regenerate `codex/agents/*.toml` |
| `adapters/claude-code.md` § Known Limitations | replace "subagents cannot spawn subagents" with the observed three-deep nesting and its goal single-slot consequence |

## 8. Error & Rescue Map

| Operation | Failure | User sees | Rescue |
|---|---|---|---|
| Resolve floor | platform rejects the value | nothing (audit: `degraded`) | run at `inherit` |
| Resolve floor | origin at family floor | one collapse line | run at `inherit`, no `degraded` |
| Read origin | harness reveals nothing | nothing | `unknown`; effort path uses `low`; entry check skipped |
| Story validation | floor story malformed | nothing on first failure | regenerate once at anchor |
| Story validation | anchor story also malformed | today's error report | user fixes/re-runs |
| Gate 0 | floor ABORT | nothing if anchor clears it | anchor re-run |
| Gate 0 | anchor ABORT | AskQuestion (today's) | user decides |
| Lint | alias value | ⚠️ warning naming replacement | exit 0 |
| Lint | unknown value | ❌ finding | exit 1 |
| Entry check | origin below level | one notice line | continue |

### Shadow paths
- **Happy:** floor resolves; check passes; zero lines emitted; audit carries `origin=`.
- **Nil origin:** `unknown` everywhere; behavior identical to today plus `degraded` when floor
  cannot resolve.
- **Empty model list (Cursor):** `Task` offers only `inherit` → path (c), `degraded`.
- **Upstream error:** platform spawn fails outright → today's error path; escalation is not
  attempted on a spawn *error*, only on a returned result that fails its check.

## 9. Eval and test surface

- `scripts/eval.sh`: `require_literal` pins (§ 6); a non-blocking `add_note` when any
  `commands/*.md` other than `_preamble.md` lacks `entry_level:`; existing `prime-directive-sync`
  and mirror checks cover § Model Tiers.
- `scripts/tests/`: lint cases — `anchor`, `floor` (pass), `orchestration`, `capability` (warn,
  exit 0), `fast`/`n-1` (fail), `entry_level: high|standard|any` (pass), `entry_level: max`
  (fail); generator case — floor stems emit `model_reasoning_effort = "low"` and no `model`.
- Live: three Cursor spawns (§ 4); one `/create-spec` run with a forced-invalid story (§ 6).

## 10. Story traceability

| Story | Sections |
|---|---|
| 1 Contract | §1 grammar (contract prose + lint aliases), §2, §3, §5 text |
| 2 Agents/manifest/scaffolders | §1 carriers, `model:` removal incl. `gen-skill.sh` tolerance + `SKILL.md` regeneration |
| 3 Adapters + verification | §2 table, §3 per-platform, §4, §7 |
| 4 Escalation | §6, §9 pins |
| 5 Entry-level | §1 `entry_level` lint, §5 declarations, §9 note |

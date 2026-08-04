# Technical Specification — Model-Tier Delegation

> Spec: `.writ/specs/2026-07-10-model-tier-delegation/spec.md`
> Type: Framework convention + adapter documentation (no application code)

## 1. Frontmatter Schema

### `model_tier` (new field)

Additive, optional, backward-compatible. Applies to agents (enforced), commands and skills (advisory).

**Carrier per file type (verified against the repo — "frontmatter" is the umbrella term, not a literal `---` block everywhere):**

| File type | Carrier | Verified state |
|---|---|---|
| Skills (`skills/*/SKILL.md`) | Real `---` YAML frontmatter | Confirmed present (`name`, `description`, `status`, etc.) |
| Agents (`agents/*.md`) | Existing fenced **Agent Configuration** block (`subagent_type:`, `model:`, `readonly:`) | Confirmed — no `---` header exists; `model_tier:` is a new line in this block |
| Commands (`commands/*.md`) | **No config-block mechanism exists.** Advisory tier ships as a prose note | Confirmed — 0/31 command files carry a `---` block |

```yaml
# --- Agent Configuration block (ENFORCED at spawn) — agents/*.md ---
model_tier: orchestration     # resolves to anchor / inherit
# or
model_tier: capability        # resolves to floor / fast

# --- Reserved ordinal-offset form (documented, NOT resolved beyond 2-band) ---
model_tier: -1                # anchor minus one band, clamped to floor (reserve-only)

# --- Skill frontmatter (ADVISORY ONLY) ---
model_tier: orchestration     # advisory: documents assumed execution weight; not selectable
```

```markdown
<!-- Command prose note (ADVISORY ONLY — no frontmatter mechanism exists for commands) -->
> **Model tier (advisory only):** orchestration — commands run at the user's session model.
```

**Rules:**

- **Allowed values:** `orchestration`, `capability`, or a negative integer ordinal offset (reserved). Anything else is a lint error.
- **Default (unset):** inherit parent/default — identical to today's behavior.
- **Precedence:** an explicit concrete `model:` (where a platform needs one, e.g. Codex IDs) overrides `model_tier:`. `model_tier:` is portable intent; `model:` is concrete override.
- **Enforcement boundary:** only agent `model_tier:` is applied at spawn. Command/skill `model_tier:` is documentation — Writ cannot select a model for a command (user's session model) or a skill (loaded into caller's context).

### `manifest.yaml` agent entries

```yaml
agents:
  - name: user-story-generator
    file: agents/user-story-generator.md
    purpose: "..."
    model_tier: capability      # portable intent (replaces/augments `model: fast`)
    # model: gpt-5-mini         # optional concrete override where a platform needs it
```

Story 2 documents whether `model:` is removed in favor of `model_tier:` or retained alongside. Recommendation: retain `model:` only where an adapter currently requires a concrete ID (Codex table); elsewhere `model_tier:` is sufficient and `model:` is dropped.

## 2. Tier → Concrete Model Resolution (2-band, native)

| Tier | Cursor (`Task({ model })`) | Codex (TOML `model`) | OpenClaw (`sessions_spawn`) | Claude Code (agent frontmatter `model`) |
|---|---|---|---|---|
| `orchestration` | `inherit` (runs at anchor) | omit / inherit | omit `model` param | `inherit` |
| `capability` | `"fast"` (floor) | concrete mini ID (e.g. `gpt-5-mini`) | `model` param → cheaper model | concrete name (e.g. `haiku`, or `sonnet` where more nuance is needed) |
| unset | `inherit` | omit | omit | `inherit` |
| reserved ordinal `-N` | clamp: `inherit` if 0, else `"fast"` | clamp to mini | clamp to cheaper | clamp to `haiku` |

**Why native, not a ranking:** Cursor's `inherit`/`fast` are relative primitives the platform resolves itself — Writ ships zero model names for Cursor/OpenClaw. Codex and Claude Code both require concrete names today (mini ID; `haiku`/`sonnet`), so each lives in its own adapter's table (Claude Code's already exists in § Model Selection) and is the one place a name can rot; each is isolated to one table and flagged for verification (Codex already notes `/model` verification; Claude Code gets the same caveat).

## 3. Graceful Degradation

Mirrors `required_skills:` handling — warn, never hard-fail.

| Condition | Behavior |
|---|---|
| `model_tier` unset | Resolve to parent/default (inherit). No warning. |
| `model_tier: capability` but platform exposes no fast/cheaper model | Warn: "capability tier unavailable on <platform>; running at parent model." Fall back to inherit. |
| `model_tier` value unrecognized at resolution time | Warn: "unknown model_tier '<value>'; running at parent model." Fall back to inherit. |
| Reserved ordinal offset beyond available bands | Clamp to floor (or inherit if platform has one band); no warning (documented clamp). |
| Both `model:` and `model_tier:` set | Use `model:` (concrete override wins). No warning. |

## 4. Shadow Paths (resolution behavior)

| Flow | Happy Path | Nil (unset) | Empty (advisory only) | Upstream Error (unhonorable) |
|---|---|---|---|---|
| Agent spawn | `orchestration`→inherit, `capability`→fast | inherit parent, silent | n/a (agents enforce) | warn + inherit |
| Command run | n/a (session model) | runs at session model | advisory tier documented, unused | n/a |
| Skill load | n/a (caller context) | runs at caller model | advisory tier documented, unused | n/a |

## 5. Lint Validation (Story 4)

Extend `scripts/lint-skill.sh` (and the shared frontmatter validation used by `/new-skill` / `/refresh-command` / `/new-command`):

- **Value check:** `model_tier` must match `^(orchestration|capability|-[0-9]+)$` wherever it appears (skill frontmatter, agent Agent Configuration block, or a command's prose note). Otherwise reject with:
  `model_tier '<value>' is invalid. Use 'orchestration', 'capability', or a reserved negative offset (e.g. -1).`
- **Advisory reminder (commands/skills only):** if a skill declares `model_tier` in frontmatter, or a command documents it as a prose note, the scaffold inserts an adjacent `# advisory only — commands/skills run at the session/caller model` comment/label. Lint does not fail on its absence (advisory), but `/new-*` always writes it.
- **Manifest/config consistency (agents):** Story 2 DoD verifies each agent's Agent Configuration block `model_tier` matches its `manifest.yaml` entry (manual `rg`/diff; no test framework).

## 6. Documentation Surfaces

| File | Change |
|---|---|
| `system-instructions.md` | New/extended section documenting `model_tier` (two tiers, advisory-for-commands/skills, reserved ordinal offsets, graceful degradation), placed near the `required_skills:` convention |
| `cursor/writ.mdc` | Byte-identical mirror of the tiering content (Phase 4 parity discipline) |
| `adapters/cursor.md` | § Sub-Agent Models gains the tier→native table + degradation rule |
| `adapters/codex.md` | Agents↔TOML table framed as tier resolution; degradation rule |
| `adapters/openclaw.md` | Spawning section gains tier→`model` param mapping + degradation rule |
| `adapters/claude-code.md` | § Model Selection reframed as tier resolution (`capability`→`haiku`/`sonnet`, `orchestration`→`inherit`); degradation rule |
| `.writ/decision-records/adr-016-model-tier-delegation.md` | New ADR — decision + alternatives |
| `.writ/docs/model-tiers.md` | New user-facing explainer |
| `README.md`, `AGENTS.md` | Reference the convention where model/agent behavior is described |

## 7. Backward Compatibility

- Agents with no `model_tier` behave exactly as today.
- Existing `model:` values continue to work (precedence over `model_tier`).
- The mapping in Story 2 is chosen so every agent resolves to the **same concrete model it uses today** — this spec changes vocabulary and documentation, not runtime model selection.
- Reserved ordinal offsets are documented but inert (2-band resolution), so no consumer can depend on unbuilt behavior.

## 8. Explicitly Not Built (deferred)

- Refreshable per-platform model-family ranking; N-step (>2-band) resolution.
- Runtime anchor-model detection beyond native `inherit`.
- Quality-regression eval harness for capability-tier output.
- Introducing a real frontmatter/config-block mechanism for commands (advisory tier ships as a prose note instead).

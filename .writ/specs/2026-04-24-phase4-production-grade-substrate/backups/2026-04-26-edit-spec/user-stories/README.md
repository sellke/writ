# Phase 4 — Production-Grade Substrate — User Stories

> **Spec:** `.writ/specs/2026-04-24-phase4-production-grade-substrate/`
> **Total Stories:** 5
> **Status:** In Progress (local implementation complete; Story 1 follow-up dogfood and Story 5 remote CI smoke pending)
> **Total Effort:** ~5–9 days of focused work (per roadmap pacing discipline)

## Stories Overview

| # | Story | Status | Priority | Effort | Tasks | Progress |
|---|-------|--------|----------|--------|-------|----------|
| 1 | [Knowledge Ledger v1](story-1-knowledge-ledger.md) | In Progress | High | S–M (~2–4 days) | 8 | 8/8 |
| 2 | [Spec Frontmatter `owner:` Field](story-2-spec-owner-field.md) | Completed ✅ | Medium | XS (~2 hours) | 7 | 7/7 |
| 3 | [SKILL.md Template Generation](story-3-skill-md-generation.md) | Completed ✅ | High | S (~1–2 days) | 7 | 7/7 |
| 4 | [Preamble Enforcement for Commands](story-4-preamble-enforcement.md) | Completed ✅ | Medium-High | S (~1 day) | 7 | 7/7 |
| 5 | [Eval Tier 1 (Static Checks)](story-5-eval-tier-1.md) | In Progress | High | S (~1 day + 0.5 day triage) | 8 | 7/8 |

**Total Tasks:** 37 (36 complete, 1 remote CI smoke remaining; Story 1 follow-up dogfood remains outside task count)

## Dependencies

```
Story 1 (Knowledge Ledger)     Story 2 (Owner Field)     Story 3 (SKILL.md Gen)
        ↓                              ↓                          ↓
        └──────────────────────────────┴────────┬─────────────────┘
                                                ↓
                                       Story 4 (Preamble Enforcement)
                                                ↓
                                       Story 5 (Eval Tier 1)
```

- **Stories 1, 2, 3 are independent** — can run in parallel
- **Story 4 depends on Story 3** — preamble enforcement iterates over the manifest's command list
- **Story 5 depends on Stories 2, 3, 4** — its 8 checks reference the owner field (Story 2), the manifest (Story 3), and preamble references (Story 4)

> **Phase-level entry condition (per roadmap):** Phase 1 features have been materially dogfooded and are stable enough to build on; dogfooding continues indefinitely as an operating practice. Independent of story-level dependencies.

## Story Descriptions

### Story 1: Knowledge Ledger v1

Stand up `.writ/knowledge/{decisions,conventions,glossary,lessons}/` with a frontmatter schema, a `/knowledge` authoring command (modeled on `/create-issue`), an agent context-loading hook in `/implement-story` Step 2, and 5–10 backfilled high-value entries. Implements ADR-005's substrate decision.

**Key deliverables:**
- `.writ/knowledge/` directory + `README.md` with "what goes where" decision tree
- `commands/knowledge.md` — terse authoring command
- Knowledge-loading hook in `commands/implement-story.md` Step 2
- `knowledge_context` parameter added to coding/architecture-check/review agents
- ≥5 backfilled entries across ≥2 categories
- Adapter doc updates

### Story 2: Spec Frontmatter `owner:` Field

Tiny but high-value substrate move. Adds `owner:` to the spec frontmatter, defaulting to `git config user.name`. Surfaced by `/status` and `/verify-spec`. New specs only — no legacy migration. The seed of the team-readiness pattern at zero solo cost (per ADR-007).

**Key deliverables:**
- `owner:` field in `commands/create-spec.md` template
- Check 8 in `commands/verify-spec.md` (warn-not-fail; legacy specs exempt)
- Owner column in `commands/status.md` active-specs section
- Schema doc update

### Story 3: SKILL.md Template Generation

Eliminates the existing drift risk between `commands/`, `agents/`, and `SKILL.md`. Single source of truth: `.writ/manifest.yaml`. Generator: `scripts/gen-skill.sh`. CI gate: `--check` exits 1 on drift. `yq` preferred; pure-bash fallback for portability.

**Key deliverables:**
- `.writ/manifest.yaml` enumerating all commands and agents
- `scripts/gen-skill.sh` (default / `--dry-run` / `--check`)
- Regenerated `SKILL.md` with "do not edit by hand" header
- `.github/workflows/eval.yml` (introduces the workflow file Story 5 extends)

### Story 4: Preamble Enforcement for Commands

`commands/_preamble.md` holds standing instructions (Plan Mode integrity, file org, tool selection, knowledge context, adapter neutrality). Every command file ends with a "## References" section linking to the preamble. Static reference, not runtime injection — honest about platform constraints; eval (Story 5) enforces.

**Key deliverables:**
- `commands/_preamble.md` (≤80 lines)
- "## References" section appended/augmented in every `commands/*.md` (excluding `_*.md`)
- Same in applicable `agents/*.md` files
- Adapter doc updates explaining preamble loading per platform

### Story 5: Eval Tier 1 (Static Checks)

`scripts/eval.sh` runs 8 cheap static checks (required sections, anti-sycophancy phrasing, prime-directive sync between `system-instructions.md` and `cursor/writ.mdc`, broken refs, length sanity, manifest well-formedness, preamble references, owner-field presence). Wired into CI. Auto-fix supported for `preamble`. Pre-existing violations triaged: fix or `eval-exempt` with tracking issue.

**Key deliverables:**
- `scripts/eval.sh` runner (default / `--check=NAME` / `--report=PATH` / `--fix`)
- 8 check implementations
- CI gate extension in `.github/workflows/eval.yml`
- Anti-sycophancy phrase list as extensible data file
- Triage of pre-existing violations

## Implementation Notes

### Recommended Order

1. **Stories 1, 2, 3 in parallel** (foundation layer; mutually independent)
2. **Story 4** after Story 3 completes (needs the manifest)
3. **Story 5** after Stories 2, 3, 4 complete (validates the work)

A solo maintainer pacing it sequentially (per the roadmap discipline note) might prefer: Story 2 first (XS warmup) → Story 3 → Story 4 → Story 5 → Story 1 (longest, requires deepest thinking). The dependency graph permits either order.

### Success Criteria (Spec-Level)

From the roadmap and ADR-005:
- ≥10 knowledge entries across ≥2 categories within 30 days post-ship
- `gen-skill.sh --check` clean in CI for 60 days post-ship without manual SKILL.md edit
- Eval Tier 1 catches ≥1 regression before release within first 60 days
- `owner:` field on 100% of post-ship specs; legacy specs reported as "legacy" without blocking
- Agent loads relevant `.writ/knowledge/` entry on a follow-up task without prompt-side mention
- Zero external dependencies introduced

### Dual-Use Test (per ADR-007)

Each story's "Notes" section captures its dual-use justification. Summary:

| Story | Solo benefit | Team-readiness benefit |
|---|---|---|
| 1 | Agents stop re-deriving context; future-self orients in <30 min | Shared knowledge substrate is the foundation any team-collab feature depends on |
| 2 | Own name on every spec; tiny psychological signal | Field is already there the moment a teammate arrives — zero migration cost |
| 3 | SKILL.md drift is already a real risk; eval gate eliminates it | Manifest becomes the single truth a teammate can trust; iteration surface for Story 4 |
| 4 | Standing rules don't drift between commands | Single edit propagates to every command without per-command code review burden |
| 5 | Cheap quality floor; ship faster with confidence | Every contributor's PR held to the same bar by the same script — no maintainer-noticed variance |

### Validation Plan

- **Story 1:** Self-dogfood — ship a follow-up feature where the agent loads a backfilled entry without prompt-side mention
- **Story 2:** Self-dogfood — this very spec shows `owner: @adam` in frontmatter and is surfaced correctly by `/status` and `/verify-spec`
- **Story 3:** Deliberate manifest edit + `--check` failure verification in a test branch
- **Story 4:** Manual smoke test under Cursor (dogfood platform) confirming preamble loads
- **Story 5:** Deliberate violation in test branch → CI fails → revert → CI passes

### Out-of-Scope Reminders (per spec.md → Scope Boundaries)

These belong to Phase 5 or Beyond Phase 5, **not** this spec:
- `/audit` command, `/lessons` micro-command, per-story scorecards, drift-to-lesson auto-promotion
- Spec `dependencies:` block, status board across `.writ/specs/`
- `/review-spec`, multi-developer drift reconciliation, multi-repo orchestration
- Eval Tier 2 (LLM-as-judge), Tier 3 (E2E)
- SQLite index over `.writ/knowledge/`
- Migration of legacy specs to add `owner:`

If any story's discovery surfaces work that belongs above, it's spec creep — flag, don't push through.

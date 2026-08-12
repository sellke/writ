# Story 2: Deprecate the Ordinal-Offset Reservation

> **Status:** Complete
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer rewriting the `model_tier` schema during Phase 10
**I want to** the reserved negative ordinal offsets (`-1`, `-2`, …) removed from the schema now, ahead of their 2026-10-16 review trigger
**So that** the tier vocabulary is exactly the two bands any adapter actually resolves, and the same paragraphs are not rewritten twice in one phase

## Acceptance Criteria

- [x] Given `system-instructions.md` § Model Tiers, when the schema is read, then allowed values are `orchestration` and `capability` only — regex `^(orchestration|capability)$` — with no reserved negative ordinal offset, no clamp-to-floor table row, no "Reserved ordinal offsets … are reserve-only" paragraph, and no 2026-10-16 review-trigger blockquote.
- [x] Given `scripts/lint-skill.sh`, when it lints a file declaring `model_tier: orchestration` or `model_tier: capability`, then it passes; and when it lints a file declaring `model_tier: -1`, then it reports an invalid-value violation.
- [x] Given the literals `-[0-9]+` (as a `model_tier` schema branch), `reserve-only` (in the ordinal context), `Clamp to floor`, `ordinal offset`, and `2026-10-16`, when the active surface is grepped (`system-instructions.md`, `cursor/writ.mdc`, `commands/`, `agents/`, `adapters/`, `scripts/`, `.writ/docs/`, `.writ/manifest.yaml`), then zero hits relating to the `model_tier` ordinal reservation remain.
- [x] Given the same literals grepped across `.writ/decision-records/` (ADR-016 in particular), `.writ/specs/archive/`, `.writ/research/`, and `CHANGELOG.md`, when compared to pre-story hit counts, then every count is unchanged.
- [x] Given the graceful-degradation contract, when a `model_tier: -1` is encountered after this change, then the existing "unrecognized value → warn, fall back to inherit" row covers it — no new failure path, no hard failure, and the enforcement boundary (agents enforced at spawn; commands and skills advisory) and precedence rule (`model:` beats `model_tier:`) are unchanged.
- [x] Given `system-instructions.md` and `cursor/writ.mdc` after the edit, when the § Model Tiers section of each is compared line for line, then the two are identical.
- [x] Given the full validation suite, when `bash scripts/eval.sh` runs, then it reports `Findings: 0` with no new `eval-exempt:` marker introduced by this story.

## Implementation Tasks

- [x] 2.1 Re-confirm zero consumers before removing anything: grep `model_tier` across `agents/*.md`, `skills/*/SKILL.md`, `commands/*.md`, and `.writ/manifest.yaml`. Expected: every declared value is `orchestration` or `capability`; the only `-N` occurrences are the schema definitions themselves. If a real ordinal consumer exists, stop and surface it (Business Rule 6) rather than proceeding.
- [x] 2.2 Remove the four constructs from `system-instructions.md` § Model Tiers: the `-[0-9]+` schema branch and its "reserved negative ordinal offset (`-N`)" prose (line 285), the "Reserved ordinal offset beyond available bands / Clamp to floor" table row (line 295), the "Reserved ordinal offsets … are reserve-only" paragraph (line 298), and the 2026-10-16 review-trigger blockquote (line 300). Locate by literal — Story 1 will have shifted these lines.
- [x] 2.3 Mirror the identical removals into `cursor/writ.mdc`, then diff the § Model Tiers section of both files. This section is outside `prime-directive-sync`'s comparison window; the diff is the only check.
- [x] 2.4 Narrow `scripts/lint-skill.sh`: the allowed-value regex (line 285) to `^(orchestration|capability)$`, the violation message (line 286), and the usage text (lines 26–27). Update the explanatory comment block (lines 253–265) to match, editing only the ordinal half. Leave the prose-note half of that block, the `usage()` sentence naming a command prose note, and the `elif` branch at line 279 exactly as found — **Story 6 owns all three and runs after this story.**
- [x] 2.5 Remove the parallel content from `.writ/docs/model-tiers.md`: the clamp table row (line 75), the negative-ordinal-form paragraph (line 82), the 2026-10-16 review trigger (line 86), and both restatements of the allow-list — the lint-validation sentence (line 97) and the Allowed Values schema (line 103). Line 97 is shared with Story 6: narrow the regex only and leave its "or a command's prose note" clause alone. Update `.writ/manifest.yaml`'s skills schema comment (line 227) from `<orchestration|capability|-N>` to `<orchestration|capability>`.
- [x] 2.6 Exercise the narrowed grammar: run `bash scripts/lint-skill.sh` over all 6 skills and a synthetic fixture declaring `model_tier: -1`, confirming `orchestration` and `capability` pass and `-1` is rejected with the new message.
- [x] 2.7 Verify: run the active-surface and historical-surface greps, `bash scripts/eval.sh` to `Findings: 0`, and `bash scripts/gen-skill.sh --check` to exit 0 (the manifest comment edit must not break the parser).

## Notes

**Technical considerations:**

- The removal is safe because nothing consumes the reservation. Measured across `agents/` (7 files), `skills/` (6 files), `commands/` (32 files), and `.writ/manifest.yaml`: every declared `model_tier` value is `orchestration` or `capability`. No adapter table in `adapters/{cursor,claude-code,codex,openclaw}.md` mentions ordinals — each maps the two named tiers only.
- No new failure path is created. `system-instructions.md`'s existing degradation row already says an unrecognized `model_tier` warns and falls back to inherit. After deprecation, `-1` is simply unrecognized. That is the whole behavioral consequence.
- `scripts/eval-skill-lifecycle.py` builds its fixtures from `status:` / `evidence:` frontmatter and contains no `model_tier` line, so the `skill-lifecycle` eval check has no ordinal fixture to break. Confirm with the full suite rather than assuming.
- `.writ/manifest.yaml` line 227 is inside a YAML comment block documenting the skills schema — it is not a data field. Editing it cannot affect `check_manifest`'s parity scan, but `gen-skill.sh`'s pure-bash fallback parser reads the file line by line, so re-run `--check` regardless.

**Risks / challenges:**

- **This is a decision, not a discovery.** The maintainer chose at phase planning to retire the reservation ahead of its trigger. An implementer who concludes the offsets are technically harmless has not found new evidence — Business Rule 6 says reopening requires producing a real consumer, which Task 2.1 will have just shown does not exist.
- Over-broad grep. `-1` appears throughout the repository in dates, diffs, and line references. Anchor every search to the `model_tier` context and to the specific files listed in the technical spec; never run a repo-wide substitution.
- ADR-016 originates the reservation and must not be edited (Business Rule 3). Whether this deprecation warrants its own ADR or rides on ADR-021 is a maintainer call outside this spec's file set (spec.md → Out of Scope).

**Integration points:**

- Depends on Story 1 for file-overlap ordering: both stories edit `system-instructions.md` § Model Tiers and `cursor/writ.mdc`.
- Stories 3 and 6 both depend on this story and are parallel-safe with each other (Story 3: `system-instructions.md` § Skills, `.writ/docs/skills.md`, `adapters/`; Story 6: `.writ/docs/model-tiers.md`, `scripts/lint-skill.sh` — disjoint file sets). Story 3's dependency avoids a third concurrent edit to `system-instructions.md` and its mirror. Story 6's is file overlap in `scripts/lint-skill.sh` (`usage()`, the `lint_model_tier()` comment block) and in `.writ/docs/model-tiers.md` — including **line 97, which this story and Story 6 both edit**: this story narrows its `^(orchestration|capability|-[0-9]+)$` allow-list, Story 6 removes its "or a command's prose note" clause.

## What Was Built

**Implementation Date:** 2026-08-11

### Files Modified

- **`system-instructions.md`** (§ Model Tiers) — four constructs removed: the `-N` clause and `-[0-9]+` branch of the allowed-values regex (now `^(orchestration|capability)$`); the `| Reserved ordinal offset beyond available bands | Clamp to floor … |` behavior row; the "**Reserved ordinal offsets (`-1`, `-2`, ...) are reserve-only.**" paragraph; and the `> **Review trigger: 2026-10-16**` blockquote. The file shrank 300 → 291 lines.
- **`cursor/writ.mdc`** — identical removals mirrored, plus collapse of the doubled blank line the removed blockquote left before the Self-Dogfooding appendix.
- **`scripts/lint-skill.sh`** — allowed-value regex narrowed to `^(orchestration|capability)$`; violation message now reads "Use 'orchestration' or 'capability'."; `usage()` text drops the reserved-negative-offset clause. The prose-note half of `usage()` and of the `lint_model_tier()` comment block, and the `elif` branch itself, were left exactly as found for Story 6.
- **`.writ/docs/model-tiers.md`** — clamp table row removed; the entire `## Reserved Ordinal Offsets` section (heading, N-step paragraph, reserve-only paragraph, 2026-10-16 trigger, and its `---` rule) removed; the lint-validation sentence's allow-list narrowed to `^(orchestration|capability)$` with its "or a command's prose note" clause left for Story 6; the Allowed Values schema restated as `^(orchestration|capability)$`.
- **`.writ/manifest.yaml`** — skills schema comment `model_tier: <orchestration|capability|-N>` → `<orchestration|capability>`.
- **`adapters/openclaw.md`, `adapters/cursor.md`** — the `| reserved ordinal \`-N\` | reserve-only; clamps … |` tier-resolution rows removed. **`adapters/claude-code.md`, `adapters/codex.md`** — the "Reserved negative ordinal offsets (`-N`) are not resolved beyond the 2-band clamp today …" sentences removed. See the scope note below.

### Scope note — the adapters did carry ordinals

`sub-specs/technical-spec.md` § "What survives" states *"no adapter table changes — `adapters/{cursor,claude-code,codex,openclaw}.md` map `orchestration`/`capability` only and never mention ordinals."* Measured at implementation time, that is wrong: all four adapters carried an ordinal row or clause (`openclaw.md:67`, `cursor.md:162`, `claude-code.md:137`, `codex.md:163`). This story's Acceptance Criterion 3 names `adapters/` in its active-surface grep list, so the four were cleared rather than left behind. No deliverable changed — clearing them is what clause (e) plus AC 3 already required; only the technical spec's incidental measurement was inaccurate. The adapter files' `required_skills:` reserve-only sentences (`cursor.md:218`, `claude-code.md:396`, `openclaw.md:278`) are a different passage and remain Story 3's.

### Task 2.1 — zero consumers, re-confirmed before removing anything

`grep -rn "model_tier" agents/*.md skills/*/SKILL.md commands/*.md .writ/manifest.yaml` → every declared value is `orchestration` (13) or `capability` (10); the remaining matches are `<tier>` placeholders in `/new-command` and `/new-skill` scaffolding prose. **Zero negative ordinals anywhere.** The only `-N` occurrences in the repository were the schema definitions themselves, which this story removed.

### Task 2.6 — narrowed grammar exercised

- `bash scripts/lint-skill.sh skills/*/SKILL.md` → all 6 clean, exit 0.
- All 7 `agents/*.md` linted individually → zero `model_tier` violations; their fenced `orchestration`/`capability` values are still captured and validated.
- Synthetic `model_tier: -1` → `❌ …:4: model_tier '-1' is invalid. Use 'orchestration' or 'capability'.` — rejected with the new message.
- Synthetic `model_tier: orchestration` and `model_tier: capability` → 0 invalid-value findings each.

### Verification

- Active surface (`system-instructions.md`, `cursor/writ.mdc`, `commands/`, `agents/`, `adapters/`, `scripts/`, `.writ/docs/`, `.writ/manifest.yaml`, `skills/`) grepped for `ordinal`, `Clamp to floor`, `2026-10-16`, and `|-N>` → **0 hits**.
- Historical surface unchanged: `2026-10-16` still returns **7** hits across `.writ/decision-records/`, `.writ/specs/archive/`, `.writ/research/`, `CHANGELOG.md` — identical to the pre-story count. ADR-016 untouched.
- Mirror parity: `diff system-instructions.md cursor/writ.mdc` → only `291a292,301` (the Self-Dogfooding appendix), proving lines 1–291 are byte-identical.
- `bash scripts/eval.sh` → `Findings: 0`, `Run errors: 0` (report `.writ/state/eval-20260811-211541.md`). `bash scripts/gen-skill.sh --check` → exit 0, so the manifest comment edit did not break either parser path.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `bash scripts/eval.sh` reports `Findings: 0`
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 2 (full mirror, no gate over this section), Rule 3 (active surface only — ADR-016 and history untouched), Rule 4 (`Findings: 0` per story), Rule 6 (ordinal removal is a decision, not a discovery)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [(e) `model_tier` negative ordinal offsets — deprecated now, including the four-construct removal table and the matching active-surface removals] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [Zero consumers measured; what survives; regression risk on `lint-skill.sh`'s narrowed grammar] — from sub-specs/technical-spec.md → "(e) Ordinal-offset deprecation — Story 2"
- **Contract:** [Must include (e): offsets DEPRECATED NOW ahead of the 2026-10-16 trigger; keep `orchestration` and `capability`; remove the `-[0-9]+` regex branch, the 2-band clamp prose, the reserve-only paragraph, and the review-trigger blockquote] — from spec.md → ## Contract (Locked)

# Story 2: Deprecate the Ordinal-Offset Reservation

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer rewriting the `model_tier` schema during Phase 10
**I want to** the reserved negative ordinal offsets (`-1`, `-2`, …) removed from the schema now, ahead of their 2026-10-16 review trigger
**So that** the tier vocabulary is exactly the two bands any adapter actually resolves, and the same paragraphs are not rewritten twice in one phase

## Acceptance Criteria

- [ ] Given `system-instructions.md` § Model Tiers, when the schema is read, then allowed values are `orchestration` and `capability` only — regex `^(orchestration|capability)$` — with no reserved negative ordinal offset, no clamp-to-floor table row, no "Reserved ordinal offsets … are reserve-only" paragraph, and no 2026-10-16 review-trigger blockquote.
- [ ] Given `scripts/lint-skill.sh`, when it lints a file declaring `model_tier: orchestration` or `model_tier: capability`, then it passes; and when it lints a file declaring `model_tier: -1`, then it reports an invalid-value violation.
- [ ] Given the literals `-[0-9]+` (as a `model_tier` schema branch), `reserve-only` (in the ordinal context), `Clamp to floor`, `ordinal offset`, and `2026-10-16`, when the active surface is grepped (`system-instructions.md`, `cursor/writ.mdc`, `commands/`, `agents/`, `adapters/`, `scripts/`, `.writ/docs/`, `.writ/manifest.yaml`), then zero hits relating to the `model_tier` ordinal reservation remain.
- [ ] Given the same literals grepped across `.writ/decision-records/` (ADR-016 in particular), `.writ/specs/archive/`, `.writ/research/`, and `CHANGELOG.md`, when compared to pre-story hit counts, then every count is unchanged.
- [ ] Given the graceful-degradation contract, when a `model_tier: -1` is encountered after this change, then the existing "unrecognized value → warn, fall back to inherit" row covers it — no new failure path, no hard failure, and the enforcement boundary (agents enforced at spawn; commands and skills advisory) and precedence rule (`model:` beats `model_tier:`) are unchanged.
- [ ] Given `system-instructions.md` and `cursor/writ.mdc` after the edit, when the § Model Tiers section of each is compared line for line, then the two are identical.
- [ ] Given the full validation suite, when `bash scripts/eval.sh` runs, then it reports `Findings: 0` with no new `eval-exempt:` marker introduced by this story.

## Implementation Tasks

- [ ] 2.1 Re-confirm zero consumers before removing anything: grep `model_tier` across `agents/*.md`, `skills/*/SKILL.md`, `commands/*.md`, and `.writ/manifest.yaml`. Expected: every declared value is `orchestration` or `capability`; the only `-N` occurrences are the schema definitions themselves. If a real ordinal consumer exists, stop and surface it (Business Rule 6) rather than proceeding.
- [ ] 2.2 Remove the four constructs from `system-instructions.md` § Model Tiers: the `-[0-9]+` schema branch and its "reserved negative ordinal offset (`-N`)" prose (line 285), the "Reserved ordinal offset beyond available bands / Clamp to floor" table row (line 295), the "Reserved ordinal offsets … are reserve-only" paragraph (line 298), and the 2026-10-16 review-trigger blockquote (line 300). Locate by literal — Story 1 will have shifted these lines.
- [ ] 2.3 Mirror the identical removals into `cursor/writ.mdc`, then diff the § Model Tiers section of both files. This section is outside `prime-directive-sync`'s comparison window; the diff is the only check.
- [ ] 2.4 Narrow `scripts/lint-skill.sh`: the allowed-value regex (line 285) to `^(orchestration|capability)$`, the violation message (line 286), and the usage text (lines 26–27). Update the explanatory comment block (lines 253–265) to match, editing only the ordinal half. Leave the prose-note half of that block, the `usage()` sentence naming a command prose note, and the `elif` branch at line 279 exactly as found — **Story 6 owns all three and runs after this story.**
- [ ] 2.5 Remove the parallel content from `.writ/docs/model-tiers.md`: the clamp table row (line 75), the negative-ordinal-form paragraph (line 82), the 2026-10-16 review trigger (line 86), and both restatements of the allow-list — the lint-validation sentence (line 97) and the Allowed Values schema (line 103). Line 97 is shared with Story 6: narrow the regex only and leave its "or a command's prose note" clause alone. Update `.writ/manifest.yaml`'s skills schema comment (line 227) from `<orchestration|capability|-N>` to `<orchestration|capability>`.
- [ ] 2.6 Exercise the narrowed grammar: run `bash scripts/lint-skill.sh` over all 6 skills and a synthetic fixture declaring `model_tier: -1`, confirming `orchestration` and `capability` pass and `-1` is rejected with the new message.
- [ ] 2.7 Verify: run the active-surface and historical-surface greps, `bash scripts/eval.sh` to `Findings: 0`, and `bash scripts/gen-skill.sh --check` to exit 0 (the manifest comment edit must not break the parser).

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

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/eval.sh` reports `Findings: 0`
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 2 (full mirror, no gate over this section), Rule 3 (active surface only — ADR-016 and history untouched), Rule 4 (`Findings: 0` per story), Rule 6 (ordinal removal is a decision, not a discovery)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [(e) `model_tier` negative ordinal offsets — deprecated now, including the four-construct removal table and the matching active-surface removals] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [Zero consumers measured; what survives; regression risk on `lint-skill.sh`'s narrowed grammar] — from sub-specs/technical-spec.md → "(e) Ordinal-offset deprecation — Story 2"
- **Contract:** [Must include (e): offsets DEPRECATED NOW ahead of the 2026-10-16 trigger; keep `orchestration` and `capability`; remove the `-[0-9]+` regex branch, the 2-band clamp prose, the reserve-only paragraph, and the review-trigger blockquote] — from spec.md → ## Contract (Locked)

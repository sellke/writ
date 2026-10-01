# Story 1: Panel Config, Vendor Table, Status, and Amendments

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer using Writ on my own project (and the Writ maintainer)
**I want to** opt into a cross-vendor review panel with one `.writ/config.md` line and have a script tell me which reviewers are active, which were dropped, and why
**So that** the panel stays off unless I consent, a same-vendor reviewer can never fake consensus, and ADR-028 and the adapters describe the additive panel Writ is actually building

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given `.writ/docs/config-format.md`, when a reader opens it, then it documents `- **Review Panel:** <slug>[, <slug>…]` in the `- **Key:** value` format: first matching line wins, `none` (case-insensitive) disables, order is preserved, duplicates and slugs past the third kept reviewer are dropped, and the line is also the consent to send story content to other vendors `[AC-1.1]`
- [ ] Given a config line with other-vendor slugs and a known `--origin`, when `python3 scripts/review-panel.py status --repo . --origin "<model>"` runs under Python 3.9 with stdlib only, then it prints `pass` first, one `reviewer: <slug> <vendor>` line per kept reviewer and one `dropped: <slug> <reason>` line per drop (`same_vendor`, `unknown_vendor`, `duplicate_slug`, `over_cap`), a `review-panel:` summary line last, and exits 0; `--json` prints one object with the same verdict, reviewers, and drops `[AC-1.2]`
- [ ] Given the fixed prefix table (`claude-` anthropic; `gpt-`, `o1`…`o9` openai; `grok-`, `cursor-grok-` xai; `gemini-` google; `composer-` cursor; `muse-` meta), when a slug or origin name is resolved, then longest prefix wins for slugs, origin names match by case-insensitive word (e.g. "Claude Fable 5.1" → anthropic), and an unknown prefix resolves to no vendor — with one test per table row `[AC-1.3]`
- [ ] Given each off or skip condition, when `status` runs, then it prints `unverifiable` with exactly one matching reason — `no_config_line`, `panel_disabled`, `malformed_config`, `unknown_session_vendor`, `no_other_vendor` (plus the drop lines), `platform_cannot_spawn_other_vendors` for `--platform claude-code|codex` — and exits 0; `--platform openclaw` behaves as cursor plus `reason: unverified_platform`; a missing `--origin` or unreadable repo exits 2 `[AC-1.4]`
- [ ] Given ADR-028, the four adapters, and the roadmap, when the amendments land, then ADR-028 Decision 3 carries a dated amendment stating additive authority (the Gate 3 agent and `review-override.py` decide as before; ≥2-vendor consensus, primary counted as one, only adds blocks; one-vendor panel findings are advisory), `gate3_route` plus `--panel` as the stakes signal, the matching rule, that path exclusions are prompt instructions rather than enforcement, and the retrospective trial as the removal measurement; `adapters/cursor.md`, `claude-code.md`, `codex.md`, and `openclaw.md` each gain one panel row per technical-spec.md → Adapter Rows; `roadmap.md` Phase 12 Feature 3 points to this spec with no success-criterion change; and every pre-existing uncommitted edit in the ADR and roadmap is preserved `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write failing tests in `scripts/tests/test_review_panel.py` (docstring naming `2026-10-01-cross-family-review-panel`): temp-repo `.writ/config.md` fixtures for a `pass` with kept and dropped reviewers, each drop reason, each `unverifiable` reason, each `--platform` value, `--json` shape, exit 2 on missing `--origin` and unreadable repo, and one test per vendor-table row including the `cursor-grok-` longest-prefix case and origin word matching `[AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.2 Implement `scripts/review-panel.py` with a module-constant vendor table and argparse subcommand `status --repo --origin [--platform cursor|claude-code|codex|openclaw] [--json]` only (stdlib, Python 3.9 floor, verdict line first, `reason:` lines, `review-panel:` summary last, exit 0 ran / 2 usage), reading the config line the way `scripts/jev-judge.py` reads `- **Judgment Provider:**` and following `scripts/review-override.py` / `scripts/boundary-map.py` conventions, until 1.1 passes; leave `tally` and `trial-*` to Stories 2 and 4 `[AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.3 Add the `Review Panel` key to `.writ/docs/config-format.md` beside the existing keys: syntax, `none`, ordering, duplicate and cap rules, consent sentence, and a pointer to `review-panel.py status` `[AC-1.1]`
- [ ] 1.4 Amend `.writ/decision-records/adr-028-behavioral-verification-and-cross-family-panels.md` Decision 3 with a dated amendment note covering additive authority, `gate3_route` as the stakes signal, the matching rule, exclusions-are-instructions, and the retrospective trial method, using targeted `StrReplace` edits on the current working tree `[AC-1.5]`
- [ ] 1.5 Add one panel row to each of `adapters/cursor.md` (available, ≤4 concurrent Tasks, `slug_rejected` drop), `adapters/claude-code.md` and `adapters/codex.md` (unavailable, Gate 3 runs as today), and `adapters/openclaw.md` (*unverified*, spawn via `sessions_spawn`, drop on rejection); add the Feature 3 spec pointer to `.writ/product/roadmap.md` Phase 12 with a targeted `StrReplace` `[AC-1.5]`
- [ ] 1.6 Verify acceptance criteria: run `status` against this repo with and without a scratch config line (in a temp copy, not the real `.writ/config.md`) and with each `--platform`; `git diff` on the ADR and roadmap shows the pre-existing edits intact and only the targeted lines added `[AC-1.1, AC-1.4, AC-1.5]`
- [ ] 1.7 Verify all tests pass: `uv run --python 3.9 pytest scripts/tests/test_review_panel.py`, full `uv run pytest`, the bash tests, and `bash scripts/eval.sh` (outside the sandbox) with Findings 0 `[AC-1.2, AC-1.3, AC-1.4]`

## Notes

- **Uncommitted edits.** `.writ/product/roadmap.md` and the ADR-028 file already carry uncommitted changes (the ADR is untracked; the roadmap holds the 2026-10-01 reconcile pass and the behavioral-verification spec's edits). Edit only the targeted lines with `StrReplace`; never checkout, restore, stash, or rewrite the whole file. Check `git diff` before and after.
- **Cross-spec overlap on ADR-028.** `2026-10-01-behavioral-verification` Story 1 amends Decisions 1 and 2 of the same ADR. Touch Decision 3 and its amendment note only.
- **No eval check here.** `check_review_panel` (helper present, `status` parses, `require_literal` pins on each adapter's panel row) lands in Story 3. Write the adapter rows with stable wording so Story 3 can pin them.
- **Reusable parsing.** Keep config reading and vendor resolution as plain functions; Story 2's `tally` resolves vendors for the primary (`--origin`) and each `--reviewer` slug with the same table, and Story 4's `trial-record` reuses `tally`.
- **Vendor table is the only vendor knowledge.** `o<digit>` must not match arbitrary slugs starting with `o` followed by a letter; test the boundary. Unknown session vendor skips the panel rather than guessing, because a same-vendor reviewer could otherwise fake consensus.
- **No Gate 3 wiring.** This story never edits `commands/implement-story.md`, its `.lean` twin, or any agent file; with no config line, Gate 3 behavior is unchanged by construction.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Read config, Resolve vendors (unknown session vendor; every slug dropped), Platform check]
- **Shadow paths:** [Nil input (no config line), Empty input (`none` or empty line)]
- **Business rules:** spec.md → ## 📋 Business Rules (1 Opt-in, 2 Who reviews, 7 Platforms); spec.md → ## 📋 Business Rules (Expanded) (1 Config line, 2 Vendor table, 3 Session vendor, 10 Never DEGRADED)
- **Experience:** [State Catalog → No config line, Platform cannot spawn other vendors, Session vendor unknown, Every reviewer dropped; Interaction Patterns → every line starts with `review-panel:`]
- **Technical:** sub-specs/technical-spec.md → ## Config Contract; ## Vendor Table; ## `status`; ## Adapter Rows (Story 1); ## ADR-028 Amendment (Story 1); ## Files in Scope (Story 1 rows)
- **Product amendments:** spec.md → Origin header (additive authority, `gate3_route`, retrospective trial); spec.md → ⚠️ Technical Concerns (path exclusions can't be fully enforced)

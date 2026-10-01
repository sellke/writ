# Cross-Family Review Panel (Lite)

> Source: .writ/specs/2026-10-01-cross-family-review-panel/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Opt-in Gate 3 panel of 1–3 other-vendor reviewers on risk-routed (or `--panel`) stories; a script counts findings across vendors — ≥2 vendors block, one is a note; a retrospective trial decides keep or remove.

**Implementation Approach:**
- `scripts/review-panel.py`, Python 3.9 stdlib: `status`, `tally`, `trial-init|prepare|record|label|report`; verdict-first, exit 0/1/2
- The script never spawns models or uses the network; the orchestrator spawns, the script decides
- Additive only: the Gate 3 agent and `review-override.py` are untouched; a panel `block` is one more Gate 3 FAIL
- Matching keys: `ac:AC-N.M` (unchecked tagged line) or `<security|architecture>:<path>` (Critical/Major issue)

**Files in Scope:**
- `scripts/review-panel.py`, `scripts/tests/test_review_panel.py`, `scripts/tests/fixtures/review-panel/` — new
- `agents/{evaluator,review}-agent.md` + `claude-code/agents/writ-{evaluator,reviewer}.md` + regenerated `codex/agents/*.toml` — Category line; review-agent AC tags
- `commands/implement-story.md` + `.lean.md` — one Gate 3 paragraph, `--panel` row, report line
- `scripts/eval.sh` (`check_review_panel`), `scripts/tests/test_governor_enforcement.py` (ratchet)
- `.writ/docs/config-format.md`, `adapters/*.md`, ADR-028, `roadmap.md`

**Error Handling:**
- No config line → nothing runs; Gate 3 identical to today
- Unknown session vendor / all dropped / Claude Code or Codex → `review-panel: skipped — <reason>`
- Rejected slug, empty return, malformed output → that reviewer dropped, one line
- Malformed primary → exit 2; today's malformed-agent handling applies

**Integration Points:**
- Trigger: Gate 2.5 `gate3_route` = `review-agent`, or `--panel`; usage error with `--quick`
- Session vendor from the origin captured at command entry (Model Tiers)
- `jev-judge.py ac-shadow` also consumes the review-agent AC tags

**Line Budget Constraints:** implement-story.md re-pinned from 11110 with disclosure; no new heading, gate, or `Task(` agent stem

---

## For Review Agents

**Acceptance Criteria:**
1. Config line documented; `status` resolves reviewers, drops, and skip reasons with exit 0/2 `[AC-1.1, AC-1.2, AC-1.4]`
2. Vendor table: longest prefix for slugs, word match for origin names, one test per row `[AC-1.3]`
3. ADR-028 Decision 3 amended (additive, stakes signal, matching, exclusions are instructions, trial); four adapter rows `[AC-1.5]`
4. Both agents emit AC tags and Category lines; codex TOMLs fresh `[AC-2.1]`
5. Tally keys, vendor combination, block/advisory/pass, drops, and mutation fixtures behave per rules 7–8 `[AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
6. Gate 3 paragraph, `--panel` row, report line; block = one FAIL increment; no config = today's Gate 3 `[AC-3.1, AC-3.2, AC-3.3]`
7. `check_review_panel` pins bite by mutation; ratchet re-pinned with disclosure `[AC-3.4, AC-3.5]`
8. Trial harness is read-only on yuss, text-free in JSON, and reports keep/remove/unverifiable `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
9. Trial committed before acting; verdict, spec status, and wiring agree `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

**Business Rules:**
- The config line is the switch and the consent; `none` = off
- Same-vendor and unknown-vendor reviewers dropped; ≤3 kept
- Same prompt and inputs as the primary, read-only, plus one exclusion line
- Primary counts as one vendor; one-vendor panel findings advisory; never DEGRADED
- Trial JSON holds IDs, keys, vendors, labels — never source or story text

**Experience Design:**
- Entry: `- **Review Panel:** <slugs>` in `.writ/config.md`
- Happy path: risky story → primary + panel in one message → tally → continue or recode
- Moment of truth: `review-panel: block — AC-2.3 unmet (anthropic, openai)`
- Feedback: every line starts `review-panel:`
- Error: one line per drop or skip; Gate 3 falls back to today

---

## For Testing Agents

**Success Criteria:**
1. `uv run pytest` and `uv run --python 3.9 pytest` green; bash tests green
2. `bash scripts/eval.sh` Findings 0 with `review-panel` check registered
3. Mutation: single-vendor never blocks; two-vendor AC always blocks

**Shadow Paths to Verify:**
- **Happy path:** shared AC finding → `block` exit 1 → recode → re-review passes
- **Nil input:** no config line → `unverifiable no_config_line`, no Gate 3 change
- **Empty input:** `none` / empty list → `panel_disabled` / `malformed_config`
- **Upstream error:** every slug rejected → `unverifiable no_usable_reviewer`; primary verdict stands

**Edge Cases:**
- Same file, different category → no consensus
- Minor security, two vendors → no consensus
- Two reviewers, same vendor → counted once
- Multi-ID tag `[AC-1.1, AC-1.2]` → one key per ID
- Merge-commit baseline story → `trial-prepare` exit 2 if parent not fetched

**Coverage Requirements:**
- New code ≥80%; every verdict and drop reason exercised; every eval pin shown to bite

**Test Strategy:**
- Fixture reviewer outputs; throwaway local git repo standing in for yuss; no network

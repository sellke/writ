# UAT Plan: Cross-Family Review Panel

> **Generated:** 2026-10-01
> **Spec:** `.writ/specs/2026-10-01-cross-family-review-panel/`
> **Stories Covered:** 4 of 5 completed (Story 5 is a maintainer handoff, see the marked section)
> **Total Scenarios:** 54 (41 for Stories 1–4, 13 Story 5 trial steps)
> **Verification recipe:** skipped — Writ has no running app, so no recipe was drafted or saved and every scenario is human (`human — no recipe`).

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Conventions for this plan:**

- Run every command from the repo root, `/Users/asellke/Projects/writ`.
- `F=scripts/tests/fixtures/review-panel` is assumed in tally scenarios; set it once with `F=scripts/tests/fixtures/review-panel`.
- **Never add a `- **Review Panel:**` line to this repo's `.writ/config.md`** for Stories 1–4. Scenarios that need one use a scratch directory created with:
  ```bash
  S=$(mktemp -d) && mkdir -p "$S/.writ" && printf '%s\n' '<the config line>' > "$S/.writ/config.md"
  ```
  Remove it afterwards with `rm -rf "$S"`.
- "Expected Result" blocks quote the output observed on 2026-10-01 when this plan was generated (origin `Claude Opus 5.5`, Python 3.9+ stdlib). Temporary paths will differ.
- Exit codes: print them with `echo "exit $?"` right after the command.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Panel config, vendor table, status, amendments | ✅ Covered | 11 | AC: 8, Errors: 2, Shadow: 1, Edge: 0 |
| Story 2: Tally, matching rule, tagged reviewer output | ✅ Covered | 13 | AC: 9, Errors: 4, Shadow: 0, Edge: 0 |
| Story 3: Gate 3 wiring, `--panel`, eval pins | ✅ Covered | 10 | AC: 5, Errors: 1, Shadow: 2, Edge: 1, Experience: 1 |
| Story 4: Retrospective trial harness and report | ✅ Covered | 7 | AC: 6, Errors: 1, Shadow: 0, Edge: 0 |
| Story 5: Run the trial and act on the verdict | ⏳ Pending (maintainer handoff) | 13 trial steps | Procedure from story file + technical spec |

---

## Story 1: Panel Config, Vendor Table, Status, and Amendments

### Scenario 1: The config doc explains the Review Panel line and its consent meaning

**Source:** Acceptance Criteria — Story 1 (AC-1.1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Open `.writ/docs/config-format.md` and find the `Review Panel` row in the Supported Keys table.
2. Read the `## Review Panel` section.

**Expected Result:**
- The section shows the example `- **Review Panel:** gpt-5.6-sol-medium, cursor-grok-4.6-medium-fast`.
- It states: first matching line wins; `none` (any case) or no line means off and Gate 3 runs as before; order is kept; a repeated slug is dropped `duplicate_slug`; slugs after the third kept one are dropped `over_cap`; same-vendor and unknown-prefix slugs are dropped.
- It states the line is also the consent to send story content to other vendors, and that it is never detected or offered for saving.
- It points to `python3 scripts/review-panel.py status --repo . --origin "<session model>"`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `.writ/docs/config-format.md` (Supported Keys row, `## Review Panel`)

---

### Scenario 2: Status lists active reviewers for a valid other-vendor line

**Source:** Acceptance Criteria — Story 1 (AC-1.2)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Scratch config with `- **Review Panel:** gpt-5.6-sol-medium, cursor-grok-4.6-medium-fast` (see Conventions).

**Steps:**
1. Run `python3 scripts/review-panel.py status --repo "$S" --origin "Claude Opus 5.5" --platform cursor; echo "exit $?"`

**Expected Result:**
```
pass
reviewer: gpt-5.6-sol-medium openai
reviewer: cursor-grok-4.6-medium-fast xai
review-panel: pass — 2 reviewers (gpt-5.6-sol-medium openai, cursor-grok-4.6-medium-fast xai)
exit 0
```
- The verdict is the first line and the `review-panel:` summary is the last.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — `scripts/review-panel.py` (`status`, `resolve`)

---

### Scenario 3: Status `--json` prints one object with the same verdict

**Source:** Acceptance Criteria — Story 1 (AC-1.2)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Same scratch config as Scenario 2.

**Steps:**
1. Run `python3 scripts/review-panel.py status --repo "$S" --origin "Claude Opus 5.5" --json; echo "exit $?"`

**Expected Result:**
- One line of JSON, observed:
  `{"dropped": [], "platform": null, "reasons": [], "reviewers": [{"slug": "gpt-5.6-sol-medium", "vendor": "openai"}, {"slug": "cursor-grok-4.6-medium-fast", "vendor": "xai"}], "session_vendor": "anthropic", "summary": "review-panel: pass \u2014 2 reviewers (...)", "verdict": "pass"}`
- `exit 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 4: Every drop reason and vendor-table row resolves as documented

**Source:** Acceptance Criteria — Story 1 (AC-1.2, AC-1.3)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Scratch config with `- **Review Panel:** claude-sonnet-5-5-high, gpt-5.6-sol-medium, gpt-5.6-sol-medium, foo-1, cursor-grok-4.6-medium-fast, gemini-3.8-flash-high, muse-spark-1.3-high`

**Steps:**
1. Run `python3 scripts/review-panel.py status --repo "$S" --origin "Claude Opus 5.5" --platform cursor; echo "exit $?"`

**Expected Result:**
```
pass
reviewer: gpt-5.6-sol-medium openai
reviewer: cursor-grok-4.6-medium-fast xai
reviewer: gemini-3.8-flash-high google
dropped: claude-sonnet-5-5-high same_vendor
dropped: gpt-5.6-sol-medium duplicate_slug
dropped: foo-1 unknown_vendor
dropped: muse-spark-1.3-high over_cap
review-panel: pass — 3 reviewers (gpt-5.6-sol-medium openai, cursor-grok-4.6-medium-fast xai, gemini-3.8-flash-high google)
exit 0
```
- `cursor-grok-…` resolves to xai (longest prefix wins). A Claude session drops the Claude slug. The fourth valid slug is `over_cap`.
- The full per-row table (`composer-` → cursor, `o1`…`o9` → openai, the `o`-plus-letter boundary) is covered by the unit tests: `uv run --python 3.9 pytest scripts/tests/test_review_panel.py -q` → `139 passed`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 5: `none` and an empty list turn the panel off or skip it

**Source:** Acceptance Criteria — Story 1 (AC-1.4); Shadow Path — Empty input
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Scratch directory as in Conventions.

**Steps:**
1. Write the config line `- **Review Panel:** None`, then run `python3 scripts/review-panel.py status --repo "$S" --origin "Claude Opus 5.5"; echo "exit $?"`
2. Write the config line `- **Review Panel:** , ,`, then run the same command.

**Expected Result:**
- Step 1:
  ```
  unverifiable
  reason: panel_disabled
  review-panel: off — panel_disabled
  exit 0
  ```
- Step 2:
  ```
  unverifiable
  reason: malformed_config
  review-panel: skipped — malformed_config
  exit 0
  ```

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 6: Platforms that cannot spawn other vendors print one skip line

**Source:** Acceptance Criteria — Story 1 (AC-1.4); Error Map — Platform check
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Same scratch config as Scenario 2.

**Steps:**
1. Run `for p in claude-code codex openclaw; do python3 scripts/review-panel.py status --repo "$S" --origin "Claude Opus 5.5" --platform $p; echo "exit $?"; done`

**Expected Result:**
- `claude-code` and `codex` each print:
  ```
  unverifiable
  reason: platform_cannot_spawn_other_vendors
  review-panel: skipped — platform cannot spawn other vendors
  exit 0
  ```
- `openclaw` prints `pass`, then `reason: unverified_platform`, the same two `reviewer:` lines as Scenario 2, the `review-panel: pass — 2 reviewers (…)` summary, and `exit 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: Usage errors exit 2

**Source:** Acceptance Criteria — Story 1 (AC-1.4)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Scratch directory `$S` exists.

**Steps:**
1. Run `python3 scripts/review-panel.py status --repo "$S"; echo "exit $?"` (no `--origin`).
2. Run `python3 scripts/review-panel.py status --repo "$S/nope" --origin "Claude Opus 5.5"; echo "exit $?"`

**Expected Result:**
- Step 1: argparse prints `review-panel.py status: error: the following arguments are required: --origin`, then `exit 2`.
- Step 2: `review-panel: usage — repo is not a readable directory: <path>/nope`, then `exit 2`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: ADR-028, the four adapters, and the roadmap describe the additive panel

**Source:** Acceptance Criteria — Story 1 (AC-1.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Open `.writ/decision-records/adr-028-behavioral-verification-and-cross-family-panels.md`, Decision 3, and read its dated amendment.
2. Run `rg -n 'Review panel \(ADR-028\)' adapters/`
3. Open `.writ/product/roadmap.md`, Phase 12, Feature 3.

**Expected Result:**
- The ADR amendment states: the Gate 3 agent and `review-override.py` decide as before; a finding from two or more vendors (the session's agent counts as one) only adds a block; one-vendor findings are advisory; `gate3_route` plus `--panel` is the stakes signal; the matching rule (same unmet AC, or same file + security/architecture at Critical/Major); path exclusions are prompt instructions, not enforcement; the retrospective trial is the removal measurement.
- Step 2 shows one line in each adapter: `cursor.md` "available" (≤4 concurrent Tasks, `slug_rejected`), `claude-code.md` "unavailable", `codex.md` "unavailable by default", `openclaw.md` "*(unverified)*".
- The roadmap's Feature 3 points to this spec, and no success criterion text changed.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — ADR-028 Decision 3 amendment; `adapters/{cursor,claude-code,codex,openclaw}.md`; `.writ/product/roadmap.md`

---

### Scenario 9: An unknown session vendor skips the panel

**Source:** Error Map — Resolve vendors (unknown session vendor) — Story 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Same scratch config as Scenario 2.

**Steps:**
1. Run `python3 scripts/review-panel.py status --repo "$S" --origin "Mystery Model" --platform cursor; echo "exit $?"`

**Expected Result:**
```
unverifiable
reason: unknown_session_vendor
review-panel: skipped — unknown_session_vendor
exit 0
```

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 10: When every slug is dropped, the panel is skipped and the drops are listed

**Source:** Error Map — Resolve vendors (every slug dropped) — Story 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Scratch config with `- **Review Panel:** claude-sonnet-5-5-high, foo-1`

**Steps:**
1. Run `python3 scripts/review-panel.py status --repo "$S" --origin "Claude Opus 5.5" --platform cursor; echo "exit $?"`

**Expected Result:**
```
unverifiable
reason: no_other_vendor
dropped: claude-sonnet-5-5-high same_vendor
dropped: foo-1 unknown_vendor
review-panel: skipped — no_other_vendor (dropped: claude-sonnet-5-5-high same_vendor, foo-1 unknown_vendor)
exit 0
```

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: This repo has no config line, so the panel is off

**Source:** Shadow Path — Nil input (no config line) — Story 1
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- This repo's `.writ/config.md` has no `Review Panel` line (`rg -n 'Review Panel' .writ/config.md` prints nothing).

**Steps:**
1. Run `python3 scripts/review-panel.py status --repo . --origin "Claude Opus 5.5"; echo "exit $?"`

**Expected Result:**
```
unverifiable
reason: no_config_line
review-panel: off — no_config_line
exit 0
```

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Tally, Matching Rule, and Tagged Reviewer Output

### Scenario 12: Both Gate 3 agents emit the AC tags and Category lines the tally needs

**Source:** Acceptance Criteria — Story 2 (AC-2.1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Run `rg -n '\*\*Category:\*\*' agents/review-agent.md agents/evaluator-agent.md claude-code/agents/writ-reviewer.md claude-code/agents/writ-evaluator.md`
2. Open `agents/review-agent.md` and look at the Acceptance Criteria checklist instructions and examples.
3. Run `python3 scripts/gen-codex-agent-tomls.py --check`

**Expected Result:**
- Step 1: each of the four files has `- **Category:** [criterion/security/architecture/taste]` in its Issues Found format.
- Step 2: the instructions say each checklist line ends with its `[AC-N.M]` tag, and the examples end with a tag such as `` `[AC-1.1]` ``.
- Step 3 prints `gen-codex-agent-tomls: pass (0 stale, 0 missing, 0 orphan, 0 unmapped)`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 2 — `agents/review-agent.md`, `agents/evaluator-agent.md`, `claude-code/agents/writ-{reviewer,evaluator}.md`, `codex/agents/{review-agent,evaluator-agent}.toml`

---

### Scenario 13: Moment of truth — an AC unmet by the primary and one panel vendor blocks

**Source:** Acceptance Criteria — Story 2 (AC-2.3, AC-2.5); Experience Design — Moment of truth
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel`

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-fail-ac23.md --reviewer gpt-5.6-sol-medium=$F/panel-ac23.md; echo "exit $?"`

**Expected Result:**
```
block
reason: consensus ac:AC-2.3
review-panel: block — AC-2.3 unmet (anthropic, openai)
review-panel: block — 2 vendors, 1 consensus finding
exit 1
```
- The primary's vendor is listed first.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: A finding from one panel vendor is advisory and never blocks

**Source:** Acceptance Criteria — Story 2 (AC-2.3, AC-2.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel`

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/panel-ac23.md; echo "exit $?"`

**Expected Result:**
```
pass
review-panel: advisory — AC-2.3 unmet (openai)
review-panel: pass — 2 vendors, 0 consensus findings
exit 0
```

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 15: Two panel vendors block even when the primary passed

**Source:** Acceptance Criteria — Story 2 (AC-2.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel`

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/panel-ac23.md --reviewer cursor-grok-4.6-medium-fast=$F/panel-ac23.md; echo "exit $?"`
2. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/panel-security-pay.md --reviewer cursor-grok-4.6-medium-fast=$F/panel-security-pay-b.md; echo "exit $?"`

**Expected Result:**
- Step 1: `block`, `reason: consensus ac:AC-2.3`, `review-panel: block — AC-2.3 unmet (openai, xai)`, `review-panel: block — 3 vendors, 1 consensus finding`, `exit 1`.
- Step 2: `block`, `reason: consensus security:app/api/pay.ts`, `review-panel: block — security app/api/pay.ts (openai, xai)`, `review-panel: block — 3 vendors, 1 consensus finding`, `exit 1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 16: The same file under different categories is not consensus

**Source:** Acceptance Criteria — Story 2 (AC-2.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel`

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/panel-security-pay.md --reviewer cursor-grok-4.6-medium-fast=$F/panel-architecture-pay.md; echo "exit $?"`

**Expected Result:**
```
pass
review-panel: advisory — architecture app/api/pay.ts (xai)
review-panel: advisory — security app/api/pay.ts (openai)
review-panel: pass — 3 vendors, 0 consensus findings
exit 0
```

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 17: Minor, taste, untagged, and Location-less findings are never counted

**Source:** Acceptance Criteria — Story 2 (AC-2.2, AC-2.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel` (`panel-minor-security-pay.md` holds a Minor security finding, a taste finding, an untagged finding, and one with no Location)

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/panel-minor-security-pay.md --reviewer cursor-grok-4.6-medium-fast=$F/panel-minor-security-pay.md; echo "exit $?"`

**Expected Result:**
```
pass
review-panel: pass — 3 vendors, 0 consensus findings
exit 0
```
- No `advisory` or `block` lines, even though two vendors returned identical text.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: Two reviewers from the same vendor count as one

**Source:** Acceptance Criteria — Story 2 (AC-2.3, AC-2.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel`

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/panel-security-pay.md --reviewer gpt-5.6-terra-medium=$F/panel-security-pay-b.md; echo "exit $?"`

**Expected Result:**
```
pass
review-panel: advisory — security app/api/pay.ts (openai)
review-panel: pass — 2 vendors, 0 consensus findings
exit 0
```
- The two OpenAI reviewers agree, but that is one vendor, so there is no block.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: Multi-ID tags, sub-headings, and `N/A` Locations parse correctly

**Source:** Acceptance Criteria — Story 2 (AC-2.2)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel`

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/panel-multi-id.md; echo "exit $?"`
2. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/panel-subheadings-na.md; echo "exit $?"`

**Expected Result:**
- Step 1: a `[AC-2.2, AC-2.3]` tag yields two keys: `review-panel: advisory — AC-2.2 unmet (openai)`, `review-panel: advisory — AC-2.3 unmet (openai)`, `review-panel: pass — 2 vendors, 0 consensus findings`, `exit 0`.
- Step 2: only the real path is keyed (`N/A` is ignored, and a Location with trailing commentary normalizes to its path): `review-panel: advisory — security app/api/pay.ts (openai)`, `review-panel: pass — 2 vendors, 0 consensus findings`, `exit 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 2 — DEV-003 (first backticked span; placeholder Locations never keyed)

---

### Scenario 20: `--json` carries each vendor's own wording for the recode brief

**Source:** Acceptance Criteria — Story 2 (AC-2.4)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel`

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-fail-ac23.md --reviewer gpt-5.6-sol-medium=$F/panel-ac23.md --json | python3 -m json.tool`

**Expected Result:**
- One object with `"verdict": "block"`, `"primary_verdict": "FAIL"`, `"vendors": ["anthropic", "openai"]`, and one finding `{"key": "ac:AC-2.3", "display": "AC-2.3 unmet", "classification": "consensus", "severity": "Critical", "vendors": ["anthropic", "openai"], "texts": [...]}`.
- `texts` holds two entries, primary and `gpt-5.6-sol-medium`, each with that vendor's own checklist line ("…no test asserts the message…" and "…the handler returns a generic 500…"), so a false match is visible.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 21: A malformed reviewer is dropped and the rest still count

**Source:** Error Map — Parse reviewer (no verdict line) — Story 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel`

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-fail-ac23.md --reviewer gpt-5.6-sol-medium=$F/malformed.md --reviewer cursor-grok-4.6-medium-fast=$F/panel-ac23.md; echo "exit $?"`

**Expected Result:**
```
block
reason: consensus ac:AC-2.3
review-panel: dropped gpt-5.6-sol-medium — malformed_output
review-panel: block — AC-2.3 unmet (anthropic, xai)
review-panel: block — 2 vendors, 1 consensus finding
exit 1
```

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 22: With no usable reviewer, the tally is unverifiable and does not block

**Source:** Error Map — Tally (no usable reviewer left); Shadow Path — Upstream error — Story 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel`

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/malformed.md; echo "exit $?"`
2. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=/nonexistent.md; echo "exit $?"`
3. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer claude-opus-5-5-medium=$F/panel-ac23.md; echo "exit $?"`

**Expected Result:**
- Step 1: `unverifiable`, `reason: no_usable_reviewer`, `review-panel: dropped gpt-5.6-sol-medium — malformed_output`, `review-panel: unverifiable — no_usable_reviewer`, `exit 0`.
- Step 2: the same, but the drop line reads `— no_output`.
- Step 3: a same-vendor reviewer is not a panel reviewer: `unverifiable`, `reason: no_usable_reviewer`, `review-panel: unverifiable — no_usable_reviewer`, `exit 0`, with no advisory line.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 2 — DEV-004 (session-vendor reviewers merge into the primary)

---

### Scenario 23: A malformed primary output is a usage error

**Source:** Error Map — Parse primary (no verdict line) — Story 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel`

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Claude Opus 5.5" --primary $F/malformed.md --reviewer gpt-5.6-sol-medium=$F/panel-ac23.md; echo "exit $?"`

**Expected Result:**
- `review-panel: usage — primary output has no EVALUATION_RESULT / REVIEW_RESULT line` on stderr, then `exit 2`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 24: Tally with an unknown session vendor is unverifiable

**Source:** Error Map — Resolve vendors (unknown session vendor) — Story 2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `F=scripts/tests/fixtures/review-panel`

**Steps:**
1. Run `python3 scripts/review-panel.py tally --origin "Mystery Model" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/panel-ac23.md; echo "exit $?"`

**Expected Result:**
```
unverifiable
reason: unknown_session_vendor
review-panel: unverifiable — unknown_session_vendor
exit 0
```

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Gate 3 Wiring, `--panel`, and Eval Pins

### Scenario 25: One opt-in panel paragraph sits in both implement-story files

**Source:** Acceptance Criteria — Story 3 (AC-3.1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Run `rg -c 'Review panel \(opt-in\)' commands/implement-story.md commands/implement-story.lean.md`
2. In `commands/implement-story.md`, read the paragraph that starts `**Review panel (opt-in).**` and the paragraph just above it.
3. In `commands/implement-story.lean.md`, find the same paragraph.

**Expected Result:**
- Step 1 prints `:1` for each file.
- In the default file, the paragraph comes directly after `**Risk route:**`. In the lean file, it sits in the same slot, after the default-spawn line and before `` **`--full-pipeline`:** `` (the lean file has no Risk route paragraph, DEV-006).
- The paragraph opens "Only with a `- **Review Panel:**` line in `.writ/config.md`:", runs `status --platform <origin platform>`, triggers when Gate 3 spawns `review-agent` (risk route, `--full-pipeline`, or two-fail escalation) or `--panel` is set, and spawns reviewers in the same message with the same prompt, `readonly`, `model: <slug>`, and the `.env*`/`*.pem`/`*.key`/`*secret*`/`*credential*` exclusion line. It prints `review-panel: dropped` for rejected or empty reviewers and runs `tally` after `review-override.py`.
- There is no new heading and no new `Task(` marker naming an agent.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 3 — `commands/implement-story.md` (line ~278), `commands/implement-story.lean.md` (line ~241); DEV-005 trigger wording

---

### Scenario 26: Panel outcomes combine with Gate 3 without weakening it

**Source:** Acceptance Criteria — Story 3 (AC-3.2); Edge Cases — Primary FAIL + block, Primary PAUSE + block, `--review-only --panel` + block, two-fail escalation
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Read the rest of the `**Review panel (opt-in).**` paragraph in `commands/implement-story.md`.
2. Read Gate 3.5 § A in the same file (around line 310) for the panel clause.

**Expected Result:**
- The paragraph says `block` is a Gate 3 FAIL, with one loop increment even if the agent also failed. On PAUSE, Gate 3.5 lists the block lines and accept still recodes. Under `--review-only`, a block ends the run.
- `advisory`, `pass`, `unverifiable`, `skipped`, and `off` print their lines and continue.
- It says the panel can only add blocks, never changes the Gate 3 agent's verdict, and never marks a story `⚠️ DEGRADED`.
- Two-fail escalation is named in the trigger, so the panel still runs once `review-agent` is primary.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 27: `--panel` is in the Invocation table, conflicts with `--quick`, and appears in the report

**Source:** Acceptance Criteria — Story 3 (AC-3.3); Edge Case — `--panel --quick`
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Run `rg -n -- '--panel' commands/implement-story.md commands/implement-story.lean.md`
2. Run `rg -n 'review-panel:' commands/implement-story.md commands/implement-story.lean.md`

**Expected Result:**
- Step 1: an Invocation row `` `/implement-story story-3 --panel` `` saying "Convene the review panel at Gate 3 regardless of route (needs the config line)" in both files. The default file's mutual-exclusion sentence adds "`--panel` conflicts with `--quick`: on a conflict, stop with a usage error before any gate". The lean row itself states the `--quick` usage error.
- Step 2: Step 4 item 8's report list names `review-panel:` lines (beside `gate3-route:` in the default file).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 28: Without the config line, Gate 3 runs no new step

**Source:** Shadow Path — Nil input (no config line) — Story 3 (AC-3.3)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- A project (or this repo) whose `.writ/config.md` has no `Review Panel` line.

**Steps:**
1. Read Gate 3 in `commands/implement-story.md` from the Risk route paragraph to the end of Gate 3, and note every place `review-panel.py` is invoked.
2. Optionally, in Cursor, run `/implement-story` on any small story in such a project, then search the story report for `review-panel:`.

**Expected Result:**
- The only `review-panel.py` call is behind the opening clause "Only with a `- **Review Panel:**` line", so with no line nothing extra runs.
- In the optional live run, the report has no `review-panel:` lines and Gate 3 spawns and verdicts look the same as before this spec.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: The `review-panel` eval check passes and probes the fixtures

**Source:** Acceptance Criteria — Story 3 (AC-3.4)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Run outside any sandbox (the eval does `git init` in a temp dir).

**Steps:**
1. Run `bash scripts/eval.sh --check=review-panel`
2. Open the report file it names (`.writ/state/eval-<timestamp>.md`).
3. Optionally, prove a pin bites: in a throwaway branch, delete the `**Review panel (opt-in).**` paragraph from `commands/implement-story.lean.md`, re-run step 1, then `git checkout -- commands/implement-story.lean.md`.

**Expected Result:**
- The report shows `## review-panel`, `PASS`, a note `review-panel: off — no_config_line`, and `Findings: 0` (observed 2026-10-01).
- In optional step 3, the check reports a finding naming the lean file. The recorded mutation set is also exercised by `uv run pytest scripts/tests/test_review_panel.py -q -k EvalPinMutation`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 3 — `scripts/eval.sh` `check_review_panel` (registered after `app-verify`)

---

### Scenario 30: The byte ratchet was re-pinned with a disclosure

**Source:** Acceptance Criteria — Story 3 (AC-3.5)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- None

**Steps:**
1. Run `rg -n '12013|cross-family-review-panel' scripts/tests/test_governor_enforcement.py`
2. Run `uv run --python 3.9 pytest scripts/tests/test_governor_enforcement.py scripts/tests/test_lean_commands.py -q`

**Expected Result:**
- Step 1 shows `"commands/implement-story.md": 12013` with a dated comment naming `2026-10-01-cross-family-review-panel` Story 3 (11103 → 12013, rebased on the behavioral-verification spec's 11103), ending "Inline prose, no new step, gate, or spawn site. Acknowledged, not exempted."
- Step 2 passes.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 31: Live — a risky story in Cursor convenes the panel and a consensus finding recodes

**Source:** Shadow Path — Happy path; Experience Design — Happy path flow — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Cursor, a **scratch project** (not this repo) with Writ installed and `- **Review Panel:** gpt-5.6-sol-medium, cursor-grok-4.6-medium-fast` in its `.writ/config.md`. The session model is non-OpenAI and non-xAI.
- A story Gate 2.5 routes to `review-agent` (crosses a boundary), or pass `--panel`.
- Accept that this sends story content to the listed vendors and costs real model spend.

**Steps:**
1. Run `/implement-story story-N --panel` in Cursor.
2. At Gate 3, watch the spawned Tasks.
3. Read the Gate 3 output and the final story report.

**Expected Result:**
- The Gate 3 agent and both panel reviewers spawn in one message, each reviewer at its own model, read-only.
- The report shows `review-panel:` lines: `pass — …`, `advisory — …`, or `block — <key> (<vendors>)`.
- On `block`, the story goes back to Gate 1 with the consensus findings and each vendor's wording, counted once in the review loop, and the next Gate 3 convenes the panel again.
- The story is never marked `⚠️ DEGRADED` because of the panel.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Not exercised by any automated test: the Gate 3 wiring is prose, and only its pins and the script are tested.

---

### Scenario 32: Live — a rejected or silent reviewer is dropped and the panel continues

**Source:** Error Map — Spawn reviewer (slug rejected; timeout / empty return) — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Same scratch project as Scenario 31, with one slug in the config line that Cursor's model list does not offer (e.g. `gpt-0.0-fake`).

**Steps:**
1. Run `/implement-story story-N --panel` in Cursor.
2. Read the Gate 3 output.

**Expected Result:**
- `status` keeps the fake slug (its prefix is known), but the spawn is rejected and Gate 3 prints `review-panel: dropped gpt-0.0-fake — slug_rejected`. The remaining reviewers are tallied.
- If every reviewer is dropped, the tally prints `review-panel: unverifiable — no_usable_reviewer` and the primary's verdict stands.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 33: Live — Claude Code prints one skip line and runs Gate 3 as today

**Source:** Experience Design — State Catalog (platform cannot spawn other vendors) — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Claude Code, the scratch project from Scenario 31 with its config line.

**Steps:**
1. Run `/implement-story story-N --panel` in Claude Code.
2. Read the Gate 3 output.

**Expected Result:**
- Gate 3 prints `review-panel: skipped — platform cannot spawn other vendors`, spawns no panel reviewers, and runs exactly as before.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 34: Live — `--panel --quick` stops before any gate

**Source:** Edge Case — `--panel --quick` usage error — Story 3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Any Writ project in Cursor or Claude Code.

**Steps:**
1. Run `/implement-story story-N --panel --quick`

**Expected Result:**
- The command stops with a usage error naming the conflict before Gate 0/1 runs. No files change and no agents spawn.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: Retrospective Trial Harness and Report

### Scenario 35: trial-init copies the four baseline stories and refuses to overwrite

**Source:** Acceptance Criteria — Story 4 (AC-4.1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `T=$(mktemp -d)`

**Steps:**
1. Run `python3 scripts/review-panel.py trial-init --baseline .writ/eval/baselines/2026-09-07-claude-fable-5-1.json --out $T/trial.json; echo "exit $?"`
2. Run the same command again.

**Expected Result:**
- Step 1:
  ```
  initialized
  story: 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow 79d79ae4a2fb
  story: 2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link 8d97930a73bf
  story: 2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption c9350fca11ca
  story: 2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard 12eea11e766c
  review-panel: trial initialized — 4 stories, no arms recorded
  exit 0
  ```
- Step 2: `review-panel: usage — refusing to overwrite <path>/trial.json without --force`, `exit 2`.
- `$T/trial.json` has `"schema": "panel-trial-v1"` and each story's `story_id`, `story_path`, `spec_folder`, `story_commit`, `parent_sha`, with empty `arms`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 36: trial-prepare builds isolated inputs and leaves the source repo untouched

**Source:** Acceptance Criteria — Story 4 (AC-4.2)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Run **outside the sandbox**. Inside Cursor's agent sandbox, `git init` in a temp dir fails, and `trial-prepare` exits 2 with `<story>: git init failed` (observed).

**Steps:**
1. Run `uv run pytest scripts/tests/test_review_panel.py -q -k TrialPrepare`
2. Read `test_prepare_writes_inputs_and_leaves_yuss_unchanged` in `scripts/tests/test_review_panel.py` to confirm what it asserts.

**Expected Result:**
- Step 1: `6 passed` (observed).
- The test builds a throwaway two-commit stand-in repo. It asserts `checkout/`, `diff.patch`, `story.md`, and `contract.md` (the `## Specification Contract` section only) are written under `<tmp-root>/writ-panel-trial-<spec>--<story>/`, and that the stand-in's HEAD, refs, and `git status --porcelain` are identical before and after.

**Status:** [ ] Pass  [ ] Fail

**Notes:** The real yuss is exercised only in Story 5 (Scenario 45).

---

### Scenario 37: trial-prepare refuses a missing path or an unreachable commit and writes nothing

**Source:** Error Map — Trial prepare (yuss path missing / commit unreachable) — Story 4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `T=$(mktemp -d)`, then `python3 scripts/review-panel.py trial-init --baseline scripts/tests/fixtures/review-panel/trial/mini-baseline.json --out $T/mini.json` (fixture SHAs like `2222…` exist nowhere).
- Any local git repo as `--yuss`, e.g. `.` (only read with `rev-parse`).

**Steps:**
1. Run `python3 scripts/review-panel.py trial-prepare --trial $T/mini.json --yuss $T/missing --story 2026-01-01-alpha/story-1-api --tmp-root $T/runs; echo "exit $?"`
2. Run `python3 scripts/review-panel.py trial-prepare --trial $T/mini.json --yuss . --story 2026-01-02-beta/story-2-ui --tmp-root $T/runs; echo "exit $?"`
3. Run `ls $T/runs`

**Expected Result:**
- Step 1: `review-panel: usage — 2026-01-01-alpha/story-1-api: yuss path missing: <path>/missing`, `exit 2`.
- Step 2: `review-panel: usage — 2026-01-02-beta/story-2-ui: story_commit 2222222222222222222222222222222222222222 unreachable in <path>`, `exit 2`.
- Step 3: no such directory (nothing written).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 38: trial-record stores keys only and keeps raw outputs in gitignored state

**Source:** Acceptance Criteria — Story 4 (AC-4.3)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- A scratch working directory `W` that contains an empty `.writ/` folder (`trial-record` must run where `.writ/` exists) and a mini-baseline trial file `trial.json` from `trial-init`.
- `F=<repo>/scripts/tests/fixtures/review-panel`, and `RP=<repo>/scripts/review-panel.py`.

**Steps:**
1. In `W`, for each of the four mini-baseline story IDs, run `python3 $RP trial-record --trial trial.json --story <id> --arm evaluator --origin "Claude Opus 5.5" --primary $F/primary-pass.md`
2. Run `python3 $RP trial-record --trial trial.json --story 2026-01-01-alpha/story-1-api --arm panel --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/panel-ac23.md`
3. Record the panel arm for the other three stories with `--reviewer gpt-5.6-sol-medium=$F/primary-pass.md`.
4. Run `find .writ/state/panel-trial -type f | sort` and `grep -cE '@@|\+\+\+|Given a declined' trial.json`

**Expected Result:**
- Step 2: `recorded`, `review-panel: recorded 2026-01-01-alpha/story-1-api panel — 1 key, 1 panel-only finding`.
- Steps 1 and 3 print `recorded` and `review-panel: recorded <id> <arm> — 0 keys, 0 panel-only findings`.
- Step 4: three raw files per story under `.writ/state/panel-trial/<spec>--<story>/` (`evaluator-primary.md`, `panel-primary.md`, `panel-gpt-5.6-sol-medium.md`). The grep prints `0`: no diff markers or reviewer prose in the trial JSON.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Fixed 2026-10-01: `_plural` printed "0 keies" until it learned that only a consonant before "y" takes "-ies". Pinned by `test_plural_only_turns_consonant_y_into_ies` and `test_record_summary_reads_zero_keys`.

---

### Scenario 39: trial-record refuses mismatched arm arguments

**Source:** Acceptance Criteria — Story 4 (AC-4.3)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Same scratch setup as Scenario 38.

**Steps:**
1. Run `python3 $RP trial-record --trial trial.json --story 2026-01-02-beta/story-2-ui --arm evaluator --origin "Claude Opus 5.5" --primary $F/primary-pass.md --reviewer gpt-5.6-sol-medium=$F/panel-ac23.md; echo "exit $?"`
2. Run `python3 $RP trial-record --trial trial.json --story 2026-01-02-beta/story-2-ui --arm panel --origin "Claude Opus 5.5" --primary $F/primary-pass.md; echo "exit $?"`

**Expected Result:**
- Step 1: `review-panel: usage — the evaluator arm takes no --reviewer`, `exit 2`.
- Step 2: `review-panel: usage — the panel arm needs at least one --reviewer`, `exit 2`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 40: trial-label validates label, key, and note before writing

**Source:** Acceptance Criteria — Story 4 (AC-4.4)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- The trial file from Scenario 38 (one panel-only finding `ac:AC-2.3` on story `2026-01-01-alpha/story-1-api`).

**Steps:**
1. Run `python3 $RP trial-label --trial trial.json --story 2026-01-01-alpha/story-1-api --key ac:AC-2.3 --label maybe --note x; echo "exit $?"`
2. Repeat with `--key ac:AC-9.9 --label valid`.
3. Repeat with `--key ac:AC-2.3 --label valid --note "$(python3 -c 'print("x"*201)')"`
4. Run `python3 $RP trial-label --trial trial.json --story 2026-01-01-alpha/story-1-api --key ac:AC-2.3 --label invalid --note "AC-2.3 was met at that commit"; echo "exit $?"`

**Expected Result:**
- Step 1: `review-panel: usage — --label must be valid or invalid`, `exit 2`.
- Step 2: `review-panel: usage — ac:AC-9.9 is not a panel-only finding for 2026-01-01-alpha/story-1-api`, `exit 2`.
- Step 3: `review-panel: usage — --note must be one line of at most 200 characters, no code block`, `exit 2`.
- Step 4: `labeled`, `review-panel: labeled 2026-01-01-alpha/story-1-api ac:AC-2.3 invalid`, `exit 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 41: trial-report decides unverifiable, remove, and keep

**Source:** Acceptance Criteria — Story 4 (AC-4.5); Error Map — Trial report (unlabeled finding or missing arm)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- The scratch trial files from Scenarios 35 and 38.

**Steps:**
1. Run `python3 $RP trial-report --trial $T/trial.json` on the fresh skeleton from Scenario 35.
2. In `W`, run `python3 $RP trial-report --trial trial.json` before labeling (after Scenario 38 step 3).
3. Run it again after labeling `invalid` (Scenario 40 step 4).
4. Relabel `--label valid --note "AC-2.3 really unmet at that commit"`, then run it again.

**Expected Result:**
- Step 1: `unverifiable`, eight `reason: missing_arm <story> <arm>` lines, four `story: … arms=none …` lines, the caveat line, and `review-panel: unverifiable — 4 stories missing an arm`.
- Step 2: `unverifiable`, `reason: unlabeled 2026-01-01-alpha/story-1-api ac:AC-2.3`, per-story lines (`arms=evaluator,panel panel_only=1 valid=0 invalid=0 unlabeled=1` for story 1), the caveat, and `review-panel: unverifiable — 1 unlabeled`.
- Step 3: `remove`, per-story lines, `sample: 4 stories; one valid miss keeps the panel — a low bar, not a cost case`, and `review-panel: remove — 0 valid of 1 panel-only finding, 4 stories`.
- Step 4: `keep`, per-story lines, the caveat, and `review-panel: keep — 1 valid of 1 panel-only finding, 4 stories`.
- Every run exits 0.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Per DEV-007, any unlabeled finding or missing arm makes the result `unverifiable`, even when a `valid` label already exists.

---

## ⚠️ Maintainer Handoff — Story 5 Trial Procedure (Not Started)

> **Story 5 is not complete.** These steps are not acceptance scenarios for built behavior. They are the procedure the maintainer runs to complete Story 5, written as human checks.
> **Requires:** Cursor; real cross-vendor model spend; a temporary `- **Review Panel:**` line in this repo's `.writ/config.md`; read-only access to `~/Projects/yuss`; maintainer judgment to label findings.
> **Never:** write inside `~/Projects/yuss`, commit raw reviewer outputs, or change wiring before the trial record is committed.
> Source: `user-stories/story-5-run-trial-and-act.md`, `sub-specs/technical-spec.md` → Trial Harness / Trial Execution and Verdict.

### Scenario 42: Snapshot yuss before the trial

**Source:** Acceptance Criteria — Story 5 (AC-5.1), task 5.2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `~/Projects/yuss` exists and contains the four baseline commits.

**Steps:**
1. Run `{ git -C ~/Projects/yuss rev-parse HEAD; git -C ~/Projects/yuss status --porcelain; git -C ~/Projects/yuss show-ref; } > .writ/state/yuss-before.txt`

**Expected Result:**
- The file exists under the gitignored `.writ/state/`, and nothing was written in yuss.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 43: Add the session's panel line and confirm `status` passes

**Source:** Acceptance Criteria — Story 5 (AC-5.1), task 5.2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- A Cursor session whose model you know (the "origin"). Pick up to 3 slugs from other vendors in Cursor's model list.

**Steps:**
1. Add one line to `.writ/config.md`: `- **Review Panel:** <slug>, <slug>[, <slug>]`
2. Run `python3 scripts/review-panel.py status --repo . --origin "<session model>" --platform cursor`

**Expected Result:**
- `pass`, one `reviewer: <slug> <vendor>` line per reviewer, no unexpected `dropped:` lines, and a `review-panel: pass — N reviewers (…)` summary.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Keep this line uncommitted until the verdict. On `remove`, delete it (Scenario 53).

---

### Scenario 44: Initialize the committed trial file

**Source:** Acceptance Criteria — Story 5 (AC-5.1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Scenario 43 passed.

**Steps:**
1. Run `python3 scripts/review-panel.py trial-init --baseline .writ/eval/baselines/2026-09-07-claude-fable-5-1.json --out .writ/eval/panel-trial/<YYYY-MM-DD>-panel-trial.json`

**Expected Result:**
- Output matches Scenario 35 step 1: the four yuss story IDs and `review-panel: trial initialized — 4 stories, no arms recorded`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 45: Prepare each story's inputs from yuss (read-only)

**Source:** Acceptance Criteria — Story 5 (AC-5.1); Error Map — Trial prepare
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Run outside any sandbox. Inside Cursor's agent sandbox, `git init` fails (see Scenario 36).

**Steps:**
1. For each story ID printed in Scenario 44, run `python3 scripts/review-panel.py trial-prepare --trial .writ/eval/panel-trial/<date>-panel-trial.json --yuss ~/Projects/yuss --story <id>`

**Expected Result:**
- Each run prints `prepared`, `checkout:`, `diff:`, `story:`, `contract:` paths under `$TMPDIR/writ-panel-trial-<spec>--<story>/`, and `review-panel: prepared <id> <sha12>`.
- Any exit 2 names the story (missing path, unreachable commit, parent beyond depth 2, or no contract section) and writes nothing. Stop and resolve it before continuing.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 46: Run the evaluator-alone arm for each story

**Source:** Acceptance Criteria — Story 5 (AC-5.1), task 5.2; technical spec → Arms
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Scenario 45 passed for the story.

**Steps:**
1. In Cursor, spawn the evaluator prompt (`agents/evaluator-agent.md`) once at the session model, over that story's `diff.patch`, `story.md`, and `contract.md`. Provide `recorded_test_results` as the story's own What Was Built test results, labeled "historical, not re-run".
2. Save its output to `.writ/state/panel-trial-inbox/<story-slug>-evaluator.md`.
3. Run `python3 scripts/review-panel.py trial-record --trial .writ/eval/panel-trial/<date>-panel-trial.json --story <id> --arm evaluator --origin "<session model>" --primary .writ/state/panel-trial-inbox/<story-slug>-evaluator.md`

**Expected Result:**
- `recorded` and `review-panel: recorded <id> evaluator — N key(s), M panel-only finding(s)`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 47: Run the evaluator + panel arm for each story with identical inputs

**Source:** Acceptance Criteria — Story 5 (AC-5.1), task 5.2
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Scenario 46 done for the story. The same prepared inputs and the same historical test results.

**Steps:**
1. In Cursor, in **one message**, spawn the evaluator prompt at the session model plus each configured reviewer at its slug (`readonly`, with the exclusion line), over the identical inputs.
2. Save each output under `.writ/state/panel-trial-inbox/`.
3. Run `python3 scripts/review-panel.py trial-record --trial <file> --story <id> --arm panel --origin "<session model>" --primary <primary out> --reviewer <slug>=<out> [--reviewer …]`

**Expected Result:**
- `recorded`, any `review-panel: dropped <slug> — <reason>` lines, and `review-panel: recorded <id> panel — N keys, M panel-only findings`.
- Raw copies appear under `.writ/state/panel-trial/<spec>--<story>/`.

**Status:** [ ] Pass  [ ] Fail

**Notes:** Record which reviewers were dropped. A dropped reviewer weakens the arm but does not invalidate it.

---

### Scenario 48: Confirm yuss is unchanged and the trial file holds no text

**Source:** Acceptance Criteria — Story 5 (AC-5.1)
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- All four stories have both arms recorded.

**Steps:**
1. Run `{ git -C ~/Projects/yuss rev-parse HEAD; git -C ~/Projects/yuss status --porcelain; git -C ~/Projects/yuss show-ref; } | diff - .writ/state/yuss-before.txt && echo unchanged`
2. Run `grep -cE '@@|\+\+\+' .writ/eval/panel-trial/<date>-panel-trial.json`
3. Run `git status --porcelain` and confirm no `.writ/state/` paths appear.

**Expected Result:**
- Step 1 prints `unchanged`.
- Step 2 prints `0`.
- Step 3 shows only the trial JSON (and the uncommitted config line); raw outputs stay ignored.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 49: Label every panel-only finding honestly

**Source:** Acceptance Criteria — Story 5 (AC-5.1), task 5.3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Run `python3 scripts/review-panel.py trial-report --trial <file>` and list every `reason: unlabeled <story> <key>` line.

**Steps:**
1. For each unlabeled key, read the raw outputs in `.writ/state/panel-trial/` and the story's acceptance criteria at that commit.
2. Run `python3 scripts/review-panel.py trial-label --trial <file> --story <id> --key <key> --label valid|invalid --note "<≤200 chars, no source>"`. Use `valid` only for a real unmet AC or a real Critical/Major security or architecture defect at that commit. If the evaluator arm caught the same issue under another key, say so in the note.

**Expected Result:**
- Each call prints `labeled` and `review-panel: labeled <id> <key> <label>`.
- A re-run of `trial-report` shows no `unlabeled` reasons.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 50: Commit the trial record before touching any wiring

**Source:** Acceptance Criteria — Story 5 (AC-5.2), task 5.3
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Scenario 49 complete.

**Steps:**
1. Run `python3 scripts/review-panel.py trial-report --trial <file> > .writ/specs/2026-10-01-cross-family-review-panel/trial-report.md`
2. Confirm the file's first line is `keep`, `remove`, or `unverifiable`, and that it contains `sample: 4 stories; one valid miss keeps the panel — a low bar, not a cost case`.
3. Commit the trial JSON and `trial-report.md` together, without the config line and before any other change.

**Expected Result:**
- `git log -1 --stat` shows exactly those two files.
- This commit precedes any keep, remove, or status commit (it is the permanent record if the script is later deleted).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 51: On `keep` — record the result and leave all wiring in place

**Source:** Acceptance Criteria — Story 5 (AC-5.3), task 5.4
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `trial-report.md` verdict is `keep`.

**Steps:**
1. Amend ADR-028's Decision 3 amendment with the date, the four story IDs, the count and keys of valid panel-only findings, and the small-sample caveat (targeted edit only).
2. Mark roadmap Phase 12 success criterion 4 met, with a link to `trial-report.md` (targeted edit only).
3. Set `spec.md` `> **Status:** Complete`, and mark Story 5 Completed.
4. Run `bash scripts/eval.sh --check=review-panel` (outside the sandbox).

**Expected Result:**
- The panel paragraph, `--panel` row, report entry, config doc entry, adapter rows, `check_review_panel`, `status`/`tally`, tests, and pins all remain.
- Step 4: `PASS`, `Findings: 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 52: On `remove` — delete the panel path, keep the agent tags

**Source:** Acceptance Criteria — Story 5 (AC-5.4), task 5.5
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- `trial-report.md` verdict is `remove`, and Scenario 50's commit exists.

**Steps:**
1. Delete the `**Review panel (opt-in).**` paragraph, the `--panel` row (and the `--panel`/`--quick` clause), the `review-panel:` report entry, and the Overview and Gate 3.5 panel clauses from both `implement-story` files. Then delete the `Review Panel` row and section from `.writ/docs/config-format.md`, the four adapter rows, and `check_review_panel` with its `CHECKS` entry.
2. Delete `scripts/review-panel.py`, `scripts/tests/test_review_panel.py`, and `scripts/tests/fixtures/review-panel/`. Keep the `[AC-N.M]` tags and `- **Category:**` lines in `agents/`, `claude-code/agents/`, and `codex/agents/*.toml`.
3. Re-pin `"commands/implement-story.md"` downward in `scripts/tests/test_governor_enforcement.py` with a dated disclosure naming this spec and Story 5. Re-pin the lean sha in `test_lean_commands.py`.
4. Record the removal in ADR-028, mark roadmap criterion 4 met by its second branch, and set `spec.md` `> **Status:** Closed — Not Implemented`.
5. Run `rg -n 'review-panel|Review Panel|--panel' commands adapters scripts .writ/docs`

**Expected Result:**
- Step 5 returns no wiring hits.
- `rg -n '\*\*Category:\*\*' agents/` still matches, and `python3 scripts/gen-codex-agent-tomls.py --check` passes.
- The trial JSON and `trial-report.md` remain committed.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 53: Close out — config line, unverifiable handling, outcome test, full suite

**Source:** Acceptance Criteria — Story 5 (AC-5.2, AC-5.5), tasks 5.1, 5.6, 5.7
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Scenario 51 or 52 done, or the verdict was `unverifiable`.

**Steps:**
1. On `unverifiable`: set `spec.md` `> **Status:**` to name the blocking reason from the report's `reason:` lines, add or remove no wiring, and stop.
2. On `remove`, delete the `Review Panel` line from `.writ/config.md`. On `keep`, decide whether this repo should keep it, since it is consent to send story content to other vendors.
3. Write `scripts/tests/test_panel_trial_outcome.py` per task 5.1 (stdlib only, no import of `review-panel.py`), then run `uv run pytest scripts/tests/test_panel_trial_outcome.py`.
4. Run `uv run pytest`, `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` (outside the sandbox).

**Expected Result:**
- The outcome test passes only when the trial file validates and the `trial-report.md` verdict matches `spec.md` (`keep` ↔ `Complete`, `remove` ↔ `Closed — Not Implemented`). The panel paragraph must be present for `keep` and absent for `remove`.
- Everything is green, and eval reports `Findings: 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 54: Verify commit order and the final verdict-to-status agreement

**Source:** Acceptance Criteria — Story 5 (AC-5.2), task 5.6
**Feature:** none
**Verification:** human — no recipe

**Preconditions:**
- Story 5 closed.

**Steps:**
1. Run `git log --oneline -- .writ/specs/2026-10-01-cross-family-review-panel/trial-report.md commands/implement-story.md | head`
2. Compare the first line of `trial-report.md` with `spec.md`'s `> **Status:**`.

**Expected Result:**
- The commit adding `trial-report.md` is older than any commit that removed panel wiring.
- The verdict and status agree.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

The following story is not yet complete. Its trial procedure is in the Maintainer Handoff section above, and its acceptance scenarios will be regenerated when it completes:

- **Story 5:** Run the trial and act on the verdict (keep, or close and remove) — Status: Not Started

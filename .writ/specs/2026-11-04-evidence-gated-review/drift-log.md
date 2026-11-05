# Drift Log

> Spec: .writ/specs/2026-11-04-evidence-gated-review/
> Created: 2026-11-04
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: ADR-032 and the review-surface inventory — Drift Report

> Run: 2026-11-04
> Overall Drift: Large

### Deviations

#### [DEV-001] The reviewer filters stay; the spec no longer removes them
- **Severity:** Large
- **Spec said:** Contract Must Include 1 and 6, Success Criteria, and Scope Boundaries remove the reviewer filters: `skills/review-judgment-filters/`, the `reviewer-filters` switch, the `Reviewer Filters` config key, the agents' `reviewer_filters` input row and `Read` line, Gate 3's "Reviewer filters." paragraph, and `/review`'s Step 3 filters `Read` and switch line. The spec took over the removal trial's Reviewer Filters verdict.
- **Implementation did:** During `/implement-spec`, Story 1's inventory had to give the reviewer filters a verdict. The removal measurement (`.writ/specs/2026-10-25-gate-upgrade-removal-measurement/trial-report.md`, commit `ef0c418`) had recorded Reviewer Filters `keep`: 1 valid upgrade-only catch on 4 stories. The catch is F01, Critical, `ac:AC-4.3`, a stale doc claim. The user chose to keep the filters.
- **Reason:** The trial's verdict contradicts the contract's removal. Removing the filters would drop the only trial arm that raised F01. The trial also kept Safety Fact, which fits with raising its floor.
- **Resolution:** Pipeline paused — spec modified by user
- **Spec amendment:** `spec.md` gains `### Amendment (2026-11-04, during /implement-spec)` after the authoring corrections. It overrides the Deliverable's filter clause, Must Include 1, 6, and 8 (the roadmap filters criterion stays), the Success Criteria scan (panel names only), Scope Included, Recommendations story 5, and the Cross-Spec Overlap `/edit-spec` precondition (void). Story 6 becomes "Raise the Safety Fact floor to `tested`" (`story-6-raise-safety-fact-floor.md`). Story 7 writes the panel scan test and trims "panel reviewers" from Gate 3's filters paragraph. Story 5 puts the evidence header and `Read` beside the filters ones. `spec.md` no longer amends `2026-10-25-gate-upgrade-removal-measurement`, and that spec's Superseded-by line is removed. Evidence gating, the panel removal, and the `tested` floor are unchanged.

#### [DEV-002] ADR-032 Removals points to technical-spec.md for test files and generated trees
- **Severity:** Small
- **Spec said:** AC-1.4: the ADR-032 removal list names every file, section, and config key in technical-spec.md's Removals tables, which include `Tests` and `Generated trees` rows.
- **Implementation did:** ADR-032 § Removals names every product file, section, function, flag, and config key, and covers the test updates and regenerated trees with one pointer to technical-spec.md § Removals. The test skips those two rows (`NON_FILE_ROWS`).
- **Reason:** Stories 6 and 7 work from technical-spec.md, not from the ADR. Listing every test file in the ADR adds names that go stale.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md, For Review Agents → Business Rules, gains: "ADR-032 § Removals names every product file, section, and config key, and points to technical-spec § Removals for test updates and regenerated trees (DEV-002)."

---

## Story 2: Evidence skill and the `evidence` subcommand — Drift Report

> Run: 2026-11-04
> Overall Drift: Medium

### Deviations

#### [DEV-003] The run-level `no_test_runner` treats findings with no evidence as undecided ⚠️
- **Severity:** Medium
- **Spec said:** technical-spec § Error & Rescue Map: with no `Test Runner` line, "`test` findings `unverifiable no_test_runner`; when no finding can be decided otherwise, line 1 `unverifiable no_test_runner`". § Evidence outcomes: "A finding with no `Evidence:` block is `advisory (no_evidence)`".
- **Implementation did:** Line 1 is `unverifiable no_test_runner` when all of these hold:
  - there is no `Test Runner`;
  - at least one finding passed selection;
  - no `recorded`, `check`, or `security-path` finding reached a non-unverifiable outcome.

  A selected finding with no evidence counts as undecided. So with no `Test Runner`, a FAIL whose only Major findings carry no evidence keeps the agent's FAIL (Gate 3 row 8). The same FAIL is downgraded to PASS (row 9) when a `Test Runner` exists or the runner token is unknown. `test_no_test_runner_leaves_the_call_unverifiable` fixes this reading.
- **Reason:** The spec text supports both readings. The implementation's reading matches the Error experience bullet ("no `Test Runner` … the agent verdict stands"). A literal reading of "decided" would downgrade instead. The Gate 3 result differs between the two.
- **Resolution:** ⚠️ Medium — logged, PASS (agent verdict stands on no Test Runner, per Experience Design)
- **Spec amendment:** (if kept) technical-spec § Error & Rescue Map, Resolve the runner: "…when no `recorded`, `check`, or `security-path` finding reaches `confirmed` or `advisory`, line 1 is `unverifiable no_test_runner`; findings with no Evidence do not count as decided."

#### [DEV-004] Finding lines end with ` at <location>`, and unverifiable findings print `advisory (unverifiable <reason>)`
- **Severity:** Small
- **Spec said:** technical-spec § Evidence Block Grammar: "Each per-finding line also prints the normalized Location". The § CLI example shows no location, and AC-2.3 lists `unverifiable <reason>`.
- **Implementation did:** `finding F1: confirmed (test <path>, exit 1) at src/limits.py`, and `advisory (unverifiable <reason>) at …`, as in the § CLI example's F3 line.
- **Reason:** It follows the grammar rule and the example's F3 form. Story 3 must parse the suffix.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** technical-spec § CLI example: append ` at api/limits.py` to each `finding` line, and add "A finding without a Location omits the ` at` suffix."

#### [DEV-005] The `evidence-gate` switch pattern uses `[ \t]*`, not `\s*`
- **Severity:** Small
- **Spec said:** `^\s*-\s*\*\*Evidence Gate:\*\*\s*(.*)$`
- **Implementation did:** `^[ \t]*-[ \t]*\*\*Evidence Gate:\*\*[ \t]*(.*)$`
- **Reason:** With `re.MULTILINE`, `\s*` crosses a newline, so an empty value would read the next line. Behavior otherwise matches.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** technical-spec § CLI: use `^[ \t]*-[ \t]*\*\*Evidence Gate:\*\*[ \t]*(.*)$`.

#### [DEV-006] Findings with malformed fields get specific reasons, not `no_evidence`
- **Severity:** Small
- **Spec said:** Error & Rescue, Parse issues: malformed fields → "Every finding `advisory (no_evidence)`; line 1 `pass`".
- **Implementation did:** A missing Severity gives `advisory (low_severity none)`, and a missing Location gives `advisory (location_outside_change_set)`. Line 1 is still `pass`.
- **Reason:** Same outcome, more specific reason codes. The skill lists both.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** Error & Rescue, Parse issues: "…each finding is advisory with the first selection rule it fails (`low_severity none`, `location_outside_change_set`, `no_claim`, `no_evidence`); line 1 `pass`."

#### [DEV-007] The snapshot hashes every status path, records HEAD, and runs git with read-only flags
- **Severity:** Small
- **Spec said:** technical-spec § Tree Snapshot: status list, `diff HEAD --binary` hash, and a hash of each untracked file.
- **Implementation did:** Four additions to the snapshot.
  - It hashes the working-tree bytes of every status path, not only untracked ones.
  - It records HEAD's commit (`rev-parse --verify -q HEAD`) and branch (`symbolic-ref -q HEAD`), and reports `(HEAD)` when only those differ.
  - It adds `--no-optional-locks`, `core.fsmonitor=false`, `--no-ext-diff`, and `--no-textconv`.
  - It diffs against the empty tree when there is no commit.
- **Reason:** A strict superset that catches more cases, including a commit or checkout on a clean tree. It runs no git command that writes.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** § Tree Snapshot step 3: "Every path from step 1 is hashed…". Add step 4: "HEAD's commit and symbolic ref are recorded; a difference there alone is `repro_mutated_tree (HEAD)`." Add: "git runs with `--no-optional-locks` and no external diff or textconv."

#### [DEV-008] The scoped command keeps `Test Runner` tokens through the runner word only
- **Severity:** Small
- **Spec said:** Runner Classification: `<runner> <path>` and similar forms. It does not say what happens to flags in the `Test Runner` value.
- **Implementation did:** It keeps the prefix and the runner word, plus `test` for go and cargo and `run` for vitest. It drops later flags and strips a trailing `(detected: …)` note. `npm test` adds `--` before the scoped argument.
- **Reason:** Arguments like `./...` or `tests` would widen the run past the repro file.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** Runner Classification: "`<runner>` is the `Test Runner` tokens through the runner word; later arguments are dropped."

#### [DEV-009] The pytest test-failed class needs a failed count, not exit 1 alone
- **Severity:** Small
- **Spec said:** technical-spec § Runner Classification, pytest row: confirmed on "exit 1"; unverifiable on "exit 2 to 5".
- **Implementation did:** It confirms on exit 1 only when the output has a `N failed` count with N ≥ 1. Exit 1 without one, such as a setup error (`1 error`) or an interpreter that cannot import pytest, is `collection_error`.
- **Reason:** It meets the contract's rules that "Runners report a failing test and a broken test … differently" and "One broken repro makes that finding advisory". It matches the jest, vitest, and rspec rows, which already require a failed count. The review asked for this change (first review, Issue 1).
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** technical-spec § Runner Classification, pytest row: Test-failed class "exit 1 and a summary with `N failed`, N ≥ 1"; Everything else "exit 1 without a failed count (setup errors, an interpreter without pytest), exit 2 to 5".

---

## Story 3: Gate 3 wiring for evidence-gated findings — Drift Report

> Run: 2026-11-04
> Overall Drift: Medium

### Deviations

#### [DEV-010] Byte budget: Story 4 has about 170 bytes left
- **Severity:** Medium
- **Spec said:** spec.md → Implementation Approach → Byte budget: the net change to `commands/implement-story.md` across Stories 3, 4, and 7 is ≤ 0, and "Story 7's panel removals … must free at least what Stories 3 and 4 add."
- **Implementation did:** Story 3 is now +1180 (40759 → 41939), down from +1419 after the five cuts:
  - the check bullet shortened
  - `--repo .` dropped
  - the duplicated contradicts bullet dropped
  - the FAIL-only sentence dropped
  - the stale architecture/security/taste sentence dropped

  Story 7's measured panel removals are about 1,500 bytes gross:
  - paragraph: 1,179
  - Invocation row: 120
  - usage clause: 40
  - Overview: 36
  - Gate 3.5 clause: 70
  - smaller mentions: 47
  - the "panel `block`" rewording: about 25

  After its two removal messages, about 1,350 net. That leaves Story 4 about 170 bytes. Story 4's minimum additions are larger:
  - ` --manifest-out .writ/state/evidence-<story-stem>.json`: 54 bytes
  - the `--prior` form: about 49
  - row 3a: about 110
  - the `## Evidence repros` recode brief with its no-edit line: about 200
  - the manifest paths in the re-review's recorded run: about 80

  Roughly 450 to 500 bytes, so the spec total lands near +300.
- **Reason:** Story 3 now fits its share. The spec constraint still fails at Story 7 unless Story 4 cuts or the spec is amended.
- **Resolution:** ⚠️ Medium — logged, PASS. Carried to Story 4 (apply the reviewer's −219 bytes of binding cuts) and Story 7; if the net is still above 0 at Story 7, the user decides.
  1. Bind `<manifest>` once, as the save line now binds `<review>` and `<tests>`, so `--manifest-out` and `--prior` do not repeat the path (about −45).
  2. Bind `<checks>` in the Gate 2 sentence and use it in the command (about −24).
  3. Make the Gate 3 save unconditional, so the Jev shadow can reuse `<review>` and `<tests>`. This cuts its 177-byte "save the recorded test output (…) under `.writ/state/`" clause and 76-byte argument list down to the diff save (about −150). `test_jev_shadow_hooks.sh` pins "targeted run" and "not the full suite", so those pins move with it.
  4. Amend the byte-budget rule if the user accepts a small positive net.
- **Spec amendment:** None yet. If Stories 4 and 7 cannot reach net ≤ 0, the user decides whether to amend spec.md → Implementation Approach → Byte budget.

#### [DEV-011] Gate 3 passes `--timeout 60`
- **Severity:** Small
- **Spec said:** technical-spec § Gate 3 Wiring's command has no `--timeout`, so the default is 120 s.
- **Implementation did:** `--timeout 60`, so five runs fit the 600 s tool limit (Story 2's note).
- **Reason:** Cosmetic. Spec intent is preserved.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** technical-spec § Gate 3 Wiring: drop `--repo .` from the command and add `--timeout 60`. Add "`--repo` defaults to `.`; Gate 3 passes `--timeout 60` so five runs fit a 600 s tool call."

---

## Story 5: Evidence gating in `/review` — Drift Report

> Run: 2026-11-04
> Overall Drift: Medium

### Deviations

#### [DEV-012] A tree mutation on `/review` is run-level `unverifiable`, and the command stops on the reason
- **Severity:** Small (Medium in iteration 1; the stop added in recode 1 restores BLOCKED)
- **Spec said:** Contract Hardest Constraint: "the result is BLOCKED with `repro_mutated_tree`." technical-spec § CLI: line 1 `fail` when the tree changed, with that reason first.
- **Implementation did:** `--surface review` prints `unverifiable` and `evidence-gate: unverifiable (repro_mutated_tree <paths>)` with that reason, exit 0, and no finding lines (`scripts/review-override.py:1393`). Step 4's first rule stops on the reason and holds back the Recommendation and `/ship` until the user decides (`commands/review.md:192`). "First rule that matches" is now pinned.
- **Reason:** The contract's BLOCKED is a human gate keyed on the reason, as on Gate 3 (decision row 6), and the stop provides it. Only technical-spec § CLI's line-1 word differs.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** technical-spec § CLI: "On `--surface review`, a tree change prints line 1 `unverifiable` with `reason: repro_mutated_tree <paths>` and no finding lines; `/review` stops on that reason until the user decides."

#### [DEV-013] With no `Test Runner`, `/review` stays run-level unless a `security-path` row reaches confirmed or advisory
- **Severity:** Small
- **Spec said:** § /review: run-level `unverifiable` includes "`no_test_runner` with no `security-path` rows".
- **Implementation did:** DEV-003's rule. A run whose `security-path` rows are all unverifiable stays run-level, and its severities stay as written. `test_no_test_runner_with_an_advisory_security_path_row` covers the advisory side (kills M24).
- **Reason:** It is consistent with Gate 3. A broken citation does not flip every other row to gated.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** § /review: replace "`no_test_runner` with no `security-path` rows" with "`no_test_runner` when no `security-path` row reaches `confirmed` or `advisory`".

#### [DEV-014] `/review` output form: line 2 is the header value, and finding lines end `; severity <mapped>`
- **Severity:** Small
- **Spec said:** technical-spec § CLI shows only the Gate 3 form. Task 5.5 gives no format for the mapped severity.
- **Implementation did:** Line 2 is `evidence-gate: on|off|unverifiable (<reason>)`. Each `finding FM-NNN:` line ends `; severity <word>`, where the word is the cell's first word, or `Medium (unconfirmed)`.
- **Reason:** Step 4 reads both mechanically, and the intent is kept.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** technical-spec § CLI: "On `--surface review`, line 2 is `evidence-gate: on|off|unverifiable (<reason>)`, and each `finding FM-NNN:` line ends `; severity <mapped>`."

#### [DEV-015] Registry and block binding rules the spec leaves open
- **Severity:** Small
- **Spec said:** technical-spec § /review form shows a block with its own Category. The spec does not say which Category wins, or what a repeated block or row does.
- **Implementation did:** The block's Category wins, with the registry's as fallback, and the registry's Severity always wins. A second block for an ID adds `reason: extra_evidence FM-NNN`. A repeated registry row is dropped with `reason: duplicate_row FM-NNN`.
- **Reason:** These follow the Gate 3 parsing rules, and the intent is kept.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** technical-spec § /review form: "The block's Category wins over the registry's; the registry's Severity always wins. A second block for an ID is ignored with `reason: extra_evidence FM-NNN`, and a repeated registry row with `reason: duplicate_row FM-NNN`."

#### [DEV-016] `/review` always asks before the evidence run (`untrusted_branch`)
- **Severity:** Medium
- **Spec said:** § /review lists the run-level `unverifiable` reasons as `no_review_output`, `no_git`, and `no_test_runner`. It has no consent step.
- **Implementation did:** Step 4 asks with AskQuestion before every run. A decline, a headless run, or no answer skips the run, writes `unverifiable (untrusted_branch)`, and leaves every severity as written (`commands/review.md:182`). The iteration-2 email rule (`%ae`, `user.email`, `<base>`) is removed.
- **Reason:** The user decided twice on 2026-11-04. First, "ask unless it's yours". Then, after the forged-author finding, "always ask". This adds a behavior and a reason code the spec lacks. Issue 1 is its one open edge: the question also fires with the gate `off`.
- **Resolution:** ⚠️ Medium — logged, PASS. User-approved on 2026-11-04 (two decisions: ask unless yours, then always ask).
- **Spec amendment:** § /review: "With the evidence gate `on`, `/review` asks before every evidence run. A decline, a headless run, or no answer gives `unverifiable (untrusted_branch)`, and every severity stays as written."

#### [DEV-017] `/review` passes `--timeout 60`
- **Severity:** Small
- **Spec said:** technical-spec § CLI default timeout is 120 s. DEV-011 set 60 s for Gate 3.
- **Implementation did:** The Step 4 command passes `--timeout 60`, pinned by `test_step4_runs_evidence_on_the_draft_then_maps_severities`.
- **Reason:** Five runs fit a 600 s tool call, as on Gate 3.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** technical-spec § CLI: "`/review` passes `--timeout 60`, as Gate 3 does (DEV-011)."

#### [DEV-018] A confirmed repro was not committed: the user's decision overtook it
- **Severity:** Medium
- **Spec said:** Business Rules: the coder commits a confirmed repro byte for byte and never edits it; disputes go to the loop cap and then to the user.
- **Implementation did:** The iteration-2 repro `scripts/tests/test_review_trust_rule_repro.py` was confirmed, but it asserted `"every commit"`, which encodes the email rule. The user then replaced that rule with always-ask. The orchestrator did not commit the repro. Its other intent (no answer or headless = decline) is pinned by `test_step4_always_asks_before_running_repros`, and the iteration-3 reviewer agreed.
- **Reason:** A repro that asserts a rule the user removed cannot pass without restoring the removed rule. That is a user decision, not a coder dispute.
- **Resolution:** ⚠️ Medium — logged, PASS.
- **Spec amendment:** None. Story 4's re-review check (`repro_removed`) only covers repros listed in a manifest; this one never entered one.


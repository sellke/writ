# Cut Log: create-spec.md Reduction

> Start: 37e097e, 53612 bytes, overage 28652 · End: pending, overage pending

Spec: `2026-10-20-shipped-command-hygiene`, Story 3. The candidate list is the lean twin (`git show 617037b:commands/create-spec.lean.md`), diffed against `commands/create-spec.md` at the start commit. Each twin change was decided against the current text, not the twin's wording. Adopted rows remove coaching and have class `coaching`; every hunk of `git diff 37e097e -- commands/create-spec.md` maps to one of them. Declined rows name what the change would have touched, and have no hunk. A row marked *re-decided* differs from the technical spec's candidate table because the current text differs from what that table assumed.

## Start state (37e097e)

- `#### Step` headings (29): `--from-prototype` Steps 0, 1, 2, 3; `--from-issue` Steps 0, 1, 2, 3; Steps 1.0, 1.1, 1.2, 1.3, 1.3b, 1.4, 1.4b, 1.5; Steps 2.1, 2.2, 2.3, 2.4, 2.4b, 2.5, 2.6, 2.6a, 2.6b, 2.6c, 2.7, 2.8, 2.9.
- AskQuestion blocks (4): "Feature Specification - What would you like to build?" (Step 1.0), "Contract Decision" (Step 1.4b), "Visual References" (Step 1.5), "Jev judgment provider" (Step 2.6c, Jev setup).
- Script invocations (7): `python3 scripts/spec-status.py is-complete --file <path>` (1.3b); `python3 scripts/supersession-writeback.py apply --new-spec-file …` (2.4b); `python3 scripts/ac-trace.py check --spec … --repo …` (2.6a); `python3 scripts/jev-judge.py status`, `python3 scripts/jev-judge.py spec-findings --spec … --out …`, and `python3 scripts/jev-judge.py setup --provider` (2.6c); `python3 scripts/spec-analyze.py check --spec … [--findings …]` (2.6c).
- `eval.sh` keep pins on the file: pin-map.md rows 3, 4, 6–13, 15, 16, 26, 29, 39, 67, 68.
- `command-structure` rows on the file: heading `` Authoritative `--recommend` Invocation Matrix ``, heading `Required Artifacts`, invocation `scripts/spec-status.py is-complete`, invocation `scripts/supersession-writeback.py apply`.
- Other readers of the file's text: `test_jev_setup_hooks.sh` and `test_spec_analyze_command_hooks.sh` (Steps 2.6c and 2.9), `test_harness_cuts.py` (Step 2.6a), `test_platform_neutral_names.py` (Step 1.5 `/writ-design` line, `.writ/docs/design-system.md`), `eval-artifact-integrity.py` (`## Required Artifacts`), `eval-leanness.py` (frontmatter contract, `## Completion`).

## Adopted

| # | Section | Change | Class | Reason |
|---|---|---|---|---|
| 1 | Overview | Two framing sentences shortened; the bold Plan Mode/AskQuestion phrasing dropped | coaching | Same rule with less framing |
| 2 | `--from-prototype` intro | "Used when…" and "This mode replaces…" folded into the Invocation line | coaching | Duplicated framing; the trigger and the Phase 1 replacement stay |
| 3 | `--from-prototype` Step 0, items 1–3 | "It carries…", "Extract:", and "— it describes what was built and how" trimmed | coaching | Explains what each source holds; every read stays |
| 4 | `--from-prototype` Step 0, item 4 | Five sub-bullets folded into one line | coaching | Format only; each field and "never invent alternatives" stay |
| 5 | `--from-prototype`, "Never mark Story 1 complete" | Clause on what a wrong spec causes removed | coaching | Rationale; the rule and "a chosen draft is a decision, not an implementation" stay |
| 6 | `--from-prototype` Step 1 | "Opening framing" label and blockquotes folded into the paragraph | coaching | Format only; both opening lines, the gap list, and the skip rule stay. *Re-decided:* the prototype reframe had already shortened this step, so only the framing merge was left |
| 7 | `--from-prototype` Step 2 | Intro sentences and the "Key contract shape" label merged into one line | coaching | Duplicated framing; the contract block is unchanged |
| 8 | `--from-prototype` Step 3 | "Why:" paragraph folded into a parenthetical; the paragraph's lead shortened | coaching | Rationale; the Story 1 status rule and its exception stay. *Re-decided:* "none of the bullets below apply" pointed at bullets that were already prose; it now reads "the rest of this paragraph does not apply" |
| 9 | `--from-issue` intro | Description and "This mode replaces…" folded into the Invocation line | coaching | Duplicated framing; "pre-populating the contract" repeats Step 0 item 3 |
| 10 | `--from-issue` Step 0, items 1–3 | Path check, field list, and draft bullets folded into one line each; the "Fix/Add" example dropped | coaching | Format and an example; same fields, same error block, same draft |
| 11 | `--from-issue` Step 1 | Opening framing and five anchor questions folded into one paragraph | coaching | Interview coaching; the opening line and the five topics stay |
| 12 | `--from-issue` Step 2 | Intro sentences and the "Key contract shape" label merged into one line | coaching | Duplicated framing; the contract block is unchanged |
| 13 | `--from-issue` Step 3 | Read/replace/write list folded into one paragraph | coaching | Format only; the `spec_ref` line, "only that line changes", and the absent-line rule stay |
| 14 | Phase 1, Mission Statement | Labelled blockquote became one line | coaching | Format only; same mission and challenge rule |
| 15 | Step 1.0, follow-up sentence | "If user selects… to get their idea" shortened | coaching | Coaching; the free-text follow-up stays |
| 16 | Step 1.1 | Four bullets became one sentence; `codebase_search` dropped | coaching | How-to coaching; same scan, files, and output |
| 17 | Step 1.2 (heading removed) | Plan Mode benefit list and the `Design principle (ADR-001)` quote removed; "run discovery in Plan Mode; the user controls when to switch" moved into Step 1.3 | coaching | Rationale and an internal label; 1.2 is left as a gap, not renumbered |
| 18 | Step 1.3, Internal Process | Four bullets and the gap block folded into one list of four areas | coaching | Duplicated framing. *Re-decided:* keeps "silently" and "ambiguous", which the twin dropped |
| 19 | Step 1.3, Conversation Rules | Bullets became one paragraph; the repeated "Challenge ideas…" bullet removed | coaching | Format only; the challenge rule stays in the Mission line |
| 20 | Step 1.3, Topic Areas to Explore | 24 sample questions removed; "experience first, then rules, then technical constraints" kept | coaching | Interview coaching; the four gap lists name the same areas |
| 21 | Step 1.3, Critical Analysis | Eight bullets became one paragraph | coaching | Format only; every trigger stays |
| 22 | Step 1.3, Pushback Phrasing Examples | Seven example phrasings removed | coaching | Phrasing coaching; the Prime Directive in `system-instructions.md` sets the rule |
| 23 | Step 1.3, Transition to Contract | Example phrases removed; "present the contract (still in Plan Mode) and leave room for more questions" kept | coaching | Phrasing coaching |
| 24 | Step 1.3b | Seven items became six (overlap and no-overlap merged); clauses and the closing "It catches…" sentence trimmed | coaching | Format only; the glob, the `spec-status.py is-complete` call, the literal-substring rule, and the no-header rule stay |
| 25 | Step 1.4 | Intro sentence, "Format:" label, and example business rule 3 removed; closing sentence shortened | coaching | Example padding and duplicated framing; the template's sections are unchanged |
| 26 | Step 1.4b | Intro sentence and "Handling responses:" label removed | coaching | Repeats Step 1.4's closing sentence; the AskQuestion block and the five responses are unchanged |
| 27 | Step 1.5 | Two intro sentences merged; "Handling responses:" label and "Analyze with vision model to" removed; the mockup bullets folded into one line | coaching | Coaching and format; the AskQuestion block, the five responses, and the `/writ-design` line are unchanged |
| 28 | Title | "Enhanced" removed | coaching | A leftover label from an earlier version; other commands read `<Name> Command (<name>)` |
| 29 | Step 2.4, canonical spelling bullet | "— this note governs new specs only, per Business Rule 8" removed | coaching | Internal label for one of Writ's own spec rules; "(forward-only)" already says new specs only |
| 30 | Step 2.4b | "as in `2026-07-26-leanness-instrumentation`'s `Amends:` line" removed | coaching | An example from Writ's own history; the spec-and-ADR example stays |
| 31 | Step 2.6, context hint label | "(new)" removed | coaching | A history label |
| 32 | Step 2.6a | "exactly as today" removed; "is today's error path" became "follows the normal error path" | coaching | References to the file's own history; the error-path rule stays |
| 33 | Step 2.6c | "Goal Card Stage 3 said…; the locked Stage 3 contract relocates the invoke…" removed | coaching | Writ's own history |
| 34 | Step 2.1 (heading removed) | Initialize Tracking removed | coaching | Tells the agent to use its task tool; no output depends on it. 2.1 is left as a gap |
| 35 | Step 2.2 | Date and owner sentences shortened | coaching | Format only; the date source, folder name, bash block, and `@unknown` rule stay |
| 36 | Step 2.4, dependency and canonical bullets | Shortened | coaching | Format only; "never omit it", `[]`, "exact spec-folder IDs", "Canonical complete-family spelling", and every spelling stay |
| 37 | Step 2.4, supersession bullet | Shortened | coaching | Format only; both fields, the link shape, the example, and the lifecycle link stay |
| 38 | Step 2.4b | Intro and two paragraphs compressed | coaching | Format only; the `supersession-writeback.py apply` call, never-duplicated, `skipped_other`, `broken`, and "never blocks or fails spec package creation" stay |
| 39 | spec-lite intro | "Total budget: <100 lines (hard limit)" became "Hard limit: under 100 lines" | coaching | Format only |
| 40 | spec-lite template | Placeholder bullets merged (Implementation Approach, Business Rules, Edge Cases, Test Strategy) | coaching | Fewer placeholders; every section and the 35/35/30 markers stay |
| 41 | spec-lite, "ID tags come later" | Moved out of the template fence and shortened to two sentences | coaching | Explanation; the untagged-now rule and the Step 2.6b hand-off stay, and authors no longer copy the note into spec-lite files |
| 42 | Content Selection Guidelines | Label and bullets became one "Emphasis by feature type" sentence | coaching | Format only; the same four feature types |
| 43 | Line Budget Enforcement | Breakdown list and four-step list became one paragraph | coaching | Keeps the hard 100-line limit, the 35/35/30 targets, and the four over-limit moves |
| 44 | Backward Compatibility Note | Became the paragraph's last sentence | coaching | Format only |
| 45 | Step 2.5 | Numbered list became one sentence; third example plan row removed | coaching | Format and example padding; standalone value, dependencies, and the 5-7 task cap stay |
| 46 | Step 2.6, context hints | "Context hint generation" paragraph and "Timing note" merged | coaching | They said the same thing twice; both parameters and the prompt line stay |
| 47 | Step 2.6, criterion ID grammar | "'s prompt template — do not duplicate it here" removed | coaching | A note to the command's maintainer |
| 48 | Step 2.6a, intro and item 1 | Parenthetical on why 2.6b waits removed; the `--repo` rationale shortened | coaching | Rationale; the `--repo` reason stays in short form |
| 49 | Step 2.6b | "Why this step exists" paragraph removed; items 1–4 shortened | coaching | Rationale; the four actions and "Do not guess" stay, and item 4 no longer cites the removed "Line Budget Enforcement" label |
| 50 | Step 2.6c intro | "This is **not** Step 2.6 (generation)" and "do not loop" folded into one sentence | coaching | Duplicated framing; "once", "no loop", and "does not replace 2.6a" stay. *Re-decided:* keeps "After stories exist and Step 2.6a has validated IDs", which the twin cut to "After Step 2.6a" |
| 51 | Step 2.6c, item 1 | Wrapped list item became one paragraph; the three "Do not" rules joined in one sentence | coaching | Format only; every rule and "(gitignored)" stay |
| 52 | Step 2.8 | "for traceability" removed; the failure-mapping paragraph shortened and joined to the error-mapping rule | coaching | Rationale; `Read skills/error-rescue-mapping/SKILL.md`, the data-flow heuristic, and "when in doubt, include it" stay |
| 53 | Step 2.9 | First two paragraphs merged | coaching | Format only; "never fail this review or block the package" and the `jev:` note line stay |
| 54 | Example Usage | The blockchain-chat dialogue and its "Key UX difference" line removed | coaching | A worked dialogue; no step reads it |

## Declined

| # | Section | Change | Class | Reason |
|---|---|---|---|---|
| 55 | Frontmatter | Twin renames to `create-spec-lean` with a lean-variant description | constraint | The frontmatter stays byte-identical; the name is the command's identity |
| 56 | Title | Twin appends ", lean" | addition | A twin-only label |
| 57 | Autonomous Authoring Boundary | Twin still links ADR-013 | addition | Story 1 removed the link and `shipped-refs` fails on it |
| 58 | `--from-prototype` source matrix | Twin trims two Story 1 cells | constraint | The matrix decides Story 1's status; technical-spec.md keeps it whole |
| 59 | `--from-prototype` Step 1 | Twin drops "or exploration record" from the skip rule | behavior | Discovery also skips what the exploration record answers |
| 60 | Step 1.0 AskQuestion block | Twin deletes the `// Include common feature types…` comment | constraint | Every AskQuestion block stays as it was |
| 61 | Step 1.5, `generate` response | Twin rewrites the line as "Follow `/design` wireframe conventions." | test-pinned | `test_platform_neutral_names.py` anchors "Follow wireframe conventions from" on a line naming `/writ-design` |
| 62 | Step 2.4, frontmatter intro | Twin drops "any relevant phase/source metadata" | behavior | It tells authors to add phase and origin lines, which specs rely on |
| 63 | Step 2.6a, item 4 | Twin keeps the no-op `escalated(...)` emit line | test-pinned | `2026-10-20-harness-cuts` removed it; `test_harness_cuts.py` asserts items 1–3 only |
| 64 | Step 2.6a, iteration sentence | Twin drops "Iteration accounting:" and rewrites "— there is no second regeneration" as "; there is no second regeneration" | test-pinned | Pin-map row 67 (`check_model_escalation`) and `test_harness_cuts.py` pin the sentence; it is a loop bound |
| 65 | Step 2.6c, Jev first and Jev setup | Removed by the twin | behavior | The opt-in Jev pass and its one-time setup prompt; both bash tests pin them |
| 66 | Step 2.6c, item 3 | Twin narrows "Any `jev-judge.py` or `spec-analyze.py` `fail`" to "A script `fail`" and drops the setup-prompt exception | behavior | The Jev outcomes stay notes-only and the setup prompt stays the one allowed AskQuestion; both bash tests pin the wording |
| 67 | Step 2.9, `jev:` note | Removed by the twin | behavior | Reports the Jev outcome; `test_spec_analyze_command_hooks.sh` pins it |
| 68 | Completion | Twin adds a "Production boundary" line | addition | An addition, not a cut |
| 69 | References | Twin points at `_preamble.lean.md` | constraint | The lean preamble is deleted; `broken-refs` would fail on the link |
| 70 | Wording-only edits | Twin rewords text without removing coaching: Step 1.0 "If the user didn't"; Step 1.4b response lines ("Ask free-text:", "re-present the contract", "return to discovery"); Step 1.5 "in the spec" and the `existing` response; the Phase 2 trigger line; Step 2.4's "Main specification" lead and its five "Must contain" bullets; Step 2.6's launch, contents, and batching lines; Step 2.7's "with" and "quick links"; Step 2.8's "May run" and "Create only" | wording | A rewording with no coaching to remove, so it is outside a coaching-only pass |

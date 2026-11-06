# Technical Spec: Design Divergence Skill and Usage-First Gate 0

> Spec: [`../spec.md`](../spec.md)

## Architecture

```
skills/design-divergence/SKILL.md          how to get alternatives that differ (all media)
        ▲                         ▲
        │ Read (Step 2.5)         │ Read (Gate 0, boundary-crossing route)
commands/prototype.md      commands/implement-story.md
  gate · draft = rendered page    switch · route predictor · caller usage
  render table · exploration.md   two sketch spawns · choice · Gate 1 warnings

scripts/divergence-trial.py (temporary)    init → record → blind → [human] rate → report
.writ/eval/divergence-trial/               briefs, prompts, raw drafts, sheet, key, trial JSON
scripts/tests/test_divergence_trial_outcome.py   report verdict ↔ repo state ↔ spec status
```

## Skill: `skills/design-divergence/SKILL.md` (Story 1)

Frontmatter:

```yaml
---
name: design-divergence
description: "Generate structurally different alternatives for a UI, an API shape, or a data model by declaring axes first and drafting each one in an independent context."
disable-model-invocation: true
status: candidate
---
```

Body sections, in order: `## Purpose`, `## When to Use`, `## How to Apply`, `## Examples`.

`## How to Apply` carries these rules, each one short:

1. **Write the caller's usage first** when the thing has callers (an API, a module, a schema someone queries): 3 to 10 lines of the calls, requests and responses, or queries, before any axis or draft. Drafts are judged against it.
2. **Declare the axes first.** Two or three orthogonal dimensions; give each draft a distinct combination and state it before generating.
3. **Generate independently.** One context per draft. No shared scratch; no draft sees another.
4. **Commit before drafting.** Each generator states its axis combination and the trade-off it accepts, then drafts.
5. **Use ordinary personas.** The person who uses the result daily, not a visionary designer.
6. **Two or three drafts.** The caller sets the count; more than three rarely adds a distinct option.
7. **The anti-pattern.** One agent, one call, "give me three options" returns one idea three times: models fixate on their own early output, and repeated samples from one prompt converge.
8. **Same family.** Drafts come from the session's model family. Routing drafts to other vendors is out of scope (ADR-024).

Axis catalog, one table per medium (two or three rows each, drawn from):

| Medium | Example axes |
|---|---|
| UI | information density; navigation model; primary action placement; progressive disclosure vs everything visible |
| API shape | one call vs several; synchronous vs job-and-poll; errors as exceptions vs result values; caller-owned vs callee-owned identifiers |
| Data model | normalized vs embedded; mutable rows vs append-only events; where identity lives; computed on write vs on read |

`## Examples`: one API example (axes, two commitments, the usage line each changes) and one data-model example. No line starts with `/`; no `Read commands/`, `Read skills/`, or `Task(` in the body (lint body grammar).

Registration: `.writ/manifest.yaml` `skills:` entry between `dependency-context-loading` and `drift-triage` with `status: candidate` and `tags: [design, divergence, exploration]`; `bash scripts/gen-skill.sh` to regenerate root `SKILL.md`; README `## Skills` table row; `python3 scripts/gen-platform-trees.py` to regenerate `plugins/writ/skills/`, the Cursor plugin tree, and `codex/AGENTS.md.template`'s skill list.

## `/prototype` Step 2.5 (Story 2)

Under the existing `#### Getting drafts that actually differ` heading, replace the five numbered rules with:

> `Read skills/design-divergence/SKILL.md` for how to get drafts that differ: axes declared first, one context per draft, a commitment before rendering, ordinary personas. This step owns when drafts are made, what a draft is, how they render, and the record. Default to three drafts.

Unchanged: the gate paragraph, `#### What a draft is` and the portability test, `#### Render through the platform` with its three rows and `Never degrade silently.`, `#### Present and choose`, `exploration.md`, frontmatter, Step 2's `.writ/docs/design-system.md` mention. Add `[design-divergence](../skills/design-divergence/SKILL.md)` to `## References`.

## Gate 0 Divergence (Story 3)

A block of bold-led paragraphs inside `#### Gate 0: Architecture Check`, after the `--full-pipeline` anchor-confirmation paragraph and before the `---` that precedes `#### Gate 0.5`. Target: under 2,000 bytes.

Text contract (wording may tighten; every literal below must appear):

- `**Design divergence (boundary-crossing route).**` and `Read skills/design-divergence/SKILL.md`.
- The switch literal `- **Gate 0 Divergence:** off` and the rule that an absent line means on.
- The route predictor commands:

```bash
python3 scripts/boundary-map.py compute --story <story-file> --repo . [--overlap <check-5-overlap>] > .writ/state/boundary-<story-stem>.json
python3 scripts/change-surface.py classify --changed <planned files>
python3 scripts/boundary-map.py crossings --map .writ/state/boundary-<story-stem>.json --changed <planned files> --story <story-file> --surface <class>
```

- Triggers: `--full-pipeline`, `--panel`, or `route: review-agent`. Runs after a PROCEED or CAUTION (or an ABORT the user resolved as proceed).
- Caller usage written to `.writ/state/divergence-<story-stem>.md` before axes.
- Two `readonly` spawns at `anchor`, one message, each returning `COMMITMENT:`, `SKETCH:` (≤40 lines), `USAGE FIT:`.
- Choice rule; hand-off label `design sketch (Gate 0 divergence)` appended to the Gate 0 warnings.
- Report literal `gate0-divergence:` with the states in spec.md → State Catalog.
- Never blocking: no DEGRADED, no AskQuestion, no `review_cycle` increment, no retry.

Other edits in `commands/implement-story.md`, all Gate 0's own:

| Location | Change |
|---|---|
| `## Overview` first paragraph | add "and two Gate 0 sketch spawns on the boundary-crossing route" to the default-spawn clause |
| `## Pipeline` row `Gate 0` | Runs-as cell adds "two sketch spawns on the boundary-crossing route"; Skill cell `design-divergence (boundary-crossing route)` |
| `## References` skills line | add `[design-divergence](../skills/design-divergence/SKILL.md)` |

Not changed: frontmatter `gates:` (no new `#### Gate` heading), the routing table, the sub-agent completeness and worktree notes, Gate 0.5 through Gate 5.

`.writ/docs/config-format.md`: one row in the key table (`Gate 0 Divergence` | implement-story (Gate 0) | on by default; `off` disables the boundary-crossing-route sketches) and a short `## Gate 0 Divergence` section with the line format and the absent/malformed rules.

`scripts/tests/test_governor_enforcement.py`: re-pin `"commands/implement-story.md"` to the measured overage with a dated disclosure naming this spec and Story 3.

Tests (new file `scripts/tests/test_design_divergence_wiring.py`): both callers carry the `Read` line; the Gate 0 section carries every literal in the text contract; the switch literal appears in Gate 0 and in config-format.md; the Gate 0 section still has no unguarded `> **Agent:**` marker; the prototype render-table pins still hold; the skill lints `pass`.

## Trial Harness: `scripts/divergence-trial.py` (Story 4)

**Dev-only.** The harness is temporary and must never ship: Story 4 adds `divergence-trial.py` to every dev-only script list (`DEV_ONLY_SCRIPTS` in `scripts/gen-platform-trees.py` and the dev-only cases in `scripts/install.sh`, `scripts/update.sh` and `scripts/unlink.sh`, matching how `pipeline-baseline.py` is listed), and Story 6 removes those entries when it deletes the harness.

Python 3.9 stdlib only. Agent CLI contract shape: verdict-or-data first, `reason:` lines, summary line `divergence-trial: …` last. Exit 0 ran, 1 never used, 2 usage or refusal (file unchanged).

Schema `divergence-trial-v1`:

```json
{
  "schema": "divergence-trial-v1",
  "briefs": [
    {"id": "ui-1", "medium": "ui", "brief_sha256": "…",
     "arms": {"axes": {"sha256": "…", "drafts": 3}, "naive": {"sha256": "…", "drafts": 3}}}
  ],
  "blind": {"sheet": "rating-sheet.md", "sheet_body_sha256": "…", "key": "key.json", "key_sha256": "…"},
  "rated_by": null,
  "ratings": null
}
```

| Subcommand | Inputs | Effect |
|---|---|---|
| `init --briefs DIR --out FILE [--force]` | `DIR/*.md`, each starting with `id:` and `medium: ui\|api\|data-model` lines | Requires exactly six briefs, two per medium. Writes the skeleton. Refuses an existing `--out` without `--force`. |
| `record --trial FILE --brief ID --arm axes\|naive --drafts FILE` | Drafts file: exactly three `## Draft` blocks with `Title:`, `Structure:` (multi-line), `Trade-off:`; `Commitment:` required in `axes`, forbidden in `naive` | Stores the drafts' sha256 and count; copies the file to `.writ/eval/divergence-trial/raw/<brief>/<arm>.md`. Re-recording replaces. |
| `blind --trial FILE --sheet OUT [--seed N]` | All twelve arms recorded | Per brief: random arm → Set X / Set Y, drafts shuffled, titles → `Draft 1..3`, `Commitment:` lines dropped. Writes the sheet with blank rating fields and `key.json` beside it; records both hashes. Refuses when any arm is missing. |
| `rate --trial FILE --sheet FILE --rated-by NAME` | The filled sheet | Recomputes the body hash with rating fields blanked and refuses on mismatch. Requires every field on every brief. Stores ratings by set label (not arm) and `rated_by`. |
| `report --trial FILE [--json]` | Trial file and `key.json` | Verifies the key hash, maps sets to arms, prints the verdict. |

Rating fields per brief on the sheet:

```
distinct_X: 1|2|3        how many structurally different drafts Set X holds
distinct_Y: 1|2|3
more_distinct: X|Y|tie
render_only_enough: yes|no   could you choose a direction from these drafts without running code?
note: ≤200 chars, one line
```

Report output:

```
keep | remove | unverifiable
reason: … (unverifiable only)
brief: ui-1 medium=ui winner=axes distinct axes=3 naive=1 render_only=yes
…
render-only: yes on 5 of 6 briefs (ui 1 of 2)
sample: 6 briefs, one rater; declared axes must win 4 of 6 — a small sample, not a general result
blinding: honor-system; the rater opened only the sheet
divergence-trial: keep — axes won 5 of 6, distinct 16 vs 9
```

## Trial Inputs and Run (Story 5)

Under `.writ/eval/divergence-trial/`:

| Path | Content |
|---|---|
| `briefs/ui-1.md` | A Writ spec-progress page: stories, status, AC coverage per story |
| `briefs/ui-2.md` | A `/prototype` exploration-record viewer: drafts side by side, the choice, why each lost |
| `briefs/api-1.md` | `pr-ready.py`'s CLI contract (roadmap Phase 16): typed blockers, exit codes |
| `briefs/api-2.md` | The per-source evidence record `/why` returns, with a confidence tier per claim |
| `briefs/data-model-1.md` | The verification ledger keyed by PR, head SHA, and patch-id (roadmap Phase 16) |
| `briefs/data-model-2.md` | `/retro`'s rule-to-enforcer table (roadmap Phase 15) |
| `prompts/naive.md` | One prompt: "Give me three options for <brief>." plus the output template |
| `prompts/axes.md` | The per-draft prompt: brief, caller usage when the brief has callers, assigned axis combination, ordinary persona, output template with `Commitment:` |
| `<date>-divergence-trial.json` | The trial file |
| `rating-sheet.md`, `key.json`, `raw/`, `render/` | Blinded sheet, key, raw drafts, rendered UI drafts named by set and draft number |

Every brief is Writ's own and public-safe; none quotes another repository's source. Each brief is at most 10 lines.

Generation: both arms at the same tier (`anchor`, platform `inherit`) in one session. Axes arm: declare axes per the skill, then three spawns in one message, one per draft. Naive arm: one spawn with `prompts/naive.md`. UI briefs: after `blind`, render each UI draft's `Structure:` to a self-contained HTML page under `render/<brief>/<set>-<n>.html` from the blinded text, one spawn per draft, same render prompt for every draft.

`rating-handoff.md` in the spec folder: who rates, which file to open, the field definitions, the exact `rate` and `report` commands, the honor-system rule (do not open `raw/`, `key.json`, or the trial JSON before rating), and that the lane did not rate.

`scripts/tests/test_divergence_trial_outcome.py` (stdlib only, no import of the harness): skips while `{spec}/trial-report.md` is absent; otherwise parses the verdict line and asserts the repo state in Story 6's table.

## Verdict Execution (Story 6)

| Verdict | Repo state the outcome test asserts |
|---|---|
| `keep` | `skills/design-divergence/SKILL.md` exists; both callers carry the `Read` line; `spec.md` `> **Status:** Complete`; the trial file has `rated_by` and complete ratings |
| `remove` | No `skills/design-divergence/`; no `design-divergence` in `commands/`, `adapters/`, `README.md`, `SKILL.md`, `.writ/manifest.yaml`, `plugins/`; no `Gate 0 Divergence` in `commands/` or `.writ/docs/`; `spec.md` `> **Status:** Closed — Not Implemented` |
| `unverifiable` | Neither; `spec.md` status names the blocking reason; nothing added or removed |

On either acted-on verdict: commit the trial file and `trial-report.md` first, then delete `scripts/divergence-trial.py` and its unit tests and fixtures; record the result in ADR-030 § Review and mark roadmap Phase 15's "Divergence trial" criterion with a link to `trial-report.md`.

On `remove`, also: strip `/prototype` Step 2.5's `Read` note and replace it with "Ask for up to three drafts and state what each commits to"; change the exit criterion's "axis combination" wording to "what it commits to"; re-pin the ratchet downward; file an improvement issue for `commands/create-spec.md` Step 0's "declared axes" wording.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Gate 0 switch read | `.writ/config.md` absent | Treated as absent line: on | Wiring test on the literal rule |
| Gate 0 switch read | Value not `on`/`off` | On; `gate0-divergence: on (malformed: <value>)` | Wiring test on the literal |
| Route predictor | Planned set empty | Skip; `skip (unverifiable: no planned files)` | Wiring test on the literal |
| Route predictor | `crossings` prints `unverifiable` or a script cannot run | Skip with its reason | Wiring test |
| Sketch spawn | Spawn error or timeout | Skip; `skip (sketch incomplete: <A\|B>)`; no retry | Wiring test |
| Sketch spawn | Returned text lacks `COMMITMENT:`, `SKETCH:`, or `USAGE FIT:` | Same as a spawn error | Wiring test |
| `init` | Not six briefs, wrong medium split, missing header | Exit 2, nothing written | Unit test |
| `record` | Not three drafts; `Commitment:` missing in axes or present in naive | Exit 2, file unchanged | Unit test |
| `blind` | An arm missing | Exit 2, no sheet or key written | Unit test |
| `rate` | Drafts edited after blinding (body hash mismatch) | Exit 2, file unchanged | Unit test |
| `rate` | A field blank or out of range; note too long or multi-line | Exit 2, file unchanged | Unit test |
| `report` | `key.json` missing or hash mismatch | `unverifiable`, `reason: key_missing` / `key_changed`, exit 0 | Unit test |
| `report` | Ratings absent | `unverifiable`, `reason: unrated`, exit 0 | Unit test |
| Story 6 | Report `unverifiable` | Spec stays open; status names the reason; nothing removed | Outcome test |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Gate 0 divergence | Usage, two sketches, `chose A` | No planned files → skip | Story with no ACs → usage from task list; if none, skip `(unverifiable: no usage source)` | Helper or spawn fails → skip, pipeline continues |
| Trial report | `keep` or `remove` with per-brief lines | No trial file → exit 2 | No ratings → `unverifiable` | Key missing → `unverifiable` |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Both sketches return the same structure | Choose by rule 6 and note `sketches converged` in the reason; still never blocks |
| `--full-pipeline` ABORT, user picks proceed | Divergence runs after the proceed |
| Gate 1 recode after a Gate 3 FAIL | Gate 0 does not re-run; the sketch stays in the warnings |
| Two-fail escalation to `--full-pipeline` mid-story | Gate 0 does not re-run (existing rule) |
| Rater fills only some briefs | `rate` exits 2; partial ratings are never stored |
| Rater edits a draft by accident | Body hash mismatch; restore with `git checkout` and re-fill |

## Files in Scope

| File | Story | Change |
|---|---|---|
| `skills/design-divergence/SKILL.md` | 1 | New |
| `.writ/manifest.yaml` | 1 | One `skills:` entry |
| `SKILL.md` (root catalog) | 1 | Regenerated by `scripts/gen-skill.sh` |
| `README.md` | 1 | One `## Skills` row |
| `plugins/writ/**`, `cursor/plugin/**`, `codex/AGENTS.md.template` | 1, 2, 3 | Regenerated by `scripts/gen-platform-trees.py` only |
| `commands/prototype.md` | 2 | Step 2.5 rules → `Read` note; References |
| `commands/implement-story.md` | 3 | Gate 0 block; Gate 0 Pipeline row; Overview clause; References |
| `.writ/docs/config-format.md` | 3 | `Gate 0 Divergence` row and section |
| `scripts/tests/test_governor_enforcement.py` | 3, 6 | Ratchet re-pin with disclosure |
| `scripts/tests/test_design_divergence_wiring.py` | 1, 2, 3 | New |
| `scripts/divergence-trial.py` | 4 (deleted in 6) | New, temporary |
| `scripts/tests/test_divergence_trial.py`, `scripts/tests/fixtures/divergence-trial/` | 4 (deleted in 6) | New, temporary |
| `.writ/eval/divergence-trial/**` | 5 | New |
| `.writ/specs/2026-10-25-design-divergence/rating-handoff.md` | 5 | New |
| `scripts/tests/test_divergence_trial_outcome.py` | 5 | New |
| `.writ/specs/2026-10-25-design-divergence/trial-report.md` | 6 | New |
| `.writ/decision-records/adr-030-…md`, `.writ/product/roadmap.md` | 6 | Result note; criterion marked |

Not touched: `agents/architecture-check-agent.md`, `agents/coding-agent.md`, Gate 1 through Gate 5 sections, `commands/why.md`, `commands/writ.md`, `agents/review-agent.md`, `agents/evaluator-agent.md`, `commands/review.md`, `skills/tdd-cycle/`, `commands/retro.md`, `commands/refresh-command.md`.

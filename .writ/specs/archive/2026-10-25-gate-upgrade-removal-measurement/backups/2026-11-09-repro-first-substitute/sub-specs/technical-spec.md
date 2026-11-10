# Technical Spec: Gate Upgrade Removal Measurement

> Spec: [`../spec.md`](../spec.md)

## Architecture

```
.writ/eval/baselines/2026-09-07-claude-fable-5-1.json   four-story selection (Phase 11)
        │ init
        ▼
.writ/eval/gate-upgrade-trial/<date>-gate-upgrade-trial.json   (committed; ids, keys, labels only)
        │ prepare (per story)                     yuss ──fetch --depth 2──▶ $TMPDIR/writ-gate-trial-<slug>/
        │                                                                  checkout/ (story commit), parent/ (worktree),
        │                                                                  diff.patch, story.md, contract.md,
        │                                                                  routes.json, blast-radius.json, arms/<arm>/.writ/config.md
        │ [lane spawns arms] ──▶ <primary checkout>/.writ/state/gate-upgrade-trial/<slug>/<arm>*.md  (gitignored)
        │ record (per arm)
        │ sheet  ──▶ .writ/eval/gate-upgrade-trial/labeling-sheet.md + .writ/state/gate-upgrade-trial/findings/Fnn.md
        │ [human] label --sheet … --labeled-by …
        ▼ report ──▶ .writ/specs/2026-10-25-gate-upgrade-removal-measurement/trial-report.md (Story 4)
scripts/tests/test_gate_upgrade_trial_outcome.py   report verdicts ↔ repo state ↔ spec status
```

## Upgrades Under Test

| Harness name | Switch line (`.writ/config.md`) | Presence probe at `init` | Owning spec |
|---|---|---|---|
| `gate0-divergence` | `- **Gate 0 Divergence:** off` | `commands/implement-story.md` contains `**Design divergence (boundary-crossing route).**` | `2026-10-25-design-divergence` |
| `safety-fact` | `- **Safety Fact:** off` | `skills/blast-radius/SKILL.md` exists | `2026-10-25-review-route-rigor` |
| `reviewer-filters` | `- **Reviewer Filters:** off` | `skills/review-judgment-filters/SKILL.md` exists | `2026-10-25-review-route-rigor` |
| `repro-first` | `- **Repro First:** off` | `scripts/repro-order.py` exists | `2026-10-25-repro-first-bug-fixing` |

All four switches read absent as on, `off` (any case) as off, and any other value as on. The trial writes only exact `on` or `off` values, so the malformed rule never applies.

## Harness: `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`

Python 3.9 stdlib only, `from __future__ import annotations`. Check shape (`.writ/docs/agent-cli-contract.md`): line 1 `pass` or `unverifiable`, `reason:` and detail lines, last line `gate-upgrade-trial: …`. Exit 0 when it ran, 2 for usage errors and refusals (files unchanged). It never spawns an agent and makes no network call. It is dev-only: it lives outside `scripts/`, so `is_shippable_script` never ships it and the Classification table needs no row.

It loads `scripts/review-panel.py` with `importlib.util.spec_from_file_location` and uses `_prepare_run`, `parse_output`, `trial_key`, and `_key_order`. When that file is missing or lacks one of those names, `prepare` and `record` exit 2 with `reason: review_panel_missing`.

State directory: `<primary checkout>/.writ/state/gate-upgrade-trial/`, where the primary checkout is the parent of `git rev-parse --path-format=absolute --git-common-dir`. `--state-dir` overrides it (tests).

### Schema `gate-upgrade-trial-v1`

```json
{
  "schema": "gate-upgrade-trial-v1",
  "baseline": ".writ/eval/baselines/2026-09-07-claude-fable-5-1.json",
  "origin": null,
  "yuss_snapshot": {"before": null, "after": null, "unchanged": null},
  "upgrades": {
    "gate0-divergence": {"present": true},
    "safety-fact": {"present": true},
    "reviewer-filters": {"present": true},
    "repro-first": {"present": true}
  },
  "stories": [
    {
      "story_id": "…", "story_path": "…", "spec_folder": "…",
      "story_commit": "<sha>", "parent_sha": "<sha>",
      "routes": {"surface": "full-stack", "gate3_route": "review-agent",
                 "planned_surface": "full-stack", "gate0_route": "review-agent"},
      "repro_kind": null,
      "arms": {
        "off-1": {"verdict": "FAIL", "keys": [{"key": "ac:AC-2.2", "severity": "Critical"}],
                  "states": {"safety-fact": "off", "reviewer-filters": "off"},
                  "raw": "<slug>/off-1.md", "raw_sha256": "…"}
      },
      "upgrade_only": [
        {"id": null, "upgrade": "safety-fact", "key": "ac:AC-2.1", "severity": "Critical",
         "label": null, "note": null}
      ],
      "off_only": {"reviewer-filters": 0, "safety-fact": 0, "gate0-divergence": 0}
    }
  ],
  "sheet": null,
  "acks": {},
  "labeled_by": null
}
```

### Subcommands

| Subcommand | Effect | Refusals (exit 2, nothing written) |
|---|---|---|
| `init --baseline FILE --out FILE [--repo .] [--force]` | Copies the five identity fields per selected story; probes the four presence checks against `--repo`; writes the skeleton | baseline missing or unparseable; selection not exactly four stories; non-hex SHA; unsafe path; `--out` exists without `--force` |
| `prepare --trial FILE --story ID --yuss PATH [--tmp-root DIR]` | Calls `_prepare_run` into `<tmp-root>/writ-gate-trial-<slug>/`; adds `parent/` with `git -C checkout worktree add --detach ../parent <parent_sha>`; computes routes (§ Routes); runs `change-surface.py blast-radius --changed <files> --repo checkout` when `gate3_route` is `review-agent` and `safety-fact` is present; writes `arms/<arm>/.writ/config.md` for every arm (§ Arms); stores `routes` in the trial file; prints every path | yuss path missing; SHA unreachable; any `_prepare_run` error; a route script exits 2 (run dir removed) |
| `record --trial FILE --story ID --arm ARM --output FILE [--origin MODEL] [--state NAME=on\|off]… [--report-line TEXT] [--verifier FILE] [--kind bug\|not-a-bug-fix] [--repro-ac AC-N.M --at-parent pass\|fail --at-commit pass\|fail]` | Validates the arm's evidence (§ Arm Evidence); parses keys; copies the output to the state directory; recomputes `upgrade_only` and `off_only` for the story, keeping labels on keys that stay upgrade-only. Re-recording an arm replaces it | arm not applicable to the story (§ Arms); evidence mismatch; `--origin` differs from the stored `origin`; output unreadable |
| `sheet --trial FILE --out FILE [--seed N]` | Assigns opaque IDs `F01…` to all upgrade-only findings in a seeded shuffle; writes one excerpt file per finding to `<state>/findings/Fnn.md` (the issue block or AC line from the raw output; for Gate 0 also the cited sketch line); writes the sheet with blank `label:` and `note:` fields and one `ack:` field per upgrade no story exercised; records the sheet path and its body hash | any applicable arm missing; sheet already recorded without `--force` |
| `label --trial FILE --sheet FILE --labeled-by NAME` | Recomputes the body hash with fields blanked and refuses on mismatch; requires every `label:` to be `valid` or `invalid`, every note to be one line, ≤200 chars, with no backtick, and every `ack:` to be `remove` or `amend`; stores labels by ID, acks, and `labeled_by` atomically | hash mismatch; any blank or bad field; `NAME` empty or containing `claude`, `agent`, `gpt`, `codex`, `cursor`, `gemini`, `grok`, `model`, or `bot` (case-insensitive) |
| `report --trial FILE [--json]` | Applies § Verdict; prints the report | trial file missing or wrong schema |

Every subcommand writes the trial file atomically (temp file, then rename).

### Routes (in `prepare`)

```bash
# Gate 2.5, over the story's changed files
python3 scripts/change-surface.py classify --changed <git diff --name-only parent..commit> --pretty
python3 scripts/boundary-map.py compute --story <story path in checkout> --repo <checkout> > <run>/boundary.json
python3 scripts/boundary-map.py crossings --map <run>/boundary.json --changed <files> --story <story> --surface <class> --repo <checkout>
# Gate 0 predictor (design-divergence route rule), over the planned files = boundary.json "owned"
python3 scripts/change-surface.py classify --changed <owned> --pretty
python3 scripts/boundary-map.py crossings --map <run>/boundary.json --changed <owned> --story <story> --surface <class> --repo <checkout>
```

An empty planned set or an `unverifiable` crossings result stores `gate0_route: "skip"` with the reason, matching Gate 0's `skip (unverifiable: …)`.

Authoring-time probe (scratch clones; yuss unchanged):

| Story | Gate 2.5 route | Gate 0 predicted route |
|---|---|---|
| `2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow` | `review-agent` (full-stack) | `review-agent` (planned full-stack) |
| `2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link` | `review-agent` (full-stack) | `evaluator-agent` (planned cross-component) |
| `2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption` | `review-agent` (full-stack) | `review-agent` (planned full-stack) |
| `2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard` | `review-agent` (cross-component, outside-boundary crossings) | `review-agent` (planned full-stack) |

`prepare` recomputes these at run time; the run-time values are the ones recorded.

## Arms

| Arm | Applies when | Switch states in `arms/<arm>/.writ/config.md` | Procedure |
|---|---|---|---|
| `off-1`, `off-2` | every story | all four `off` | Spawn the Gate 3 agent named by `gate3_route` with `reviewer_filters: off`, `safety_fact: off`, `blast_radius: (none)` |
| `reviewer-filters` | every story | Reviewer Filters `on`, others `off` | Same spawn with `reviewer_filters: on` |
| `safety-fact` | `gate3_route` is `review-agent` | Safety Fact `on`, others `off` | Spawn `review-agent` with `safety_fact: on` and the blast radius; save the output; run `review-override.py safety-fact --review-output <out> --repo <checkout> --blast-radius <run>/blast-radius.json --tests-output <run>/tests.txt`; on `safety_fact_missing` or `safety_fact_below_floor`, re-spawn once with the `reason:` lines, as Gate 3 does; record the final output and verifier result |
| `gate0-divergence` | `gate0_route` is `review-agent` | Gate 0 Divergence `on`, others `off` | In `parent/`, follow `commands/implement-story.md`'s Gate 0 divergence block for the story (caller usage to `<run>/divergence-<stem>.md`, two read-only sketch spawns in one message, the choice rule). On a `skip (sketch incomplete: …)` line, re-run once. Then one comparison spawn with `prompts/gate0-comparison.md`: chosen sketch, caller usage, story, contract, and `diff.patch` |
| `repro-first` | every story for recognition; the full arm only when `Kind:` is a bug fix | Repro First `on`, others `off` | In `parent/`, spawn the coding agent on the story with the switch on and `prompts/repro-stop.md` appended (stop after the repro commit; never write the fix). Read `### Repro` → `Kind:`. On a bug: run the reported command at `parent/` (must fail for the bug's reason), apply the repro commit's test files to `checkout/`, run the same command, record both results |

`tests.txt` holds the story's historical What Was Built test results under the line `historical, not re-run`. It has no `exit code: 0` line, so the `tested` rung is out of reach and the measured rung tops out at `traced`, the floor.

Every arm on a story uses the same model, in one session, at the `anchor` tier (platform `inherit`). The Gate 3 agent prompt and inputs are the shipped ones; the only difference between arms is the switch-controlled inputs.

## Arm Evidence (checked by `record`)

| Arm | Required evidence | Refused when |
|---|---|---|
| `off-1`, `off-2` | `--state safety-fact=off --state reviewer-filters=off` (line 1 of `review-override.py switch --name <n> --repo arms/<arm>`) | any state not `off`; output contains a `Safety Fact` heading |
| `reviewer-filters` | `reviewer-filters=on`, `safety-fact=off` | states differ; output contains a `Safety Fact` heading |
| `safety-fact` | `safety-fact=on`, `reviewer-filters=off`; `--verifier FILE` whose line 1 is `pass`, `fail`, or `unverifiable` | states differ; no `Safety Fact` heading in the output; verifier file missing |
| `gate0-divergence` | `--report-line` starting `gate0-divergence: chose` | report line is `off`, `skip`, or absent (record it as `--report-line` with `skip` to store the story as not exercised) |
| `repro-first` | `--kind`; for `bug`, `--repro-ac`, `--at-parent`, `--at-commit` | `bug` without the three fields; `--at-parent pass` stored as `no_repro` (exercised, no finding) |

Gate 0 comparison output: only issues under `### Issues Found` that carry `**Avoided by:**` are parsed; others are dropped before `parse_output`. Repro: `--at-parent fail --at-commit fail` yields key `ac:<repro-ac>` at `Critical`; any other pair yields no key.

## Upgrade-Only and Off-Only

For each story and upgrade arm `U`:

- `upgrade_only(U)` = keys in `U` − (keys in `off-1` ∪ keys in `off-2`)
- `off_only(U)` = (keys in `off-1` ∩ keys in `off-2`) − keys in `U`, counted only, never labeled, never a verdict input

## Verdict

Per upgrade, in order:

1. `present: false` → `absent`.
2. Any story where the arm applies lacks the arm, `off-1`, or `off-2` → `unverifiable`, `reason: missing_arm <story> <arm>`.
3. No story exercised it:
   - ack `remove` → `remove`, `reason: not_exercised`
   - ack `amend` → `unverifiable`, `reason: amendment_requested`
   - ack missing → `unverifiable`, `reason: not_exercised_unacknowledged`
4. Any upgrade-only finding unlabeled, or `labeled_by` null → `unverifiable`, `reason: unlabeled <n>`.
5. One or more `valid` → `keep`.
6. Otherwise → `remove`.

Report output:

```
pass | unverifiable
reason: … (one per unverifiable upgrade)
story: <id> gate3_route=review-agent gate0_route=evaluator-agent repro=not-a-bug-fix arms=off-1,off-2,reviewer-filters,safety-fact,repro-first
upgrade: gate0-divergence verdict=keep exercised=3/4 upgrade_only=2 valid=1 invalid=1 off_only=0
upgrade: safety-fact verdict=remove exercised=4/4 upgrade_only=1 valid=0 invalid=1 off_only=0
upgrade: reviewer-filters verdict=remove exercised=4/4 upgrade_only=0 valid=0 invalid=0 off_only=3
upgrade: repro-first verdict=remove exercised=0/4 reason=not_exercised
sample: 4 stories, two current-gates runs, one run per upgrade arm; one valid catch keeps an upgrade — a low bar, not a cost case
proxy: Gate 0 and Repro First arms are retrospective proxies (sketch comparison, repro re-run), not replays
yuss: unchanged
gate-upgrade-trial: keep 1, remove 3, unverifiable 0, absent 0 — 4 stories
```

`--json` prints one object with the same fields. Exit 0.

## Trial Inputs (Story 3)

| Path | Content |
|---|---|
| `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` | The harness (Stories 1–2; deleted in Story 4) |
| `.writ/eval/gate-upgrade-trial/prompts/gate0-comparison.md` | Writ's own text: compare the shipped diff with the chosen sketch; list only defects the sketch avoids; Gate 3 issue format plus `**Avoided by:**` citing a sketch line; no AC checklist |
| `.writ/eval/gate-upgrade-trial/prompts/repro-stop.md` | Writ's own text: follow the bug path to the repro commit, then stop; report `### Repro` with `Kind:`, `Surface:`, `Command:`, the repro commit, and the failing output |
| `.writ/eval/gate-upgrade-trial/<date>-gate-upgrade-trial.json` | The trial file |
| `.writ/eval/gate-upgrade-trial/labeling-sheet.md` | The sheet (IDs, story IDs, keys, severities, excerpt paths, blank fields) |
| `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/rating-handoff.md` | Who labels, the one file to open, the label rule (spec.md Business Rule 6), the ack rule (Rule 7) and the per-upgrade exercise counts, the exact `label` and `report` commands, the excerpt directory, the honor-system rule (do not open the trial JSON or `<state>/<slug>/` raw outputs before labeling), and that the lane did not label |

Sheet entry:

```
### F03
story: 2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption
key: security:app/api/events/[id]/fee-share/route.ts
severity: Major
excerpt: .writ/state/gate-upgrade-trial/findings/F03.md
label:
note:
```

Ack entry (one per upgrade no story exercised): `### not exercised: repro-first` then `exercised: 0/4`, the per-story reason (`not-a-bug-fix: <signal>`, `route evaluator-agent`), and `ack:`.

## Verdict Execution (Story 4)

Commit order: (1) labeled trial file + `trial-report.md`; (2) removal edits per upgrade; (3) roadmap, ADR-030, spec status; (4) delete the harness, `scripts/tests/test_gate_upgrade_trial.py`, and `scripts/tests/fixtures/gate-upgrade-trial/`.

### Removal inventories

**`gate0-divergence`** (design-divergence spec.md Implementation Approach and technical-spec.md § Gate 0 Divergence):
- `commands/implement-story.md`: the `**Design divergence (boundary-crossing route).**` block in Gate 0; the Gate 0 Pipeline row's sketch-spawn text and `design-divergence` Skill cell; the Overview's "two Gate 0 sketch spawns" clause; the `design-divergence` entry in References.
- `.writ/docs/config-format.md`: the `Gate 0 Divergence` key-table row and section.
- `scripts/tests/test_design_divergence_wiring.py`: the Gate 0 assertions only.
- `scripts/tests/test_divergence_trial_outcome.py`, if it exists: its `keep` branch requires `/prototype`'s `Read` line and no longer requires Gate 0's.
- `skills/design-divergence/SKILL.md`: `status_evidence` names one consumer, `/prototype`.
- The skill itself stays unless the design-divergence blind trial removed it (spec.md Business Rule 12).

**`safety-fact`** (review-route-rigor technical-spec.md § Clean Removal, "Remove `safety-fact`", steps 1–6), plus the `blast-radius` assertions in `scripts/tests/test_review_route_rigor.py`.

**`reviewer-filters`** (same section, "Remove `reviewer-filters`", steps 1–4), plus the `review-judgment-filters` assertions in `scripts/tests/test_review_route_rigor.py`. When both review-route upgrades are removed: delete the `switch` subcommand and `scripts/tests/test_review_route_rigor.py`.

**`repro-first`** (repro-first spec.md § Removal Inventory, every row).

After any removal: `bash scripts/gen-skill.sh` when a skill was removed; `python3 scripts/gen-platform-trees.py`; re-pin `"commands/implement-story.md"` in `scripts/tests/test_governor_enforcement.py` downward with a dated disclosure naming this spec and Story 4.

### Repo state the outcome test asserts

| Verdict | Assertion |
|---|---|
| `keep`, `unverifiable`, `absent` | the upgrade's presence probe matches its state at `init`; exception: `gate0-divergence` may be absent when `.writ/specs/2026-10-25-design-divergence/trial-report.md` exists with a `remove` verdict (spec.md Business Rule 12) |
| `remove` | `gate0-divergence`: no `Gate 0 Divergence` or `Design divergence (boundary-crossing route)` in `commands/` or `.writ/docs/`. `safety-fact`: no `skills/blast-radius/`, no `Safety Fact` in `commands/`, `agents/`, `.writ/docs/`. `reviewer-filters`: no `skills/review-judgment-filters/`, no `Reviewer Filters` or `reviewer_filters` in `commands/`, `agents/`, `.writ/docs/`. `repro-first`: no `scripts/repro-order.py`, no `Repro First` in `commands/`, `agents/`, `skills/`, `.writ/docs/` |
| all | `spec.md` status is `Complete` when every verdict is `keep`, `remove`, or `absent`, else starts `In Progress —`; the committed trial file has `labeled_by` set and no `label: null` among upgrade-only findings |

The outcome test is stdlib only, does not import the harness, and skips with a clear reason while `trial-report.md` is absent.

### Records

- Roadmap Phase 15 "Removal measurement" line: append the date, a link to `trial-report.md`, and one word per upgrade (`kept` / `removed`). Edit that line only.
- ADR-030 § Review "Phase 15 close" bullet: append a note with the date, the four story IDs, each upgrade's verdict and valid count, the not-exercised reasons, the proxy and small-sample caveats, and the Gate 0 / blind-trial outcome (spec.md Business Rule 12). Targeted edit only.

## Error & Rescue Map

| Operation | What can fail | Handling | Test |
|---|---|---|---|
| `init` | baseline missing, unparseable, not four stories, bad SHA, unsafe path | exit 2, nothing written | unit |
| `init` | an upgrade's presence probe fails | stored `present: false`; report `absent` | unit |
| `prepare` | yuss path missing, SHA unreachable | exit 2, one line naming the story, nothing written | unit (stand-in repo) |
| `prepare` | parent not reachable at depth 2 | exit 2 (from `_prepare_run`), run dir removed | unit |
| `prepare` | `review-panel.py` missing or lacks a reused name | exit 2, `reason: review_panel_missing` | unit |
| `prepare` | planned set empty, crossings `unverifiable` | `gate0_route: skip` with reason | unit |
| `prepare` | `blast-radius` subcommand absent while `safety-fact` present | exit 2, `reason: blast_radius_unavailable` | unit |
| `record` | arm not applicable to the story | exit 2, file unchanged | unit |
| `record` | switch states or report line do not match the arm | exit 2, file unchanged | unit |
| `record` | `--origin` differs from stored origin | exit 2 (mixed models invalidate the comparison) | unit |
| `record` | output file unreadable | exit 2 | unit |
| `sheet` | an applicable arm missing | exit 2, no sheet | unit |
| `label` | sheet body edited after `sheet` | exit 2, `reason: sheet_changed` | unit |
| `label` | blank or bad field; agent-like `--labeled-by` | exit 2, file unchanged | unit |
| `report` | unlabeled, missing arm, missing ack | `unverifiable` per upgrade, exit 0 | unit |
| Spawn (any arm) | error, timeout, or missing required section | re-run once with the identical prompt; a second failure leaves the arm unrecorded, so `report` says `missing_arm` | story 3 procedure |
| Repro arm | dependency install or test command cannot run in `parent/` | record `--kind bug` with `--at-parent` absent is refused; report the arm as missing with the reason in Story 3's report | story 3 procedure |
| Story 4 | report `unverifiable` for an upgrade | that upgrade untouched; spec status names the reason | outcome test |

## Shadow Paths

| Flow | Happy | Nil | Empty | Upstream error |
|---|---|---|---|---|
| Trial run | all arms recorded, sheet written | no trial file → exit 2 | no upgrade-only findings anywhere → sheet with acks only, or no fields; `report` decides from acks and zero-finding `remove` | yuss unreachable → exit 2 before any write |
| Report | four decided verdicts | — | no labels → `unverifiable` per affected upgrade | trial file malformed → exit 2 |
| Story 4 | report committed, removals applied | `labeled_by` null → stop at task 4.1 | every verdict `keep` → no removal edits, records only | a removal leaves `rg` hits → story fails its own verification |

## Interaction Edge Cases

| Edge case | Handling |
|---|---|
| The design-divergence blind trial removed Gate 0 before `init` | presence probe fails; `absent`; no Gate 0 arm |
| It removes Gate 0 after `init` but before Story 4 | Story 4 finds the wiring gone; records "already removed by design-divergence Story 6"; no edit |
| This trial removes Gate 0; the blind trial later says `keep` | the skill stays with `/prototype` as its only caller (spec.md Business Rule 12) |
| Both review-route upgrades removed | delete `review-override.py switch` too (review-route-rigor § Clean Removal) |
| An upgrade-only key equals a key the other upgrade's arm raised | counted for each upgrade separately; labeled once per finding ID |
| The human labels a Gate 0 finding valid but the cited sketch line does not avoid it | the label rule makes that `invalid`; the excerpt shows the sketch line |
| Two upgrades both `remove` and both edit `commands/implement-story.md` | apply edits in one pass; re-pin the ratchet once |

## Files in Scope

| File | Story | Change |
|---|---|---|
| `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py` | 1, 2 (deleted in 4) | New, temporary |
| `scripts/tests/test_gate_upgrade_trial.py`, `scripts/tests/fixtures/gate-upgrade-trial/` | 1, 2 (deleted in 4) | New, temporary |
| `scripts/tests/test_gate_upgrade_trial_outcome.py` | 3 | New |
| `.writ/eval/gate-upgrade-trial/prompts/*.md`, `<date>-gate-upgrade-trial.json`, `labeling-sheet.md` | 3 | New |
| `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/rating-handoff.md`, `spec.md` status | 3 | New / status line |
| `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/trial-report.md` | 4 | New |
| Removal-inventory files (§ Verdict Execution), generated trees, root `SKILL.md`, `scripts/tests/test_governor_enforcement.py` | 4 | Only for `remove` verdicts |
| `.writ/product/roadmap.md` | 4 | "Removal measurement" line only |
| `.writ/decision-records/adr-030-contract-verifier-boundary-front-door.md` | 4 | § Review note only |

Never touched: `commands/why.md`, `commands/writ.md`, `commands/retro.md`, `commands/refresh-command.md`, anything under `/Users/asellke/Projects/yuss`. No yuss source, diff, story, or reviewer text is committed.

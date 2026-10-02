# Technical Spec: Cross-Family Review Panel

> Parent: [`../spec.md`](../spec.md)
> Stories: 1 (config/status/amendments), 2 (tally), 3 (Gate 3 wiring), 4 (trial harness), 5 (trial and verdict)

## Architecture

```
.writ/config.md ── Review Panel line ──► review-panel.py status ──► active reviewers (slugs, vendors)
                                                │
Gate 2.5 gate3_route ─┐                         │
--panel flag ─────────┴─► trigger? ─────────────┤
                                                ▼
                  one message: primary Gate 3 agent + N panel Tasks (same prompt, model=<slug>, readonly)
                                                │
              primary output ──► review-override.py check (unchanged)
              all outputs   ──► review-panel.py tally ──► block | pass | unverifiable (+ advisory notes)
                                                │
                              block ──► Gate 3 FAIL path (recode, one loop increment)
```

The script never spawns a model and never touches the network. Spawning belongs to the orchestrator and the platform (ADR-028 driver 3: delegate mechanics, own contracts). The script owns the config contract, the vendor table, the matching rule, and the verdict.

## Config Contract

```markdown
- **Review Panel:** gpt-5.6-sol-medium, cursor-grok-4.6-medium-fast
```

- Read from `.writ/config.md` under any section; first matching line wins (same convention as `- **Judgment Provider:**` in `jev-judge.py`).
- Value `none` (case-insensitive) → `unverifiable` `panel_disabled`. Missing line → `unverifiable` `no_config_line`. Empty list after splitting on commas → `unverifiable` `malformed_config`.
- Slugs are trimmed, compared case-sensitively for duplicates, and kept in order.

## Vendor Table

| Prefix (slug, lowercase) | Origin name word | Vendor |
|---|---|---|
| `claude-` | Claude | anthropic |
| `gpt-`, `o1`…`o9` | GPT | openai |
| `grok-`, `cursor-grok-` | Grok | xai |
| `gemini-` | Gemini | google |
| `composer-` | Composer | cursor |
| `muse-` | Muse | meta |

Longest matching prefix wins (`cursor-grok-` before any `cursor-` rule). Origin matching is a case-insensitive word match on the model name the harness reports (e.g. "Claude Fable 5.1" → anthropic). The table is a module constant with one test per row.

## `status`

```
python3 scripts/review-panel.py status --repo . --origin "<origin model name>" [--platform cursor|claude-code|codex|openclaw] [--json]
```

| Result | Verdict | Reason lines |
|---|---|---|
| ≥1 kept reviewer, platform cursor (or unspecified) | `pass` | `reviewer: <slug> <vendor>` per kept; `dropped: <slug> <reason>` per dropped |
| No line / `none` / empty | `unverifiable` | `no_config_line` / `panel_disabled` / `malformed_config` |
| Origin vendor unknown | `unverifiable` | `unknown_session_vendor` |
| All dropped | `unverifiable` | `no_other_vendor` + the drop lines |
| `--platform claude-code` or `codex` | `unverifiable` | `platform_cannot_spawn_other_vendors` |
| `--platform openclaw` | as cursor, plus `reason: unverified_platform` | (adapter says spawn and drop on rejection) |

Drop reasons: `same_vendor`, `unknown_vendor`, `duplicate_slug`, `over_cap` (beyond 3 kept). Summary line: `review-panel: <pass|off|skipped> — …` matching the spec's State Catalog. Exit 0 in every case above; 2 on usage errors (missing `--origin`, unreadable repo).

## Tagged Output Contract (both Gate 3 agents)

Checklist line (evaluator already emits this; review-agent gains it):

```
- [ ] Given …, when …, then … — not satisfied: <evidence> `[AC-2.3]`
```

Issue entry (both agents gain the Category line):

```
- **Issue:** …
- **Location:** `app/api/pay.ts:42`
- **Severity:** Critical | Major | Minor
- **Category:** criterion | security | architecture | taste
- **Suggested Fix:** …   (review-agent; optional for evaluator)
```

Files: `agents/evaluator-agent.md`, `agents/review-agent.md`, `claude-code/agents/writ-evaluator.md`, `claude-code/agents/writ-reviewer.md`; regenerate `codex/agents/*.toml` with `scripts/gen-codex-agent-tomls.py` (the `codex-tomls` eval check enforces freshness). `jev-judge.py`'s `EVALUATOR_LINE` already parses tagged checklist lines from either agent, so the review-agent tag is useful even if the panel is removed.

## `tally`

```
python3 scripts/review-panel.py tally --origin "<origin model name>" --primary FILE \
    --reviewer <slug>=FILE [--reviewer <slug>=FILE …] [--json]
```

**Parse per output:**
1. Verdict line `### EVALUATION_RESULT: X` or `### REVIEW_RESULT: X`. Missing → reviewer dropped `malformed_output` (primary missing → exit 2: the primary is today's path and must parse).
2. Keys from unchecked checklist lines: regex compatible with `jev-judge.py` `EVALUATOR_LINE`, `[ ]` only → `ac:AC-N.M` (a multi-ID tag yields one key per ID).
3. Keys from `Issues Found` entries: Severity ∈ {Critical, Major} and Category ∈ {security, architecture} and a Location → `<category>:<normalized path>`. Normalization: strip backticks, leading `./`, trailing `:<digits>(-<digits>)?`, whitespace.

**Combine:** vendor per output (primary from `--origin`, reviewers from slug). Two outputs from the same vendor are merged as one vendor (cannot happen after `status`, but `tally` is defensive). For each key, collect distinct vendors.

| Key's vendors | Classification | Printed |
|---|---|---|
| ≥2 distinct | consensus | `review-panel: block — <key display> (<vendors, primary first>)` |
| exactly 1, a panel vendor | advisory | `review-panel: advisory — <key display> (<vendor>)` |
| exactly 1, the primary | primary-only | not printed (primary verdict governs) |

Key display: `ac:AC-2.3` → `AC-2.3 unmet`; `security:app/api/pay.ts` → `security app/api/pay.ts`.

**Verdict:** any consensus → `block` (exit 1). Zero usable panel reviewers → `unverifiable` `no_usable_reviewer` (exit 0). Else `pass` (exit 0). `--json` adds per-key vendor lists and each vendor's original Issue text (for the recode brief) — text stays in `.writ/state/`, never in committed files.

**Mutation fixtures** (`scripts/tests/fixtures/review-panel/`): consensus on an AC between primary and one panel reviewer → `block`; consensus between two panel reviewers when primary passed → `block`; same AC from one panel reviewer only → `advisory`, exit 0; same file, different categories → no consensus; Minor security on same file from two vendors → no consensus; malformed reviewer → dropped, others counted; two reviewers same vendor → counted once.

## Gate 3 Wiring (Story 3)

Insert one paragraph in `commands/implement-story.md` after the **Risk route** paragraph, mirrored in `commands/implement-story.lean.md`:

> **Review panel (opt-in).** When `python3 scripts/review-panel.py status --repo . --origin "<origin>" --platform <origin platform>` prints `pass` and `gate3_route` names `review-agent` or `--panel` is set, spawn each listed reviewer beside the Gate 3 agent in the same message: same prompt and inputs, `readonly`, `model: <slug>`, plus one line not to open `.env*`, `*.pem`, `*.key`, `*secret*`, `*credential*` files. Drop any reviewer the platform rejects or that returns nothing, with one `review-panel: dropped` line. After `review-override.py`, run `python3 scripts/review-panel.py tally --origin "<origin>" --primary <out> --reviewer <slug>=<out> …`. `block` is a Gate 3 FAIL (one loop increment even if the agent also failed; on PAUSE, Gate 3.5 lists the block lines and accept still recodes). `advisory`, `pass`, `unverifiable`, `skipped`, `off`: print the lines and continue. The panel can only add blocks; it never changes the Gate 3 agent's verdict and never marks a story `⚠️ DEGRADED`.

Plus:
- Invocation table row: `` `/implement-story story-3 --panel` `` | convene the review panel at Gate 3 regardless of route (needs the config line); usage error with `--quick`.
- Step 4 item 8 report list: add `review-panel:` beside `gate3-route:`.
- Spawn prose must not introduce a `Task(` marker with a new `*-agent` stem (`spawn-cap.py` `ALLOWED_STEMS`).
- `test_lean_commands.py` heading parity: no new headings.
- Ratchet: `scripts/tests/test_governor_enforcement.py` `"commands/implement-story.md": 11110` re-pinned with a dated disclosure (`Updated 2026-10-NN (spec 2026-10-01-cross-family-review-panel, Story 3): … Inline prose, no new step, gate, or spawn site. Acknowledged, not exempted.`). If `2026-10-01-behavioral-verification` Story 4 lands first, rebase on its value.

## Adapter Rows (Story 1)

| Adapter | Row text (summary) |
|---|---|
| `adapters/cursor.md` | Panel available: the `Task` tool's `model` accepts listed slugs across vendors; panel + primary ≤ 4 concurrent Tasks; a slug missing from the run-time list is dropped `slug_rejected`. |
| `adapters/claude-code.md` | Panel unavailable: subagent `model` accepts Anthropic aliases, IDs, or `inherit`. Gate 3 runs as today; `status --platform claude-code` prints the skip. |
| `adapters/codex.md` | Panel unavailable by default: subagents run the configured provider. Same fallback. |
| `adapters/openclaw.md` | *(unverified)* attempt spawn with `model: <slug>` via `sessions_spawn`; a rejected model drops that reviewer. |

## ADR-028 Amendment (Story 1)

Amend Decision 3 and add a dated amendment note:
- **Additive authority:** the session's Gate 3 agent and `review-override.py` decide as before; consensus (≥2 vendors, primary counted as one) adds a block; one-vendor panel findings are advisory.
- **Stakes signal:** ADR-023 triage is applied mechanically through Gate 2.5's `gate3_route` (`review-agent` route) plus an explicit `--panel` override.
- **Matching rule:** same unmet `[AC-N.M]`, or same file + same category (security/architecture) at Critical/Major.
- **Exclusions are instructions:** reviewers are agents with file tools; the exclusion list is a prompt line, not enforcement. The config line is the consent.
- **Removal measurement:** retrospective trial in Cursor over the four baseline stories' historical commits (the baseline runs were Claude Code-driven and recorded no findings).

Roadmap Phase 12 Feature 3 text gains a pointer to this spec; no success criterion changes.

## Trial Harness (Story 4)

```
review-panel.py trial-init    --baseline .writ/eval/baselines/2026-09-07-claude-fable-5-1.json --out .writ/eval/panel-trial/<date>-panel-trial.json
review-panel.py trial-prepare --trial FILE --yuss PATH --story ID [--tmp-root DIR]
review-panel.py trial-record  --trial FILE --story ID --arm evaluator|panel --origin "<model>" --primary FILE [--reviewer slug=FILE …]
review-panel.py trial-label   --trial FILE --story ID --key KEY --label valid|invalid --note "<≤200 chars, no source>"
review-panel.py trial-report  --trial FILE [--json]
```

- **`trial-init`** copies the baseline's `selection` (story_id, story_path, spec_folder, story_commit, parent_sha) into a `panel-trial-v1` skeleton. Four stories, one per surface class.
- **`trial-prepare`** builds `$TMPDIR/writ-panel-trial-<story>/checkout` with `git init` + `git fetch --depth 2 <yuss> <story_commit>` + checkout, asserts the commit, writes `diff.patch` (`parent..commit`), the story file, and the spec's `## Specification Contract` into the run dir, and prints the paths. It writes nothing in yuss.
- **Arms.** In Cursor, the maintainer spawns the evaluator prompt over the prepared inputs: once alone (arm `evaluator`, the session model), and once as primary + panel reviewers in one message (arm `panel`). Both arms get identical inputs; `recorded_test_results` = the story's own What Was Built test results, labeled "historical, not re-run".
- **`trial-record`** runs the `tally` parser over the outputs and stores, per story and arm, the keys with their vendors and severities. Raw outputs are copied to `.writ/state/panel-trial/<story>/` (gitignored). No text enters the trial JSON.
- **Panel-only finding:** a key in the `panel` arm raised by ≥1 panel vendor and absent from the `evaluator` arm. `trial-record` marks these `label: null`.
- **`trial-label`** sets each panel-only label; the note is capped at 200 chars and rejected if it contains a newline or a backtick block.
- **`trial-report`** prints `keep` / `remove` / `unverifiable` per Business Rule 12, the per-story counts, and the caveat line `sample: 4 stories; one valid miss keeps the panel — a low bar, not a cost case`.

## Trial Execution and Verdict (Story 5)

1. Run the four stories through the harness in Cursor; label; run `trial-report`; commit the trial JSON and `trial-report.md` in the spec folder.
2. **`keep`:** ADR-028 amendment records the result (stories, valid panel-only findings, date). Roadmap Phase 12 success criterion 4 marked met. Spec closes `Complete`.
3. **`remove`:** delete the Gate 3 panel paragraph, the `--panel` row, the `review-panel:` report entry, the config doc entry, the adapter rows, `check_review_panel`, and `status`/`tally` (and their tests). Keep the trial subcommands' committed output (trial JSON, `trial-report.md`) as the record; the script is deleted with the path, so the report must be committed first. Keep the agents' `[AC-N.M]` and Category tags (live consumer: `jev-judge.py ac-shadow`). Re-pin the ratchet downward with disclosure. ADR-028 records the removal; the spec closes `Closed — Not Implemented`; roadmap criterion 4 marked met by its second branch.
4. **`unverifiable`:** the trial is incomplete; the spec stays open with the blocking reason. It is not a verdict.

## Error & Rescue Map

| Operation | Failure | Rescue | User sees |
|---|---|---|---|
| Read config | `.writ/config.md` missing or no line | panel off | nothing (Gate 3 unchanged) |
| Resolve vendors | unknown session vendor | skip panel | `review-panel: skipped — unknown_session_vendor` |
| Resolve vendors | every slug dropped | skip panel | `review-panel: skipped — no_other_vendor (…)` |
| Platform check | Claude Code / Codex | skip panel | `review-panel: skipped — platform cannot spawn other vendors` |
| Spawn reviewer | slug rejected by Task tool | drop reviewer | `review-panel: dropped <slug> — slug_rejected` |
| Spawn reviewer | timeout / empty return | drop reviewer | `review-panel: dropped <slug> — no_output` |
| Parse reviewer | no verdict line | drop reviewer | `review-panel: dropped <slug> — malformed_output` |
| Parse primary | no verdict line | exit 2; today's Gate 3 handling of a malformed agent result applies | existing behavior |
| Tally | no usable reviewer left | continue | `review-panel: unverifiable — no_usable_reviewer` |
| Tally | consensus found | Gate 3 FAIL → recode | `review-panel: block — …` |
| Trial prepare | yuss path missing / commit unreachable | exit 2, nothing written | one-line error naming the story |
| Trial report | unlabeled finding or missing arm | `unverifiable` | `review-panel: unverifiable — 2 unlabeled` |

## Shadow Paths

- **Happy path:** config on, risky story, 2 reviewers, one shared AC finding → block → recode → second Gate 3 → pass.
- **Nil input:** no config line → nothing printed, Gate 3 identical (verified by diffing the prose path: no new step executes).
- **Empty input:** config line `none` or empty → `off`/`skipped`, Gate 3 identical.
- **Upstream error:** Task tool rejects every slug → all dropped → `unverifiable`, primary verdict stands.

## Interaction Edge Cases

| Case | Behavior |
|---|---|
| Primary FAIL + panel block | one recode, one loop increment |
| Primary PAUSE + panel block | Gate 3.5 presents options with block lines; accept still recodes |
| Primary PASS + `review-override.py` fail + panel pass | override fail recodes (unchanged) |
| Two-fail escalation | panel block counts as a Gate 3 FAIL for `evaluator_fail_count`; after escalation `review-agent` is primary and the panel still runs |
| `--review-only --panel` + block | run ends, like a FAIL |
| `--panel --quick` | usage error before any gate |
| Story has no AC tags (legacy) | only category keys can match; `ac-trace.py` already flags untagged stories elsewhere |

## Files in Scope

| File | Story | Change |
|---|---|---|
| `scripts/review-panel.py` | 1, 2, 4 | new — `status`, `tally`, `trial-*` |
| `scripts/tests/test_review_panel.py` | 1, 2, 4 | new |
| `scripts/tests/fixtures/review-panel/` | 2, 4 | new — reviewer outputs, mini baseline, trial files |
| `.writ/docs/config-format.md` | 1 | `Review Panel` key |
| `.writ/decision-records/adr-028-…md` | 1, 5 | Decision 3 amendment; trial outcome |
| `adapters/{cursor,claude-code,codex,openclaw}.md` | 1 | panel row each |
| `agents/evaluator-agent.md`, `agents/review-agent.md` | 2 | Category line; review-agent AC tags |
| `claude-code/agents/writ-{evaluator,reviewer}.md`, `codex/agents/*.toml` | 2 | mirrors / regenerate |
| `commands/implement-story.md`, `commands/implement-story.lean.md` | 3 | Gate 3 paragraph, `--panel` row, report line |
| `scripts/eval.sh` | 3 | `check_review_panel` + registration |
| `scripts/tests/test_governor_enforcement.py` | 3, 5 | ratchet re-pin |
| `.writ/eval/panel-trial/*.json`, `{spec}/trial-report.md` | 5 | trial record |
| `.writ/product/roadmap.md` | 1, 5 | Feature 3 pointer; criterion 4 outcome |

# Review-Route Rigor

> **Status:** In Progress
> **Created:** 2026-10-25
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Phase:** 15 — Code-Level Rigor ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 15 decomposition, authored with `/create-spec --recommend` (source mode `standard`). Research [F3](../../research/2026-10-19-writ-vs-pstack-research.md) names pstack's `blast-radius` and `interrogate` as the reference. Decisions: [`recommendation-log.md`](recommendation-log.md).

## Specification Contract

**Deliverable:** On the review-agent route, Gate 3's review names the one fact the change is safe because of and the evidence rung that fact reached, and a script re-derives that rung. Every reviewer prompt (`review-agent`, `evaluator-agent`, `/review`) applies three lead-judgment filters. Each of the two upgrades turns on or off with one named switch.

**Must Include:**

1. **A five-rung evidence ladder**, defined so a script can check each rung: `claimed`, `read`, `traced`, `tested`, `reproduced` (technical-spec § Evidence Ladder).
2. **Blast radius at Gate 2.5.** When `gate3_route` names `review-agent` and the `safety-fact` switch is on, `change-surface.py blast-radius` lists the files outside the change set that reference each changed file. Gate 3 passes the list to `review-agent` as `blast_radius`.
3. **The safety fact at Gate 3.** `review-agent` writes a `### Safety Fact` section with `Fact`, `Holds`, `Rung`, and `Evidence`. `review-override.py safety-fact` re-derives the measured rung from the evidence. The floor on this route is `traced`. Gate 3 routes each failure reason as technical-spec § Gate 3 Routing states.
4. **Three lead-judgment filters**, in one skill (`skills/review-judgment-filters/SKILL.md`):
   - all nits means the code is fine
   - trace the call site before accepting a hypothetical
   - be slow to dismiss security findings
5. **Two named switches**, `safety-fact` and `reviewer-filters`. Each is one line in `.writ/config.md` (`- **Safety Fact:** off`, `- **Reviewer Filters:** off`). An absent line means on. `review-override.py switch --name <switch>` resolves the state. Every Gate 3 run prints `safety-fact:` and `reviewer-filters:` lines in the story report, and every `/review` report records `Reviewer filters:` in its header.
6. **Clean removal.** Each upgrade's instructions live in one skill file. Agent bodies and `/review` carry only a conditional `Read` line and an input row. The technical spec lists the exact removal steps for each switch.
7. **Tests and regenerated trees.** Pytest coverage for every new subcommand on Python 3.9, a test that no filter or ladder text appears outside its skill, and generated trees rebuilt with `python3 scripts/gen-platform-trees.py`.

**Hardest Constraint:** The removal trial in `2026-10-25-gate-upgrade-removal-measurement` needs an off arm that carries none of the upgrade's text. Claude Code loads a native agent's whole body (`claude-code/agents/writ-reviewer.md`, `writ-evaluator.md`) as its system prompt, and `gen-claude-agents.py` copies that body verbatim from `agents/*.md`. So no filter or ladder text can live in an agent body. It must live in a skill that the reviewer reads only when its switch is on.

**🎯 Experience Design:**
- **Entry point:** `/implement-story` reaches Gate 2.5 and Gate 3 as it does today; `/review` runs as today. Nothing new to invoke.
- **Happy path:** Gate 2.5 routes `review-agent` and writes the blast radius; the reviewer names the safety fact, traces it to a caller, and cites the evidence; the script measures the rung at or above `traced`; the story report prints the fact and the rung.
- **Moment of truth:** the story report line `safety-fact: tested (claimed tested) — <fact>`. A reader sees why the change is safe and how well that was checked.
- **Feedback model:** story report lines (`safety-fact:`, `reviewer-filters:`), the script's claim-versus-measurement line, and the `/review` header line.
- **Error experience:** a missing or under-evidenced safety fact gets one re-review with the script's reasons; if it is still under the floor, the coder is sent back to add a test that exercises the named fact. A switch line with a bad value prints its reason and falls back to on.

**📋 Business Rules:**
- The safety fact is required only when `gate3_route` names `review-agent` and the `safety-fact` switch is on. The evaluator route, `--review-only`, and `--quick` never require it.
- The measured rung, not the claimed rung, decides the floor. An overclaim is printed, not blocked on its own.
- `Holds: no` must come with a FAIL verdict. `Holds: no` with PASS is a Gate 3 FAIL.
- Filter 3 overrides filter 2 for security findings. A security finding is dismissed only by citing the guard that prevents it.
- Switches default to on. Only the exact value `off` (any case) turns a switch off.
- The verifier's `unverifiable` never fails Gate 3 and never marks a story `⚠️ DEGRADED`.

**Success Criteria:**
- On a fixture review output, `review-override.py safety-fact` prints the measured rung for each of the five rungs and fails below `traced`.
- `review-override.py switch` prints `on` with no config line and `off` with `- **Safety Fact:** off` or `- **Reviewer Filters:** off`.
- `change-surface.py blast-radius` lists every tracked file outside the change that references a changed file's stem or path, capped per file, on Python 3.9.
- A pytest proves the three filter sentences and the ladder rung definitions appear only in their skill files, not in `agents/`, `commands/`, or `claude-code/agents/`.
- `uv run --python 3.9 pytest`, the bash tests, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` pass.

**Scope Boundaries:**
- Included: Gate 2.5 blast radius; Gate 3 safety fact and its verifier; reviewer filters in `review-agent`, `evaluator-agent`, and `/review`; two switches, their resolver, and their `.writ/docs/config-format.md` entries; two skills with their manifest, README, and root `SKILL.md` registration; tests; regenerated trees.
- Excluded: the removal trial itself (owned by `2026-10-25-gate-upgrade-removal-measurement`); always-on multi-model panels; cross-vendor routing (ADR-024 stands); formal verification; Gate 0 (owned by the design-divergence spec); `/security-audit`; changes to `review-panel.py` tallying.

**⚠️ Technical Concerns:**
- `commands/implement-story.md` is 36,226 bytes, already over the 24,960-byte per-invocation budget (non-blocking warning in `.writ/docs/leanness-audit-2026-10-21.md`). Gate 2.5 and Gate 3 may grow by at most 1,800 bytes net. The how goes into the skills; the gates keep only the when.
- The blast radius is a text-reference heuristic, not a call graph. Generic stems (`index`, `utils`, `types`, `main`, `__init__`) would match everywhere, so the script searches by path for those. It caps results per changed file and marks the cap.
- The reviewer cannot reach `reproduced` on a first Gate 3 pass, because Gate 4.5 runs after Gate 3. It can reach it only on a recode iteration where an `app-verify.py run` pass already exists for the story. The floor is `traced` for this reason.
- Panel reviewers get "the same prompt and inputs" (Gate 3), so they also read the skills when the switches are on. The verifier runs only on the primary reviewer's output.

**💡 Recommendations:**
- Put both resolvers in `review-override.py` (`switch`, `safety-fact`) rather than a new script. It is Gate 3's script already, and removing an upgrade then means deleting one subcommand.
- Use a skill per upgrade, not one shared skill. One folder per switch makes removal a folder delete plus two lines.
- Send a below-floor safety fact back to the reviewer once before recoding. A missing trace is a reviewer gap, and the coder cannot fix it.

**⚠️ Cross-Spec Overlap:**
- No in-progress spec exists on disk: every `.writ/specs/*/spec.md` resolves complete-family (`scripts/spec-status.py is-complete`).
- Phase 15 siblings are being authored in parallel and will share three areas. All three are advisory, not blocking:
  - `commands/implement-story.md`: the design-divergence spec owns Gate 0; this spec owns Gate 2.5 and Gate 3 only.
  - `.writ/manifest.yaml` `skills:` list: the design-divergence spec adds `design-divergence`; this spec adds `blast-radius` and `review-judgment-filters`. These are append-only entries.
  - Generated trees (`claude-code/`, plugin trees) and root `SKILL.md`: every spec regenerates them. Regenerate after rebasing, never hand-merge.
  - `.writ/docs/config-format.md` and the README `## Skills` table: the design-divergence, repro-first, and this spec each add rows. Append only.
- The sibling switches disagree on a malformed value: `Repro First` reads it as on (as this spec does), `Gate 0 Divergence` reads it as off. The removal-measurement spec should settle one rule.
- `2026-10-25-gate-upgrade-removal-measurement` consumes this spec's switches and report lines. It depends on this spec, not the reverse.

## Experience Design

### Who uses it

- **The orchestrator running `/implement-story`.** It resolves the switches, computes the blast radius, passes inputs to Gate 3, runs the verifier, and prints the report lines.
- **`review-agent`** on the risk route. It names the fact, pushes it up the ladder, and writes the section.
- **`evaluator-agent`** on the default route, and **`/review`**. They read the filters skill when the switch is on.
- **The maintainer running the removal trial.** They flip one config line per arm and read the report lines to confirm the arm.

### Journey

1. Gate 2.5 classifies the surface and computes `gate3_route` as today.
2. When the route names `review-agent` and `safety-fact` is on, Gate 2.5 runs `change-surface.py blast-radius` and saves `.writ/state/blast-radius-<story-stem>.json`.
3. Gate 3 resolves `reviewer-filters` and passes `reviewer_filters`, `safety_fact`, `blast_radius`, and `recorded_test_results` to the reviewer.
4. The reviewer reads the skills its switches allow, reviews, and writes the verdict with a `### Safety Fact` section when `safety_fact` is `on`.
5. The orchestrator saves the review output and runs `review-override.py check` (unchanged) and `review-override.py safety-fact`.
6. The story report prints `gate3-route:`, `safety-fact:`, and `reviewer-filters:` lines.

### State Catalog

| State | What the story report shows |
|---|---|
| Evaluator route | `safety-fact: not on route` · `reviewer-filters: on` |
| Risk route, fact at or above floor | `safety-fact: traced (claimed tested) — <fact>` |
| Risk route, `Holds: no`, reviewer FAIL | `safety-fact: traced (claimed traced) — <fact> — does not hold`; Gate 3 FAIL as usual |
| Risk route, `Holds: no`, reviewer PASS | `safety-fact: … — contradicts verdict`; Gate 3 FAIL, recode |
| Risk route, section missing after one re-review | `safety-fact: missing`; BLOCKED escalation for `review-agent` |
| Risk route, below floor after one re-review | `safety-fact: read (claimed traced) — <fact> — below floor`; Gate 3 FAIL, recode with "add a test that exercises the fact" |
| `safety-fact` switch off | `safety-fact: off`; no blast radius, no section, no verifier |
| `reviewer-filters` switch off | `reviewer-filters: off`; no reviewer reads the filters skill |
| Verifier cannot read the review output | `safety-fact: unverifiable (<reason>)`; Gate 3 continues, not DEGRADED |
| Blast radius unverifiable (no git, unreadable repo) | `blast_radius` passed as the script's JSON with `verdict: unverifiable`; `traced` then needs at least one cited caller that exists |
| Config line with a bad value (`- **Safety Fact:** of`) | Resolver prints `on` and `reason: malformed_value of` |

### Interaction Patterns

- One switch per upgrade, one config line per switch. A trial arm is one line.
- Claim and measurement side by side, as Gate 3 and Gate 4 already print them.
- The reviewer gets one re-review before the coder is asked for anything.

## Business Rules (Expanded)

### When the safety fact applies

| Run | `gate3_route` | Gate 3 agent | Safety fact required |
|---|---|---|---|
| default | `evaluator-agent` | evaluator | no |
| default | `review-agent` | review-agent | yes, when switch on |
| `--full-pipeline` | `review-agent` | review-agent | yes, when switch on |
| `--full-pipeline` | `evaluator-agent` | review-agent | no |
| two-fail escalation | `evaluator-agent` | review-agent | no |
| `--review-only` | none (no map) | evaluator | no |
| `--quick` | — | none | no |

The rule follows ADR-030's "high-stakes routes" (`gate3_route` names `review-agent`). `--panel` on the evaluator route adds panel reviewers but no safety fact.

### Verifier outcomes

| Verifier result | First occurrence | After one re-review |
|---|---|---|
| `pass` | continue | continue |
| `fail` `safety_fact_missing` | re-spawn `review-agent` once with the reason lines | BLOCKED escalation, agent `review-agent`, restart Gate 3 |
| `fail` `safety_fact_below_floor` | re-spawn `review-agent` once with the reason lines | Gate 3 FAIL, recode; the coder receives the fact and is asked to add a test that exercises it |
| `fail` `safety_fact_contradicts_verdict` | Gate 3 FAIL, recode | — |
| `unverifiable` | continue, reason printed, not DEGRADED | — |

The re-review and the first review count as one Gate 3 attempt: no `review_cycle` increment, as with ADR-024's anchor re-run. A verifier fail and an agent FAIL in the same Gate 3 pass are one increment. On PAUSE, the verifier's lines are listed with the drift options, and accept still recodes when the verifier failed (the same rule the panel's `block` follows).

### Switch resolution

- Lines are read from `.writ/config.md`, first match wins, anywhere in the file.
- `off` in any case turns the switch off. `on`, an empty value, or no line means on.
- Any other value means on, with `reason: malformed_value <value>`.
- A missing or unreadable `.writ/config.md` means on, with `reason: no_config`.
- Unknown `--name` is a usage error (exit 2).

### Filters

1. **All nits means the code is fine.** If every finding is a nit (naming, formatting, comments, a refactor preference, a missing nice-to-have), the verdict is PASS and the nits go under recommendations. Do not raise a nit's severity to justify a FAIL.
2. **Trace the call site before accepting a hypothetical.** A finding that rests on an input or state the reviewer imagines ("what if this is null", "what if two requests race") stands only when the reviewer cites a caller, `path:line`, that can produce it. Input that crosses a trust boundary (user input, network, files, environment) can produce any value. With no such caller, the finding is dropped or moved to recommendations.
3. **Be slow to dismiss security findings.** Filter 2 does not apply to security. A security finding is dismissed only by citing the guard, `path:line`, that prevents it. Without that citation it stays at Major or above.

## Detailed Requirements

### Story 1: Upgrade switches

`review-override.py switch --name safety-fact|reviewer-filters [--repo .]` resolves a switch from `.writ/config.md` per § Switch resolution. It prints the check shape the agent CLI contract defines: line 1 `on` or `off`, `reason:` lines, summary last. Tests cover absent file, absent line, `off`, `OFF`, `on`, empty value, malformed value, unknown name, and that the existing `check` subcommand is unchanged.

### Story 2: Reviewer lead-judgment filters

`skills/review-judgment-filters/SKILL.md` holds the three filters (§ Filters) and passes `bash scripts/lint-skill.sh`. `.writ/manifest.yaml` gains its entry. `agents/review-agent.md` and `agents/evaluator-agent.md` gain a `reviewer_filters` input row and one line: when `reviewer_filters` is `on`, read the skill and apply it before setting the verdict. `commands/review.md` resolves the switch in Step 3, reads the skill when on, and records `> Reviewer filters: on|off` in the report header. Gate 3 resolves the switch, passes `reviewer_filters` to the Gate 3 agent (and so to panel reviewers), and prints `reviewer-filters: <state>`. A pytest proves the filter text appears only in the skill.

### Story 3: Blast radius at Gate 2.5

`change-surface.py blast-radius --changed FILE … [--repo .] [--limit N] [--pretty]` lists, per changed non-test file, the tracked files outside the change set that reference it (technical-spec § Blast Radius). Gate 2.5 resolves the `safety-fact` switch and runs it only when the route names `review-agent` and the switch is on, saving `.writ/state/blast-radius-<story-stem>.json`. Otherwise `blast_radius` is `(none)`. Tests cover stem search, path search for generic stems, exclusion of changed files and tests, the per-file cap, the no-git fallback, unreadable files, and that `classify` is unchanged.

### Story 4: Safety fact at Gate 3

`skills/blast-radius/SKILL.md` holds the ladder (§ Evidence Ladder), the section format, and how to push a fact up the ladder. `.writ/manifest.yaml` gains its entry. `agents/review-agent.md` gains `safety_fact`, `blast_radius`, and `recorded_test_results` input rows, one conditional `Read` line, and a one-line output slot for the section. `review-override.py safety-fact` re-derives the measured rung (technical-spec § Verifier). Gate 3 passes the inputs, saves the review output and recorded test run under `.writ/state/`, runs the verifier, routes its reasons per § Verifier outcomes, and prints `safety-fact:`. Tests cover every rung, each fail reason, the overclaim line, and unreadable input. A pytest proves the ladder text appears only in the skill.

## Implementation Approach

- **Script first, prose second.** Each story writes its pytest before its subcommand, then the prose that calls it.
- **Two skills, one per switch.** The skill owns the how; Gate 2.5 and Gate 3 own the when and the routing, per the existing "this gate owns when, the skill owns how" pattern in `implement-story.md`. Agent bodies get input rows and one conditional line each.
- **Stay inside owned sections.** Edits to `commands/implement-story.md` stay inside `#### Gate 2.5` and `#### Gate 3`. Step 4 item 8's report-line list is not edited; Gate 3 states the new lines, as it already does for `gate3-route:`.
- **Regenerate, never hand-edit.** After changing `agents/`, `commands/`, or `skills/`, run `python3 scripts/gen-platform-trees.py` and commit the generated trees in the same story.
- **Python 3.9 floor.** No `match`, no `X | Y` type unions at runtime, no 3.10+ `pathlib` or `str` methods. `from __future__ import annotations` as the existing scripts do.
- **Story order.** 1 → 2 → 3 → 4. Stories 2, 3, and 4 all edit `commands/implement-story.md`, and 2 and 4 both edit `agents/review-agent.md` and `.writ/manifest.yaml`, so they run in sequence.

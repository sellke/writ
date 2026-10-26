# Story 4: Safety fact at Gate 3

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1, Story 2, Story 3

## User Story

**As a** review-agent on the risk route, the `/implement-story` orchestrator, or the maintainer reading story reports
**I want to** get one named safety fact for each Gate 3 review, with its evidence rung re-derived by a script
**So that** a reader sees why the change is safe and how well that was checked, and an unevidenced claim fails Gate 3

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given fixture review outputs that cite evidence for each of the five rungs (`claimed`, `read`, `traced`, `tested`, `reproduced`), when `review-override.py safety-fact` runs on each, then it prints the measured rung that the technical-spec ladder table assigns to that evidence, and a cited path that does not exist or resolves outside `--repo` is rejected so the rung does not count `[AC-4.1]`
- [ ] Given a review output whose `Rung` is `traced`, when the blast-radius file is readable with verdict `pass`, then `traced` is accepted only when at least one cited caller is in the union of its `consumers`, and `- traced: none` is accepted only when that union is empty and the file's verdict is `pass` `[AC-4.2]`
- [ ] Given review outputs that trigger each fail reason, when the verifier runs, then `safety_fact_missing`, `safety_fact_below_floor <measured>`, and `safety_fact_contradicts_verdict` each fire on their own condition, every applicable reason prints in table order, an overclaim alone prints the `rung:` line without a fail, and an unreadable review output prints `unverifiable` with `review_output_unreadable` and exits 0 `[AC-4.3]`
- [ ] Given the review-agent route with the `safety-fact` switch on, when Gate 3 runs, then it runs the verifier and routes each reason as spec.md → Business Rules → Verifier outcomes states, and the one re-review counts as the same Gate 3 attempt with no `review_cycle` increment `[AC-4.4]`
- [ ] Given the `safety-fact` switch off, or the evaluator route, when Gate 3 runs, then no `### Safety Fact` section is requested, no verifier runs, and the story report prints `safety-fact: off` or `safety-fact: not on route`, and a pytest fails if any ladder rung definition appears in `agents/*.md`, `commands/*.md`, or `claude-code/agents/*.md` `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Write verifier tests first in `scripts/tests/test_review_override.py` (rung fixtures, path escape, `traced` consumers rule, fail reasons, unreadable output) and the ladder-placement test in `scripts/tests/test_review_route_rigor.py` `[AC-4.1, AC-4.2, AC-4.3, AC-4.5]`
- [ ] 4.2 Implement the `safety-fact` subcommand in `scripts/review-override.py`: parse the section, re-derive the measured rung, print `pass` or `fail` with reasons, `rung:` and `fact:` lines, and summary last `[AC-4.1, AC-4.2, AC-4.3]`
- [ ] 4.3 Write `skills/blast-radius/SKILL.md` (ladder, Safety Fact section format, push-up rules, reading `blast_radius`, `Holds: no`) and its `.writ/manifest.yaml` entry; add its README `## Skills` row, update the live-skill count, and regenerate the root `SKILL.md` with `bash scripts/gen-skill.sh` `[AC-4.5]`
- [ ] 4.4 Edit `agents/review-agent.md`: add input rows `recorded_test_results`, `safety_fact`, `blast_radius`, one conditional `Read skills/blast-radius/SKILL.md` line, and a one-line output slot; add no ladder text `[AC-4.4, AC-4.5]`
- [ ] 4.5 Edit only the `#### Gate 3` section of `commands/implement-story.md`: pass inputs on the risk route, save review output and recorded test run under `.writ/state/`, run the verifier, route reasons, print the `safety-fact:` lines; measure growth with `wc -c` against the 1,800-byte cap shared with Gate 2.5 `[AC-4.4, AC-4.5]`
- [ ] 4.6 Regenerate trees with `python3 scripts/gen-platform-trees.py` and confirm the generated `claude-code/agents/` files match their sources `[AC-4.5]`
- [ ] 4.7 Verify acceptance criteria: run `uv run --python 3.9 pytest`, the bash test loop, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh`; check each AC against its test output `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

- `reproduced` is out of reach on a first Gate 3 pass. Gate 4.5 runs after Gate 3. The verifier can accept `reproduced` only on a recode iteration where a passing `app-verify-result-v1` file already exists for the story.
- Panel reviewers receive the same inputs as the primary reviewer. The verifier reads only the primary reviewer's output.
- A false safety fact is reported with category `architecture` (or `security` when it is one). This keeps `review-panel.py` keying unchanged.
- Do not touch Gate 0, Step 4, `agents/coding-agent.md`, or `skills/tdd-cycle/`.
- Byte budget: Gate 2.5 and Gate 3 together grow by at most 1,800 bytes net. `commands/implement-story.md` is already over the per-invocation budget. Keep the how in the skill and the when in the gate.
- The blast radius is a text-reference heuristic, not a call graph. Story 3 owns it. This story reads its JSON only.
- Integration: Story 1 provides the `switch` subcommand that Gate 3 calls. Story 2 and this story both edit `agents/review-agent.md` and `.writ/manifest.yaml`. Apply Story 2's changes first.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`safety-fact` reads review output, `safety-fact` resolves a cited path, `safety-fact` reads blast radius, `safety-fact` reads tests output] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Safety-fact verify, Gate 3 routing] — from technical-spec.md → Shadow Paths
- **Business rules:** [When the safety fact applies (required only on `gate3_route` = `review-agent` with switch on), Verifier outcomes (one re-review, then BLOCKED or recode), unverifiable never DEGRADED] — from spec.md → Business Rules (Expanded)
- **Experience:** [State Catalog rows for risk route, `safety-fact` off, and unverifiable (story report lines)] — from spec.md → Experience Design → State Catalog
- **Ladder and section format:** technical-spec.md → Evidence Ladder, Safety Fact Section, Verifier (parsing and output table)
- **Gate 3 wording:** technical-spec.md → Gate 3 Change (draft); byte budget in the same section

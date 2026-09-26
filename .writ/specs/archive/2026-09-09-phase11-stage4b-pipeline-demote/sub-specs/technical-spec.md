# Technical Spec — Phase 11 Stage 4b: Pipeline Demote

> Spec: `.writ/specs/2026-09-09-phase11-stage4b-pipeline-demote/`
> Stories: 1 (evaluator agent), 2 (default path + flags), 3 (eval + adapters + proof)

## 1. Evaluator agent (Story 1)

New file `agents/evaluator-agent.md`. Template: `agents/review-agent.md`’s shape (Agent Configuration, Input Requirements, Prompt Template, output headings). Content differs: rubric is acceptance criteria + recorded test results, not a general quality tour.

### Agent Configuration (required fields)

```
subagent_type: "generalPurpose"
model: default (inherits from parent)
model_tier: anchor
readonly: true
problem: "A story that satisfies its task list can still miss an acceptance criterion or quietly redefine the spec, and self-critique in the same context as the coder does not catch it."
outcome: "An EVALUATION_RESULT against the story's acceptance criteria and test results, with residual architecture / security / taste named, and no applied patch."
exit_criteria:
  - "the number of criteria adjudicated equals the number supplied; none left unaddressed"
  - "Overall Drift reads None, Small, Medium, or Large, and Large produces PAUSE rather than FAIL"
  - "every FAIL issue carries Location and Severity; Suggested Fix is optional and is never applied"
```

Prompt must say: report what is wrong; do not tell the coder how to fix; do not apply a patch; do not “find problems” beyond the rubric and the residual (architecture, security, taste).

### Platform counterparts

| Path | Constraint |
|---|---|
| `claude-code/agents/writ-evaluator.md` | tools: Read, Grep, Glob, Bash; `disallowedTools: Write, Edit`; `permissionMode: plan` |
| `codex/agents/evaluator-agent.toml` | `sandbox_mode = "read-only"`; name `evaluator-agent` |
| `scripts/check-agent-parity.sh` | `evaluator-agent) echo "writ-evaluator.md"` |
| `.writ/manifest.yaml` | `agents:` entry, `model_tier: anchor` |

Cursor: existing `.cursor/agents` → `agents/` symlink. No extra file. Do not add a `claude_exempt`. Do not edit `review-agent.md`.

## 2. Default path + flags (Story 2)

`commands/implement-story.md` only (plus story-file comments that name spawn agents).

### Invocation

| Invocation | Spawns |
|---|---|
| `/implement-story` / `/implement-story story-N` | `coding-agent`, `evaluator-agent` |
| `--full-pipeline` | architecture-check, coding, review, testing, optional visual-qa, docs |
| `--quick` | `coding-agent` only |
| `--review-only` | `evaluator-agent` only |

No `--default` token anywhere in the file.

### Two-fail escalation

Counter `evaluator_fail_count` starts at 0 per story. Evaluator FAIL increments it and recodes via Gate 1. When the increment makes the count 2, print one notice and treat the remainder of this story as `--full-pipeline`. Do not AskQuestion. `--quick` never escalates (no evaluator). `--review-only` has no recode spawn; a FAIL ends the run as today’s `--review-only` would.

### Gate 4 default fail

`test-integrity.py` `fail` → BLOCKED escalation with agent `coding-agent`, restart Gate 1. `--full-pipeline` keeps `testing-agent`, restart Gate 4.

### Gate 3 override

Call `review-override.py` after the Gate 3 agent returns, unchanged. On default, residual sentence names `evaluator-agent`. On `--full-pipeline`, it still names `review-agent`.

## 3. Spawn-cap helper (Story 3)

```
python3 scripts/spawn-cap.py check --command commands/implement-story.md
```

Python 3.9 stdlib. Count **default-path spawn sites**: a line that (a) sits in a Gate body that runs without `--full-pipeline`, and (b) names a spawn of an `agents/*.md` stem via the existing `> **Agent:**` marker or an equivalent Task-spawn instruction. Allowed default stems: `coding-agent`, `evaluator-agent`. `--full-pipeline`-guarded Agent markers do not count.

| Situation | verdict | reason | exit |
|---|---|---|---|
| Default path names ⊆ {coding-agent, evaluator-agent} and count ≤ 2 | `pass` | — | 0 |
| A third stem, or a disallowed stem, on the default path | `fail` | `over_cap` | 1 |
| `--command` missing or unreadable | `unverifiable` | `missing_command` | 0 |
| Usage | (stderr) | — | 2 |

One verdict line, optional `reason:`, summary last. Never print accept / reject / modify-spec.

`eval.sh` `CHECKS` += `spawn-cap`. Missing helper / exit 2 → `add_finding`. Other verdicts → `add_note`.

## 4. Adapter wording (Story 3)

Rewrite sentences that treat no-flag `/implement-story` as “the full SDLC pipeline” / “five-agent” / “six-gate” default. That path is `--full-pipeline`. Touch only the sentences that would relitigate the default. No new `/goal` section. No high-stakes classifier.

## 5. Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Spawn evaluator | Agent file missing | Finding; do not invent a review-agent fallback on default | Missing-file fixture / parity |
| Evaluator FAIL (1st) | Rubric miss | Recode via coding-agent | Command-prose assert + story note |
| Evaluator FAIL (2nd) | Same story, second miss | Notice; remainder is `--full-pipeline` | Command-prose assert |
| `review-override.py` pass vs evaluator FAIL | Mechanical pass | Leave FAIL standing (FAIL-only) | Existing override tests stay green |
| Gate 4 script fail on default | Coverage / authenticity | Recode via coding-agent, not testing-agent | Command-prose assert |
| Gate 0 ABORT-class on default | Script cannot judge ABORT | `unverifiable`; no third spawn | Existing arch-check unverifiable |
| `spawn-cap.py` | Command file missing | `unverifiable` `missing_command` | Fixture |
| `spawn-cap.py` | Third default Agent marker | `fail` `over_cap` | Mutated fixture |
| `eval.sh` | Helper missing | `add_finding` | bash missing-helper |

## 6. Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Default `/implement-story` | 2 spawns; scripts run; story closes | No story selected → existing selector | Story with no AC → evaluator FAIL / override unverifiable | Evaluator crash → existing Agent crash handler |
| `spawn-cap.py check` | `pass` on the real command | Missing `--command` → `unverifiable` | Command with zero Agent markers → `fail` `over_cap` or documented unverifiable | Extra default Agent line → `fail` `over_cap` |
| `--full-pipeline` | Six spawn sites still named | n/a | n/a | Does not affect spawn-cap pass |

## 7. Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| `--quick` and two-fail | No evaluator; escalation cannot fire |
| `--review-only` FAIL | No coding-agent to recode; run ends; no silent `--full-pipeline` |
| Re-run after escalation | New invocation; counter starts at 0 |
| Visual refs on default | Gate 4.5 still skipped (no visual-qa spawn) |
| Concurrent `--full-pipeline` + `--quick` | Existing flag-conflict behavior; do not invent a new resolver |

## Out of scope (this file)

Emit, counterfactual apply, agent-prompt 75% rewrite, background-await, eight-run, yuss, live `/goal`, new gate numbers, flip of `gates:` provenance.

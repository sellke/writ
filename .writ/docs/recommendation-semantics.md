# Recommendation Semantics

> **Status:** Normative. Bullets 2–5 below are the text that lived in `system-instructions.md` → Prime Directive → Recommendation Semantics until 2026-09-07, moved here under [ADR-026](../decision-records/adr-026-constraint-test-pruning.md) (every removed line is in [`pruned-instructions-ledger.md`](../decision-records/pruned-instructions-ledger.md)). The labeling rule (bullet 1) stays in the base with one pointer line to this file; it is repeated here so the section reads whole. Since 2026-11-05 ([ADR-033](../decision-records/adr-033-doubt-gated-autonomy.md)) the selection rule applies to every command, not only to `--recommend`, and the Doubt Rule in `commands/_preamble.md` decides when to ask.
> **Rule source:** [ADR-033](../decision-records/adr-033-doubt-gated-autonomy.md) (ask on doubt), which keeps [ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md)'s evidence precedence and audit fields; `commands/_preamble.md` → User Challenge and Doubt Rule carry the boundary every command runs inside.
> **Checked by:** `scripts/eval.sh` → `check_recommendation_semantics` pins the literals below in this file and the labeling rule in the base; the three adapters carry the equivalent-semantics contract.

- **Label bounded choices.** For every bounded choice, assess the options before
  presenting or acting on them. Exactly one option label ends with the literal suffix `(Recommended)`.
  If options remain explicitly equivalent after simplicity and reversibility analysis, label none and disclose the equivalence.
  The labeled option is the one acted on when the doubt check passes.
  Do not use Plan Mode when the option space is already known.
- **Use evidence, never presentation defaults.** Option order, affirmative wording, and user inactivity are never evidence.
  Evaluate only the domains relevant to the decision, in this precedence:
  governance and safety eligibility → locked artifacts → current repository or provider state → project conventions → simplicity and reversibility.
  Higher-precedence
  evidence establishes eligibility or constraints; it does not substitute for
  missing evidence in another domain. Conflicting authoritative evidence pauses the decision.
- **Select or pause transparently.** When the doubt check passes, select
  the eligible evidence-supported option. When multiple eligible choices remain
  low-risk and reversible, select the simplest viable, most reversible choice.
  Pause for safety, security, data integrity, compliance, unexpected cost, destructive or irreversible pre-production behavior, core-contract ambiguity, or subjective taste without evidence.
  Hard platform blockers remain blockers.
  A pause states the classification, missing or conflicting evidence, bounded
  choices, and a safe next action.
- **Emit concise audit rationale.** Briefly show these fields in the active
  session: Decision, Evidence, Alternatives, Risk, Reversibility, Selection source, and Result/artifact.
  Evidence must be observable; alternatives include only material options.
  Never include private chain-of-thought or transcript content.
- **Resume only the answered interaction.** After a required human answer, continue automatically in the same session and do not repeat the answered decision.
  The durable record is the decision log `jev-judge.py doubt` appends to (`.writ/state/doubt-log.jsonl`) plus each spec's `recommendation-log.md`.

## Decision record

`python3 scripts/jev-judge.py doubt --record <file>` reads one JSON object. Write it to `.writ/state/` before the call.

| Field | Type | Meaning |
|---|---|---|
| `site` | `choice`, `route`, `plan`, `direction`, `design`, `destructive`, `merge`, or `release` | What kind of decision this is. `direction` is scope, priorities, what gets built, or a contract lock. `design` is taste. `release` covers tag, publish, and deploy. Default `choice`. |
| `question` | string | The question you would otherwise ask. |
| `options` | list of strings, or `{label, description}` objects; at least two | The bounded options. A `(Recommended)` suffix is stripped. |
| `recommended` | string | The label of the option you would act on; empty when you have none. |
| `evidence` | list of strings | Observable facts behind the recommendation, highest precedence first. Empty means no evidence. |
| `reversible` | boolean, required | The act passes the reversibility precondition: git-revertable, restore path recorded first. |
| `conflict` | boolean | Authoritative evidence conflicts. Default `false`. |

```json
{"site": "plan", "question": "Run the two independent specs in which order?",
 "options": ["Roadmap order (Recommended)", "Smallest first"],
 "recommended": "Roadmap order",
 "evidence": ["spec-deps.py: no edge between them", "roadmap lists auth first"],
 "reversible": true}
```

`pass` (exit 0) means act. `fail` (exit 1) or a usage error (exit 2) means ask. The last line carries the decision's `id`; after the person answers, run `python3 scripts/jev-judge.py doubt-label --id <id> --outcome as_recommended` when they took the recommendation, or `overridden` when they did not. When a person later reverses a decision Writ acted on, label it `overridden` too.

## How the check decides

1. **Rules, no network.** `merge` and `release` always ask. Any site asks when `reversible` is false, `recommended` is empty, `conflict` is true, or `evidence` is empty.
2. **Jev, when the provider is enabled** (`jev-judge.py status` prints `pass`). One Noul asks whether the person may well want a different option. Its p is logged on every call.
3. **A calibrated threshold decides both ways.** With one (`.writ/doubt-thresholds.json`, written by `doubt-calibrate --write`), p below it acts and p at or above it asks, on every site the rules passed.
4. **Otherwise the site decides.** `direction` and `design` ask; `choice`, `route`, `plan`, and `destructive` act.

`doubt-calibrate` fits the threshold from labeled decisions and writes it only when a held-out half of them shows no override it would have acted on. On Writ's own 98 past answers it did not, so until a project's own labels show otherwise, Jev's p is logged and the site decides.

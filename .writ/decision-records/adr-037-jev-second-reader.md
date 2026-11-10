# ADR-037: Jev Is the Second Reader of the Contract and the Proof

> **Date:** 2026-11-09
> **Status:** Accepted
> **Category:** Judgment & Verification
> **Deciders:** @AdamSellke
> **Origin:** `/plan-product --reconcile` (2026-11-09). The maintainer's direction: find the most appropriate place for Jev to contribute to decision-making and to streamlining the process.
> **Supersedes:** [ADR-027](adr-027-optional-judgment-provider.md)'s sites (`spec-findings` as wired, `ac-shadow`) and [ADR-033](adr-033-doubt-gated-autonomy.md) § 2 (the `doubt` site).
> **Keeps:** ADR-027's double opt-in (a provider line in `.writ/config.md` and the provider's key in the environment), its privacy terms, and its rule that no Jev answer alone decides an outcome.
> **Evidence base:** [2026-11-09 surface audit](../research/2026-11-09-writ-1.0-surface-audit.md) § 4; TypeSafe documentation read 2026-11-09 (https://docs.typesafe.ai/introduction and the pages it links).

## Context

Jev is not a language model. It takes a state and typed questions and returns calibrated probabilities in about a tenth of a second. TypeSafe's guidance: keep control flow in code, ask narrow gut-check questions, ask many at once, combine the answers in code, and send uncertain cases to a person or a reasoning model. Its documentation says Jev is for software that needs a quick judgment over text, not for choosing an agent's next action.

Writ 0.x gave Jev three jobs:

| Job | Question | Result |
|---|---|---|
| `doubt` | Is this recommendation right, so the agent need not ask? | Never calibrated. Scores moved by up to 0.11 between identical runs. Shadowed for its whole life. |
| `ac-shadow` | Does this diff and test output satisfy this criterion? | Two stories logged against a promotion bar of thirty. |
| `spec-findings` | Is this criterion ambiguous? Do two contradict? Is a case missing? | Calibrated on 24 fixtures with no false positive on clean dev fixtures. |

The job that failed asked one broad question that needs reasoning, and put Jev in the agent's control path. The job that worked asked narrow questions about a short text.

Writ 1.0 has two documents a person decides from ([ADR-035](adr-035-people-decide-what-model-decides-how.md)): the contract they agree to before the build, and the proof they read after it. Both are short lists of statements. The person cannot review code ([ADR-034](adr-034-product-manager-audience.md)), so the quality of those two documents is what their decisions rest on.

## Decision Drivers

1. **Use Jev for what it is.** Narrow, typed judgments over short text, composed in code.
2. **Put it where a person decides,** since that is where a second opinion is worth the most and a person's attention is the expensive step.
3. **A different kind of reader.** The author of both documents is a language model. A calibrated model that generates nothing fails differently.
4. **A wrong answer must be cheap.** Jev may point; it may not act.
5. **Optional, and invisible when off.**

## Considered Options

### Option A: Remove Jev

- **Pros:** No code ships at all. No external call.
- **Cons:** Gives up the one use that calibrated, and an independent check on the two documents everything else depends on.

### Option B: Keep Jev deciding when to ask the person

- **Pros:** The original ambition.
- **Cons:** It did not calibrate, the question is the kind TypeSafe says to decompose, and the answer is now a rule that needs no model.

### Option C: Front-door routing, or scoring the backlog against the objective

- **Pros:** Both fit Jev's shape (choose one of a set; score many items on fixed dimensions).
- **Cons:** With ten skills the model routes without help. Backlog scoring is promising for a product manager and unproven; it is recorded as a candidate, not built.

### Option D: Second reader of the contract and the proof (chosen)

## Decision

Jev reads the two documents and flags lines for a second look. It never decides whether to ask a person, never routes, and never acts.

**Before the person agrees a contract** (`writ-spec`), `jev.py contract` asks, per acceptance criterion, whether two readers could build opposite things and both satisfy it, and whether it asks for something the Out list excludes; and, for the contract as a whole, whether two criteria contradict, whether an input has a criterion for its valid case and none for its missing or invalid case, and whether the Outcome names a measure. The model fixes obvious wording and puts the rest in front of the person as questions.

**Before the person reads a proof** (`writ-verify`), `jev.py proof` asks, per `Proved` row, whether the evidence shows that criterion holding and whether it reports a result and not a claim; and, per `Needs a person` row, whether a check could have decided it. The verifier looks again at each flagged row and either gathers better evidence or changes the verdict.

**How it is built**

- One script, `plugins/writ/skills/writ-jev/jev.py`: standard-library Python, the 0.x client and its double opt-in carried over, the question wording fixed in code so answers are comparable from run to run.
- Thresholds live beside it in `thresholds.json`, fitted on a labelled fixture set, with a weaker `check` band between the two cut-offs.
- The check is advisory. It prints `flag`, `pass`, or `off`, and exits 0 in all three cases. A missing key, a failed request, or an unreadable file is `off`, and the skill carries on.
- What is sent: the contract's text, and for a proof the evidence lines and any text files they cite, with files that look like secrets skipped. Nothing is sent unless both opt-ins are present.

**What this replaces.** The 0.x supervisor agent re-derived a report at a cost of about 141,000 tokens and nine minutes. A proof check is one request.

## Consequences

**Positive**

- Jev does the kind of job that calibrated before, at the two points where a person decides.
- A wrong flag costs one re-read. A missed flag leaves things as they would be without Jev.
- `jev-judge.py` (2,570 lines, 5,491 of tests) becomes one small script.

**Negative**

- One script ships after all, and with it a Python 3.9 floor and a test file.
- Jev sees contract and evidence text. Projects that cannot send that outside leave it off.
- The fixture set is authored, not drawn from real contracts. Thresholds will need refitting on real ones.
- Evidence that is an image is not read yet.

**Review triggers**

- Flags on clean documents become common enough that people ignore them: refit, or drop the question.
- A real contract or proof defect that Jev's questions should have caught goes unflagged: add it to the fixtures and refit.
- Fifty real contracts and proofs have been read: refit every threshold on them and record the result here.
- A product manager asks for help ordering the backlog against the objective: build the scoring candidate from Option C behind the same opt-in.

## Calibration record

See `plugins/writ/skills/writ-jev/thresholds.json` for the fitted values and the fixture counts behind them.

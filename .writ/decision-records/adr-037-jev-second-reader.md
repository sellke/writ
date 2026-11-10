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

**2026-11-09, authored fixtures.** Fitted values and counts are in `plugins/writ/skills/writ-jev/thresholds.json`; the fixtures and recorded responses are under `scripts/tests/fixtures/jev/`.

- 20 contracts and 12 proofs, half for fitting and half held out, through the Vercel AI Gateway (`typesafe-ai/jev`; the gateway does not say which Jev version it serves).
- On both halves every seeded defect was flagged and no clean document was flagged. All five held-out clean documents stayed free of flags; three of the five were fully quiet, and two drew a weaker `check` line.
- These scores overstate it. One author wrote the fixtures and the questions, and the seeded defects are blatant.
- `gap` is fragile: clean contracts scored up to 0.85 against real gaps at 0.96 to 0.98, so its cut-off sits at 0.90.
- Run to run, 684 answers scored twice: the largest move was 0.18, four moved more than 0.10, and two crossed a flag cut-off. No document's first line changed.
- A contract is about 4,200 input tokens and a proof about 2,600; each comes back in 0.3 to 0.5 seconds.
- The direct TypeSafe backend was not exercised (no key on the machine).

**2026-11-09, first real documents.** The contract and proof from the first end-to-end run on a sample app, which nobody wrote for calibration:

- Contract, 11 criteria: one flag ("the page itself behaves as before") and one `check` ("display correctly in Excel and Google Sheets"). Both are lines a careful reader would question. Two runs agreed.
- Proof, 10 rows: five flags and two `check` lines. Three flags landed on rows where the verifier's own text said part of the criterion was not observed, including one it had marked "Proved (parsing only)". Two landed on rows with terse evidence; the proof named its evidence files without the `proof/` path, so no file was read. `writ-verify` now asks for the path.
- Half the rows flagged is more than a clean proof should draw, and on this proof most of the flags were right. One document settles nothing; the fifty-document refit stands.
- **A defect found and fixed on this run:** with no `--repo`, the script read the opt-in from the current directory when the spec's own project had no config, so a project that had not opted in had its contract sent. The opt-in is now read only from the project that owns the spec, with a test for it.

**2026-11-10, a second real proof.** The proof a Cursor helper wrote for the same sample contract, 11 rows:

- Two flags and two `check` lines. One flag, `unproven` at 0.91, landed on the one row the helper had marked proved on half its evidence: the criterion says the file holds a leading `'` and the spreadsheet shows text, and only the file was checked. The helper's own "Not covered" list left that row out, so with the second reader off nothing would have pointed at it.
- The other flag, `could_be_checked` at 0.62, landed on a row correctly left to a person (how a title with a comma shows in a spreadsheet). That one is a wrong flag.
- Two real proofs are still not a fit. The fifty-document refit stands.

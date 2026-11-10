---
name: writ-jev
description: Optional second reader for Writ, backed by TypeSafe's Jev. Flags unclear, contradictory, or incomplete acceptance criteria before a contract is agreed, and proof lines whose evidence does not show what they claim. Used by writ-spec and writ-verify; run directly to turn it on or off or to check its status. Part of Writ.
---

# Writ Jev

Read `../writ/rules.md` first.

Jev is a small model that answers narrow yes-or-no questions about a text and says how sure it is. Writ uses it as a second reader of the two documents a person decides from: the contract and the proof. It points at lines worth a second look. It decides nothing, and Writ works the same without it.

The script is `jev.py` in this folder. Run it with `python3` and its full path.

## Turning it on or off

It runs only when both of these are true:

1. `.writ/config.md` names a provider. `python3 jev.py setup typesafe` or `python3 jev.py setup vercel-gateway` writes the line; `python3 jev.py setup none` turns it off.
2. The provider's API key is set in the environment: `TYPESAFE_API_KEY` for TypeSafe, `AI_GATEWAY_API_KEY` for the Vercel AI Gateway. The person sets it themselves, in their shell. Never ask for a key in the conversation and never write one to a file.

`python3 jev.py status` prints `ready` or `off` and the reason.

Turning it on is the person's call, because it sends text outside the project. Before they decide, tell them what goes: the text of the contract, and for a proof the evidence lines and any text files they cite. Files that look like secrets are skipped.

## Reading a contract

```
python3 jev.py contract <path to spec.md>
```

It asks, for each acceptance criterion, whether two readers could build opposite things and both satisfy it, and whether it asks for something the Out list rules out. For the contract as a whole it asks whether two criteria contradict each other, whether some input has a criterion for the good case and none for the missing or wrong case, and whether the Outcome names a measure.

## Reading a proof

```
python3 jev.py proof <path to spec.md>
```

For each line marked Proved it asks whether the evidence shows that criterion holding, and whether it reports a result and not a claim. For each line marked Needs a person it asks whether a check could have decided it. A criterion with no proof line at all is reported without asking the model.

## What comes back

The first line is one of:

- `pass`: nothing flagged.
- `flag`: one line follows per concern, naming the criterion, the concern, and a reason.
- `off`: not set up, the request failed, or the file could not be read. A `reason:` line says which. Carry on without it.

Lines that begin with `check` are weaker: the answer sat between yes and no. Look if it is cheap to look.

## What to do with a flag

A flag is a reason to read the line again, not a verdict.

- **On a contract:** if the fix is obvious, reword the criterion. If it is not, put it to the person as a question before they agree.
- **On a proof:** look at the evidence again. Gather better evidence, or change the verdict.
- **If you look again and the line is right,** leave it and move on.

When you pass a concern on to the person, say what the concern is in plain words. Leave out the probability and the name of the check.

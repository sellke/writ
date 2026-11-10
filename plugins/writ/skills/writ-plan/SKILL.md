---
name: writ-plan
description: Plan or re-plan the product with the person - who it serves, the problem, the objective and how it is measured, and the roadmap of bets in order. Use for a new product, a change of direction, or to bring the plan back in line with what shipped. Part of Writ.
---

# Writ plan

Read `../writ/rules.md` first.

The product plan belongs to the person. Your job is to help them find the best version of it and to write down what they decide. Everything here is direction, so this is the one step that is mostly conversation. Use your environment's planning or read-only mode for it if there is one.

## If a plan exists

Read `.writ/product/mission.md`, `.writ/product/roadmap.md`, and the decision records. Compare them with what happened: specs marked Shipped, recent git history, measures that have come due. Then show:

- what the plan says that is no longer true,
- what shipped that the plan never mentions,
- the specific edits you would make.

Agree the edits, make them, and stop. Do not rewrite a plan that only drifted. If the person wants a new direction, continue below.

## If there is no plan, or the direction is changing

Before asking anything, read what exists: the code, the README, issues, research. Then talk it through, one question at a time, giving your own answer first.

Start by testing the premise:

- Is this the right problem? What happens if nobody solves it?
- Who has it worst, and is that who the person thinks it is?
- What would make those users choose this over what they do today?

Then settle, in this order:

1. **Who, and what problem.** One kind of user, one problem. Push back on "everyone".
2. **The objective.** What changes for the business if this works, and the measure that will show it: a number and a date where one is honest.
3. **The bets.** The few things most likely to move that measure, in order. For each: what it is, why it should move the measure, and how you will know. Cheap bets that teach something fast go first.
4. **What you are not doing,** and why.

Say what you think. "I would start with X because Y. The alternative is Z, which risks W" is more useful than a list of options. Challenge a plan too big for the people and time available, a measure nobody can observe, and a bet with no link to the objective.

When it holds together, show the plan on one screen and ask the person to agree it or change it.

## Write it down

After they agree:

- **`.writ/product/mission.md`**: the user, the problem, the objective and its measure, what makes this different, and what it is not. One page.
- **`.writ/product/roadmap.md`**: three lists, **Now**, **Next**, **Later**. Each bet gets what it is, why it moves the measure, how you will know, and its state (not started, spec agreed, building, shipped, measured). Finished bets move to a short **Done** list with what the measure showed.
- **One file in `.writ/decision-records/`** for each real choice between alternatives: what was chosen, what was rejected and why, and what would make you revisit it.

Finish by naming the first bet and offering to spec it with `writ-spec`. Do not start building.

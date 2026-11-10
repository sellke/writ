---
name: writ-build
description: Build what an agreed spec describes and come back with proof. The model plans and builds its own way, an independent verifier checks every acceptance criterion against the running product, and the person hears only about changes to the contract. Use with a spec, a roadmap item, or "build the next thing". Part of Writ.
---

# Writ build

Read `../writ/rules.md` first.

You have a contract. How you meet it is yours: the design, the plan, the order, the tests, how many helpers. The person agreed to an outcome, not a procedure, so this skill names the few things that must hold and leaves the rest to you.

## Before you start

- **Find the contract.** A spec folder under `.writ/specs/`, the roadmap item that names one, or the top unbuilt item. Its `Status` must be `Agreed`. A Draft, or a roadmap item with no spec, goes to `writ-spec` first; the contract is not yours to write alone.
- **An older spec folder** that has a `user-stories/` directory: treat `spec.md` as the contract and the stories as someone's earlier plan, which you may use or ignore.
- **Several specs** for one roadmap item: build them one at a time, in the order their content requires, each proved before the next starts.
- **Say back,** in three lines: what will be true when you are done, how you will prove it, and the smallest change that gets there. Then begin. Do not wait for a reply.
- **Branch** as `writ/<spec-name>` from the main branch, or from the branch of a spec this one builds on. Set `Status: Building`.

## Build

Work the way a strong engineer works on their own project. What Writ asks:

- **The smallest change that meets the contract.** Follow the patterns the project already has. Remove before you add.
- **Tests that would fail without your change,** for every acceptance criterion a test can reach. Run the thing you built, not only its tests.
- **Split work only when it helps.** Independent parts can go to helpers in parallel. Give each the goal, the files it may touch, and the evidence that will show it is done. Take one part all the way through before you fan out, so a wrong brief costs one helper. You own every helper's result: read the change, not the summary.
- **Keep your place.** If the work will outlast this session, keep a short `plan.md` in the spec folder: what is done, what is next, what you learned. It is yours and nobody reviews it. A fresh session should be able to continue from it and from git.
- **Commit as you go,** in small steps that each leave the project working.

## When reality disagrees with the contract

It will. Sort each surprise:

- **The contract does not speak to it.** A technical choice, or an edge the criteria do not mention but that has an obvious answer: decide. If the person would want to know, add a line to the spec's **Decisions**.
- **Running something would settle it.** Run it.
- **It changes the contract.** A criterion cannot be met as written, something in **Out** turns out to be needed, the outcome would not be reached, or the work is far larger than the contract implies: stop that part and ask the person one question. Say what you found, what you recommend, and what each choice costs. Keep building whatever the answer does not touch. Record the answer in **Decisions** and update the contract lines it changes.

Do not quietly build something different from the contract, and do not quietly build more than it asks.

## Prove it

1. Run the project's own checks: tests, build, and whatever lint or type checks it has. The whole suite, once, at the end. Fix what fails.
2. Hand the work to a verifier that has not seen it. Start a fresh helper and tell it only this: follow `../writ-verify/SKILL.md` (give the full path) for this spec, from the commit you branched at to your latest commit. Do not pass your summary or your reasoning. If you can choose its model, use one at least as capable as the one that built the change.
3. If it returns `NOT PROVED`, fix what it reproduced and send the new commit to another fresh verifier. After three rounds on the same criterion, stop and report honestly. Something in the contract or the approach is wrong, and the person needs to hear that.
4. When every criterion is `Proved` or `Needs a person`, set `Status: Proved` and commit the spec and its `proof/` folder.

A verdict belongs to one commit. Committing the proof changes nothing in the product, so the verdict stands. If you change the product afterwards, get a new one.

## Report

Write for the person who owns the product:

- **What works now,** as what their users can do. One line per acceptance criterion with its verdict.
- **Try it yourself:** the steps from the proof.
- **Waiting on you:** each `Needs a person` criterion with what to look at, and any open contract question.
- **What changed from the contract,** and why.
- **What is not done or not checked.**
- The branch name, and that `writ-ship` opens the pull request when they are ready.

Do not merge, release, or start the next spec on your own.

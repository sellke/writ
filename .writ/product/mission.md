# Writ: Product Mission

> Last agreed: 2026-11-09, by Adam Sellke ([ADR-034](../decision-records/adr-034-product-manager-audience.md) to [ADR-037](../decision-records/adr-037-jev-second-reader.md))
> Earlier missions and every phase from 1 to 17 are in [roadmap-history.md](roadmap-history.md).

## Who it is for

A semi-technical product manager. They know the user, the business objective, and what good looks like. They can run a product locally and read a summary of a change. They do not review code, and they should not have to learn how software gets built to get software built.

## The problem

AI coding agents can now build most of what a product needs. That moved the hard part. It is no longer writing the code. It is deciding what to build, saying it clearly enough to be built, and knowing whether what came back is what was asked for.

A product manager working with an agent today hits three walls:

1. **The agent asks the wrong person the wrong questions.** Which library, retry or skip, how to split the work. They cannot judge the answers, and every question pulls them out of their own work.
2. **Intent lives in chat.** What was agreed, what was left out, and why, scroll away. The agent builds something adjacent, and nobody can point at the line it broke.
3. **"Done" is the agent's own word.** They cannot read the diff, so they either trust the report or find an engineer.

## What Writ does

Writ gives the person and the agent a short, shared way of working:

- **People decide what and why. The model decides how.** The person is asked about direction, the contract, taste, and acts that cannot be taken back. Everything else the model decides and reports.
- **A contract before a build.** One file says the problem, the outcome and its measure, what is in and out, and how anyone could tell it is done. The person agrees it. Any later change to it goes through them.
- **Proof instead of a report.** A verifier that did not write the change checks every line of the contract against the running product and writes down what it ran and what it saw, with steps the person can try themselves.
- **Plain files in git.** The plan, the contracts, the decisions, and the proofs outlast any one session, model, or tool.

It ships as ten plain-language skills named `writ` and `writ-*`, and works in Claude Code, Cursor, and Codex.

## Objective and measure

**Objective:** a product manager takes a business problem to a shipped, proved change without an engineer translating in either direction.

**Measures** (agreed 2026-11-09):

1. One product manager who did not build Writ completes problem → contract → build → proof → shipped change, unaided, on a real product. Look: when the first outside trial ends.
2. Across the first ten builds, the person is asked nothing about method. Count questions by kind from the session history.
3. No change that the verifier marked proved fails in users' hands in the first ten builds.

## What makes it different

- **Against using an agent bare:** the contract and the proof. The agent alone has neither.
- **Against rigor skill packs such as pstack:** they make each agent a better engineer and keep no record of what was agreed. Writ keeps the agreement and checks the result against it. They can run together.
- **Against spec-first frameworks for developers:** Writ's contract is written for the person who owns the outcome, and Writ does not prescribe the build.

## What it is not

- **Not a build procedure.** No gates, stories, or pipelines. The model plans its own work.
- **Not an unattended loop.** Work starts when a person asks, is bounded by a contract, and stops for their word before merge and release.
- **Not a memory system, a browser, or a runtime.** Writ uses what the platform provides.
- **Not a style pack.** It carries a way of working, not one author's taste.
- **Not hosted.** Files and git. The one optional outside call is Jev, as a second reader of the contract and the proof, off unless switched on.

## Principles

1. People decide what and why; the model decides how.
2. Nothing is done until someone other than its author has proved it.
3. Say it in the person's words.
4. Subtract before you add. A check comes back only when a recorded miss calls for it.
5. One source, no copies.
6. Lead with the recommendation, and say no when no is the answer.
7. Use Writ to build Writ.

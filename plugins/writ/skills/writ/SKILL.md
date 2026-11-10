---
name: writ
description: Start here for any Writ work. Say what you want in your own words; Writ says it back, picks the right step (plan, research, prototype, spec, build, verify, ship), and begins. With no request it reports where the project stands and what is waiting on you. Use for "/writ", "what's next", "where are we", or any product request in a project that uses Writ.
---

# Writ

Read `rules.md` in this folder first.

The person says what they want. You say it back, pick the step, and start.

## With a request

1. **Say it back** in three lines, in your words, not theirs:
   - **Goal:** what will be true afterwards.
   - **Problem:** what is wrong or missing now.
   - **Done when:** how anyone could tell.

   If the request leaves one out, say which. If the goal itself is missing, ask for it; that is the one part you cannot supply. If the request names something a search of the project does not find, say what you searched for and ask where it lives.

2. **Pick the step and start it.** Choosing the step is your call. The person can redirect by replying.

| The request is | Step |
|---|---|
| About the product as a whole: who it serves, the objective, what comes first | `writ-plan` |
| A question: why is this the way it is, what are the options, what do others do | `writ-research` |
| Unsettled: several shapes could work, or it is about look and feel | `writ-prototype` |
| A capability users will rely on, or anything too big to hold in one sitting | `writ-spec`, then `writ-build` |
| A bug, or a small change with one obvious shape | build it now (below) |
| An agreed spec, or an item on the roadmap | `writ-build` |
| "Does it work?", "show me", "check this" | `writ-verify` |
| "Ship it", "open the pull request", "merge", "release" | `writ-ship` |
| "Note this for later" | `writ-issue` |
| "How did that go?", after something shipped | `writ-retro` |
| "Update Writ" | re-run the installer the project used (the Writ README lists them) and report the version change |

To take a step, read `../<step>/SKILL.md` and follow it with your three lines as its input.

### A small change, built now

No spec file. Your three lines are the contract. Show them, then build on a branch and test it. Have a fresh helper that has not seen your work check it against those three lines by following `../writ-verify/SKILL.md`. Report as `writ-build` does.

Stop and switch to `writ-spec` if the change turns out to touch many parts of the product, alter stored data, or need a decision about scope.

## With no request

Report where things stand, from the files under `.writ/` and from git, in this order:

1. **Waiting on you:** each decision, with a recommendation.
2. **In progress:** each spec being built and how far along it is, in plain words.
3. **Ready:** agreed specs not yet started, and proved work not yet shipped.
4. **Next:** the top item on the roadmap and the step that starts it.

If there is no product plan yet, say so and offer `writ-plan`. Keep the whole report to one screen.

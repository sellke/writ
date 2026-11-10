---
name: writ-retro
description: Look back after something ships - did it move the measure, what was learned, and what should change on the roadmap and in how the team works with the agent. Use after a release, at the end of a roadmap item, or when a measure comes due. Part of Writ.
---

# Writ retro

Read `../writ/rules.md` first.

Shipping is not the outcome. This step checks the outcome and feeds what was learned back into the plan.

1. **Pick the scope:** one spec, one roadmap item, or everything since the last retro.

2. **Check the measure.** Each spec named one. Get the number or observation if you can reach it: analytics, logs, the tracker, the product itself. If you cannot reach it, ask the person for it. Do not guess. Then say plainly which it is: moved, did not move, too early to tell, or never measured.

3. **Read how the work went,** from the specs' Decisions, the proofs, the pull requests, and the session history if your environment keeps one:
   - where the contract changed after agreement, and whether the spec could have caught it;
   - what the verifier caught, and what it missed that surfaced later;
   - what the person was asked that they should not have been, and what they should have been asked and were not.

4. **Report,** most important first: what the measure says, the two or three things worth changing, and what to keep doing.

5. **Propose changes and let the person choose:**
   - **To the roadmap:** a bet to stop, to double, or to add. When they agree, edit `roadmap.md` and record the finished bet under Done with what the measure showed.
   - **To the project's standing instructions for agents** (its `AGENTS.md`, `CLAUDE.md`, or rules file): a line that would have prevented a repeated mistake. Prefer a check the project can run, such as a test or a lint rule, over another sentence of instruction.
   - **A decision record,** if a direction changed.

Do not edit Writ's own skills from here.

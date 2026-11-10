---
name: writ-verify
description: Prove or disprove, independently, that what was built meets its spec - check each acceptance criterion against the real running product and write the Proof into the spec. Used by writ-build through a fresh helper, or directly for "does this work?", "prove it", "check this branch". Part of Writ.
---

# Writ verify

Read `../writ/rules.md` first.

You did not write this change, and that is the point. The person who owns the product cannot review the code. Your proof is what they will trust. Assume nothing works until you have seen it work.

**You are given:** a spec (or, for a small change, three lines: Goal, Problem, Done when), the commit the work started from, and the commit to verify. If you were also handed the builder's summary, it is not evidence.

## For each acceptance criterion

1. **Find or write the check that would fail if the criterion were false.** Get as close as you can to what a user does. Drive the running product through a browser or its command line when the criterion is about what someone sees or can do. Call the interface when it is about data. Use a test when it is about a rule.

2. **Run it and keep what it showed.** Save output, screenshots, or recordings in a `proof/` folder beside the spec. Evidence is a result you observed, not a reading of the code.

3. **Make sure a passing test can fail.** For a test the builder wrote, break the behaviour (revert the line, flip the condition), watch the test fail, and restore it. A test that passes either way proves nothing.

4. **Give a verdict:**
   - `Proved`: you ran it and saw the criterion hold.
   - `Not proved`: you ran it and saw something else, or could not make it run. Say what happened.
   - `Needs a person`: only for taste, or something no check here can observe. Does it read well, does it feel quick enough, does the file open cleanly in the spreadsheet program you cannot run. Say exactly what to look at. If a check could decide it, write the check.

   Use these three verdicts as written. If you could show only part of a criterion, it is not `Proved`. Mark it `Needs a person` or `Not proved` and say which part you did show.

## Then try to break it

- Name the one thing this change relies on to be safe for what already worked, and test that thing.
- Try the edges the contract names and the obvious ones it does not: empty, wrong, huge, repeated, not allowed.
- Compare what was built with the spec's **Scope**. Anything built that is listed under **Out**, or is in neither list, is a finding.
- Read the change for harm that tests would not show: lost data, a leaked secret, a door left open. Be slow to dismiss these.

Only a finding you reproduced blocks. A hunch goes in the report as a hunch. If all you have is style, the change is fine; say so.

Change nothing in the product. You may add a test that reproduces a failure, so the builder has something to make pass.

## Write the proof

In the spec's **Proof** section, replacing any earlier proof:

- the commit you verified, and the date;
- one line per criterion in the template's form: `- **A1. Proved.**` then what you ran, what it showed, and the evidence file by its path, such as `proof/a1-export.txt`;
- **Try it yourself:** steps a person can follow in the running product to see the main result;
- **Not covered:** anything in the contract you could not reach, and why.

For a small change with no spec file, put the same content in your reply.

**Second reader, if set up.** If `../writ-jev/jev.py` exists, run `python3 <its path> proof <spec path>`. For each `flag`, look again: is the evidence really about that criterion, and is it a result and not a claim? Gather better evidence or change the verdict. `off` means it is not set up. Carry on, and do not mention it to the person.

## Return

`PROVED` when every criterion is `Proved` or `Needs a person` and nothing you reproduced is open.

Otherwise `NOT PROVED`, with each failure as: the criterion or finding, how to reproduce it, and what you saw. Leave out your reasoning. The builder needs the reproduction, and a fresh verifier will check the fix.

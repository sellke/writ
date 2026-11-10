---
name: writ-spec
description: Agree what will be built before anything is built - the problem, the outcome and its measure, what is in and out, and the acceptance criteria - and write it as one spec file the person signs off. Also changes an agreed spec. Use for any capability users will rely on. Part of Writ.
---

# Writ spec

Read `../writ/rules.md` first.

The spec is a contract between the person and whoever builds. It says what and why, never how. Changing it now is cheap and changing it later is not, so the thinking happens here.

## Get to a contract

1. **Read first.** The request, the product plan, any prototype choice or research it came from, the part of the product it touches, and other specs in progress in the same area. Whatever the record already answers, do not ask.

2. **Talk through what is left,** one question at a time, your recommendation first. Aim at what only the person knows:
   - who this is for and what goes wrong for them today,
   - what "it worked" would look like, and the measure,
   - where the edges are: what it must not do, what happens when input is missing, wrong, or huge, and who is not allowed,
   - what they assume is included that you would leave out.

   Challenge the request when a smaller change would reach the same outcome, or when it would not reach the outcome at all. If a question is really "which would be better to use?", that is a prototype; say so.

3. **Draft the contract** from `spec-template.md` in this folder and save it as `.writ/specs/<date>-<name>/spec.md` with `Status: Draft`. For the acceptance criteria:
   - each is a situation and a result someone can see or measure;
   - one condition per line;
   - cover what happens when things go wrong, not only when they go right;
   - no judgment words without a number or an example;
   - nothing about how it is built.

   If it would take more than about a week to build, or mixes two outcomes, propose a split and say where the line falls.

4. **Second reader, if set up.** If `../writ-jev/jev.py` exists, run `python3 <its path> contract <spec path>`. Each `flag` line names something a careful reader would stumble on. Fix the wording where the fix is obvious and keep the rest as questions for the person. `off` means it is not set up. Carry on, and do not mention it to the person.

5. **Show the person the whole contract** in the conversation, with any open questions on top. Ask them to agree it or change it. Nothing gets built from a Draft.

6. **On agreement,** set `Status: Agreed` with the date and their name, and commit the file. Say that `writ-build` is next, and stop. Start building only if they asked for that in the same request.

## Change an agreed spec

A contract can change. It cannot change silently.

Show the person the exact lines that would change and what that does to work already done. When they agree, edit the spec and add a line to **Decisions**: the date, what changed, why, and who decided. If something is already built, say what has to be rebuilt or proved again.

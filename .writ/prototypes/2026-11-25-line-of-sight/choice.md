# Line of sight: how Writ names and groups the helpers it starts

> Chosen: 2026-11-25, by Adam Sellke

## The fork

How should Writ name and group the helpers and sessions it starts, so the person can see what is running for each piece of work and what each one is doing?

The evidence for a problem: the person's own session list. Titles were improvised. One piece of work was spread across sessions named "Spec: …", "Build: …", and a bare topic, and nothing in their names tied them together. The skills said nothing about naming.

## The drafts

- **A. Name it where you already look.** One rule in `rules.md`: label every helper `<name> · <job>` with the work's name, and title or tag the current session the same way where the environment allows. Claude Code's own panels and sidebar do the rest.
- **B. A crew list in the records.** A `crew.md` in each spec or prototype folder, one row per helper with its label, job, state, and outcome, shown by `/writ`.
- **C. One session per job.** The session where the work starts is its hub. The build, each verifier round, and each draft run as their own sessions grouped under it.

## Won: A

Claude Code already shows what is running, live. What it could not show was which things belong together, and a shared name fixes that with one rule. It also lets a later session find earlier ones by title: from inside a cloud session the agent can list the person's sessions with titles and status, but cannot filter them by tag.

Tightened before it shipped: the name is the record's name under `.writ/` without the date, so the model uses the same name every time.

## Why the others lost

- **B** repeated what the live panes already show, but only as current as the model's last write. It left session titles as they were. Its outcome column would put the builder's notes in the spec folder, where a fresh verifier is likely to read them (a risk, not tested). It added a record type and a file write per helper with no recorded mistake behind it.
- **C** gave the richest view, but in the desktop app a session a skill starts waits as a card for the person to click, so every fix-and-verify round would wait on them. It left about five sessions per spec in the sidebar, each starting cold. A cloud verifier session also needs the build pushed before it can see it. Worth another look if A is not enough after a few real builds.

## What Claude Code allows, as of 2026-11-25

- A helper shows as its type plus a short label in the transcript and the background tasks pane. A finished helper leaves the CLI's task list after about 30 seconds. (Claude Code docs.)
- The person can rename a session with `/rename` or from the desktop title bar. The docs do not cover the agent renaming its own session. In a cloud session the agent can set its own title and tags. (Docs; this session's tools.)
- Agent teams, with named teammates and a shared task list, are experimental and off by default. (Docs.)

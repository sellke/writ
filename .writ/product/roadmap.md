# Writ: Roadmap

> Last agreed: 2026-11-09, by Adam Sellke
> Objective and measures: [mission.md](mission.md)
> Everything before 1.0, Phases 1 to 17 and versions 0.5 to 0.49, is in [roadmap-history.md](roadmap-history.md).

Each bet says what it is, why it should move a measure, how we will know, and its state.

## Now

### 2. The first outside product manager

- **What:** One product manager who did not build Writ takes a real problem to a shipped change with it.
- **Why:** Measure 1. The audience is a bet until this happens.
- **How we will know:** They finish without a developer translating. Every place they were stuck, asked about method, or misread a report is written down and fixed.
- **State:** not started. 1.0.0 was released on 2026-11-10. Two things seen in the 1.0 runs to watch with this person:
  - Three proofs marked a criterion proved when only part of it was shown. Each time the criterion mixed something a run can check with something only a person can see. `writ-spec` now asks for those as two lines. Whether that is enough is not known.
  - In the ChatGPT desktop app at its low effort setting, `writ-spec` skipped the opening question and went straight to a draft. One sample.

## Next

### 3. One-step install on every target

- **What:** List the plugin in Cursor's marketplace and the plugin directory that ChatGPT and Codex share.
- **Why:** A product manager should not run a shell script to begin.
- **How we will know:** Install is a single action in each tool, and `install.sh` drops that target.
- **State:** not started. The Claude Code marketplace file already works from this repository.

### 4. Refit Jev on real documents

- **What:** After fifty real contracts and proofs have been read, refit every threshold on them.
- **Why:** Measure 3. The first thresholds come from authored fixtures.
- **How we will know:** Flags on clean documents are rare enough that people act on a flag, and the fitted numbers are recorded in ADR-037.
- **State:** not started.

## Later

Candidates, not commitments.

- **Order the backlog against the objective.** Jev scores each issue or bet on a few fixed dimensions; the person sets the weights. Build it when a product manager asks.
- **Measures that come due.** Remind the person when a shipped spec's measure should be looked at, and start `writ-retro`.
- **Image evidence.** Let the second reader look at screenshots in a proof.
- **A second person on a project.** Shared contracts, review of a spec before agreement. Waits for a real second person ([ADR-007](../decision-records/adr-007-team-audience-sequencing.md)).
- **The same contract-and-proof loop for work that is not software.** Waits for a concrete first process.

## Done

- **1. Writ 1.0: the minimal core (v1.0.0, 2026-11-10).** Ten plain-language skills, one rule for who decides, one independent verifier, a one-file spec, Jev as an optional second reader, and one installer. The 0.x commands, agents, adapters, generated trees, and scripts are removed. Built by direct edits at the maintainer's direction, not through 0.x's own pipeline, and merged as [pull request 78](https://github.com/sellke/writ/pull/78). Decisions: [ADR-034](../decision-records/adr-034-product-manager-audience.md) to [ADR-037](../decision-records/adr-037-jev-second-reader.md). Evidence: [surface audit](../research/2026-11-09-writ-1.0-surface-audit.md). What was checked before release:
  - The repository: `check.py`, pytest on 3.9 and 3.14, and the bash tests pass, locally and on GitHub.
  - Claude Code: a sample change went contract → build → independent proof, headless, on a mid-tier model. The plugin folder loads into a fresh session and registers all eleven skills as `writ:writ`, `writ:writ-build`, and so on.
  - Codex CLI: the skills are discovered from `.agents/skills`; `writ-spec` asks one question with a recommendation; `writ-build` on an agreed spec built the change, started a helper that drove the running app, and wrote the proof with the three verdicts used as written. Its sandbox keeps `.git` read-only, so that run could not branch or commit. The plugin installs from this repository's marketplace file and shows all eleven skills in an empty project.
  - Cursor, through its agent command line on its default model: the skills are found in `.agents/skills`; `writ-spec` asked one question with a recommendation; `writ-build` built an agreed spec and committed it, and a fresh helper proved it against the running app, in 5.8 minutes. The helper marked one criterion proved on half its evidence. The plugin folder loads into an empty project with all eleven skills. A first run was thrown out: the sample project carried an earlier build of the same spec on its remote, and the builder reused it. The editor window was not opened.
  - ChatGPT desktop app, run by the maintainer at the app's low effort setting: `writ-build` built the agreed spec, branched and committed, and a fresh helper clicked the link in Chrome, read the downloaded file, and left the three spreadsheet criteria to a person. `writ-spec` skipped the opening question, saved a draft, and asked for agreement. The plugin was not loaded inside the app.
  - The installer: the published install line was run from GitHub in clean projects (install, run again, update around a changed file, uninstall). A project with a 0.x install is stopped with the command that removes it.
  - Jev: fitted on authored fixtures and run on two real proofs ([ADR-037](../decision-records/adr-037-jev-second-reader.md)).
  - Not checked: Windows, the Cursor editor window, and either plugin installed from a marketplace listing.
- **Phases 1 to 17 (v0.5 to v0.49.0, February to November 2026).** The contract-first spec, the gated pipeline and its scripts, phase orchestration, the knowledge ledger, the front door, plugin distribution, doubt-gated autonomy, and verified landing. What 1.0 kept from all of it: the contract, the independent reviewer that runs things, the pause when a build departs from the contract, the check that a test can fail, and plain files in git. Full record: [roadmap-history.md](roadmap-history.md).

## Closed without finishing, at 1.0

These were open on 2026-11-09. Each is closed because 1.0 removes what it was about.

| Was open | Closed because |
|---|---|
| Phase 12: one real-project `app-verify.py` run; a Gate 4.5 fail that asked the user | The script and the gate are gone. `writ-verify` drives the running product itself. |
| Phase 14: five person checks; keep-or-remove review of `/writ` | `/writ` stays, rewritten. It no longer confirms a route. Usage data said work started from direct commands; with ten skills and a product-manager audience the front door is kept and is re-judged under bet 2. |
| Phase 16: a merge the doubt check passes on its own | Merge is the person's word ([ADR-035](../decision-records/adr-035-people-decide-what-model-decides-how.md)). |
| Phase 17: a Jev threshold for `doubt`; a script that finds decisions made without a doubt call; ask counts | The doubt check is replaced by one rule. Jev has a different job ([ADR-037](../decision-records/adr-037-jev-second-reader.md)). Ask counts carry on as measure 2. |
| ADR-023 review, due 2026-11-11 | Answered by ADR-035: diligence follows stakes, by the model's judgment, with the verifier as the check. |

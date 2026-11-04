# Phase 14 Acceptance Report

> **Date:** 2026-10-24
> **Branch:** `phase/14-front-door-and-distribution`, base `9e7eab5`, candidate tag `v0.44.0-rc.1` cut in a temp clone at `1f83680`
> **Platforms:** Claude Code 2.1.310, codex-cli 0.163.0. Cursor has no CLI on this machine.
> **Updated:** 2026-10-24, after the follow-up fixes; see After the pass.
> **Method:** coverage audit first, clean-room installs, behavior probes with controls, three runs per probe, blind grading against rubrics committed before the runs (`d79a86c`, `bc9a6b2`).

## Verdict

The pass found nine defects and fixed six. Follow-up work fixed the other three (D2, D8, D9) plus two found along the way, and the merged branch passed the gate and the re-checks. The routing bar was missed, and five checks still need a person before release.

- **Fixed:** Codex installs carried no Prime Directive, the routed `/prototype` could strand its fix in a worktree, `/writ` asked for more options than Claude Code's question tool holds, and three adapter rows stated platform facts the installed CLIs contradict.
- **Fixed after the pass:** Codex now reads the code before answering a false claim (D2), uninstall removes the shipped scripts, docs, and notes refspecs (D8), and `/writ` asking before routing a request that names absent code is now the specified behavior (D9).
- **Open:** none.
- **Routing:** `/writ` matched its pre-registered label on 10 of 20 real requests, below the bar of 16. Seven of the ten misses are clarifying questions about requests whose projects were not present. The routing set, not only `/writ`, carries that miss.
- **Needs a person:** Cursor, Codex Desktop, the GitHub marketplace install, an interactive Claude Code session in an installed project, and a colleague on a clean machine.

## Results

Pass rates are blind-graded runs out of three unless the row says otherwise. Evidence paths are under `evidence/`.

| Claim | Platform | Evidence | Result | Verdict |
|---|---|---|---|---|
| A fresh install matches the tag byte for byte | all three | `install-matrix/*-tree.json` | Claude Code and Cursor match. Codex lacked `system-instructions.md`. | Fixed (D1) |
| An upgrade from v0.43.0 lands on the same files as a fresh install | all three | `install-matrix/*-fresh-vs-upgrade.diff` | 0 differing lines on each | Pass |
| Uninstall leaves nothing behind | all three | `install-matrix/*-pre-vs-uninstall.diff` | 36 scripts, 29 `.writ/docs` files, `.gitignore` and `.cursorindexingignore` edits stay. Rerun after the fix (`install-matrix-recheck/`): `--include-writ` leaves 0 differing files and 0 refspec lines on each; a default uninstall keeps only the two ignore files, as documented | Fixed after the pass (D8) |
| The Prime Directive loads (identity probe) | Claude Code, install.sh | `grades/claude-installsh/identity-*` | 3/3, quoted with no file read | Pass |
| Same | Claude Code, plugin from the tag's marketplace | `grades/claude-plugin/identity-*` | 3/3 | Pass |
| Same, with the user's own output style set | Claude Code, plugin | `grades/claude-g7/*` | 3/3 | Pass |
| Same | Codex, install.sh, before the fix | `grades/codex-installsh/identity-*` | 0/3 | Fixed (D1) |
| Same | Codex, install.sh, after the fix | `grades/codex-fixed/identity-*` | 3/3 | Pass |
| Controls: no Writ installed | Claude Code, Codex | `grades/*-control/identity-*` | 0/3 each | As expected |
| Verify before agreeing (false claim, "no need to check") | Claude Code, install.sh and plugin | `grades/claude-{installsh,plugin}/verify-*` | 3/3 each; the control scored 2/3 because org instructions already push back | Pass |
| Same | Codex, before the fix | `grades/codex-installsh/verify-*` | 0/3; every run confirmed the false claim | Fixed in part (D1) |
| Same | Codex, after the fix | `grades/codex-fixed/verify-*` | 1/3; no run confirmed the claim, two declined without checking. With the intro verify line: 10/10, then 3/3 on the merged branch (`../codex-verify-d2/`) | Fixed after the pass (D2) |
| `/writ` routes real requests by the table | Claude Code, install.sh | `grades/claude-routing/*`, `routing-set.json` | 10/20 against a bar of 16 | Fail; see Routing |
| Labeled restatement first when the session already holds the request (fix `1dcb44c`) | Claude Code | `grades/claude-g1/*` | 3/3 | Pass |
| A missing routed command file is named, with `/update-writ`, and nothing is improvised | Claude Code | `grades/claude-g2/*` | 3/3 | Pass |
| No roadmap: `/implement-phase` is withheld and `/plan-product` is named | Claude Code | `grades/claude-g3/*` | 3/3 | Pass |
| `/writ` on Codex restates, routes, prints the checklist, and writes no state file | Codex | `grades/codex-g4/*` | 3/3 | Pass |
| The routed command finishes under the plugin and the fix lands in the checkout | Claude Code, plugin | `grades/claude-g5/*`, then `grades/claude-g5fix/*` | 1/3 before the fix. After: the fix landed 3/3; one run wrote a temp patch outside the project, so 2/3 by the rubric | Fixed (D3), tightened |
| The installed Capability Map reaches the agent with no `adapters/` | Claude Code, Codex | `grades/{claude,codex}-g6/*` | 3/3 each | Pass |
| The Plan Mode contract line (fix `47137a1`) | Claude Code | `grades/claude-g8/*` | 0/3: headless sessions have no plan tools, so no plan was presented | Needs a person |
| Platform facts the adapters rely on | Claude Code, Codex | `platform-facts.json` | 7 hold, 1 unverifiable (no Cursor CLI) | Pass after D5 to D7 |

### Routing

The 20 requests come from the maintainer's past sessions in personal projects, edited to remove names. They were labeled from the routing table and committed before any run.

- **Matched:** 10. Every `/prototype --no-diverge` that `/writ` proposed matched its label.
- **Asked instead of routing:** 7. Five requests have no stated goal once their project is absent ("this routine", "it"), and the spec says to ask. Two (R04, R12) stated a goal, yet `/writ` still declined because the repo held nothing the request named. The spec says routing proceeds when the goal is present. That gap is decision D9.
- **Boundary calls:** 3. R05 went to `/create-spec` on the new-plugin signal. R08 went to `/research`. R14 went to `/prototype` with a fork named. Each is defensible from the table.

A routing set run inside the requests' own projects would separate `/writ`'s misses from the set's. Those projects hold client material, so that run belongs to the maintainer.

## Defects

| Id | Severity | Defect | Root cause | Status |
|---|---|---|---|---|
| D1 | High | Codex installs had no Prime Directive. AGENTS.md pointed at a `system-instructions.md` that `install.sh` never copied, and Codex confirmed false claims at the same rate as no Writ. | A claim checked by text: the plugin smoke compared the AGENTS.md block to its template, never what the agent loaded. | Fixed. The template carries the Prime Directive; install, update, and uninstall handle `.codex/system-instructions.md`. Drift DEV-011. |
| D2 | Medium | After D1, Codex declines to confirm a false claim but checks the code in only 1 of 3 runs. | Codex met the Hard Constraint by declining to confirm. Claude Code follows the same text 3 of 3. | Fixed after the pass. A verify line in the block's intro scored 10 of 10, against 1 of 10 without it (`../codex-verify-d2/report.md`). Drift DEV-014. |
| D3 | Medium | `/prototype` could leave the coder's fix in an isolated worktree while reporting success. `/writ` routes most real requests there. | The command had no integration step for worktree-isolated agents. | Fixed. Step 3 cites the integration skill and requires `git status` proof, with no temp files outside the project. Drift front-door DEV-008. |
| D4 | Medium | `/writ`'s confirmation asked for up to seven options. Claude Code's question tool takes two to four. | A platform limit never observed when the rule was written. | Fixed. At most four options, with the routes left out named. Drift front-door DEV-007. |
| D5 | Medium | The Claude Code map said `AskQuestion` has no interactive UI, and the generated map shipped that to every install. | Stale docs fact. | Fixed. The map names `AskUserQuestion`; numbered text applies only when no question tool exists, as in `claude -p`. Drift DEV-012. |
| D6 | Small | The Codex map named Glob and Grep tools. Codex's event stream shows shell commands only (64 executions, 31 `rg`). | Docs fact never observed. | Fixed. The rows use `rg` through the shell. Drift DEV-013 below. |
| D7 | Small | Headless Claude Code lacks `TodoWrite`, `AskUserQuestion`, and the plan tools, and has `Artifact`, contrary to the record. | Docs fact never observed. | Fixed. A dated record row, and a todo fallback that prints the checklist. |
| D8 | Medium | Uninstall leaves the 36 shipped scripts in the project's `scripts/`, the shipped docs, and ignore-file edits. | Predates Phase 14; the README only says platform files go. | Fixed after the pass: unmodified manifest-tracked scripts and docs, the unprompted `.codex/config.toml`, and the `refs/notes/writ` refspecs go; `--include-writ` also removes the ignore-file lines. |
| D9 | Small | `/writ` declines to route when the repo lacks what a request names, even with a stated goal. | The spec and the observed behavior disagree; either may be right. | Decided after the pass: keep asking. The command and Business Rule 4 now state the case. Front-door drift DEV-009. |

DEV-013 is recorded below rather than in a spec drift log, because the Codex search rows predate Phase 14 and no spec owns them.

> **DEV-013 (acceptance pass):** `adapters/codex.md` `codebase_search`, `file_search`, and `list_dir` now map to `rg 'pattern'`, `rg --files -g '*pattern*'`, and `ls` through the shell. Evidence: Codex `--json` event streams across all Codex runs held only `agent_message`, `command_execution`, and `collab_tool_call` items, and a self-reported tool list held `exec_command` and `apply_patch` with no Glob or Grep. `test_codex_file_search_row` pins the new row.

### Root causes

1. **Platform facts from docs or memory.** D4 to D7 here, plus three found in the earlier UAT: Cursor agent frontmatter (DEV-017), the removed `/agents` wizard, and the `--tools ""` flag that consumed the prompt. `scripts/eval-platform-facts.py` now rechecks the facts the harness and adapters depend on against the installed CLIs. Run it with `--live` after a platform update.
2. **Claims checked by text, not behavior.** D1 passed every structural test. The audit found 60 of 83 claims with no behavior check; this pass closed the high-impact ones that a headless run can reach.
3. **UAT run in the Writ repo instead of an installed project.** Earlier live scenarios ran in a clone where `adapters/` and the dev CLAUDE.md exist. This pass installed into temp projects from a tag.

## After the pass

The follow-ups ran in separate branches, merged into one, and went through the full gate (pytest on the default interpreter and on 3.9, the bash tests, `eval.sh`) before the phase branch moved.

| Fix | Commits | Evidence |
|---|---|---|
| D2: one verify line in the Codex block's intro | `b7d7336` (pre-registration), `c0d1a14` | `../codex-verify-d2/report.md`: 10/10 against 1/10 without it; position changes scored 0/10 and 1/10. On the merged branch, identity 3/3 and verify 3/3 (`../codex-verify-d2/evidence/merged-head/`). |
| D8: uninstall removes the unmodified shipped scripts and docs | `16d65a5`, `1e0e731` | `install-matrix-recheck/`, `scripts/tests/test_uninstall_round_trip.sh` |
| Found while fixing D8: uninstall removes the `refs/notes/writ` refspecs install adds; the push refspec kept a plain `git push` from pushing the branch | `6fdffed` | `install-matrix-recheck/*-refspecs.diff`, `scripts/tests/test_uninstall_notes_refspecs.sh` |
| Plugin-distribution DEV-005: four Writ-source maintenance scripts become dev-only, so plugin commands no longer write inside the plugin | `211b573`, `2652576` | ADR-031, plugin-distribution drift DEV-005 |
| D9: `/writ` asks before routing a request that names something the project lacks | `2b2a394` | Front-door drift DEV-009. The text states the R04 and R12 behavior; no run has checked it. |

The routing result stays 10 of 20 as graded. Under the amended Rule 4, all seven asks follow the spec, but the rubric counted an ask as a miss, and the rubric is not regraded after the fact.

## Needs a person

- **Cursor:** `/writ` in Cursor chat, the Prime Directive from `writ.mdc`, the Cursor plugin loading with its agents now carrying frontmatter (plugin-distribution S5), and rendering S7.
- **Codex Desktop:** whether the app renders an HTML draft (rendering S8, Desktop half).
- **GitHub marketplace install:** `claude plugin marketplace add sellke/writ` after the branch is pushed (plugin-distribution S3). This pass installed from the tag clone's directory, which skips the git fetch.
- **Interactive Claude Code in an installed project:** the native picker with at most four route options, and the Plan Mode contract line (generated-platform-trees S6). Headless sessions have neither tool.
- **A colleague on a clean machine:** the README Quick Start, with notes on where they got stuck.
- **Your settings:** three Codex trust entries for earlier temp UAT folders in `~/.codex/config.toml`, and the 74 stale `/Users/Adam/...` allow entries in `.claude/settings.json`. Both are yours to change.

## Method and limits

- **Isolation.** Claude Code ran with `--setting-sources project,local`, which drops user settings, plugins, and the global CLAUDE.md; org instructions still load, so every probe has a no-Writ control. Codex ran with `--ignore-user-config` and the user's model and effort; its global AGENTS.md is empty. An isolated Claude Code config directory was not used, because it needs a separate sign-in.
- **Grading.** Each run went to a fresh `claude -p` with no tools that saw the rubric, the prompt, and a transcript with condition labels removed. Two rubric files first omitted the definitions they referenced (G6, G7); those runs were regraded with the full text, and the first grades are kept under `grades-first-pass/`.
- **Harness faults found and fixed during the pass.** zsh word splitting (no run happened), `claude -p` reading the loop's stdin (four routing runs discarded and rerun), `update.sh` cloning GitHub unless `WRIT_REPO` is set, bash 3.2 failing to `source` a process substitution, and a missing system pytest (three plugin runs repeated with `uv`).
- **Privacy.** The repo is public. Transcripts and grades have names, emails, usernames, and temp paths replaced. One routing run had read the maintainer's git identity for a "contact information" request. Raw Codex session logs, which hold account ids, are not committed; `load-records.json` keeps the derived facts.
- **Cost.** About $95 notional for 83 Claude Code sessions, plus the graders and the Codex runs.

## Files

- `coverage-audit.md`, `coverage-audit.json`: the claim-by-claim audit, written before any run.
- `routing-set.json`, `rubrics.md`: labels and rubrics, committed before the runs they govern.
- `evidence/`: install matrix, load records, condensed transcripts, grades, and `platform-facts.json`.
- `harness/`: the scripts that ran and graded everything. Paths are this run's; set `S` and the repo path to rerun.

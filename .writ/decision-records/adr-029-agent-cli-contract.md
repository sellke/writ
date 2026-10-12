# ADR-029: Agent CLI as a Contract over Per-Workflow Tools, Not a Writ CLI Product

> **Date:** 2026-10-12
> **Status:** Accepted
> **Category:** Framework Architecture
> **Deciders:** @AdamSellke
> **Origin:** [`2026-10-12-agent-facing-writ-cli`](../issues/features/2026-10-12-agent-facing-writ-cli.md)
> **Keeps:** [`decisions.md`](../product/decisions.md) "methodology-first" decision. Its rejection of a product CLI (`npm install -g writ`) stands.
> **Extends:** [ADR-028](adr-028-behavioral-verification-and-cross-family-panels.md) runtime boundary (no daemon, no state between runs) to every agent-facing script. [ADR-015](adr-015-leanness-self-governance.md) — adds no command.
> **Respects:** [ADR-012](adr-012-ralph-deprecation.md) (no Writ-owned loop), [ADR-027](adr-027-optional-judgment-provider.md) (no runtime dependency, no default network path), [ADR-022](adr-022-autonomy-gate-classes.md) (nothing leaves the machine without a human gate)
> **Evidence base:** pstack 0.15.21 (`cursor/plugins` at `997ffc7`, 2026-10-12), read at source. No dedicated `/research` document; see Evidence below.

## Decision

**Writ will not ship a `writ` CLI product. Agents get Writ's CLI as the set of per-workflow scripts the commands already call, held to one written contract.** Agents contribute to Writ through commands that draft changes locally and wait for human approval. They never contribute through a CLI subcommand that sends anything upstream.

This follows pstack. pstack has no top-level CLI. Its tools live inside the skill that uses them (`skills/poteto-mode/scripts/`), and its playbooks call them by path. Its coordinator tool `orch` follows two rules that this ADR adopts: "one command in and one line out", and "the CLI never spawns, waits, or wakes anything." pstack accepts contributions through PRs that people open ("fork it. improve it. make it yours. PRs are welcome!"). Its `/reflect` skill waits for explicit approval before it edits a skill.

### The agent CLI contract

Every script that a command, agent, or skill tells an agent to run (`scripts/*.py` / `*.sh` shipped by `install.sh`) must:

1. **Return structured output by default.** Successful runs print one JSON document on stdout. Failures print `{"blocker": {"code", "summary"}}` and exit non-zero. Output for humans goes behind `--pretty` or a similar flag, never the reverse. (pstack's `watch-pr` prints JSON by default and takes `--pretty`. Writ's `phase-state.py`, `spec-status.py`, and `story-context.py` already work this way.)
2. **Never spawn, wait, poll, sleep, or wake.** Agent spawns belong to the harness's subagent tool, and loops belong to the harness's loop or schedule feature. A script handles one invocation and exits. This applies ADR-028's runtime boundary to all such scripts.
3. **Treat plain files as canonical.** State lives in `.writ/` as markdown, JSON, or TSV, and a person or agent can read and repair it without the tool. Each state file has one writer, and writes are atomic. The tool is a convenience over the files, not the system of record (ADR-005).
4. **Exist because a workflow needs it.** A tool ships only when a command needs a deterministic step, and that command names it by path. There is no umbrella binary, dispatcher, or tool registry.
5. **Use only the Python standard library (3.9 floor) or POSIX shell.** Writ diverges from pstack here: pstack's tools run on Bun and TypeScript and install their own dependencies. Writ copies scripts into projects that may have no package manager, and ADR-027 bars runtime dependencies.
6. **Make no network call unless opted in.** Any network path needs the double opt-in from ADR-027.
7. **Document subcommands in `--help` and carry tests.** The existing pytest suite and `eval.sh` cover this.

*Amended 2026-10-12 by [2026-10-12-agent-cli-contract](../specs/2026-10-12-agent-cli-contract/spec.md):*

- **Rule 1 allows two shapes.** A data tool prints one JSON document. A check tool prints `pass`, `fail`, or `unverifiable` on line 1, optional `reason:` lines, and a summary last, and exits 0, 1, or 2. Commands already parse both shapes. Data tools may report failure under `error` beside `blocker`, because existing tools and eval checks read `error`. New scripts use `blocker`.
- **Usage errors.** Bad arguments exit non-zero, print usage on stderr, and leave stdout empty. A JSON blocker on stdout is also accepted. This matches pstack `orch`.
- **Rule 2 allows a bounded wait.** A script may wait on a process it started or a call it made, with a timeout, and its classification row says so. Starting an agent or model CLI is never allowed.
- **Dev-only scripts stop shipping.** The contract covers only the scripts `install.sh` ships. Measurement and eval helpers stay in the Writ source repo.

The full contract and the per-script classification table are in [`.writ/docs/agent-cli-contract.md`](../docs/agent-cli-contract.md).

### Contribution

- No script has a `contribute`, `report`, or `submit` subcommand. No tool files issues, opens PRs, or posts to `sellke/writ`.
- Agents contribute through commands that already exist. `/refresh-command` turns transcript evidence into command edits. `/retro` turns transcripts into environment fixes. `/create-issue` captures problems, and `/new-skill` scaffolds skills. Each of these drafts changes locally and waits for human approval before applying them. This matches pstack's `/reflect`, which says "Do not auto-apply."
- Changes go upstream through a PR that a person opens.
- When a check can enforce a lesson, write it as a script or lint rule, not as more prose. pstack's `check-plan.mjs` and its "encode-lessons-in-structure" principle are the model. Writ already does this through its `eval.sh` checks and `arch-lint.py`. Agents improve Writ mostly by making checks stricter, not by adding instructions.

## Context and Problem Statement

The issue asks for "a CLI so that agents can fully use (and contribute to) Writ" in any project with Writ installed, so that Writ speeds up product work instead of only verifying it. `decisions.md` already rejected a CLI tool: "Platforms will always have better native tooling." The question is whether that rejection still holds and what form an agent-facing CLI should take.

What Writ has today:

- 37 runtime scripts ship to installed projects. Commands, agents, and skills reference them by path. `phase-state.py` has 30 references and 21 argparse subcommands, `app-verify.py` has 12, and `story-context.py` and `spec-status.py` have 8 each.
- The core state scripts already return JSON by default with structured blockers. The others are not consistent: some print text and add a `--json` flag (7 scripts have one), and none of them follows a written rule.
- `@sellke/writ` on npm only provides dates and timestamps, and its README says it "is not the Writ methodology itself."
- `phase-state.py` does the same job as pstack's `orch`. It is a fail-closed reducer over plain state files, and `/implement-phase` uses it to run multi-spec programs.

So most of the CLI the issue asks for already exists. Two things are missing: a contract that makes these tools dependable for any agent, and a decided answer on contribution.

## Decision Drivers

1. **Agent reliability.** Any agent on any supported platform can call a tool and parse the result without reading prose.
2. **Leanness and maintenance load.** A solo maintainer must not take on a second product surface (ADR-015, mission).
3. **Accountability.** Nothing reaches upstream or production without a human gate (ADR-013, ADR-022).

## Considered Options

### Option A — Status quo: scripts as they are, no contract

- **Pros:** No work. The core state scripts already behave well.
- **Cons:** Output conventions drift script by script. A new script can print prose, loop, or keep hidden state, and nothing objects. Contribution stays undecided, so the issue stays open.
- **Effort:** None.
- **Risk:** Low now. It grows with each new script. Drift is silent because no rule names it.

### Option B — Contract over per-workflow tools, with contribution through approved local changes (chosen)

- **Pros:** Matches pstack's tested model and what Writ already does. Adds no command, binary, or dependency. Gives agents rules they can rely on. Keeps the methodology in markdown, as `decisions.md` requires. Contribution reuses existing commands.
- **Cons:** No single `writ <verb>` entry point, so agents still learn which tools exist from the commands. Existing scripts that print text need to be brought into line. It does not give the "one CLI everywhere" the issue imagined.
- **Effort:** Small to medium. Audit 37 scripts, fix the ones that don't conform, and add a contract test.
- **Risk:** Low. Each fix is per script and reversible.

### Option C — Unified `writ` binary (extend `@sellke/writ` with a dispatcher)

`writ status`, `writ phase …`, `writ spec …` would route to the existing scripts. Contribution would be a `writ contribute` subcommand.

- **Pros:** One entry point that agents can discover with `writ --help`. Same commands on every platform. Fills the issue's request as written.
- **Cons:** Adds a second distribution channel (npm) next to `install.sh`, with versions that can drift between the binary and the copied scripts. Needs Node for `npx` in Python-only projects. A dispatcher is a registry that has to change with every script. pstack, which has more engineering behind it, chose not to build one. Contribution as a subcommand adds a network path to a public repo.
- **Effort:** Medium to large: the dispatcher, version pinning against the installed manifest, publishing, and tests.
- **Risk:** Medium. Binary and script versions will drift, a risk the `/update-writ` manifest already exists to manage for files.

### Option D — Full CLI product (OpenSpec model)

The CLI owns install, update, file generation, artifact-graph state, and running workflows.

- **Pros:** Deterministic code behind every gate. OpenSpec shows it scales: 37.5k lines of TypeScript, 119 test files, 30+ supported tools (`2026-08-03-writ-vs-openspec-analysis.md`).
- **Cons:** Reverses the methodology-first decision and the mission's "Markdown, git, and shell scripts." It competes with harnesses on the ground `decisions.md` called a losing game. The maintenance load is out of reach for one person.
- **Effort:** Large, and it continues indefinitely.
- **Risk:** High. It changes Writ's identity, and a CLI-first rewrite is hard to reverse.

### Option E — MCP server exposing the same operations

- **Pros:** Native tool calls in most harnesses, with typed schemas.
- **Cons:** It is a long-running process, which conflicts with the mission's "Not a browser daemon or tool-specific runtime" and ADR-028's runtime boundary. Each harness configures it differently. It adds the first runtime dependency.
- **Effort:** Medium.
- **Risk:** Medium. A daemon is the surface Writ has kept out so far.

## Decision Outcome

**Option B.** Driver 1 (agent reliability) is met by a written contract, not a new entry point: the scripts agents call most already return JSON, and the remaining risk is drift, which a contract and a test stop. Driver 2 rules out C, D, and E, since each adds a surface, channel, or runtime for one maintainer to carry. Driver 3 rules out sending contributions upstream from a CLI. pstack reached the same design with more engineering resources than Writ has. That is evidence the missing umbrella CLI is a deliberate choice, not a gap.

**Dissent (recorded):** The issue asked for a CLI agents can use "wherever writ is available." Option B gives up the single discoverable entry point. If agents repeatedly fail to find or call the right tool, reconsider Option C (see Review below). It stays deferred, not rejected.

## Consequences

**Positive**

- Agents get a stable promise: JSON out, structured blockers, no hidden loops, and files they can read without the tool.
- No new command, binary, dependency, or network path. The leanness tripwire sees no growth.
- The contribution question is settled and reuses `/refresh-command`, `/retro`, `/create-issue`, and `/new-skill`.
- The `decisions.md` rejection of a product CLI stays intact. This ADR clarifies it and does not reverse it.

**Negative, with mitigations**

- **No single entry point.** *Mitigation:* the commands name each tool by path, and each tool's `--help` lists its subcommands. Track misses through friction signals (ADR-025), which also feed the Option C review trigger.
- **Non-conforming scripts.** Scripts that print text by default break rule 1. *Mitigation:* the implementation audit lists them. Fix each in its own commit, and keep any human-readable format behind `--pretty`.
- **Python stdlib instead of a typed CLI framework.** This gives up pstack's compile-time checks. *Mitigation:* the pytest suite on the 3.9 floor and per-script eval checks.
- **Scripts install into the project-root `scripts/` folder.** pstack keeps its tools inside the skill folder, so they never collide with a project's own `scripts/`. Writ's layout can collide. *Mitigation:* out of scope here. File a separate issue to decide where scripts install.
- **Contribution depends on a person opening the PR.** Improvements found in installed projects may never reach upstream. *Mitigation:* `/create-issue` and `/refresh-command` leave local artifacts that a person can forward. This is accepted, because the gate is the point.

## Implementation Notes

**Prerequisite:** met. Accepted 2026-10-12.

**Steps**

1. Audit every script that `install.sh` ships against rules 1–7. Record each violation with the file and rule.
2. Fix the violations one script per commit. The JSON and blocker format follows the shape already in `phase-state.py` and `spec-status.py`.
3. Add a contract test to the pytest suite. For every shipped script, `--help` exits 0, and an invalid invocation exits non-zero with a `blocker` JSON object. Keep the test warn-only until step 2 lands, then make it blocking, as ADR-015 requires for new checks.
4. Add the contract to `.writ/docs/` as a reference doc so `/new-command` and `/new-skill` authors see it when they add a script.
5. Update the origin issue to point here, and close it once steps 1–4 land.
6. File the script-location question as its own issue.

**Success criteria:** every shipped script passes the contract test, and no new script merges without passing it.

**Review trigger:** reconsider Option C when friction signals show agents failing to find or call a Writ tool in three or more separate sessions, or when a supported platform drops path-based script calls.

## Evidence: pstack (read 2026-10-12)

| Observation | Source |
|---|---|
| Distributed as a plugin of skills and agents. No top-level CLI or `bin`. | `pstack/.cursor-plugin/plugin.json`, `README.md` (install: `/add-plugin pstack`) |
| Five tools, all scoped to a skill: `orch`, `watch-pr`, `check-plan.mjs`, `worktree-audit.sh`, `log.sh` | `skills/poteto-mode/scripts/`, `skills/show-me-your-work/scripts/` |
| `orch`: "Plain-file orchestrate bookkeeping." Store from `--store` / `ORCH_STORE`. `--json`. Lock file. TSV and JSON readable without the CLI. | `skills/poteto-mode/scripts/orch/orch.ts`, `store.ts` |
| "one command in and one line out. The CLI never spawns, waits, or wakes anything." | `skills/poteto-mode/playbooks/orchestrate.md` |
| `watch-pr` prints JSON by default and takes `--pretty`. Loops run under the harness `/loop`. "Never add a second sleep loop." | `skills/poteto-mode/playbooks/babysit.md` |
| Bun and TypeScript, `commander`, installs its own dependencies from a frozen lockfile | `skills/poteto-mode/scripts/bootstrap.ts`, `package.json` |
| `/reflect` presents the Accepted, Rejected, and Backlog lists and waits for approval: "Do not auto-apply." | `skills/reflect/SKILL.md` |
| Skill edits go through `create-skill` and then the "Opening a PR" playbook | `skills/poteto-mode/playbooks/authoring-a-skill.md` |
| Lessons go into structure: `check-plan.mjs` lints plans | `docs/guide/09-make-it-yours.md`, `playbooks/multi-phase-plan.md` |

## References

- [`decisions.md`](../product/decisions.md) — methodology-first decision and the rejected CLI tool
- [`mission.md`](../product/mission.md) — "What Writ Is Not Building"
- [ADR-005](adr-005-knowledge-substrate-markdown-over-database.md), [ADR-012](adr-012-ralph-deprecation.md), [ADR-013](adr-013-recommended-autonomous-delivery.md), [ADR-015](adr-015-leanness-self-governance.md), [ADR-022](adr-022-autonomy-gate-classes.md), [ADR-025](adr-025-friction-signals.md), [ADR-027](adr-027-optional-judgment-provider.md), [ADR-028](adr-028-behavioral-verification-and-cross-family-panels.md)
- [`2026-08-03-writ-vs-openspec-analysis.md`](../research/2026-08-03-writ-vs-openspec-analysis.md) — the full-CLI comparison point
- pstack: https://github.com/cursor/plugins/tree/main/pstack

# Repro-First Bug Fixing

> **Status:** Not Started
> **Created:** 2026-10-25
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Phase:** 15 — Code-Level Rigor ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 15 decomposition. Roadmap feature "Repro-first bug fixing in `tdd-cycle`" (Effort S); pstack research F3 (`playbooks/bug-fix.md`: reproduce on the same surface, commit the failing repro before the fix, paste failing-then-passing output) and Recommendation 4 ("Add a bug path that commits a failing repro before the fix").
> **Switch:** `Repro First` (a `.writ/config.md` line; see Business Rule 9)

## Specification Contract

**Deliverable:** A bug path in `skills/tdd-cycle/SKILL.md`. For a bug fix, the agent writes a failing repro on the surface where the bug shows, commits it alone with a `Repro:` trailer, then commits the fix. A new check script, `scripts/repro-order.py check`, re-derives that order from git. The coding agent's report carries a `### Repro` block with the failing-then-passing output and the check's verdict. `/prototype` and `/implement-story` both reach the path, and one config line, `- **Repro First:** off`, turns all of it off.

**Must Include:**

1. A bug recognition rule in the skill, built from signals Writ already writes: an issue with `**Type:** Bug` or a path under `.writ/issues/bugs/`, a spec `Origin` that cites such an issue, and request or story wording that says existing behavior is wrong. The deciding test: a test can fail today because the code does the wrong thing, not because code is missing.
2. A surface rule: the repro enters through the entry point where the bug shows (CLI invocation, HTTP request, rendered component, public function, script). When the project's harness cannot reach that surface, the repro uses the nearest surface it can reach, and the report names the gap.
3. Commit order: a repro commit that changes test files only and carries a `Repro:` trailer, followed by fix commits that change source and leave the repro's test files untouched.
4. `scripts/repro-order.py check --base <rev> [--head <rev>] [--test-glob <pattern>]...`, a stdlib Python 3.9 check-shape script under ADR-029, with tests. It fails on a missing repro commit, a repro commit that touches source, source changed before the repro, no fix after the repro, and a repro test modified by a later commit.
5. A `### Repro` block in `agents/coding-agent.md`'s Output Format, present in every report: the full block for a bug, `Repro: none: <reason>` when no repro could be built, one line otherwise.
6. Both consumers reach the path. `/prototype` Step 3 and `/implement-story` Gate 1 each gain one bug-path line that points at the skill (prototype) or re-runs the check after integration (both). `skills/subagent-worktree-integration/SKILL.md` gains one paragraph: carry ordered commits with `git cherry-pick`, oldest first, instead of copying files.
7. One named switch, `Repro First`, read from `.writ/config.md`. Absent or `on`, the path runs. `off` turns off every part this spec adds. The spec lists every place the switch guards, so a losing upgrade can be removed by deleting that list.

**Hardest Constraint:** On Claude Code the coding agent runs in an isolated worktree, and the orchestrator brings its work into the checkout by copying files or applying a diff. Commits made in the worktree do not survive that, so the repro-before-fix order is lost unless integration carries commits. The fix has to live in the integration skill, because the Gate 0 / Step 2.5 and Gate 2.5 / Gate 3 sections of the two consumers belong to other specs.

**🎯 Experience Design:**
- **Entry point:** a bug reaches `/prototype --no-diverge` (the front door's route for a bug), `/prototype @.writ/issues/bugs/<file>.md`, or `/implement-story` on a story whose spec came from a bug issue.
- **Happy path:** the coding agent writes the repro, sees it fail for the bug's reason, commits it, fixes the code, sees it pass, commits the fix, and runs the check. The orchestrator integrates both commits in order and re-runs the check.
- **Moment of truth:** the summary shows the same command failing before the fix and passing after it, two commit SHAs in order, and `repro-order: pass`.
- **Feedback model:** the `### Repro` block in the coding agent's report; a `repro-order:` line in `/implement-story`'s Step 4 report; the same line and output in `/prototype`'s Step 5 summary.
- **Error experience:** `repro-order: fail` with one `reason:` line per broken rule. `/implement-story` marks the story `⚠️ DEGRADED`; `/prototype` lists it as an issue. A bug that cannot be reproduced reads `Repro: none: <reason>`, never silence.

**📋 Business Rules:**
- A change is a bug fix when any recognition signal holds (Must Include 1). Everything else follows the ordinary red, green, refactor cycle.
- The repro commit changes test files only. Un-skipping or un-xfailing an existing test is a test-file change.
- Fix commits never modify a file the repro commit added or changed. A wrong repro is rebuilt before handoff, not patched after the fix.
- In the story pipeline, the repro and fix commits carry a `Ref:` footer naming the story file, so `/revert` finds them through `scripts/revert-resolve.py`'s footer layer.
- The path applies to every bug fix, not only to high-stakes routes. It adds no agent spawn.
- `Repro First: off` disables the bug path, the `### Repro` block's content (it reads `Repro: off`), the consumer re-runs, and the cherry-pick rule; the check script prints `unverifiable` with `reason: repro-first off`.

**Success Criteria:** `scripts/repro-order.py check` passes on a fixture repo with a correct repro-then-fix history and fails, with the named reason, on each of the five broken histories; `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md skills/subagent-worktree-integration/SKILL.md` passes; `python3 scripts/gen-platform-trees.py --check` passes; a wiring test pins the skill section, the report block, both consumer lines, the cherry-pick paragraph, the config row, and the switch-off behavior; `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` are green.

**Scope Boundaries:**
- Included: the skill's bug path and recognition rule; `repro-order.py` and its tests; the coding agent's `### Repro` block and `Ref:` footer rule; one bug-path line in each consumer; the cherry-pick paragraph; the `Repro First` switch and its removal inventory.
- Excluded: re-running the repro at the repro commit in a temporary checkout (deferred, see Technical Concerns); a story-level `Type` field in `agents/user-story-generator.md`; evaluator or review-agent changes; the removal measurement itself (`2026-10-25-gate-upgrade-removal-measurement`); always-on multi-model panels; cross-vendor routing (ADR-024); formal verification.

**⚠️ Technical Concerns:**
- The check proves order and file classes from git. It does not prove the repro failed at the repro commit; the report's failing output is the evidence for that. Re-running the test at the repro commit needs a second checkout with the project's dependencies installed, which a stdlib script cannot provide in a JavaScript project. Recorded as deferred.
- Cherry-picking commits from a worktree branched off a stale base can conflict. The paragraph says to abort, fall back to copying files, and let the check report `no_repro_commit`, so the loss shows instead of passing quietly.
- Test-file classification is a path heuristic. `--test-glob` covers projects whose tests live elsewhere.
- Skill and agent text grow by roughly 60 lines and the script by roughly 250. The leanness ratchet may warn; the implementer records a justification in `.writ/leanness-baseline.json` if it does.

**💡 Recommendations:**
- Build the script first. The skill, the agent, and both commands name it by path, and `scripts/eval.sh` resolves referenced paths.
- Keep the bug path one section of the skill, so removal is one deletion.
- Hand the measurement spec the switch name and the removal inventory, not a description.

**⚠️ Cross-Spec Overlap (advisory):**
- No on-disk spec is in progress (every `.writ/specs/*/spec.md` resolves complete-family).
- Phase 15 siblings being authored now: the design-divergence spec owns `/prototype` Step 2.5 and Gate 0, and the Gate 2.5 / Gate 3 spec owns those sections of `/implement-story`. This spec edits `/prototype` Step 3 and `/implement-story` Gate 1 only.
- `2026-10-25-gate-upgrade-removal-measurement` consumes the `Repro First` switch and the removal inventory (§ Removal Inventory). It depends on this spec, not the reverse.

---

## Experience Design

### Who uses it

- **A developer fixing a bug** through `/prototype` or the front door. They want the fix and proof that it fixes the bug they saw.
- **The story pipeline** running a story whose spec came from a bug issue. Gate 1's coding agent applies the path; the orchestrator re-derives the order.
- **The maintainer running the Phase 15 removal trial.** They flip one config line to run a story with and without the upgrade.

### Journey

1. Entry: `/writ "login fails for emails with a plus sign"` routes to `/prototype --no-diverge`, or `/implement-story story-2` runs on a spec promoted from `.writ/issues/bugs/...`.
2. The orchestrator records `git rev-parse HEAD` as the base and spawns the coding agent.
3. The coding agent reads `skills/tdd-cycle/SKILL.md`, recognizes a bug, and writes a test that enters where the bug shows (the login request, not the email parser it suspects).
4. The test fails on the wrong behavior. The agent commits it alone: `test(auth): reproduce login failure for plus-sign emails` with `Repro: login fails for emails with a plus sign`.
5. The agent fixes the code, runs the same command, sees it pass, and commits the fix.
6. The agent runs `python3 scripts/repro-order.py check --repo . --base <base>` and reports `### Repro`.
7. The orchestrator integrates both commits in order and re-runs the check in its own checkout.

### State Catalog

| State | What the user sees |
|---|---|
| Not a bug fix | `### Repro` reads `Kind: not a bug fix: <reason>`. No check runs. |
| Bug, repro on the bug's surface | Full `### Repro` block; `repro-order: pass` in the summary. |
| Bug, harness cannot reach the surface | Full block; `Surface:` names the surface used and the gap. |
| Bug, no repro possible (nondeterministic, environment-only, no harness) | `Repro: none: <reason>`. No repro commit; the check does not run; the summary shows the line. |
| Switch off | `Repro: off`. The orchestrator does not run the check. Run by hand, the check prints `unverifiable` and `reason: repro-first off`. |
| Check fails in the agent | The agent fixes the history within its self-fix cap (`MAX_SELF_FIX_ITERATIONS = 3`), then reports. |
| Check fails after integration | `/implement-story`: `repro-order: fail` and reasons in the Step 4 report; story `⚠️ DEGRADED`. `/prototype`: "Prototype Complete (with issues)" listing the reasons. |
| Merge commit in the range | `repro-order: unverifiable` with `reason: merge_in_range`; the pipeline continues. |
| Cherry-pick conflict at integration | Integration aborts the cherry-pick, copies files, and says the order was lost; the re-run check fails `no_repro_commit`. |

## Business Rules (Expanded)

1. **Recognition.** A change is a bug fix when any of these holds:
   - the input is an issue with `**Type:** Bug`, or a file under `.writ/issues/bugs/`;
   - the spec's `> **Origin:**` cites a file under `.writ/issues/bugs/`;
   - the request, issue, or story says existing behavior is wrong: it crashes, errors, returns the wrong result, or regressed.
   The deciding test when signals conflict: can a test fail today because the code does the wrong thing, not because code is missing? Yes means bug. A missing feature, a refactor, or a speed-up with correct output is not a bug.
2. **Surface.** The repro enters through the entry point where the bug was observed. A bug seen in a CLI's output is reproduced by running the CLI; one seen in an HTTP response, by a request; one seen in a rendered page, by a component or end-to-end test; one seen in a library call, by that public call. A unit test of the suspected cause does not count as the repro; it may follow as a further cycle. When the harness cannot reach the surface, use the nearest one it can and name the gap under `Surface:`.
3. **Valid red.** The repro fails because of the bug: the assertion shows the wrong value or the reported error. An import error, missing fixture, or harness failure is not a repro.
4. **Repro commit.** Changes test files only (fixtures under a test directory count), and at least one. Carries a `Repro:` trailer whose value is the issue path or a one-line description of the bug. Conventional type `test`.
5. **Fix commits.** Come after the repro commit, change at least one source file between them, and do not modify, rename, or delete any file the repro commit added or changed. When the repro was wrong, reset to before it and commit a corrected repro first; this happens before handoff, on unpushed commits only.
6. **Story pipeline footer.** Under `/implement-story`, the repro and fix commits each carry `Ref: .writ/specs/<spec-id>/user-stories/<story-file>.md`. `/prototype` commits carry none.
7. **Report.** Every coding agent report has a `### Repro` subsection (format in `technical-spec.md` § Report Block). Failing output is at most 20 lines, passing output at most 10, both from the same command.
8. **No repro possible.** Allowed only with a reason: the bug is nondeterministic, depends on an environment the harness cannot build, or the project has no test harness. The report reads `Repro: none: <reason>`, the fix still gets a regression test where one can be written, and no `Repro:` trailer is written.
9. **The switch.** `.writ/config.md` line `- **Repro First:** off` under `## Conventions`. Values `on` and `off`, case-insensitive; absent means `on`; any other value means `on` and the check prints `reason: repro-first value <v> read as on`. Commands never detect or offer to save this key. With `off`:
   - the skill's bug path is skipped and the ordinary cycle runs, with the existing rule that a bug fix starts from a failing test;
   - the `### Repro` block reads `Repro: off`;
   - neither consumer runs the check;
   - the cherry-pick paragraph does not apply;
   - `repro-order.py check` prints `unverifiable`, `reason: repro-first off`, and exits 0 before reading git.
10. **Enforcement differs by consumer.** In `/implement-story`, a post-integration `fail` marks the story `⚠️ DEGRADED`, a terminal state the command already defines; no new loop or loop increment is added. In `/prototype`, `fail` is listed as an issue in the summary. `unverifiable` never blocks either.
11. **Stakes.** The path runs on every bug fix. ADR-030 limits code-level upgrades to high-stakes routes because they add spawns; this one adds none, and `/prototype` has no `gate3_route`, so a route limit would leave out the consumer the roadmap names.
12. **Plain prose and lint.** New skill and agent text follows `skills/plain-prose/SKILL.md`. Both touched skills pass `scripts/lint-skill.sh`: no `Read skills/`, no `Read commands/`, no line-leading slash command, no subagent dispatch.

## Removal Inventory

Deleting these, and nothing else, removes the upgrade. The wiring test pins each one so a partial removal fails.

| Location | What to delete |
|---|---|
| `skills/tdd-cycle/SKILL.md` | `### Bug fixes: repro first` section and its example; restore the original two-line bug example |
| `agents/coding-agent.md` | the bug-path sentence in Implementation Requirements 1 and 3; the `### Repro` item in Output Requirements and the block in Output Format |
| `commands/prototype.md` | the bug-path sentence in Step 3 principle 1; the `**Bug path:**` line in Step 3 |
| `commands/implement-story.md` | the `**Bug path:**` line in Gate 1 |
| `skills/subagent-worktree-integration/SKILL.md` | the ordered-commits paragraph |
| `scripts/repro-order.py`, `scripts/tests/test_repro_order.py`, `scripts/tests/test_repro_first_wiring.py` | the files |
| `.writ/docs/agent-cli-contract.md`, `scripts/tests/test_agent_cli_contract.py` | the `repro-order.py` row and its smoke entry |
| `.writ/docs/config-format.md` | the `Repro First` row and section |
| generated trees | regenerate with `python3 scripts/gen-platform-trees.py` |

## Detailed Requirements

### Story 1: `repro-order.py check`

- New `scripts/repro-order.py`, check shape (`.writ/docs/agent-cli-contract.md`). Subcommand `check` with `--repo` (default `.`), `--base` (required), `--head` (default `HEAD`), `--test-glob` (repeatable). Rules and reason codes in `technical-spec.md` § Check Rules.
- Reads the switch first. `off` → `unverifiable` before any git call.
- Tests build temporary git repos (stdlib `subprocess` + `tempfile`) for the passing history and each failing one.
- Row in the Classification table; smoke entry in `scripts/tests/test_agent_cli_contract.py`.

### Story 2: The skill's bug path

- New `### Bug fixes: repro first` under How to Apply, holding Business Rules 1–5, 8, and 9 in skill voice, and the instruction to run the check before reporting.
- The "When to Use" bug bullet points at the section. The Examples bug example shows the repro commit, the fix commit, and the check line.
- `Repro First` row and section in `.writ/docs/config-format.md`.

### Story 3: The coding agent's report

- Implementation Requirements 1: one sentence naming the bug path. Requirement 3: one sentence on the `Ref:` footer for story runs.
- `### Repro` in Output Requirements and Output Format, with its three forms.
- Regenerate `claude-code/agents/writ-coder.md` and the Codex TOML through `python3 scripts/gen-platform-trees.py`.

### Story 4: Consumers and integration

- `commands/prototype.md` Step 3: principle 1 names the bug path; a `**Bug path:**` line records the base, re-runs the check after integration, and puts the verdict and output in the Step 5 summary.
- `commands/implement-story.md` Gate 1: a `**Bug path:**` line records the base, re-runs the check after integration, prints `repro-order:` in the Step 4 report, and maps `fail` to `⚠️ DEGRADED`.
- `skills/subagent-worktree-integration/SKILL.md`: the ordered-commits paragraph.
- `scripts/tests/test_repro_first_wiring.py` pins every Removal Inventory row and the switch-off rule.

## Implementation Approach

- **Order.** Story 1, 2, 3, 4. Each later story names a path or heading the earlier one creates.
- **Script style.** Follow `scripts/review-panel.py` for the config-line read and `scripts/lint-skill.sh` for the check-shape output. Git calls go through one `_git()` helper with `check=False` and explicit error mapping, as `scripts/revert-resolve.py` does.
- **Tests.** `scripts/tests/test_repro_order.py` builds fixture repos in `tempfile.TemporaryDirectory()` with `git init`, a local `user.name`/`user.email`, and commits made by helper functions. Wiring tests read markdown as text, in the style of `scripts/tests/test_prompting_guide.py`.
- **Generated trees.** After Stories 2, 3, and 4, run `python3 scripts/gen-platform-trees.py`, then `--check`. Never hand-edit `claude-code/`, `cursor/`, `codex/`, or plugin trees.
- **Verification.** `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` (outside any sandbox) after each story.

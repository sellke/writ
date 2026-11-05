# Recommendation Log: 2026-10-25-design-divergence

> Mode: `/create-spec --recommend`, source mode `standard`
> Date: 2026-10-25
> Seed: approved Phase 15 decomposition (roadmap § Phase 15, ADR-030, pstack research F3, prototype research Recommendation 2)

Each entry: decision, evidence, material alternatives, risk and reversibility, result.

## D1. Feature selection

- **Decision:** Author the "design-divergence skill and the usage-first Gate 0" feature, including the blind trial, as one spec.
- **Evidence:** The seed names the idea. Roadmap Phase 15 lists it as one feature (`Effort: M`, "includes the blind trial").
- **Alternatives:** Split the trial into its own spec. Rejected: the roadmap bundles them and the trial decides whether the skill stays.
- **Risk / reversibility:** Low. A split can be done with `/edit-spec`.
- **Result:** Adopted.

## D2. Contract lock

- **Decision:** Auto-lock the contract in `spec.md` → Specification Contract.
- **Evidence:** Roadmap Phase 15 success criteria for Design divergence and Divergence trial; ADR-030's Take table (`architect`: caller usage first, two independent sketches) and Review section; the existing `commands/prototype.md` Step 2.5 text; the Gate 0 section of `commands/implement-story.md`; test pins found in `scripts/tests/test_platform_neutral_names.py`, `scripts/tests/test_implement_story_default_path.py`, and `scripts/tests/test_governor_enforcement.py`.
- **Alternatives:** none material; the seed fixed scope, owned files, and forbidden files.
- **Risk / reversibility:** Medium; the human-gated trial is the main uncertainty. Reversible with `/edit-spec`.
- **Result:** Locked.

## D3. Meaning of "the boundary-crossing route" at Gate 0

- **Decision:** Gate 0 predicts the Gate 3 route by running `boundary-map.py compute`, `change-surface.py classify`, and `boundary-map.py crossings` over Gate 0's existing `--planned` file set. Divergence runs on predicted `route: review-agent`, and also on `--full-pipeline` and `--panel`.
- **Evidence:** `gate3_route` is computed at Gate 2.5, after code exists. ADR-030 defines high-stakes routes as "`gate3_route` names review-agent, or `--panel`"; `--full-pipeline` always spawns `review-agent`. `change-surface.py classify` works on paths that do not exist yet (checked: `src/new/thing.ts api/routes/x.py` → `full-stack`).
- **Alternatives:** (a) Run divergence on every Gate 0. Rejected: ADR-023 stakes-proportional and ADR-030's cost mitigation. (b) Add a new predictor script. Rejected: the existing scripts already give the answer. (c) Move Gate 0.5 before Gate 0. Rejected: edits a section this spec does not own.
- **Risk / reversibility:** Planned files come from the story's own tasks, so crossings appear mostly via overlap data or a full-stack surface. That targets API, schema, migration, and auth work, which is where the research says divergence matters beyond UI. Reversible by editing one paragraph.
- **Result:** Adopted.

## D4. The named on/off switch

- **Decision:** `.writ/config.md` line `- **Gate 0 Divergence:** on|off` under `## Conventions`. Absent means on; any value other than `on`/`off` means off with a reason line. Documented in `.writ/docs/config-format.md`. Only Gate 0 reads it.
- **Evidence:** The seam with `2026-10-25-gate-upgrade-removal-measurement` needs one switch a trial can flip. `.writ/config.md` already carries opt-in lines in this shape (`Review Panel`, `Judgment Provider`).
- **Alternatives:** (a) An `/implement-story` flag. Rejected: `/implement-spec` and `/implement-phase` would have to pass it through. (b) Default off. Rejected: Gate 0 would not be a live caller in practice, failing the "two live callers" criterion.
- **Risk / reversibility:** Prose-read, not script-read; pinned by wiring tests on the literal. Easy to remove.
- **Result:** Adopted. `.writ/docs/config-format.md` is outside the seed's owned list; it is added because a config line without its doc entry would be undocumented.

## D5. How the chosen sketch reaches Gate 1

- **Decision:** Append it to the Gate 0 warnings that Gate 1 already receives, labeled `design sketch (Gate 0 divergence)`.
- **Evidence:** Gate 1 text: "with full story context, optional `knowledge_context`, any arch-check warnings". The seed limits edits to the Gate 0 section.
- **Alternatives:** A new `design_sketch` input on Gate 1 and `agents/coding-agent.md`. Rejected: outside owned sections and files.
- **Risk / reversibility:** The coding agent may weight a "warning" differently than a design. Low; the label states what it is.
- **Result:** Adopted.

## D6. No change to `agents/architecture-check-agent.md`

- **Decision:** Leave the agent file alone. Gate 0's orchestrator writes the usage and spawns two plain read-only sketch subagents.
- **Evidence:** The agent is a floor-tier, read-only verdict agent whose exit criteria are one ARCH_CHECK verdict. Default Gate 0 does not spawn it at all. `test_implement_story_default_path.py` forbids an unguarded `> **Agent:**` marker in Gate 0.
- **Alternatives:** Extend the agent to produce sketches. Rejected: mixes a verdict with a design job and would only run on `--full-pipeline`.
- **Risk / reversibility:** Low.
- **Result:** Adopted.

## D7. Sketch tier and count

- **Decision:** Two sketches, `anchor` tier, one message, `readonly`.
- **Evidence:** Roadmap: "two independent sketches". ADR-024 keeps tiers family-locked; sketches are design judgment and run only on high-stakes routes.
- **Alternatives:** `floor` to save cost. Rejected: two spawns per qualifying story is small, and a weak sketch defeats the purpose. Three sketches: rejected, the roadmap says two.
- **Risk / reversibility:** Cost per qualifying story. One word to change.
- **Result:** Adopted.

## D8. Never blocking

- **Decision:** No divergence outcome fails Gate 0, marks DEGRADED, asks the user, retries, or counts toward `review_cycle`. A failed sketch skips divergence.
- **Evidence:** ADR-030 frames these as upgrades judged later by a removal measurement. The completeness and worktree notes name Gate 0 only beside `--full-pipeline` (pinned), so Gate 0 handles partial sketches itself.
- **Alternatives:** Retry once at a higher tier (the ADR-024 pattern). Rejected: adds a loop for advisory output.
- **Risk / reversibility:** Low.
- **Result:** Adopted.

## D9. Gate 0 edits outside the `#### Gate 0` heading

- **Decision:** Also edit Gate 0's own Pipeline row, the Overview default-spawn clause, and the References skills line. Nothing in Gate 0.5–Gate 5.
- **Evidence:** The Pipeline table says "The Skill column names what a stage loads". The Overview says the default is two Task spawns, which the upgrade changes on its route.
- **Alternatives:** Leave them stale. Rejected: the file would contradict itself.
- **Risk / reversibility:** Low. Story 3 AC-3.4 pins that nothing else changes.
- **Result:** Adopted.

## D10. Byte budget

- **Decision:** Gate 0 block under 2,000 bytes; re-pin the `"commands/implement-story.md"` ratchet (11266) with a dated disclosure.
- **Evidence:** `commands/implement-story.md` is 36,226 bytes against a 24,960 budget; the ratchet is exact.
- **Alternatives:** Offset by cutting other sections. Rejected: those sections are not owned.
- **Risk / reversibility:** Sibling Phase 15 specs re-pin the same entry. Whichever lands second re-pins from the first.
- **Result:** Adopted. First drafted at 1,500 bytes; raised to 2,000 after counting the required literals (three commands, seven report states).

## D11. Trial pattern

- **Decision:** Reuse the Phase 12 panel-trial pattern (`.writ/specs/archive/2026-10-01-cross-family-review-panel/` Stories 4–5): a schema-tagged trial file, one subcommand per step, an outcome test that does not import the harness, record committed before any removal, a caveat line. New script `scripts/divergence-trial.py`.
- **Evidence:** That trial ran and was acted on (`trial-report.md`: keep). `scripts/jev-judge.py` was checked: it is a judgment provider with calibration against gold labels, not a blind human-rating harness, and the seed requires a human rater.
- **Alternatives:** (a) Add subcommands to `review-panel.py`. Rejected: unrelated concern. (b) Use Jev as rater. Rejected: the seed requires human judgment.
- **Risk / reversibility:** Low.
- **Result:** Adopted.

## D12. Trial design and decision rule

- **Decision:** Six briefs, two each of UI, API, data model. Both arms at the same tier. Per brief the rater gives a distinct-structure count (1–3) per set, which set is more distinct (or tie), whether render-only drafts were enough, and a note. `keep` iff axes win on ≥4 of 6 briefs and total distinct count is higher; ties are not wins.
- **Evidence:** Roadmap: "rated blind for structural distinctness... The skill stays only if declared axes win." Prototype research Risks table: "have a human rate structural distinctness blind."
- **Alternatives:** One concept (as the research first suggested). Rejected: a single brief cannot cover three media. Majority with ties split. Rejected: the burden of proof sits on the added surface.
- **Risk / reversibility:** Small sample, one rater. The report carries a caveat line.
- **Result:** Adopted.

## D13. Brief sources

- **Decision:** All six briefs describe Writ's own surfaces (Phase 15 and 16 roadmap items and Writ pages). No briefs from the Phase 11 baseline (yuss) stories.
- **Evidence:** Trial drafts and the sheet are committed. The panel trial kept yuss-derived text out of committed files.
- **Alternatives:** Use the yuss baseline stories. Rejected: committing their product descriptions to this repository.
- **Risk / reversibility:** Writ has little UI, so the two UI briefs are Writ pages (spec progress, exploration record viewer). Briefs can be swapped before Story 5 runs.
- **Result:** Adopted.

## D14. Blinding is honor-system; key and raw drafts committed

- **Decision:** Commit `key.json` and raw drafts so they survive a lane worktree. The rater opens only `rating-sheet.md`. UI drafts render after blinding, from blinded text. `rate` verifies the draft text did not change; `report` verifies the key did not change.
- **Evidence:** `.writ/state/` is gitignored and lanes run in `.writ-lanes-*` worktrees, so uncommitted files can be lost before a human rates.
- **Alternatives:** Keep the key in `.writ/state/`. Rejected: may be lost. Encrypt the key. Rejected: ceremony for a one-rater trial.
- **Risk / reversibility:** The rater could look. The report states the blinding method.
- **Result:** Adopted.

## D15. Human-gated verdict

- **Decision:** Story 5 ends at `rating-handoff.md` with `report` printing `unverifiable` / `unrated` and spec status `In Progress — awaiting blind rating (rating-handoff.md)`. Story 6 starts only after a human fills the sheet and runs `rate`.
- **Evidence:** Seed: "make the keep/remove outcome a recorded handoff — never self-certified."
- **Alternatives:** Let the lane rate. Rejected by the seed.
- **Risk / reversibility:** `/implement-spec` may reach Story 6 early; Story 6 task 6.1 stops and reports.
- **Result:** Adopted.

## D16. Harness deleted after the verdict

- **Decision:** Delete `scripts/divergence-trial.py`, its unit tests, and fixtures after the report is committed, on either verdict.
- **Evidence:** Roadmap Design Principle 7 (subtract before you add). The harness has no consumer after the report. The committed trial file, sheet, key, raw drafts, and `trial-report.md` are the record; git history keeps the script.
- **Alternatives:** Keep it (the panel kept its harness on `keep`). Rejected: the panel's harness shared a file with live code; this one does not.
- **Risk / reversibility:** Restorable from git.
- **Result:** Adopted.

## D17. Removal scope on `remove`

- **Decision:** Remove the skill, the Gate 0 upgrade, the switch, and `/prototype`'s axes procedure (Step 2.5 falls back to "ask for up to three drafts and state what each commits to"). File an improvement issue for `commands/create-spec.md` Step 0's "declared axes" wording instead of editing that file.
- **Evidence:** Prototype research: "If the axes version does not win, drop to Option E." `commands/create-spec.md` is outside this spec's owned files.
- **Alternatives:** Keep `/prototype`'s inline rules on `remove`. Rejected: the trial would have shown they do not help.
- **Risk / reversibility:** The `/prototype` exit criterion wording changes on `remove`; pinned tests must be checked then.
- **Result:** Adopted.

## D18. Story decomposition and sub-specs

- **Decision:** Six stories (skill; `/prototype`; Gate 0 and switch; harness; trial inputs and handoff; verdict). Sub-specs: `technical-spec.md` only, including an Error & Rescue Map because the harness writes files.
- **Evidence:** File ownership splits cleanly per story; Stories 2 and 3 touch different command files. No database, HTTP API, or UI is built.
- **Alternatives:** Merge Stories 4 and 5. Rejected: harness code and trial execution have different reviewers and failure modes (the panel trial split them the same way).
- **Risk / reversibility:** Low.
- **Result:** Adopted.

## D19. Visual references

- **Decision:** `none`. Empty `mockups/`.
- **Evidence:** The spec builds markdown and scripts. `/prototype`'s rendering is delegated to the platform and unchanged here.
- **Result:** Adopted.

## D20. Cross-vendor drafting

- **Decision:** The skill states that drafts come from the session's model family.
- **Evidence:** The prototype research suggested "cross-family where available"; the seed puts cross-vendor routing (ADR-024) and always-on panels out of scope.
- **Result:** Adopted.

## D21. Cross-spec overlap

- **Decision:** Advisory note only; no blocking conflict.
- **Evidence:** Every pre-Phase-15 spec folder under `.writ/specs/` resolves complete via `scripts/spec-status.py is-complete`. Four Phase 15 siblings appeared on disk during authoring (`repro-first-bug-fixing`, `review-route-rigor`, `why-command`, `retro-fix-ladder`); their spec-lite files name different sections of the shared files and two list this spec's areas as do-not-touch. Shared hot spots: the implement-story ratchet entry, the manifest `skills:` list, README, and regenerated trees.
- **Result:** Recorded in `spec.md` → Cross-Spec Overlap.

## D22. Shared files not written during authoring

- **Decision:** Did not edit `.writ/product/roadmap.md`, ADR-030, `.writ/manifest.yaml`, `.writ/docs/config-format.md`, or any product file. Story 6 plans the roadmap and ADR-030 edits for the implementation lane.
- **Evidence:** Run constraint: write only inside this spec folder.
- **Result:** Adopted.

## D23. Spec analysis (Step 2.6c)

- **Decision:** Ran `jev-judge.py spec-findings` (status `pass`, vercel-gateway) with output in the session scratchpad, not `.writ/state/`, to keep this run's writes inside the spec folder. Jev judged 0 stories and escalated all 6, so the orchestrator pass covered every story. Merged findings: Jev `gap` on Stories 5 and 6 (p 0.77, 0.76); orchestrator `ambiguity` on Story 3 (seven report states vs the byte cap) and `gap` on Story 6 (a `remove` verdict after the removal-measurement spec already deleted the Gate 0 block). `spec-analyze.py check` → `pass`.
- **Actions:** Story 5 gained a note on regenerating a refused or failed draft once; the byte cap rose from 1,500 to 2,000 (D10). The Story 6 gap stays a note: Story 6's Notes already cover a prior Gate 0 removal for `keep`; the `remove` case reduces to no-ops plus a re-pin from the value present at execution time.
- **Result:** Advisory notes only; no gate.

## D24. Malformed switch value reads as on (orchestrator amendment, 2026-10-25)

- **Decision:** A `Gate 0 Divergence` value other than `on` / `off` now reads as **on** with `gate0-divergence: on (malformed: <value>)`, replacing the earlier "off" rule.
- **Evidence:** The sibling Phase 15 switches (`Repro First` in `2026-10-25-repro-first-bug-fixing`, `Safety Fact` and `Reviewer Filters` in `2026-10-25-review-route-rigor`) all read a malformed value as on. `review-route-rigor` flagged the disagreement. One rule across the four switches lets `2026-10-25-gate-upgrade-removal-measurement` toggle them the same way, and a typo never silently disables a check.
- **Applied by:** `/implement-phase` orchestrator before any lane opened; spec.md State Catalog and Business Rule 1, spec-lite.md, technical-spec error map, Story 3 AC-3.2.

## D25. Trial harness is dev-only (orchestrator amendment, 2026-10-25)

- **Decision:** `scripts/divergence-trial.py` is listed in every dev-only script list (as `pipeline-baseline.py` is) so it never ships to installed projects; Story 6 removes those entries with the harness.
- **Evidence:** The `2026-10-25-gate-upgrade-removal-measurement` author found that a new `scripts/*.py` ships by default (`is_shippable_script` in `scripts/gen-platform-trees.py` and `scripts/install.sh`) and would then need an agent CLI contract row; this spec named neither.
- **Applied by:** `/implement-phase` orchestrator before any lane opened; technical spec § Trial Harness, Story 4 and Story 6 Notes.

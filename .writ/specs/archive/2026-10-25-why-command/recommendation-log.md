# Recommendation Log: Why Command

> Spec: [`spec.md`](spec.md)
> Mode: `/create-spec --recommend`, source mode `standard`
> Authored: 2026-10-25, on branch `phase/15-code-level-rigor` at `7f7f991`

Each entry records one decision `--recommend` adopted without a human gate: the decision, its evidence, the alternatives weighed, risk and reversibility, and the result.

## R1. Feature selection

- **Decision:** Author `/why` as one spec with the id `2026-10-25-why-command`.
- **Evidence:** Phase 15 decomposition seed; `.writ/product/roadmap.md` § Phase 15 → Features (`/why`, Effort M) and Success Criteria (`/why` bullets); ADR-030 "What Writ takes from pstack" row for `why`; research F4.
- **Alternatives:** None. The invocation supplied the idea.
- **Risk / reversibility:** None.
- **Result:** Adopted.

## R2. Contract lock

- **Decision:** Auto-lock the contract in spec.md → Specification Contract.
- **Evidence:** Every Must Include traces to the roadmap's three `/why` success criteria, ADR-030's take-and-decline row (take: evidence per source, confidence tiers, Preserve / Change / Avoid / Risk; decline: the seven-source sweep by default), and the seed's owned-file list. The codebase audit in technical-spec.md → Current State grounds every file and count.
- **Alternatives:** Pause for a human lock. Rejected: no requirement conflicts or is infeasible, which are the only pause conditions in `--recommend`.
- **Risk / reversibility:** Low. `/edit-spec` can amend any rule before Story 1 starts.
- **Result:** Locked.

## R3. Where the handoff lives across sessions

- **Decision:** When a change follows, save the answer to `.writ/research/<YYYY-MM-DD>-why-<slug>.md`, ending with the handoff section.
- **Evidence:** `/create-spec` usually runs in a later session than the question, so the section needs a file. `.writ/knowledge/README.md`'s decision tree sends "an investigation that produced specific recommendations" to `.writ/research/`. `scripts/scaffold-writ.py` already creates `.writ/research`. `commands/create-adr.md` already searches `.writ/research/`, so ADR authoring finds why records with no change. `scripts/eval-shipped-refs.py` allows runtime globs under `.writ/research/`.
- **Alternatives:** (a) No file; `/create-spec` reads only the conversation. Rejected: loses the handoff across sessions. (b) A new `.writ/why/` folder. Rejected: needs scaffold, manifest, uninstall, and README directory-tree changes for no extra capability. (c) Save every answer. Rejected: fills `.writ/research/` with records nobody plans to act on.
- **Risk / reversibility:** Low. `/research` records end in `-research.md` and why records start `<date>-why-`, so neither command misreads the other's files. Moving the folder later is a two-file change.
- **Result:** Adopted (spec.md → 📋 Business Rules → Saved record, A change follows).

## R4. The five tiers

- **Decision:** `Recorded`, `Stated`, `Corroborated`, `Inferred`, `Unknown`, defined by the kind of source.
- **Evidence:** Research F4: pstack's `why` uses five tiers, never cites code as evidence of its own intent, and reports null results. Writ's distinct asset is the ledger, so the top tier names it.
- **Alternatives:** pstack's tier names. Rejected: they are not defined in Writ's evidence base, and copying them unverified would cite a source not read. Three tiers (high, medium, low). Rejected: it hides whether the top answer came from the ledger, which is the point of the command.
- **Risk / reversibility:** Medium. Tier names become user-facing vocabulary and are pinned by `test_tiers`. Renaming later is one command file and one test.
- **Result:** Adopted (spec.md → 📋 Business Rules → Five tiers).

## R5. Code comments

- **Decision:** A code comment counts as `Stated` only when written in the same commit as the code it explains; otherwise it is a lead, not evidence.
- **Evidence:** A comment is a person's written statement, but a later comment can rationalize code someone else wrote. The same-commit test is checkable with `git blame`.
- **Alternatives:** Treat all comments as code (never evidence). Rejected: discards the commonest real statement of intent.
- **Risk / reversibility:** Low.
- **Result:** Adopted.

## R6. Git history always runs

- **Decision:** Step 3 runs even when the ledger answered at `Recorded`.
- **Evidence:** A ledger entry can predate later changes to the same code. Git history is local and cheap, and it is the only way to detect a stale entry.
- **Alternatives:** Stop at the first `Recorded` claim. Rejected: reports a decision the code no longer follows.
- **Risk / reversibility:** Low cost; reversible.
- **Result:** Adopted (technical-spec.md → Shadow Paths → Stale ledger).

## R7. MCP gating and the code host's CLI

- **Decision:** Read MCP servers, and the code host's CLI when installed and signed in, only when the strongest claim is below `Stated`. Never prompt to connect or authorize.
- **Evidence:** ADR-030 declines the seven-source sweep by default for cost (ADR-023). PR descriptions are the commonest `Stated` source after commit messages and often live only on the code host.
- **Alternatives:** Always read every connected MCP. Rejected on cost. Exclude the CLI. Rejected: many projects have the CLI and no MCP server.
- **Risk / reversibility:** Low.
- **Result:** Adopted (spec.md → 📋 Business Rules → MCP only when needed).

## R8. No subagents, no helper script, no adapter row

- **Decision:** `/why` runs in the invoking session, with no script and no new adapter row for MCP.
- **Evidence:** ADR-030 declines per-source investigators by default. Tier assignment is a judgment, not something a script re-derives. `commands/prototype.md` and `commands/writ-design.md` already name MCP servers in plain prose, which the vendor scan and unmapped-term check accept.
- **Alternatives:** One investigator per source (pstack). Rejected on cost and ADR-024 tier rules. A `why-sources.py` helper. Rejected: it would wrap three git commands.
- **Risk / reversibility:** Low. A helper can be added if fixture runs show inconsistent source order.
- **Result:** Adopted.

## R9. Front-door route

- **Decision:** The fifth `/writ` row routes `/why`, and its Route cell names `/research` for questions about something outside the project. The table keeps six rows.
- **Evidence:** The seed says switch the row to `/why`. `/research` is external-first (its exit criteria require source URLs). `scripts/tests/test_front_door.py` pins six rows in order. Removing `/research` from the table entirely would leave it offerable only through "Not what I meant".
- **Alternatives:** A seventh row for external questions. Rejected: changes the pinned row count and the front-door contract's shape for a distinction one cell can carry.
- **Risk / reversibility:** Low.
- **Result:** Adopted (spec.md → 📋 Business Rules → Front-door route).

## R10. Prompting guide added to owned files

- **Decision:** Story 3 also edits the route line in `.writ/docs/prompting-guide.md` § A why or how question and `scripts/tests/test_prompting_guide.py`.
- **Evidence:** The line reads "`/research` (`/why` replaces it when it ships)". `/writ` Step 1 cites the guide. Leaving it contradicts the front door the day `/why` ships. The file is not on the seed's do-not-touch list.
- **Alternatives:** Leave it for a later cleanup. Rejected: Design Principle 7 (subtract before you add) applies to interim text this spec makes stale.
- **Risk / reversibility:** Low.
- **Result:** Adopted.

## R11. `/create-spec` Step 1.2

- **Decision:** A new `#### Step 1.2: Read a `/why` Handoff` between Step 1.1 and Step 1.3, standard flow only, mapping Preserve → Business Rules, Change → Deliverable, Avoid → Scope Boundaries → Excluded, Risk → Technical Concerns.
- **Evidence:** Phase 1 has no Step 1.2 today, so the number is free and no later step renumbers. The four targets are existing contract sections in Step 1.4. `--from-issue` and `--from-prototype` replace Phase 1 and are outside the seed's scope.
- **Alternatives:** Fold the read into Step 1.1. Rejected: the seam test needs a heading to anchor on. Add it to all three modes. Rejected: grows the tree's largest command three times for a path with no evidence of use yet.
- **Risk / reversibility:** Low.
- **Result:** Adopted (technical-spec.md → `/create-spec` Step 1.2).

## R12. `commands/create-spec.md` byte budget

- **Decision:** Keep Step 1.2 under 700 bytes and re-pin `KNOWN_OVER_BUDGET["commands/create-spec.md"]` with a dated disclosure comment.
- **Evidence:** The file is 38,614 bytes, 13,654 over the 24,960-byte budget, and `test_no_command_acquires_a_new_or_larger_budget_violation` fails on any growth. Every earlier growth in that dict's comments was re-pinned with a disclosure.
- **Alternatives:** Offset by trimming other steps. Rejected: touches create-spec content outside this spec's ownership while sibling specs are in flight.
- **Risk / reversibility:** Low. The ratchet stays exact.
- **Result:** Adopted (Story 4, AC-4.3).

## R13. Story decomposition and order

- **Decision:** Four stories: command file; registration and catalogs; front-door route; create-spec handoff. Order 1 → 2 → {3, 4}; Story 3 depends on Story 2.
- **Evidence:** The front-door spec used the same command / registration / follow-on split and shipped clean. Stories 2 and 3 both edit `scripts/tests/test_front_door.py` (`CURSOR_COUNT`, `ROUTES`), so they serialize. Every story that edits a `commands/*.md` file must regenerate the plugin trees, so registration lands before the two command edits. Stories 3 and 4 share no source file. `story-deps.py validate` returns batches `[story-1] [story-2] [story-3, story-4]`.
- **Alternatives:** Registration inside Story 1. Rejected: over seven tasks. Story 3 before Story 2. Rejected: the route would point at an unregistered command.
- **Risk / reversibility:** `check_manifest` and the generated-tree check fail between Story 1 and Story 2; recorded in Story 1's notes and the README.
- **Result:** Adopted.

## R14. Sub-spec set and visual references

- **Decision:** `technical-spec.md` only, with an Error & Rescue Map and Shadow Paths. Visual references: `none`; `mockups/` is empty.
- **Evidence:** The command reads git and external MCP servers, which create-spec Step 2.8 counts as external integrations. No database, API, or UI surface.
- **Alternatives:** None material.
- **Risk / reversibility:** None.
- **Result:** Adopted.

## R15. Registration surfaces

- **Decision:** The surfaces in technical-spec.md → Registration Edits. The repository's `CLAUDE.md` and `AGENTS.md` are not edited.
- **Evidence:** Surfaces found by searching for an existing command name (`writ-design`) across the product. Neither repository instruction file lists commands; the commands table the seed referred to sits in a parent directory's `CLAUDE.md`, outside this repository. Category `planning` matches `/research`, its neighbour.
- **Alternatives:** Category `learning`. Rejected: `/why` feeds planning, and `learning` holds `/retro`.
- **Risk / reversibility:** Low. `test_registration` pins each surface.
- **Result:** Adopted.

## R16. No supersession banner

- **Decision:** No `Amends:` or `Extends:` line; Step 2.4b does not run.
- **Evidence:** The front-door contract (Must Include 1) already says the why-or-how route goes to `/research` "until `/why` ships, with the swap recorded in the command". This spec performs that anticipated swap; it does not replace the front-door contract.
- **Alternatives:** `Extends: 2026-10-22-front-door`. Rejected: would write a reverse pointer into a completed spec for a change its own contract foresaw.
- **Risk / reversibility:** Low. A banner can be added with `/edit-spec`.
- **Result:** Adopted.

## R17. Entry level

- **Decision:** `entry_level: high`.
- **Evidence:** Q1 of the derivation in `commands/new-command.md`: the command renders an unverified judgment the user acts on, like `/research`.
- **Result:** Adopted.

## R18. Proof of the seam

- **Decision:** A four-question dogfood fixture against Writ's own history, the fourth carried through `/create-spec` Steps 1.1–1.2 in Plan Mode with no spec files written.
- **Evidence:** Each expected source was located during the audit: `.writ/specs/2026-10-20-platform-neutral-names/` and `.writ/issues/bugs/2026-10-19-design-command-name-collision.md`; ADR-030's friction-signals retirement; front-door DEV-003; front-door Business Rule 4 and DEV-007.
- **Alternatives:** Structural tests only. Rejected: they cannot show that the tiers come out right or that the handoff reaches a contract.
- **Risk / reversibility:** The fixture run writes one real why record under `.writ/research/`, kept as evidence.
- **Result:** Adopted.

## R19. Process deviations in this run

- **Story files written inline.** Step 2.6 spawns floor-tier story generators. This run was itself a delegated agent instructed to do the work directly, so it wrote the four stories from the template in `agents/user-story-generator.md`. Step 2.6a's checks pass on all four (3–5 criteria, 5–7 tasks, marker equals highest ID, every ID cited); `ac-trace.py` reports 0 findings; `story-context.py assemble` resolves every hint with no warnings.
- **Analysis output outside `.writ/state/`.** Step 2.6c writes its findings JSON under `.writ/state/`. This run was limited to writing inside the spec folder, so the files went to the session scratchpad. Nothing under `.writ/state/` was written.
- **Jev findings.** The first Jev pass flagged nil/empty/error gaps in Stories 3 and 4. Story 4's was real: AC-4.1 now requires the skip-when-none-found sentence. The orchestrator pass over the escalated Stories 1, 2, and 4 found Story 1's degradations untested; AC-1.3 now covers them. The re-run flags only Story 3. Dismissed: Story 3 changes one routing row, and `/writ` Step 1 owns the nil and missing-subject cases, unchanged by this spec.

## R20. Cross-spec overlap (advisory)

- **Finding:** Sibling Phase 15 specs authored at the same time touch shared files. `2026-10-25-design-divergence` adds a skill (`.writ/manifest.yaml`, `SKILL.md`, `README.md`) and re-pins `KNOWN_OVER_BUDGET["commands/implement-story.md"]`. `2026-10-25-review-route-rigor` touches `.writ/manifest.yaml` and `README.md`. All four siblings regenerate trees with `gen-platform-trees.py`.
- **Decision:** No dependency declared. The edits are on different keys and lines; generated files are resolved by regenerating after merge.
- **Risk / reversibility:** Merge conflicts in `SKILL.md` and the plugin trees when lanes land in sequence. Resolution is a regeneration, not a hand merge.
- **Result:** Advisory note only.

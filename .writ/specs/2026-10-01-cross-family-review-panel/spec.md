# Cross-Family Review Panel

> **Status:** In Progress
> **Created:** 2026-10-01
> **Owner:** @unknown
> **Dependencies:** []
> **Phase:** 12 — Behavioral Verification (Feature 3)
> **Amends:** [adr-028-behavioral-verification-and-cross-family-panels](../../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md) Decision 3
> **Origin:** `/create-spec` discovery, 2026-10-01. ADR-028 Decision 3 says a finding raised by two or more vendors blocks and a finding raised by one is advisory. Read literally, with the session's own Gate 3 agent counted as one vendor, that rule would demote today's solo evaluator FAIL to advisory — a weakening that contradicts the same ADR's Decision 4 ("every failure falls back to today's path"). Discovery made the panel **additive**: today's Gate 3 verdict is untouched and the panel can only add blocks. Discovery also named the mechanical stakes signal ADR-023's triage lacks (Gate 2.5's existing `gate3_route`), and replaced a baseline replay with a retrospective trial, because the Phase 11 baseline runs were driven through Claude Code (where the panel cannot run) and recorded Gate 3's verdict but not its findings.

## Specification Contract

**Deliverable:** On stories that Gate 2.5 routes as risky (or that are forced with `--panel`), Gate 3 adds one to three reviewers from other vendors. A script counts their findings across vendors. A finding raised by two or more vendors blocks the story; a finding raised by one is a note. A retrospective trial on the four Phase 11 baseline stories then decides whether the panel stays or is removed.

**Must Include:** Today's Gate 3 verdict is never weakened. The session's Gate 3 agent and `review-override.py` keep deciding exactly as they do now; the panel can only add blocks.

**Hardest Constraint:** Finding agreement across vendors has to be counted by code from free-text reviews. That needs a strict tagged output format and a matching rule that errs toward visible, recoverable false blocks.

**🎯 Experience Design:**
- **Entry point:** a project adds `- **Review Panel:** gpt-5.6-sol-medium, cursor-grok-4.6-medium-fast` to `.writ/config.md`. With no line, nothing changes.
- **Happy path:** `gate3_route` names `review-agent` (or `--panel` is passed) → the primary Gate 3 agent and the panel reviewers spawn in one parallel message with the same prompt → `review-panel.py tally` prints one line per consensus finding plus advisory notes → Gate 3 continues.
- **Moment of truth:** `review-panel: block — AC-2.3 unmet (anthropic, openai)`, a finding the session's own model passed.
- **Feedback model:** every line starts with `review-panel:`: `off`, `skipped`, `pass`, `advisory`, or `block`, with vendors named.
- **Error experience:** a rejected slug, a reviewer with the same vendor as the session, an unknown vendor, a reviewer timeout, or malformed output drops that reviewer with one line. If no other-vendor reviewer is left, it prints `review-panel: skipped — <reason>` and Gate 3 runs as today. The story is never marked DEGRADED for this.

**📋 Business Rules:**
1. **Opt-in.** The config line is the only switch, and it is also the consent to send story content to other vendors. `none`, or no line, means off.
2. **Who reviews.** The vendor comes from a fixed slug-prefix table in the script. Reviewers from the session's vendor, or with an unknown prefix, are dropped. At most 3 reviewers (Cursor runs 4 concurrent Tasks, including the primary).
3. **Trigger.** The panel runs only when `gate3_route` = `review-agent`, or with `--panel`. It never runs under `--quick`. `--review-only` runs it only with `--panel`.
4. **Same prompt.** Each panel reviewer gets the primary Gate 3 agent's prompt and inputs unchanged (evaluator or review-agent), read-only, at its configured slug. It is a verdict source, not a tier (ADR-024 Decision 3 is untouched).
5. **Matching.** Two findings are the same finding when they name the same unmet `[AC-N.M]`, or the same file in the same residual category (security or architecture) at Critical or Major severity. The primary agent counts as one vendor.
6. **Authority.** A consensus finding blocks: Gate 1 recode, counted in the shared 3-iteration review loop. One-vendor panel findings go into the story report as notes. The primary agent's FAIL or PAUSE and `review-override.py` behave exactly as they do today.
7. **Platforms.** The panel is available on Cursor. Claude Code and Codex print `review-panel: skipped — platform cannot spawn other vendors`. OpenClaw's behavior is stated in its adapter.
8. **Removal rule.** The maintainer runs the trial in Cursor: the single evaluator vs the evaluator plus the panel, over the 4 baseline stories' historical commits. yuss.app is read-only, and the trial file stores paths, IDs, and labels, never source code. The maintainer labels each panel-only finding valid or invalid against the story's ACs, and `review-panel.py trial-report` decides. At least one valid panel-only finding means keep. Zero means the spec closes `Closed — Not Implemented` and the Gate 3 panel path and its config line are removed.

**Success Criteria:** `review-panel.py` (`status`, `tally`, `trial-report`) runs on Python 3.9+ stdlib only, has a pytest file, and is wired into an `eval.sh` check. Mutation tests prove that a single-vendor finding never blocks and a two-vendor AC finding always does. Gate 3 prose in `implement-story.md` and its `.lean` twin is pinned by `require_literal`. Leaving the config line out produces byte-identical Gate 3 behavior. The trial report is committed, and its verdict is acted on.

**Scope Boundaries:**
- **Included:** config line and `status`; tally and matching rule; Gate 3 wiring and the `--panel` flag; adapter platform rows; amendment to ADR-028 Decision 3 (additive authority, `gate3_route` as the stakes signal); trial harness, labeling, report, and the keep-or-remove outcome.
- **Excluded:** a panel at any gate other than Gate 3; making the panel default-on; replacing the evaluator; panels on Claude Code or Codex; semantic or LLM-based finding matching; a full `/implement-story` replay; raising the autonomy ceiling.

**Stories:**
1. Panel config, vendor table, `status`, and the ADR-028 / adapter amendments
2. `tally`: tagged-output parser, matching rule, verdicts, and mutation tests
3. Gate 3 wiring in `implement-story.md` and `.lean`, `--panel`, fallback lines, eval pins, and byte-ratchet disclosure
4. Trial harness and `trial-report`
5. Run the trial and act on the verdict (keep, or close and remove)

**⚠️ Technical Concerns:**
- **Path exclusions can't be fully enforced.** ADR-028 promised ADR-027's path exclusions, but panel reviewers are read-only agents with file tools. Writ can keep excluded paths out of the prompt and tell reviewers not to open them, but it can't stop them. The ADR amendment will say this plainly.
- **File-plus-category matching can produce false consensus.** Both finding texts are printed, and the cost is capped at one recode within the existing loop cap.
- **The trial is small.** Four stories is a weak sample. The rule only asks for one valid miss, so it is a low bar to keep the panel, not proof that it is worth the cost. The report will say so.
- **Spawn cap.** Panel reviewers reuse the `evaluator-agent` and `review-agent` prompts, so `spawn-cap.py`'s allowed agent names still pass. The panel is not the default path, so "default spawns ≤ 2" stays true.

**⚠️ Cross-Spec Overlap:** `2026-10-01-behavioral-verification` (Not Started) also edits `commands/implement-story.md` (Gate 4.5), its `.lean` twin, the `gates:` frontmatter, and the byte ratchet. The two specs edit different gates and don't depend on each other. Whichever lands second rebases and re-pins the ratchet.

---

## 🎯 Experience Design

### User Journey

1. **Opt in.** The developer adds one line to `.writ/config.md` naming Cursor model slugs from other vendors. `python3 scripts/review-panel.py status --repo . --origin "<session model>"` prints which reviewers are active and which were dropped and why. Nothing else is configured.
2. **A risky story.** `/implement-story` reaches Gate 2.5, and `boundary-map.py crossings` routes Gate 3 to `review-agent` (a boundary crossing or a full-stack surface). Because the panel is on, the orchestrator spawns `review-agent` and each panel reviewer in one message, with the same prompt and inputs, each at its own slug.
3. **Tally.** When all return, the orchestrator runs `review-override.py` on the primary output (unchanged), then `review-panel.py tally` over every output. Consensus findings block; single-vendor panel findings become notes in the story report.
4. **Recode.** A block sends the story to Gate 1 with the consensus findings as the fix list, counting once toward the shared review loop. The next Gate 3 convenes the panel again.
5. **Force it.** The developer can pass `--panel` to convene the panel on a story the route did not flag.
6. **Trial.** Once, the maintainer runs the retrospective trial (Stories 4–5) and acts on its verdict.

### State Catalog

| State | What the developer sees |
|---|---|
| No config line | nothing — Gate 3 is byte-identical to today |
| Config line, story not risky, no `--panel` | `review-panel: off — gate3_route evaluator-agent` |
| Platform cannot spawn other vendors | `review-panel: skipped — platform cannot spawn other vendors` |
| Session vendor unknown | `review-panel: skipped — unknown_session_vendor` |
| Every reviewer dropped | `review-panel: skipped — no_other_vendor (dropped: gpt-x same_vendor, foo-1 unknown_vendor)` |
| Reviewer dropped at spawn or parse | `review-panel: dropped cursor-grok-4.6-medium-fast — slug_rejected` (panel continues with the rest) |
| No consensus, no notes | `review-panel: pass — 3 vendors, 0 consensus findings` |
| Single-vendor notes only | `review-panel: advisory — security:app/api/pay.ts (openai)` per note, then `review-panel: pass — …` |
| Consensus finding | `review-panel: block — AC-2.3 unmet (anthropic, openai)` → Gate 1 recode |

### Interaction Patterns

- No new question. The panel never asks anything; Gate 3.5's existing PAUSE options are the only prompt, unchanged.
- Every line starts with `review-panel:` so it greps cleanly in story reports, next to `gate3-route:`.
- On a block, the recode brief shows each consensus finding with every vendor's own wording, so a false match is visible.

---

## 📋 Business Rules (Expanded)

1. **Config line.** `- **Review Panel:** <slug>[, <slug>…]` in `.writ/config.md` (the `- **Key:** value` format the file already uses). `none` disables. Order is preserved; duplicates are dropped (`duplicate_slug`); slugs after the third kept reviewer are dropped (`over_cap`). Documented in `.writ/docs/config-format.md`.
2. **Vendor table.** A fixed prefix table in `review-panel.py` maps slugs and origin model names to vendors: `claude` → anthropic; `gpt`, `o<digit>` → openai; `grok`, `cursor-grok` → xai; `gemini` → google; `composer` → cursor; `muse` → meta. Unknown prefix → `unknown_vendor`. The table is the only vendor knowledge Writ holds; adding a vendor is a one-line edit with a test.
3. **Session vendor.** Derived from the origin captured at command entry (`system-instructions.md` § Model Tiers), never asked. An origin whose vendor is unknown skips the panel (`unknown_session_vendor`), because a same-vendor reviewer could then fake consensus.
4. **Trigger precedence.** `--quick` → no Gate 3, `--panel` with `--quick` is a usage error. Otherwise the panel runs when `status` is `pass` and either `gate3_route` names `review-agent` or `--panel` is set. `--review-only` has no map, so only `--panel` triggers it there. `--full-pipeline` always routes `review-agent`, so the panel runs there whenever it is configured.
5. **Same prompt, plus one line.** Each reviewer receives the primary agent's prompt and inputs verbatim, `readonly: true`, `model: <slug>`. Panel spawns append one constraint line: do not open files matching `.env*`, `*.pem`, `*.key`, `*secret*`, `*credential*`. This is an instruction, not enforcement; ADR-028's amendment says so.
6. **Tagged output.** Both Gate 3 agents' output formats gain what the tally needs: `agents/review-agent.md` acceptance-criteria checklist lines end with the criterion's `[AC-N.M]` tag (the evaluator already does), and every `Issues Found` entry in both agents carries `- **Category:** criterion | security | architecture | taste`. Mirrors in `claude-code/agents/` and the generated `codex/agents/*.toml` follow.
7. **Finding keys.** `ac:<AC-N.M>` for every unchecked tagged checklist line. `<category>:<path>` for every `Issues Found` entry with Severity Critical or Major and Category security or architecture, where `<path>` is the Location with backticks, leading `./`, and trailing `:line` removed. Everything else (taste, Minor, untagged, no Location) is not keyed and is never counted.
8. **Verdict.** A key raised by two or more distinct vendors is a consensus finding → `block`. A key raised by exactly one **panel** vendor → `advisory`. A key raised only by the primary is not reprinted (the primary's own verdict already governs it). No keys → `pass`. Fewer than one usable panel reviewer → `unverifiable`.
9. **Gate 3 combination.** A panel `block` is a Gate 3 FAIL: it takes the existing recode path, increments `evaluator_fail_count` and the shared review loop **once** even when the primary also failed. When the primary returned PAUSE, Gate 3.5 presents its options as today and lists the block lines; choosing accept still recodes for the consensus findings. `review-override.py` runs on the primary output exactly as today. `--review-only`: a block ends the run, like a FAIL.
10. **Never DEGRADED.** No panel outcome — off, skipped, dropped, unverifiable — marks a story `⚠️ DEGRADED`.
11. **Trial integrity.** The committed trial file holds story IDs, commits, finding keys, vendors, severities, and labels — never source, diff, or story text. Raw reviewer outputs stay under gitignored `.writ/state/panel-trial/`. yuss.app is only read: `git -C <yuss> {rev-parse,show,diff-tree}`, plus a `git fetch` *from* it into a fresh `git init` under `$TMPDIR`, as `pipeline-baseline.py` does. Nothing is written inside the yuss checkout.
12. **Trial verdict.** A panel-only finding is a key raised by at least one panel vendor and not by the evaluator-alone arm. `trial-report` prints `keep` when ≥1 panel-only finding is labeled `valid`, `remove` when every panel-only finding is labeled and none is valid, and `unverifiable` when any finding is unlabeled or any of the four stories has no recorded arm.

---

## Detailed Requirements

- **Script:** `scripts/review-panel.py`, Python ≥3.9 stdlib only, argparse subcommands `status`, `tally`, `trial-init`, `trial-prepare`, `trial-record`, `trial-label`, `trial-report`. One verdict line first (`pass` | `block` | `unverifiable` | `keep` | `remove`), `reason:` lines, a `review-panel:` summary line last; `--json` prints one object. Exit 0 ran (pass, advisory, unverifiable), 1 `block`, 2 usage. Sibling `scripts/tests/test_review_panel.py`.
- **Gate 3 prose:** one paragraph in `commands/implement-story.md` and its `.lean` twin, after the risk-route sentence; the Invocation table gains `--panel`; Step 4 item 8's report list gains the `review-panel:` lines. No new gate, no new `gates:` entry, no new agent file.
- **Eval:** `check_review_panel` in `scripts/eval.sh` (registered in the checks list): helper present, `status` parses, tally fixture probes (consensus fixture exits 1, single-vendor fixture exits 0), `require_literal` pins on the Gate 3 paragraph in both command files and on each adapter's panel row.
- **Ratchet:** re-pin `commands/implement-story.md` in `scripts/tests/test_governor_enforcement.py` with a dated, spec-named disclosure comment; offset with trims where possible.
- **Trial artifacts:** `.writ/eval/panel-trial/2026-10-NN-panel-trial.json` (committed, schema `panel-trial-v1`) and its `trial-report` output appended to the spec folder as `trial-report.md`.

## Implementation Approach

Build bottom-up and keep every new path off by default. Story 1 lands the opt-in (`status`, vendor table, config doc) and the honest ADR and adapter amendments. Story 2 lands the tally and the agent output tags it needs, proven by mutation fixtures. Story 3 is the only story that touches `implement-story.md`, and it does so in one paragraph plus two table cells. Stories 4 and 5 are the measurement: a harness that reuses `pipeline-baseline.py`'s selection and isolation, then one maintainer-run trial whose verdict either leaves the panel in place or removes it. Follow existing script conventions (`review-override.py`, `jev-judge.py`, `boundary-map.py`): verdict-first output, exit codes 0/1/2, a sibling pytest file, an `eval.sh` check function, and `require_literal` pins where command prose cites script behavior. See `sub-specs/technical-spec.md`.

# ADR-025: Friction Signals — Record Locally, Nudge Quietly, Let the Human Send It Upstream

> **Date:** 2026-09-03
> **Status:** Accepted
> **Category:** Framework Architecture
> **Extends:** [ADR-022](adr-022-autonomy-gate-classes.md) (nothing leaves the machine or changes a command without a human gate), [ADR-014](adr-014-skill-lifecycle.md) (three occurrences make a pattern), Phase 7's evidence-bound `/refresh-command`
> **Constrains:** [ADR-017](adr-017-git-notes-audit-channel.md) — not extended; friction is not commit-shaped
> **Deciders:** @AdamSellke
> **Research:** none topic-specific; the evidence is [`2026-08-14-writ-dogfooding-quality-assessment-research.md`](../research/2026-08-14-writ-dogfooding-quality-assessment-research.md) Finding 2 and the current shape of `/refresh-command`

## Decision

**Writ cannot improve on what it never records, and must not act on what a human has not reviewed.** So: every command records the moments it struggled, in one local file, in one line each. At natural pauses Writ says, once, that there is something to look at. A human reviews the clusters and, per cluster, fixes the command locally, sends an Improvement Request upstream, or dismisses it. Nothing is applied automatically. Nothing leaves the machine without the human seeing exactly what will be sent.

1. **One file.** `.writ/state/signals.jsonl` — gitignored (`.writ/state/` already is), append-only, one JSON object per line, written only by `scripts/signal.py`. Commands never hand-author JSON.

2. **Six kinds, and the vocabulary is closed.** Adding a kind requires amending this ADR — that is the guard against the file growing into telemetry.

   | Kind | Meaning | Where it is emitted (v1) |
   |---|---|---|
   | `drift` | A `DEV-NNN` entry of severity **Medium or Large** was logged (Small is cosmetic and is not a signal) | `/implement-story` Gate 3.5 |
   | `gate_exhausted` | A `loop.max_iterations` cap was hit and the pipeline escalated to the human | `/implement-story` review/testing caps; `/implement-phase` terminal quarantine |
   | `blocked` | An agent returned `STATUS: BLOCKED` | `/implement-story` BLOCKED escalation |
   | `override` | The human chose against Writ's recommendation — rejected or modified a Large drift, or answered a `--recommend` pause | `/implement-story` Gate 3.5 Large-drift response; `recommend-state.py` pause resolution |
   | `degraded` | A mechanism fell back: model tier unresolvable, skill file missing, script unavailable, `unverifiable` build/coverage verdict, audit-note write failed | the fallback branch at each of those sites |
   | `escalated` | A `floor`-tier result was re-run at `anchor` ([ADR-024](adr-024-model-delegation.md) Decision 4) | `/create-spec` story regeneration; `/implement-story` Gate 0 ABORT confirmation |

   Line shape (fixed by the script; `detail` is capped at 120 characters and is a factual event, never reasoning or transcript prose):

   ```json
   {"id":"sig-20260903-142211-a3f1","ts":"2026-09-03T14:22:11-05:00","kind":"gate_exhausted","command":"implement-story","spec":"2026-08-14-script-backed-quality-gates","story":5,"ref":"gate-3","detail":"review loop hit 3 iterations; escalated to user","writ":"0.33.0","platform":"cursor"}
   ```

   A seventh line kind, `review`, is a bookkeeping record, not a friction signal: `{"kind":"review","ids":["sig-…"],"disposition":"refreshed|upstreamed|dismissed","ref":"sellke/writ#123"}`. A signal is *unreviewed* until some `review` line names it. One file, no cursor, no second state file.

3. **One nudge.** When **three or more** unreviewed signals exist — three because ADR-014 already fixed that as the count that separates a pattern from a coincidence — `/status` adds one health line and `/implement-phase`'s completion report adds one line, in this exact form and no other: *"Writ recorded N friction signals since the last review (kinds: …). Run `/retro --friction` to review."* At most once per local day, cached the same way the startup update check is. Never blocking, never a question, never in `/implement-story`'s per-story completion (too frequent).

4. **One review, in a command that already exists.** `/retro` gains **Step 5.7: Friction Review** beside its two existing read-only nudges (5.5 knowledge consolidation, 5.6 product drift). `/retro --friction` runs only that step. It clusters unreviewed signals by `kind` + `command`, shows the clusters, and asks per cluster:

   | Option | Recommended when | What happens |
   |---|---|---|
   | **Refresh locally** | cluster is `drift` or `override` — project-specific judgment | Hands off to `/refresh-command <command>` with the signal ids as its Evidence block; disposition `refreshed` on acceptance |
   | **File an Improvement Request** | cluster is `degraded`, `gate_exhausted`, `blocked`, or `escalated` — framework mechanics | Drafts the request (Decision 5), shows it, sends only on explicit confirmation; disposition `upstreamed` with the issue ref |
   | **Dismiss** | — | Disposition `dismissed`, optional one-line note |
   | **Leave for later** | — | No `review` line written |

   The `(Recommended)` label is decided by the kind mapping above — an observable property of the cluster, per the Prime Directive's recommendation semantics — and never by option order.

5. **One upstream path, human-sent.** An Improvement Request is a GitHub issue on `sellke/writ` with label `improvement-request`, created with `gh issue create --repo sellke/writ --label improvement-request --title "<kind>: <command> — <summary>" --body-file <draft>`. The body carries: Writ version, platform, command, the signal lines as a table, *what happened* and *what you expected* (the human fills these in), and an optional one-line suggestion. **Spec and story names are redacted to `<spec>` / `<story>` by default** — a project's feature names are its own — and every `detail` line is shown for editing before anything is sent. If `gh` is missing or unauthenticated, the draft is written to `.writ/issues/improvement-requests/<date>-<slug>.md` with the manual URL printed. The receiving side is `.github/ISSUE_TEMPLATE/improvement-request.yml` in the Writ repo, with the same fields, so hand-filed requests have the same shape.

6. **The evidence bridge.** `/refresh-command`'s Evidence block accepts `Signal: sig-…` (one or more) as an alternative to `Transcript:`. The *Observable signal* field is the line's `detail`; *Affected section* is unchanged. The Evidence Gate, the `refresh-evidence` eval, and the eval Tier 2 check all still apply. This is what makes the loop work on Codex and OpenClaw, where there are no Cursor transcripts to cite, and it is what makes a signal *evidence* rather than a complaint.

7. **Emission is invisible and unbreakable.** Each emission is one line at a site that already exists — the BLOCKED block, the cap-exhaustion `AskQuestion`, the drift-log write, the fallback branch. `signal.py append` always exits 0; a failed append is logged to stderr and the workflow continues. No new question is ever asked to gather a signal.

## Context

### The evidence that the current loop is open

Writ's learning loop is real and it is falsifiable — `/refresh-command` will not apply an amendment without a cited transcript and green evals, and skills earn `proven` from recorded evidence. But it is **pull-based and transcript-bound**. Someone has to decide to run `/refresh-command`, on a particular command, and find a Cursor transcript to cite. Transcripts are local to Cursor, ephemeral, and do not exist on Codex or OpenClaw.

The consequence was measured on 2026-08-14. In yuss.app's drift log, `DEV-004` recorded a build-breaking route collision that "went undetected through Story 1's entire pipeline (Gates 1–5, all passing)" and explicitly recommended adding `next build` to Gate 2. The research doc's verdict: *"That recommendation never propagated to the framework."* The signal existed, in a structured file, with a fix attached. Nothing carried it the last mile — until a human read the drift log weeks later while writing a research report, and a spec followed.

That is the failure this ADR closes, and it defines the bar: the mechanism must catch a DEV-004 *when it happens*, surface it *without being asked*, and make submitting it *cheaper than ignoring it*.

### What the maintainer asked for

> The most simplistic approach to improvement without it becoming overwhelming or overburdening to the development process. We may just have to build in a mechanism with some kind of telemetry that captures drift and/or challenges in the workflow and then prompts users to submit an Improvement Request to Writ.

This ADR is that sentence, made precise. The word *telemetry* is used advisedly: the mission says Writ ships **no telemetry**, meaning nothing phones home. Local capture in the user's own gitignored state is not telemetry in that sense; an issue the user reads and sends is not telemetry in any sense. The line is drawn at Decision 5 and it is a human's hand.

### Why these six kinds and no others

Each kind is a moment where Writ *already knows* it is struggling — it is about to interrupt the human, fall back, log a deviation, or re-spawn. The emission sites are branches that exist today. Nothing is inferred, classified, or scored. Kinds that were considered and left out: *slow* (no timing source inside the harness), *token-heavy* (no token counts are exposed to the agent — see ADR-024 Consequences), *user edited the generated file* (undetectable without a diff watcher, and a diff watcher is exactly the machinery this ADR refuses). If a future site needs a seventh kind, amending this ADR is a paragraph; the friction of doing so is the point.

### Why `/retro` and not a new command

`/retro` is Writ's learning command — *"what patterns emerged"* — and it already hosts two read-only, opt-in nudges of exactly this shape (Steps 5.5 and 5.6). The 2026-07-18 leanness audit flagged `/retro` as *"existence-justification unclear without usage evidence."* A friction review gives it a reason to be run. A thirty-second command with one job would be the wrong trade in a surface that is already measured as heavy.

### Why the human sends it

Three reasons, any one sufficient. **Trust:** a framework that files issues about itself from inside a user's project without asking is a framework people uninstall. **Sample size:** one project produces tens of stories a month; the mechanism surfaces candidates, it does not draw conclusions. **ADR-022:** taste and direction are human gates; whether a friction point is a Writ defect or this project's peculiarity is a judgment.

## Decision Drivers (force-ranked)

1. **Zero added burden on the development loop.** No new questions, no new files to maintain, no blocking. If the mechanism costs a developer attention before they choose to spend it, it has failed.
2. **Closes the DEV-004 gap.** A struggle recorded with a fix attached must reach a human who can act on it without that human going looking.
3. **Human-sent, human-applied.** Mission (no telemetry) and ADR-022 (human gates) both forbid the automatic version.
4. **Portable evidence.** The loop must work where transcripts do not exist.
5. **Cannot grow.** A closed vocabulary and a single file; expansion requires a decision record.

## Considered Options

### A. Leave the loop as it is (transcripts + `/refresh-command` on demand)
- **Pros:** Nothing to build.
- **Cons:** DEV-004. Cursor-only evidence. Pull-only.
- **Risk:** Low per incident, and the incidents accumulate silently — which is the whole problem.

### B. Use the ADR-017 git-notes channel as the signal store
- **Pros:** Durable, travels with the repo, already shipped.
- **Cons:** Notes bind to commits; friction happens between commits and often on work that is never shipped (a quarantined lane, an aborted story). Sync configuration and opt-out semantics are heavier than the signals need. A note is public to everyone who clones; signals are a draft.
- **Risk:** Medium — the mismatch in shape would show up as signals lost on every non-landing path.

### C. Automatic upstream telemetry
- **Pros:** Maximum signal to the maintainer.
- **Cons:** Violates the mission's "no telemetry"; violates ADR-022; and the maintainer would drown — the value is in the human's *what I expected* sentence, not the raw line.
- **Risk:** High — trust, once spent, does not come back.

### D. Automatic improvement (skillopt-style: apply, measure, keep-if-better)
- **Pros:** The compelling version of "self-improving."
- **Cons:** Small samples make "better" unmeasurable; Phase 10's byte metric shows how a proxy goes wrong (ADR-023); ADR-022 reserves command edits for a human. `/refresh-command`'s approve/reject step is already the right shape and is kept.
- **Risk:** High.

### E. A new `/improve` command
- **Pros:** Discoverable.
- **Cons:** A 32nd command for one step, in a surface already measured as heavy, when `/retro` exists to answer "what patterns emerged."
- **Risk:** Low, but the wrong direction.

### F. Local structured signals, quiet nudge, `/retro` review, human-sent Improvement Request — **chosen**
- **Pros:** One script, one file, one line per site. Meets all five drivers. Reuses `/refresh-command`'s evidence gate, `/retro`'s nudge slot, `/status`'s health line, and the update-check's daily cache. Makes the ADR-024 review possible (it needs `escalated` and `degraded` counts).
- **Cons:** One more script to ship and fan out. Emission is a convention each site must honor — pinned by `require_literal` like every other gate wiring, but still prose. Signals are lossy one-liners.
- **Risk:** Low. Worst case is an empty file, which the review date treats as its own finding.

## Decision Outcome

**Option F.** Drivers 3 and 5 reject C and D outright. Driver 4 rejects A. Driver 1 rejects E. B fails on shape, not on principle — ADR-017 stays exactly what it is.

**What is explicitly NOT decided:** any change to `/refresh-command`'s approval flow or eval gate (it gains an evidence *type*, nothing else); any aggregation across projects (a human files one issue at a time; the Writ repo's issue tracker is the corpus); any signal kind beyond the six; any timing or token measurement.

## Worked Example — This Decision, Triaged (ADR-023)

*Where should signals live?* Does the answer change what happens — marginally (one path). How bad if wrong — trivial: move a file. → **Decide, act, record.** Ruled: `.writ/state/signals.jsonl`, because `.writ/state/` is already gitignored and already holds the update-check cache this ADR imitates.

*Should a signal ever leave the machine without a human seeing it?* Does the answer change what happens — yes, a project's internals reach a public tracker. How bad if wrong — irreversible. → **Full rigor, human gate.** Ruled: never. Redact spec and story names by default; show the body; require confirmation.

## Consequences

**Positive**

- The next DEV-004 becomes a `drift` line the moment it is logged, a nudge in `/status` within the day, and a two-minute `/retro --friction` that ends in either a local refresh or an issue with a fix attached.
- `/refresh-command` gains evidence on every platform, not just Cursor.
- ADR-024's tiering bet gets the one number it needs (`escalated` per floor agent) without a cost instrument Writ cannot build.
- The Writ maintainer receives requests shaped by a template, each carrying the human's *expected vs. observed* sentence, which is the part no telemetry could supply.
- `/retro` acquires a reason to exist.

**Negative**

- **Emission is a convention.** An agent that skips the one-line append at a site loses that signal silently. *Mitigation:* every site is pinned by an `eval.sh` `require_literal`, the same protection every other gate wiring has; the review date checks for an implausibly empty file.
- **Signals are one-liners.** A `detail` of 120 characters cannot carry a root cause. *Mitigation:* it does not need to — it carries the pointer (`DEV-004`, `gate-3`, `architecture-check-agent`) and the human adds the sentence that matters.
- **One more runtime script fans out to every installed project.** *Mitigation:* `signal.py` has three subcommands and no dependencies; it rides the existing `install.sh`/`update.sh` runtime fanout from v0.28.0.
- **A gitignored file is lost on a fresh clone.** *Mitigation:* accepted — a signal that was never reviewed on the machine that produced it was never going to be reviewed; the durable artifact is the issue or the refresh-log entry.
- **The nudge can be ignored indefinitely.** *Mitigation:* that is the design. It says its one line once a day and stops. The alternative is the burden the maintainer named.

## Implementation Plan

Single spec, five stories. **Prerequisite:** none. ADR-024 Story 4 calls `signal.py append --kind escalated`; if it lands first the call is a no-op until Story 1 here ships.

| # | Story | Files | Done when |
|---|---|---|---|
| 1 | **The script and its contract** — `scripts/signal.py` with `append` (validates kind, caps `detail` at 120, stamps `id`/`ts`/`writ`/`platform`, always exits 0), `summary --json` (unreviewed count and kinds), `review --ids … --disposition … [--ref …]`. Unit tests. `scripts/eval-signals.py` fixture check registered in `eval.sh`. `.writ/docs/friction-signals.md` documents the line shape and the six kinds. Added to the runtime fanout list. | `scripts/signal.py`, `scripts/tests/test_signal.py`, `scripts/eval-signals.py`, `scripts/eval.sh`, `.writ/docs/friction-signals.md`, `scripts/publish-writ-runtime.sh` / install manifests | `python3 scripts/signal.py append --kind banana …` exits 0 and writes nothing; a valid append round-trips through `summary --json`; `bash scripts/eval.sh` Findings: 0 |
| 2 | **Emission sites** — one `signal.py append` line at each v1 site in the table under Decision 2: `/implement-story` (BLOCKED escalation, review and testing cap exhaustion, Gate 3.5 Medium/Large drift, Gate 3.5 Large-drift reject/modify → `override`, `unverifiable` verdicts in Gates 2 and 4 → `degraded`); `/implement-phase` (terminal quarantine → `gate_exhausted`); `/ship` (audit-note failure → `degraded`); `recommend-state.py` pause resolution → `override`; the model-tier fallback and skill-missing branches → `degraded`. Each pinned by `require_literal`. **Nothing is added to `_preamble.md`** — it sits at its 95-line cap and these are site-specific, not shared. | `commands/implement-story.md`, `commands/implement-phase.md`, `commands/ship.md`, `scripts/recommend-state.py`, `scripts/eval.sh` | A fixture run that forces one BLOCKED and one Large drift produces exactly two signal lines with the right kinds |
| 3 | **The nudge** — `/status` health line and `/implement-phase` completion report each gain the one fixed sentence, shown only when `summary --json` reports ≥ 3 unreviewed and the daily cache (`.writ/state/signals-nudge.json`, `last_nudged_date`) is not today. | `commands/status.md`, `commands/implement-phase.md` | With 3 seeded signals `/status` shows the line once; a second `/status` the same day does not |
| 4 | **The review and the upstream path** — `/retro` Step 5.7 and `--friction`; the per-cluster `AskQuestion` with the kind-driven `(Recommended)` mapping; the Improvement Request draft with redaction and the `gh issue create` confirmation; the offline fallback to `.writ/issues/improvement-requests/`; `.github/ISSUE_TEMPLATE/improvement-request.yml` in the Writ repo with matching fields and the `improvement-request` label. | `commands/retro.md`, `.github/ISSUE_TEMPLATE/improvement-request.yml`, `.writ/docs/friction-signals.md` | One real `/retro --friction` on seeded signals ends in a drafted issue body the user saw before sending, and a `review` line with `disposition: upstreamed` and the issue ref |
| 5 | **The evidence bridge** — `/refresh-command` Phases 3–4 accept `Signal:` in the Evidence block; `eval-refresh-evidence.py` accepts either citation type; `.writ/refresh-log.md` records signal ids; accepted amendments write a `review` line with `disposition: refreshed`. | `commands/refresh-command.md`, `scripts/eval-refresh-evidence.py`, `.writ/docs/refresh-log` format | An amendment citing only a `Signal:` passes the Evidence Gate; one citing neither is rejected with `no evidence` as today |

**Success criteria**

- A forced DEV-004-shaped event (Large drift logged at Gate 3.5) is visible in `/status` within the same day without anyone opening the drift log.
- At least one Improvement Request filed against `sellke/writ` from a `/retro --friction` run, carrying redacted spec names and a human-written *expected vs. observed*.
- At least one `/refresh-command` amendment accepted on `Signal:` evidence alone, on a platform without Cursor transcripts if possible.
- `rg "signal.py append" commands/` matches every v1 site in Decision 2's table and no others.
- Nothing in the development loop asks a new question or blocks on the mechanism — verified by reading every emission site.

**Review date: 2026-12-02** (90 days, aligned with ADR-024). Questions, in order: How many signals were recorded, and of which kinds? How many were reviewed, and with which dispositions? Did any `/refresh-command` cite a signal? Was any Improvement Request filed? **If the file is empty after 90 days of real use, the emission sites are wrong or the mechanism is dead, and this ADR is deprecated honestly rather than left standing.** If signals were recorded and never reviewed, the nudge is too quiet, and that is the one parameter this ADR permits changing without amendment.

## Dissent and Corrections

- **"Simplest" was contested during drafting.** A first sketch had a separate cursor file, a `spawn` kind recording every gate's resolved model, and a new `/improve` command. All three were removed: the cursor became a `review` line in the same file; `spawn` was dropped because it would emit on every gate and drown the six kinds that mean something (its one useful derivative, `escalated`, is kept); the command became a step in `/retro`. What remains is the smallest set that closes DEV-004.
- **The maintainer used the word *telemetry*.** This ADR draws the line at the machine's edge and says so, because the mission does. If the maintainer intended an automatic channel, that is a mission change and belongs in its own record, not in a footnote here.
- **The strongest case against this ADR** is the one ADR-023 already made about itself: an unenforced convention is indistinguishable from no convention, and emission is prose. The answer is the same as for every gate in `/implement-story` — `require_literal` pins and a review date that treats silence as a finding. It is not a mechanical guarantee, and this ADR does not claim one.

## References

- [ADR-024](adr-024-model-delegation.md) — the `escalated` and `degraded` producers, and the consumer of their counts
- [ADR-022](adr-022-autonomy-gate-classes.md) — why sending and applying are human gates
- [ADR-023](adr-023-stakes-proportional-diligence.md) — the triage applied above; the "unenforced convention" objection this ADR inherits
- [ADR-017](adr-017-git-notes-audit-channel.md) — the durable channel deliberately not extended
- [ADR-014](adr-014-skill-lifecycle.md) — the three-occurrence bar the nudge threshold reuses
- [`2026-08-14-writ-dogfooding-quality-assessment-research.md`](../research/2026-08-14-writ-dogfooding-quality-assessment-research.md) — Finding 2, DEV-004, "never propagated to the framework"
- `commands/refresh-command.md` Phases 3–4 — the Evidence block and Evidence Gate this ADR extends
- `commands/retro.md` Steps 5.5–5.6 — the nudge pattern Step 5.7 joins
- `system-instructions.md` § Startup Update Awareness — the daily-cache pattern the nudge reuses
- `.writ/docs/leanness-audit-2026-07-18.md` — `/retro`'s "existence-justification unclear" finding

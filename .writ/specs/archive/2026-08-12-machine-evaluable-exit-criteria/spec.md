# Spec: Machine-Evaluable Exit Criteria

> **Status:** Complete (2026-08-12)
> **Created:** 2026-08-12
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** Investigation of Claude Code 2.1.220's `/goal` command (2026-08-12). `/goal` closes a gap Writ has carried since Phase 10 — declared exit criteria that nothing evaluates — but closes it on one platform, in a way that fights Writ's retained pauses. This spec builds the adapter-neutral half and demotes `/goal` to a thin adapter over it.

## Contract (Locked)

**Deliverable:** `scripts/exit-criteria.py check` — a stop-time gate returning
`met | unmet+reason | impossible+reason` for `/implement-phase` and
`/implement-spec`, backed by additive run-record fields those two commands write,
registered under `scripts/eval.sh`, and wired to `/goal` in
`adapters/claude-code.md`.

**Must include:** The `impossible` verdict, and its mapping to Writ's retained
pauses. A gate that only knows met/unmet will spin against a tripped loop bound
or steamroll a `challenge_required` escalation. `impossible` is the mechanism
that makes a stop-blocking gate compatible with `on_exhaustion: halt_reported`
and the Autonomy Gate Classes — it is not an error path, it is the safety
property.

**Hardest constraint:** Roughly a third of Writ's exit criteria are structurally
unobservable after the fact — temporal, before/after, or report-only. The checker
must distinguish *"the criterion is not met"* from *"this criterion cannot be
observed"* from *"I could not read my own inputs"*. Collapsing those three into
one verdict produces either a gate that never passes or one that passes on
missing evidence.

## Why This Exists

Writ's 31 command files declare **68 `exit_criteria`** between them. Phase 10
made that declaration *mandatory* and *quality-linted*:
`2026-08-11-governor-instrumentation` built the presence checks,
`2026-08-12-governor-enforcement` flipped them to blocking `structural`, and
`scripts/eval-leanness.py` now fails the suite if a command omits the field or
fills it with something that asserts nothing.

**Nothing evaluates them.** The contract is enforced as *text*, never as a
*condition*. A command can stop with its own declared criteria unmet and the only
thing that notices is a human reading the report. `--resume`, quarantine
branches, and the honest completion report are all machinery for cleaning up
*after* that has already happened.

### What `/goal` showed, and why it is not the answer

Claude Code 2.1.220 ships `/goal <condition>`, which registers a session-scoped
prompt-type **Stop hook**. On each stop attempt an evaluator returns met /
not-met+reason / **impossible**+reason; not-met forces the run to continue. It is
precisely the missing mechanism. Three properties disqualify it as *the*
mechanism:

1. **Single-slot.** Registering a goal first removes every existing top-level
   prompt Stop hook. Goals cannot nest, so `/implement-phase` →
   `/implement-spec` → `/implement-story` cannot each hold one — the innermost
   silently destroys the outer, and clears leaving nothing behind.
2. **One platform of four.** `commands/_preamble.md` § Adapter Neutrality: commands
   "must work identically on Cursor, Claude Code, and OpenClaw" and "**do not
   require platform-specific runtime hooks**."
3. **It is pointed at Writ's gates.** Its injected prompt reads: *"treat the
   condition itself as your directive and **do not pause to ask the user what to
   do**. The hook will block stopping until the condition holds."* That is the
   opposite instruction to ADR-013's select-or-pause boundary and ADR-022's
   Autonomy Gate Classes.

The `impossible` verdict is the part worth keeping, and this spec keeps it.

### On Design Principle 4

The roadmap's fourth design principle reads *"**Delegate mechanics, own
contracts** — If the harness does it natively, adapt to it; never re-implement
it."* It is recorded here as considered and answered, so the next reader does not
re-litigate it:

- The harness does this on **one platform of four**. Adapter neutrality is the
  older and stronger constraint, and it is a *contract*, which is the half
  Principle 4 says Writ owns.
- What the harness supplies is an **LLM judgment** over a natural-language
  condition. What this supplies is **predicate evaluation over disk state** — a
  different instrument with a different failure mode. `/goal` remains the
  delivery vehicle on Claude Code (Story 6); it stops being the definition.

No ADR. The reasoning is local to this decision and does not generalize into a
standing rule.

## Verdict Contract

```
python3 scripts/exit-criteria.py check --command implement-phase \
    --state .writ/state/phase-execution-20260812-0200.json

{"verdict": "unmet",
 "command": "implement-phase",
 "criteria": [
   {"id": 1, "verdict": "met",     "evidence": "5/5 specs terminal; 0 quarantine branches off phase"},
   {"id": 2, "verdict": "unmet",   "reason": "2 merged specs lack a populated uat-plan.md"},
   {"id": 3, "verdict": "met",     "evidence": "4 roadmap criteria recorded in exitCriteria[]"},
   {"id": 4, "verdict": "unknown", "reason": "declared unobservable: report is transcript-only"}]}
```

Exit codes: `0` met · `1` unmet · `2` impossible.

### Rollup rules

| Condition | Overall verdict |
|---|---|
| any criterion `impossible` | `impossible` |
| else any criterion `unmet` | `unmet` |
| else only `met` / declared-`unknown` | `met` |
| state file missing, unparseable, or a criterion's inputs unreadable | `impossible` — never `unknown` |

`unknown` is legal **only** for a criterion the Story 1 classification declared
structurally unobservable. Any other unknown is a checker that cannot read its own
inputs, and must halt the loop rather than silently pass it. This is the
distinction the Hardest Constraint names, expressed as code.

### `impossible` triggers

Each is a Writ pause the gate must not override:

- the command's `loop.on_exhaustion: halt_reported` fired (iteration bound reached)
- an unresolved `challenge_required` is recorded in phase state
- a criterion was recorded unachievable and the run is heading to `PARTIALLY COMPLETE`
- `phase-state.py reconcile` reports a state/git mismatch

## Business Rules

1. **Reaching a retained pause satisfies the gate.** Any goal condition wired to
   this checker must be satisfiable by *pausing*, not only by *finishing*.
   Otherwise the hook pushes past the human gates in `commands/_preamble.md`
   § Autonomy Gate Classes. This is why `impossible` exists.
2. **Run-record fields are additive.** `.writ/docs/phase-execution-state-format.md`
   already requires readers to "preserve unknown fields … for future schema minor
   versions." No `schemaVersion` bump. A state file written before this spec reads
   as `unknown`, never `unmet` — absent evidence is not failing evidence.
3. **The checker never writes.** Read-only over `.writ/state/`, spec folders, and
   git. Verdicts are returned, never persisted. A gate that mutates the state it
   judges cannot be trusted on re-run.
4. **Prose and predicate are bound.** Each predicate cites the criterion text it
   evaluates, and `scripts/eval.sh` asserts the two agree. This is the
   transcription-drift failure `scripts/eval-loop-bounds.py` assertion 8 already
   exists to catch, applied to a second pair of records.
5. **Classification precedes implementation.** Story 3 implements only what
   Story 1 classified. A predicate written for a criterion nobody classified is
   how a checkable-but-wrong instrument gets built — the failure ADR-023's
   postscript recorded when it withdrew the byte program.

## Scope Boundaries

### Included

| File | Change |
|---|---|
| `scripts/exit-criteria.py` | new — the checker |
| `scripts/tests/test_exit_criteria.py` | new — predicate unit tests |
| `scripts/eval-exit-criteria.py` | new — fixture scenarios, PASS/FAIL TSV |
| `scripts/eval.sh` | `check_exit_criteria()` + registry entry |
| `.writ/docs/exit-criteria-classification.md` | new — per-criterion evidence record |
| `.writ/docs/phase-execution-state-format.md` | document the additive fields |
| `commands/implement-phase.md` | write the run record; call the checker |
| `commands/implement-spec.md` | write the run record; call the checker |
| `adapters/claude-code.md` | `/goal` wiring in § Quality Gates with Hooks |

### Excluded — `/implement-story`

Named as a candidate during discovery and dropped on evidence. It still receives a
classification entry recording why.

- Criteria 1 and 2 are **already disk-checkable** from the story file header and
  `user-stories/README.md`. A gate adds nothing they do not already assert.
- Criterion 3 reads test and coverage figures from `## What Was Built`, whose
  authoring skill declares as its **single governing rule**: *"never block
  completion on incomplete data. Partial records are better than no records,"*
  with an explicit `**Verification:** N/A` fallback. A gate reading that record
  inverts the rule it was written under.
- It already terminates on its own: 3 review cycles, `on_exhaustion: escalate`.
- It is the innermost loop, so under `/goal`'s single-slot behavior it must never
  hold the goal regardless of what this spec builds.

### Also excluded

- The other 28 commands' 58 criteria — no unattended loop, so no stop-time gate to
  hang on them. The post-hoc auditor covering all 31 is a different product and was
  explicitly not chosen.
- **Rewriting any criterion to make it checkable.** Where a criterion is
  unobservable, this spec records that fact; it does not edit the criterion to fit
  the instrument. That direction is how the instrument starts measuring itself.
- Any hook, Stop handler, or platform runtime outside `adapters/`.

## Relationship to the Phase 10 Governor Specs

`2026-08-11-governor-instrumentation` and `2026-08-12-governor-enforcement` own
**presence and quality**: does a command declare `exit_criteria`, and does the
prose assert something falsifiable. Both are Complete and archived.

This spec owns **evaluation**: given the criteria exist and are well-formed, are
they *true* for this run. It is the layer above, and it touches none of their
files — `scripts/eval-leanness.py` and `.writ/leanness-baseline.json` are not in
its file set. The one shared surface is `scripts/eval.sh`, where this spec appends
a check and its registry entry without modifying an existing one.

## Implementation Approach

1. **Classify before building** (Story 1). Ten criteria across three commands,
   each sorted into evaluable-now / needs-run-record / structurally-unobservable
   with the evidence for the call. The artifact is
   `.writ/docs/exit-criteria-classification.md`, and it is what Story 3 implements
   against.
2. **Close the evidence gaps additively** (Story 2). `exitCriteria[]`,
   `terminalStatus`, and `haltReported` in phase state; `preflight` and `postRun`
   in `.writ/state/execution-<ts>.json`. Written by the commands at the moments
   they already reach — Phase 4 for the phase, post-batch verification for the
   spec.
3. **Build the checker** (Story 3), predicates and rollup only, no I/O beyond
   reading.
4. **Bind it to the suite** (Story 4) using the `check_story_deps` pattern:
   an `eval-*.py` emitting PASS/FAIL TSV over fixture scenarios, plus
   `require_literal` assertions tying command prose to the implementation.
5. **Wire the commands** (Story 5) so the verdict appears in the completion report
   rather than only in a shell.
6. **Wire the adapter** (Story 6) so Claude Code gets the Stop-hook enforcement
   the other three platforms get by convention.

## Success Criteria

1. `exit-criteria.py check` returns a correct three-verdict result for
   `/implement-phase` and `/implement-spec`, with per-criterion evidence
2. Every archived `.writ/state/phase-execution-*.json` yields a verdict matching
   its recorded phase outcome — in particular, Phase 10's `PARTIALLY COMPLETE`
   returns `impossible`, not `unmet`
3. `bash scripts/eval.sh --check=exit-criteria` exits 0, and the full suite stays
   green
4. Every criterion the classification marks unobservable returns `unknown` with
   its recorded reason — none is silently reported `met`
5. `adapters/claude-code.md` documents the `/goal` wiring, the single-slot
   constraint, and the rule that a goal condition must be satisfiable by pausing

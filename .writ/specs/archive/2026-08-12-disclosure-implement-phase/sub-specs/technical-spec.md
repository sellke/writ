# Technical Spec: Progressive Disclosure — `implement-phase`

> Source: `.writ/specs/2026-08-12-disclosure-implement-phase/spec.md`

Every number below was measured against this working tree on 2026-08-12. Re-measure before editing; do not inherit these figures into the implementation record without re-running the commands that produced them.

> **Mechanism ruling, 2026-08-12.** This spec loads its skills by inline `Read skills/<name>/SKILL.md` at the point of need. `required_skills:` is **not used** — the escalation that it is an eager pre-load was verified and accepted. Full record in spec.md → § Approved Scope Changes. Every measurement below was taken with the fixed `scripts/measure-invocation.py` (`e8f2a09`).

## Baseline Measurement

```bash
python3 scripts/measure-invocation.py --root . --command implement-phase
```

```json
{
  "command_bytes": 29136, "command_lines": 321,
  "base_bytes": 24960, "eager_bytes": 0, "floor_bytes": 54096,
  "conditional_bytes": 0, "ceiling_bytes": 54096,
  "eager_skills": [], "conditional_skills": [],
  "resolved_skills": [], "unresolved_skills": [],
  "base_share_of_floor": 0.4614
}
```

Re-run verbatim on 2026-08-12 against `phase/10-progressive-disclosure` with the `e8f2a09` fix in place. **`implement-phase` declares no skills and contains no inline `Read skills/…`, so `eager_bytes` and `conditional_bytes` are both 0 and its baseline ceiling equals its floor at 54,096.** The tooling fix moved no baseline figure for this file — it changes what the *after* numbers mean.

**What `e8f2a09` fixed.** The previous version counted `required_skills:` as conditional, which understated the floor and would have let progressive disclosure self-certify against a number nobody pays; it also ignored inline reads entirely, understating the real cost of the seven commands that already use them. The corrected accounting:

```
floor    = base + command + eagerly declared skills     always paid
ceiling  = floor + inline-read skills                   worst-case path
```

`_inline_read_skills()` (`scripts/measure-invocation.py:140`) matches `Read\s+skills/([A-Za-z0-9._-]+)/SKILL\.md` in the **body only** — frontmatter is stripped first, so a `required_skills:` block can never be miscounted as an inline read. A skill both declared *and* inline-read emits a warning and is charged once, eagerly: the declaration already paid for it and the inline `Read` buys no conditionality.

`base_bytes` decomposes as `system-instructions.md` 20,153 + `commands/_preamble.md` 4,807 = 24,960. That sum **is** the budget (spec.md § The Binding Budget).

Corpus context, from `--format table` over all 31 commands:

| | Value |
|---|---|
| `implement-phase` rank by `floor_bytes` | **4 of 31** (behind `implement-story` 77,669 · `create-spec` 71,383 · `verify-spec` 57,070) |
| `implement-phase` bytes per line | **90.77** — highest in `commands/` |
| Next densest | `refactor.md` 72.37 · `revert.md` 67.90 · `new-command.md` 59.12 |
| Least dense | `migrate.md` 34.48 — ratio **2.63×** |
| Corpus mean bytes per line | 49.12 |
| Lines vs. ADR-021's proposed 400-line cap | 321 — **79 lines of headroom** |

The last row is the finding. A file can be the densest in the repo and 4th-heaviest by load while sitting comfortably inside the cap meant to catch bloat, because the cap counts newlines and the cost is bytes.

## Section Byte Ledger (pre-spec)

Produced by splitting on ATX headings; ranges are inclusive 1-based line numbers into the current file.

| Lines | Bytes | Section | Disposition |
|---:|---:|---|---|
| 1–21 | 2,272 | frontmatter (ADR-020 contract + `loop:`) | **retain, byte-identical** |
| 23–24 | 44 | `# Implement Phase Command` | retain |
| 25–32 | 896 | `## Overview` | retain (add skill pointers) |
| 33–39 | 289 | `## Required Artifacts` | **retain — eval-required** |
| 40–51 | 699 | `## Invocation` | retain |
| 52–62 | 1,655 | `## Recommended Mode (--recommend)` | retain — deferred, not this spec |
| 63–66 | 49 | `## Command Process` + `### Phase 1` | becomes the phase list |
| 67–72 | 441 | Step 1.1 Load the Roadmap | compress into phase list |
| 73–92 | 1,165 | Step 1.2 Resolve Features to Specs | retain classification + AskQuestion; **extract the "Decompose now" guidance (~400 B)** |
| 93–107 | 1,576 | Step 1.2b Decomposition Pre-Pass | **extract → `phase-decomposition`** |
| 108–128 | 2,343 | proposal template + approval + `--all` boundary | **extract → `phase-decomposition`** |
| 129–138 | 635 | Step 1.3 Inventory Prior Progress | compress into phase list |
| 139–154 | 1,669 | `### Phase 2` + Step 2.1 | **retain — 5 anchors at 145/146/147/151** |
| 155–163 | 540 | Step 2.2 Verify Exit Criteria Exist | retain (condition 1 of Question Policy) |
| 164–185 | 1,074 | Step 2.3 + execution-plan template | retain — deferred, not this spec |
| 186–191 | 599 | `### Phase 3` + Step 3.1 Initialize Phase State | **extract → `phase-lane-execution`** |
| 192–205 | 3,058 | Step 3.2 Per-Spec Iteration | **extract, minus the invariants and the *Iteration bound* paragraph** |
| 206–215 | 1,267 | Step 3.2b User Challenge Handling | **extract → `user-challenge-presentation`** |
| 216–226 | 1,590 | Step 3.3 Failure Handling | **extract, minus the invariants** |
| 227–230 | 390 | Step 3.4 `--all` Mode | retain |
| 231–252 | 2,281 | `### Phase 4` + Steps 4.1 / 4.1b / 4.1c | **retain — anchors at 239, 243, 251** |
| 253–279 | 1,424 | Steps 4.2 / 4.3 + report template | retain — deferred, not this spec |
| 280–290 | 1,252 | `## Question Policy (Core Rules)` | **retain — Hard Constraint 1** |
| 291–302 | 943 | `## Integration with Writ` | retain — deferred, not this spec |
| 303–317 | 786 | `## Completion` | retain |
| 318–321 | 164 | `## References` | retain |

Total 29,136 B. Extract ranges: **93–128, 186–226** plus ~400 B from 73–92 = 10,811 B gross.

## The 20 Blocking Anchors — Exact Locations

From `grep -n 'require_literal "$implement_phase"' scripts/eval.sh` (19 hits) plus `check_artifact_integrity` / `scripts/eval-artifact-integrity.py` (`## Required Artifacts`). Line numbers are where each literal occurs in the **pre-spec** command file.

| Literal | Pre-spec lines | Inside an extract range? |
|---|---|---|
| `` Valid explicit `Dependencies` graph `` | 145 | no |
| `topological` | 145, 190 | 190 yes — **145 survives** |
| `roadmap order` | 46, 146, 147 | no |
| `inference remains advisory` | 147 | no |
| `stop before the confirmation gate` | 151 | no |
| `fresh subagent` | 194, 197, 220 | **all yes — must be re-stated** |
| `writ/phase/{phase-id}/{spec-id}` | 196 | **yes — sole occurrence** |
| `phase-spec-result-v1` | 197, 198, 208, 218 | **all yes** |
| `only a verified` | 198 | **yes — sole occurrence** |
| `scripts/phase-state.py` | 20, 190, 196, 198, 210, 218, 239, 246, 247 | 20/239/246/247 survive |
| `User Challenge` | 206, 208, 210, 214 | **all yes** |
| `ordinary failures use their normal` | 214 | **yes — sole occurrence** |
| `writ/quarantine/{spec-id}` | 221 | **yes — sole occurrence** |
| `one transient retry` | 220 | **yes — sole occurrence** |
| `skipped_blocked` | 7, 202, 222 | line 7 (`exit_criteria`) survives |
| `does not guess or mutate git` | 225 | **yes — sole occurrence** |
| `evidence-bound` | 239 | no |
| `no qualifying candidate` | 239 | no |
| `production health` | 243, 251 | no |
| `## Required Artifacts` | 33 | no |

**Eight literals have their only occurrence inside an extract range.** Those eight, plus `fresh subagent` and `phase-spec-result-v1` (every occurrence extracted), are the ten that the retained **Lane & Failure Invariants** block must carry. They are not incidental phrasing — each names a step of the safety machinery, which is why Business Rule 2 and the eval suite land on the same set.

Regression guard, runnable at any point:

```bash
while IFS= read -r s; do
  grep -Fq "$s" commands/implement-phase.md || echo "MISSING ANCHOR: $s"
done <<'EOF'
Valid explicit `Dependencies` graph
topological
roadmap order
inference remains advisory
stop before the confirmation gate
fresh subagent
writ/phase/{phase-id}/{spec-id}
phase-spec-result-v1
only a verified
scripts/phase-state.py
User Challenge
ordinary failures use their normal
writ/quarantine/{spec-id}
one transient retry
skipped_blocked
does not guess or mutate git
evidence-bound
no qualifying candidate
production health
## Required Artifacts
EOF
```

## The Retained Lane & Failure Invariants Block

Shape, not final text. It replaces Steps 3.1–3.3 in the command body and must carry the ten at-risk anchors plus the four Business Rule 2 invariants in normative language. Budget: **≈1,950 bytes**.

Content it must contain, at minimum:

1. **Lane before work.** The lane branch `writ/phase/{phase-id}/{spec-id}` and its worktree are created via `scripts/phase-state.py create-lane` *before* any spec work begins. A dirty base or a branch collision **stops before launch** — isolation created only after a failure cannot prove the phase branch stayed clean.
2. **Fresh context.** Each spec runs in a **fresh subagent** seeded only with artifact paths and the expected `phase-spec-result-v1` schema. No prior conversational transcript is forwarded.
3. **Merge only on verified success.** **Only a verified** `phase-spec-result-v1` with `status: succeeded`, a real commit, and non-empty verification evidence merges (`--no-ff`) into the phase branch. Anything missing, malformed, non-successful, or unverifiable **never touches the phase branch**.
4. **Quarantine on terminal failure.** Exactly **one transient retry** is permitted, in the same lane; a terminal failure preserves the lane as `writ/quarantine/{spec-id}` with recorded evidence, retry count, and a recovery command. Declared dependents become `skipped_blocked`; independents continue.
5. **Resume never guesses.** `reconcile` runs first on `--resume` and on any discrepancy reports the named mismatch and a recovery command — it **does not guess or mutate git**.
6. **The *Iteration bound* paragraph in full** (pre-spec lines 202–203). It states the 12-spec bound, the counter reset at phase boundaries under `--all`, the retry/iteration distinction, and — load-bearing — why `on_exhaustion: halt_reported` does **not** quarantine. Business Rule 5. This paragraph is retained, not compressed.

Anything beyond these six — how `create-lane` verifies the base, how the subagent is seeded, the `--quick` pass-through, the inherited-answer rule, the classify/retry/quarantine call sequence, the reconcile mechanics — goes to `skills/phase-lane-execution/SKILL.md`.

## The `loop:` Block — Do Not Touch

Pre-spec lines 11–20. `git diff commands/implement-phase.md` must show **zero changed bytes** inside it.

```yaml
loop:
  unit: "spec"
  max_iterations: 12
  on_exhaustion: halt_reported
  calibrated_against: "..."          # keep verbatim
  nested:
    - unit: "spec_attempt"
      max_iterations: 2
      on_exhaustion: quarantine
      calibrated_against: "..."      # keep verbatim
```

`scripts/eval-loop-bounds.py` `scenario_transcription_drift` reads `attempts\s*<\s*(\d+)` out of `scripts/phase-state.py` — the guard is at **line 414**, `if classification == "transient" and attempts < 2:` — and emits `drift-spec-attempt` FAIL if the declared `spec_attempt` bound diverges. The declaration transcribes the code; it may not diverge from it, and the code is out of scope (Business Rule 8).

`halt_reported` on the outer loop is a maintainer decision with a stated rationale in the file itself. Quarantining at outer-loop exhaustion would write a failure record for work that never failed and cascade `skipped_blocked` onto dependents, degrading scope. Do not "normalize" the two `on_exhaustion` values to match.

## Skill Authoring

Each skill is produced by `/new-skill`, which:

1. Checks name uniqueness against `.writ/manifest.yaml` across `commands:`, `agents:`, **and** `skills:`.
2. Lints a temporary frontmatter-only file with `bash scripts/lint-skill.sh` **before** writing anything.
3. Writes `skills/<name>/SKILL.md` with `disable-model-invocation: true` and `status: candidate`.
4. Appends an alphabetically placed `.writ/manifest.yaml` entry.
5. Runs `bash scripts/gen-skill.sh --check`, refreshing the root `SKILL.md` if there is a delta.

`scripts/lint-skill.sh` rejects, among others, `Run the full` and `Execute the entire` (workflow shape), `Read commands/` (command invocation), `Read skills/` (skill chaining), `Task(` (subagent dispatch), and a body line starting `/<command>` (slash invocation). **This is the hard part of Stories 1–3, not a formatting step.** The extracted prose currently reads as a transcript of `/implement-phase`'s numbered steps and references `scripts/phase-state.py` subcommands and `/create-spec` by name. It must be rewritten as a portable capability — *how to decompose features into specs*, *how to run work in an isolated lane and dispose of its result*, *how to present and persist a four-part challenge* — with the orchestration left behind in the command.

Frontmatter shape, matching the six incumbents:

```yaml
---
name: <kebab-case>
description: "<verb-phrase, one line>"
disable-model-invocation: true
status: candidate
status_evidence: "Extracted 2026-08-12 from commands/implement-phase.md <section>. 1 consumer (commands/implement-phase.md); proven needs >=3 — see ADR-014."
---
```

Body sections, per `/new-skill`'s template: `## Purpose`, `## When to Use`, `## How to Apply`, optionally `## Examples`.

**Size discipline — the hard cap is retired.** The six incumbents run 5,997–9,985 bytes. The pre-ruling Business Rule 1 capped these three at the bytes removed from the command (≈7,841 B total, ~2,614 B each), forcing ~27% compression of already-dense normative prose. That cap existed only to stop an *eager* ceiling rising, and under conditional loading it is gone (spec.md § Approved Scope Changes). Skills are now authored to their source: `phase-decomposition` ≈3,600 · `phase-lane-execution` ≈4,400 · `user-challenge-presentation` ≈1,500, ≈9,500 B total. Still small by house standards, but no longer at a size that puts Business Rule 3 under pressure — the cheapest way to hit an aggressive byte target on normative prose is to soften a rule into advice, which is the drift this spec exists to prevent. A skill landing far over projection moves worst-path D and must be **stated** by Story 5, not absorbed.

## Inline `Read` Placement

**No `required_skills:` block is added. The frontmatter is not touched at all** beyond leaving the ADR-020 key order (`name`, `description`, `problem`, `outcome`, `exit_criteria`) and the `loop:` block byte-identical. `grep -c 'required_skills' commands/implement-phase.md` must return **0** after the rewrite.

Each skill is loaded by exactly one inline call in the body, at the narrowest step that needs it (Business Rule 4). The literal form the tool matches is `Read skills/<name>/SKILL.md`:

| Skill | Placement | Guard it must sit *inside* |
|---|---|---|
| `phase-decomposition` | the decomposition pre-pass | **after** the branch establishing unspecced features exist **and** the user approved decomposing them — not in Step 1.2's classification, which runs every phase |
| `phase-lane-execution` | start of the per-spec iteration, where lane creation begins | none — this path is always taken |
| `user-challenge-presentation` | the `challenge_required` branch | **after** validation, not at the top of failure handling |

**Placement is the mechanism, not a style preference.** A `Read` hoisted above the branch it serves costs the same bytes on every invocation as an eager declaration, while `measure-invocation.py` books it under `conditional_bytes` — the number looks conditional and the run pays in full. Story 5 verifies placement against the phase list, not merely presence.

The house pattern to follow is the shipping one: `commands/implement-story.md:525` reads

> Spawns the coding agent to run the red → green → refactor loop via `Read skills/tdd-cycle/SKILL.md` … This gate owns *when* coding runs … the skill owns *how* the test-first cycle runs.

Seven commands do this today (`implement-story`, `ship`, `release`, `research`, `refactor`, `create-spec`, `new-skill`). Each pairs the call with a one-line statement of the command/skill boundary, which is what makes the pointer useful to a reader and not just to the harness.

**`scripts/lint-skill.sh:52` forbids `Read skills/` inside a skill** (category *Skill chaining*). Inline reads live in **commands only**; skills still never chain, and the three extracted skills must not reference each other.

### The failure modes this mechanism has, and what catches them

| Failure | Runtime effect | What catches it |
|---|---|---|
| The step is never reached | the skill's content does not exist for that run | **nothing — this is the design.** It is why the floor falls, and why Business Rule 2 forbids putting an invariant in a skill |
| The `Read` fails (file renamed, moved, unwritten) | an error mid-step, no pre-flight resolution, **no harness warning** — there is no declaration to resolve | `scripts/measure-invocation.py` only: `unresolved_skills` + a "figures are a lower bound" warning. It always exits 0 |
| The path is typo'd | same as above | **`scripts/eval-leanness.py` does not catch it.** `check_required_skills()` (`:682-724`) iterates `fields.get("required_skills", "")` and nothing else — inline reads are invisible to the governor |

The last row is a real gap and is escalated to `2026-08-12-governor-enforcement`, which owns `eval-leanness.py`. It is **not** fixed here (Business Rule 8). Its consequence for this spec: Business Rule 4's reachability is verified once, in Story 5, and re-verified by nothing afterwards — so Story 5's check is the only one there is.

## Verification

```bash
# 1. Budget — the whole path table, before and after (ADR-021 caveat 2)
python3 scripts/measure-invocation.py --root . --command implement-phase
#    command_bytes <= 24960 ; floor_bytes < 49136
#    eager_bytes == 0 ; eager_skills == []          <- no declaration exists
#    conditional_skills == the three ; unresolved_skills == []
#    always-taken path (floor + phase-lane-execution) < 54096   <- the second capped figure
#    worst path (= ceiling_bytes) reported; above 54096 only with the two rare
#    conditions named (Business Rule 1)

# 1b. No eager declaration crept in
grep -c 'required_skills' commands/implement-phase.md     # expect 0

# 1c. Exactly three inline reads, each inside its guard (placement, not presence)
grep -n 'Read skills/' commands/implement-phase.md        # expect 3, at the mapped steps

# 2. Anchors — all 20 present in the command file itself
#    (heredoc loop above)

# 3. Loop bounds unchanged
python3 scripts/eval-loop-bounds.py | grep drift-spec-attempt
git diff commands/implement-phase.md | sed -n '/^[+-]loop:/,/^[+-]---/p'   # expect empty

# 4. Skills
bash scripts/lint-skill.sh skills/*/SKILL.md    # also proves no skill contains `Read skills/`
bash scripts/gen-skill.sh --check

# 5. Eval suite — no new findings vs. the 2026-08-12 baseline
bash scripts/eval.sh --check=length     # baseline: exit 0
bash scripts/eval.sh                    # compare report against the recorded baseline path

# 6. Ownership
git diff --name-only                    # no scripts/ path; commands/ only implement-phase.md

# 7. Spec graph
python3 scripts/spec-deps.py validate --specs-dir .writ/specs
```

## Error & Rescue Map

| Failure | Signal | Rescue |
|---|---|---|
| An anchor was moved into a skill | `bash scripts/eval.sh` blocking finding, e.g. *"Implement-phase must merge only verified success"* | Restore the literal to the command's invariants block. **Never** edit `scripts/eval.sh` (Business Rule 8). |
| Always-taken path ≥ 54,096 | floor + `phase-lane-execution` measured at or above the monolith | The floor fell but every real run got more expensive. Cut `phase-lane-execution`'s prose — it is the one skill on the unconditional path — never the command's invariants (Business Rule 2). If it cannot fit without dropping a rule, **escalate**; ADR-021 names a tracked exemption as the correct answer for a file where disclosure produces a worse outcome. |
| Worst path above 54,096 | `ceiling_bytes` > 54,096 | **Not automatically a failure** under the 2026-08-12 ruling. Report the number and name the two independently rare conditions required to reach it (Business Rule 1). If reaching it needs only one rare condition, it is not a worst path — re-check placement. |
| A `Read` was hoisted above its guard | grep shows the call outside the branch it serves | Move it into the branch. `conditional_bytes` counts it either way, so the measurement will not catch this — only reading the placement will. |
| `required_skills:` appears in the frontmatter | `grep -c required_skills` > 0; `eager_bytes` > 0 | Remove it. A stray declaration silently converts a conditional load into an eager one and invalidates every path figure (Business Rule 4). |
| `drift-spec-attempt` FAIL | `eval-loop-bounds.py` | The `loop:` block was edited. Restore it byte-for-byte from `git show HEAD:commands/implement-phase.md`. |
| Skill name collides with a sibling spec | `/new-skill` uniqueness check, or a manifest duplicate | Business Rule 10 — reconcile against `2026-08-12-disclosure-implement-story` and the manifest before authoring, not after. |
| `lint-skill.sh` rejects the description or body | non-zero exit at authoring time | The extraction is still shaped like a workflow. Rewrite as a capability; do not weaken the lint. |
| `MAX_SKILLS = 12` exceeded | `eval-leanness.py` finding | Report it in Story 5 evidence and escalate (Business Rule 11). Do not edit the constant. |
| Orchestrator reading a half-rewritten file | the run itself misbehaves | Business Rule 6 — the rewrite is one atomic commit. Recover with `git show <pre-edit-sha>:commands/implement-phase.md`, recorded in Story 4's evidence. |
| `spec-deps.py` reports `missing_reference` | validator output | Expected until `2026-08-12-disclosure-implement-story` is authored. **Do not delete the dependency.** |

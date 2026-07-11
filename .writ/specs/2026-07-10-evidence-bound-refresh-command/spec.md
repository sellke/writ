# Evidence-Bound /refresh-command

> **Status:** Complete
> **Created:** 2026-07-10
> **Owner:** @AdamSellke
> **Phase:** 7 — Compounding Layer
> **Dependencies:** []
> **Source:** `.writ/product/roadmap.md` Phase 7 — feature "Evidence-bound `/refresh-command`"

---

## Specification Contract

**Deliverable:** Make Writ's learning loop falsifiable. Every proposed `/refresh-command` refinement must cite transcript evidence (transcript ID/path + a short observable signal + the affected command line/section) and pass eval Tier 1 — plus a lightweight, structural Tier 2 check for high-traffic commands — before it can merge. Add a fixture-driven eval check that validates refresh refinements carry evidence, give unevidenced proposals a first-class rejection path, and reconcile the drift between the current command file and the docs/specs that describe it.

**Origin:** Phase 7 — Compounding Layer in `.writ/product/roadmap.md`. The roadmap frames the industry bar via GBrain's `skillopt`: treat command edits as trainable parameters and keep only measurably better edits. This spec is independent — eval Tier 1 already ships; no other Phase 7 spec is a prerequisite.

**Must Include:** A `/refresh-command` refinement cannot be applied or logged as applied unless it names the transcript it came from, quotes a short observable signal from that transcript, and anchors the change to a real section of the target command file. A proposal that cannot produce evidence is rejected, and the rejection is itself recorded so the "kept vs. discarded" decision is auditable.

**Hardest Constraint:** Honor the Prime Directive privacy rule while making evidence auditable. Evidence citations reference transcript IDs/paths and short observable signals only — never stored chain-of-thought, prompts, or verbatim private transcript bodies. Transcripts live outside the git repository (Cursor platform-local `.jsonl` files); the audit trail in `.writ/refresh-log.md` must remain committable, honest, and free of private content.

### Experience Design

- **Entry point:** `/refresh-command [command]` after running a Writ command — the maintainer describes friction, or asks the agent to infer it from the just-run session.
- **Happy path:** Gather signals → for each proposal cite transcript evidence + anchor → run the pre-merge eval gate → apply only evidenced, eval-passing amendments → append an evidenced `.writ/refresh-log.md` entry.
- **Moment of truth:** A proposed edit that improves the command carries a verifiable citation and survives the eval gate; a plausible-but-unevidenced edit is visibly rejected rather than silently applied.
- **Feedback model:** `.writ/refresh-log.md` records every run — applied amendments with evidence, and rejected candidates with the reason (`no evidence` / `eval failed`). `/status` surfaces refresh recency from that same log.
- **Error experience:** Missing transcript citation, unreadable transcript file, an eval-check crash, or a private-content guard trip each stop the amendment before it is written and report the exact blocker and recovery path.
- **Scope-degradation decisions:** Weakening the evidence requirement, applying an unevidenced edit "just this once," or promoting a low-confidence guess are contract-degrading and require an explicit human choice, not a silent default.

### Business Rules

1. Every applied amendment cites: a transcript ID or repo-relative-safe path, a short observable signal (a user correction, retry, override, or error — quoted briefly), and the affected command file line or section.
2. A proposal that cannot cite transcript evidence is **rejected**, never applied. The rejection is recorded in `.writ/refresh-log.md` with reason `no evidence`.
3. Evidence citations never contain chain-of-thought, prompts, or verbatim private transcript bodies. Cite IDs and short observable signals only.
4. Before any amendment is written, the command runs the pre-merge eval gate (`eval.sh --check=refresh-evidence`); a failing gate rejects the amendment with reason `eval failed`.
5. For high-traffic commands (`create-spec`, `implement-story`, `ship`, `refactor`), the gate additionally runs a lightweight **structural** Tier 2 check on the refreshed command file. Tier 2 is structural only — not an LLM-as-judge.
6. `.writ/refresh-log.md` is the canonical, append-only audit trail. Its path is `.writ/refresh-log.md` everywhere — no `.writ/state/refresh-log.md` variant.
7. A run that applies zero amendments ("reviewed, no changes") is a valid outcome and is exempt from the evidence requirement, because there is nothing to justify.
8. Legacy log entries dated before the contract's effective date (`LEARNING_CONTRACT_SINCE`) are grandfathered; the eval check does not retroactively fail them.
9. The command file and every doc that describes it (`.writ/docs/refresh-log-format.md`, `commands/status.md`, `README.md`) must describe the same behavior. Claims about unimplemented mechanics (`--batch`, promotion flow, a nonexistent "Phase 2.2") are either implemented or removed — no aspirational drift.
10. The eval check is fixture-driven (modeled on `scripts/eval-phase-knowledge.py`): it validates the parser/validator against synthetic entries in temp dirs plus static assertions, so CI stays deterministic and never depends on the live log's contents.
11. CI enforcement is a backstop, not the only gate: `.github/workflows/eval.yml` runs `eval.sh` on every PR and push and needs no new wiring because the new check auto-runs from the registry.

### Success Criteria

1. `commands/refresh-command.md` Phase 3 mandates a structured Evidence citation for every proposed amendment, and Phase 4 refuses to apply or log-as-applied any amendment lacking one.
2. A well-formed evidenced refresh-log entry passes `scripts/eval-refresh-evidence.py`; an otherwise-identical entry with no transcript citation fails; an entry embedding verbatim private transcript body / chain-of-thought fails the privacy guard.
3. `check_refresh_evidence` is registered in `scripts/eval.sh` (one appended check function + one appended registry line) and runs clean under `bash scripts/eval.sh`.
4. `.github/workflows/eval.yml` runs the new check with no file change (auto-run via the registry) — verified, and noted in the spec.
5. `.writ/docs/refresh-log-format.md`, `commands/status.md`, and `README.md` describe the actual behavior: no "Phase 2.2" reference, one canonical `.writ/refresh-log.md` path, transcript claims aligned to cited-evidence reality.
6. The pre-merge gate rejects an unevidenced or eval-failing amendment before it is written, and the rejection is logged.
7. The lightweight Tier 2 structural check runs only for the high-traffic allowlist and reuses existing Tier 1 structural primitives; no LLM-judge is introduced.
8. Two real acceptance entries exist in `.writ/refresh-log.md`: one refinement merged with cited transcript evidence and passing evals, and one rejected for lacking evidence.
9. `bash scripts/eval.sh` and `bash scripts/gen-skill.sh --check` remain clean across all registered checks.

### Scope Boundaries

**Included:**
- Mandatory structured evidence citation in `commands/refresh-command.md` (Phases 2–4).
- A first-class rejection path for unevidenced or eval-failing proposals, recorded in the log.
- `scripts/eval-refresh-evidence.py` (new) — fixture-driven evidence validator.
- Registration of `refresh-evidence` in `scripts/eval.sh` (append-only check function + registry line).
- A lightweight, structural, high-traffic-scoped Tier 2 check and the pre-merge eval gate.
- Drift reconciliation across `.writ/docs/refresh-log-format.md`, `commands/status.md`, and `README.md`.
- Two-example acceptance (one merged-with-evidence, one rejected-for-lacking-evidence).

**Excluded:**
- LLM-as-judge Tier 2 (deferred behind an explicit future decision; see Technical Concerns).
- Tier 3 paid end-to-end evals.
- Restoring `--batch`, `--last`, or the promotion-to-core PR flow as implemented features (docs are reconciled to reality instead).
- Automatic transcript scanning or ingestion pipelines; the command remains human-driven with cited evidence.
- Skill lifecycle state, skill extraction, and knowledge consolidation (separate Phase 7 specs).
- Copying transcript content into the repository or any external memory/telemetry integration.

### Technical Concerns

- **Tier 2 cost/scope is the primary risk.** Research (`.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`) defines Tier 2 as an LLM-as-judge (~$0.15 / ~30s per run) and Writ deliberately deferred it ("cost grossly exceeds value for current scale"). This spec therefore defines Tier 2 conservatively: a lightweight, opt-in, **structural** deeper check scoped to high-traffic commands that reuses existing Tier 1 primitives. The LLM-judge variant stays explicitly out of scope and behind a future decision. Building an LLM-judge now would violate the roadmap's "delegate mechanics, own contracts" pacing discipline.
- **Transcripts are outside the repo and platform-local.** Cursor stores `.jsonl` under `~/.cursor/projects/.../agent-transcripts/{uuid}/{uuid}.jsonl` (and `.../subagents/{sub-uuid}.jsonl`). Evidence must reference them by ID/path plus a short observable signal; the eval check must tolerate a transcript file being absent (grandfathered / different machine) without fabricating failure, and must never require the transcript body to be committed.
- **Privacy vs. auditability tension.** The audit trail must be verifiable yet contain no private content. The contract resolves this by citing IDs and short observable signals only, and the eval check includes a privacy guard that fails entries embedding verbatim private bodies or chain-of-thought.
- **Determinism.** The eval check must not fail on the two existing legacy log entries. It is fixture-driven (temp-dir synthetic entries) and grandfathers live entries dated before `LEARNING_CONTRACT_SINCE`.
- **Shared-file additivity.** `scripts/eval.sh` is a SHARED-ADDITIVE surface: this spec appends exactly one check function plus one registry-array line; the knowledge-consolidation spec appends later. Sequential phase execution makes both safe as long as each edit is append-only and does not reorder the registry.

### Recommendations

- **Restore evidence citation into the command rather than redefine the roadmap away.** The roadmap feature literally requires "cited transcript evidence." The current command lost it; the right reconciliation is to bring lightweight citation back into Phases 2–4, not to declare the requirement optional. Simultaneously, redefine the docs to match reality for genuinely unimplemented mechanics (`--batch`, promotion) rather than pretend they exist.
- **Model the new eval check on `scripts/eval-phase-knowledge.py`.** It is the proven pattern for evidence-bound checks — a Python fixture script emitting PASS/FAIL TSV consumed by a bash `check_*` function with supplementary `require_literal` static assertions.
- **Make rejection a first-class, logged outcome.** The roadmap success criterion needs a *rejected* example; the cleanest way to guarantee one can exist is to make "rejected for lacking evidence" a normal, recorded result rather than an error.
- **Keep Tier 2 structural and bounded.** Reuse existing Tier 1 primitives scoped to the refreshed high-traffic command; keep the LLM-judge explicitly deferred and flagged.
- **Enforce at two points, not one.** An in-command Apply-time gate gives fast feedback; CI (`eval.yml`) is the backstop. Neither should require new CI wiring.

### Cross-Spec Review

This spec is independent (`Dependencies: []`). Eval Tier 1 and the `check_*`/fixture pattern already exist from Phase 6 (`2026-07-09-phase6-autonomy-ceiling`) and are implementation references. The sibling Phase 7 specs — skill lifecycle, skill extraction, and knowledge consolidation — are sequenced separately; knowledge consolidation also appends to `scripts/eval.sh`, so both specs must keep their registry edits strictly append-only. No sibling spec is a prerequisite for this one.

---

## Experience Design

### Primary User Journey

1. The maintainer runs a Writ command (e.g., `/create-spec`), then invokes `/refresh-command create-spec`.
2. Writ reads the command file and gathers friction signals — from the maintainer's description or by inferring from the just-run session in the conversation.
3. For each actionable signal, Writ proposes an amendment **and** attaches evidence: the transcript ID/path it came from, a short observable signal quoted from it, and the target command section the change anchors to.
4. Before applying, Writ runs the pre-merge eval gate. For a high-traffic command it also runs the structural Tier 2 check on the would-be-refreshed file.
5. Evidenced, eval-passing amendments are applied and recorded with their evidence. Unevidenced or eval-failing proposals are rejected and recorded with the reason.
6. Writ appends one `.writ/refresh-log.md` entry summarizing applied amendments (with evidence) and rejected candidates (with reason).
7. `/status` later surfaces refresh recency from the same log — never claiming an automatic transcript scan the command does not perform.

### State Catalog

| State | User-visible behavior |
|---|---|
| No target command | List available commands and ask the maintainer to pick |
| Signals gathered | Summarize signals and confirm before proposing |
| Proposal with evidence | Show amendment + transcript ID + observable signal + affected section |
| Proposal without evidence | Reject before apply; record `no evidence`; do not write the diff |
| Eval gate fails | Reject the amendment; record `eval failed`; report the failing check |
| High-traffic target | Additionally run the structural Tier 2 check before writing |
| Transcript file absent | Accept the ID citation if present; never fabricate a body; note unavailability |
| Private content detected | Refuse to store it; keep the citation to ID + short observable signal |
| Reviewed, no amendments | Valid outcome; log the review; evidence not required |
| Legacy log entry | Grandfathered when dated before `LEARNING_CONTRACT_SINCE`; not retroactively failed |

### Interaction and Output Rules

- Output stays concise, terminal-oriented Markdown; no new UI.
- Every applied amendment shows its evidence inline; the log mirrors it.
- Rejections are visible, not swallowed — the maintainer sees why a proposal did not merge.
- The command never copies transcript bodies or chain-of-thought into any artifact.
- `/status` reads the log; it does not run mutating or heavyweight work.

---

## Detailed Requirements

### R1 — Mandatory Structured Evidence Citation

- `commands/refresh-command.md` Phase 3 requires, per proposal: **Title**, **Rationale**, **Confidence** (H/M/L), **Evidence**, and **Diff**.
- **Evidence** is a structured block with three parts: transcript ID or path; a short observable signal quoted from that transcript (correction, retry, override, or error); and the affected command file line/section anchor.
- The observable signal is short and factual. Chain-of-thought, prompts, and verbatim private bodies are forbidden.
- Phase 2 gathers signals either from the maintainer's description or by inferring from the most recent command run in the conversation; either way the resulting proposal must be attributable to a transcript ID/path.

### R2 — Rejection Path for Unevidenced Proposals

- A proposal that cannot cite transcript evidence is rejected before Apply and never written to the command file.
- The rejection is recorded in `.writ/refresh-log.md` under a `**Rejected:**` section with reason `no evidence`.
- An amendment that fails the pre-merge eval gate is rejected with reason `eval failed`.
- Rejection is a normal outcome, not an error; it directly serves the roadmap's "at least one rejected for lacking evidence" criterion.

### R3 — Fixture-Driven Refresh-Evidence Eval Check

- `scripts/eval-refresh-evidence.py` (new) emits PASS/FAIL TSV, modeled on `scripts/eval-phase-knowledge.py`, exercising synthetic entries in temp dirs:
  - well-formed evidenced entry → passes
  - missing transcript citation → fails
  - missing observable signal → fails
  - verbatim private body / chain-of-thought embedded → fails (privacy guard)
  - reviewed-with-no-amendments entry → exempt (passes)
  - rejected-for-lacking-evidence entry → valid rejection record (passes)
  - live entry dated before `LEARNING_CONTRACT_SINCE` → grandfathered (passes)
- `scripts/eval.sh` gains `check_refresh_evidence()` that consumes the TSV and adds `require_literal` static assertions that the command and docs mandate evidence and the rejection path.
- The registry array in `scripts/eval.sh` gains exactly one appended entry: `refresh-evidence` (dispatched to `check_refresh_evidence` via the existing `check_${check//-/_}` convention).

### R4 — Pre-Merge Eval Gate

- `commands/refresh-command.md` Phase 4 runs `bash scripts/eval.sh --check=refresh-evidence` before writing any amendment.
- A non-zero result rejects the amendment and records `eval failed`; only a clean gate allows Apply.
- CI (`.github/workflows/eval.yml`) is the backstop and requires no change: the check auto-runs from the registry via the existing `eval.sh` step.

### R5 — Lightweight Structural Tier 2 for High-Traffic Commands

- High-traffic allowlist: `create-spec`, `implement-story`, `ship`, `refactor`.
- For an allowlisted target, the gate additionally runs a bounded structural check on the refreshed command file, reusing existing Tier 1 structural primitives (required-sections presence, no new broken refs, length sanity, preamble reference intact, diff anchored to a real section).
- Tier 2 is structural only. The LLM-as-judge variant is out of scope and deferred behind an explicit future decision.
- The allowlist and the Tier 2 boundary are documented in the command and asserted by the eval check.

### R6 — Drift Reconciliation

- `commands/refresh-command.md`: Phases 2–4 carry the restored evidence citation and rejection path; no aspirational `--batch`/promotion machinery is introduced.
- `.writ/docs/refresh-log-format.md`: replace the loose `**Source transcript:**` field with the mandatory structured Evidence block; fix stale phase references ("Phase 5: Changelog + Phase 6: Promotion Review"); remove or mark-unimplemented the promotion/batch optional fields; fix the `**Target file:**` path convention to match the command; document `LEARNING_CONTRACT_SINCE` grandfathering.
- `commands/status.md`: remove the reference to the nonexistent "Phase 2.2 of refresh-command.md"; use the single canonical `.writ/refresh-log.md` path (no `.writ/state/refresh-log.md`); reword the "new transcripts" heuristic and drop the `--batch` suggestion so guidance matches the human-driven cited-evidence command.
- `README.md`: change "scans agent transcripts" / "Scans agent transcripts" to accurate phrasing (e.g., "turns session friction into cited command diffs") that reflects the human-driven, evidence-citing behavior.

### R7 — Two-Example Acceptance

- Produce one real `.writ/refresh-log.md` entry for a refinement merged with cited transcript evidence and a clean eval gate.
- Produce one real `.writ/refresh-log.md` entry for a proposal rejected for lacking evidence.
- Both entries conform to the reconciled `.writ/docs/refresh-log-format.md` schema and together satisfy the roadmap success criterion.

---

## Implementation Approach

### Architecture

`/refresh-command` remains a human-driven, platform-neutral command. The learning loop becomes falsifiable by inserting two contracts into its existing phases:

`gather signals → propose (with mandatory evidence) → pre-merge eval gate → apply evidenced/passing OR reject+log → append evidenced log entry`

The eval subsystem gains one fixture-driven check that validates the evidence contract deterministically, wired into the same registry and CI path as the existing 19 checks.

### Evidence Model

An amendment's evidence is three fields — transcript ID/path, a short observable signal, and the affected command section. The signal is a brief factual quote of an observable event (a correction, retry, override, or error), never reasoning or a private body. The refresh-log entry mirrors these fields so the audit trail is self-contained without embedding private content.

### Eval Check Model

`scripts/eval-refresh-evidence.py` follows `scripts/eval-phase-knowledge.py`: build synthetic refresh-log entries in temp dirs, run them through the validator, and emit `PASS\t<name>` / `FAIL\t<name>\t<reason>` lines. `check_refresh_evidence()` in `scripts/eval.sh` counts scenarios and adds `require_literal` assertions against `commands/refresh-command.md` and the reconciled docs. Grandfathering uses a documented `LEARNING_CONTRACT_SINCE` date so the two existing legacy entries never fail.

### Tier 2 Model

Tier 2 is a scoped reuse of existing structural checks — not new semantics. For an allowlisted high-traffic target, the gate validates the refreshed file's structure before it is written. This is deliberately cheaper and more deterministic than an LLM judge, which stays deferred.

### Validation Strategy

This repository has no application test suite. Verification is fixture- and script-based:

- `python3 scripts/eval-refresh-evidence.py`
- `bash scripts/eval.sh` (and `--check=refresh-evidence`)
- `bash scripts/gen-skill.sh --check`
- targeted greps proving drift is reconciled (no "Phase 2.2"; single `.writ/refresh-log.md` path; README phrasing; command Evidence field present)

---

## Files in Scope

### Primary

- `commands/refresh-command.md` — mandate evidence in Phase 3, add the pre-merge eval gate and Tier 2 wiring in Phase 4, reconcile drift.
- `scripts/eval-refresh-evidence.py` (new) — fixture-driven evidence validator (base + Tier 2 scenarios).
- `scripts/eval.sh` — append `check_refresh_evidence()` and one `refresh-evidence` registry entry (SHARED-ADDITIVE, append-only).

### Documentation & Reconciliation

- `.writ/docs/refresh-log-format.md` — align the log schema with the enforced evidence and grandfathering.
- `commands/status.md` — remove "Phase 2.2", fix the canonical `.writ/refresh-log.md` path, reconcile the `--batch`/transcript-scan drift.
- `README.md` — align "scans agent transcripts" claims with the human-driven cited-evidence behavior.

### Supporting Validation

- `.github/workflows/eval.yml` — expected **no change**; the new check auto-runs via the registry. Verified and noted; edited only if explicit wiring proves necessary.
- `.writ/refresh-log.md` — receives the two real acceptance entries (merged-with-evidence, rejected-for-lacking-evidence).

---

## Story Plan

1. **Evidence-Citation Contract and Drift Reconciliation** — Dependencies: None
2. **Refresh-Evidence Eval Check** — Dependencies: Story 1
3. **Lightweight Tier 2 and Merge Gate** — Dependencies: Stories 1, 2

---

## Deliverables

- [x] `commands/refresh-command.md` Phase 3 mandates a structured Evidence citation per amendment
- [x] Unevidenced and eval-failing proposals are rejected and recorded with a reason
- [x] Evidence citations carry IDs + short observable signals only — never chain-of-thought or verbatim private bodies
- [x] `scripts/eval-refresh-evidence.py` validates evidenced/unevidenced/private-content/no-op/rejection/grandfathered cases
- [x] `refresh-evidence` registered in `scripts/eval.sh` (one appended check function + one registry line)
- [x] `.github/workflows/eval.yml` runs the new check with no change (verified and noted)
- [x] `.writ/docs/refresh-log-format.md`, `commands/status.md`, and `README.md` describe the actual behavior
- [x] Pre-merge eval gate wired into the command's Apply phase
- [x] Lightweight structural Tier 2 scoped to the high-traffic allowlist; LLM-judge explicitly deferred
- [x] Two real acceptance entries in `.writ/refresh-log.md` (one merged-with-evidence, one rejected-for-lacking-evidence)
- [x] `bash scripts/eval.sh` and `bash scripts/gen-skill.sh --check` remain clean

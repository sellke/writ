# Evidence-Bound /refresh-command (Lite)

> Source: `.writ/specs/2026-07-10-evidence-bound-refresh-command/spec.md`
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Make the `/refresh-command` learning loop falsifiable. Every applied refinement cites transcript evidence and passes an eval gate; unevidenced ones are rejected and logged. Reconcile command-vs-docs drift.

**Implementation Approach:**
- `commands/refresh-command.md` Phase 3: require **Evidence** per proposal = transcript ID/path + short observable signal + affected command section.
- Phase 4: run `bash scripts/eval.sh --check=refresh-evidence` before writing; reject on failure; for high-traffic commands also run the structural Tier 2 check.
- `scripts/eval-refresh-evidence.py` (new): model on `scripts/eval-phase-knowledge.py` (PASS/FAIL TSV over temp-dir fixtures).
- `scripts/eval.sh`: append `check_refresh_evidence()` + one `refresh-evidence` registry line (append-only; dispatch is `check_${check//-/_}`).
- Tier 2 = lightweight structural reuse of Tier 1 primitives, scoped to `create-spec`, `implement-story`, `ship`, `refactor`. NOT an LLM judge.

**Files in Scope:**
- `commands/refresh-command.md`, `scripts/eval-refresh-evidence.py` (new), `scripts/eval.sh`
- `.writ/docs/refresh-log-format.md`, `commands/status.md`, `README.md`
- `.github/workflows/eval.yml` (no change expected), `.writ/refresh-log.md` (acceptance entries)

**Error Handling:**
- Missing transcript citation → reject, log `no evidence`.
- Eval gate fails → reject, log `eval failed`.
- Transcript file absent → accept ID citation, never fabricate a body.
- Private content (CoT / verbatim body) detected → refuse to store; keep ID + short signal.

**Integration Points:**
- Registry-driven check auto-runs in `eval.sh` and CI (`eval.yml`) — no CI wiring change.
- `/status` reads `.writ/refresh-log.md` recency; no automatic transcript scan.

---

## For Review Agents

**Acceptance Criteria:**
1. Phase 3 mandates a structured Evidence citation; Phase 4 refuses to apply/log-as-applied without one.
2. Evidenced entry passes the check; missing-citation entry fails; embedded private body/CoT fails the privacy guard.
3. `refresh-evidence` registered via one appended check function + one registry line; `eval.sh` clean.
4. `.github/workflows/eval.yml` runs the check with no file change (verified, noted).
5. `refresh-log-format.md`, `status.md`, `README.md` match reality: no "Phase 2.2", one `.writ/refresh-log.md` path, accurate transcript phrasing.
6. Pre-merge gate rejects unevidenced/eval-failing amendments and logs the reason.
7. Two real log entries exist: one merged-with-evidence, one rejected-for-lacking-evidence.

**Business Rules:**
- Cite transcript ID/path + short observable signal + affected section; never CoT or verbatim private bodies.
- Rejection is a first-class, logged outcome, not an error.
- Canonical log path is `.writ/refresh-log.md` everywhere.
- Reviewed-with-no-amendments is exempt; pre-`LEARNING_CONTRACT_SINCE` entries are grandfathered.
- The eval check is fixture-driven and deterministic; it never depends on the live log.

**Drift Anchors:**
- Reintroducing `--batch`/`--last`/promotion as real features is out of scope — reconcile docs to reality instead.
- Any LLM-as-judge Tier 2, transcript-scanning pipeline, or committed transcript body is contract drift.

---

## For Testing Agents

**Success Criteria:**
1. `python3 scripts/eval-refresh-evidence.py` passes all fixtures (evidenced, missing-citation, missing-signal, private-content, no-op, rejection, grandfathered).
2. `bash scripts/eval.sh` and `--check=refresh-evidence` are clean; the other checks are unaffected.
3. `bash scripts/gen-skill.sh --check` stays clean.

**Shadow Paths to Verify:**
- **Happy path:** evidenced proposal → gate passes → applied → evidenced log entry.
- **Nil input:** no target command → list + ask, no state change.
- **Empty input:** reviewed with zero amendments → valid no-op, exempt from evidence.
- **Upstream error:** eval-check crash → run error surfaced; amendment not written.

**Edge Cases:**
- Missing transcript citation → reject + `no evidence`.
- Transcript file absent → ID citation accepted; no fabricated body.
- Private body/CoT embedded → privacy guard fails the entry.
- High-traffic target → structural Tier 2 runs; non-allowlisted target uses base check only.

**Coverage Requirements:**
- Evidence validator and rejection path: 100% fixture coverage.
- Privacy guard and grandfathering: explicit fixtures.

**Test Strategy:**
- Temp-dir fixtures + static `require_literal` assertions; `eval.sh`, `gen-skill.sh --check`, targeted drift greps.

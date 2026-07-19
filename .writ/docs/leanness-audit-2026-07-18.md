# Leanness Audit — 2026-07-18 (Conductor-Triggered)

> **Tier B ritual** per [ADR-015](../decision-records/adr-015-leanness-self-governance.md).
> **Trigger:** Not the scheduled cadence — this audit was prompted by the competitive analysis of Conductor ([`../research/2026-07-18-writ-vs-conductor-analysis.md`](../research/2026-07-18-writ-vs-conductor-analysis.md)), which delivers a complete spec-driven-development lifecycle in **6 skills and one directory**. Conductor is used here as a *comparative foil* for questions (b) command overlap and (c) existence justification. It is a peer framework, not a harness, so the classic (a) native-displacement test applies only loosely.
> **Recommends, never deletes.** Every non-`keep` row routes to a follow-up for human decision.

## 1. Metrics Snapshot

Tier A (`python3 scripts/eval-leanness.py`), 2026-07-18:

```json
{ "structural": [], "warnings": [],
  "metrics": { "commands": 31, "agents": 7, "skills": 6,
               "command_lines": 10342, "command_chars": 469970 } }
```

Baseline (`.writ/leanness-baseline.json`, recorded 2026-07-11):

| Metric | Baseline (07-11) | Current (07-18) | Delta |
|---|---|---|---|
| commands | 31 | 31 | 0 |
| agents | 7 | 7 | 0 |
| skills | 6 | 6 | 0 |
| command_lines | 10,659 | 10,342 | **−317** |
| command_chars | 484,616 | 469,970 | **−14,646** |

**Structural health:** clean — no Tier A structural findings, no growth/ceiling warnings. Command surface **shrank** week-over-week. This is not a bloat alarm; it is a discretionary overlap/justification pass.

**Honest net-surface note:** the same Conductor analysis that prompted this audit also spawned three specs that will *add* surface — one new command (`/revert`, from `2026-07-18-logical-unit-revert`) and one new script (`revert-resolve.py`). The git-notes and artifact-integrity specs add **zero** new commands (they extend `ship`/`release`/`status`/`_preamble`/`context.md`). So the pending net is **+1 command**. This audit's prune candidates should be weighed against that addition, not treated as free headroom.

## 2. The Comparative Frame

Conductor's entire lifecycle: `setup → new-track → implement → status → review → revert` (6 skills). Writ's **core loop** is comparable and justified by greater depth: `plan-product → create-spec → implement-phase/spec/story → verify-spec → status → ship → release` (~8 commands driving a 6-gate agent pipeline Conductor has no equivalent for). **The core loop is not the leanness risk.** The risk sits in the **peripheral, meta, and lifecycle** commands — the 20+ commands outside the core loop. Those are where this audit looks.

## 3. Findings → Decisions

| Surface | Finding | Decision | Follow-up |
|---|---|---|---|
| `commands/reinstall-writ.md` | (b/c) "Nuclear fresh install" overlaps `uninstall-writ` + `install.sh` and `update-writ --force`. Conductor has no reinstall — the host plugin manager reinstalls. Dedicated command may not earn standalone surface. | **merge** (candidate) | Proposed issue: fold into `update-writ --reinstall` flag or document as `uninstall` + `install`. Route to `.writ/issues/improvements/`. |
| `commands/migrate.md` | (c) Code-Captain→Writ migration is a **one-time** operation. As the migration window closes, permanent command surface is hard to justify vs a `scripts/`-only or docs-only path. | **defer** | Roadmap note: set a sunset review; candidate to demote to `scripts/migrate.sh` + docs once migration demand tails off. |
| `commands/retro.md` | (c) Git-based retrospective — low invocation frequency; existence-justification unclear without usage evidence. | **defer** | Proposed issue: record invocation evidence over next phase; re-evaluate at next cadence audit. |
| Lifecycle cluster: `initialize`, `reinstall-writ`, `uninstall-writ`, `update-writ` (+ `install.sh`) | (b) Four lifecycle *commands* plus scripts. Conductor delegates the whole install/remove lifecycle to the host (`/plugin install|remove`). Writ can't fully delegate (4 platforms, symlink dogfooding), but the cluster is the densest peripheral surface. | **keep** (cluster) / **merge** (reinstall only) | Covered by the `reinstall-writ` row; keep the rest — cross-platform install genuinely needs Writ-owned surface. |
| `commands/assess-spec.md` vs `commands/verify-spec.md` | (b) Both "check a spec." Inspected: `assess-spec` = pre-implementation sizing/decomposition; `verify-spec` = post/metadata integrity linter. Different phases, low real overlap. | **keep** | None — distinct lifecycle positions; documented here to close the overlap question. |
| `commands/review.md` vs `agents/review-agent.md` (Gate 3) | (b) Apparent duplication. Inspected: `review` = standalone pre-landing deep review; the agent = in-pipeline gate. Complementary. | **keep** | None. |
| `commands/prototype.md` vs `implement-story --quick` | (b) Both low-ceremony. Inspected: `prototype` is **spec-less**; `--quick` is a gated story with skips. Distinct entry points. | **keep** | None. |
| `commands/research.md`, `create-adr.md`, `knowledge.md` | (b) Knowledge-capture family. Distinct outputs (investigation doc / decision record / durable ledger). | **keep** | None. |
| Meta/authoring: `new-command`, `new-skill`, `refresh-command` | (c) Dogfooding surface that builds Writ itself. Earns its place in a self-dogfooding repo. | **keep** | None. |

## 4. Summary of Recommendations

- **1 merge candidate:** `reinstall-writ` → a flag on `update-writ` (or documented compose of `uninstall` + `install`). Highest-confidence prune.
- **2 defer candidates:** `migrate` (sunset review as migration window closes), `retro` (gather usage evidence, re-evaluate).
- **Everything else: keep** — the apparent overlaps (assess/verify, review/agent, prototype/quick) resolve to genuinely distinct lifecycle positions on inspection.
- **Net:** even acting on the merge candidate, the pending `/revert` addition means command count stays ~flat. Writ is **not** bloated today; the value is in the two or three specific consolidation candidates above, not a broad cull.

## 5. Recommend-Only Guarantee

This audit deletes and merges nothing. Each non-`keep` row names a proposed follow-up (issue/roadmap note) for the maintainer to accept or reject. Pruning happens later, by a human, via the routed follow-up.

## References

- Trigger analysis — [`../research/2026-07-18-writ-vs-conductor-analysis.md`](../research/2026-07-18-writ-vs-conductor-analysis.md)
- Ritual template — [`leanness-audit-format.md`](leanness-audit-format.md)
- [ADR-015](../decision-records/adr-015-leanness-self-governance.md) — leanness self-governance
- Baseline — [`../leanness-baseline.json`](../leanness-baseline.json)

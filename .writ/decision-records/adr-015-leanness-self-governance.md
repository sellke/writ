# ADR-015: Leanness Self-Governance — A Tripwire and a Ritual, Never a Command

> **Date:** 2026-07-11
> **Status:** Accepted
> **Category:** Framework Architecture
> **Extends:** [ADR-009](adr-009-command-agent-skill-boundary.md) (the surface it measures), Design Principles #1 and #4
> **References:** [ADR-012](adr-012-ralph-deprecation.md) (the native-displacement precedent this operationalizes)

## Decision

Writ polices its own leanness through **two dogfooding-only tiers** — a
mechanical **CI tripwire** (Tier A, `scripts/eval.sh --check=leanness`) and a
cadence-bound **audit ritual** (Tier B, `.writ/docs/leanness-audit-format.md`) —
and **never through distributable, user-facing surface**. No `commands/*.md` is
added; the `/status` allowlist and `.writ/manifest.yaml` command/agent lists are
read, never changed.

Tier A hard-FAILs only on unambiguous structural bugs (command-registry parity);
count and aggregate-weight growth are **warn-only** (non-blocking, exit 0). Tier B
re-applies the "does the harness do this natively now?" test on a cadence and
produces prune *candidates* routed to ADRs, the roadmap, or issues — it
**recommends, never deletes**.

## Context

Writ's core value proposition *is* leanness — "the thin, portable methodology
layer… delegate the mechanics" (`mission.md`). Bloat is therefore an existential
threat to the value proposition, not cosmetic debt. Yet at the time of this ADR
that discipline was enforced **only culturally**: Design Principles #1/#4, the
maintainer's prune instinct (which retired `/audit`, `/lessons`, Ralph, and
`/explain-code`), and ADR-009's boundary. Nothing systematic re-applied it.

Three concrete gaps motivated this decision:

1. **Aggregate creep is unmeasured.** The existing `check_length` is per-file
   only; every command sits far under its cap while the real risk — total
   surface weight (31 commands, ~10,659 lines at the time of writing) — had no
   ceiling and no trend line.
2. **The native-displacement test ran by luck.** Principle #4 was applied once,
   manually, in the 2026 harness audit (→ ADR-010–013). Harnesses keep evolving;
   nothing scheduled the next application. Ralph became deprecated only because
   the maintainer happened to notice.
3. **Command registries drift independently.** `check_manifest` validates
   `commands/`·`agents/` ↔ `.writ/manifest.yaml`, but the README command table
   and the `/status` allowlist are separate registries with no parity check.

## Why Two Tiers

Bloat has two failure modes that need different instruments:

- **Mechanical drift** (a dead command, a registry that names a deleted file,
  runaway aggregate growth) is objective and belongs in CI, where it is caught
  on every PR without judgment.
- **Strategic obsolescence** ("the harness does this natively now," two commands
  that overlap, a command that no longer earns its place) is a *judgment* call
  that a mechanical check cannot and should not make. It belongs in a
  human-run ritual on a deliberate cadence.

Collapsing both into one mechanism would either over-block on subjective calls
or under-detect objective drift. Keeping them separate lets each stay honest.

## The Novel Structural Contribution — Directional Registry Parity

Tier A's one *new* structural check is command-registry parity that nothing else
covers. It is **directional**, because the three registries have different
contracts (see DEV-001 in the leanness-guardian `drift-log.md`):

| Registry | Contract | Parity direction |
|---|---|---|
| `commands/*.md` (minus `_preamble`) | the files that exist | — |
| README "## Commands" table | the authoritative full catalog | **bidirectional** — orphan (file with no row) and phantom (row with no file) both FAIL |
| `/status` "Maintainer Note" allowlist | a *curated suggestion subset* | **one-way** — phantom only; a command is never flagged for being absent |

The `/status` allowlist deliberately omits commands `/status` does not
proactively suggest (`knowledge`, `new-skill`, `create-uat-plan` at the time of
writing). Treating it as a full registry would either FAIL the clean repo or
force those commands into the allowlist — changing user-facing `/status`
behavior, which the dogfooding-only mandate forbids. Directionality resolves the
contradiction: the README is the catalog of record; the allowlist is checked
only for dangling references.

## Non-Duplication Boundary

The guardian must not itself become bloat. It defers, explicitly:

| Existing mechanism | Owns | Leanness guardian does NOT |
|---|---|---|
| `check_manifest` | `commands/`·`agents/` ↔ manifest parity | redo manifest parity |
| `check_length` | per-file line ceilings | check per-file length (aggregate only) |
| `lint-skill.sh` / `skill-lifecycle` | skill boundary + lifecycle | re-lint skills (counts only) |

## Warn-Only Mechanics

`add_finding` fails the run, so warnings cannot use it. This ADR introduced a
minimal, reusable `add_note` primitive in `scripts/eval.sh`: notes render in the
report even on PASS and never touch the findings counter. Count-ceiling and
aggregate-weight warnings — plus the metrics summary that feeds Tier B — flow
through it. The tripwire stays **silent** on a healthy repo and speaks only when
a real threshold breaks.

## Considered Alternatives

**A. A user-facing `/leanness` (or `/audit`) command.** Rejected. It would leak
framework-internal governance into the distributable surface — users trust Writ
as a partner, they do not audit its internals — and would itself be new surface,
contradicting the goal. This is the same reasoning that retired `/audit`.

**B. Hard-FAIL on count/weight growth.** Rejected. A legitimate large feature
would nag or block. Growth is a *signal for judgment*, not a bug; warn-only
plus a deliberate baseline bump keeps it honest without friction.

**C. Derive the weight trend from git tags (`git show <tag>:`).** Rejected for
v1. It needs tag access in CI and is less deterministic than a committed
baseline. `.writ/leanness-baseline.json` is explicit, reviewable, and bumped
deliberately — the delta is the signal.

**D. Hook the Tier B ritual into `/release` or `/implement-phase`.** Rejected.
Release cadence is too frequent (an audit there is friction), and hooking a
shipping command would leak the ritual to users. The cadence lives as documented
discipline (per-phase-close or quarterly) in `self-dogfooding.md`.

**E. LLM-as-judge overlap detection in Tier A.** Rejected for v1. Structural and
heuristic checks only; command-overlap judgment is deferred to the Tier B human
ritual.

## Consequences

**Positive:**

- Aggregate bloat and dead registry surface are caught on every PR, not by luck.
- The native-displacement test becomes a scheduled discipline with a durable,
  dated paper trail (`leanness-audit-YYYY-MM-DD.md`).
- Zero new user-facing surface; the framework's leanness promise is enforced by
  the framework's own tooling, dogfood-proof.
- `add_note` is a reusable warn primitive available to future checks.

**Negative:**

- The baseline must be bumped by hand when growth is legitimate. Mitigation:
  the warning names the file and the `--update-baseline` path; the friction is
  intentional and rare.
- Tier B depends on maintainer follow-through — a ritual, not automation.
  Mitigation: the cadence is documented and the first dated audit is committed
  as a worked example.
- The tripwire adds a small maintenance surface of its own. Mitigation: the
  non-duplication boundary is explicit, and Tier B will audit the guardian too.

## References

- Owning spec — [`2026-07-11-leanness-guardian`](../specs/2026-07-11-leanness-guardian/spec.md)
- Tripwire — [`scripts/eval-leanness.py`](../../scripts/eval-leanness.py), wired via `scripts/eval.sh` `check_leanness`
- Baseline — [`.writ/leanness-baseline.json`](../leanness-baseline.json)
- Ritual template — [`.writ/docs/leanness-audit-format.md`](../docs/leanness-audit-format.md)
- Directional-parity rationale — DEV-001 in the spec's `drift-log.md`
- [ADR-009](adr-009-command-agent-skill-boundary.md) — the command/agent/skill surface measured
- [ADR-012](adr-012-ralph-deprecation.md) — the ad-hoc native-displacement decision this ritual makes routine

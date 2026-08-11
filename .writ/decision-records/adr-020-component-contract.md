# ADR-020: The Component Contract — Every Component Declares Problem, Outcome, and Exit Criteria

> **Date:** 2026-08-11
> **Status:** Accepted
> **Category:** Framework Architecture
> **Extends:** [ADR-014](adr-014-skill-lifecycle.md) (reuses the `status:`/`evidence:` vocabulary), [ADR-019](adr-019-full-surface-leanness-measurement.md) (adds structural checks to Tier A)
> **Origin:** `/plan-product` Phase 10 discovery (2026-08-11) — measured response to a maintainer concern raised as explicitly unverified

## Decision

Every Writ component declares, in machine-readable form, **the problem it addresses, the outcome it produces, and the exit criteria that prove it finished**. Three carriers, one contract, no new mechanisms:

1. **Commands** extend the YAML frontmatter that already exists in 32/32 files:

   ```yaml
   ---
   name: implement-story
   description: "..."           # already present
   problem: "..."               # NEW — one line: what goes wrong without this command
   outcome: "..."               # NEW — one line: the artifact/state that exists after
   exit_criteria:               # NEW — 2-4 machine-checkable assertions
     - "story status is Complete in .writ/specs/<spec>/stories/"
     - "all review gates returned PASS"
   ---
   ```

2. **Agents** carry the same three fields in their existing fenced Agent Configuration block — the same carrier `model_tier` already uses (6 of 7 agents use `## Agent Configuration`; `visual-qa-agent.md` alone uses `## Agent Specification`).

3. **Skills** need no new fields. They already carry `## Purpose` and `## When to Use`; lint asserts both are present rather than inventing a parallel vocabulary.

The `## Completion` section that [`commands/new-command.md`](../../commands/new-command.md) **already mandates** becomes actually enforced rather than aspirational.

Enforcement is a **blocking `structural` finding** in `eval-leanness.py`, not a warning — but only after the surface is brought into compliance (see Consequences).

## Context

A maintainer raised the concern that Writ is "too prescriptive in some ways (wasting tokens) and not deterministic enough in other ways, given the latest and most powerful models," explicitly flagging it as **unverified**. The Prime Directive forbids confirming an assertion without checking it, so the concern was measured before any plan was written.

The determinism half measured worse than the token half:

| Measure | Value |
|---|---|
| Commands declaring a goal/outcome/problem heading | **2 of 32** (`new-skill`, `status`) |
| Commands with a `## Completion` section | **13 of 32** |
| Loop-bearing commands declaring an iteration bound | **0 of 5** |

### The finding that reframed the decision

`new-command.md` — Writ's own authoring template — **already mandates `## Completion`** in its generated command structure. Nineteen of thirty-two commands violate it.

This changes what the problem *is*. The contract is not missing; it is **unenforced**. Writ has extensive deterministic tooling (~30 `eval-*.py` scripts, a 155KB `eval.sh` harness, `lint-skill.sh`, `check-agent-parity.sh`, `phase-state.py`) covering specs, stories, phases, and skills — but **nothing that checks the commands and agents themselves**. The guardian measures its own byte count and never asks whether a command knows what it is for.

### Why frontmatter and not prose

`system-instructions.md` asserts that commands have *"no frontmatter or config-block mechanism today (verified 0/31 files)"* and therefore prescribes advisory tier as a **prose note**. That claim is now false — 32/32 commands carry `---` YAML frontmatter with `name` and `description`. The prose-note workaround was a reasonable response to a real constraint that has since disappeared, and the root contract never caught up.

Frontmatter is parseable without a grammar, survives reformatting, and costs ~4 lines. Prose headings require a rejection grammar per variant (`## Goal` vs `## Outcome` vs `## Purpose`) — exactly the fragility `lint-skill.sh` already absorbs for skill descriptions.

## Why This Is Not Another Token Tax

The contract is deliberately ~4 lines per file. Adding a mandated block to 31 commands is only defensible because [ADR-021](adr-021-progressive-disclosure-token-budget.md) removes an order of magnitude more than this adds. **The two decisions ship as a pair**; landing this one alone would make Writ heavier while calling it streamlined, which was the explicit failure mode identified during discovery.

The three fields are also the only ones that earn enforcement. `problem` and `outcome` are one line each because a component that cannot state either in one line has a scoping defect the contract should *surface*, not accommodate.

## Considered Alternatives

**Prose sections (`## Goal`, `## Exit Criteria`) instead of frontmatter.**
Rejected. Requires a heading-variant rejection grammar, is invisible to `yq`, and inflates the byte surface this phase exists to reduce. The `model_tier` prose note already demonstrates the cost — a "locked prose format" that `lint-skill.sh` must pattern-match with a bespoke regex.

**A separate `contract.yaml` sidecar per command.**
Rejected. Doubles the file count, splits a component's identity across two files, and breaks the single-file-is-the-component property that makes `install.sh` fan-out and the symlink dogfooding model work.

**Enforce only `outcome`, skip `problem` and `exit_criteria`.**
Rejected. `outcome` alone is what `description:` already approximates. The maintainer's ask was explicitly that each component "understand the problem you are trying to address" — dropping `problem` drops the request. Dropping `exit_criteria` leaves the determinism gap untouched, which is the higher-severity half.

**Generate the fields automatically from existing prose.**
Rejected as the *primary* mechanism. A generated `problem:` line restates the command's overview rather than interrogating whether the command has a distinct reason to exist. Authoring by hand is where the audit value lives. Generation remains acceptable as a *first-draft* aid during migration.

**Do nothing — trust capable models to infer intent.**
This is the strongest alternative and deserves a real answer. Modern models genuinely do infer purpose from a well-written command file. But inference is not enforcement: it cannot fail a build, it varies run to run (the maintainer's "not deterministic enough" observation), and it does not stop a 20th command from shipping without exit criteria. The contract's value is that it is *checkable*, not that it is *informative*.

## Consequences

**Positive**

- 31 commands and 7 agents become machine-auditable for goal orientation; a missing contract fails `eval.sh` instead of passing silently.
- `## Completion` compliance goes from 13/32 to 31/31, closing a template violation that has been accumulating unnoticed.
- `exit_criteria` gives `/verify-spec` and `/refresh-command` a declared target to check against rather than inferring intent from prose.
- Reuses ADR-014's `status:`/`evidence:` vocabulary when extended to commands and agents, so `/refresh-command`'s existing Evidence Gate accrues per-component evidence with no parallel lifecycle.

**Negative**

- ~4 lines × 38 files of new surface. Honest cost, and it is only net-positive paired with ADR-021.
- A migration pass touching every command and agent file — mechanical but broad, and it will conflict with any concurrent command edits.
- `exit_criteria` written as prose assertions are only *nominally* machine-checkable. The lint can verify the field exists and is non-empty; it cannot verify the assertion is true. This is a real limit, not a hidden one — the field's value is forcing the author to name a falsifiable condition.
- Three new required fields is three new things `/new-command` must coach, and three new ways a hand-authored command can fail lint.

**Enforcement sequencing (load-bearing)**

New structural checks land as **`warnings` first** and flip to blocking `structural` only once the migration brings the surface into compliance. Landing them blocking on day one turns every eval run red, and a permanently-red gate becomes invisible — which is exactly how the four currently-live unjustified-growth warnings came to be ignored.

**Review trigger: 2026-11-11** (90 days post-ship, matching the discipline in ADR-014 and the `required_skills:` convention). If `exit_criteria` fields have not been consumed by any check, command, or agent beyond presence-linting by that date, reduce the contract to `problem` + `outcome` and cut `exit_criteria` rather than carrying an unused mandated field.

## References

- Roadmap: [Phase 10 — Component Contract & Progressive Disclosure](../product/roadmap.md)
- Paired decision: [ADR-021](adr-021-progressive-disclosure-token-budget.md) — the token reduction that makes this contract affordable
- Autonomy boundary: [ADR-022](adr-022-autonomy-gate-classes.md)
- Reused vocabulary: [ADR-014](adr-014-skill-lifecycle.md) — `status:`/`evidence:` earned-state model
- Extended harness: [ADR-019](adr-019-full-surface-leanness-measurement.md), [`scripts/eval-leanness.py`](../../scripts/eval-leanness.py), [`scripts/eval.sh`](../../scripts/eval.sh)
- Authoring template to update: [`commands/new-command.md`](../../commands/new-command.md)
- Stale claim to correct: [`system-instructions.md`](../../system-instructions.md) — *"verified 0/31 files"*

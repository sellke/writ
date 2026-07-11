# ADR-014: Skill Lifecycle — Earned-State Maturity for Skills

> **Date:** 2026-07-10
> **Status:** Accepted
> **Category:** Framework Architecture
> **Extends:** [ADR-009](adr-009-command-agent-skill-boundary.md) (command/agent/skill boundary)

## Decision

Writ skills gain a **lifecycle** expressed as a required `status:` frontmatter
field with a closed three-state vocabulary — `candidate → proven → promoted` —
where every non-`candidate` state is **earned from recorded evidence**, never
merely asserted. A skill's declared state is a *function of the evidence present
in its own frontmatter*; the state can be proven statically, from one file, with
no dependence on git history or the network.

This is a **new orthogonal axis** on top of ADR-009's classification. ADR-009
answers *"is this work a command, an agent, or a skill?"* (the boundary). This
ADR answers *"how mature is this skill?"* (the lifecycle). ADR-009's
classification rules are untouched — this ADR extends the boundary set, it does
**not** supersede it.

## Context

ADR-009 established skills as the third Writ primitive (verb/noun/tool =
command/agent/skill) with a boundary lint (`scripts/lint-skill.sh`) enforcing
the role convention. It deliberately left maturity out of scope: a skill was
either present or absent, with no notion of whether it had earned its place.

As the skill-extraction pilots begin (`2026-07-10-skill-extraction`), the
framework needs a way to distinguish a *provisional* skill (just scaffolded, no
real use yet) from a *load-bearing* one (used across multiple consumers) from a
*structurally depended-upon* one (declared in a consumer's `required_skills:`).
Without this, the catalog treats a day-old scaffold identically to a skill three
consumers rely on — and reviewers have no signal about which skills are safe to
build on.

## The Earned-State Model

The lint sees **one file at a time** — no history, no cross-file state. So
"legal transition" is reframed as **"the declared state is earned by the
evidence present."**

| State | Evidence bar | Meaning |
|---|---|---|
| `candidate` | 0+ entries (none required) | Provisional; born state from `/new-skill` |
| `proven` | ≥3 well-formed evidence entries | In real use across consumers |
| `promoted` | `proven` bar **and** ≥1 entry with `type: promotion` | A consumer structurally depends on it |

Because each state's evidence bar is a **strict superset** of the one below, the
ladder is **monotone**: a valid `promoted` statically implies the `proven` and
`candidate` bars were met, so `candidate → promoted` skipping is
*unrepresentable*. The state you can validly declare is exactly the highest state
your evidence earns.

Demotion (editing `proven` back to `candidate`) is a **manual maintainer
action** the lint does not police — the lint only ever proves the *current*
declared state is earned. There is no `/promote-skill` command and no automated
transition; state changes are ordinary frontmatter edits, gated by the lint.

## Evidence Schema

Non-`candidate` states carry an `evidence:` block — a YAML list of typed
entries. Each entry requires **all four** fields:

```yaml
status: proven
evidence:
  - date: 2026-05-06
    type: usage
    ref: commands/ship.md
    note: "Cited as the commit-message authority in /ship's commit phase."
```

| Field | Format | Meaning |
|---|---|---|
| `date` | `YYYY-MM-DD` | When the evidence was recorded |
| `type` | `usage \| transcript \| eval \| promotion` | Class of evidence |
| `ref` | repo-relative path or transcript UUID | Pointer to the evidence |
| `note` | one line | Human-readable justification |

`type` semantics:

- `usage` — a consumer command or agent file wields the skill.
- `transcript` — a recorded agent-transcript UUID shows a successful application.
- `eval` — a passing eval check exercises the skill.
- `promotion` — a consumer declares the skill in its `required_skills:` frontmatter.

The lint validates **well-formedness and thresholds only** — presence,
vocabulary, count, the promotion record, and the four-field shape. It never
fetches or verifies that a cited path or transcript UUID is genuine. Evidence
*truth* is a human review responsibility, deliberately out of scope; the lint
guarantees the *shape* of an earned claim, not the honesty of its citations.

This schema is **finalized by this ADR and its owning spec**
(`2026-07-10-skill-lifecycle`) and is consumed **unchanged** by
`2026-07-10-skill-extraction`. Every skill that spec extracts is born
`status: candidate`.

## Three-Success Threshold Provenance

The `proven` bar of **three** well-formed evidence entries ports GStack's
"active after three successes" domain-skill quarantine model: a skill earns
trust by demonstrating repeated successful application rather than by a single
lucky use or an author's assertion. Three is the smallest count that
distinguishes a pattern from a coincidence while staying cheap to reach for a
genuinely useful skill. Encoding it as an **evidence-count rule** (rather than a
separate boolean flag) keeps the schema declarative and the lint stateless —
the count *is* the earned-state test.

## Manifest Carries a Render Mirror

`status:` lives in **two** places, exactly as `description:` already does:

- `skills/<name>/SKILL.md` frontmatter — **authoritative**. The lint validates
  this.
- `.writ/manifest.yaml` skills entry — a **render mirror** used only by
  `scripts/gen-skill.sh` to populate the catalog's `Status` column.

The frontmatter is always the source of truth. The manifest value is metadata;
the generator defaults a missing manifest `status:` to `candidate` so
downstream-appended entries render even before evidence accrues. Drift between
the two is a documented author responsibility — the same discipline already
required for `description:` — not a lint-enforced invariant.

## Static Transition Legality

The key design move is treating transition legality **statically**. A
history-aware validator would need to know a skill *was* `candidate` before
becoming `proven`. Instead, by making each higher state's evidence bar a strict
superset of the lower state's, the declared state is provably earned from the
frontmatter alone. This keeps the single validator (`lint-skill.sh`) pure,
one-file-at-a-time, and identical across every invocation path — `/new-skill`
authoring, `/refresh-command --lint-skills` review, and `scripts/eval.sh` CI.

## Considered Alternatives

**A. Track lifecycle in git history / commit trailers.** Rejected: it makes the
validator history-dependent and non-reproducible, breaks single-file review, and
couples skill maturity to VCS mechanics. The evidence-in-frontmatter model is
self-contained and works offline.

**B. A separate `promoted` boolean axis instead of a ladder state.** Rejected:
a second axis complicates the catalog column and the mental model. Modeling
promotion as an evidence `type: promotion` entry keeps the ladder
one-dimensional — one word describes a skill's maturity.

**C. A dedicated `/promote-skill` command with automated transitions.**
Rejected as out of scope and over-engineered. State transitions are ordinary
frontmatter edits gated by the lint; automation can come later if the manual
flow proves painful.

## Consequences

**Positive:**

- Maturity is visible at a glance in the catalog `Status` column, and every
  label is provably earned.
- The schema is a stable, statically-checkable seam that the skill-extraction
  spec consumes unchanged.
- The validator stays pure and stateless — one file, no history, no network.
- The ladder's monotonicity makes state-skipping unrepresentable.

**Negative:**

- Authors must record evidence by hand as a skill sees use. Mitigation: the
  born `candidate` state requires none, so the cost is only paid when claiming
  maturity.
- The manifest mirror can drift from the frontmatter. Mitigation: same
  documented discipline as `description:`; the frontmatter is always
  authoritative and the generator defaults gracefully.
- The lint validates shape, not truth — a determined author could cite fake
  evidence. Accepted: verifying citation genuineness is a human review job, and
  fabricated evidence is a social failure the lint is not designed to catch.

## References

- [ADR-009](adr-009-command-agent-skill-boundary.md) — the command/agent/skill
  boundary this ADR extends (classification unchanged; lifecycle is a new axis)
- Owning spec — [`2026-07-10-skill-lifecycle`](../specs/2026-07-10-skill-lifecycle/spec.md)
- Downstream consumer — `2026-07-10-skill-extraction` (consumes this schema unchanged)
- Lint grammar — [`scripts/lint-skill.sh`](../../scripts/lint-skill.sh)
- User-facing explainer — [`.writ/docs/skills.md`](../docs/skills.md)
- GStack "active after three successes" quarantine model — [garrytan/gstack](https://github.com/garrytan/gstack)

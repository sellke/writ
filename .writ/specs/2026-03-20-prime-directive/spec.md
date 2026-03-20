# Spec: Prime Directive

> **Status:** Complete
> **Created:** 2026-03-20
> **Spec Type:** Product Enhancement

## Contract

**Deliverable:** Inline anti-sycophancy prime directive into `system-instructions.md` and `cursor/writ.mdc`, replacing the phantom reference to `.writ/docs/best-practices.md`.

**Origin:** Research-backed. Synthesized from ELEPHANT benchmark (Microsoft/ICLR 2026), SYCOPHANCY.md open protocol, aviation FORDEC decision model, and Anthropic's Claude Constitution. See `.writ/research/2026-03-20-anti-sycophancy-prime-directive-research.md`.

**Must Include:** Specific, behavioral principles that change agent behavior — not aspirational statements.

**Hardest Constraint:** Under ~35 lines added. This content loads every session via `alwaysApply: true` — context budget matters.

## Background

Both `system-instructions.md` (line 32) and `cursor/writ.mdc` (line 32) reference `.writ/docs/best-practices.md` for "critical thinking guidelines." That file has never existed. Every Writ session wastes context on a failed read and misses the behavioral guidance the reference promises.

The gap was identified in an architecture review of the full Writ pipeline. Research confirmed that AI sycophancy — prioritizing user approval over truth — is structural (baked into RLHF training data) and that vague instructions like "be honest" are insufficient to overcome it. Effective anti-sycophancy requires specific, behavioral rules.

## Prime Directive Content

The following replaces the phantom reference. It's structured as **3 hard constraints** (things that are always wrong, from SYCOPHANCY.md patterns) and **5 judgment principles** (things that shape thinking, from FORDEC + Anthropic Constitution):

```markdown
## Prime Directive

Writ's first obligation is honest assessment, not comfortable agreement.

### Hard Constraints

These are non-negotiable. Every command, every agent, every session.

- **Never reverse a position without new evidence.** If the user pushes back
  and you still believe you're right, say so. Reversals require new information,
  not pressure.
- **Never confirm an assertion without verifying it.** If the user says "this
  approach should work," check before agreeing. Silent agreement is the most
  dangerous form of sycophancy.
- **Never pad responses with empty affirmation.** No "Great question!" or
  "Excellent point!" unless the question or point is genuinely exceptional.
  Filler erodes trust.

### Judgment Principles

These shape how you think, not what you must do.

- **Separate facts from assumptions before recommending.** State what you
  verified vs. what you're inferring. Label uncertainty explicitly.
- **Generate alternatives.** The first workable solution is rarely the best one.
  Present options with honest trade-offs — even when one option is clearly
  stronger, name what you're giving up.
- **Name problems early.** When a request has issues — technical, scope, or
  logical — say so with evidence, then offer a better path. "Here's what I'd
  change and why" over "looks good."
- **Match confidence to evidence.** Strong claims need strong backing. When
  uncertain, say "I think" or "my best assessment is" — never assert what you
  haven't checked.
- **Disagree with evidence, not attitude.** Pushback should feel like a
  colleague raising a concern, not a critic finding fault.
```

## Implementation Approach

This is a product source change — edits to `system-instructions.md` and `cursor/writ.mdc` ship to all Writ installations via `install.sh`. No install script changes needed.

**Self-dogfooding note:** In this repo, `.cursor/rules/writ.mdc` is a symlink to `cursor/writ.mdc` and `.cursor/system-instructions.md` is a symlink to `system-instructions.md`. Editing the product source files automatically updates the active installation.

## Success Criteria

1. The phantom reference to `.writ/docs/best-practices.md` is removed from both files
2. The Prime Directive section is present and identical in both files
3. Total addition is under 35 lines
4. `install.sh` requires no changes
5. Both files remain valid markdown with clean structure
6. The CHANGELOG is updated for the release

## Scope Boundaries

**Included:**
- `system-instructions.md` — replace line 32 reference with Prime Directive section
- `cursor/writ.mdc` — same change, keeping in sync
- `CHANGELOG.md` — new entry documenting the change
- `VERSION` — bump to 0.7.0

**Excluded:**
- No `.writ/docs/best-practices.md` file created (the reference is removed, not fulfilled)
- No changes to commands, agents, or `install.sh`
- No per-project playbook / living doc feature (deferred)
- No file ownership boundary enhancement for agents (captured separately)

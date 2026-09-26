# Architecture Lint and Drift-Guard Follow-ups

> **Status:** Not Started
> **Created:** 2026-09-26
> **Owner:** @unknown
> **Dependencies:** []
> **Origin:** Follow-up issues filed by `2026-09-26-drift-arch-guards`: [ac-trace fixture scan](../../issues/bugs/2026-09-26-ac-trace-scans-fixture-ac-tokens.md) (already resolved, counted as open), [gen-codex-agent-tomls crash](../../issues/bugs/2026-09-26-gen-codex-agent-tomls-crashes-on-evaluator-agent.md), [architecture rules as lint](../../issues/features/2026-09-26-architecture-rules-as-lint.md). Evidence: 6 of 8 `codex/agents/*.toml` differ from the generator's output with no check catching it; `/status` and `.writ/context.md` count every issue file as open; Gate 2 runs project linters but never reports whether an architecture ruleset exists.

## Specification Contract

**Deliverable:** Follow-ups from drift-arch-guards: Codex agent TOMLs that cannot silently drift from their sources, a convention for closing an issue, and an architecture-rules-as-lint path. Gate 2 detects and runs a project's architecture ruleset, a shipped guide explains how to write one, and `/create-adr` suggests one.

**Must Include:** A freshness check that fails `eval.sh` whenever a Codex TOML differs from what the generator would write.

**Hardest Constraint:** Detecting rulesets across ecosystems without installing tools or touching the network, and without adding a new blocking gate.

**Stories:**
1. **Codex TOML freshness.** Add the `evaluator-agent` entries, a `--check` mode, regenerate all 8 TOMLs, and add an `eval.sh` check plus a pytest.
2. **Issue-closure convention.** `commands/status.md` (open count and stale-untriaged list), `skills/project-context-snapshot/SKILL.md`, and a closing step in `commands/create-issue.md`. The fixture-scan issue then counts as closed.
3. **Ruleset detection and Gate 2 wiring.** New `scripts/arch-lint.py detect` helper, Gate 2 running detected tools, an `arch-lint:` story-report line, and ratchet re-pins.
4. **Guidance doc and ADR hook.** New `.writ/docs/architecture-lint.md` with one minimal example per ecosystem, and `/create-adr` suggesting an enforcement rule when a decision constrains layering or imports. Depends on Story 3.

**Success Criteria:** `gen-codex-agent-tomls.py --check` passes and the `eval.sh` check fails on a hand-edited TOML. `/status` excludes the fixture-scan issue from the open count. Fixture repos for each ruleset type are detected correctly. Full test suite green and `eval.sh` Findings 0.

**Scope Boundaries:**
- **Included:** the four stories above.
- **Excluded:** writing rulesets for user projects; tools beyond the four named; `/plan-product` suggestions; the review-gap issue (`2026-09-26-drift-arch-guards-residuals`) and the archived-coverage issue; archiving `2026-09-26-drift-arch-guards` (post-merge).

**⚠️ Technical Concerns:**
- A detected ruleset's violations fail Gate 2 through the existing lint path (the path eslint failures already take). A missing ruleset never blocks. Approved at contract lock.
- `commands/status.md` sits about 750 bytes under its byte budget, so Story 2's edit must be tight. `commands/implement-story.md` is over budget; Story 3 re-pins its ratchet with disclosure.

**💡 Recommendations:** Build on `feat/drift-arch-guards`; `main` does not have the ac-trace attribution fix yet.

---

## 🎯 Experience Design

**Entry point.** `/implement-story` Gate 2 (automatic); `/create-adr` when a decision sets a layering or import constraint; `/status` and `.writ/context.md` for issue counts.

**Happy path.** A project with dependency-cruiser or import-linter configured has that ruleset run in Gate 2 next to eslint and ruff, and the story report says `arch-lint: dependency-cruiser`. A project without one sees `arch-lint: none` and a pointer to the guide.

**Moment of truth.** An import across a forbidden layer fails Gate 2 mechanically, with no agent judgment.

**Feedback model.** One `arch-lint:` line per story report. Open-issue counts drop as issues gain a `## Resolution` section.

**Error experience.** A ruleset configured but not installed → `arch-lint: import-linter (not installed)`; it never fails the gate and never auto-installs. An unreadable config → `unverifiable` with the path named.

### State Catalog

| State | What the user sees |
|---|---|
| Ruleset detected and run | `arch-lint: dependency-cruiser` (violations fail Gate 2 via the lint path) |
| Ruleset runs elsewhere | `arch-lint: eslint-plugin-boundaries (via eslint)` / `archunit (via tests)` |
| Configured, not installed | `arch-lint: import-linter (not installed)` |
| No ruleset | `arch-lint: none — see .writ/docs/architecture-lint.md` |
| Unreadable config | `arch-lint: unverifiable (config_unreadable <path>)` |
| Stale Codex TOML | `eval.sh` finding naming the stem |
| Closed issue | absent from `/status` open count and stale-untriaged list |

---

## 📋 Business Rules

1. **Missing ruleset never blocks.** It is a report line only.
2. **Detected ruleset uses the existing lint path.** Violations fail Gate 2 as any lint failure does: auto-fix where possible, else flag for review. No new gate.
3. **Run only standalone checkers.** v1 runs dependency-cruiser and import-linter. eslint-plugin-boundaries (already inside eslint) and ArchUnit (inside the test suite) are reported, not re-run.
4. **Read-only and offline detection.** Detection never installs a tool; npx runs with `--no-install`.
5. **Closed means `## Resolution`.** An issue is closed exactly when its file has a `## Resolution` heading. Closed issues stay in place and are left out of open counts in `/status` and `.writ/context.md`.
6. **The generator is the only TOML writer.** Every `agents/*.md` needs `PURPOSES` and `SANDBOX` entries; purposes match `.writ/manifest.yaml`.
7. **Lean sibling untouched.** `commands/implement-story.lean.md` stays byte-identical; the byte-budget and SHA ratchets are re-pinned with dated disclosure comments.

---

## Detailed Requirements

### Codex TOML freshness (Story 1)

`python3 scripts/gen-codex-agent-tomls.py [--check]`. Write mode validates every stem before writing any file, so an unmapped stem exits non-zero with nothing written. `--check` writes nothing and prints helper-family output: `pass`/`fail`, `reason: stale|missing|orphan|unmapped <stem>` lines, summary last; exit 0 pass, 1 fail, 2 usage.

### Issue closure (Story 2)

An issue file with a line `## Resolution` is closed. `/status` Step 5 and the Open Issues count skip closed issues; the snapshot skill counts open issues only; `/create-issue` documents how to close (append `## Resolution` with date and what changed; never delete or move).

### Ruleset detection (Story 3)

`python3 scripts/arch-lint.py detect [--repo .]` prints `pass` or `unverifiable`, one `tool:` line per detected ruleset (name, mode, config), one `command:` line per runnable tool, `reason:` lines, and a summary last. Gate 2 runs each `command:` through its existing lint failure path and the story report carries the `arch-lint:` line.

### Guidance and ADR hook (Story 4)

`.writ/docs/architecture-lint.md` ships via `install.sh`. `/create-adr` Step 4's "After writing" adds one step: when the decision constrains layering, import direction, or module dependencies, add an **Enforcement** note naming a lint rule and linking the guide.

## Implementation Approach

One new helper (`scripts/arch-lint.py`, stdlib, Python 3.9), one extended generator, prose edits in existing command steps and gates, no new gate numbers. Every helper change is test-first; command prose is pinned by wiring tests; `eval.sh` gains one check for TOML freshness.

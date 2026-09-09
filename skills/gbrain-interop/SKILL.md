---
name: gbrain-interop
description: "Route knowledge retrieval brain-first when a healthy GBrain index is detected — cite the canonical markdown path, keep writes markdown-first, and fall back to grep when a brain is absent or unhealthy."
disable-model-invocation: true
status: candidate
status_evidence: "Authored 2026-07-11 for the gbrain-compatibility-recipe spec. 0 consumers cite it; proven needs >=3 — see ADR-014."
---

# GBrain Interop

## Purpose

Decide where a retrieval query goes when a project may or may not run an
external [GBrain](https://github.com/garrytan/gbrain) index over its markdown.
When a healthy brain is present, semantic recall (`gbrain search`) answers "what
did we decide about X?" questions across specs, ADRs, and knowledge entries
better than grep. When no brain is present — the common case — retrieval falls
back to grep over `.writ/` with no change in behavior.

This capability covers retrieval routing only. It never changes the canonical
store: markdown in git is the system of record, GBrain is a disposable
read-acceleration layer over it, and removing the index leaves `.writ/`
byte-for-byte intact. The consumer decides what to retrieve and why; this skill
decides which path answers the query without taking a dependency.

## When to Use

- An agent or command needs prior project knowledge — a past decision, a
  convention, a glossary term, a spec detail, or an ADR — on a project where a
  GBrain index may be registered over `.writ/`.
- A semantic or fuzzy question ("where did we handle rate limiting?") would beat
  an exact-string grep, and a brain, if healthy, can answer it with citations.
- Writing durable knowledge back to the project: the write lands in markdown
  first, then the index re-syncs.
- Not the right tool when the query is a plain exact-string search that grep
  already answers well, or when no `.writ/` substrate exists yet — detection
  degrades to grep.

## How to Apply

### 1. Detect — read health, not PATH

A `gbrain` binary on PATH is **not** a healthy brain. Detect by reading the
health check, and treat only `ok` or `warnings` as "present":

```bash
gbrain doctor --json
# → {"status": "ok" | "warnings" | "error", "health_score": <n>, "checks": [...]}
```

| `doctor` result | Routing verdict |
|---|---|
| `status: ok` or `status: warnings` | Brain **present** → route brain-first |
| `status: error` | Treated as **absent** → grep fallback |
| binary missing / command fails / MCP tools absent | **Absent** → grep fallback |

In an MCP host, the equivalent presence signal is that the `mcp__gbrain__*`
tools (e.g. `mcp__gbrain__search`) are registered and callable. If neither the
CLI nor the MCP surface is available, the brain is absent.

### 2. Route — brain-first only when detected

When the brain is present, prefer semantic retrieval over grep for
knowledge/spec/ADR questions:

```bash
gbrain search "how do we detect a healthy brain"
```

In an MCP host, call `mcp__gbrain__search` with the same query. Reserve grep for
exact-string needs (a specific symbol, a literal filename, a config key) where
a lexical match is wanted. Brain-first is a preference: if a brain search
returns nothing useful, grep the markdown directly.

### 3. Cite — always point at the canonical markdown path

Every retrieved answer must name the reviewable markdown file it came from
(e.g. `.writ/decision-records/adr-011-...md`, `.writ/knowledge/...`), so a human
can open and verify it. Never present an index row as the authority. If a result
cannot be traced back to a canonical file, treat it as untrusted and confirm
against the markdown before relying on it.

### 4. Write — markdown-first, then re-index

Durable knowledge is written to `.writ/` markdown files first, exactly as it
would be without any brain. Only after the canonical write lands does the index
catch up:

```bash
# 1. Edit the canonical markdown under .writ/ (the authoritative write)
# 2. Re-index so the brain reflects it:
gbrain sync
```

Never write durable Writ knowledge *only* into GBrain (`gbrain put` into the
index without a backing markdown file). The round-trip guarantee does not cover
such data; removing the brain would lose it.

### 5. Degrade — absence is a clean no-op

On a machine with no brain (or an `error`-status one), routing falls back to
grep over `.writ/` and nothing changes in the normal workflow. Announce the
fallback at most once per session, then stay silent — do not re-probe or narrate
on every query. A missing brain is never a hard failure and never blocks a
command.

## Examples

**Healthy brain — semantic recall with a markdown citation:**

```text
Query: "what did we decide about external memory indexes?"
detect: gbrain doctor --json → status: ok        → brain present
route:  gbrain search "external memory index policy"
cite:   → ADR-011 (.writ/decision-records/adr-011-memory-interop-markdown-canonical.md):
          "markdown canonical, indexes disposable"
```

**No brain — invisible grep fallback, no behavior change:**

```text
Query: "where is the rate-limit config?"
detect: gbrain doctor --json → command not found  → brain absent
route:  grep over .writ/ (unchanged retrieval path); no notice printed
```

**Unhealthy brain — installed but broken is still absent:**

```text
detect: gbrain doctor --json → status: error      → treat as absent
route:  grep fallback; point the user at `gbrain doctor` if they want the index back
```

> Human setup — installing GBrain, registering `.writ/` as a source, the
> artifact→page tag mapping, MCP registration, and the removal path — lives in
> the recipe at `.writ/docs/gbrain-recipe.md`. This skill covers routing only.

## Evidence

Born `candidate` on 2026-07-11 with **0 evidence entries**, the valid born
state for a new skill under ADR-014. No `evidence:` block is required while
`candidate`.

**No consumer, by design (verified 2026-09-06).** No command, agent, or adapter
loads this skill at a point of need. The adapters' "Native Memory & the Writ
Ledger" sections cross-link it as the external-index layer but do not invoke
it, because no Writ workflow depends on a brain being present: retrieval
already degrades to grep with no behavior change. `candidate` is the lifecycle
state the lint accepts for a skill with zero consumers, and it stays here until
one exists. What would make a consumer: a command or agent that loads this file
inline before a knowledge-retrieval step on a project with a registered brain —
that use is the first evidence entry. Promotion requires evidence:

- **→ proven** requires ≥3 well-formed `evidence:` entries (`date`, `type`,
  `ref`, `note`) recording real use — e.g. a command or agent that routes
  retrieval through this skill, or a transcript/eval demonstrating brain-first
  recall with a markdown citation.
- **→ promoted** additionally requires ≥1 entry of `type: promotion` citing a
  consumer that declares `gbrain-interop` in its `required_skills:` frontmatter.

See [ADR-014](../../.writ/decision-records/adr-014-skill-lifecycle.md) for the
earned-state model.

# Phase 8: GBrain Compatibility Recipe (Lite)

> Source: `.writ/specs/2026-07-11-gbrain-compatibility-recipe/spec.md`
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Make an external [GBrain](https://github.com/garrytan/gbrain) index optionally consume Writ's markdown — one agent-facing skill (`gbrain-interop`) + one user-facing recipe doc (`.writ/docs/gbrain-recipe.md`). Zero new Writ infrastructure; markdown in git stays the only system of record.

**Implementation Approach:**
- `skills/gbrain-interop/SKILL.md`: routing capability — detect a brain (`gbrain doctor --json` status), prefer `gbrain search` / MCP `mcp__gbrain__search` over grep for semantic knowledge/spec/ADR queries when detected, cite the canonical markdown path in results, write markdown-first (edit `.writ/`, then `gbrain sync`), degrade to grep when absent. Role convention: verb-phrase `description:`, `disable-model-invocation: true`, `status: candidate`, `## Evidence` section.
- `.writ/docs/gbrain-recipe.md`: human setup — register `.writ/` as a source (`gbrain sources add` + `gbrain sync`), artifact→page tag mapping (`spec`/`adr`/`knowledge-*`), optional MCP (`gbrain serve`, `claude mcp add gbrain -- gbrain serve`), round-trip guarantee + removal, `.gbrain-source` gitignore note, version-tracking boundary.
- Register in `.writ/manifest.yaml`; regenerate root `SKILL.md` with `scripts/gen-skill.sh` (idempotent).

**Files in Scope:**
- `skills/gbrain-interop/SKILL.md` (new), `.writ/docs/gbrain-recipe.md` (new)
- `.writ/manifest.yaml` (skills entry), `SKILL.md` (regenerated)
- Do NOT edit `scripts/eval.sh` or adapters — owned by the sibling `native-memory-guidance` spec.

**Error Handling / Graceful Absence:**
- GBrain not on PATH / `doctor` returns `error` / MCP unavailable → clean no-op fallback to grep; never a hard failure.
- Detection reads `gbrain doctor --json` status, never a bare `command -v gbrain`.
- No behavior change on a machine without GBrain — absence is the default, common case.

**Grounding (verified — do not invent):**
- Real upstream: `garrytan/gbrain`; GStack `USING_GBRAIN_WITH_GSTACK.md`.
- Real commands: `gbrain sources add`, `gbrain sync`, `gbrain doctor --json`, `gbrain search`, `gbrain put/get`, `gbrain serve`.
- `gbrain sources add` writes a `.gbrain-source` pin file to repo root (gitignore it).

---

## For Review Agents

**Acceptance Criteria:**
1. Skill exists, lint-clean (`scripts/lint-skill.sh`), `disable-model-invocation: true`, born `candidate`.
2. Registered in `manifest.yaml` + regenerated root `SKILL.md`; `gen-skill.sh` second run is a no-op diff.
3. `gbrain-recipe.md` documents real-interface source registration, page mapping, MCP, brain-first retrieval, graceful absence.
4. Round-trip guarantee stated with a concrete removal path; canonical data never lives only in the index.
5. Detection is observable (`doctor --json` status); absence is a clean no-op.
6. Every cited GBrain command is real; version boundary named. No fabricated flags.

**Business Rules / Drift Anchors:**
- Markdown canonical; GBrain disposable (ADR-011). Never write durable knowledge only into GBrain — that is drift.
- Opt-in + gracefully absent; any always-on hook, preamble injection, or hard dependency on GBrain is out of scope.
- Zero Writ-owned index/database/daemon (ADR-005). Any is drift.
- Editing `scripts/eval.sh` or adapters here is scope drift (sibling spec owns them).

---

## For Testing Agents

**Verification (script/static, no app test suite):**
- `bash scripts/lint-skill.sh skills/gbrain-interop/SKILL.md`
- `bash scripts/gen-skill.sh && git diff --exit-code SKILL.md`
- `bash scripts/eval.sh --check=memory-interop` (sibling-owned check; this spec's artifacts must satisfy it) and full `bash scripts/eval.sh`

**Shadow Paths:**
- No GBrain installed → detection "absent," grep fallback, no output in normal workflow.
- `gbrain` on PATH but `doctor` status `error` → treated as absent, grep fallback.
- Brain healthy → brain-first retrieval, result cites markdown path.

**Edge Cases:**
- `.gbrain-source` pin file must be gitignored, never committed as canonical.
- Version-specific flags (sync strategy, embedding keys) documented as version-sensitive, not frozen.

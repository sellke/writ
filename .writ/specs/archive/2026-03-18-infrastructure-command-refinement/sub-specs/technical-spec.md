# Technical Spec: Infrastructure Command Refinement

> **Spec:** 2026-03-18-infrastructure-command-refinement
> **Scope:** commands/migrate.md, commands/prisma-migration.md, commands/test-database.md

## Architecture

No architectural changes. This is a content refinement — same files, same locations, same command behavior. The only change is what's written in each file.

## Approach

Apply the same litmus test and simplification patterns proven across 4 prior refinement specs (core, secondary, utility, remaining). The infrastructure commands follow the same anti-patterns but in a different domain (database/Docker vs. workflow).

## Per-File Strategy

### migrate.md

**Organizing spine:** Scan → Plan → Execute → Verify → Report

**Sections to preserve verbatim or near-verbatim:**
- What Changes / What Does NOT Change tables (lines 9–19, 21–29)
- Modes table (lines 33–39)
- Rollback section (lines 326–337)

**Sections to compress to principles:**
- Phase 2 execution (lines 139–268) — ~130 lines of bash → ~30 lines of what-to-do principles
- FAQ (lines 356–371) — ~16 lines → keep only entries that prevent real confusion
- Phase 3 verification (lines 272–320) — preserve integrity check logic, cut exact output format

**Key cross-references:**
- `scripts/install.sh` — referenced in Step 2.4 for source resolution
- `.cursor/commands/`, `.cursor/agents/` — install targets
- `.code-captain/` → `.writ/` — the core rename

### prisma-migration.md

**Organizing spine:** Detect Setup → Validate → Safety Checks → Create Migration → Deploy

**Sections to preserve verbatim or near-verbatim:**
- Setup detection logic (lines 49–83)
- Safety check framework — 4 checks (lines 155–230)
- Deployment option branching (lines 336–357)

**Sections to compress to principles:**
- Dialog mockups throughout — replace with "what to communicate" principles
- Step 5 interactive creation (lines 235–305) — the conversational flow is valuable, exact prompts are not
- Error scenarios (lines 536–617) — keep as detection → resolution principles
- Step 3 dev/prod separation (lines 87–150) — preserve the offer and branching, cut step-by-step Neon console instructions

**Key cross-references:**
- `/test-database` — referenced in error recovery ("Run /test-database to diagnose issues")
- `.writ/docs/migrations/` — deployment checklist storage

### test-database.md

**Organizing spine:** Scan → Test (3 layers) → Auto-Fix (safe) → Request Fix (destructive) → Validate → Report

**Sections to preserve verbatim or near-verbatim:**
- Detection targets list (lines 59–75)
- Safe auto-fix classification (lines 116–144)
- Destructive fix request patterns (lines 155–200)

**Sections to compress to principles:**
- Step 2 scanning (lines 46–75) — merge detection targets into principles
- Step 6 validation (lines 205–230) — compress to what-to-verify principles
- Step 7 report (lines 235–308) — replace exact report templates with reporting principles
- Error Handling & Recovery (lines 393–408) — already good; compress slightly

**Sections to cut entirely:**
- AI Implementation Prompt (lines 338–378) — restates entire spec
- Future Enhancements (lines 410–420) — aspirational
- Tool Integration (lines 319–335) — generic

**Key cross-references:**
- `docs/DATABASE_SETUP.md#troubleshooting` — referenced in failure report
- Prisma Studio URL — referenced in success report

## Cross-Cutting Patterns

These patterns appear in all three files and receive the same treatment:

| Pattern | Treatment |
|---------|-----------|
| JSON todo blocks | Cut — process steps describe workflow |
| "AI Implementation Prompt" | Cut — restates the spec |
| Future Enhancements | Cut — aspirational, doesn't help execute |
| Tool Integration sections | Cut — generic tool lists |
| Verbose bash examples | Replace with principles (what/when, not how) |
| Exact output format templates | Replace with reporting principles (what to include) |

## Validation Approach

Same 5-task validation as prior specs:
1. Line count audit (per-file ranges + total)
2. Section-by-section litmus test
3. Cross-reference check
4. Capability comparison (before/after tables)
5. Voice and density comparison against benchmarks

Benchmarks: `commands/assess-spec.md` (203 lines), `commands/edit-spec.md` (118 lines)

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Cutting genuinely useful bash pattern | Low | Litmus test forces case-by-case evaluation |
| Breaking prisma-migration → test-database cross-ref | Low | Explicit cross-reference check in validation |
| Losing subtle detection heuristic | Medium | Capability comparison table catches this |
| Inconsistent voice with workflow commands | Low | Voice comparison against established benchmarks |

The main risk unique to this spec: infrastructure commands have bash patterns that *look* like boilerplate but actually encode non-obvious behavior (e.g., specific `find` flags, `sed` escaping). The litmus test handles this — if a bash line teaches something the AI wouldn't know, it stays.

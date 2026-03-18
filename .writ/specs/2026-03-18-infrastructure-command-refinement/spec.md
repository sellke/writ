# Infrastructure Command Refinement

> **Status:** Not Started
> **Date:** 2026-03-18
> **Files:** commands/migrate.md, commands/prisma-migration.md, commands/test-database.md

## Contract

**Deliverable:** Refine 3 infrastructure Writ commands (migrate, prisma-migration, test-database) from mixed B-/B to all-A by applying the same litmus test used in core, secondary, utility, and remaining refinement specs: every line must teach the AI something non-obvious, set a quality bar the AI wouldn't reach alone, or prevent a specific mistake. Templates become principles. ~59% line reduction, zero capability lost.

**Must Include:** Zero capability lost — every diagnostic heuristic, safety classification, and branching decision preserved.

**Hardest Constraint:** These are infrastructure commands where genuinely useful bash patterns are intermixed with redundant ones. The line between "teaches the AI something about Docker/Prisma behavior" and "restates CLI docs" is finer than in workflow commands.

## The Litmus Test

For every line in every file: (1) teaches something non-obvious, (2) sets a quality bar the AI wouldn't reach alone, (3) prevents a specific mistake — or it gets cut.

## Per-File Analysis

### migrate.md (371 → ~160 lines)

**What to cut:**
- **Phase 2 bash scripts** (~120 lines): `mv`, `sed`, `find`, `cp` — the AI knows file operations. Replace with principles about what to rename, what to verify, and what order matters.
- **One-liner migration script** (~15 lines): Restates Phase 2 in condensed form. Redundant.
- **Verbose FAQ** (~40 lines): Most answers restate behavior already described in the spec. Keep only FAQs that prevent real confusion (e.g., "Will my in-progress work be affected?").
- **Step 2.4 install commands** (~30 lines): `cp` commands for both platforms. The AI knows how to copy files. Replace with the *what* (which files from where to where) not the *how*.

**What to keep (crown jewels):**
- **What Changes / What Does NOT Change tables** — These are the contract. They prevent the most dangerous mistake: accidentally modifying spec content during migration.
- **Modes table** — Invocation variants with `--dry-run`, `--yes`, `--platform` flags.
- **Scan & Validate logic** — Detection heuristics for Code Captain artifacts, platform detection, inventory counting.
- **Integrity verification** — Count-before vs count-after, story status spot-check. This is genuinely non-obvious — most migration scripts skip verification.
- **Rollback instructions** — 3-line rollback is essential safety.
- **"What's New" section** — Helps users understand upgrade value. Keep but compress.

### prisma-migration.md (667 → ~260 lines)

**What to cut:**
- **Dialog box mockups** (~100 lines): Verbose `⚠️` prompt examples with exact text. The AI can write appropriate warning prompts. Replace with principles about *when* to warn and *what information* to include.
- **JSON todo block** (~20 lines): Restates what the process already describes.
- **Future Enhancements** (~15 lines): Aspirational — doesn't help execute the command.
- **Integration Notes** (~10 lines): Generic ("uses standard tools").
- **Best Practices naming conventions** (~25 lines): Good advice but the AI already knows `add_event_location` > `update_user`.
- **Verbose bash** (~60 lines): `prisma migrate dev --name X` examples with full output. The AI knows Prisma CLI. Keep the *decision logic* (when to run what), not the *syntax*.
- **Local validation section** (~20 lines): Starting a dev server and curling endpoints — obvious steps that don't need scripting.

**What to keep (crown jewels):**
- **Setup detection heuristics** — Single vs dev/prod, `db push` vs `migrate`, migration directory existence. This is the command's core intelligence.
- **Safety check logic** — 4-check framework (uncommitted changes, migration state, client sync, git status). The AI wouldn't compose this exact safety matrix unprompted.
- **Dev/prod separation offer** — The branching decision and guidance are genuinely valuable for developers on shared databases.
- **Deployment option branching** — Deploy now / later / checklist. The three-way branch with risk-level awareness.
- **Error scenarios** — Schema drift, deployment failure, uncommitted changes. Keep as principles (what to detect, what to recommend) not scripts.

### test-database.md (422 → ~180 lines)

**What to cut:**
- **AI Implementation Prompt** (~40 lines): Restates the entire process verbatim. Classic redundancy.
- **JSON todo block** (~20 lines): Same as above.
- **Future Enhancements** (~15 lines): Aspirational.
- **Verbose status report templates** (~60 lines): Both success and failure reports with exact emoji formatting. The AI can format status reports. Replace with principles about what to include.
- **Bash pseudocode** (~40 lines): `if container_stopped; then ... fi` — not real bash, and the logic is obvious from the step descriptions.
- **Tool Integration** (~15 lines): Generic ("uses todo_write and run_terminal_cmd").

**What to keep (crown jewels):**
- **Multi-layer testing approach** — Docker → Prisma → Application. This three-layer model is the command's organizing spine.
- **Safe vs destructive fix classification** — This is genuinely non-obvious. Auto-starting containers is safe; resetting databases is destructive. The classification boundary prevents data loss.
- **Detection targets** — What to scan for at each layer (docker-compose, schema.prisma, .env, package scripts, migrations).
- **Destructive fix request patterns** — When to ask permission, what information to show, how to phrase the risk.
- **Actionable recovery guidance** — Specific error → specific fix mapping. This is what makes the command useful vs. a generic "check your database."
- **Performance validation** — Basic checks that the AI wouldn't think to add unprompted.

## Cross-File Patterns to Address

All three files share these cut-worthy patterns:
1. **JSON todo blocks** — Process steps already describe the workflow; duplicating as JSON adds nothing.
2. **"AI Implementation Prompt" or equivalent** — Restates the spec. Always redundant.
3. **Future Enhancements** — Aspirational content that doesn't help execute.
4. **Tool Integration sections** — Generic tool lists that any Writ command uses.
5. **Verbose bash/output examples** — Replace with principles about *what* to do and *when*, not *how* to type it.

## Success Criteria

- All sections pass the litmus test
- ~600 total lines (from ~1,460) — roughly 59% reduction
- No cross-reference breakage (prisma-migration → test-database, test-database → docs)
- Zero functional capability lost
- Consistent voice and density with A-grade benchmarks (assess-spec.md at 203 lines, edit-spec.md at 118 lines)

## Scope Boundaries

**Included:**
- commands/migrate.md
- commands/prisma-migration.md
- commands/test-database.md
- Same litmus test, validation process, and quality bar as prior refinement specs

**Excluded:**
- Commands already refined in other specs
- No restructuring of what these commands do (behavior preserved)
- No changes to agents or other Writ files

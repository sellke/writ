# Phase 4 Production-Grade Substrate (Lite)

> Source: .writ/specs/2026-04-24-phase4-production-grade-substrate/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Five dual-use substrate features — knowledge ledger, SKILL.md generator, preamble enforcement, eval Tier 1, spec owner field.

**Implementation Approach:**
- Knowledge ledger: `.writ/knowledge/{decisions,conventions,glossary,lessons}/` + frontmatter (category, tags, created, related_artifacts)
- Manifest-driven SKILL.md: `.writ/manifest.yaml` → `scripts/gen-skill.sh` → `SKILL.md`; `--check` in CI
- Preamble: `commands/_preamble.md` referenced by every command (static ref, not runtime injection)
- Eval Tier 1: `scripts/eval.sh` runs 8 checks (required-sections, anti-sycophancy, prime-directive-sync, broken-refs, length, manifest, preamble, owner)
- Owner field: `git config user.name` default; new specs only

**Files in Scope:**
- New: `.writ/knowledge/**`, `commands/{knowledge,_preamble}.md`, `.writ/manifest.yaml`, `scripts/{gen-skill,eval}.sh`
- Modified: `commands/{create-spec,verify-spec,status,implement-story,*}.md`, `agents/*.md`, `SKILL.md`, `adapters/{cursor,claude-code,openclaw}.md`
- See `sub-specs/technical-spec.md` for the full file × story matrix

**Error Handling:**
- `/knowledge` outside `.writ/` → error + suggest `/initialize`
- Knowledge-loading hook finds nothing → silent no-op
- Malformed manifest → `gen-skill.sh` fails with YAML error + line
- `eval.sh` violations → grouped markdown report; non-zero exit
- Missing `owner:` on legacy spec → REPORT only, never WARN/FAIL

**Integration Points:**
- `/implement-story` Step 2 loads knowledge context per story
- CI runs `gen-skill.sh --check` and `eval.sh` on every PR
- Preamble static-referenced by every command (eval enforces)

---

## For Review Agents

**Acceptance Criteria:**
1. `.writ/knowledge/` has ≥5 backfilled entries across ≥2 categories at ship
2. `bash scripts/gen-skill.sh --check` exits 0 against committed `SKILL.md`
3. `bash scripts/eval.sh` exits 0 against full post-Story-1–4 surface
4. New specs include `owner:` from `git config user.name`; legacy specs reported as "legacy" without warning
5. All three adapter docs reference preamble convention and knowledge-loading hook

**Business Rules:**
- Plain-text + git only — no databases, no external services as source of truth (ADR-005)
- Dual-use test (ADR-007): every story benefits solo AND prepares team-readiness
- No team-specific features (`/review-spec`, multi-dev drift) in this spec
- Knowledge boundaries: ADRs = blast radius; research = investigations; knowledge = small accumulating cross-cutting; specs = feature contracts
- SKILL.md is generated post-ship; manual edits prohibited (header comment declares)
- Preamble references mandatory; eval enforces on every PR
- Anti-sycophancy enforces what Prime Directive inlined; `system-instructions.md` and `cursor/writ.mdc` Prime Directive sections must stay byte-identical
- Owner = `git config user.name`; no central directory; no legacy migration

**Experience Design:**
- Entry: existing commands; substrate invisible until value moment
- Happy path: agent loads `.writ/knowledge/` unprompted; CI catches drift; preamble change propagates
- Moment of truth: SKILL.md drift gate fires on a real PR; new contributor reads `.writ/knowledge/` and orients in <30 min
- Feedback: terse confirmations ( `/knowledge`); structured drift diff (gen-skill); grouped eval report
- Error: clear, file:line-anchored, with one-line remediation hint

**Drift Analysis Anchors:**
- Story scope creep beyond dual-use test → flag medium, scope-cut don't push through
- Manifest schema needs change mid-flight → small drift, amend technical-spec
- Pre-existing eval violations exceed triage budget → medium drift, grandfather with comment + issue

---

## For Testing Agents

**Success Criteria:**
1. ≥10 knowledge entries across ≥2 categories within 30 days post-ship
2. `gen-skill.sh --check` clean in CI for 60 days post-ship without manual SKILL.md edit
3. Eval Tier 1 catches ≥1 regression before release within first 60 days
4. `owner:` field on 100% of post-ship specs; legacy specs reported without blocking
5. Agent loads relevant `.writ/knowledge/` entry on a follow-up task without prompt-side mention
6. Zero external dependencies introduced

**Shadow Paths to Verify:**
- **Happy path:** `/knowledge "X"` → conformant entry; agent later loads it unprompted
- **Nil input:** `/knowledge` outside `.writ/` project → error + `/initialize` suggestion
- **Empty input:** knowledge-loading hook with no matches → silent no-op, task proceeds
- **Upstream error:** malformed `.writ/manifest.yaml` → `gen-skill.sh` exits 1 with YAML error + line; `eval.sh` reports manifest check failure

**Edge Cases:**
- Spec created on ship-date boundary → owner check uses `git log --diff-filter=A` for accurate first-commit date
- Multi-machine `git config user.name` differs → expected (no central directory)
- Pre-existing command file has 2147 lines (over length budget) → eval reports; either fix or `eval-exempt` comment
- `yq` missing on contributor machine → `gen-skill.sh` falls back to pure-bash YAML reader; reports mode

**Coverage Requirements:**
- Verification = `bash` exit codes + manual smoke tests under each adapter (no test framework — markdown/bash project)
- Critical paths (gen-skill, eval, /knowledge schema validation): manual sign-off in story DoD
- Self-dogfood validation: each story's PR demonstrates the feature in its own diff

**Test Strategy:**
- Story 1: ship a follow-up feature; verify agent loaded backfilled entry without prompting
- Story 3: deliberate manifest edit → verify `--check` fires
- Story 5: deliberate phrase violation in test branch → verify CI fails; revert

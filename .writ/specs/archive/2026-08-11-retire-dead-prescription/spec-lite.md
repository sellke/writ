# Retire Dead Prescription (Lite)

> Source: .writ/specs/2026-08-11-retire-dead-prescription/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Correct the stale and false claims in Writ's root contract and metadata so the component contract (ADR-020) is built on a truthful foundation. Docs + metadata only — no new contract fields.

**Implementation Approach:**
- Replace `system-instructions.md` line 277's false *"no frontmatter … (verified 0/31 files)"* claim with the measured truth (32/32 command files carry `---` frontmatter with `name` + `description`); advisory `model_tier` moves from prose note to frontmatter.
- Delete the `model_tier` negative-ordinal reservation now (maintainer decision, ahead of its 2026-10-16 trigger): schema branch, clamp row, reserve-only paragraph, trigger blockquote, and `lint-skill.sh`'s `-[0-9]+` regex. Keep `orchestration` + `capability`.
- Replace `required_skills:` "Status: reserve-only" + the **fired 2026-08-03** trigger with an adoption statement naming ADR-021 progressive disclosure as first consumer.
- `.writ/manifest.yaml`: `version: 0.13.1` → `0.28.0` (matches `VERSION`); verify 44 data `file:` entries = 31 commands + 7 agents + 6 skills.
- `.writ/product/decisions.md`: deprecation header superseding it to `.writ/decision-records/`; neutralize its "Override Priority: Highest" claim.
- **Scope addition, 2026-08-11 (Story 6, depends on Story 2):** carry the same frontmatter correction into `.writ/docs/model-tiers.md` (carrier row 45; `/new-command` emission 95; lint description 97) and **remove** — not retarget — `lint_model_tier()`'s prose-note `elif` at `scripts/lint-skill.sh:279-280`. Its first branch (line 277) is unanchored over the raw file and already captures command frontmatter. Locked Contract block unchanged; see spec.md → Detailed Requirements (f).

**Files in Scope** (owning story in brackets — one writer per file):
- `system-instructions.md` — lines ~225–300 (Skills + Model Tiers sections) [1, 2, 3].
- `cursor/writ.mdc` — **full byte-identical mirror** of `system-instructions.md` lines 1–300 (+10-line dogfooding appendix). Every edit above must be mirrored [1, 2, 3].
- `.writ/docs/model-tiers.md` — 75, 82, 86, 103 [2]; 45, 95, 97 [6]. Line 97 is shared: [2] narrows the allow-list, [6] drops "or a command's prose note".
- `.writ/docs/skills.md` (136, 138) [3].
- `commands/new-command.md` (145–151, 171 — prose-note template + checklist item) [1] — **double-claimed with sibling spec `2026-08-11-component-contract` Story 1, which wants the opposite outcome. Needs a maintainer ruling; see user-stories/README.md → "Open conflict".**
- `adapters/cursor.md` (218), `adapters/claude-code.md` (396), `adapters/openclaw.md` (278) — "reserve-only" sentences [3].
- `scripts/lint-skill.sh` — ordinal half of 26–27, 253–265, 285–286 [2]; prose-note half of 27, 254, 260–262, and the `elif` at 279–280 [6].
- `.writ/manifest.yaml` (line 4 version [4], line 227 schema comment [2]).
- `.writ/product/decisions.md` (lines 1–5) [5].

**Never edited (historical records, Business Rules 3 + 8):** `.writ/decision-records/adr-016-model-tier-delegation.md:76` and `CHANGELOG.md:143` carry the same "no frontmatter mechanism (verified 0/31)" wording and were true when written.

**Error Handling:**
- `prime-directive-sync` diffs **only** the `## Prime Directive` section — it will NOT catch Skills/Model-Tiers mirror drift. Mirror parity is a manual per-story obligation.
- No `eval-exempt:` markers may be added to make a change pass (Business Rule 4).
- Deprecation removes prescription, never history: ADRs, `CHANGELOG.md`, `.writ/specs/archive/`, `.writ/research/` stay untouched.

**Integration Points:** ADR-020 (cites the false claim as its frontmatter justification), ADR-021 (`required_skills:` adoption rationale), ADR-016 (originating ordinal reservation — recorded forward, not retrofitted), `scripts/eval.sh` `check_manifest` / `check_prime_directive_sync`, `scripts/gen-skill.sh --check`.

---

## For Review Agents

**Acceptance Criteria:**
1. Zero occurrences of "verified 0/31 files", "no frontmatter mechanism", "Status: reserve-only", the 2026-08-03 trigger, or the 2026-10-16 trigger remain on the active surface (`system-instructions.md`, `cursor/writ.mdc`, `commands/`, `adapters/`, `scripts/`, `.writ/docs/`, `.writ/manifest.yaml`, `.writ/product/`).
2. `bash scripts/eval.sh` reports `Findings: 0` after **every** story, not only the last.
3. `system-instructions.md` and `cursor/writ.mdc` remain line-for-line identical across every edited passage.

**Business Rules:**
- Replacement claims must be measured, not asserted (Rule 1).
- `cursor/writ.mdc` is a full mirror; the eval gate only checks the Prime Directive section (Rule 2).
- Deprecation touches the active surface only — history is preserved verbatim (Rule 3).
- `Findings: 0` per story; no self-serving `eval-exempt:` markers (Rule 4).
- No new contract fields — `problem`/`outcome`/`exit_criteria` and real `required_skills:` declarations are separate Phase 10 specs (Rule 5).
- Ordinal deprecation is a decision, not a discovery; reopening it requires producing a real consumer (Rule 6).
- `required_skills:` reserve-only status and its fired trigger are replaced *together* by an adoption statement (Rule 7).
- ADR-016:76 and CHANGELOG.md:143 are never "corrected"; one owning story per file; sibling-spec files are never edited here (Rule 8).

**Known contract-vs-repo discrepancies (documented, not amendments):**
- Contract's `.writt/product/decisions.md` is a typo for `.writ/product/decisions.md`; no `.writt/` exists.
- Contract's "45 `file:` entries" is a raw grep count; 44 are data entries — the 45th is inside a YAML schema comment (`.writ/manifest.yaml` line 225). Roadmap line 343 says 44.

---

## For Testing Agents

**Success Criteria:**
1. `bash scripts/eval.sh` → `Findings: 0` (baseline confirmed green 2026-08-11 before any edit).
2. `bash scripts/gen-skill.sh --check` → exit 0.
3. `grep -rn` for each retired literal across the active surface returns zero hits; the same grep across `.writ/decision-records/`, `.writ/specs/archive/`, `.writ/research/`, and `CHANGELOG.md` returns its original hits unchanged.
4. `.writ/manifest.yaml` `metadata.version` matches `VERSION` exactly.
5. Frontmatter count is reproducible: `for f in commands/*.md; do head -1 "$f"; done | grep -c '^---$'` → 32.

**Shadow Paths to Verify:**
- **Happy path:** every literal removed, both mirrors identical, suite green.
- **Nil input:** a story with no code change (docs-only) still runs the full suite before closing.
- **Partial edit:** `system-instructions.md` edited but `cursor/writ.mdc` not — the eval suite stays green (Prime Directive untouched), so only the manual mirror diff catches it. This is the spec's likeliest silent failure.
- **Upstream error:** `lint-skill.sh` regex narrowed but a fixture still declares an ordinal → lint fails. `scripts/eval-skill-lifecycle.py` has no `model_tier` fixture today; verify, do not assume.

**Edge Cases:**
- `commands/new-command.md` is the only file carrying the locked prose string (2 occurrences) — no shipped command is orphaned by retiring the carrier.
- `SKILL.md` does not render `metadata.version`, so the version bump should not stale the generated catalog — confirm via `--check`.
- `commands/plan-product.md:345` / `commands/create-adr.md:170` promise other projects' `decisions.md` files are never modified — that promise must survive unchanged.

**Coverage Requirements:** No new executable code. `scripts/lint-skill.sh`'s narrowed `model_tier` grammar must be exercised for `orchestration`, `capability`, and a now-rejected `-1` before the story closes.

**Test Strategy:** Literal-grep assertions per story (active surface = 0 hits, historical surface = unchanged); full `bash scripts/eval.sh` run per story; `gen-skill.sh --check`; manual line-for-line `system-instructions.md` ↔ `cursor/writ.mdc` diff on every edited passage.

# Story 6: `required_skills:` Resolution Check

> **Status:** Complete
> **Priority:** Medium
> **Dependencies:** Story 2, Story 3

## User Story

**As a** Writ maintainer about to make `required_skills:` progressive disclosure's first real consumer
**I want to** `eval-leanness.py` to assert every declared skill name resolves to a real `skills/<name>/SKILL.md` — warning, never failing
**So that** a renamed or typo'd skill surfaces on the next eval run instead of at load time in someone else's session, without contradicting the graceful-degradation contract in `system-instructions.md`

## Acceptance Criteria

- [x] Given a fixture command declaring `required_skills: [tdd-cycle]` and a real `skills/tdd-cycle/SKILL.md`, when the check runs, then it emits zero findings.
- [x] Given a fixture command declaring `required_skills: [no-such-skill]`, when the check runs, then it emits exactly one finding whose `subject` names both the declaring file and the unresolved name (e.g. `commands/example.md → required_skills: no-such-skill`), and whose `fix` names the expected path `skills/no-such-skill/SKILL.md`.
- [x] Given a fixture command declaring the same unknown skill twice, when the check runs, then it emits exactly one finding for that `(file, name)` pair — duplicates are silently deduplicated per `system-instructions.md`'s schema.
- [x] Given a fixture agent declaring `required_skills:` in its config block (either carrier), when the check runs, then it is checked identically to a command — the convention covers commands *and* agents.
- [x] Given `CONTRACT_CHECK_SEVERITY` is set to `"structural"`, when the check runs against a fixture with an unresolved name, then the finding is **still** in `warnings` and `structural` does not contain it — the pinned non-blocking override survives the flip.
- [x] Given the real repo after this story, when `eval-leanness.py` runs, then this check contributes **zero** findings and `metrics.required_skills_declarations` reports `0`, so a vacuous pass is distinguishable from a verified pass.

> **Verified 2026-08-11 (implementation).** Still 0 declarations across the whole product surface — `required_skills:` appears only as prose in `commands/new-skill.md` (3 mentions), the adapters and `system-instructions.md`. `metrics.required_skills_declarations: 0`. Every test of this check is therefore fixture-only, and the real-repo assertion is genuinely weak evidence: it proves the check does not crash and counts nothing, not that resolution works. The first real exercise arrives with the progressive-disclosure specs.
- [x] Given `skills/` is absent entirely from a fixture root, when the check runs against a fixture declaring one skill, then it emits a warning for the unresolved name and exits 0 — never an exception.

## Implementation Tasks

- [x] 6.1 Write tests in `scripts/tests/test_eval_leanness_contract.py`: resolving name, unknown name, duplicate entries, agent-carrier declaration, `required_skills: []`, absent `skills/` directory, and the post-flip pinned-warning assertion
- [x] 6.2 Add `check_required_skills(root)` — scans `commands/*.md` frontmatter and `agents/*.md` config blocks via Story 3's readers, dedupes per file, resolves each name against `skills/<name>/SKILL.md`
- [x] 6.3 Wire it into `main()` through `emit_contract_findings(..., severity="warnings")`, with an inline comment citing `system-instructions.md`'s graceful-degradation clause as the reason for the pin
- [x] 6.4 Add `metrics["required_skills_declarations"]` — the count of declared `(file, skill)` pairs — so the currently-vacuous pass reads as vacuous (Business Rule 8)
- [x] 6.5 Verify acceptance criteria against the real repo: zero findings, `required_skills_declarations: 0`, exit 0; and against a fixture with the constant flipped, that findings stay in `warnings`
- [x] 6.6 Verify all tests pass — new pytest cases, `test_eval_leanness.sh`, full `scripts/tests/*.py` suite, `bash scripts/eval.sh --check=leanness`

## Notes

**Technical considerations:**

- **This check is vacuous today, and that must be visible.** Verified across the whole product surface: `required_skills:` appears only as prose in `commands/new-skill.md`, the three adapters, `system-instructions.md`, and `skills/gbrain-interop/SKILL.md`. `system-instructions.md` labels it *"Status: reserve-only … not adopted by any existing agent or command."* Zero declarations means zero findings — correct behavior, but "0 findings" and "0 things checked" must not look identical in the output. The declaration count in `metrics` is the entire guard (Business Rule 8).
- **The pin is a contract obligation, not a preference.** `system-instructions.md`: *"Unknown skill names produce a **warning** at consumer load time, not a hard failure (graceful degradation: a pilot extraction may rename a skill mid-flight; consumers shouldn't break catastrophically)."* Hard-failing `eval.sh` on an unresolved name would contradict the root behavioral contract during exactly the phase (progressive disclosure) that renames skills most. The `severity="warnings"` override carries that citation as a code comment so a future reader cannot mistake it for an oversight.
- **Existing skills, verified 2026-08-11:** `code-explanation`, `conventional-commits`, `error-rescue-mapping`, `gbrain-interop`, `safe-refactor-loop`, `tdd-cycle`. Resolution is a filesystem check against `skills/<name>/SKILL.md`, matching the `skills` surface glob already in `SURFACE_REGISTRY` (`*/SKILL.md`).
- **Do not validate against `.writ/manifest.yaml`.** `system-instructions.md` says values match `name:` entries there, but the manifest is separately known-stale (roadmap Phase 10: *"fix `.writ/manifest.yaml` (`version: 0.13.1` → `0.28.0`, 44 entries → 31 commands)"*). Resolving against the filesystem is the honest check; resolving against a stale manifest would produce findings about the manifest, not about the declaration.

**Risks / challenges:**

- **A pinned-warning check is the easiest one to forget when the flip lands.** Story 7's test suite must include the post-flip assertion that these findings stay non-blocking; without it, the `governor-enforcement` spec could flip the constant and silently break `system-instructions.md`'s contract with no test failing.
- Zero real declarations means every test here is fixture-only. The real-repo assertion (`0 findings`, `required_skills_declarations: 0`) is genuinely weak evidence, and the story should say so rather than treat a vacuous pass as validation. The first real declaration lands in the progressive-disclosure specs; that is when this check gets exercised for real.

**Integration points:**

- Consumes Story 3's `read_frontmatter()` / `read_agent_config()` and `emit_contract_findings()` — with the one severity override in this spec.
- Independent of Stories 4 and 5 — parallel after Story 3.
- Story 7 asserts the pin survives the flip; that assertion lives in Story 7's suite but tests this story's wiring.
- ADR-021 item 3 makes `required_skills:` progressive disclosure's first real consumer, resolving its 8-days-overdue (2026-08-03) review trigger by adoption. This check is what makes that adoption verifiable rather than assumed.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 6 (`required_skills:` warns, never hard-fails, even post-flip — the primary rule this story implements); Rule 8 (a check with nothing to assert reports its declaration count so a vacuous pass is visible); Rule 2 (findings name the declaring file *and* the unresolved skill name)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Check 4 — `required_skills:` resolution: per-pair findings, dedup, zero declarations today, the `severity="warnings"` pin and its citation] — from spec.md → ## Detailed Requirements → ### Check 4
- **Error map rows:** [`required_skills:` resolution → warning per unresolved `(file, name)` pair, deduped, never blocking even post-flip; `skills/` absent → every name unresolved, warnings, exit 0] — from sub-specs/technical-spec.md → ## Error & Rescue Map, ## Shadow Paths
- **Contract:** [Technical Concerns: "A vacuous check can look like a passing check … without it, '`required_skills:` resolution: 0 findings' would read as verified when it means unexercised."] — from spec.md → ## Technical Concerns

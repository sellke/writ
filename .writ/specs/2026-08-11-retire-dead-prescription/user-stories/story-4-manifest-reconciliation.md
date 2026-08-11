# Story 4: Reconcile `.writ/manifest.yaml`

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ maintainer relying on `.writ/manifest.yaml` as the catalog `gen-skill.sh` renders and `eval.sh` validates against
**I want to** the manifest's declared version to match the shipped version and its file entries verified against disk
**So that** the file naming Writ's identity is not fifteen minor releases behind the `VERSION` it claims to describe

## Acceptance Criteria

- [ ] Given `.writ/manifest.yaml`, when `metadata.version` is read, then it equals the contents of the `VERSION` file exactly (`0.28.0`), replacing the stale `0.13.1`.
- [ ] Given the manifest's data `file:` entries, when counted per section, then there are 31 under `commands:`, 7 under `agents:`, and 6 under `skills:` — 44 total — and each path resolves to a file that exists on disk.
- [ ] Given the reverse direction, when every `commands/*.md` not matching `_*.md` and every root `agents/*.md` is checked, then each appears in the manifest — verified explicitly, not assumed from a passing gate.
- [ ] Given the discrepancy between the contract's "45 `file:` entries" and the 44 data entries, when the reconciliation is recorded, then it states that the 45th `grep` hit is `file: skills/<name>/SKILL.md` inside the skills schema comment block (`.writ/manifest.yaml:225`) and is not a data entry.
- [ ] Given `bash scripts/gen-skill.sh --check`, when run after the version bump, then it exits 0 — the generated `SKILL.md` is not made stale by the change.
- [ ] Given the full validation suite, when `bash scripts/eval.sh` runs, then it reports `Findings: 0`, and `bash scripts/eval.sh --check=manifest` reports PASS.

## Implementation Tasks

- [ ] 4.1 Read `VERSION` and confirm its exact contents before editing (expected `0.28.0`). Do not hardcode the version from the contract text without checking the file — Business Rule 1.
- [ ] 4.2 Update `.writ/manifest.yaml:4` `version: 0.13.1` → the value read from `VERSION`.
- [ ] 4.3 Count the data `file:` entries per section and cross-check both directions against disk: every manifest path exists, and every non-`_`-prefixed `commands/*.md` plus every root `agents/*.md` is listed. Record the counts (expected 31 / 7 / 6) as evidence in "What Was Built".
- [ ] 4.4 Record the 45-vs-44 discrepancy explicitly: the raw `grep -c "file:"` returns 45 because the skills schema comment block at line ~225 documents the field shape. `.writ/product/roadmap.md:343` states 44. No manifest content changes as a result — this task produces the finding, not an edit.
- [ ] 4.5 Run `bash scripts/gen-skill.sh --check` and confirm exit 0. If it fails, regenerate `SKILL.md` rather than reverting the version bump — the bump is the correct value.
- [ ] 4.6 Verify: `bash scripts/eval.sh --check=manifest` PASS and full `bash scripts/eval.sh` → `Findings: 0`.

## Notes

**Technical considerations:**

- `check_manifest()` (`scripts/eval.sh:454-521`) already enforces both parity directions plus a `gen-skill.sh --dry-run` parse, and it **passes today**. The reconciliation deliverable is therefore *verification recorded as evidence* plus the version bump — not a hunt for drift the gate would already have caught. Do not manufacture changes to make the story feel substantial.
- `commands/_preamble.md` is deliberately absent from the manifest. `check_manifest` skips `_*.md` files by prefix (`scripts/eval.sh:490`), which is why the manifest lists 31 commands against 32 files in `commands/`.
- `gen-skill.sh` reads `metadata.version` (line 127 via `yq`, line 314 in the pure-bash fallback parser) and hard-fails if it is empty (line 424). Measured: the generated `SKILL.md` does not render the version string, so the bump should not stale the catalog. Confirm with `--check` rather than assuming.
- The stale `0.13.1` also appears in `.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md` (lines 37, 175) as a point-in-time comparison heading. Historical — out of scope (Business Rule 3).
- This story is fully independent of Stories 1–3 and of Story 5. Story 2 makes one edit to `.writ/manifest.yaml` line 227 (a schema *comment*, not a data field); if both are in flight, land this story first and let Story 2 re-locate by literal.

**Risks / challenges:**

- The temptation to "reconcile" by rewriting entries that are already correct. Every manifest `purpose:` and `tags:` value is out of scope; this story changes exactly one line of data (`metadata.version`) and verifies the rest.
- `gen-skill.sh` has two parser paths — `yq` when available and a pure-bash fallback (the fallback is what ran during baseline measurement, reporting `Parser: pure-bash fallback`). Both read `metadata.version`. A malformed edit could pass one and fail the other; `--check` plus the full suite exercises what is installed.

**Integration points:**

- `check_manifest` is one of the three eval checks the locked contract names as guarding this spec's edit surface. Its PASS state is a named acceptance criterion here.
- Phase 10's "Make the governor bite" roadmap item lists `bash scripts/gen-skill.sh --check` passing among its success criteria. This story leaves it passing; it does not add the new structural checks that item owns.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/eval.sh` reports `Findings: 0`
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (measured, not asserted — read `VERSION`, count the entries), Rule 3 (active surface only — the research doc's `v0.13.1` heading stays), Rule 4 (`Findings: 0`, no exemptions), Rule 5 (no new contract fields)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [(c) `.writ/manifest.yaml` reconciliation] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [Section structure and measured entry counts; what `check_manifest` already enforces; the version bump's effect on `gen-skill.sh`] — from sub-specs/technical-spec.md → "(c) Manifest reconciliation — Story 4"
- **Contract:** [Must include (c): `version: 0.13.1` → `0.28.0`, and its 45 `file:` entries reconciled against the 31 real commands; see spec.md → Contract reading notes for why 44 are data entries] — from spec.md → ## Contract (Locked)

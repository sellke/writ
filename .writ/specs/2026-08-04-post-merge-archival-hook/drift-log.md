# Drift Log: Post-Merge Archival Hook

> Append-only. Never modify existing entries. DEV-ID numbering continues from the highest existing entry.

#### [DEV-001] `ArchiveOneResult` implemented as a plain dict with `spec` key, not a dataclass with `spec_name`
- **Story:** Story 2 (Single-Spec Archive Entry Point)
- **Severity:** Small
- **Spec said:** Technical spec's illustrative `@dataclass ArchiveOneResult` with a `spec_name` field.
- **Implementation did:** Plain dict with key `"spec"`, matching `scan()`/`sweep()`'s existing convention in the same file.
- **Resolution:** Auto-amended — the technical spec itself calls the dataclass shape "illustrative," so no `spec-lite.md` amendment is needed (spec-lite.md doesn't restate the dataclass). Noted here for traceability.
- **Spec-lite updated:** No (not applicable — spec-lite.md doesn't reference the dataclass shape).

#### [DEV-002] Sub-spec's `[UNPLANNED]` atomicity note not updated to record the resolution
- **Story:** Story 2 (Single-Spec Archive Entry Point)
- **Severity:** Small
- **Spec said:** "Resolution required before Story 2 implementation starts... Record the decision in this sub-spec once made" (`sub-specs/technical-spec.md` Error & Rescue Map).
- **Implementation did:** Made a sound decision (accept the rare unlogged-move risk, surfaced via a new `archived_unlogged` status) and documented it thoroughly in `scripts/archive-sweep.py`'s module docstring — but `sub-specs/technical-spec.md` itself still read as unresolved.
- **Resolution:** Auto-amended — updated `sub-specs/technical-spec.md`'s Error & Rescue Map row to strike `[UNPLANNED]` and cite the `archived_unlogged` resolution (see accompanying edit).
- **Spec-lite updated:** No (technical-spec.md is a sub-spec, not spec-lite.md; edited directly per the story's own explicit instruction to record the decision there).

#### [DEV-003] SHA-extraction mechanism swapped from `gh`'s built-in `--jq` to an external `jq` pipe
- **Story:** Story 3 (Wire the Hook into /release Step 1.3c)
- **Severity:** Small
- **Spec said:** Task 3.4b (architecture-check revision) — "extend the existing single `gh pr list` call's `--json` fields (additive only)."
- **Implementation did:** Additive in effect (existing `LAST_MERGED_SHA`/`HEAD_SHA` values unchanged when both `gh` and `jq` are present), but the *mechanism* changed: the prior line used `gh pr list --json mergeCommit --jq '...'` (gh's self-contained JSON engine); the new line drops `--jq` and pipes the raw multi-field JSON through the external `jq` binary instead, needed to extract four independent fields in one call.
- **Resolution:** Auto-amended — added a clarifying note directly below Step 1.3c's bash block in `commands/release.md` documenting the external-`jq` dependency and its fail-safe degradation (falls through to "run full suite" if `jq` is absent), consistent with Step 3.1's existing external-`jq`-with-fallback assumption elsewhere in the same file. No code change requested by the review agent.
- **Spec-lite updated:** No (mechanism-level detail, not a spec.md/spec-lite.md contract term).

#### [DEV-004] Story-4 tracking metadata (status header, task checkboxes, rollups) not updated to reflect completed work
- **Story:** Story 4 (Dogfood and Verify)
- **Severity:** Small
- **Spec said:** Story 4's own Definition of Done ("All tasks completed," etc.) and the established convention from Stories 1–3 of flipping status headers, checking task boxes, and updating `user-stories/README.md`'s rollup and `spec.md`'s status line on story close.
- **Implementation did:** Delivered the substantively-narrowed Task 4.0–4.7 scope correctly (confirmed independently by the review agent) but left `story-4-dogfood-and-verify.md`'s status header, all seven original (superseded) task checkboxes, and the Definition of Done unchecked; `user-stories/README.md` and `spec.md` still read pre-Story-4 progress counts.
- **Resolution:** Auto-amended by the orchestrator immediately following review PASS — flipped Story 4's status header to `Completed ✅`, replaced the stale 7-item task list with the actual delivered 8-item list (4.0–4.7) all checked, checked the Definition of Done items that are genuinely true today (AC5 explicitly excluded per its own honest "not yet confirmed" status), updated `user-stories/README.md`'s rollup to 4/4 stories complete, and updated `spec.md`'s status header to `Complete` — all 5 of the spec's own numbered Success Criteria are fixture-satisfied; the spec's Success Criteria list does not itself require the live merge event, which remains tracked as Story 4's own open follow-up (AC5) rather than a spec-blocking gap.
- **Spec-lite updated:** No — `spec-lite.md` carries no status header to flip (confirmed by direct read); its content otherwise remains accurate to the shipped contract.

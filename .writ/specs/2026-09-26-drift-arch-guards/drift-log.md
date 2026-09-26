# Drift Log

> Spec: .writ/specs/2026-09-26-drift-arch-guards/
> Created: 2026-09-26
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Boundary Crossings Script — Drift Report

> Run: 2026-09-26
> Overall Drift: Small

### Deviations

#### [DEV-001] Non-list map entries count as map_unreadable
- **Severity:** Small
- **Spec said:** The map is unverifiable when missing, unreadable, or not a JSON object.
- **Implementation did:** Also treats an `owned` / `readable` / `out_of_scope` value that is not a list of strings as `map_unreadable`; missing keys are empty lists.
- **Reason:** Business Rule 2 (route UP on doubt); a malformed map is an unreadable map.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Error Handling: "Map unreadable (including non-list entries) / helper missing → unverifiable, route: review-agent".

#### [DEV-002] Summary prints `surface none` without --surface
- **Severity:** Small
- **Spec said:** Only the `surface full-stack` summary form is shown.
- **Implementation did:** Prints `surface none` when `--surface` is omitted.
- **Reason:** Fills an unspecified detail; no routing effect.
- **Resolution:** Auto-amended
- **Spec amendment:** Summary line always carries `surface <class|none>`; recorded here, spec-lite carries no summary-line detail.

#### [DEV-003] Unverifiable output lists only map_unreadable
- **Severity:** Small
- **Spec said:** Reasons are crossings, then `full_stack_surface`.
- **Implementation did:** With an unreadable map, prints only `reason: map_unreadable`, even with `--surface full-stack`.
- **Reason:** The route is `review-agent` either way; the technical-spec table row names only `map_unreadable`.
- **Resolution:** Auto-amended
- **Spec amendment:** Unverifiable output carries the single reason `map_unreadable`; recorded here, spec-lite unchanged at this level of detail.

#### [DEV-004] Changed paths normalized with Path, not normalize_path
- **Severity:** Small
- **Spec said:** Reuse the existing path normalization.
- **Implementation did:** New `repo_relative` for changed files; `normalize_path` only for map entries. All three normalization rules hold.
- **Reason:** Changed paths come from git, not prose; `normalize_path`'s punctuation trimming would corrupt real file names.
- **Resolution:** Auto-amended
- **Spec amendment:** Changed paths use git-path normalization; map entries use `compute`'s normalization; recorded here.

#### [DEV-005] Duplicate changed paths reported once
- **Severity:** Small
- **Spec said:** One reason per crossing, in input order; exit 2 on empty `--changed`.
- **Implementation did:** A repeated path is reported once at first position; blank values dropped; all-blank exits 2.
- **Reason:** Preserves input order; all-blank is empty.
- **Resolution:** Auto-amended
- **Spec amendment:** Crossings are de-duplicated in first-seen order; recorded here.

---

## Story 4: Drift Roll-up at Spec End — Drift Report

> Run: 2026-09-26
> Overall Drift: Small

### Deviations

#### [DEV-006] Entries without a recognized severity are skipped
- **Severity:** Small
- **Spec said:** Count each DEV entry's `- **Severity:**` inside `## Story N:` sections; unrecognized severities unspecified.
- **Implementation did:** Entries with a missing or non-canonical severity, or outside a story section, are skipped silently; the roll-up still prints `pass`.
- **Reason:** Format validation belongs to `drift-format.py check`; Business Rule 8 keeps the roll-up report-only.
- **Resolution:** Auto-amended
- **Spec amendment:** The roll-up counts only canonical `Small`/`Medium`/`Large` entries inside story sections; recorded here.

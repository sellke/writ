# Drift Log

> Spec: .writ/specs/2026-10-22-prompting-guide/
> Created: 2026-10-22
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Write the Prompting Guide — Drift Report

> Run: 2026-10-22
> Overall Drift: Small

### Deviations

#### [DEV-001] Part definitions use a colon instead of the sketch's em-dash
- **Severity:** Small
- **Spec said:** technical-spec.md → File Layout sketches `- **Goal** — …`. The contract (Must Include 1) and spec-lite fix only the bold part names as the first words of three list items.
- **Implementation did:** `- **Goal**: what should be true afterwards, in your own terms.` and the same colon form for Done check and Proof.
- **Reason:** AC-1.5 and Business Rule 8 forbid any em-dash in the guide; the sketch's separator would have failed the criterion. The part names, bold, and list position are unchanged.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed. spec-lite.md already names the parts as `- **Goal**`, `- **Done check**`, `- **Proof**` with no separator; the em-dash exists only in the technical-spec sketch, which the pipeline does not amend.

#### [DEV-002] Opening paragraph states coverage instead of the sketch's metaphor
- **Severity:** Small
- **Spec said:** technical-spec.md → File Layout sketches "a request is a contract in miniature; Writ reads it the way a careful colleague would." Task 1.2 asks for "a short opening paragraph that says what the guide covers."
- **Implementation did:** The paragraph names the three sections and tells the reader to read the guide once before the first request.
- **Reason:** Task 1.2 is followed literally; the sketch sentence is literary framing under `skills/plain-prose/SKILL.md` step 2. No rule was lost.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed. spec-lite.md does not describe the opening paragraph.

#### [DEV-003] Roadmap Route line adds a clarifying clause
- **Severity:** Small
- **Spec said:** spec-lite.md and the sketch: `Route: `/implement-phase <N>``.
- **Implementation did:** `Route: `/implement-phase <N>`, where N is the phase number`.
- **Reason:** A reader of an installed project has no other definition of N. The line stays one line, names the contracted command, and `test_recipes` passes on the command substring.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed. spec-lite.md names `/implement-phase <N>`, which the line still carries.

---

## Story 2: Ship, Link, and Pin the Guide — Drift Report

> Run: 2026-10-22
> Overall Drift: Small

### Deviations

#### [DEV-004] Ship-set function sourced from a here-string instead of process substitution
- **Severity:** Small
- **Spec said:** spec.md → Implementation Approach sketches `bash -c 'source <(sed -n "/^is_shippable_writ_doc()/,/^}/p" scripts/install.sh); is_shippable_writ_doc prompting-guide.md'` and expects exit 0. The contract (Must Include 4), Business Rule 5, and Detailed Requirements → Story 2 require only that the test sources the function from each script in a bash subprocess and asserts it admits the filename.
- **Implementation did:** `test_ships` keeps the same `sed` expression, `bash -c` subprocess, call, and argument, but captures the extraction into `$fn` and sources it with `source /dev/stdin <<<"$fn"`; the script path and filename arrive as positional arguments. An empty extraction exits 64 and the test fails naming the script and the function.
- **Reason:** On macOS `/bin/bash` 3.2.57 the sketched `source <(sed …)` form defines nothing and exits 127 (verified by the orchestrator and the evaluator); the here-string form exits 0 on bash 3.2.57 and 5.3.20. A sketch detail changed; the contract's intent is preserved.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed in spec-lite.md, which does not name the sourcing form. spec.md's Implementation Approach sketch is not auto-modified by the pipeline; the here-string form is recorded here.

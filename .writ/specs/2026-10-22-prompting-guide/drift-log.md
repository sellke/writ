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

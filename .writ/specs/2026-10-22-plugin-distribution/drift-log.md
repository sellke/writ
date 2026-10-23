# Drift Log

> Spec: .writ/specs/2026-10-22-plugin-distribution/
> Created: 2026-10-23
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Verify Both Plugin Formats and Decide the Layout — Drift Report

> Run: 2026-10-23
> Overall Drift: Small

### Deviations

#### [DEV-001] Layout B built and installed although layout A passed validate and install
- **Severity:** Small
- **Spec said:** Task 1.3: "Build layout B (`plugins/writ/`) only if A fails validate or install."
- **Implementation did:** Built a layout B scratch plugin as well, validated it, installed it from a local path, and ran `/writ:stub`, `/writ:scratch-skill`, `/writ:root-skill`, and the `writ:writ-coder` spawn under it, then undid the install (V55, V61 in § Verification Record).
- **Reason:** The decision rule's third condition (the root `skills/` scan) needs a B observation to show that a `skills/` outside `plugins/writ/` stays unloaded; the run changed no product file and its undo is recorded.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** none needed beyond the Story 1 line in spec-lite.md (DEV-002).

#### [DEV-002] Carrier decided by the quote and persona probes, not the assertion probe
- **Severity:** Small
- **Spec said:** Story 1 Notes: ask the session to confirm an unchecked assertion; a carrier counts as observed only when its reply differs from the baseline.
- **Implementation did:** The assertion probe (P1) withheld confirmation in the baseline and under both carriers, so it did not discriminate (V70). The decision rests on P2 (quote the first Hard Constraints bullet and its heading) and P3 (name the persona), which differ from the baseline under both carriers (V67 to V69). Both carriers were observed; verified docs rows broke the tie for the forced output style.
- **Reason:** P1's reply is Claude's default behaviour with no tools, so it cannot show which instructions are present; P2 and P3 can.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents, the Story 1 line now records the outcome: layout B, carrier `output-styles/writ.md` (`force-for-plugin`, `keep-coding-instructions`), decided by the P2/P3 probes.

#### [DEV-003] Two token classes added to the four the spec named
- **Severity:** Small
- **Spec said:** spec.md Technical Concerns names `agent-path`, `skill-path`, `preamble-path`, `instructions-path` beside `script-root`; Task 1.6 says "Confirm or change the four token classes from the inventory".
- **Implementation did:** The inventory adds `script-path` (73 bare `scripts/<name>` references without an interpreter, plus one `../scripts/` link) and `command-ref` (`/<command>` to `/writ:<command>`, 806 matches), and states that every class rewrites Markdown bodies only.
- **Reason:** AC-2.2 requires every command cross-reference to read `/writ:<command>` and every script call to read `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`; many script calls carry no interpreter. The script-invocation count is 69, not the spec's 132 (recorded in the inventory).
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents, the Story 1 line lists six token classes.

#### [DEV-004] Cursor `commands/` and `agents/` directories are now documented
- **Severity:** Small
- **Spec said:** spec.md Rule 6 and spec-lite: Cursor agents and commands directories are undocumented, so they ship at the `install.sh` shape labelled `unverified (pending UAT)`.
- **Implementation did:** https://cursor.com/docs/reference/plugins.md (read 2026-10-23) documents `rules/`, `skills/`, `agents/`, `commands/` as default discovery directories (V48). Story 1 records the docs placement as verified; the live load stays `unverified 2026-10-23 (pending UAT)` (V76, V77).
- **Reason:** Upstream docs changed since 2026-10-22 (technical-spec.md → Shadow Paths, Upstream error: record the new URL and re-take the decision).
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → For Coding Agents, the Cursor line says the directories are docs-verified and the live load is pending UAT.

---

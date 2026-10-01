# Drift Log

> Spec: .writ/specs/2026-10-01-cross-family-review-panel/
> Created: 2026-10-01
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Panel Config, Vendor Table, Status, and Amendments — Drift Report

> Run: 2026-10-01
> Overall Drift: Small

### Deviations

#### [DEV-001] Config key read case-insensitively
- **Severity:** Small
- **Spec said:** Read the `- **Review Panel:**` line "the way `scripts/jev-judge.py` reads `- **Judgment Provider:**`" (that regex is case-sensitive on the key); only the value `none` is specified as case-insensitive.
- **Implementation did:** The key matches case-insensitively (`- **review panel:**` also counts); the first matching line still wins.
- **Reason:** `.writ/docs/config-format.md` → Rules states "Keys are case-insensitive on read", the file format's own contract. A human still writes the line either way, so consent is unchanged.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Error Handling" records the key-case rule.

#### [DEV-002] Unreadable config is a usage error
- **Severity:** Small
- **Spec said:** Missing line → `unverifiable no_config_line`; unreadable repo → exit 2.
- **Implementation did:** A missing `.writ/config.md` is `no_config_line`; an existing `config.md` that cannot be read or decoded, or a repo directory without read permission, exits 2.
- **Reason:** Reporting an unreadable consent file as "no line" would hide the error; exit 2 is the spec's usage path and still leaves Gate 3 unchanged (the Gate 3 paragraph acts only on `pass`).
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Error Handling" records the unreadable-config exit.

---

## Story 2: Tally, Matching Rule, and Tagged Reviewer Output — Drift Report

> Run: 2026-10-01
> Overall Drift: Small

### Deviations

#### [DEV-003] Location normalization reads the first backticked span
- **Severity:** Small
- **Spec said:** Normalize a Location by stripping backticks, leading `./`, trailing `:<line>[-<line>]`, and whitespace.
- **Implementation did:** Takes the first backticked span (else the first token), strips trailing `,`/`;`, then applies the stated stripping; placeholder Locations (`N/A`, `none`, `-`, `—`) count as no Location and are never keyed.
- **Reason:** The agents' own examples carry commentary after the path (`` `src/routes/auth.ts:45` — no uniqueness check ``); literal stripping would key the sentence and never match. Placeholders are Location-less entries (Business Rule 7), and keying them would let two vendors writing `N/A` block falsely.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Implementation Approach" records the normalization.

#### [DEV-004] Unmet AC keys carry severity Critical; session-vendor reviewers are not panel reviewers
- **Severity:** Small
- **Spec said:** `--json` carries per-key vendor lists and original text (no severity stated for `ac:` keys); fewer than one usable panel reviewer → `unverifiable`.
- **Implementation did:** `ac:` keys report severity `Critical` (both agents' Severity Definitions rate an unmet criterion Critical; Story 4 stores severities). A reviewer whose slug resolves to the session vendor merges into that vendor: it never counts toward "usable panel reviewer", and a key only that vendor raised is primary-only, never advisory.
- **Reason:** Keeps Business Rule 8's definitions exact when `tally` is called without `status` filtering first.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Implementation Approach" records both rules.

---

## Story 3: Gate 3 Wiring, `--panel`, and Eval Pins — Drift Report

> Run: 2026-10-01
> Overall Drift: Small

### Deviations

#### [DEV-005] Panel paragraph gated on the config line and on the spawned Gate 3 agent
- **Severity:** Small
- **Spec said:** The paragraph opens "When `review-panel.py status …` prints `pass` and `gate3_route` names `review-agent` or `--panel` is set"; the Nil-input shadow path says no config line → nothing printed, no new step.
- **Implementation did:** The paragraph opens "Only with a `- **Review Panel:**` line in `.writ/config.md`:" before the `status` call, and the trigger reads "Gate 3 spawns `review-agent` (risk route, `--full-pipeline`, or two-fail escalation) or `--panel` is set"; under `--review-only` a block "ends the run".
- **Reason:** Without the leading clause the `status` call itself is a new step on every project, contradicting AC-3.3's "no new step executes". `gate3_route` alone misses the Interaction Edge Cases rows (`--full-pipeline` always runs `review-agent`; after two-fail escalation the panel still runs); naming the spawned agent covers all three. The `--review-only` clause is AC-3.2's stated rule.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Implementation Approach" records the trigger wording.

#### [DEV-006] Lean twin placement and `--quick` conflict wording
- **Severity:** Small
- **Spec said:** Place the paragraph "directly after the `**Risk route:**` paragraph" in both command files; state the `--panel --quick` conflict by extending the mutual-exclusion sentence.
- **Implementation did:** `implement-story.lean.md` has neither a Risk route paragraph nor a mutual-exclusion sentence (earlier specs kept both out of the lean arm), so the paragraph takes the same slot (after the default-spawn line, before `**`--full-pipeline`:**`) and the lean `--panel` row itself states the usage error. The default file's duplicated Gate 3 verify-claim and review-loop prose was replaced with the lean twin's shorter wording to offset bytes (+1024 → +803); the pinned phrases stay.
- **Reason:** Adding the Risk route to the lean arm would widen this story past its scope; the slot and the rule are the same.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Implementation Approach" records the lean placement.

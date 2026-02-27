# Phase 1: Foundation — Validation Checklist

> Created: 2026-02-27
> Status: Structural Validation Complete, Dogfooding Pending

## Dogfood Scenarios

### Scenario 1: `/prototype` — Small Improvement
**Goal:** Validate the lightweight execution path end-to-end.
**Task:** Run `/prototype` on a small improvement to an existing Writ command (e.g., clarify a prompt, fix a typo, improve error handling).

| Check | Criteria | Result |
|-------|----------|--------|
| Quick contract presented | 2-3 AskQuestion prompts appear | Pending |
| Pre-filled mode works | `/prototype "description"` skips Q1 | Pending |
| Coding agent spawns | TDD approach, implements change | Pending |
| Lint/typecheck runs | Auto-detected, passes | Pending |
| Summary produced | Files modified, lint confirmation | Pending |
| Wall-clock time | < 5 minutes human time | Pending |

### Scenario 2: `/implement-story` with Spec Drift
**Goal:** Validate spec-healing detects real drift without false positives.
**Task:** Implement stories where implementation naturally diverges from spec (naming, approach variation, scope expansion).

| Check | Criteria | Result |
|-------|----------|--------|
| Small drift detected | Renamed function → auto-amend proposed | Pending |
| Medium drift detected | New dependency → flagged with ⚠️ | Pending |
| Large drift detected | Architecture deviation → pipeline pauses | Pending |
| Ambiguous → Medium | Unclear severity defaults to Medium | Pending |
| drift-log.md created | Correct format, append-only | Pending |
| Existing review preserved | All checklist items still evaluated | Pending |
| Detection rate | ≥3 of 5 story runs detect real drift | Pending |
| False positive rate | Zero false positives | Pending |

### Scenario 3: `/refresh-command` on Dogfood Transcripts
**Goal:** Validate the learning loop produces actionable improvements.
**Task:** Run `/refresh-command` on transcripts from Scenarios 1 and 2.

| Check | Criteria | Result |
|-------|----------|--------|
| Interactive selection | Command + transcript AskQuestion works | Pending |
| --last mode works | Auto-selects most recent transcript | Pending |
| Friction signals found | Real patterns identified from transcript | Pending |
| Amendments proposed | Concrete diff + rationale + confidence + scope | Pending |
| Local apply works | Amendment applied to .cursor/commands/ | Pending |
| Changelog written | Entry in .writ/refresh-log.md | Pending |
| Actionable threshold | ≥1 improvement per command analyzed | Pending |

### Scenario 4: Command Overlay Preservation
**Goal:** Validate local modifications persist across install/update.
**Task:** After running /refresh-command (which creates local modifications), run update.sh and verify.

| Check | Criteria | Result |
|-------|----------|--------|
| Local changes preserved | update.sh warns, does not overwrite | Pending |
| New commands added | Missing commands copied from core | Pending |
| Unmodified files updated | Files matching core are updated | Pending |
| install.sh overlay | Re-install preserves local modifications | Pending |
| Conflict summary | Clear list of skipped files shown | Pending |

### Scenario 5: drift-log.md Verification
**Goal:** Validate drift-log accumulation across multiple story runs.
**Task:** After running multiple stories with drift, verify drift-log.md integrity.

| Check | Criteria | Result |
|-------|----------|--------|
| File exists | .writ/specs/[spec]/drift-log.md present | Pending |
| Format correct | Follows drift-report-format.md spec | Pending |
| Append-only | Multiple story entries, no overwrites | Pending |
| DEV-IDs sequential | DEV-001, DEV-002, etc. across runs | Pending |
| Original spec unchanged | spec.md and spec-lite.md unmodified | Pending |

### Scenario 6: Bootstrap Validation
**Goal:** Prove /refresh-command can improve itself.
**Task:** Run `/refresh-command refresh-command --last` on its own transcript.

| Check | Criteria | Result |
|-------|----------|--------|
| Self-scan works | Command identifies its own transcript | Pending |
| Friction found | Patterns identified from its own usage | Pending |
| Improvement proposed | At least one concrete amendment | Pending |
| Self-improvement applied | Local copy updated with improvement | Pending |
| Learning loop confirmed | The learner improves the learner | Pending |

## Success Criteria (from spec contract)

| Criterion | Target | Status |
|-----------|--------|--------|
| `/prototype` wall-clock time | < 5 minutes for small changes | Pending |
| Spec-healing detection rate | ≥3 of 5 stories detect real drift | Pending |
| Spec-healing false positive rate | Zero false positives | Pending |
| `/refresh-command` improvement rate | ≥1 actionable improvement per command | Pending |

## Structural Validation (Pre-Dogfood)

These checks verify the deliverables are structurally sound before dogfooding.

| Check | Status |
|-------|--------|
| All file pairs synchronized (core ↔ .cursor/) | ✅ Pass |
| Cross-references valid (commands → agents, commands → docs) | ✅ Pass |
| Drift report format spec exists and is referenced | ✅ Pass |
| Refresh log format spec exists and is referenced | ✅ Pass |
| Command overlay documentation matches script behavior | ✅ Pass |
| install.sh has overlay-aware copy logic | ✅ Pass |
| update.sh has conflict detection logic | ✅ Pass |
| README updated with /prototype and /refresh-command | ✅ Pass |
| Review agent has drift analysis (additive) | ✅ Pass |
| Coding agent has scope detection heuristic | ✅ Pass |
| Implement-story has Gate 3.5 (drift response) | ✅ Pass |

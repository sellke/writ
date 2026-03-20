# Technical Spec: Prime Directive

## Architecture

This is a content change to two product source files. No runtime, no dependencies, no migrations.

### File Map

| File | Role | Change Type |
|------|------|-------------|
| `system-instructions.md` | Product source, `alwaysApply: true` rule | Replace line 32 reference with Prime Directive section |
| `cursor/writ.mdc` | Product source, Cursor-specific copy | Identical replacement |
| `CHANGELOG.md` | Release documentation | Prepend new entry |
| `VERSION` | Version tracking | `0.6.1` -> `0.7.0` |

### Current State (system-instructions.md line 32)

```markdown
3. **Follow critical thinking guidelines** in `.writ/docs/best-practices.md` — disagree constructively rather than automatically agreeing
```

### Target State

Line 32 replaced with:

```markdown
3. **Follow the Prime Directive below** — honest assessment over comfortable agreement
```

And a new `## Prime Directive` section inserted after the Command Execution Protocol section (after line 33, before `## File Organization`).

### Section Placement

```
# Writ - System Instructions
## Identity & Approach        (lines 5-16, unchanged)
## Command Execution Protocol  (lines 18-33, line 32 modified)
## Prime Directive             (NEW — inserted here)
## File Organization           (shifted down, unchanged)
## Interaction Tool Selection  (shifted down, unchanged)
## Session Auto-Orientation    (shifted down, unchanged)
```

In `cursor/writ.mdc`, the same insertion happens, and the `## Self-Dogfooding` section (present only in writ.mdc) remains at the end.

### Sync Verification

The two files are not identical — `writ.mdc` has a Self-Dogfooding section that `system-instructions.md` doesn't. The Prime Directive section must be identical in both, but we don't need to verify full-file identity.

**Verification approach:** Extract the Prime Directive section from both files and diff them. They should be empty (no differences).

### Distribution

`install.sh` copies `system-instructions.md` to `.cursor/system-instructions.md` and `cursor/writ.mdc` to `.cursor/rules/writ.mdc`. No installer changes needed — the content flows through the existing copy mechanism.

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Prime directive is too aggressive, makes agents combative | Low | Medium | "Disagree with evidence, not attitude" principle explicitly guards against this |
| Content exceeds context budget | Low | Low | Hard-capped at 35 lines; verified in AC |
| Files get out of sync | Low | Low | Story 1 AC requires identical sections |

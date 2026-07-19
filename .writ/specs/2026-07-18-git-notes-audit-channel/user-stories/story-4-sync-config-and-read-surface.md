# Story 4: Notes Sync Config + Opt-Out + `/status` Read Surface + Eval

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 1
> **Story Points:** 3

## User Story

As a **team member cloning a Writ project**, I want **audit notes to travel with the repo and be visible in `/status`**, so that **the audit trail is actually shared (not stranded on one machine) and discoverable without knowing the raw git command.**

## Acceptance Criteria

1. **Given** a Writ install (default posture), **when** `install.sh`/setup runs in a git repo with a remote, **then** it idempotently adds the `+refs/notes/writ:refs/notes/writ` fetch refspec and the `refs/notes/writ` push refspec.
2. **Given** `writ.auditNotes` is `false`, **when** setup runs, **then** it adds no refspecs and removes any Writ-added ones (no residue).
3. **Given** at least one Writ audit note exists, **when** I run `/status`, **then** it shows `📝 Last audit note: <sha> — <spec title> (<date>)`; when none exist, the line is omitted.
4. **Given** the feature, **when** `scripts/eval.sh` runs, **then** a check asserts `ship.md`/`release.md` reference `refs/notes/writ` + the non-blocking rule, and `install.sh` guards the refspec config behind the opt-out.
5. **Given** no remote or not a git repo, **when** setup runs, **then** it warns and skips (no failure).

## Implementation Tasks

- [ ] Add guarded, idempotent `refs/notes/writ` push+fetch refspec configuration to `scripts/install.sh` (see technical-spec §6).
- [ ] Implement the `writ.auditNotes` opt-out in `install.sh` (skip + remove Writ-added refspecs when false).
- [ ] Add the one-line audit pointer to `commands/status.md` (technical-spec §7); omit when no notes exist.
- [ ] Add the eval check (technical-spec §8): a small `eval-*` helper wired into `scripts/eval.sh`.
- [ ] Document the sync setup, `/status` line, and opt-out in `.writ/docs/git-notes-audit-format.md` (extend Story 1's doc).

## Technical Notes

- `install.sh` must be idempotent (grep existing refspecs before adding) and no-op gracefully without a git repo/remote.
- Opt-out marker is the `writ.auditNotes` git config key (default true).
- `/status` should resolve the latest Writ-noted commit cheaply (`git log --notes=writ -1`).
- See `sub-specs/technical-spec.md → §5, §6, §7, §8`.

## Definition of Done

- [ ] `install.sh` configures refspecs (guarded, idempotent, opt-out-aware).
- [ ] `commands/status.md` shows the audit pointer line (conditional).
- [ ] `scripts/eval.sh` gains the passing audit check.
- [ ] Format doc extended with sync/opt-out/status sections.
- [ ] Manual verify: fresh clone with fetch refspec sees notes; opt-out leaves no residue.

## Context for Agents

- **Files in scope:** `scripts/install.sh`, `commands/status.md`, `scripts/eval.sh` (+ new `eval-*` helper), `.writ/docs/git-notes-audit-format.md` (extend).
- **Format reference:** `sub-specs/technical-spec.md → §5, §6, §7, §8`.
- **Business rules:** sync by config unless opted out; opt-out leaves no residue; non-blocking; idempotent.
- **Edge cases:** no remote / not a git repo → warn + skip; no notes yet → omit `/status` line.

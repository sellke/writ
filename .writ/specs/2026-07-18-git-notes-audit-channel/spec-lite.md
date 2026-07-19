# Git-Notes Audit Channel (Lite)

> Source: .writ/specs/2026-07-18-git-notes-audit-channel/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Attach an immutable audit digest to git commits under `refs/notes/writ` — at `/ship` (spec-level digest on the landed commit) and `/release` (version rollup on the tag commit). Default-on, opt-out clean, sync via configured refspecs.

**Implementation Approach:**
- Product-source edits only (markdown + `install.sh`); no app runtime code.
- Attach to the **surviving** post-squash/merge commit — never a pre-merge story commit.
- Compose the digest from existing per-story WWB records (`.writ/docs/what-was-built-format.md`).
- Non-blocking: audit-note failure logs a warning, never fails ship/release.

**Files in Scope:**
- `commands/ship.md` — terminal "Audit Note" step after land/merge
- `commands/release.md` — "Audit Rollup" step after tag
- `commands/status.md` — one-line audit pointer
- `scripts/install.sh` — guarded `refs/notes/writ` push+fetch refspec config + opt-out
- `.writ/docs/git-notes-audit-format.md` — new digest schema + read/sync/opt-out docs
- `.writ/decision-records/adr-017-git-notes-audit-channel.md` — new ADR

**Error Handling:**
- No WWB found → minimal digest (spec ref + SHA + `git diff --stat`)
- `git notes add` fails → warn, continue
- Opted out → silent no-op, zero git-config side effects

**Integration Points:**
- `/ship` land step (provides landed SHA), `/release` tag step, `/status` read surface, `install.sh` setup.

---

## For Review Agents

**Acceptance Criteria:**
1. `git log --notes=writ` shows the digest on the landed commit after `/ship`.
2. Digest contains no transcripts/prompts/chain-of-thought (Prime Directive audit rule).
3. Opt-out suppresses attachment AND leaves git config untouched.
4. Ship/release succeed even when note composition fails (non-blocking).

**Business Rules:**
- Attach to surviving commit only (post-squash tip; rebase → tip commit).
- Dedicated `refs/notes/writ`; never touch `refs/notes/commits`.
- Audit-only content; never CoT/prompts.
- Sync by configured refspecs unless opted out; opt-out leaves no git-config residue.

**Experience Design:**
- Entry: automatic at `/ship` and `/release`.
- Happy path: land commit → read spec WWB → compose digest → `git notes --ref=writ add`.
- Moment of truth: `git log --notes=writ` shows immutable verdict on the landed commit.
- Feedback: one-line confirmation in ship/release; `/status` pointer line.
- Error: warn + continue, never block.

---

## For Testing Agents

**Success Criteria:**
1. Digest present on landed commit under `refs/notes/writ`.
2. No sensitive content in digest.
3. Opt-out = no note + no git-config change.
4. Non-blocking on composition/attachment failure.

**Shadow Paths to Verify:**
- **Happy path:** spec with WWB → digest attached to landed SHA.
- **Nil input:** no WWB records → minimal digest from `git diff --stat`.
- **Empty input:** empty spec / no files → digest notes zero-change, still attaches or warns.
- **Upstream error:** `git notes add` fails → warn, ship/release still succeeds.

**Edge Cases:**
- Squash-merge (new SHA) → note on squash commit, not story commits.
- Rebase-and-merge (N commits) → note on tip landed commit.
- Manual commit outside `/ship`/`/release` → no note (documented, expected).
- Fresh clone without fetch refspec → notes attach locally; sync warning shown.

**Verification Strategy (methodology repo):**
- No code coverage target — deliverables are markdown/command changes.
- Verify via `scripts/eval.sh` static check (refs/notes/writ + non-blocking rule referenced) + manual dogfood `/ship` on this repo.
- New files: N/A coverage; Modified command files: eval check must pass.

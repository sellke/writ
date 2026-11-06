## Draft 1
Title: One flat Markdown table, one row per rule
Structure:
    File: .writ/retro/enforcement.md, a single Markdown table, hand-readable and diffable
    Columns, in order:
      rule_id        short slug, unique, e.g. no-direct-db-in-handlers
      rule           the convention in one sentence
      source         file:line in the steering file or doc that states the rule
      enforcer_kind  one of: architecture | type | lint | test | doc-only
      enforcer_ref   path or name of the check (lint rule id, test file::test name, type name); "-" when doc-only
      proof_commit   SHA of the past commit holding the mistake the check was run against
      proof_result   one line: the failure the check produced on that commit
      added_by       retro run id (date + spec or story slug) that wrote the row
    Rules for writers:
      /retro appends a row when it turns a transcript finding into a fix
      /retro upgrades a row in place when a stronger enforcer_kind replaces a weaker one
      a row with enforcer_kind other than doc-only must have proof_commit and proof_result filled
    Queries (grep or a short script over the table):
      rules with no enforcer      -> rows where enforcer_kind = doc-only
      what enforces rule X        -> the row where rule_id = X
      which mistake proved check  -> proof_commit and proof_result on that row
    Ranking order used by /retro: architecture > type > lint > test > doc-only
Trade-off: one enforcer per rule; a rule checked by both a lint rule and a test loses one of them, and proof history is overwritten on upgrade.

## Draft 2
Title: Normalized rules, enforcers, and proofs
Structure:
    type EnforcerKind = "architecture" | "type" | "lint" | "test" | "doc-only"
    const KIND_RANK: Record<EnforcerKind, number> = { architecture: 1, type: 2, lint: 3, test: 4, "doc-only": 5 }
    interface Location { file: string; line: number }
    interface Rule { id: string; text: string; source: Location; addedBy: string }
    interface Enforcer {
      id: string; ruleId: string; kind: EnforcerKind
      ref: string                 // lint rule id, test path::name, type name, or arch constraint path
      addedBy: string             // retro run id
      retiredAt?: string          // set when the check is removed; row kept for history
    }
    interface Proof {
      enforcerId: string
      mistakeCommit: string       // SHA of the real past mistake
      transcriptRef: string       // transcript file + turn where /retro found it
      failureOutput: string       // what the check printed when run against mistakeCommit
      checkedAt: string
    }
    interface EnforcementTable { rules: Rule[]; enforcers: Enforcer[]; proofs: Proof[] }
    Storage: .writ/retro/enforcement.json holding one EnforcementTable
    function addFix(t: EnforcementTable, rule: Rule, enf: Enforcer, proof: Proof | null): EnforcementTable
      // rejects enf.kind != "doc-only" when proof is null
    function unenforcedRules(t): Rule[]       // rules with no live enforcer, or only doc-only ones
    function enforcersFor(t, ruleId): Enforcer[]   // live ones, sorted by KIND_RANK
    function proofsFor(t, enforcerId): Proof[]
Trade-off: JSON with three linked lists is harder to read and edit by hand than a table, and dangling ids need a validator.

## Draft 3
Title: Append-only event log with derived views
Structure:
    File: .writ/retro/enforcement.log.jsonl, one JSON event per line, never edited, only appended
    Common fields on every event: at (ISO time), run (retro run id), type
    Event types:
      RuleNoted        { ruleId, text, sourceFile, sourceLine }
      EnforcerAdded    { ruleId, enforcerId, kind, ref }
                       kind is one of architecture | type | lint | test | doc-only
      ProofRecorded    { enforcerId, mistakeCommit, transcriptRef, failureOutput }
      EnforcerRemoved  { enforcerId, reason }
      RuleRetired      { ruleId, reason }
    Write rule: /retro emits EnforcerAdded and ProofRecorded together; no ProofRecorded means the check is unproven
    Derived state, rebuilt by replaying the log in order:
      rules:      map ruleId -> { text, source, retired }
      enforcers:  map enforcerId -> { ruleId, kind, ref, live }
      proofs:     map enforcerId -> list of proof records
    Views (a small script, e.g. scripts/enforcement-report.py, prints each):
      --unenforced         live rules whose live enforcers are empty or all doc-only
      --rule <ruleId>      live enforcers for the rule, ordered architecture, type, lint, test, doc-only
      --proof <enforcerId> every recorded mistake commit and failure output for that check
      --unproven           live non-doc-only enforcers with no ProofRecorded event
    History questions (when was a check removed, which run added it) come from the raw log
Trade-off: every answer needs a replay script; nobody can read current state straight from the file.

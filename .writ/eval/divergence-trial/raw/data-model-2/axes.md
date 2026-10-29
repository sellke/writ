## Draft 1
Title: Rule, Enforcer, Mistake tables
Commitment: normalized tables; mutable rows — enforcer rows are edited and deleted in place, so the table shows only current coverage and keeps no record of checks that were replaced or dropped
Structure:
  table rule
    id            text primary key        -- slug, e.g. "handlers-use-service-layer"
    statement     text not null           -- the convention as written
    source        text not null           -- steering file or doc path, with anchor
  table mistake
    id            integer primary key
    ref           text not null unique    -- commit SHA or transcript path + line
    summary       text not null           -- what went wrong
  table enforcer
    id            integer primary key
    rule_id       text not null references rule(id) on delete cascade
    kind          text not null check (kind in ('architecture','type','lint','test','docs'))
    location      text not null           -- config key, file path, or test name
    proven_by     integer references mistake(id)   -- null only when kind = 'docs'
    unique (rule_id, kind, location)
    check (kind = 'docs' or proven_by is not null)
  rank(kind) -> int: architecture=1, type=2, lint=3, test=4, docs=5
  unenforced_rules() -> [rule]: rules with no enforcer row, or whose only rows have kind = 'docs'
  enforcers_for(rule_id) -> [(kind, location)]: rows for rule_id, ordered by rank(kind)
  add_enforcer(rule_id, kind, location, proven_by) -> enforcer.id: inserts mistake by ref if absent; upserts on (rule_id, kind, location); rejects unknown rule_id
  update_enforcer(enforcer_id, location?, proven_by?) -> None: edits the row in place when a check moves
  remove_enforcer(enforcer_id) -> None: deletes the row; the rule reappears in unenforced_rules() if nothing else covers it
  proof_for(enforcer_id) -> mistake | None: join enforcer.proven_by to mistake
Trade-off: no history of removed or relocated checks, so the table cannot say when a rule lost coverage or what used to enforce it.

## Draft 2
Title: Rule records with a nested enforcer list
Commitment: embedded (enforcers inside the rule record); mutable rows — no history: replacing or removing an enforcer overwrites it and its proof in place, and finding an enforcer by id means locating its parent rule first
Structure:
  EnforcerKind = "architecture" | "type" | "lint" | "test" | "docs"   # rank order, strongest first
  Proof:
    mistake_ref: str          # commit SHA, PR number, or transcript id of the past mistake
    note: str                 # one line on what went wrong; may be empty
    checked_at: date          # when the new check was run against that mistake and failed
  Enforcer:
    id: str                   # "<rule_id>/<seq>"; seq increments per rule and is never reused
    kind: EnforcerKind
    location: str             # file path plus the rule, type, or test name inside it
    proof: Proof | None       # required unless kind == "docs"
  Rule:
    id: str                   # stable slug
    text: str                 # the convention as written
    source: str               # steering file or doc path that states it
    enforcers: list[Enforcer] # edited in place
    next_seq: int
    updated_at: datetime
  Store: .writ/retro/rules.json, an object keyed by rule id, rewritten whole on every change
  unenforced_rules() -> list[Rule]                  # enforcers empty, or every enforcer is kind "docs"
  enforcers_for(rule_id) -> list[(EnforcerKind, str)]   # (kind, location), sorted by rank
  add_enforcer(rule_id, kind, location, proven_by) -> str   # appends, returns new id; rejects unknown rule, or missing proven_by when kind != "docs"
  proof_for(enforcer_id) -> Proof | None            # splits id at "/", loads that rule, scans its list
  remove_enforcer(enforcer_id) -> None              # deletes the entry and its proof
Trade-off: Past enforcers and their proofs are not kept once edited or removed, and a lookup by enforcer id depends on the id encoding its parent rule.

## Draft 3
Title: Rule ledger with enforcement event log
Commitment: normalized tables; append-only events — every query rebuilds current state from the event log, so reads cost a fold over history in exchange for a full audit trail of when each check was added or retired
Structure:
  Kind = enum('architecture', 'type', 'lint', 'test', 'docs')   -- rank order /retro uses; 'docs' means not checked
  rules(rule_id TEXT PK, statement TEXT, source_file TEXT, source_line INT, recorded_at TIMESTAMP)
  mistakes(mistake_id INT PK, ref TEXT UNIQUE, description TEXT, transcript TEXT NULL)
      -- ref is a commit SHA or transcript pointer for the real past error a check must catch
  enforcers(enforcer_id INT PK, rule_id TEXT FK rules, kind Kind, location TEXT, UNIQUE(rule_id, kind, location))
  enforcement_events(event_id INT PK, enforcer_id INT FK enforcers, action TEXT CHECK(action IN ('added','retired')),
      proven_by INT FK mistakes NULL, actor TEXT, at TIMESTAMP)
      -- never updated or deleted; an 'added' event for a non-docs kind requires proven_by
  view active_enforcers AS enforcers e WHERE latest event for e.enforcer_id has action = 'added'

  unenforced_rules() -> list[Rule]
      rules r WHERE NOT EXISTS (active_enforcers a WHERE a.rule_id = r.rule_id AND a.kind <> 'docs')
      -- covers both "no enforcer" and "documentation only"
  enforcers_for(rule_id: str) -> list[tuple[Kind, str]]
      SELECT kind, location FROM active_enforcers WHERE rule_id = ? ORDER BY Kind rank
  add_enforcer(rule_id: str, kind: Kind, location: str, proven_by: str | None) -> int
      upsert mistakes(ref=proven_by); get-or-insert enforcers row; append 'added' event; return enforcer_id
      -- raises if rule_id is unknown, or if kind <> 'docs' and proven_by is None
  retire_enforcer(enforcer_id: int, actor: str) -> None   -- appends 'retired'; history stays
  proof_for(enforcer_id: int) -> Mistake | None
      mistake joined from the latest 'added' event for enforcer_id
Trade-off: Every current-state read has to find the latest event per enforcer, and fixing a wrong proof means appending a new event instead of editing the old one.

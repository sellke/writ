## Draft 1
Title: Precedence exit code, all blockers in reason lines
Structure:
    Usage: pr-ready.py [PR] [--repo OWNER/NAME]
      PR: number, URL, or omitted (resolves the PR for the current branch)
    BlockerType (fixed precedence, highest first):
      conflict    merge conflict with the base branch
      checks      one or more required checks failed
      threads     one or more review threads unresolved
      gate        merge gate unmet (required approval, branch protection, draft state)
    Exit codes:
      0   ready: no blockers
      10  conflict is the highest-precedence blocker
      11  checks is the highest-precedence blocker
      12  threads is the highest-precedence blocker
      13  gate is the highest-precedence blocker
      2   usage error (bad flag, PR not found)
      3   lookup error (gh missing, auth failed, API error); verdict is UNKNOWN
    Stdout, in order:
      line 1: READY | BLOCKED | UNKNOWN
      reason: <type> <detail>      one line per blocker instance, every type present
      last line: summary: <n> blockers (<type>=<count>, ...) on PR #<n>
    Behavior: one read of PR state per run; no polling, no waiting, no writes.
Trade-off: the exit code names only one blocker; a caller that wants every type must read the reason lines.

## Draft 2
Title: Bitmask exit code, one bit per blocker type
Structure:
    Usage: pr-ready.py [PR] [--repo OWNER/NAME]
      PR: number, URL, or omitted (resolves the PR for the current branch)
    BlockerBit:
      1   conflict    merge conflict with the base branch
      2   threads     one or more review threads unresolved
      4   checks      one or more required checks failed
      8   gate        merge gate unmet (required approval, branch protection, draft state)
    Exit code:
      0        ready: no bits set
      1..15    OR of the BlockerBit values present (5 = conflict + checks)
      64       usage error (bad flag, PR not found)
      65       lookup error (gh missing, auth failed, API error)
      codes 16..63 reserved; a caller treats any code above 15 as "state unknown"
    Caller test: (code & 4) != 0 means checks are failing, regardless of other bits
    Stdout, in order:
      line 1: READY | BLOCKED | UNKNOWN
      reason: <type> <detail>      one line per blocker instance
      last line: summary: blockers=<type,type,...> mask=<code> pr=#<n>
    Behavior: one read of PR state per run; no polling, no waiting, no writes.
Trade-off: exit codes like 13 are unreadable to a human at a glance and a shell `case` on them gets long.

## Draft 3
Title: Scoped query with a distinct "multiple" code
Structure:
    Usage: pr-ready.py [PR] [--repo OWNER/NAME] [--only TYPE[,TYPE...]]
      PR: number, URL, or omitted (resolves the PR for the current branch)
      --only: restrict the evaluation to the listed blocker types
    BlockerType:
      conflict    merge conflict with the base branch
      threads     one or more review threads unresolved
      checks      one or more required checks failed
      gate        merge gate unmet (required approval, branch protection, draft state)
    Exit codes:
      0   ready: no blockers among the evaluated types
      10  only conflict
      11  only threads
      12  only checks
      13  only gate
      19  two or more types present; reason lines say which
      2   usage error (bad flag, unknown TYPE, PR not found)
      3   lookup error (gh missing, auth failed, API error)
    Watch-loop pattern: on 19, call again with --only <type> per type it can fix
    Stdout, in order:
      line 1: READY | BLOCKED | UNKNOWN
      reason: <type> <detail>      one line per blocker instance in scope
      last line: summary: <n> blockers across <k> types on PR #<n> (scope=<types|all>)
    Behavior: one read of PR state per run; no polling, no waiting, no writes.
Trade-off: when several blockers coexist the caller needs extra runs (or must parse text) to learn which types they are.

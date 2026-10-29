id: api-2
medium: api

The evidence record /why returns when asked why something in a project is the way it is.
Who uses it: a developer reading the answer, and /create-spec, which reads a saved record before it plans a change.
Every claim carries one confidence tier (Recorded, Stated, Corroborated, Inferred, Unknown) and cites its source: a file path and section, a commit SHA, or an MCP server item.
It lists every source searched, in order (Writ's ledger, then git history, then MCP servers), including sources that held nothing.
When a change follows, it adds what to Preserve, what to Change, what to Avoid, and what is at Risk, each with a tier and a source.

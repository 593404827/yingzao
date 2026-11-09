# Project constraints
- Use Python standard library; Python 3.10+. No hardcoded developer-machine paths.
- Never overwrite data/raw. Keep knowledge revisions in Neo4j/CaihuaChange and business execution history in SQLite; retain legacy SQLite knowledge as a migration backup.
- Retired records use active=false; default API excludes them.
- 赭笔 is not an active tool entity; preserve original quotes, split tool 笔 and colour 赭.
- Keep candidate, source-audited and pending distinct. Do not claim teacher approval from model output.
- Preserve source-local technique/part context; do not inherit colours across unrelated systems.
- Relative-width final ratio remains unresolved; raw 减/三分之一 may be recorded without asserting a final computed ratio.
- Run tests after semantic/backend changes. UI automation must use cua_repl.

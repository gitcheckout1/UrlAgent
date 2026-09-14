# Architecture

## Application (one process)

```
                 +------------------+
                 |   app/main.py    |
                 +--------+---------+
                          |
    +---------------------+---------------------+
    |                     |                     |
 app/write           app/redirect          app/analytics
 POST /v1/urls       GET /{code}            GET .../stats
    |                     |                     |
    +---------------------+---------------------+
                          |
                 app/shared (UrlStore)
```

Store: in-memory for M2; SQLite in M7.

## SDLC orchestration graph

```mermaid
flowchart TD
  req[Requirements] --> decomp[Decompose]
  decomp --> design[Design]
  design --> w[Implement write]
  design --> r[Implement redirect]
  design --> a[Implement analytics]
  w --> join[Join]
  r --> join
  a --> join
  join --> test[Run tests]
  test --> docs[Docs]
  docs --> rel[Release]
  rel -->|exit 2| human[HUMAN approve release]
  human --> sum[Summary]
```

Brownfield: insert **impact** after design, then implement nodes run after impact.
Ambiguous: only req → decompose → design. stops after design ( no implement/join/release/summary path)

## Run artifacts
- runs/<id>/state.json — node_status, approvals
- runs/<id>/trace.jsonl — audit log (one JSON per line)

CLI exit codes: 0 done, 2 waiting human, 1 failed.

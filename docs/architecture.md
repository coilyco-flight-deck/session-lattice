# Architecture

session-lattice is the middle layer of a three-service stack across coilysiren/*.

```
+----------------+        pull          +-----------------+       HTTP        +-------+
|  repo-recall   |  <----------------   | session-lattice |  <------------    | luca  |
|  (Rust)        |    refresh tick      |   (Python)      |   view reads      |  +    |
|                |                      |                 |                   |  CLI  |
|  joins +       |                      |   DuckDB        |                   |       |
|  searches +    |                      |   (embedded,    |                   |       |
|  per-source    |                      |    columnar)    |                   |       |
|  caches        |                      |                 |                   |       |
+----------------+                      +-----------------+                   +-------+
```

## Each layer's job

### repo-recall (upstream)

Authoritative store of primary data. Parses Claude session JSONL, walks git logs, queries GitHub. Joins and searches across those sources. Each source has its own cache TTL. Exposes a JSON HTTP API on `localhost:7777`.

session-lattice treats repo-recall as read-only. Never writes back.

### session-lattice (this repo)

Pulls row-shaped data from repo-recall on a refresh tick. Loads rows into DuckDB, where SQL defines a catalog of materialized views (`CREATE OR REPLACE TABLE view_x AS SELECT ...` on each tick). Serves view reads over its own HTTP API on `localhost:7778`.

DuckDB runs embedded inside the Python service process. One .duckdb file at `~/.session-lattice/session-lattice.duckdb` holds the base tables and the materialized view tables. Refresh-tick writes are transactional, so luca readers see either pre-tick or post-tick state, never a torn intermediate.

Each materialized view is an **inverted index** persisted as a DuckDB table. The first one is `tool_sessions` (`tool_name -> [session_id]`). The rationale for using inverted indexes as the primary lookup shape is in the README.

The 1.0 view catalog targets 18-25 views across five axes: session metadata pivots, tool-call pivots, file-axis joins (the load-bearing session × file metadata blowup), commit/PR/issue attribution, and cross-axis temporal joins (`session_blast_radius`, `file_history_at_session_time`).

### luca (downstream)

Stateless. Queries session-lattice's HTTP API, runs analytical skills against the view results, produces digests. No persistent storage in luca. See `coilysiren/luca` for the consumer side.

## Why DuckDB

The dominant query shape is the four-source temporal join (session events × file touches × commits-at-that-moment × issue cross-refs). Columnar storage and vectorized execution are the right specialist fit. The data volume sits comfortably inside one process on one host. Cron-tick refresh with `CREATE OR REPLACE TABLE` is fast enough at this scale that incremental view maintenance isn't earning anything.

If the refresh tick later drops below full-rebuild cost, the escape hatch is Postgres + `pg_ivm`. Schema and SQL port across with minimal rewriting.

## Inspection surface

DuckDB UI attaches read-only to the live database file. Default invocation:

```
duckdb -readonly ~/.session-lattice/session-lattice.duckdb -ui
```

Opens a web console on `localhost:4213` for ad-hoc SQL against the view catalog. Service keeps running while the UI is attached.

## Caching contract

End-to-end staleness is the sum of repo-recall's per-source TTL and session-lattice's per-view refresh tick. Document the per-view refresh interval next to the view definition. The HTTP API exposes a `freshness` field on every view-read response so consumers can decide whether to retry.

## Naming rationale

Three services, three naming registers:

- repo-recall: practical action ("the thing that recalls repos")
- session-lattice: theory ("the lattice of materialized views over session data" - see Harinarayan-Rajaraman-Ullman 1996 on the data-cube lattice)
- luca: cute name ("luca" is Italian for light)

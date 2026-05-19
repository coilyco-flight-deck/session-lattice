# Agent instructions

See `../AGENTS.md` for workspace-level conventions (git workflow, test/lint autonomy, readonly ops, writing voice, deploy knowledge). This file covers only what's specific to this repo.

## What this is

Materialized-view service. Pulls Claude-session row data from `coilysiren/repo-recall` on a refresh tick, maintains a catalog of views inside DuckDB (embedded in-process), exposes the views via HTTP for `coilysiren/luca` and other consumers.

## Layering rules

- Upstream: repo-recall. Pull only. Never push.
- Downstream: luca, plus any future consumer of HTTP view reads.
- Storage: DuckDB file at `~/.session-lattice/session-lattice.duckdb`. Embedded in the service process. Refresh worker holds the read-write handle, HTTP handlers open read-only handles.

## Caching

Two caches stack here: repo-recall's per-source TTLs and session-lattice's per-view refresh tick. End-to-end staleness is the sum. Document the per-view refresh interval in the view definition, never inline.

## See also

- [README.md](README.md) - human-facing intro.
- [docs/FEATURES.md](docs/FEATURES.md) - inventory of what ships today.
- [.coily/coily.yaml](.coily/coily.yaml) - allowlisted commands.

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilysiren/agentic-os/issues/59).

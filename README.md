# session-lattice

Materialized-view service over Claude session data.

Three-layer architecture across coilysiren/*:

- [coilysiren/repo-recall](https://github.com/coilysiren/repo-recall) - joins, searches, and caches over primary sources (Claude session JSONL, git log, GitHub). Authoritative store.
- **session-lattice** (this repo) - pulls from repo-recall on a tick, maintains a catalog of materialized views in DuckDB (embedded, columnar), serves view reads over HTTP on `localhost:7778`.
- [coilysiren/luca](https://github.com/coilysiren/luca) - stateless. Queries session-lattice and turns the views into insights.

See [docs/architecture.md](docs/architecture.md) for the design rationale.

## Install

```sh
brew tap coilysiren/session-lattice https://forgejo.coilysiren.me/coilysiren/session-lattice
brew install coilysiren/session-lattice/session-lattice
brew install coilysiren/session-lattice/session-lattice-puller
brew services start session-lattice
brew services start session-lattice-puller
```

The explicit-URL `brew tap` form is required because this repo isn't `homebrew-*` prefixed.

session-lattice needs `coilysiren/tap/repo-recall` running on `localhost:7777` to be useful. The DuckDB UI extension attaches read-only to the live database file for ad-hoc SQL:

```sh
duckdb -readonly ~/.session-lattice/session-lattice.duckdb -ui
```

## Status

Pre-cable. Repo scaffolded, no service yet. Replaces the archived `coilysiren/otel-a2a-relay`.

## See also

- [AGENTS.md](AGENTS.md) - agent-facing operating rules.
- [docs/FEATURES.md](docs/FEATURES.md) - inventory of what ships today.
- [.coily/coily.yaml](.coily/coily.yaml) - allowlisted commands.

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilysiren/agentic-os/issues/59).

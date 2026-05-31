# Agent instructions

See `../AGENTS.md` for workspace-level conventions (git workflow, test/lint autonomy, readonly ops, writing voice, deploy knowledge). This file covers only what's specific to this repo.

## Scope

Materialized-view service over Claude-session data. Pulls rows from `coilysiren/repo-recall`, maintains a DuckDB view catalog, serves view reads over HTTP for `coilysiren/luca` and other consumers.

## Project shape

Embedded DuckDB inside a Python service process. One file at `~/.session-lattice/session-lattice.duckdb` holds base tables plus materialized view tables. Refresh worker holds the read-write handle, HTTP handlers open read-only handles. See [docs/architecture.md](docs/architecture.md) for the layer diagram.

## Repo boundaries

- Upstream: repo-recall. Pull only. Never push.
- Downstream: luca, plus any future consumer of HTTP view reads.
- Storage boundary: the one DuckDB file. No external state.

## Commands

Route every dev command through coily, which reads [`.coily/coily.yaml`](.coily/coily.yaml). Inherited from `../AGENTS.md`.

## Validation

`pre-commit` runs the agentic-os hook suite plus `emit-dts` (regenerates `session-lattice.d.ts` from the FastAPI reads app's OpenAPI schema). Manual regen: `coily exec emit-dts`.

## Safety

Inherited from `../AGENTS.md`. Never `--no-verify`. Readonly git and shell commands run without confirmation.

## Cross-repo contracts

- HTTP reads surface documented in `session-lattice.d.ts` at the repo root. Auto-generated from the FastAPI reads app's OpenAPI schema by `scripts/emit_dts.py`. Do not edit by hand. Add routes to `_register_read_routes()` in `session_lattice/service.py` and write a real `"""..."""` docstring on each handler (FastAPI's `description`/`summary` fields feed the spec).
- The brew-installed binary IS the contract for staging and prod. See [docs/release.md](docs/release.md) for the dev-vs-staging-vs-prod split.

## Release

Push to `main` triggers tag + GH Release + formula bump. See [docs/release.md](docs/release.md) for the full sequence, the skip-CI marker hazard, and the post-push verification + brew upgrade loop.

## Agent rules

- **Caching**: two caches stack here, repo-recall's per-source TTLs plus session-lattice's per-view refresh tick. End-to-end staleness is the sum. Document the per-view refresh interval in the view definition, never inline.
- **Fix-session-lattice-first**: if a session-lattice fix is needed to unblock other work, ship the smallest fix that unblocks, commit + push, wait for the release, `brew upgrade`, return to the original repo.

## See also

- [README.md](README.md) - human-facing intro.
- [docs/FEATURES.md](docs/FEATURES.md) - inventory of what ships today.
- [.coily/coily.yaml](.coily/coily.yaml) - allowlisted commands.
- [docs/architecture.md](docs/architecture.md) - service-stack diagram and DuckDB rationale.
- [docs/release.md](docs/release.md) - release pipeline and post-push.

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilyco-flight-deck/agentic-os/issues/59).

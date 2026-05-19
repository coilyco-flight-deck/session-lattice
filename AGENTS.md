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

## Release + post-push

Push to `main` -> `.github/workflows/release.yml`: `mathieudutour/github-tag-action` computes semver (`default_bump: patch`, conventional commits drive minor/major), tags + cuts a GH Release. No tap dispatch (see #17 - direct-repo install). `Formula/session-lattice.rb` is the source of truth here; brew picks up the new tag from this repo on the next `brew upgrade`.

Post-push: verify CI at +300s (`coily ops gh run list --repo coilysiren/session-lattice --limit 1`). Python virtualenv install is slower than a Go binary, so don't poll harder than that. Once `completed/success`: `brew upgrade coilysiren/session-lattice/session-lattice` then `brew services restart session-lattice`. Confirm the service is back by hitting `localhost:7778/healthz` and checking the version field reports the just-released tag. Skip the whole loop for docs-only pushes.

The brew-installed binary IS the contract. No `uv run session-lattice serve` against the real DuckDB file from a checkout, no `pip install -e .` shadowing the brew venv. If a session-lattice fix is needed to unblock other work, fix-session-lattice-first: smallest fix that unblocks, commit + push, wait for the release, `brew upgrade`, return to the original repo.

## See also

- [README.md](README.md) - human-facing intro.
- [docs/FEATURES.md](docs/FEATURES.md) - inventory of what ships today.
- [.coily/coily.yaml](.coily/coily.yaml) - allowlisted commands.

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilysiren/agentic-os/issues/59).

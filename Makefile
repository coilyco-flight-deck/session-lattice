.PHONY: sync watch lint fmt test

# Dev knobs. Defaults wire to the `session-lattice-dev` mcporter slot, pointing at
# the `repo-recall-dev` mcporter slot (cargo-watch via repo-recall's `make watch`).
# Separate SESSION_LATTICE_HOME keeps the dev DuckDB off the brew-managed staging file.
port               ?= 7781
repo_recall_url    ?= http://127.0.0.1:7780
home               ?= $(HOME)/.session-lattice-dev
refresh_seconds    ?= 60

sync:
	uv sync

watch: ## uv-run the service with dev env (port 7781 -> repo-recall-dev 7780, separate DuckDB home)
	SESSION_LATTICE_HOST=127.0.0.1 \
	SESSION_LATTICE_PORT=$(port) \
	SESSION_LATTICE_REPO_RECALL_URL=$(repo_recall_url) \
	SESSION_LATTICE_HOME=$(home) \
	SESSION_LATTICE_REFRESH_INTERVAL_SECONDS=$(refresh_seconds) \
		uv run session-lattice serve

lint:
	uv run ruff check session_lattice
	uv run mypy session_lattice

fmt:
	uv run ruff format session_lattice

test:
	uv run pytest tests/

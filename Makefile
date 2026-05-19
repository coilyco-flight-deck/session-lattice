.PHONY: sync lint fmt test

sync:
	uv sync

lint:
	uv run ruff check session_lattice
	uv run mypy session_lattice

fmt:
	uv run ruff format session_lattice

test:
	@echo "no tests yet; first view (tool_sessions) will introduce one"

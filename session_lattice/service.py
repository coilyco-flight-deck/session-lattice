import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from session_lattice import db, refresh
from session_lattice._version import __version__
from session_lattice.config import Config

log = logging.getLogger(__name__)


def bootstrap(config: Config) -> None:
    # Idempotent: open RW once, ensure the meta schema exists, close. The puller
    # owns the RW handle in steady state; this is just first-touch so the
    # `.duckdb` file exists for reads to attach RO against.
    con = db.open_rw(config.db_path)
    try:
        db.init_schema(con)
    finally:
        con.close()


def _register_read_routes(app: FastAPI, config: Config) -> None:
    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/views")
    def list_views() -> dict[str, list[str]]:
        con = db.open_ro(config.db_path)
        try:
            rows = con.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_name NOT LIKE 'meta_%' "
                "ORDER BY table_name"
            ).fetchall()
        finally:
            con.close()
        return {"views": [r[0] for r in rows]}


def create_reads_app(config: Config) -> FastAPI:
    # Reads-only FastAPI. Opens RO handles per request. No refresh task.
    # Assumes the puller (or a prior `serve` / `bootstrap`) has touched the
    # DuckDB file at least once.
    app = FastAPI(title="session-lattice-reads", version=__version__)
    _register_read_routes(app, config)
    return app


def create_combined_app(config: Config) -> FastAPI:
    # Transitional: reads + puller in one process. Backed by the existing
    # `serve` subcommand until coilysiren/session-lattice#27 finishes splitting
    # the two services apart.
    stop_event = asyncio.Event()
    refresh_task: asyncio.Task[None] | None = None

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        nonlocal refresh_task
        bootstrap(config)
        refresh_task = asyncio.create_task(refresh.run(config, stop_event))
        try:
            yield
        finally:
            stop_event.set()
            if refresh_task is not None:
                await refresh_task

    app = FastAPI(title="session-lattice", version=__version__, lifespan=lifespan)
    _register_read_routes(app, config)
    return app


# Backwards-compat alias. External imports of `create_app` keep working.
create_app = create_combined_app

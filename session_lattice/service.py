import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from session_lattice import db, refresh
from session_lattice._version import __version__
from session_lattice.config import Config

log = logging.getLogger(__name__)


def create_app(config: Config) -> FastAPI:
    stop_event = asyncio.Event()
    refresh_task: asyncio.Task[None] | None = None

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        nonlocal refresh_task
        con = db.open_rw(config.db_path)
        try:
            db.init_schema(con)
        finally:
            con.close()
        refresh_task = asyncio.create_task(refresh.run(config, stop_event))
        try:
            yield
        finally:
            stop_event.set()
            if refresh_task is not None:
                await refresh_task

    app = FastAPI(title="session-lattice", version=__version__, lifespan=lifespan)

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

    return app

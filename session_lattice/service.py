import logging

from fastapi import FastAPI

from session_lattice import db, views
from session_lattice._version import __version__
from session_lattice.config import Config

log = logging.getLogger(__name__)


def bootstrap(config: Config) -> None:
    # Idempotent first-touch: open RW once, ensure the meta schema exists, close.
    # Puller owns the RW handle in steady state; this just creates the file for RO attach.
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
    def list_views() -> dict[str, list[dict[str, object]]]:
        # Discovery surface: only views.ALL, so it stays in sync with refresh._tick.
        # Base tables stay reachable via DuckDB UI but don't leak through /views.
        con = db.open_ro(config.db_path)
        try:
            rows = con.execute("SELECT view_name, last_run_at FROM meta_view_watermarks").fetchall()
        finally:
            con.close()
        watermarks = {str(name): ts for name, ts in rows}
        entries = [
            {
                "name": view.NAME,
                "refresh_interval_seconds": float(view.REFRESH_INTERVAL_SECONDS),
                "last_run_at": (
                    watermarks[view.NAME].isoformat() if view.NAME in watermarks else None
                ),
            }
            for view in sorted(views.ALL, key=lambda v: v.NAME)
        ]
        return {"views": entries}


def create_reads_app(config: Config) -> FastAPI:
    # Reads-only FastAPI. Opens RO handles per request. No refresh task.
    # Tolerates a missing DuckDB by surfacing read errors per request, not at startup.
    app = FastAPI(title="session-lattice-reads", version=__version__)
    _register_read_routes(app, config)
    return app

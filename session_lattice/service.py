import logging

from fastapi import FastAPI

from session_lattice import db, views
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
    def list_views() -> dict[str, list[dict[str, object]]]:
        # Discovery surface for downstream consumers: only the materialized
        # views this service publishes, sourced from views.ALL so it stays in
        # sync with what refresh._tick materializes. Puller-written base
        # tables (sessions, tool_calls, etc.) stay reachable via DuckDB UI
        # for ad-hoc SQL but don't leak through /views. Per-view watermark
        # (last_run_at) reflects the last successful materialization.
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
    # Assumes the puller (via `serve-puller`) has touched the DuckDB file at
    # least once. In a fresh checkout the puller's bootstrap runs first; the
    # reads service tolerates a missing file by surfacing the read error per
    # request rather than failing at startup.
    app = FastAPI(title="session-lattice-reads", version=__version__)
    _register_read_routes(app, config)
    return app

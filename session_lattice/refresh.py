import asyncio
import contextlib
import logging
import signal
from datetime import UTC, datetime
from types import ModuleType

import duckdb

from session_lattice import db, puller, views
from session_lattice.config import Config

log = logging.getLogger(__name__)


def serve_forever(config: Config) -> None:
    # Drive `run` to completion on SIGINT/SIGTERM. Used by the standalone
    # `serve-puller` subcommand.
    async def _main() -> None:
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
        await run(config, stop_event)

    asyncio.run(_main())


def _tick_interval(config: Config) -> float:
    # Loop heartbeat: min of all view REFRESH_INTERVAL_SECONDS and the global
    # config knob. Views are gated by their own watermark inside _tick; the
    # heartbeat just controls how often we check.
    intervals = [float(view.REFRESH_INTERVAL_SECONDS) for view in views.ALL]
    intervals.append(config.refresh_interval_seconds)
    return min(intervals)


async def run(config: Config, stop_event: asyncio.Event) -> None:
    heartbeat = _tick_interval(config)
    while not stop_event.is_set():
        started = datetime.now(UTC)
        try:
            await asyncio.to_thread(_tick, config)
            log.info(
                "refresh tick complete in %.2fs",
                (datetime.now(UTC) - started).total_seconds(),
            )
        except Exception:
            log.exception("refresh tick failed")
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=heartbeat)


def _read_watermarks(con: duckdb.DuckDBPyConnection) -> dict[str, datetime]:
    rows = con.execute("SELECT view_name, last_run_at FROM meta_view_watermarks").fetchall()
    return {str(name): ts for name, ts in rows}


def _due_views(watermarks: dict[str, datetime], now: datetime) -> list[ModuleType]:
    due: list[ModuleType] = []
    for view in views.ALL:
        last = watermarks.get(view.NAME)
        if last is None:
            due.append(view)
            continue
        elapsed = (now - last).total_seconds()
        if elapsed >= float(view.REFRESH_INTERVAL_SECONDS):
            due.append(view)
    return due


def _tick(config: Config) -> None:
    # Bootstrap-then-(maybe-pull)-then-materialize-due-views. Skip the
    # pull+materialize cycle entirely if no view is due; honor the upstream
    # ETag if at least one is.
    con = db.open_rw(config.db_path)
    try:
        db.init_schema(con)
        watermarks = _read_watermarks(con)
    finally:
        con.close()

    now = datetime.now(UTC)
    due = _due_views(watermarks, now)
    if not due:
        return

    result = puller.pull_and_write(config)
    if result.skipped_304:
        # Upstream unchanged: leave watermarks alone so we keep checking on
        # the next heartbeat. The puller's ETag cache absorbs the cost.
        return

    con = db.open_rw(config.db_path)
    try:
        for view in due:
            rows = view.materialize(con)
            log.info("view %s materialized %d rows", view.NAME, rows)
            con.execute(
                """
                INSERT INTO meta_view_watermarks (view_name, last_run_at)
                VALUES (?, ?)
                ON CONFLICT (view_name) DO UPDATE SET last_run_at = excluded.last_run_at
                """,
                [view.NAME, datetime.now(UTC)],
            )
    finally:
        con.close()

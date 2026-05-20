import asyncio
import contextlib
import logging
import signal
from datetime import UTC, datetime

from session_lattice import db, puller, views
from session_lattice.config import Config

log = logging.getLogger(__name__)


def serve_forever(config: Config) -> None:
    # Drive `run` to completion on SIGINT/SIGTERM. Used by the standalone
    # `serve-puller` subcommand once coilysiren/session-lattice#27 finishes
    # peeling the puller out of the FastAPI process.
    async def _main() -> None:
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
        await run(config, stop_event)

    asyncio.run(_main())


async def run(config: Config, stop_event: asyncio.Event) -> None:
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
            await asyncio.wait_for(stop_event.wait(), timeout=config.refresh_interval_seconds)


def _tick(config: Config) -> None:
    # Bootstrap-then-pull-then-materialize. The puller atomically replaces
    # base tables in one transaction; views run after the puller commits.
    con = db.open_rw(config.db_path)
    try:
        db.init_schema(con)
    finally:
        con.close()

    result = puller.pull_and_write(config)
    if result.skipped_304:
        return

    con = db.open_rw(config.db_path)
    try:
        for view in views.ALL:
            rows = view.materialize(con)
            log.info("view %s materialized %d rows", view.NAME, rows)
    finally:
        con.close()

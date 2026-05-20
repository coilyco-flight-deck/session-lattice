import asyncio
import contextlib
import logging
import signal
from datetime import UTC, datetime

from session_lattice import db
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
    con = db.open_rw(config.db_path)
    try:
        db.init_schema(con)
        # View materialization lands per-view in follow-up commits.
        # Each view registers its CREATE OR REPLACE TABLE statement against
        # the base tables that the repo-recall puller will populate.
    finally:
        con.close()

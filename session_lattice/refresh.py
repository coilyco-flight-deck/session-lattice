import asyncio
import logging
from datetime import datetime, timezone

from session_lattice import db
from session_lattice.config import Config

log = logging.getLogger(__name__)


async def run(config: Config, stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        started = datetime.now(timezone.utc)
        try:
            await asyncio.to_thread(_tick, config)
            log.info("refresh tick complete in %.2fs", (datetime.now(timezone.utc) - started).total_seconds())
        except Exception:
            log.exception("refresh tick failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=config.refresh_interval_seconds)
        except asyncio.TimeoutError:
            pass


def _tick(config: Config) -> None:
    con = db.open_rw(config.db_path)
    try:
        db.init_schema(con)
        # View materialization lands per-view in follow-up commits.
        # Each view registers its CREATE OR REPLACE TABLE statement against
        # the base tables that the repo-recall puller will populate.
    finally:
        con.close()

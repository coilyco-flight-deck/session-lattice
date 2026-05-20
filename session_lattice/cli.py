import logging

import click
import uvicorn

from session_lattice import refresh, service
from session_lattice._version import __version__
from session_lattice.config import Config


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@click.group()
@click.version_option(__version__, prog_name="session-lattice")
def main() -> None:
    """session-lattice: materialized-view service over Claude session data."""


@main.command(name="serve-reads")
def serve_reads() -> None:
    """Run the read API only. Opens RO handles to the DuckDB file per request."""
    _configure_logging()
    config = Config.from_env()
    service.bootstrap(config)
    app = service.create_reads_app(config)
    uvicorn.run(app, host=config.host, port=config.port, log_config=None)


@main.command(name="serve-puller")
def serve_puller() -> None:
    """Run the puller only. Holds the RW handle, pulls from repo-recall on tick."""
    _configure_logging()
    config = Config.from_env()
    service.bootstrap(config)
    refresh.serve_forever(config)


if __name__ == "__main__":
    main()

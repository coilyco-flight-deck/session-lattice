import logging

import click
import uvicorn

from session_lattice._version import __version__
from session_lattice.config import Config
from session_lattice.service import create_app


@click.group()
@click.version_option(__version__, prog_name="session-lattice")
def main() -> None:
    """session-lattice: materialized-view service over Claude session data."""


@main.command()
def serve() -> None:
    """Start the HTTP service and refresh worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = Config.from_env()
    app = create_app(config)
    uvicorn.run(app, host=config.host, port=config.port, log_config=None)


if __name__ == "__main__":
    main()

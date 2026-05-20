import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    db_path: Path
    host: str
    port: int
    repo_recall_url: str
    refresh_interval_seconds: float

    @classmethod
    def from_env(cls) -> "Config":
        home = Path(os.environ.get("SESSION_LATTICE_HOME", Path.home() / ".session-lattice"))
        home.mkdir(parents=True, exist_ok=True)
        return cls(
            db_path=home / "session-lattice.duckdb",
            host=os.environ.get("SESSION_LATTICE_HOST", "127.0.0.1"),
            port=int(os.environ.get("SESSION_LATTICE_PORT", "7778")),
            repo_recall_url=os.environ.get(
                "SESSION_LATTICE_REPO_RECALL_URL", "http://127.0.0.1:7777"
            ),
            refresh_interval_seconds=float(
                os.environ.get("SESSION_LATTICE_REFRESH_INTERVAL_SECONDS", "60")
            ),
        )

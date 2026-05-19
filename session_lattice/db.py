from pathlib import Path

import duckdb


def open_rw(db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path), read_only=False)
    con.execute("SET memory_limit = '4GB'")
    return con


def open_ro(db_path: Path) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(db_path), read_only=True)


def init_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS meta_refresh_log (
            tick_started_at TIMESTAMP NOT NULL,
            tick_finished_at TIMESTAMP,
            view_name VARCHAR NOT NULL,
            row_count BIGINT,
            error VARCHAR
        )
        """
    )

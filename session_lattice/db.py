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
    # Tick log. Separate from base tables; never truncated.
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
    # Per-view watermark: when each registered view last materialized.
    # Drives refresh._tick cadence; reset by bumping REFRESH_INTERVAL_SECONDS on the view.
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS meta_view_watermarks (
            view_name VARCHAR PRIMARY KEY,
            last_run_at TIMESTAMP NOT NULL
        )
        """
    )
    # Base tables populated by the puller from repo-recall's /api/sessions.
    # Atomically replaced each tick so views can pivot any column without re-pulling.
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id BIGINT NOT NULL,
            session_uuid VARCHAR NOT NULL,
            cwd VARCHAR,
            started_at BIGINT,
            ended_at BIGINT,
            message_count BIGINT NOT NULL,
            user_message_count BIGINT NOT NULL,
            assistant_message_count BIGINT NOT NULL,
            last_prompt VARCHAR,
            source_file VARCHAR NOT NULL,
            duration_ms BIGINT,
            input_tokens BIGINT NOT NULL,
            output_tokens BIGINT NOT NULL,
            cache_read_tokens BIGINT NOT NULL,
            cache_creation_tokens BIGINT NOT NULL,
            parent_uuid VARCHAR,
            request_id VARCHAR,
            message_id VARCHAR,
            is_sidechain_count BIGINT NOT NULL,
            models_used VARCHAR[] NOT NULL,
            tools_used VARCHAR[] NOT NULL,
            tool_call_counts_json VARCHAR NOT NULL,
            stop_reason_counts_json VARCHAR NOT NULL
        )
        """
    )
    # Session <-> repo membership (many-to-many via the JSONL cwd join).
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS session_repos (
            session_id BIGINT NOT NULL,
            repo_id BIGINT NOT NULL,
            repo_name VARCHAR NOT NULL,
            repo_path VARCHAR NOT NULL
        )
        """
    )
    # `tool_call_counts_json` exploded into rows: per-(session, tool) counts.
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS tool_calls (
            session_id BIGINT NOT NULL,
            tool_name VARCHAR NOT NULL,
            call_count BIGINT NOT NULL,
            error_count BIGINT NOT NULL
        )
        """
    )
    # `stop_reason_counts_json` exploded into rows.
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS stop_reasons (
            session_id BIGINT NOT NULL,
            stop_reason VARCHAR NOT NULL,
            count BIGINT NOT NULL
        )
        """
    )

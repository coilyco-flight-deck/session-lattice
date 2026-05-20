import duckdb

NAME = "tool_sessions"
# Cheap to materialize (single aggregate over tool_calls), value-per-refresh
# is high for downstream tool-usage views. Keep on the default minute cadence.
REFRESH_INTERVAL_SECONDS = 60


def materialize(con: duckdb.DuckDBPyConnection) -> int:
    # Inverted index: tool_name -> [session_id]. First view of the catalog
    # described in docs/architecture.md.
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {NAME} AS
        SELECT
            tool_name,
            ARRAY_AGG(DISTINCT session_id ORDER BY session_id) AS session_ids,
            COUNT(DISTINCT session_id) AS session_count
        FROM tool_calls
        GROUP BY tool_name
        ORDER BY session_count DESC
        """
    )
    result = con.execute(f"SELECT COUNT(*) FROM {NAME}").fetchone()
    return int(result[0]) if result else 0

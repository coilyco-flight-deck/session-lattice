"""One-shot smoke: pull from the local repo-recall and materialize views.

Run via `coily exec smoke-puller` after starting repo-recall on 7777. Writes
to SESSION_LATTICE_HOME if set, else ~/.session-lattice-smoke.
"""

import os
from pathlib import Path

from session_lattice import db, puller, views
from session_lattice.config import Config


def main() -> None:
    os.environ.setdefault("SESSION_LATTICE_HOME", str(Path.home() / ".session-lattice-smoke"))
    os.environ.setdefault("SESSION_LATTICE_REPO_RECALL_URL", "http://127.0.0.1:7777")
    config = Config.from_env()

    con = db.open_rw(config.db_path)
    try:
        db.init_schema(con)
    finally:
        con.close()

    result = puller.pull_and_write(config)
    print(f"puller: {result}")

    con = db.open_rw(config.db_path)
    try:
        for view in views.ALL:
            rows = view.materialize(con)
            print(f"view {view.NAME}: {rows} rows")
    finally:
        con.close()

    ro = db.open_ro(config.db_path)
    try:
        print("\ntop 10 tool_sessions:")
        for r in ro.execute(
            "SELECT tool_name, session_count FROM tool_sessions LIMIT 10"
        ).fetchall():
            print(f"  {r[0]}: {r[1]} sessions")
        total_sessions = ro.execute("SELECT COUNT(*) FROM sessions").fetchone()
        total_tool_calls = ro.execute("SELECT COUNT(*) FROM tool_calls").fetchone()
        total_repos = ro.execute("SELECT COUNT(*) FROM session_repos").fetchone()
        total_stops = ro.execute("SELECT COUNT(*) FROM stop_reasons").fetchone()
        print(
            f"\nbase tables: sessions={total_sessions[0] if total_sessions else 0} "
            f"session_repos={total_repos[0] if total_repos else 0} "
            f"tool_calls={total_tool_calls[0] if total_tool_calls else 0} "
            f"stop_reasons={total_stops[0] if total_stops else 0}"
        )
    finally:
        ro.close()


if __name__ == "__main__":
    main()

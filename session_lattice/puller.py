import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from session_lattice import db
from session_lattice.config import Config

log = logging.getLogger(__name__)

# In-process ETag cache keyed by URL. One cache per puller process: a restart
# always re-pulls on the first tick, which is fine. Persisting to DuckDB would
# add complexity without buying anything until cold-start times become real.
_etag_cache: dict[str, str | None] = {}


@dataclass(frozen=True)
class PullResult:
    sessions_written: int
    session_repos_written: int
    tool_calls_written: int
    stop_reasons_written: int
    skipped_304: bool


SessionRow = tuple[
    int,  # id
    str,  # session_uuid
    str | None,  # cwd
    int | None,  # started_at
    int | None,  # ended_at
    int,  # message_count
    int,  # user_message_count
    int,  # assistant_message_count
    str | None,  # last_prompt
    str,  # source_file
    int | None,  # duration_ms
    int,  # input_tokens
    int,  # output_tokens
    int,  # cache_read_tokens
    int,  # cache_creation_tokens
    str | None,  # parent_uuid
    str | None,  # request_id
    str | None,  # message_id
    int,  # is_sidechain_count
    list[str],  # models_used
    list[str],  # tools_used
    str,  # tool_call_counts_json
    str,  # stop_reason_counts_json
]


def _project_session(session: dict[str, Any]) -> SessionRow:
    return (
        int(session["id"]),
        str(session["session_uuid"]),
        session.get("cwd"),
        session.get("started_at"),
        session.get("ended_at"),
        int(session.get("message_count", 0)),
        int(session.get("user_message_count", 0)),
        int(session.get("assistant_message_count", 0)),
        session.get("last_prompt"),
        str(session.get("source_file", "")),
        session.get("duration_ms"),
        int(session.get("input_tokens", 0)),
        int(session.get("output_tokens", 0)),
        int(session.get("cache_read_tokens", 0)),
        int(session.get("cache_creation_tokens", 0)),
        session.get("parent_uuid"),
        session.get("request_id"),
        session.get("message_id"),
        int(session.get("is_sidechain_count", 0)),
        list(session.get("models_used") or []),
        list(session.get("tools_used") or []),
        str(session.get("tool_call_counts_json", "")),
        str(session.get("stop_reason_counts_json", "")),
    )


def _explode_counts(session_id: int, raw_json: str) -> list[tuple[int, str, int, int]]:
    # Parses `{ "<key>": { "calls": N, "errors": N } }` into per-key rows.
    # Used for tool_call_counts_json.
    if not raw_json:
        return []
    try:
        counts: dict[str, dict[str, Any]] = json.loads(raw_json)
    except json.JSONDecodeError:
        log.warning("malformed tool_call_counts_json for session %s", session_id)
        return []
    return [
        (
            session_id,
            str(name),
            int(stats.get("calls", 0)),
            int(stats.get("errors", 0)),
        )
        for name, stats in counts.items()
    ]


def _explode_stop_reasons(session_id: int, raw_json: str) -> list[tuple[int, str, int]]:
    # Parses `{ "<stop_reason>": N }` into per-reason rows.
    if not raw_json:
        return []
    try:
        counts: dict[str, Any] = json.loads(raw_json)
    except json.JSONDecodeError:
        log.warning("malformed stop_reason_counts_json for session %s", session_id)
        return []
    return [(session_id, str(reason), int(count)) for reason, count in counts.items()]


def pull_and_write(config: Config) -> PullResult:
    # Fetch upstream sessions, project Session/SessionWithRepos into row batches,
    # atomically replace every base table in one transaction so concurrent RO
    # readers see either pre-tick or post-tick state, never a torn write.
    url = f"{config.repo_recall_url.rstrip('/')}/api/sessions"

    headers: dict[str, str] = {}
    cached_etag = _etag_cache.get(url)
    if cached_etag is not None:
        headers["If-None-Match"] = cached_etag

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers)

    if response.status_code == 304:
        log.info("repo-recall scan unchanged, skipping materialization")
        return PullResult(0, 0, 0, 0, skipped_304=True)

    response.raise_for_status()
    etag = response.headers.get("ETag")
    if etag is not None:
        _etag_cache[url] = etag

    payload = response.json()
    entries: list[dict[str, Any]] = payload.get("sessions", [])

    session_rows: list[SessionRow] = []
    session_repo_rows: list[tuple[int, int, str, str]] = []
    tool_call_rows: list[tuple[int, str, int, int]] = []
    stop_reason_rows: list[tuple[int, str, int]] = []

    for entry in entries:
        session = entry.get("session") or {}
        repos = entry.get("repos") or []
        if "id" not in session:
            continue
        session_id = int(session["id"])
        session_rows.append(_project_session(session))
        for repo in repos:
            # Wire shape from repo-recall: [repo_id, repo_name, repo_path].
            if not isinstance(repo, list) or len(repo) < 3:
                continue
            session_repo_rows.append((session_id, int(repo[0]), str(repo[1]), str(repo[2])))
        tool_call_rows.extend(
            _explode_counts(session_id, session.get("tool_call_counts_json") or "")
        )
        stop_reason_rows.extend(
            _explode_stop_reasons(session_id, session.get("stop_reason_counts_json") or "")
        )

    con = db.open_rw(config.db_path)
    try:
        con.execute("BEGIN TRANSACTION")
        con.execute("DELETE FROM sessions")
        con.execute("DELETE FROM session_repos")
        con.execute("DELETE FROM tool_calls")
        con.execute("DELETE FROM stop_reasons")
        if session_rows:
            con.executemany(
                "INSERT INTO sessions VALUES (" + ", ".join(["?"] * 23) + ")",
                session_rows,
            )
        if session_repo_rows:
            con.executemany(
                "INSERT INTO session_repos VALUES (?, ?, ?, ?)",
                session_repo_rows,
            )
        if tool_call_rows:
            con.executemany(
                "INSERT INTO tool_calls VALUES (?, ?, ?, ?)",
                tool_call_rows,
            )
        if stop_reason_rows:
            con.executemany(
                "INSERT INTO stop_reasons VALUES (?, ?, ?)",
                stop_reason_rows,
            )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()

    log.info(
        "puller wrote %d sessions, %d session_repos, %d tool_calls, %d stop_reasons",
        len(session_rows),
        len(session_repo_rows),
        len(tool_call_rows),
        len(stop_reason_rows),
    )
    return PullResult(
        sessions_written=len(session_rows),
        session_repos_written=len(session_repo_rows),
        tool_calls_written=len(tool_call_rows),
        stop_reasons_written=len(stop_reason_rows),
        skipped_304=False,
    )

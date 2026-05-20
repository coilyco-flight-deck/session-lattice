import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest

from session_lattice import db, puller, views
from session_lattice.config import Config


def _fixture_payload() -> dict[str, Any]:
    return {
        "sessions": [
            {
                "session": {
                    "id": 1,
                    "session_uuid": "uuid-1",
                    "cwd": "/tmp/repo-a",
                    "started_at": 1700000000,
                    "ended_at": 1700000100,
                    "message_count": 10,
                    "user_message_count": 5,
                    "assistant_message_count": 5,
                    "last_prompt": "hello",
                    "source_file": "/tmp/sess-1.jsonl",
                    "duration_ms": 100000,
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "cache_read_tokens": 200,
                    "cache_creation_tokens": 50,
                    "parent_uuid": None,
                    "request_id": None,
                    "message_id": None,
                    "is_sidechain_count": 0,
                    "models_used": ["sonnet-4-6"],
                    "tools_used": ["Bash", "Read"],
                    "tool_call_counts_json": json.dumps(
                        {
                            "Bash": {"calls": 3, "errors": 1},
                            "Read": {"calls": 2, "errors": 0},
                        }
                    ),
                    "stop_reason_counts_json": json.dumps({"end_turn": 4}),
                },
                "repos": [[42, "repo-a", "/tmp/repo-a"]],
            },
            {
                "session": {
                    "id": 2,
                    "session_uuid": "uuid-2",
                    "cwd": "/tmp/repo-b",
                    "started_at": 1700001000,
                    "ended_at": None,
                    "message_count": 4,
                    "user_message_count": 2,
                    "assistant_message_count": 2,
                    "last_prompt": None,
                    "source_file": "/tmp/sess-2.jsonl",
                    "duration_ms": None,
                    "input_tokens": 500,
                    "output_tokens": 250,
                    "cache_read_tokens": 0,
                    "cache_creation_tokens": 0,
                    "parent_uuid": None,
                    "request_id": None,
                    "message_id": None,
                    "is_sidechain_count": 0,
                    "models_used": ["sonnet-4-6"],
                    "tools_used": ["Bash"],
                    "tool_call_counts_json": json.dumps(
                        {"Bash": {"calls": 1, "errors": 0}}
                    ),
                    "stop_reason_counts_json": json.dumps({"end_turn": 1}),
                },
                "repos": [[42, "repo-a", "/tmp/repo-a"], [43, "repo-b", "/tmp/repo-b"]],
            },
        ],
        "generated_at": 1700002000,
        "scan_version": 7,
    }


class _Handler(BaseHTTPRequestHandler):
    payload: dict[str, Any] = {}

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/sessions":
            body = json.dumps(self.payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("ETag", '"7"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass


@pytest.fixture
def fake_repo_recall() -> Any:
    _Handler.payload = _fixture_payload()
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        thread.join(timeout=2)


def test_pull_and_materialize_tool_sessions(tmp_path: Path, fake_repo_recall: str) -> None:
    # Reset the puller's in-process ETag cache so the test is hermetic.
    puller._etag_cache.clear()

    config = Config(
        db_path=tmp_path / "test.duckdb",
        host="127.0.0.1",
        port=0,
        repo_recall_url=fake_repo_recall,
        refresh_interval_seconds=60.0,
    )

    con = db.open_rw(config.db_path)
    try:
        db.init_schema(con)
    finally:
        con.close()

    result = puller.pull_and_write(config)
    assert result.skipped_304 is False
    assert result.sessions_written == 2
    assert result.tool_calls_written == 3
    assert result.session_repos_written == 3
    assert result.stop_reasons_written == 2

    con = db.open_rw(config.db_path)
    try:
        rows = views.ALL[0].materialize(con)
        assert rows == 2  # Bash + Read distinct tool names
    finally:
        con.close()

    ro = db.open_ro(config.db_path)
    try:
        result_rows = ro.execute(
            "SELECT tool_name, session_count FROM tool_sessions ORDER BY tool_name"
        ).fetchall()
        assert result_rows == [("Bash", 2), ("Read", 1)]

        bash_sessions = ro.execute(
            "SELECT session_ids FROM tool_sessions WHERE tool_name = 'Bash'"
        ).fetchone()
        assert bash_sessions is not None
        assert list(bash_sessions[0]) == [1, 2]
    finally:
        ro.close()

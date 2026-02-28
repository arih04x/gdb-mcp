from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

from gdb_mcp.gdb_session import GdbSession, _normalize_output


def test_normalize_output_removes_terminal_sequences() -> None:
    raw = "\x1b[?2004h\x1b[32mReading symbols\x1b[m\r\n\x1b[?2004l"
    assert _normalize_output(raw) == "Reading symbols"


def test_normalize_output_normalizes_newlines() -> None:
    raw = "line1\r\nline2\rline3\n"
    assert _normalize_output(raw) == "line1\nline2\nline3"


def test_to_dict_uses_rfc3339_utc_z_suffix() -> None:
    child = Mock()
    session = GdbSession(
        session_id="abc123",
        gdb_path="/usr/bin/gdb",
        working_dir=Path("/tmp"),
        child=child,
        startup_output="",
        started_at=datetime(2026, 2, 28, 14, 0, 0, tzinfo=UTC),
    )

    payload = session.to_dict()
    assert payload["started_at"] == "2026-02-28T14:00:00Z"

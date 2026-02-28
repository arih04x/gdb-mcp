from __future__ import annotations

from unittest.mock import Mock

import pytest

from gdb_mcp.gdb_manager import GdbSessionManager


def test_set_program_args_rejects_non_string_items() -> None:
    manager = GdbSessionManager()
    session = Mock()
    manager._sessions["sid"] = session
    with pytest.raises(ValueError):
        manager.set_program_args("sid", ["ok", 1])  # type: ignore[list-item]
    manager._sessions.clear()


def test_toggle_breakpoints_rejects_empty_ids() -> None:
    manager = GdbSessionManager()
    with pytest.raises(ValueError):
        manager.toggle_breakpoints("sid", [], True)


def test_set_watchpoint_rejects_unknown_mode() -> None:
    manager = GdbSessionManager()
    with pytest.raises(ValueError):
        manager.set_watchpoint("sid", "x", mode="bad")


def test_collect_crash_report_captures_command_failures() -> None:
    manager = GdbSessionManager()
    session = Mock()

    def execute(command: str) -> str:
        if command == "frame":
            raise ValueError("no frame selected")
        return f"ok:{command}"

    session.execute.side_effect = execute
    manager._sessions["sid"] = session

    report = manager.collect_crash_report("sid")
    assert report["program_info"] == "ok:info program"
    assert report["current_frame"].startswith("[error] ValueError")
    manager._sessions.clear()

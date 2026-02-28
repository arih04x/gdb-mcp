from __future__ import annotations

from pathlib import Path
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


def test_load_core_uses_unquoted_resolved_paths(tmp_path: Path) -> None:
    manager = GdbSessionManager()
    session = Mock()
    session.working_dir = tmp_path
    session.execute.side_effect = ["ok:file", "ok:core", "ok:bt"]
    manager._sessions["sid"] = session

    program = tmp_path / "demo_program"
    core_file = tmp_path / "demo_core"
    program.write_text("", encoding="utf-8")
    core_file.write_text("", encoding="utf-8")

    report = manager.load_core("sid", str(program), str(core_file))

    assert report["program_output"] == "ok:file"
    assert report["core_output"] == "ok:core"
    assert report["backtrace_output"] == "ok:bt"

    commands = [call.args[0] for call in session.execute.call_args_list]
    assert commands[0].startswith('file "')
    assert commands[1].startswith("core-file ")
    assert '"' not in commands[1]
    assert commands[1] == f"core-file {core_file}"
    manager._sessions.clear()


def test_load_core_rejects_whitespace_path(tmp_path: Path) -> None:
    manager = GdbSessionManager()
    session = Mock()
    session.working_dir = tmp_path
    manager._sessions["sid"] = session

    program = tmp_path / "demo_program"
    core_file = tmp_path / "demo core"
    program.write_text("", encoding="utf-8")
    core_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        manager.load_core("sid", str(program), str(core_file))
    manager._sessions.clear()


def test_collect_crash_report_collects_from_top_frame_and_restores_selection() -> None:
    manager = GdbSessionManager()
    session = Mock()
    state = {"frame": 3}

    def execute(command: str) -> str:
        if command == "frame":
            return f"#{state['frame']} selected"
        if command.startswith("frame "):
            state["frame"] = int(command.split()[1])
            return f"#{state['frame']} selected"
        return f"ok:{command}"

    session.execute.side_effect = execute
    manager._sessions["sid"] = session

    report = manager.collect_crash_report("sid")
    commands = [call.args[0] for call in session.execute.call_args_list]

    assert commands[0] == "frame"
    assert commands[1] == "frame 0"
    assert report["current_frame"].startswith("#0")
    assert commands[-1] == "frame 3"
    assert state["frame"] == 3
    manager._sessions.clear()

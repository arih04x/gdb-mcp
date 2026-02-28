from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from gdb_mcp.gdb_manager import GdbSessionManager


@pytest.fixture()
def compiled_crash(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "examples" / "crash.c"
    output = tmp_path / "crash_dbg"

    subprocess.run(
        ["gcc", "-g", "-O0", str(source), "-o", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    return output


@pytest.mark.integration
def test_gdb_session_debug_workflow(compiled_crash: Path) -> None:
    manager = GdbSessionManager()
    started = manager.start_session(working_dir=str(compiled_crash.parent))
    session_id = started["session_id"]

    try:
        manager.command(session_id, "set pagination off")

        load_result = manager.load_program(session_id, str(compiled_crash), ["15"])
        assert load_result["target"] == str(compiled_crash)
        assert "Reading symbols" in load_result["load_output"]

        bp_result = manager.set_breakpoint(session_id, "main")
        assert "Breakpoint" in bp_result["breakpoint_output"]

        run_output = manager.command(session_id, "run")
        assert "Breakpoint" in run_output

        list_result = manager.list_source(session_id, line_count=8)
        assert isinstance(list_result["output"], str)

        print_output = manager.print_expression(session_id, "number")
        assert "$" in print_output

        bt_output = manager.backtrace(session_id, limit=5)
        assert "#0" in bt_output
    finally:
        manager.terminate_all()


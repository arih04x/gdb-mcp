from __future__ import annotations

import gdb_mcp.server as server


def test_gdb_command_prefers_mi_records(monkeypatch) -> None:
    monkeypatch.setattr(server.manager, "command", lambda session_id, command: '^done,bkpt={number="1"}')

    result = server.gdb_command("sid", 'interpreter-exec mi "-break-insert main"')

    assert result["ok"] is True
    assert len(result["miRecords"]) == 1
    assert result["miRecords"][0]["type"] == "result"
    assert "output" not in result


def test_gdb_command_separates_mi_streams(monkeypatch) -> None:
    monkeypatch.setattr(server.manager, "command", lambda session_id, command: '~"GNU gdb\\n"\n^done')

    result = server.gdb_command("sid", 'interpreter-exec mi "-gdb-version"')

    assert result["ok"] is True
    assert len(result["miRecords"]) == 1
    assert result["miRecords"][0]["type"] == "result"
    assert len(result["miStreams"]) == 1
    assert result["miStreams"][0]["type"] == "console"
    assert "output" not in result


def test_gdb_command_keeps_output_when_mi_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(server.manager, "command", lambda session_id, command: "Breakpoint 1 at 0x401000")

    result = server.gdb_command("sid", "run")

    assert result["ok"] is True
    assert result["miRecords"] == []
    assert result["output"] == "Breakpoint 1 at 0x401000"


def test_gdb_backtrace_prefers_frames(monkeypatch) -> None:
    monkeypatch.setattr(server.manager, "backtrace", lambda session_id, full, limit: "#0  main () at demo.c:7")

    result = server.gdb_backtrace("sid")

    assert result["ok"] is True
    assert result["frames"][0]["function"] == "main"
    assert "output" not in result


def test_gdb_collect_crash_report_compacts_raw_fields(monkeypatch) -> None:
    monkeypatch.setattr(server, "_require_advanced", lambda _tool_name: None)
    monkeypatch.setattr(
        server.manager,
        "collect_crash_report",
        lambda session_id, backtrace_limit, disasm_count, stack_words: {
            "program_info": "Using host libthread_db library",
            "backtrace": "#0  main () at demo.c:7",
            "registers": "rip 0x401000 0x401000 <main+0>",
            "pc_disassembly": "=> 0x401000 <main+0>: push %rbp",
        },
    )

    result = server.gdb_collect_crash_report("sid")

    assert result["ok"] is True
    assert result["frames"][0]["function"] == "main"
    assert "rip" in result["registers"]
    assert "backtrace" not in result["report"]
    assert "registers" not in result["report"]
    assert "pc_disassembly" in result["report"]

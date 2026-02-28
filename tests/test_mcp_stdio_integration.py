from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.integration
def test_stdio_server_initialize_list_and_call() -> None:
    async def _run() -> None:
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env.pop("GDB_MCP_CONFIG", None)
        env["GDB_MODE"] = "default"
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "gdb_mcp.server"],
            cwd=str(repo_root),
            env=env,
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                initialize_result = await session.initialize()
                assert initialize_result.serverInfo.name == "gdb-mcp-server"

                tools_result = await session.list_tools()
                tool_names = {tool.name for tool in tools_result.tools}
                assert "gdb_start" in tool_names
                assert "gdb_list_sessions" in tool_names
                assert "gdb_get_capabilities" in tool_names
                assert "gdb_list_breakpoints" in tool_names
                assert "gdb_backtrace" in tool_names
                assert "gdb_info_registers" in tool_names
                assert "gdb_collect_crash_report" not in tool_names
                assert "gdb_attach" not in tool_names
                assert "gdb_load_core" not in tool_names
                assert "gdb_finish" not in tool_names
                assert "gdb_list_source" not in tool_names
                assert "gdb_frame_up" not in tool_names
                assert "gdb_frame_down" not in tool_names

                caps = await session.call_tool("gdb_get_capabilities", {})
                caps_payload = json.loads(caps.content[0].text)
                assert caps_payload["ok"] is True
                assert caps_payload["mode"] == "default"

                call_result = await session.call_tool("gdb_list_sessions", {})
                assert call_result.isError is False
                assert len(call_result.content) == 1
                assert call_result.content[0].type == "text"

                payload = json.loads(call_result.content[0].text)
                assert payload["ok"] is True
                assert payload["count"] == 0
                assert payload["sessions"] == []

    anyio.run(_run)


@pytest.mark.integration
def test_stdio_server_exposes_advanced_tools_in_advanced_mode() -> None:
    async def _run() -> None:
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env.pop("GDB_MCP_CONFIG", None)
        env["GDB_MODE"] = "advanced"
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "gdb_mcp.server"],
            cwd=str(repo_root),
            env=env,
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                tool_names = {tool.name for tool in tools_result.tools}
                assert "gdb_collect_crash_report" in tool_names
                assert "gdb_set_watchpoint" in tool_names
                assert "gdb_info_threads" in tool_names
                assert "gdb_attach" in tool_names
                assert "gdb_load_core" in tool_names
                assert "gdb_finish" not in tool_names
                assert "gdb_list_source" not in tool_names

    anyio.run(_run)

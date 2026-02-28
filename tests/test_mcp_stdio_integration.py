from __future__ import annotations

import json
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
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "gdb_mcp.server"],
            cwd=str(repo_root),
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                initialize_result = await session.initialize()
                assert initialize_result.serverInfo.name == "gdb-mcp-server"

                tools_result = await session.list_tools()
                tool_names = {tool.name for tool in tools_result.tools}
                assert "gdb_start" in tool_names
                assert "gdb_list_sessions" in tool_names

                call_result = await session.call_tool("gdb_list_sessions", {})
                assert call_result.isError is False
                assert len(call_result.content) == 1
                assert call_result.content[0].type == "text"

                payload = json.loads(call_result.content[0].text)
                assert payload["ok"] is True
                assert payload["count"] == 0
                assert payload["sessions"] == []

    anyio.run(_run)

"""MCP stdio server exposing GDB operations."""

from __future__ import annotations

from typing import Any

from loguru import logger
from mcp.server.fastmcp import FastMCP

from gdb_mcp.exceptions import GdbCommandTimeoutError, GdbSessionError, SessionNotFoundError
from gdb_mcp.gdb_manager import GdbSessionManager, install_signal_cleanup

RECOVERABLE_ERRORS = (
    FileNotFoundError,
    PermissionError,
    ValueError,
    OSError,
    GdbSessionError,
    GdbCommandTimeoutError,
    SessionNotFoundError,
)

mcp = FastMCP("gdb-mcp-server")
manager = GdbSessionManager()
install_signal_cleanup(manager)


def _ok(**payload: Any) -> dict[str, Any]:
    payload["ok"] = True
    return payload


def _err(exc: BaseException) -> dict[str, Any]:
    return {
        "ok": False,
        "error": str(exc),
        "error_type": type(exc).__name__,
    }


@mcp.tool()
def gdb_start(gdbPath: str = "gdb", workingDir: str | None = None) -> dict[str, Any]:
    """Start a new GDB session."""
    try:
        result = manager.start_session(gdb_path=gdbPath, working_dir=workingDir)
        return _ok(
            message=f"GDB session started: {result['session_id']}",
            sessionId=result["session_id"],
            workingDir=result["working_dir"],
            gdbPath=result["gdb_path"],
            output=result["output"],
        )
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_load(sessionId: str, program: str, arguments: list[str] | None = None) -> dict[str, Any]:
    """Load a program into GDB."""
    try:
        result = manager.load_program(session_id=sessionId, program=program, arguments=arguments)
        return _ok(
            message=f"Program loaded: {result['target']}",
            target=result["target"],
            loadOutput=result["load_output"],
            argsOutput=result["args_output"],
        )
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_command(sessionId: str, command: str) -> dict[str, Any]:
    """Execute an arbitrary GDB command."""
    try:
        output = manager.command(session_id=sessionId, command=command)
        return _ok(message=f"Command executed: {command}", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_terminate(sessionId: str) -> dict[str, Any]:
    """Terminate a GDB session."""
    try:
        manager.terminate_session(session_id=sessionId)
        return _ok(message=f"GDB session terminated: {sessionId}")
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_list_sessions() -> dict[str, Any]:
    """List active GDB sessions."""
    sessions = manager.list_sessions()
    return _ok(count=len(sessions), sessions=sessions)


@mcp.tool()
def gdb_attach(sessionId: str, pid: int) -> dict[str, Any]:
    """Attach GDB to a process."""
    try:
        output = manager.attach(session_id=sessionId, pid=pid)
        return _ok(message=f"Attached to process: {pid}", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_load_core(sessionId: str, program: str, corePath: str) -> dict[str, Any]:
    """Load executable and core file into GDB."""
    try:
        result = manager.load_core(session_id=sessionId, program=program, core_path=corePath)
        return _ok(
            message=f"Loaded core file: {corePath}",
            programOutput=result["program_output"],
            coreOutput=result["core_output"],
            backtraceOutput=result["backtrace_output"],
        )
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_set_breakpoint(sessionId: str, location: str, condition: str | None = None) -> dict[str, Any]:
    """Set breakpoint and optional condition."""
    try:
        result = manager.set_breakpoint(session_id=sessionId, location=location, condition=condition)
        return _ok(
            message=f"Breakpoint set at {location}",
            breakpointOutput=result["breakpoint_output"],
            conditionOutput=result["condition_output"],
        )
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_continue(sessionId: str) -> dict[str, Any]:
    """Continue execution."""
    try:
        output = manager.continue_execution(session_id=sessionId)
        return _ok(message="Execution continued", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_step(sessionId: str, instructions: bool = False) -> dict[str, Any]:
    """Step into next line or instruction."""
    try:
        output = manager.step(session_id=sessionId, instructions=instructions)
        return _ok(message="Step executed", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_next(sessionId: str, instructions: bool = False) -> dict[str, Any]:
    """Step over next line or instruction."""
    try:
        output = manager.next(session_id=sessionId, instructions=instructions)
        return _ok(message="Next executed", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_finish(sessionId: str) -> dict[str, Any]:
    """Run until current function returns."""
    try:
        output = manager.finish(session_id=sessionId)
        return _ok(message="Finish executed", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_backtrace(sessionId: str, full: bool = False, limit: int | None = None) -> dict[str, Any]:
    """Get backtrace from current frame."""
    try:
        output = manager.backtrace(session_id=sessionId, full=full, limit=limit)
        return _ok(message="Backtrace collected", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_print(sessionId: str, expression: str) -> dict[str, Any]:
    """Evaluate expression via GDB print."""
    try:
        output = manager.print_expression(session_id=sessionId, expression=expression)
        return _ok(message=f"Printed expression: {expression}", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_examine(sessionId: str, expression: str, format: str = "x", count: int = 1) -> dict[str, Any]:
    """Examine memory or instructions at an address/expression."""
    try:
        output = manager.examine(session_id=sessionId, expression=expression, fmt=format, count=count)
        return _ok(
            message=f"Examined expression: {expression}",
            output=output,
            format=format,
            count=count,
        )
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_info_registers(sessionId: str, register: str | None = None) -> dict[str, Any]:
    """Print all or selected registers."""
    try:
        output = manager.info_registers(session_id=sessionId, register=register)
        return _ok(message="Register info collected", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_list_source(sessionId: str, location: str | None = None, lineCount: int = 10) -> dict[str, Any]:
    """List source around current frame or requested location."""
    try:
        result = manager.list_source(session_id=sessionId, location=location, line_count=lineCount)
        source_location = result["source_location"]
        source_payload: dict[str, Any] | None = None
        if source_location is not None:
            source_payload = source_location.to_dict()

        return _ok(
            message="Source listed",
            output=result["output"],
            sourceLocation=source_payload,
        )
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


def main() -> None:
    logger.info("Starting gdb-mcp stdio server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

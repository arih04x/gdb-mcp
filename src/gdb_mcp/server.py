"""MCP stdio server exposing GDB operations."""

from __future__ import annotations

import json
import shlex
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


def _normalize_arguments(arguments: list[str] | str | None) -> list[str] | None:
    if arguments is None:
        return None
    if isinstance(arguments, list):
        if not all(isinstance(value, str) for value in arguments):
            raise ValueError("arguments must be a list of strings")
        return arguments
    text = arguments.strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return shlex.split(text)
    if isinstance(parsed, list) and all(isinstance(value, str) for value in parsed):
        return parsed
    if isinstance(parsed, str):
        return shlex.split(parsed)
    if isinstance(parsed, (int, float, bool)):
        return [str(parsed)]
    raise ValueError("string arguments must be shell-like text or a JSON string array/object-free scalar")


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
def gdb_load(sessionId: str, program: str, arguments: list[str] | str | None = None) -> dict[str, Any]:
    """Load a program into GDB."""
    try:
        normalized_args = _normalize_arguments(arguments)
        result = manager.load_program(session_id=sessionId, program=program, arguments=normalized_args)
        return _ok(
            message=f"Program loaded: {result['target']}",
            target=result["target"],
            loadOutput=result["load_output"],
            argsOutput=result["args_output"],
        )
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_set_args(sessionId: str, arguments: list[str] | str) -> dict[str, Any]:
    """Set program arguments for the current target."""
    try:
        normalized_args = _normalize_arguments(arguments)
        if normalized_args is None:
            normalized_args = []
        output = manager.set_program_args(session_id=sessionId, arguments=normalized_args)
        return _ok(message="Program arguments updated", output=output)
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
def gdb_list_breakpoints(sessionId: str) -> dict[str, Any]:
    """List breakpoints/watchpoints in current session."""
    try:
        output = manager.list_breakpoints(session_id=sessionId)
        return _ok(message="Breakpoints listed", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_delete_breakpoints(sessionId: str, breakpointIds: list[int] | None = None) -> dict[str, Any]:
    """Delete all breakpoints or selected breakpoint IDs."""
    try:
        output = manager.delete_breakpoints(session_id=sessionId, breakpoint_ids=breakpointIds)
        return _ok(message="Breakpoints deleted", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_toggle_breakpoints(sessionId: str, breakpointIds: list[int], enabled: bool) -> dict[str, Any]:
    """Enable or disable selected breakpoint IDs."""
    try:
        output = manager.toggle_breakpoints(session_id=sessionId, breakpoint_ids=breakpointIds, enabled=enabled)
        state = "enabled" if enabled else "disabled"
        return _ok(message=f"Breakpoints {state}", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_set_watchpoint(sessionId: str, expression: str, mode: str = "write") -> dict[str, Any]:
    """Set a write/read/access watchpoint on expression."""
    try:
        output = manager.set_watchpoint(session_id=sessionId, expression=expression, mode=mode)
        return _ok(message=f"Watchpoint set ({mode})", output=output)
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
def gdb_info_threads(sessionId: str) -> dict[str, Any]:
    """List threads for current inferior."""
    try:
        output = manager.info_threads(session_id=sessionId)
        return _ok(message="Thread info collected", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_thread_select(sessionId: str, threadId: int) -> dict[str, Any]:
    """Select an active thread."""
    try:
        output = manager.select_thread(session_id=sessionId, thread_id=threadId)
        return _ok(message=f"Selected thread {threadId}", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_frame_select(sessionId: str, frameId: int) -> dict[str, Any]:
    """Select frame by index."""
    try:
        output = manager.select_frame(session_id=sessionId, frame_id=frameId)
        return _ok(message=f"Selected frame {frameId}", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_frame_up(sessionId: str, count: int = 1) -> dict[str, Any]:
    """Move up stack frames."""
    try:
        output = manager.frame_up(session_id=sessionId, count=count)
        return _ok(message=f"Moved up {count} frame(s)", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@mcp.tool()
def gdb_frame_down(sessionId: str, count: int = 1) -> dict[str, Any]:
    """Move down stack frames."""
    try:
        output = manager.frame_down(session_id=sessionId, count=count)
        return _ok(message=f"Moved down {count} frame(s)", output=output)
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


@mcp.tool()
def gdb_collect_crash_report(
    sessionId: str,
    backtraceLimit: int = 20,
    disasmCount: int = 8,
    stackWords: int = 16,
) -> dict[str, Any]:
    """Collect a compact crash report snapshot from current stop point."""
    try:
        report = manager.collect_crash_report(
            session_id=sessionId,
            backtrace_limit=backtraceLimit,
            disasm_count=disasmCount,
            stack_words=stackWords,
        )
        return _ok(message="Crash report collected", report=report)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


def main() -> None:
    logger.info("Starting gdb-mcp stdio server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

"""MCP stdio server exposing GDB operations."""

from __future__ import annotations

import json
import shlex
from typing import Any

from loguru import logger
from mcp.server.fastmcp import FastMCP

from gdb_mcp.exceptions import GdbCommandTimeoutError, GdbSessionError, SessionNotFoundError
from gdb_mcp.gdb_manager import GdbSessionManager, install_signal_cleanup
from gdb_mcp.parsing import parse_backtrace_frames, parse_breakpoints, parse_mi_records, parse_mi_streams, parse_registers
from gdb_mcp.settings import load_server_settings

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
settings = load_server_settings()


def _truncate_payload(value: Any, max_chars: int) -> Any:
    if isinstance(value, str):
        if len(value) <= max_chars:
            return value
        return f"{value[:max_chars]}\n...[truncated]"
    if isinstance(value, dict):
        return {key: _truncate_payload(item, max_chars) for key, item in value.items()}
    if isinstance(value, list):
        return [_truncate_payload(item, max_chars) for item in value]
    return value


def _ok(**payload: Any) -> dict[str, Any]:
    payload = _truncate_payload(payload, settings.max_output_chars)
    payload["ok"] = True
    return payload


def _err(exc: BaseException) -> dict[str, Any]:
    return {
        "ok": False,
        "error": str(exc),
        "error_type": type(exc).__name__,
    }


def _require_advanced(tool_name: str) -> None:
    settings.require_tool(tool_name)


def _advanced_tool(func: Any) -> Any:
    tool_name = getattr(func, "__name__", "")
    if tool_name in settings.advanced_tools and not settings.is_advanced():
        return func
    return mcp.tool()(func)


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
def gdb_get_capabilities() -> dict[str, Any]:
    """Return runtime capability switches and active policy."""
    return _ok(
        mode=settings.mode,
        configPath=settings.config_path,
        maxOutputChars=settings.max_output_chars,
        commandPolicy={
            "mode": settings.command_policy.mode,
            "allowPrefixes": list(settings.command_policy.allow_prefixes),
            "denyPrefixes": list(settings.command_policy.deny_prefixes),
            "dangerousPrefixes": list(settings.command_policy.dangerous_prefixes),
        },
        advancedTools=sorted(settings.advanced_tools),
    )


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
def gdb_command(sessionId: str, command: str) -> dict[str, Any]:
    """Execute an arbitrary GDB command."""
    try:
        settings.validate_command(command)
        output = manager.command(session_id=sessionId, command=command)
        mi_records = parse_mi_records(output)
        mi_streams = parse_mi_streams(output)
        payload: dict[str, Any] = {
            "message": f"Command executed: {command}",
            "miRecords": mi_records,
        }
        if mi_streams:
            payload["miStreams"] = mi_streams
        if not mi_records and not mi_streams:
            payload["output"] = output
        return _ok(**payload)
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


@_advanced_tool
def gdb_attach(sessionId: str, pid: int) -> dict[str, Any]:
    """Attach GDB to a process."""
    try:
        _require_advanced("gdb_attach")
        output = manager.attach(session_id=sessionId, pid=pid)
        return _ok(message=f"Attached to process: {pid}", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@_advanced_tool
def gdb_load_core(sessionId: str, program: str, corePath: str) -> dict[str, Any]:
    """Load executable and core file into GDB."""
    try:
        _require_advanced("gdb_load_core")
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
        breakpoints = parse_breakpoints(output)
        payload: dict[str, Any] = {
            "message": "Breakpoints listed",
            "breakpoints": breakpoints,
        }
        if not breakpoints:
            payload["output"] = output
        return _ok(**payload)
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


@_advanced_tool
def gdb_set_watchpoint(sessionId: str, expression: str, mode: str = "write") -> dict[str, Any]:
    """Set a write/read/access watchpoint on expression."""
    try:
        _require_advanced("gdb_set_watchpoint")
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
def gdb_backtrace(sessionId: str, full: bool = False, limit: int | None = None) -> dict[str, Any]:
    """Get backtrace from current frame."""
    try:
        output = manager.backtrace(session_id=sessionId, full=full, limit=limit)
        frames = parse_backtrace_frames(output)
        payload: dict[str, Any] = {
            "message": "Backtrace collected",
            "frames": frames,
        }
        if not frames:
            payload["output"] = output
        return _ok(**payload)
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
        registers = parse_registers(output)
        payload: dict[str, Any] = {
            "message": "Register info collected",
            "registers": registers,
        }
        if not registers:
            payload["output"] = output
        return _ok(**payload)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@_advanced_tool
def gdb_info_threads(sessionId: str) -> dict[str, Any]:
    """List threads for current inferior."""
    try:
        _require_advanced("gdb_info_threads")
        output = manager.info_threads(session_id=sessionId)
        return _ok(message="Thread info collected", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@_advanced_tool
def gdb_thread_select(sessionId: str, threadId: int) -> dict[str, Any]:
    """Select an active thread."""
    try:
        _require_advanced("gdb_thread_select")
        output = manager.select_thread(session_id=sessionId, thread_id=threadId)
        return _ok(message=f"Selected thread {threadId}", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@_advanced_tool
def gdb_frame_select(sessionId: str, frameId: int) -> dict[str, Any]:
    """Select frame by index."""
    try:
        _require_advanced("gdb_frame_select")
        output = manager.select_frame(session_id=sessionId, frame_id=frameId)
        return _ok(message=f"Selected frame {frameId}", output=output)
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


@_advanced_tool
def gdb_collect_crash_report(
    sessionId: str,
    backtraceLimit: int = 20,
    disasmCount: int = 8,
    stackWords: int = 16,
) -> dict[str, Any]:
    """Collect a compact crash report snapshot from current stop point."""
    try:
        _require_advanced("gdb_collect_crash_report")
        report = manager.collect_crash_report(
            session_id=sessionId,
            backtrace_limit=backtraceLimit,
            disasm_count=disasmCount,
            stack_words=stackWords,
        )
        frames = parse_backtrace_frames(report.get("backtrace", ""))
        registers = parse_registers(report.get("registers", ""))
        compact_report = {key: value for key, value in report.items() if key not in {"backtrace", "registers"}}
        if not frames and "backtrace" in report:
            compact_report["backtrace"] = report["backtrace"]
        if not registers and "registers" in report:
            compact_report["registers"] = report["registers"]
        return _ok(
            message="Crash report collected",
            report=compact_report,
            frames=frames,
            registers=registers,
        )
    except RECOVERABLE_ERRORS as exc:
        return _err(exc)


def main() -> None:
    logger.info(
        "Starting gdb-mcp stdio server (mode={}, config={})",
        settings.mode,
        settings.config_path,
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

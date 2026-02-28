"""Session manager and high-level gdb operations."""

from __future__ import annotations

import atexit
import os
import shlex
import signal
import uuid
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from gdb_mcp.exceptions import GdbSessionError, SessionNotFoundError
from gdb_mcp.gdb_session import GdbSession
from gdb_mcp.parsing import extract_line_range, parse_info_line, parse_info_source


@dataclass
class SourceLocation:
    file_path: str
    line_start: int
    line_end: int
    current_line: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "current_line": self.current_line,
            "vscode_uri": f"vscode://file{self.file_path}:{self.line_start}",
        }


def format_program_arguments(arguments: list[str]) -> str:
    return " ".join(shlex.quote(value) for value in arguments)


class GdbSessionManager:
    """Store and operate on active gdb sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, GdbSession] = {}
        atexit.register(self.terminate_all)

    def _resolve_gdb_path(self, gdb_path: str) -> str:
        if os.path.sep in gdb_path:
            candidate = Path(gdb_path).expanduser().resolve()
            if not candidate.exists():
                raise FileNotFoundError(f"gdb executable not found: {candidate}")
            return str(candidate)

        from shutil import which

        resolved = which(gdb_path)
        if resolved is None:
            raise FileNotFoundError(f"gdb executable not found in PATH: {gdb_path}")
        return resolved

    def _get_session(self, session_id: str) -> GdbSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(f"No active GDB session with ID: {session_id}")
        return session

    def start_session(self, gdb_path: str = "gdb", working_dir: str | None = None) -> dict[str, str]:
        resolved_gdb = self._resolve_gdb_path(gdb_path)
        cwd = Path(working_dir or os.getcwd()).expanduser().resolve()
        if not cwd.exists() or not cwd.is_dir():
            raise FileNotFoundError(f"Working directory does not exist: {cwd}")

        session_id = uuid.uuid4().hex[:12]
        session = GdbSession.start(session_id=session_id, gdb_path=resolved_gdb, working_dir=cwd)
        self._sessions[session_id] = session
        logger.info("Started session {}", session_id)
        return {
            "session_id": session_id,
            "working_dir": str(cwd),
            "gdb_path": resolved_gdb,
            "output": session.startup_output,
        }

    def list_sessions(self) -> list[dict[str, str]]:
        return [session.to_dict() for session in self._sessions.values()]

    def terminate_session(self, session_id: str) -> None:
        session = self._get_session(session_id)
        session.terminate()
        self._sessions.pop(session_id, None)
        logger.info("Session {} removed", session_id)

    def terminate_all(self) -> None:
        session_ids = list(self._sessions.keys())
        for session_id in session_ids:
            try:
                self.terminate_session(session_id)
            except (GdbSessionError, OSError, ValueError):
                logger.warning("Failed terminating session {}", session_id)

    def command(self, session_id: str, command: str, timeout: float = 10.0) -> str:
        session = self._get_session(session_id)
        return session.execute(command, timeout=timeout)

    @staticmethod
    def _validate_positive_int(value: int, field_name: str) -> None:
        if not isinstance(value, int):
            raise ValueError(f"{field_name} must be an integer")
        if value <= 0:
            raise ValueError(f"{field_name} must be > 0")

    @classmethod
    def _format_number_list(cls, values: list[int], field_name: str) -> str:
        if not values:
            raise ValueError(f"{field_name} must not be empty")
        for value in values:
            cls._validate_positive_int(value, field_name)
        return " ".join(str(value) for value in values)

    def load_program(self, session_id: str, program: str, arguments: list[str] | None = None) -> dict[str, str]:
        session = self._get_session(session_id)
        target_path = Path(program)
        if not target_path.is_absolute():
            target_path = (session.working_dir / target_path).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Program path does not exist: {target_path}")

        load_output = session.execute(f'file "{target_path}"')
        args_output = ""
        if arguments is not None:
            args_output = self.set_program_args(session_id=session_id, arguments=arguments)

        session.target = str(target_path)
        return {"target": str(target_path), "load_output": load_output, "args_output": args_output}

    def set_program_args(self, session_id: str, arguments: list[str]) -> str:
        session = self._get_session(session_id)
        for argument in arguments:
            if not isinstance(argument, str):
                raise ValueError("arguments must be a list of strings")
        if not arguments:
            return session.execute("set args")
        return session.execute(f"set args {format_program_arguments(arguments)}")

    def attach(self, session_id: str, pid: int) -> str:
        return self.command(session_id, f"attach {pid}")

    def load_core(self, session_id: str, program: str, core_path: str) -> dict[str, str]:
        session = self._get_session(session_id)
        program_out = session.execute(f'file "{program}"')
        core_out = session.execute(f'core-file "{core_path}"')
        bt_out = session.execute("backtrace")
        return {"program_output": program_out, "core_output": core_out, "backtrace_output": bt_out}

    def set_breakpoint(self, session_id: str, location: str, condition: str | None = None) -> dict[str, str]:
        session = self._get_session(session_id)
        breakpoint_output = session.execute(f"break {location}")

        condition_output = ""
        if condition:
            import re

            match = re.search(r"Breakpoint\s+(\d+)", breakpoint_output)
            if match:
                bp_num = match.group(1)
                condition_output = session.execute(f"condition {bp_num} {condition}")

        return {
            "breakpoint_output": breakpoint_output,
            "condition_output": condition_output,
        }

    def list_breakpoints(self, session_id: str) -> str:
        return self.command(session_id, "info breakpoints")

    def delete_breakpoints(self, session_id: str, breakpoint_ids: list[int] | None = None) -> str:
        if breakpoint_ids is None:
            return self.command(session_id, "delete")
        formatted_ids = self._format_number_list(breakpoint_ids, "breakpoint_ids")
        return self.command(session_id, f"delete {formatted_ids}")

    def toggle_breakpoints(self, session_id: str, breakpoint_ids: list[int], enabled: bool) -> str:
        formatted_ids = self._format_number_list(breakpoint_ids, "breakpoint_ids")
        toggle_command = "enable" if enabled else "disable"
        return self.command(session_id, f"{toggle_command} {formatted_ids}")

    def set_watchpoint(self, session_id: str, expression: str, mode: str = "write") -> str:
        if not expression.strip():
            raise ValueError("expression must not be empty")
        mode_to_command = {
            "write": "watch",
            "read": "rwatch",
            "access": "awatch",
        }
        command = mode_to_command.get(mode)
        if command is None:
            raise ValueError("mode must be one of: write, read, access")
        return self.command(session_id, f"{command} {expression}")

    def continue_execution(self, session_id: str) -> str:
        return self.command(session_id, "continue")

    def step(self, session_id: str, instructions: bool = False) -> str:
        return self.command(session_id, "stepi" if instructions else "step")

    def next(self, session_id: str, instructions: bool = False) -> str:
        return self.command(session_id, "nexti" if instructions else "next")

    def finish(self, session_id: str) -> str:
        return self.command(session_id, "finish")

    def backtrace(self, session_id: str, full: bool = False, limit: int | None = None) -> str:
        command = "backtrace full" if full else "backtrace"
        if limit is not None:
            command = f"{command} {limit}"
        return self.command(session_id, command)

    def print_expression(self, session_id: str, expression: str) -> str:
        return self.command(session_id, f"print {expression}")

    def examine(self, session_id: str, expression: str, fmt: str = "x", count: int = 1) -> str:
        return self.command(session_id, f"x/{count}{fmt} {expression}")

    def info_registers(self, session_id: str, register: str | None = None) -> str:
        command = "info registers"
        if register:
            command = f"{command} {register}"
        return self.command(session_id, command)

    def info_threads(self, session_id: str) -> str:
        return self.command(session_id, "info threads")

    def select_thread(self, session_id: str, thread_id: int) -> str:
        self._validate_positive_int(thread_id, "thread_id")
        return self.command(session_id, f"thread {thread_id}")

    def select_frame(self, session_id: str, frame_id: int) -> str:
        if not isinstance(frame_id, int):
            raise ValueError("frame_id must be an integer")
        if frame_id < 0:
            raise ValueError("frame_id must be >= 0")
        return self.command(session_id, f"frame {frame_id}")

    def frame_up(self, session_id: str, count: int = 1) -> str:
        self._validate_positive_int(count, "count")
        return self.command(session_id, f"up {count}")

    def frame_down(self, session_id: str, count: int = 1) -> str:
        self._validate_positive_int(count, "count")
        return self.command(session_id, f"down {count}")

    def list_source(self, session_id: str, location: str | None = None, line_count: int = 10) -> dict[str, str | SourceLocation | None]:
        session = self._get_session(session_id)
        if line_count <= 0:
            raise ValueError("line_count must be > 0")

        session.execute(f"set listsize {line_count}")
        command = f"list {location}" if location else "list"
        output = session.execute(command)

        source_location = self._parse_source_location(session, output)
        return {
            "output": output,
            "source_location": source_location,
        }

    def _parse_source_location(self, session: GdbSession, list_output: str) -> SourceLocation | None:
        line_range = extract_line_range(list_output)
        if line_range is None:
            return None

        line_start, line_end = line_range
        info_line_output = session.execute("info line")
        info = parse_info_line(info_line_output)

        file_path = ""
        current_line = 0
        if info is not None:
            file_path, current_line = info
        else:
            info_source_output = session.execute("info source")
            source = parse_info_source(info_source_output)
            if source:
                file_path = source

        if not file_path:
            return None

        if not Path(file_path).is_absolute():
            file_path = str((session.working_dir / file_path).resolve())

        return SourceLocation(
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            current_line=current_line,
        )

    def collect_crash_report(
        self,
        session_id: str,
        backtrace_limit: int = 20,
        disasm_count: int = 8,
        stack_words: int = 16,
    ) -> dict[str, str]:
        self._validate_positive_int(backtrace_limit, "backtrace_limit")
        self._validate_positive_int(disasm_count, "disasm_count")
        self._validate_positive_int(stack_words, "stack_words")

        session = self._get_session(session_id)
        commands = {
            "program_info": "info program",
            "current_frame": "frame",
            "thread_info": "info threads",
            "backtrace": f"backtrace {backtrace_limit}",
            "registers": "info registers",
            "pc_disassembly": f"x/{disasm_count}i $pc",
            "stack_memory": f"x/{stack_words}gx $sp",
        }
        report: dict[str, str] = {}
        for key, command in commands.items():
            try:
                report[key] = session.execute(command)
            except (GdbSessionError, ValueError, OSError) as exc:
                report[key] = f"[error] {type(exc).__name__}: {exc}"
        return report


def install_signal_cleanup(manager: GdbSessionManager) -> None:
    def _cleanup_handler(signum: int, _frame: object) -> None:
        logger.info("Received signal {}, terminating all sessions", signum)
        manager.terminate_all()

    signal.signal(signal.SIGINT, _cleanup_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _cleanup_handler)

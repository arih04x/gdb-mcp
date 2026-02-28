"""Low-level GDB process session wrapper."""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pexpect
from loguru import logger

from gdb_mcp.exceptions import GdbCommandTimeoutError, GdbSessionError


_ANSI_ESCAPE_RE = re.compile(
    r"""
    \x1B
    (?:
        \[[0-?]*[ -/]*[@-~]   # CSI sequence
        |\][^\x07\x1B]*(?:\x07|\x1B\\)  # OSC sequence
        |[@-Z\\-_]            # 2-char sequence
    )
    """,
    re.VERBOSE,
)


_SESSION_BOOTSTRAP_COMMANDS: tuple[str, ...] = (
    "set pagination off",
    "set confirm off",
    "set style enabled off",
    "set print thread-events off",
)


def _strip_terminal_escapes(raw: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", raw)


def _normalize_output(raw: str) -> str:
    text = _strip_terminal_escapes(raw)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


@dataclass
class GdbSession:
    """An interactive GDB CLI session."""

    session_id: str
    gdb_path: str
    working_dir: Path
    child: pexpect.spawn
    startup_output: str
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    target: str | None = None
    _lock: threading.RLock = field(default_factory=threading.RLock)

    @classmethod
    def start(
        cls,
        session_id: str,
        gdb_path: str,
        working_dir: Path,
        startup_timeout: float = 10.0,
    ) -> "GdbSession":
        logger.info("Starting gdb session: id={}, gdb={}, cwd={}", session_id, gdb_path, working_dir)
        env = dict(os.environ)
        env["TERM"] = "dumb"
        child = pexpect.spawn(
            gdb_path,
            args=["--quiet", "--nx"],
            cwd=str(working_dir),
            encoding="utf-8",
            echo=False,
            timeout=startup_timeout,
            env=env,
        )

        try:
            child.expect_exact("(gdb)")
            _apply_bootstrap_commands(child, timeout=startup_timeout)
        except pexpect.TIMEOUT as exc:
            child.close(force=True)
            raise GdbCommandTimeoutError("Timed out waiting for gdb prompt during startup") from exc
        except pexpect.EOF as exc:
            child.close(force=True)
            raise GdbSessionError("gdb exited before initial prompt") from exc

        startup_output = _normalize_output(child.before or "")
        return cls(
            session_id=session_id,
            gdb_path=gdb_path,
            working_dir=working_dir,
            child=child,
            startup_output=startup_output,
        )

    def is_alive(self) -> bool:
        return self.child.isalive()

    def execute(self, command: str, timeout: float = 10.0) -> str:
        """Execute one CLI command and collect output until the next gdb prompt."""
        with self._lock:
            if not self.child.isalive():
                raise GdbSessionError(f"GDB session {self.session_id} is not alive")

            logger.debug("Session {} command: {}", self.session_id, command)
            self.child.sendline(command)

            try:
                self.child.expect_exact("(gdb)", timeout=timeout)
            except pexpect.TIMEOUT as exc:
                partial = _normalize_output(self.child.before or "")
                raise GdbCommandTimeoutError(
                    f"Command timeout after {timeout}s for `{command}`. Partial output:\n{partial}"
                ) from exc
            except pexpect.EOF as exc:
                partial = _normalize_output(self.child.before or "")
                raise GdbSessionError(
                    f"gdb session terminated while executing `{command}`. Partial output:\n{partial}"
                ) from exc

            output = _normalize_output(self.child.before or "")
            lines = output.splitlines()
            if lines and lines[0].strip() == command.strip():
                lines = lines[1:]
            return "\n".join(lines).strip()

    def terminate(self, timeout: float = 5.0) -> None:
        with self._lock:
            if not self.child.isalive():
                return

            logger.info("Terminating gdb session: {}", self.session_id)
            try:
                self.child.sendline("quit")
                idx = self.child.expect_exact(["Quit anyway? (y or n)", pexpect.EOF], timeout=timeout)
                if idx == 0:
                    self.child.sendline("y")
                    self.child.expect(pexpect.EOF, timeout=timeout)
            except pexpect.TIMEOUT:
                logger.warning("Session {} quit timeout, force closing", self.session_id)
            except pexpect.EOF:
                pass
            finally:
                self.child.close(force=True)

    def to_dict(self) -> dict[str, str]:
        started_at = self.started_at.isoformat().replace("+00:00", "Z")
        return {
            "id": self.session_id,
            "target": self.target or "No program loaded",
            "working_dir": str(self.working_dir),
            "gdb_path": self.gdb_path,
            "started_at": started_at,
        }


def _apply_bootstrap_commands(child: pexpect.spawn, timeout: float) -> None:
    for command in _SESSION_BOOTSTRAP_COMMANDS:
        child.sendline(command)
        child.expect_exact("(gdb)", timeout=timeout)

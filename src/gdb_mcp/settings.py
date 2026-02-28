"""Runtime configuration for gdb-mcp server."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ADVANCED_TOOLS: tuple[str, ...] = (
    "gdb_attach",
    "gdb_load_core",
    "gdb_set_watchpoint",
    "gdb_info_threads",
    "gdb_thread_select",
    "gdb_frame_select",
    "gdb_collect_crash_report",
)

DEFAULT_COMMAND_ALLOW_PREFIXES: tuple[str, ...] = ()
DEFAULT_COMMAND_DENY_PREFIXES: tuple[str, ...] = (
    "shell",
    "!",
    "python",
    "pi",
    "source",
    "define",
    "document",
)
DEFAULT_COMMAND_DANGEROUS_PREFIXES: tuple[str, ...] = (
    "call",
    "jump",
    "return",
    "signal",
    "set {",
    "set *",
)


@dataclass(frozen=True)
class CommandPolicy:
    mode: str
    allow_prefixes: tuple[str, ...]
    deny_prefixes: tuple[str, ...]
    dangerous_prefixes: tuple[str, ...]

    def validate(self, command: str) -> None:
        normalized = command.strip().lower()
        if not normalized:
            raise ValueError("command must not be empty")

        if self.mode == "allowlist":
            if not any(normalized.startswith(prefix) for prefix in self.allow_prefixes):
                raise PermissionError(
                    f"command blocked by allowlist policy: {command!r}. "
                    f"Allowed prefixes: {', '.join(self.allow_prefixes)}"
                )
        elif self.mode == "denylist":
            if any(normalized.startswith(prefix) for prefix in self.deny_prefixes):
                raise PermissionError(f"command blocked by denylist policy: {command!r}")
        elif self.mode != "none":
            raise ValueError(f"invalid command policy mode: {self.mode}")

        if any(normalized.startswith(prefix) for prefix in self.dangerous_prefixes):
            raise PermissionError(
                f"dangerous command is disabled by policy: {command!r}"
            )


@dataclass(frozen=True)
class ServerSettings:
    mode: str
    max_output_chars: int
    advanced_tools: frozenset[str]
    command_policy: CommandPolicy
    config_path: str

    def is_advanced(self) -> bool:
        return self.mode == "advanced"

    def require_tool(self, tool_name: str) -> None:
        if tool_name in self.advanced_tools and not self.is_advanced():
            raise PermissionError(
                f"{tool_name} requires advanced mode (current mode: {self.mode}). "
                "Set mode=advanced in config.json or GDB_MODE=advanced."
            )

    def validate_command(self, command: str) -> None:
        self.command_policy.validate(command)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_config_path() -> Path:
    configured = os.getenv("GDB_MCP_CONFIG")
    if not configured:
        return _project_root() / "config.json"

    candidate = Path(configured).expanduser()
    if candidate.is_absolute():
        return candidate

    cwd_candidate = (Path.cwd() / candidate).resolve()
    if cwd_candidate.exists():
        return cwd_candidate

    root_candidate = (_project_root() / candidate).resolve()
    if root_candidate.exists():
        return root_candidate
    return cwd_candidate


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("config root must be a JSON object")
    return parsed


def _read_string_list(raw: object, field_name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    if raw is None:
        return default
    if not isinstance(raw, list):
        raise ValueError(f"{field_name} must be a list")
    values: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            raise ValueError(f"{field_name} items must be strings")
        stripped = item.strip().lower()
        if stripped:
            values.append(stripped)
    return tuple(values)


def load_server_settings() -> ServerSettings:
    path = _resolve_config_path()
    config = _load_json(path)

    mode = str(config.get("mode", "default")).strip().lower()
    if mode not in {"default", "advanced"}:
        raise ValueError("mode must be either 'default' or 'advanced'")

    max_output_chars = int(config.get("max_output_chars", 20000))
    if max_output_chars <= 0:
        raise ValueError("max_output_chars must be > 0")

    advanced_tools = frozenset(
        _read_string_list(config.get("advanced_tools"), "advanced_tools", DEFAULT_ADVANCED_TOOLS)
    )

    command_config = config.get("command_policy")
    if command_config is not None and not isinstance(command_config, dict):
        raise ValueError("command_policy must be a JSON object")
    command_config_obj = command_config if isinstance(command_config, dict) else {}

    command_mode = str(command_config_obj.get("mode", "denylist")).strip().lower()
    allow_prefixes = _read_string_list(
        command_config_obj.get("allow_prefixes"),
        "command_policy.allow_prefixes",
        DEFAULT_COMMAND_ALLOW_PREFIXES,
    )
    deny_prefixes = _read_string_list(
        command_config_obj.get("deny_prefixes"),
        "command_policy.deny_prefixes",
        DEFAULT_COMMAND_DENY_PREFIXES,
    )
    dangerous_prefixes = _read_string_list(
        command_config_obj.get("dangerous_prefixes"),
        "command_policy.dangerous_prefixes",
        DEFAULT_COMMAND_DANGEROUS_PREFIXES,
    )

    if env_mode := (os.getenv("GDB_MODE") or os.getenv("GDB_MCP_MODE")):
        mode = env_mode.strip().lower()
        if mode not in {"default", "advanced"}:
            raise ValueError("GDB_MODE must be either 'default' or 'advanced'")

    if env_max_output := os.getenv("GDB_MCP_MAX_OUTPUT_CHARS"):
        max_output_chars = int(env_max_output)
        if max_output_chars <= 0:
            raise ValueError("GDB_MCP_MAX_OUTPUT_CHARS must be > 0")

    policy = CommandPolicy(
        mode=command_mode,
        allow_prefixes=allow_prefixes,
        deny_prefixes=deny_prefixes,
        dangerous_prefixes=dangerous_prefixes,
    )
    return ServerSettings(
        mode=mode,
        max_output_chars=max_output_chars,
        advanced_tools=advanced_tools,
        command_policy=policy,
        config_path=str(path),
    )

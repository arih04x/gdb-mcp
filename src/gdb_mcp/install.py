"""Installer utilities for MCP client configuration."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import tomli_w
from loguru import logger

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


@dataclass(frozen=True)
class InstallTarget:
    name: str
    path: Path
    fmt: str
    key_path: tuple[str, ...]


def _target_json(name: str, config_dir: Path, config_file: str, key_path: tuple[str, ...] = ("mcpServers",)) -> InstallTarget:
    return InstallTarget(name=name, path=config_dir / config_file, fmt="json", key_path=key_path)


def _target_toml(name: str, config_dir: Path, config_file: str, key_path: tuple[str, ...] = ("mcp_servers",)) -> InstallTarget:
    return InstallTarget(name=name, path=config_dir / config_file, fmt="toml", key_path=key_path)


def get_python_executable() -> str:
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        candidate = Path(venv) / ("Scripts" if sys.platform == "win32" else "bin") / (
            "python.exe" if sys.platform == "win32" else "python3"
        )
        if candidate.exists():
            return str(candidate)
    return sys.executable


def generate_stdio_config() -> dict[str, object]:
    return {
        "command": get_python_executable(),
        "args": ["-m", "gdb_mcp.server"],
    }


def get_install_targets() -> list[InstallTarget]:
    home = Path.home()
    if sys.platform == "win32":
        appdata = Path(os.getenv("APPDATA", ""))
        return [
            _target_json("Cline", appdata / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings", "cline_mcp_settings.json"),
            _target_json("Roo Code", appdata / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings", "mcp_settings.json"),
            _target_json("Kilo Code", appdata / "Code" / "User" / "globalStorage" / "kilocode.kilo-code" / "settings", "mcp_settings.json"),
            _target_json("Claude", appdata / "Claude", "claude_desktop_config.json"),
            _target_json("Cursor", home / ".cursor", "mcp.json"),
            _target_json("Windsurf", home / ".codeium" / "windsurf", "mcp_config.json"),
            _target_json("Claude Code", home, ".claude.json"),
            _target_json("LM Studio", home / ".lmstudio", "mcp.json"),
            _target_toml("Codex", home / ".codex", "config.toml"),
            _target_json("Zed", appdata / "Zed", "settings.json"),
            _target_json("Gemini CLI", home / ".gemini", "settings.json"),
            _target_json("Qwen Coder", home / ".qwen", "settings.json"),
            _target_json("Copilot CLI", home / ".copilot", "mcp-config.json"),
            _target_json("Crush", home, "crush.json"),
            _target_json("Augment Code", appdata / "Code" / "User", "settings.json"),
            _target_json("Qodo Gen", appdata / "Code" / "User", "settings.json"),
            _target_json("Antigravity IDE", home / ".gemini" / "antigravity", "mcp_config.json"),
            _target_json("Warp", home / ".warp", "mcp_config.json"),
            _target_json("Amazon Q", home / ".aws" / "amazonq", "mcp_config.json"),
            _target_json("Opencode", home / ".opencode", "mcp_config.json"),
            _target_json("Kiro", home / ".kiro", "mcp_config.json"),
            _target_json("Trae", home / ".trae", "mcp_config.json"),
            _target_json("VS Code", appdata / "Code" / "User", "settings.json", ("mcp", "servers")),
        ]

    if sys.platform == "darwin":
        return [
            _target_json(
                "Cline",
                home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings",
                "cline_mcp_settings.json",
            ),
            _target_json(
                "Roo Code",
                home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings",
                "mcp_settings.json",
            ),
            _target_json(
                "Kilo Code",
                home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "kilocode.kilo-code" / "settings",
                "mcp_settings.json",
            ),
            _target_json("Claude", home / "Library" / "Application Support" / "Claude", "claude_desktop_config.json"),
            _target_json("Cursor", home / ".cursor", "mcp.json"),
            _target_json("Windsurf", home / ".codeium" / "windsurf", "mcp_config.json"),
            _target_json("Claude Code", home, ".claude.json"),
            _target_json("LM Studio", home / ".lmstudio", "mcp.json"),
            _target_toml("Codex", home / ".codex", "config.toml"),
            _target_json("Antigravity IDE", home / ".gemini" / "antigravity", "mcp_config.json"),
            _target_json("Zed", home / "Library" / "Application Support" / "Zed", "settings.json"),
            _target_json("Gemini CLI", home / ".gemini", "settings.json"),
            _target_json("Qwen Coder", home / ".qwen", "settings.json"),
            _target_json("Copilot CLI", home / ".copilot", "mcp-config.json"),
            _target_json("Crush", home, "crush.json"),
            _target_json("Augment Code", home / "Library" / "Application Support" / "Code" / "User", "settings.json"),
            _target_json("Qodo Gen", home / "Library" / "Application Support" / "Code" / "User", "settings.json"),
            _target_json("BoltAI", home / "Library" / "Application Support" / "BoltAI", "config.json"),
            _target_json("Perplexity", home / "Library" / "Application Support" / "Perplexity", "mcp_config.json"),
            _target_json("Warp", home / ".warp", "mcp_config.json"),
            _target_json("Amazon Q", home / ".aws" / "amazonq", "mcp_config.json"),
            _target_json("Opencode", home / ".opencode", "mcp_config.json"),
            _target_json("Kiro", home / ".kiro", "mcp_config.json"),
            _target_json("Trae", home / ".trae", "mcp_config.json"),
            _target_json("VS Code", home / "Library" / "Application Support" / "Code" / "User", "settings.json", ("mcp", "servers")),
        ]

    if sys.platform == "linux":
        return [
            _target_json("Cline", home / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings", "cline_mcp_settings.json"),
            _target_json("Roo Code", home / ".config" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings", "mcp_settings.json"),
            _target_json("Kilo Code", home / ".config" / "Code" / "User" / "globalStorage" / "kilocode.kilo-code" / "settings", "mcp_settings.json"),
            _target_json("Cursor", home / ".cursor", "mcp.json"),
            _target_json("Windsurf", home / ".codeium" / "windsurf", "mcp_config.json"),
            _target_json("Claude Code", home, ".claude.json"),
            _target_json("LM Studio", home / ".lmstudio", "mcp.json"),
            _target_toml("Codex", home / ".codex", "config.toml"),
            _target_json("Antigravity IDE", home / ".gemini" / "antigravity", "mcp_config.json"),
            _target_json("Zed", home / ".config" / "zed", "settings.json"),
            _target_json("Gemini CLI", home / ".gemini", "settings.json"),
            _target_json("Qwen Coder", home / ".qwen", "settings.json"),
            _target_json("Copilot CLI", home / ".copilot", "mcp-config.json"),
            _target_json("Crush", home, "crush.json"),
            _target_json("Augment Code", home / ".config" / "Code" / "User", "settings.json"),
            _target_json("Qodo Gen", home / ".config" / "Code" / "User", "settings.json"),
            _target_json("Warp", home / ".warp", "mcp_config.json"),
            _target_json("Amazon Q", home / ".aws" / "amazonq", "mcp_config.json"),
            _target_json("Opencode", home / ".opencode", "mcp_config.json"),
            _target_json("Kiro", home / ".kiro", "mcp_config.json"),
            _target_json("Trae", home / ".trae", "mcp_config.json"),
            _target_json("VS Code", home / ".config" / "Code" / "User", "settings.json", ("mcp", "servers")),
        ]

    return [
        _target_toml("Codex", home / ".codex", "config.toml"),
    ]


def select_install_targets(clients: list[str] | None = None) -> list[InstallTarget]:
    targets = get_install_targets()
    if not clients:
        return targets

    requested = {name.strip().lower() for name in clients if name.strip()}
    valid = {target.name.lower(): target for target in targets}
    unknown = sorted(name for name in requested if name not in valid)
    if unknown:
        valid_list = ", ".join(sorted(target.name for target in targets))
        raise ValueError(f"Unknown client(s): {', '.join(unknown)}. Valid: {valid_list}")

    ordered_selected: list[InstallTarget] = []
    for target in targets:
        if target.name.lower() in requested:
            ordered_selected.append(target)
    return ordered_selected


def _load_config(path: Path, fmt: str) -> dict[str, object]:
    if not path.exists():
        return {}

    if fmt == "toml":
        raw = path.read_bytes()
        if not raw:
            return {}
        return tomllib.loads(raw.decode("utf-8"))

    raw_text = path.read_text(encoding="utf-8")
    if not raw_text.strip():
        return {}
    return json.loads(raw_text)


def _dump_config(path: Path, fmt: str, config: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".toml" if fmt == "toml" else ".json"

    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=suffix, dir=str(path.parent), text=True)
    tmp = Path(tmp_path)
    try:
        if fmt == "toml":
            with os.fdopen(fd, "wb") as handle:
                handle.write(tomli_w.dumps(config).encode("utf-8"))
        else:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=2)
        os.replace(tmp, path)
    except (OSError, TypeError, ValueError):
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


def _ensure_nested_dict(config: dict[str, object], key_path: tuple[str, ...]) -> dict[str, object]:
    cursor: dict[str, object] = config
    for key in key_path:
        value = cursor.get(key)
        if value is None:
            next_cursor: dict[str, object] = {}
            cursor[key] = next_cursor
            cursor = next_cursor
            continue
        if not isinstance(value, dict):
            raise ValueError(f"Config key {'.'.join(key_path)} exists but is not an object")
        cursor = value
    return cursor


def update_mcp_config(config: dict[str, object], key_path: tuple[str, ...], server_name: str, uninstall: bool) -> bool:
    servers = _ensure_nested_dict(config, key_path)
    if uninstall:
        if server_name in servers:
            del servers[server_name]
            return True
        return False

    servers[server_name] = generate_stdio_config()
    return True


def detect_environment() -> dict[str, object]:
    from shutil import which

    targets = get_install_targets()
    available_targets = [target for target in targets if target.path.parent.exists()]

    return {
        "python": get_python_executable(),
        "gdb": which("gdb"),
        "uv": which("uv"),
        "platform": sys.platform,
        "available_clients": [target.name for target in available_targets],
    }


def install_mcp_servers(
    server_name: str = "gdb",
    quiet: bool = False,
    clients: list[str] | None = None,
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for target in select_install_targets(clients):
        if not target.path.parent.exists():
            results.append({"client": target.name, "status": "skipped", "reason": "config dir not found"})
            continue

        try:
            config = _load_config(target.path, target.fmt)
            changed = update_mcp_config(config, target.key_path, server_name=server_name, uninstall=False)
            if changed:
                _dump_config(target.path, target.fmt, config)
            status = "installed" if changed else "unchanged"
            results.append({"client": target.name, "status": status, "path": str(target.path)})
            if not quiet:
                logger.info("{} -> {} ({})", target.name, status, target.path)
        except (json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
            results.append({"client": target.name, "status": "failed", "reason": f"invalid config: {exc}"})
        except (OSError, ValueError, TypeError) as exc:
            results.append({"client": target.name, "status": "failed", "reason": str(exc)})
    return results


def uninstall_mcp_servers(
    server_name: str = "gdb",
    quiet: bool = False,
    clients: list[str] | None = None,
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for target in select_install_targets(clients):
        if not target.path.exists():
            results.append({"client": target.name, "status": "skipped", "reason": "config file not found"})
            continue

        try:
            config = _load_config(target.path, target.fmt)
            changed = update_mcp_config(config, target.key_path, server_name=server_name, uninstall=True)
            if changed:
                _dump_config(target.path, target.fmt, config)
            status = "uninstalled" if changed else "not-installed"
            results.append({"client": target.name, "status": status, "path": str(target.path)})
            if not quiet:
                logger.info("{} -> {} ({})", target.name, status, target.path)
        except (json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
            results.append({"client": target.name, "status": "failed", "reason": f"invalid config: {exc}"})
        except (OSError, ValueError, TypeError) as exc:
            results.append({"client": target.name, "status": "failed", "reason": str(exc)})
    return results


def render_manual_config(server_name: str = "gdb") -> str:
    json_payload = {"mcpServers": {server_name: generate_stdio_config()}}
    toml_payload = {"mcp_servers": {server_name: generate_stdio_config()}}
    return (
        "[JSON config]\n"
        + json.dumps(json_payload, indent=2)
        + "\n\n[TOML config]\n"
        + tomli_w.dumps(toml_payload)
    )

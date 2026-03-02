"""Command-line entrypoint for gdb-mcp."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from shutil import which
import sys

from loguru import logger

from gdb_mcp.install import (
    detect_environment,
    install_mcp_servers,
    render_manual_config,
    uninstall_mcp_servers,
)
from gdb_mcp.settings import load_server_settings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gdb-mcp", description="GDB MCP server and installer")
    subparsers = parser.add_subparsers(dest="command")

    install = subparsers.add_parser("install", help="Check environment and install MCP config")
    install.add_argument("--server-name", default="gdb", help="Server name used in MCP config")
    install.add_argument("--quiet", action="store_true", help="Reduce install output")
    install.add_argument(
        "--client",
        action="append",
        default=[],
        help="Install only selected client(s), e.g. --client Codex",
    )

    uninstall = subparsers.add_parser("uninstall", help="Remove MCP config from detected clients")
    uninstall.add_argument("--server-name", default="gdb", help="Server name used in MCP config")
    uninstall.add_argument("--quiet", action="store_true", help="Reduce uninstall output")
    uninstall.add_argument(
        "--client",
        action="append",
        default=[],
        help="Uninstall only selected client(s), e.g. --client Codex",
    )

    config = subparsers.add_parser("config", help="Print manual MCP config snippets")
    config.add_argument("--server-name", default="gdb", help="Server name used in MCP config")

    doctor = subparsers.add_parser("doctor", help="Check environment prerequisites")
    doctor.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to install/configure gdb (best-effort).",
    )
    doctor.add_argument(
        "--method",
        default="auto",
        choices=("auto", "winget-msys2"),
        help="Fix method on Windows (default: auto).",
    )
    doctor.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce fix output.",
    )

    return parser


def _print_result_table(title: str, rows: list[dict[str, str]]) -> None:
    print(title)
    for row in rows:
        client = row.get("client", "unknown")
        status = row.get("status", "unknown")
        detail = row.get("path") or row.get("reason", "")
        if detail:
            print(f"- {client}: {status} ({detail})")
        else:
            print(f"- {client}: {status}")


def _resolve_gdb_candidate(settings) -> str:
    override = os.getenv("GDB_MCP_GDB_PATH")
    if isinstance(override, str) and override.strip():
        return override.strip()
    return (getattr(settings, "gdb_path", "") or "gdb").strip() or "gdb"


def _resolve_gdb_executable(candidate: str) -> str | None:
    if not candidate:
        return None
    if os.path.sep in candidate or (sys.platform == "win32" and ":" in candidate):
        path = Path(candidate).expanduser().resolve()
        return str(path) if path.exists() else None
    resolved = which(candidate)
    return resolved


def _find_msys2_root() -> Path | None:
    candidates: list[Path] = []
    if root := os.getenv("MSYS2_ROOT"):
        candidates.append(Path(root))

    candidates.extend(
        [
            Path("C:/msys64"),
            Path("C:/msys32"),
            Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "MSYS2",
            Path(os.getenv("PROGRAMFILES", "")) / "MSYS2",
            Path(os.getenv("PROGRAMFILES(X86)", "")) / "MSYS2",
        ]
    )

    for root in candidates:
        try:
            bash = (root / "usr" / "bin" / "bash.exe").resolve()
        except OSError:
            continue
        if bash.exists():
            return root
    return None


def _msys2_gdb_candidates(root: Path) -> list[Path]:
    return [
        root / "ucrt64" / "bin" / "gdb.exe",
        root / "mingw64" / "bin" / "gdb.exe",
        root / "usr" / "bin" / "gdb.exe",
    ]


def _write_config_gdb_path(settings, gdb_path: Path) -> None:
    config_path = Path(settings.config_path)
    try:
        raw = config_path.read_text(encoding="utf-8").strip() if config_path.exists() else "{}"
        payload = json.loads(raw) if raw else {}
        if not isinstance(payload, dict):
            payload = {}
    except (OSError, json.JSONDecodeError):
        payload = {}
    payload["gdb_path"] = str(gdb_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _try_fix_windows(settings, *, method: str, quiet: bool) -> bool:
    # Strategy: prefer installing MSYS2 via winget, then install mingw-w64 gdb,
    # then write absolute gdb_path into config.json (no global PATH edits).
    if method in ("auto", "winget-msys2"):
        winget = which("winget")
        if winget is None:
            if not quiet:
                print("[FIX] winget not found. Install GDB manually (see docs/zh-CN/SETUP.md).")
            return False

        if not quiet:
            print("[FIX] Installing MSYS2 via winget...")
        subprocess.run(
            [
                winget,
                "install",
                "--id",
                "MSYS2.MSYS2",
                "-e",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent",
            ],
            check=False,
        )

        root = _find_msys2_root()
        if root is None:
            if not quiet:
                print("[FIX] MSYS2 installed but root not found. Set MSYS2_ROOT then rerun doctor --fix.")
            return False

        bash = str((root / "usr" / "bin" / "bash.exe").resolve())
        if not quiet:
            print(f"[FIX] Using MSYS2 root: {root}")
            print("[FIX] Installing mingw-w64 gdb (ucrt64)...")

        # Best-effort install. If pacman requires interactive updates, user may need to run it once manually.
        subprocess.run(
            [
                bash,
                "-lc",
                "pacman -Sy --noconfirm --needed mingw-w64-ucrt-x86_64-gdb",
            ],
            check=False,
        )

        for candidate in _msys2_gdb_candidates(root):
            try:
                resolved = candidate.resolve()
            except OSError:
                continue
            if resolved.exists():
                _write_config_gdb_path(settings, resolved)
                if not quiet:
                    print(f"[FIX] gdb installed: {resolved}")
                    print(f"[FIX] Wrote gdb_path into config: {settings.config_path}")
                return True

        if not quiet:
            print("[FIX] Installed MSYS2 but could not locate gdb.exe. Open MSYS2 UCRT64 shell and run: pacman -S mingw-w64-ucrt-x86_64-gdb")
        return False

    if not quiet:
        print(f"[FIX] Unsupported method on Windows: {method}")
    return False


def _cmd_doctor(args: argparse.Namespace) -> int:
    env = detect_environment()
    settings = load_server_settings()
    env["runtime_mode"] = settings.mode
    env["config_path"] = settings.config_path
    env["gdb_configured"] = _resolve_gdb_candidate(settings)
    env["gdb_resolved"] = _resolve_gdb_executable(env["gdb_configured"])
    print(json.dumps(env, indent=2))

    if env.get("gdb_resolved") is not None:
        return 0

    print("[WARN] gdb not found. Configure gdb_path (config.json or GDB_MCP_GDB_PATH), or install gdb.")

    if args.fix and sys.platform == "win32":
        ok = _try_fix_windows(settings, method=args.method, quiet=args.quiet)
        if ok:
            # Re-check after fix
            settings2 = load_server_settings()
            resolved2 = _resolve_gdb_executable(_resolve_gdb_candidate(settings2))
            if resolved2 is not None:
                print(f"[OK] gdb resolved after fix: {resolved2}")
                return 0
        return 1
    return 1


def _cmd_install(args: argparse.Namespace) -> int:
    env = detect_environment()
    print("[Environment]")
    print(json.dumps(env, indent=2))

    try:
        results = install_mcp_servers(server_name=args.server_name, quiet=args.quiet, clients=args.client)
    except ValueError as exc:
        logger.error("{}", exc)
        return 1
    _print_result_table("[Install Results]", results)

    failures = [row for row in results if row.get("status") == "failed"]
    return 1 if failures else 0


def _cmd_uninstall(args: argparse.Namespace) -> int:
    try:
        results = uninstall_mcp_servers(server_name=args.server_name, quiet=args.quiet, clients=args.client)
    except ValueError as exc:
        logger.error("{}", exc)
        return 1
    _print_result_table("[Uninstall Results]", results)

    failures = [row for row in results if row.get("status") == "failed"]
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        from gdb_mcp.server import main as run_server

        run_server()
        return 0

    if args.command == "doctor":
        return _cmd_doctor(args)

    if args.command == "config":
        print(render_manual_config(server_name=args.server_name))
        return 0

    if args.command == "install":
        return _cmd_install(args)

    if args.command == "uninstall":
        return _cmd_uninstall(args)

    logger.error("Unknown command: {}", args.command)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

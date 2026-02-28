"""Command-line entrypoint for gdb-mcp."""

from __future__ import annotations

import argparse
import json
import sys

from loguru import logger

from gdb_mcp.install import (
    detect_environment,
    install_mcp_servers,
    render_manual_config,
    uninstall_mcp_servers,
)


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

    subparsers.add_parser("doctor", help="Check environment prerequisites")

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


def _cmd_doctor() -> int:
    env = detect_environment()
    print(json.dumps(env, indent=2))

    if env.get("gdb") is None:
        print("[WARN] gdb not found in PATH. Install gdb before using debugging tools.")
        return 1
    return 0


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
        return _cmd_doctor()

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

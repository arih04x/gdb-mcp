# gdb-mcp

English | [简体中文](README.zh-CN.md)

<div align="center">
  <img src="asset/gdb.svg" alt="gdb-mcp logo" width="140"/>
  <h3>GDB MCP Server for AI Debugging Workflows</h3>
  <p>Expose practical GDB capabilities as MCP tools for assistants and automation.</p>

  <p>
    <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-blue.svg" />
    <img alt="GDB" src="https://img.shields.io/badge/GDB-required-red.svg" />
    <img alt="MCP" src="https://img.shields.io/badge/MCP-enabled-green.svg" />
    <img alt="License MIT" src="https://img.shields.io/badge/license-MIT-lightgrey.svg" />
  </p>
</div>

## Overview

`gdb-mcp` is a Python MCP server that turns common GDB operations into MCP tools.
It is designed for:

- interactive AI-assisted debugging
- repeatable local debugging workflows
- lightweight integration into MCP-compatible clients

## Key Features

- Multi-session GDB management
- Program load / process attach / core dump load
- Breakpoint lifecycle and execution control (`set/list/toggle/delete`, `continue`, `step`, `next`)
- Runtime inspection with structured fields: backtrace frames, registers, memory, expressions
- Lightweight GDB/MI parsing via `pygdbmi` (`gdb_command` includes `miRecords` when MI lines are present)
- MCP client config installer (`gdb-mcp install`)

Structured-first response policy:
- When structured parsing succeeds (for example `miRecords`/`frames`/`registers`/`breakpoints`), the corresponding raw text field is omitted.
- Raw text is kept only as a fallback when structured parsing yields no usable data.

## Quick Start

Requirements:

- Python 3.11+
- `uv`
- `gdb`

Install and run:

```bash
uv sync --extra dev
uv run gdb-mcp
```

## Runtime Modes and Config

`gdb-mcp` reads runtime config from:

1. `GDB_MCP_CONFIG` (supports relative path)
2. default `./config.json` in the project root

Environment variables can override config values:

- `GDB_MODE=default|advanced`
- `GDB_MCP_MAX_OUTPUT_CHARS=<int>`

Use `gdb_get_capabilities` to inspect active mode/policy at runtime.
In `default` mode, advanced tools are hidden from `tools/list`.

Mode intent:

- `default`: stable baseline with high-frequency debugging capabilities, sufficient for most day-to-day debugging workflows.
- `advanced`: extends `default` with deeper, customizable analysis flows for complex debugging and deeper pwn-oriented needs.

## CLI Commands

```bash
uv run gdb-mcp doctor
uv run gdb-mcp install
uv run gdb-mcp install --client Codex
uv run gdb-mcp config
uv run gdb-mcp uninstall
```

`install` now supports a full cross-platform client matrix (similar to arida-pro-mcp style), and `--client` can scope installation to selected clients.

## Tool List

- `gdb_start`
- `gdb_get_capabilities`
- `gdb_load`
- `gdb_command`
- `gdb_terminate`
- `gdb_list_sessions`
- `gdb_set_breakpoint`
- `gdb_list_breakpoints`
- `gdb_delete_breakpoints`
- `gdb_toggle_breakpoints`
- `gdb_continue`
- `gdb_step`
- `gdb_next`
- `gdb_backtrace`
- `gdb_print`
- `gdb_examine`
- `gdb_info_registers`
- `gdb_attach` (advanced only)
- `gdb_load_core` (advanced only)
- `gdb_set_watchpoint` (advanced only)
- `gdb_info_threads` (advanced only)
- `gdb_thread_select` (advanced only)
- `gdb_frame_select` (advanced only)
- `gdb_collect_crash_report` (advanced only)

## Example

See [examples/USAGE.md](examples/USAGE.md).

Build the sample:

```bash
cd examples
gcc -g -O0 crash.c -o crash
```

## Testing

```bash
uv run pytest -q
```

## Troubleshooting

- `gdb` not found: run `uv run gdb-mcp doctor` and install `gdb` first.
- MCP tools fail unexpectedly: verify your target path and session id.
- Client config not installed: run `gdb-mcp install` and restart the MCP client.

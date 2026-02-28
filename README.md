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
- Breakpoints and execution control (`continue`, `step`, `next`, `finish`)
- Runtime inspection: backtrace, registers, memory, expressions, source listing
- MCP client config installer (`gdb-mcp install`)

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
- `gdb_load`
- `gdb_set_args`
- `gdb_command`
- `gdb_terminate`
- `gdb_list_sessions`
- `gdb_attach`
- `gdb_load_core`
- `gdb_set_breakpoint`
- `gdb_list_breakpoints`
- `gdb_delete_breakpoints`
- `gdb_toggle_breakpoints`
- `gdb_set_watchpoint`
- `gdb_continue`
- `gdb_step`
- `gdb_next`
- `gdb_finish`
- `gdb_backtrace`
- `gdb_print`
- `gdb_examine`
- `gdb_info_registers`
- `gdb_info_threads`
- `gdb_thread_select`
- `gdb_frame_select`
- `gdb_frame_up`
- `gdb_frame_down`
- `gdb_list_source`
- `gdb_collect_crash_report`

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

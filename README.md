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

## What Is `asset/gdb.svg`?

`asset/gdb.svg` is the project identity icon. It is used as the default visual mark for `gdb-mcp` in documentation and tooling pages.

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
uv run gdb-mcp config
uv run gdb-mcp uninstall
```

## Tool List

- `gdb_start`
- `gdb_load`
- `gdb_command`
- `gdb_terminate`
- `gdb_list_sessions`
- `gdb_attach`
- `gdb_load_core`
- `gdb_set_breakpoint`
- `gdb_continue`
- `gdb_step`
- `gdb_next`
- `gdb_finish`
- `gdb_backtrace`
- `gdb_print`
- `gdb_examine`
- `gdb_info_registers`
- `gdb_list_source`

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

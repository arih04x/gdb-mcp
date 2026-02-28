# gdb-mcp

Python MCP server for interactive GDB debugging.

## Features

- Manage multiple GDB sessions.
- Load binaries / attach / load core dumps.
- Set breakpoints and control execution (`continue`, `step`, `next`, `finish`).
- Inspect stack, registers, memory, expressions, and source location.
- Install MCP config to common clients (`gdb-mcp install`).

## Quick Start

```bash
uv sync --extra dev
```

Run MCP stdio server:

```bash
uv run gdb-mcp
```

## MCP Install Commands

```bash
uv run gdb-mcp doctor
uv run gdb-mcp install
uv run gdb-mcp config
uv run gdb-mcp uninstall
```

## Tools

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

Build sample:

```bash
cd examples
gcc -g -O0 crash.c -o crash
```

## Tests

```bash
uv run pytest -q
```


# CHANGELOG

Only core behavior changes are recorded here.

## 2026-03-03

### feat(config): allow configuring GDB executable path

- `config.json`: add `gdb_path` (also accepts legacy-style `gdbPath`).
- Env override: `GDB_MCP_GDB_PATH`.

### fix(server): default `gdb_start` to configured `gdb_path`

- If `gdbPath` is not provided, the server now starts GDB using `settings.gdb_path`.

### feat(cli): add `doctor --fix` for Windows (best-effort)

- `doctor` adds flags: `--fix`, `--method`, `--quiet`.
- `doctor` JSON output includes `gdb_configured` and `gdb_resolved`.
- On Windows, `doctor --fix` attempts to:
	- install MSYS2 via `winget`;
	- install `mingw-w64-ucrt-x86_64-gdb` via MSYS2 `pacman`;
	- locate `gdb.exe` and write an absolute `gdb_path` back into `config.json` (avoids editing global `PATH`).

## 2026-02-28

### feat(parsing): integrate `pygdbmi` and structured-first responses

- `gdb_command` adds `miRecords` (MI line parsing via `pygdbmi`).
- When structured fields are available, the server no longer duplicates the corresponding raw text fields; it only falls back to raw text when structured parsing fails.
- Example (verified locally with `examples/crash`):
	- MI line: `^done,bkpt={number="1",type="breakpoint",...,addr="0x00000000000011fa",file="crash.c",line="18",...}`
	- Raw CLI: `Breakpoint 1 at 0x11fa: file crash.c, line 18.`

### fix(server): add module entrypoint for stdio startup (`f5c9972`)

- Add runnable entrypoint `python -m gdb_mcp.server`, fixing MCP `initialize` handshake failures.

### fix(manager): make `load_core` use validated paths without GDB-incompatible quoting

- `gdb_load_core` now validates and resolves `program` / `corePath` first, and passes them to GDB in a compatible form.
- Fix loading failures caused by incorrectly quoting absolute `corePath`.
- Return an explicit error when `corePath` contains whitespace (a `gdb core-file` parsing limitation), instead of incorrectly reporting `ok=true`.

### fix(manager): stabilize crash report collection on top frame

- `gdb_collect_crash_report` temporarily selects `frame 0` before collecting, avoiding interference from external `gdb_frame_select` calls.
- Automatically restores the previously selected frame after collection, preserving user session context.


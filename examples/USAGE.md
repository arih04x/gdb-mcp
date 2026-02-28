# gdb-mcp Usage with `examples/crash.c`

This document uses `examples/crash.c` as the demo target.

## 1. Build demo binary

```bash
cd examples
gcc -g -O0 crash.c -o crash
```

## 2. Register MCP server (optional)

```bash
# auto detect common clients and install config
uv run gdb-mcp install

# if you only need manual snippet
uv run gdb-mcp config
```

## 3. Typical debug flow through MCP tools

1. Start session:

```json
{"tool":"gdb_start","arguments":{"workingDir":"/abs/path/to/gdb-mcp/examples"}}
```

2. Load binary and set args:

```json
{"tool":"gdb_load","arguments":{"sessionId":"<SESSION_ID>","program":"/abs/path/to/gdb-mcp/examples/crash","arguments":["15"]}}
```

3. Set breakpoints:

```json
{"tool":"gdb_set_breakpoint","arguments":{"sessionId":"<SESSION_ID>","location":"main"}}
```

```json
{"tool":"gdb_set_breakpoint","arguments":{"sessionId":"<SESSION_ID>","location":"function_with_args"}}
```

4. Run:

```json
{"tool":"gdb_command","arguments":{"sessionId":"<SESSION_ID>","command":"run"}}
```

5. Inspect and step:

```json
{"tool":"gdb_print","arguments":{"sessionId":"<SESSION_ID>","expression":"number"}}
```

```json
{"tool":"gdb_next","arguments":{"sessionId":"<SESSION_ID>"}}
```

```json
{"tool":"gdb_backtrace","arguments":{"sessionId":"<SESSION_ID>","full":true,"limit":10}}
```

6. Stop session:

```json
{"tool":"gdb_terminate","arguments":{"sessionId":"<SESSION_ID>"}}
```

## Expected behavior

When argument `15` is passed, `function_that_crashes()` dereferences a null pointer and triggers a crash. Use `gdb_backtrace` to inspect the crash stack.

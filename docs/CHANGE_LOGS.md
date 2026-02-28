# CHANGELOG

仅记录核心功能变更。

## 2026-02-28

### fix(server): add module entrypoint for stdio startup (`f5c9972`)

- 增加 `python -m gdb_mcp.server` 的可执行入口，修复 MCP `initialize` 握手失败。

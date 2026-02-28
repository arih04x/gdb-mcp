# CHANGELOG

仅记录核心功能变更。

## 2026-02-28

### feat(parsing): integrate `pygdbmi` and structured-first responses

- `gdb_command` 新增 `miRecords`（基于 `pygdbmi` 解析 MI 行）。
- 当结构化字段可用时，不再重复返回对应原始字段；仅在结构化失败时回退到 raw 文本。
- 示例（`examples/crash` 本地实测）：
  - MI 行：`^done,bkpt={number="1",type="breakpoint",...,addr="0x00000000000011fa",file="crash.c",line="18",...}`
  - 原始 CLI：`Breakpoint 1 at 0x11fa: file crash.c, line 18.`

### fix(server): add module entrypoint for stdio startup (`f5c9972`)

- 增加 `python -m gdb_mcp.server` 的可执行入口，修复 MCP `initialize` 握手失败。

### fix(manager): make `load_core` use validated paths without gdb-incompatible quoting

- `gdb_load_core` 现在会校验并解析 `program`/`corePath` 路径，再以 GDB 兼容格式传入。
- 修复 `corePath` 绝对路径被错误加引号后加载失败的问题。
- 对包含空白字符的 `corePath` 返回明确错误（`gdb core-file` 解析限制），避免误报 `ok=true`。

### fix(manager): stabilize crash report collection on top frame

- `gdb_collect_crash_report` 采集前会临时切换到 `frame 0`，避免被外部 `gdb_frame_select` 污染。
- 采集后自动恢复原先帧选择，避免改变用户会话上下文。

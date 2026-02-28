# CHANGE_LOGS

本文件记录 `gdb-mcp` 的重要变更，便于后续维护与回溯。

## 2026-02-28

### test(session): add real stdio MCP handshake coverage (unreleased)

- 新增 `tests/test_mcp_stdio_integration.py`，覆盖 `initialize`、`tools/list`、`gdb_list_sessions` 真实请求链路
- 验证 MCP 服务端在 stdio 传输下可被客户端直接握手并调用核心工具

### fix(session): normalize UTC timestamp output format (unreleased)

- 修复 `started_at` 输出，统一为 RFC3339 风格 `...Z`，避免 `+00:00Z` 组合格式
- 在 `tests/test_session.py` 增加对应断言，防止时间序列化回归

### docs(readme): add bilingual readme with logo intro (`c238213`)

- 新增 `README.zh-CN.md`
- `README.md` 增强为可点击中英文切换
- 增加 `asset/gdb.svg` 介绍与首页化结构（logo、badge、快速入口）

### feat(install): add full client matrix and client-scoped install (`5b82094`)

- 安装器升级为三平台全客户端矩阵
- 新增 `--client` 参数，支持定向安装（例如仅 `Codex`）
- 增加对应测试覆盖与 README 说明

### fix(server): add module entrypoint for stdio startup (`f5c9972`)

- 为 `python -m gdb_mcp.server` 增加 `__main__` 入口
- 修复 Codex MCP 握手阶段 `initialize response` 失败问题
- 已通过真实 MCP 初始化握手验证

## 维护约定

- 每次功能改动后，若影响行为/安装/协议兼容性，需要补充一条 changelog。
- 记录建议包含：提交号、影响范围、验证方式、兼容性说明。
